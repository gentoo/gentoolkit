#!/usr/bin/python

# Copyright 2003-2010 Gentoo Foundation
# Distributed under the terms of the GNU General Public License v2


import os
import shlex
import stat
import sys
from functools import partial
from inspect import signature
from pathlib import Path
from typing import Optional, Set

import portage
from portage.dep import Atom, use_reduce
from portage.dep._slot_operator import strip_slots
from portage.dep.libc import find_libc_deps, strip_libc_deps
from portage.exception import InvalidDependString

import gentoolkit.pprinter as pp
from gentoolkit.eclean.exclude import (
    exclDictExpand,
    exclDictExpandPkgname,
    exclDictMatchCP,
    exclMatchFilename,
)

# Misc. shortcuts to some portage stuff:
port_settings = portage.settings
pkgdir = port_settings["PKGDIR"]

err = sys.stderr
deprecated_message = """"Deprecation Warning: Installed package: %s
	Is no longer in the tree or an installed overlay"""
DEPRECATED = pp.warn(deprecated_message)

debug_modules = []


def dprint(module, message):
    if module in debug_modules:
        print(message)


def get_distdir():
    """Returns DISTDIR if sane, else barfs."""

    d = portage.settings["DISTDIR"]
    if not os.path.isdir(d):
        e = pp.error("%s does not appear to be a directory.\n" % d)
        e += pp.error("Please set DISTDIR to a sane value.\n")
        e += pp.error("(Check your make.conf file and environment).")
        print(e, file=sys.stderr)
        exit(1)
    return d


distdir = get_distdir()


class DistfilesSearch:
    """

    @param output: verbose output method or (lambda x: None) to turn off
    @param vardb: defaults to portage.db[portage.root]["vartree"].dbapi
                            is overridden for testing.
    @param portdb: defaults to portage.portdb and is overriden for testing."""

    def __init__(
        self,
        output,
        portdb=portage.portdb,
        vardb=portage.db[portage.root]["vartree"].dbapi,
    ):
        self.vardb = vardb
        self.portdb = portdb
        self.output = output
        self.installed_cpvs = None

    def findDistfiles(
        self,
        exclude=None,
        destructive=False,
        fetch_restricted=False,
        package_names=False,
        time_limit=0,
        size_limit=0,
        _distdir=distdir,
        deprecate=False,
        extra_checks=(),
    ):
        """Find all obsolete distfiles.

        XXX: what about cvs ebuilds?
        I should install some to see where it goes...

        @param exclude: an exclusion dict as defined in
                        exclude.parseExcludeFile class.
        @param destructive: boolean, defaults to False
        @param fetch_restricted: boolean, defaults to False
        @param package_names: boolean, defaults to False.
        @param time_limit: integer time value as returned by parseTime()
        @param size_limit: integer value of max. file size to keep or 0 to ignore.
        @param _distdir: path to the distfiles dir being checked, defaults to portage.
        @param deprecate: bool to control checking the clean dict. files for exclusion

        @rtype: dict
        @return dict. of package files to clean i.e. {'cat/pkg-ver.tbz2': [filename],}
        """
        if exclude is None:
            exclude = {}
        clean_me = {}
        pkgs = {}
        saved = {}
        deprecated = {}
        installed_included = False
        # Check if DISTDIR is empty, return early
        if not os.listdir(_distdir):
            return clean_me, saved, deprecated

        # create a big CPV->SRC_URI dict of packages
        # whose distfiles should be kept
        if (not destructive) or fetch_restricted:
            self.output("...non-destructive type search")
            pkgs, _deprecated = self._non_destructive(destructive, fetch_restricted)
            deprecated.update(_deprecated)
            installed_included = True
        if destructive:
            self.output(
                "...destructive type search: %d packages already found" % len(pkgs)
            )
            pkgs, _deprecated = self._destructive(
                package_names, exclude, pkgs, installed_included
            )
            deprecated.update(_deprecated)
        # gather the files to be cleaned
        self.output("...checking limits for %d ebuild sources" % len(pkgs))

        vcs = self.vcs_check(Path(_distdir))
        checks = self._get_default_checks(size_limit, time_limit, exclude, destructive)
        checks.extend(extra_checks)
        clean_me = self._check_limits(_distdir, checks, clean_me)
        # remove any protected files from the list
        self.output(
            "...removing protected sources from %s candidates to clean" % len(clean_me)
        )
        clean_me = self._remove_protected(pkgs, clean_me)
        if not deprecate and len(exclude) and len(clean_me):
            self.output(
                "...checking final for exclusion from "
                + "%s remaining candidates to clean" % len(clean_me)
            )
            clean_me, saved = self._check_excludes(exclude, clean_me)
        return clean_me, saved, deprecated, vcs

    # begin _check_limits code block

    def _get_default_checks(self, size_limit, time_limit, excludes, destructive):
        # checks =[(self._isreg_check_, "is_reg_check")]
        checks = [self._isreg_check_]
        if "filenames" in excludes:
            # checks.append((partial(self._filenames_check_, excludes), "Filenames_check"))
            checks.append(partial(self._filenames_check_, excludes))
        else:
            self.output("   - skipping exclude filenames check")
        if size_limit:
            # checks.append((partial(self._size_check_, size_limit), "size_check"))
            checks.append(partial(self._size_check_, size_limit))
        else:
            self.output("   - skipping size limit check")
        if time_limit:
            # print("time_limit = ", time_limit/1000000,"M sec")
            # checks.append((partial(self._time_check_, time_limit), "time_check"))
            checks.append(partial(self._time_check_, time_limit))
        else:
            self.output("   - skipping time limit check")
        if destructive:
            self.output("   - skipping dot files check")
        else:
            checks.append(self._dotfile_check_)
        return checks

    def _check_limits(self, _distdir, checks, clean_me=None):
        """Checks files if they exceed size and/or time_limits, etc.

        To start with everything is considered dirty and is excluded
        only if it matches some condition.
        """
        if clean_me is None:
            clean_me = {}
        for file in os.listdir(_distdir):
            filepath = os.path.join(_distdir, file)
            try:
                file_stat = os.lstat(filepath)
            except OSError:
                continue
            is_dirty = False
            # for check, check_name in checks:
            for check in checks:
                should_break, is_dirty = check(file_stat, file)
                if should_break:
                    break

            if is_dirty:
                # print( "%s Adding file to clean_list:" %check_name, file)
                clean_me[file] = [filepath]
        return clean_me

    @staticmethod
    def _isreg_check_(file_stat, file):
        """check if file is a regular file."""
        is_reg_file = stat.S_ISREG(file_stat[stat.ST_MODE])
        return not is_reg_file, is_reg_file

    @staticmethod
    def _size_check_(size_limit, file_stat, file):
        """checks if the file size exceeds the size_limit"""
        if file_stat[stat.ST_SIZE] >= size_limit:
            # print( "size mismatch ", file, file_stat[stat.ST_SIZE])
            return True, False
        return False, True

    @staticmethod
    def _time_check_(time_limit, file_stat, file):
        """checks if the file exceeds the time_limit
        (think forward, not back, time keeps increasing)"""
        if file_stat[stat.ST_MTIME] >= time_limit:
            # print( "time match too young ", file, file_stat[stat.ST_MTIME]/1000000,"M sec.")
            return True, False
        # print( "time match too old", file, file_stat[stat.ST_MTIME]/1000000,"M sec.")
        return False, True

    @staticmethod
    def _filenames_check_(exclude, file_stat, file):
        """checks if the file matches an exclusion file listing"""
        # Try to match file name directly
        if file in exclude["filenames"]:
            return True, False
        # See if file matches via regular expression matching
        else:
            file_match = False
            for file_entry in exclude["filenames"]:
                if exclude["filenames"][file_entry].match(file):
                    file_match = True
                    break
        if file_match:
            # print( "filename match ", file)
            return True, False
        return False, True

    @staticmethod
    def _dotfile_check_(file_stat, file):
        """check if file is a regular file."""
        head, tail = os.path.split(file)
        if tail:
            is_dot_file = tail.startswith(".")
        return is_dot_file, not is_dot_file

    # end _check_limits code block

    @staticmethod
    def _remove_protected(pkgs, clean_me):
        """Remove files owned by some protected packages.

        @returns packages to clean
        @rtype: dictionary
        """
        for cpv in pkgs:
            uris = pkgs[cpv].split()
            uris.reverse()
            while uris:
                uri = uris.pop()
                if uris and uris[-1] == "->":
                    operator = uris.pop()  # noqa
                    file = uris.pop()
                else:
                    file = os.path.basename(uri)
                if file in clean_me:
                    del clean_me[file]
            # no need to waste IO time if there is nothing left to clean
            if not len(clean_me):
                return clean_me
        return clean_me

    def _non_destructive(
        self, destructive, fetch_restricted, pkgs_=None, hosts_cpvs=None
    ):
        """performs the non-destructive checks

        @param destructive: boolean
        @param pkgs_: starting dictionary to add to
                        defaults to {}.

        @returns packages and thier SRC_URI's: {cpv: src_uri,}
        @rtype: dictionary
        """
        if pkgs_ is None:
            pkgs = {}
        else:
            pkgs = pkgs_.copy()
        deprecated = {}
        # the following code block was split to optimize for speed
        # list all CPV from portree (yeah, that takes time...)
        self.output("   - getting complete ebuild list")
        cpvs = set(self.portdb.cpv_all())
        installed_cpvs = set(self.vardb.cpv_all())
        # now add any installed cpv's that are not in the tree or overlays
        cpvs.update(installed_cpvs)
        # Add any installed cpvs from hosts on the network, if any
        if hosts_cpvs:
            cpvs.update(hosts_cpvs)
            installed_cpvs.update(hosts_cpvs)
        if fetch_restricted and destructive:
            self.output(
                "   - getting source file names "
                + "for %d installed ebuilds" % len(installed_cpvs)
            )
            pkgs, _deprecated = self._unrestricted(pkgs, installed_cpvs)
            deprecated.update(_deprecated)
            # remove the installed cpvs then check the remaining for fetch restiction
            cpvs.difference_update(installed_cpvs)
            self.output(
                "   - getting fetch-restricted source file names "
                + "for %d remaining ebuilds" % len(cpvs)
            )
            pkgs, _deprecated = self._fetch_restricted(pkgs, cpvs)
            deprecated.update(_deprecated)
            # save the installed cpv list to re-use in _destructive()
            self.installed_cpvs = installed_cpvs.copy()
        else:
            self.output(
                "   - getting source file names " + "for %d ebuilds" % len(cpvs)
            )
            pkgs, _deprecated = self._unrestricted(pkgs, cpvs)
            deprecated.update(_deprecated)
        return pkgs, deprecated

    def vcs_check(self, distdir: Path) -> Set:
        """Checks $DISTDIR/vcs-src for checkouts which are not in the vardb"""
        # For now we only check git
        vcs_src = distdir / "git3-src"
        expected_dirs = set()
        actual_dirs = set()
        if vcs_src.is_dir():
            for i in set(self.vardb.cpv_all()):
                if "live" in self.vardb.aux_get(i, ["PROPERTIES"]):
                    try:
                        # try to get the dir names of the cloned
                        # repos from the environment file.
                        vcs_dir = {
                            i.split("=")[-1].strip('"')
                            for i in shlex.split(
                                self.vardb._aux_env_search(i, ["EVCS_STORE_DIRS"])[
                                    "EVCS_STORE_DIRS"
                                ].strip("()")
                            )
                        }
                        expected_dirs.update(vcs_dir)
                    except KeyError:
                        pass
            actual_dirs = {str(i) for i in vcs_src.iterdir() if i.is_dir()}
        return actual_dirs.difference(expected_dirs)

    def _fetch_restricted(self, pkgs_, cpvs):
        """perform fetch restricted non-destructive source
        filename lookups

        @param pkgs_: starting dictionary to add to
        @param cpvs: set of (cat/pkg-ver, ...) identifiers

        @return a new pkg dictionary
        @rtype: dictionary
        """
        if pkgs_ is None:
            pkgs = {}
        else:
            pkgs = pkgs_.copy()
        deprecated = {}
        for cpv in cpvs:
            # get SRC_URI and RESTRICT from aux_get
            try:  # main portdb
                (src_uri, restrict) = self.portdb.aux_get(cpv, ["SRC_URI", "RESTRICT"])
                # keep fetch-restricted check
                # inside try so it is bypassed on KeyError
                if "fetch" in restrict:
                    pkgs[cpv] = src_uri
            except KeyError:
                try:  # installed vardb
                    (src_uri, restrict) = self.vardb.aux_get(
                        cpv, ["SRC_URI", "RESTRICT"]
                    )
                    deprecated[cpv] = src_uri
                    self.output(DEPRECATED % cpv)
                    # keep fetch-restricted check
                    # inside try so it is bypassed on KeyError
                    if "fetch" in restrict:
                        pkgs[cpv] = src_uri
                except KeyError:
                    self.output("   - Key Error looking up: " + cpv)
        return pkgs, deprecated

    def _unrestricted(self, pkgs_, cpvs):
        """Perform unrestricted source filenames lookups

        @param pkgs_: starting packages dictionary
        @param cpvs: set of (cat/pkg-ver, ...) identifiers

        @return a new pkg dictionary
        @rtype: dictionary
        """
        if pkgs_ is None:
            pkgs = {}
        else:
            pkgs = pkgs_.copy()
        deprecated = {}
        for cpv in cpvs:
            # get SRC_URI from aux_get
            try:
                pkgs[cpv] = self.portdb.aux_get(cpv, ["SRC_URI"])[0]
            except KeyError:
                try:  # installed vardb
                    pkgs[cpv] = self.vardb.aux_get(cpv, ["SRC_URI"])[0]
                    deprecated[cpv] = pkgs[cpv]
                    self.output(DEPRECATED % cpv)
                except KeyError:
                    self.output("   - Key Error looking up: " + cpv)
        return pkgs, deprecated

    def _destructive(
        self, package_names, exclude, pkgs_=None, installed_included=False
    ):
        """Builds on pkgs according to input options

        @param package_names: boolean
        @param exclude: an exclusion dict as defined in
                        exclude.parseExcludeFile class.
        @param pkgs: starting dictionary to add to
                        defaults to {}.
        @param installed_included: bool. pkgs already
                        has the installed cpv's added.

        @returns pkgs: {cpv: src_uri,}
        """
        if pkgs_ is None:
            pkgs = {}
        else:
            pkgs = pkgs_.copy()
        deprecated = {}
        pkgset = set()
        if not installed_included:
            if not package_names:
                # list all installed CPV's from vartree
                # print( "_destructive: getting vardb.cpv_all")
                if not self.installed_cpvs:
                    pkgset.update(self.vardb.cpv_all())
                else:
                    pkgset.update(self.installed_cpvs)
                self.output("   - processing %s installed ebuilds" % len(pkgset))
            elif package_names:
                # list all CPV's from portree for CP's in vartree
                # print( "_destructive: getting vardb.cp_all")
                cps = self.vardb.cp_all()
                self.output("   - processing %s installed packages" % len(cps))
                for package in cps:
                    pkgset.update(self.portdb.cp_list(package))
        self.output("   - processing excluded")
        excludes = self._get_excludes(exclude)
        excludes_length = len(excludes)
        dprint("excludes", "EXCLUDES LENGTH =%d" % excludes_length)
        pkgset.update(excludes)
        pkgs_done = set(list(pkgs))
        pkgset.difference_update(pkgs_done)
        self.output(
            "   - (%d of %d total) additional excluded packages to get source filenames for"
            % (len(pkgset), excludes_length)
        )
        # self.output("   - processing %d ebuilds for filenames" %len(pkgset))
        pkgs, _deprecated = self._unrestricted(pkgs, pkgset)
        deprecated.update(_deprecated)
        # self.output("   - done...")
        return pkgs, deprecated

    def _get_excludes(self, exclude):
        """Expands the exclude dictionary into a set of
        CPV's

        @param exclude: dictionary of exclusion categories,
                packages to exclude from the cleaning

        @rtype: set
        @return set of package cpv's
        """
        pkgset = set()
        for cp in exclDictExpand(exclude):
            # add packages from the exclude file
            dprint(
                "excludes",
                "_GET_EXCLUDES, cp=" + cp + ", " + str(self.portdb.cp_list(cp)),
            )
            pkgset.update(self.portdb.cp_list(cp))
        return pkgset

    def _check_excludes(self, exclude, clean_me):
        """Performs a last minute check on remaining filenames
        to see if they should be protected.  Since if the pkg-version
        was deprecated it would not have been matched to a
        source filename and removed.

        @param exclude: an exclusion dictionary
        @param clean_me: the list of filenames for cleaning

        @rtype: dict of packages to clean
        """
        saved = {}
        pn_excludes = exclDictExpandPkgname(exclude)
        dprint("excludes", "_check_excludes: made it here ;)")
        if not pn_excludes:
            return clean_me, saved
        dprint("excludes", pn_excludes)
        for key in list(clean_me):
            if exclMatchFilename(pn_excludes, key):
                saved[key] = clean_me[key]
                del clean_me[key]
                self.output("   ...Saved excluded package filename: " + key)
        return clean_me, saved


def _deps_equal(deps_a, eapi_a, deps_b, eapi_b, libc_deps, uselist=None, cpv=None):
    """Compare two dependency lists given a set of USE flags

    @param deps_a: binpkg DEPEND string (for InvalidDependString errors)
    @rtype: string
    @param eapi_a: EAPI
    @rtype: string
    @param deps_b: ebuild DEPEND string (for InvalidDependString errors)
    @rtype: string
    @param eapi_b: EAPI
    @rtype: string
    @param libc_deps: List of libc packages (or atoms if realized is passed).
    @rtype: list
    @param uselist: use flag list
    @rtype: frozenset
    @param cpv: Cat/Pkg-version
    @rtype: string
    """
    if deps_a == deps_b:
        return True
    try:
        deps_a = use_reduce(deps_a, uselist=uselist, eapi=eapi_a, token_class=Atom)
    except InvalidDependString:  # the binpkg depend string is bad
        print(
            pp.warn(
                "Warning: Invalid binpkg DEPEND string found for: %s, %s"
                " | tagging for removal" % (cpv, deps_a)
            ),
            file=sys.stderr,
        )
        return False
    try:
        deps_b = use_reduce(deps_b, uselist=uselist, eapi=eapi_b, token_class=Atom)
    except InvalidDependString as er:  # the ebuild depend string is bad
        print(
            pp.warn("Warning: Invalid ebuild DEPEND String found for: %s" % cpv),
            file=sys.stderr,
        )
        print(
            pp.warn("Warning: DEPEND string for ebuild: %s" % deps_b),
            file=sys.stderr,
        )
        print(er, file=sys.stderr)
        return True

    strip_libc_deps(deps_a, libc_deps)
    strip_libc_deps(deps_b, libc_deps)
    strip_slots(deps_a)
    strip_slots(deps_b)
    return deps_a == deps_b


def findPackages(
    options: dict[str, bool],
    exclude: Optional[dict] = None,
    destructive: bool = False,
    time_limit: Optional[int] = 0,
    package_names: Optional[bool] = False,
    pkgdir: str = None,
    port_dbapi=portage.db[portage.root]["porttree"].dbapi,
    var_dbapi=portage.db[portage.root]["vartree"].dbapi,
) -> tuple[dict[str, list[str]], dict[str, list[str]]]:
    """Find obsolete binary packages.

    @param invalid_paths:
    @param options: dict of options determined at runtime
    @type  options: dict
    @param exclude: exclusion dict (as defined in the exclude.parseExcludeFile class)
    @type  exclude: dict, optional
    @param destructive: binpkg is obsolete if not installed (default: `False`)
    @type  destructive: bool, optional
    @param time_limit: exclude binpkg if newer than time value as returned by parseTime()
    @type  time_limit: int, optional
    @param package_names: exclude all binpkg versions if package is installed
                                              (used with `destructive=True`) (default: `False`)
    @type  package_names: bool, optional
    @param pkgdir: path to the binpkg cache (PKGDIR)
    @type  pkgdir: str
    @param port_dbapi: defaults to portage.db[portage.root]["porttree"].dbapi
                                       Can be overridden for tests.
    @param  var_dbapi: defaults to portage.db[portage.root]["vartree"].dbapi
                                       Can be overridden for tests.

    @return binary packages to remove. e.g. {'cat/pkg-ver': [filepath]}
    @rtype: dict
    """
    if exclude is None:
        exclude = {}

    # Access test, os.walk does not error for "no read permission"
    try:
        test = os.listdir(pkgdir)
        del test
    except OSError as er:
        if options["ignore-failure"]:
            exit(0)
        print(pp.error("Error accessing PKGDIR."), file=sys.stderr)
        print(pp.error("(Check your make.conf file and environment)."), file=sys.stderr)
        print(pp.error("Error: %s" % str(er)), file=sys.stderr)
        exit(1)

    libc_deps = find_libc_deps(var_dbapi, False)

    # Create a dictionary of all installed packages
    if destructive and package_names:
        installed = dict.fromkeys(var_dbapi.cp_all())
    else:
        installed = {}

    # Dictionary of binary packages to clean. Organized as cpv->[pkgs] in order
    # to support FEATURES=binpkg-multi-instance.
    dead_binpkgs: dict[str, list[str]] = {}
    keep_binpkgs = {}

    # FEATURES=pkgdir-index-trusted is now on by default which makes portages inavlids
    # inaccessible
    settings = var_dbapi.settings
    bin_dbapi = portage.binarytree(pkgdir=pkgdir, settings=settings).dbapi
    populate_kwargs = {}
    if "invalid_errors" in signature(bin_dbapi.bintree.populate).parameters:
        populate_kwargs["invalid_errors"] = False
    if "force_reindex" in signature(bin_dbapi.bintree.populate).parameters:
        bin_dbapi.bintree.populate(force_reindex=True, **populate_kwargs)
    for cpv in bin_dbapi.cpv_all():
        cp = portage.cpv_getkey(cpv)

        # Exclude per --exclude-file=...
        if exclDictMatchCP(exclude, cp):
            continue

        # Exclude if binpkg is newer than --time-limit=...
        if time_limit:
            mtime = int(bin_dbapi.aux_get(cpv, ["_mtime_"])[0])
            if mtime >= time_limit:
                continue

        # Exclude if binpkg has exact same USEs
        if not destructive and options["unique-use"]:
            keys = ("CPV", "EAPI", "USE")
            binpkg_metadata = dict(zip(keys, bin_dbapi.aux_get(cpv, keys)))
            cpv_key = "_".join(binpkg_metadata[key] for key in keys)
            if cpv_key in keep_binpkgs:
                old_cpv = keep_binpkgs[cpv_key]
                # compare BUILD_TIME, keep the new one
                old_time = int(bin_dbapi.aux_get(old_cpv, ["BUILD_TIME"])[0])
                new_time = int(bin_dbapi.aux_get(cpv, ["BUILD_TIME"])[0])
                drop_cpv = old_cpv if new_time >= old_time else cpv

                binpkg_path = bin_dbapi.bintree.getname(drop_cpv)
                dead_binpkgs.setdefault(drop_cpv, []).append(binpkg_path)

                if new_time >= old_time:
                    keep_binpkgs[cpv_key] = cpv
                else:
                    continue
            else:
                keep_binpkgs[cpv_key] = cpv

        # Exclude if binpkg exists in the porttree and not --deep
        if not destructive and port_dbapi.cpv_exists(cpv):
            if not options["changed-deps"]:
                continue

            dep_keys = ("RDEPEND", "PDEPEND")
            keys = ("EAPI", "USE") + dep_keys
            binpkg_metadata = dict(zip(keys, bin_dbapi.aux_get(cpv, keys)))
            ebuild_metadata = dict(zip(keys, port_dbapi.aux_get(cpv, keys)))

            deps_binpkg = " ".join(binpkg_metadata[key] for key in dep_keys)
            deps_ebuild = " ".join(ebuild_metadata[key] for key in dep_keys)
            if _deps_equal(
                deps_binpkg,
                binpkg_metadata["EAPI"],
                deps_ebuild,
                ebuild_metadata["EAPI"],
                libc_deps,
                frozenset(binpkg_metadata["USE"].split()),
                cpv,
            ):
                continue

        if destructive and var_dbapi.cpv_exists(cpv):
            # Exclude if an instance of the package is installed due to
            # the --package-names option.
            if cp in installed and port_dbapi.cpv_exists(cpv):
                continue

            # Exclude if BUILD_TIME of binpkg is same as vartree
            buildtime = var_dbapi.aux_get(cpv, ["BUILD_TIME"])[0]
            if buildtime == bin_dbapi.aux_get(cpv, ["BUILD_TIME"])[0]:
                continue

        if not destructive and options["unique-use"]:
            del keep_binpkgs[cpv_key]

        binpkg_path = bin_dbapi.bintree.getname(cpv)
        dead_binpkgs.setdefault(cpv, []).append(binpkg_path)
    try:
        invalid_paths = bin_dbapi.bintree.invalid_paths
    except AttributeError:
        invalid_paths = bin_dbapi.bintree.invalids

    return dead_binpkgs, invalid_paths


# vim: set ts=4 sw=4 tw=79:
