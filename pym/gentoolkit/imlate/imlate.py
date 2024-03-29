#!/usr/bin/python
# Copyright 1999-2017 Gentoo Foundation
# Distributed under the terms of the GNU General Public License v2
# $Id$
# Author: Christian Ruppert <idl0r@gentoo.org>

__version__ = "@VERSION@"

# works just with stable keywords!
MAIN_ARCH = "auto"  # can be overridden by -m ARCH
TARGET_ARCH = "auto"  # can be overridden by -t ARCH
# auto means e.g.:
# MAIN_ARCH = amd64
# TARGET_ARCH = ~amd64
# That will show you general stable candidates for amd64.
# The arch will be taken from your portage settings (e.g. make.conf).

################################
# do not change anything below #
################################

from os.path import join, basename
from sys import stderr, stdout
from os import stat
from time import time
from xml.dom import minidom, NotFoundErr
from xml.parsers.expat import ExpatError

# TODO: just import needed stuff to safe memory/time and maybe use "as foo"
import portage
import portage.versions

from optparse import OptionParser
from time import gmtime, strftime

# override/change portage module settings


def _portage_settings(var, value, settings=None):
    if not settings:
        settings = portage.settings

    settings.unlock()
    settings[var] = value
    # backup_changes is very important since it can cause trouble,
    # if we do not backup our changes!
    settings.backup_changes(var)
    settings.lock()


# add stuff to our imlate dict


def _add_ent(imlate, cat, pkg, ver, our_ver):
    if not cat in list(imlate.keys()):
        imlate[cat] = {}
    if not pkg in list(imlate[cat].keys()):
        imlate[cat][pkg] = []

    imlate[cat][pkg].append(ver)
    imlate[cat][pkg].append(our_ver)

    return imlate


def _fill(width, line, fill=" "):
    while len(line) < width:
        line = f"{str(line)}{str(fill)}"
    return line


# create a hopefully pretty result


def show_result(conf, pkgs):
    # X - len(colX) = space to fill
    col1 = -1
    col2 = -1
    for cat in pkgs:
        for pkg in pkgs[cat]:
            col1 = max(col1, len(f"{cat}/{pkg}"))
            col2 = max(col2, len(pkgs[cat][pkg][1]))
    col1 += 1
    col2 += 1

    _header = "%s candidates for 'gentoo' on '%s'"
    _helper = "{}{}{}".format(
        _fill(col1, "category/package[:SLOT])"),
        _fill(col2, "our version"),
        "best version",
    )
    _cand = ""
    header = ""

    if conf["FILE"] == "stdout":
        out = stdout
    elif conf["FILE"] == "stderr":
        out = stderr
    else:
        out = open(conf["FILE"], "w")

    if conf["STABLE"] and conf["KEYWORD"]:
        _cand = "%i Stable and %i Keyword(~)" % (
            conf["STABLE_SUM"],
            conf["KEYWORD_SUM"],
        )
    elif conf["STABLE"]:
        _cand = "%i Stable" % conf["STABLE_SUM"]
    elif conf["KEYWORD"]:
        _cand = "%i Keyword(~)" % conf["KEYWORD_SUM"]

    header = _header % (_cand, conf["MAIN_ARCH"])

    print("Generated on: %s" % conf["TIME"], file=out)
    print(_fill(len(header), "", "="), file=out)
    print(header, file=out)
    print(_fill(len(header), "", "="), file=out)
    print(file=out)

    print(_helper, file=out)
    print(_fill(len(_helper), "", "-"), file=out)

    for cat in sorted(pkgs.keys()):
        for pkg in sorted(pkgs[cat].keys()):
            print(
                "%s%s%s"
                % (
                    _fill(col1, (f"{cat}/{pkg}")),
                    _fill(col2, pkgs[cat][pkg][1]),
                    pkgs[cat][pkg][0],
                ),
                file=out,
            )

    if conf["FILE"] != "stdout":
        out.close()


def _get_metadata(metadata, element, tag):
    values = []

    try:
        metadatadom = minidom.parse(metadata)
    except ExpatError as e:
        raise ExpatError(
            "%s: %s"
            % (
                metadata,
                e,
            )
        )

    try:
        elements = metadatadom.getElementsByTagName(element)
        if not elements:
            return values
    except NotFoundErr:
        return values

    try:
        for _element in elements:
            node = _element.getElementsByTagName(tag)

            try:
                values.append(node[0].childNodes[0].data)
            except IndexError:
                pass
    except NotFoundErr:
        raise NotFoundErr("%s: Malformed input: missing 'flag' tag(s)" % (metadata))

    metadatadom.unlink()
    return values


def is_maintainer(maintainer, metadata):
    data = []

    if maintainer == None:
        return True

    mtainer = maintainer.split(",")

    data = _get_metadata(metadata, "maintainer", "email")

    if not data and len(maintainer) == 0:
        return True
    elif not data and len(maintainer) > 0:
        return False
    else:
        for addy in data:
            for contact in mtainer:
                if addy == contact:
                    return True
                if addy.startswith(contact):
                    return True
    return False


# fetch a list of arch (just stable) packages
# -* is important to be sure that just arch is used
def get_packages(conf):
    _pkgs = {}

    _portage_settings(
        "ACCEPT_KEYWORDS", ("-* %s" % str(conf["TARGET_ARCH"])), conf["portdb"].settings
    )

    for cp in conf["portdb"].dbapi.cp_all():
        cpvrs = []
        slots = {}

        if conf["USER_PKGS"]:
            if not cp in conf["USER_PKGS"] and not basename(cp) in conf["USER_PKGS"]:
                continue

        # None is important to match also on empty string
        if conf["MAINTAINER"] != None:
            if not is_maintainer(
                conf["MAINTAINER"], join(conf["PORTDIR"], cp, "metadata.xml")
            ):
                continue

        cpvrs = conf["portdb"].dbapi.match(cp)

        for cpvr in cpvrs:
            slot = conf["portdb"].dbapi.aux_get(cpvr, ["SLOT"])[0]
            if not slot in slots:
                slots[slot] = []
            slots[slot].append(cpvr)

        for slot in sorted(slots):
            cpvr = portage.versions.best(slots[slot])

            if cpvr:
                (cat, pkg, ver, rev) = portage.versions.catpkgsplit(cpvr)

                if not cat in list(_pkgs.keys()):
                    _pkgs[cat] = {}
                if not pkg in list(_pkgs[cat].keys()):
                    _pkgs[cat][pkg] = []

                if rev != "r0":
                    ver = f"{ver}-{rev}"

                _pkgs[cat][pkg].append(ver)

    return _pkgs


# compare get_packages() against MAIN_ARCH


def get_imlate(conf, pkgs):
    _portage_settings(
        "ACCEPT_KEYWORDS", ("-* %s" % str(conf["MAIN_ARCH"])), conf["portdb"].settings
    )

    stable = str(conf["MAIN_ARCH"].lstrip("~"))
    testing = "~%s" % stable
    exclude = "-%s" % stable
    exclude_all = "-*"

    imlate = {}

    for cat in sorted(pkgs.keys()):
        for pkg in sorted(pkgs[cat].keys()):
            for vr in pkgs[cat][pkg]:
                cpvr = ""
                abs_pkg = ""
                kwds = ""
                our = ""
                our_ver = ""
                mtime = 0
                slot = 0

                # 0 = none(default), 1 = testing(~arch), 2 = stable(arch),
                # 3 = exclude(-arch), 4 = exclude_all(-*)
                # -* would be overridden by ~arch or arch
                kwd_type = 0

                cpvr = f"{cat}/{pkg}-{vr}"

                # absolute ebuild path for mtime check
                abs_pkg = join(conf["PORTDIR"], cat, pkg, basename(cpvr))
                abs_pkg = "%s.ebuild" % str(abs_pkg)

                kwds = conf["portdb"].dbapi.aux_get(cpvr, ["KEYWORDS"])[0]

                # FIXME: %s is bad.. maybe even cast it, else there are issues because its unicode
                slot = ":%s" % conf["portdb"].dbapi.aux_get(cpvr, ["SLOT"])[0]
                if slot == ":0":
                    slot = ""

                # sorted() to keep the right order
                # e.g. -* first, -arch second, arch third and ~arch fourth
                # -* -foo ~arch
                # example: -* would be overridden by ~arch
                for kwd in sorted(kwds.split()):
                    if kwd == stable:
                        kwd_type = 2
                        break
                    elif kwd == exclude:
                        kwd_type = 3
                        break
                    elif kwd == exclude_all:
                        kwd_type = 4
                    elif kwd == testing:
                        kwd_type = 1
                        break

                # ignore -arch and already stabilized packages
                if kwd_type == 3 or kwd_type == 2:
                    continue
                # drop packages with -* and without ~arch or arch
                # even if there is another version which includes arch or ~arch
                if kwd_type == 4:
                    continue
                # drop "stable candidates" with mtime < 30 days
                # Shall we use gmtime/UTC here?
                if kwd_type == 1:
                    mtime = int((time() - stat(abs_pkg).st_mtime) / 60 / 60 / 24)
                    if mtime < conf["MTIME"]:
                        continue

                # look for an existing stable version
                our = portage.versions.best(
                    conf["portdb"].dbapi.match(f"{cat}/{pkg}{slot}")
                )
                if our:
                    _foo = portage.versions.pkgsplit(our)
                    our_ver = _foo[1]
                    if _foo[2] != "r0":
                        our_ver = f"{our_ver}-{_foo[2]}"
                else:
                    our_ver = ""

                # we just need the version if > our_ver
                if our_ver:
                    if portage.versions.vercmp(our_ver, vr) >= 0:
                        continue

                if kwd_type == 1 and conf["STABLE"]:
                    imlate = _add_ent(imlate, cat, (f"{pkg}{slot}"), vr, our_ver)
                    conf["STABLE_SUM"] += 1
                elif kwd_type == 0 and conf["KEYWORD"]:
                    conf["KEYWORD_SUM"] += 1
                    imlate = _add_ent(imlate, cat, (f"~{pkg}{slot}"), vr, our_ver)

    return imlate


# fetch portage related settings


def get_settings(conf=None):
    if not isinstance(conf, dict) and conf:
        raise TypeError("conf must be dict() or None")
    if not conf:
        conf = {}

    # TODO: maybe we should improve it a bit ;)
    mysettings = portage.config(
        config_incrementals=portage.const.INCREMENTALS, local_config=False
    )

    if conf["MAIN_ARCH"] == "auto":
        conf["MAIN_ARCH"] = "%s" % mysettings["ACCEPT_KEYWORDS"].split(" ")[0].lstrip(
            "~"
        )
    if conf["TARGET_ARCH"] == "auto":
        conf["TARGET_ARCH"] = "~%s" % mysettings["ACCEPT_KEYWORDS"].split(" ")[
            0
        ].lstrip("~")

    # TODO: exclude overlay categories from check
    if conf["CATEGORIES"]:
        _mycats = []
        for _cat in conf["CATEGORIES"].split(","):
            _cat = _cat.strip()
            _mycats.append(_cat)
            if _cat not in mysettings.categories:
                raise ValueError("invalid category for -C switch '%s'" % _cat)
        mysettings.categories = _mycats

    # maybe thats not necessary because we override porttrees below..
    _portage_settings("PORTDIR_OVERLAY", "", mysettings)
    trees = portage.create_trees()
    trees["/"]["porttree"].settings = mysettings
    portdb = trees["/"]["porttree"]
    portdb.dbapi.settings = mysettings
    portdb.dbapi.porttrees = [portage.portdb.porttree_root]
    # does it make sense to remove _all_ useless stuff or just leave it as it is?
    # portdb.dbapi._aux_cache_keys.clear()
    # portdb.dbapi._aux_cache_keys.update(["EAPI", "KEYWORDS", "SLOT"])

    conf["PORTDIR"] = portage.settings["PORTDIR"]
    conf["portdb"] = portdb

    return conf


# just for standalone
def main():
    conf = {}
    pkgs = {}

    parser = OptionParser(version="%prog " + __version__)
    parser.usage = "%prog [options] [category/package] ..."
    parser.disable_interspersed_args()

    parser.add_option(
        "-f",
        "--file",
        dest="filename",
        action="store",
        type="string",
        help="write result into FILE [default: %default]",
        metavar="FILE",
        default="stdout",
    )
    parser.add_option(
        "-m",
        "--main",
        dest="main_arch",
        action="store",
        type="string",
        help="set main ARCH (e.g. your arch) [default: %default]",
        metavar="ARCH",
        default=MAIN_ARCH,
    )
    parser.add_option(
        "-t",
        "--target",
        dest="target_arch",
        action="store",
        type="string",
        help="set target ARCH (e.g. x86) [default: %default]",
        metavar="ARCH",
        default=TARGET_ARCH,
    )
    parser.add_option(
        "--mtime",
        dest="mtime",
        action="store",
        type="int",
        help="set minimum MTIME in days [default: %default]",
        metavar="MTIME",
        default=30,
    )

    # TODO: leave a good comment here (about True/False) :)
    parser.add_option(
        "-s",
        "--stable",
        dest="stable",
        action="store_true",
        default=False,
        help="just show stable candidates (e.g. -s and -k is the default result) [default: True]",
    )
    parser.add_option(
        "-k",
        "--keyword",
        dest="keyword",
        action="store_true",
        default=False,
        help="just show keyword candidates (e.g. -s and -k is the default result) [default: True]",
    )

    parser.add_option(
        "-M",
        "--maintainer",
        dest="maintainer",
        action="store",
        type="string",
        help="Show only packages from the specified maintainer",
        metavar="MAINTAINER",
        default=None,
    )

    parser.add_option(
        "-C",
        "--category",
        "--categories",
        dest="categories",
        action="store",
        default=None,
        metavar="CATEGORIES",
        help="just check in the specified category/categories (comma separated) [default: %default]",
    )

    (options, args) = parser.parse_args()

    if len(args) > 0:
        conf["USER_PKGS"] = args
    else:
        conf["USER_PKGS"] = []

    # cleanup optparse
    try:
        parser.destroy()
    except AttributeError:
        # to be at least python 2.4 compatible
        del parser._short_opt
        del parser._long_opt
        del parser.defaults

    # generated timestamp (UTC)
    conf["TIME"] = strftime("%a %b %d %H:%M:%S %Z %Y", gmtime())

    # package counter
    conf["KEYWORD_SUM"] = 0
    conf["STABLE_SUM"] = 0

    if not options.main_arch in portage.archlist and options.main_arch != "auto":
        raise ValueError("invalid MAIN ARCH defined!")
    if not options.target_arch in portage.archlist and options.target_arch != "auto":
        raise ValueError("invalid TARGET ARCH defined!")

    conf["MAIN_ARCH"] = options.main_arch
    conf["TARGET_ARCH"] = options.target_arch

    conf["FILE"] = options.filename
    conf["MTIME"] = options.mtime

    if not options.stable and not options.keyword:
        conf["STABLE"] = True
        conf["KEYWORD"] = True
    else:
        conf["STABLE"] = options.stable
        conf["KEYWORD"] = options.keyword

    conf["CATEGORIES"] = options.categories

    conf["MAINTAINER"] = options.maintainer

    # append to our existing
    conf = get_settings(conf)
    pkgs = get_packages(conf)
    pkgs = get_imlate(conf, pkgs)

    show_result(conf, pkgs)


if __name__ == "__main__":
    main()
