#! /usr/bin/env python2.2
#
# Copyright 2003 Karl Trygve Kalleberg
# Copyright 2003 Gentoo Technologies, Inc.
# Distributed under the terms of the GNU General Public License v2
#
# $Header$
# Author: Karl Trygve Kalleberg <karltk@gentoo.org>
#
# Portions written ripped from etcat, written by Alistair Tse <liquidx@gentoo.org>

__author__ = "Karl Trygve Kalleberg"
__email__ = "karltk@gentoo.org"
__version__ = "0.1.0"
__productname__ = "gentoolkit"
__description__ = "Gentoolkit Common Library"

import os
import portage
import re
import string

settings = portage.settings
porttree = portage.db[portage.root]["porttree"]
vartree  = portage.db[portage.root]["vartree"]

# Nomenclature:
#
# CPV - category/package-version

class Package:
    """Package descriptor. Contains convenience functions for querying the
    state of a package, its contents, name manipulation, ebuild info and
    similar."""
    def __init__(self,cpv):
        self._cpv=cpv
        self._scpv=portage.catpkgsplit(self._cpv)
        self._db=None
    def get_name(self):
        """Returns base name of package, no category nor version"""
        return self._scpv[1]
    def get_version(self):
        """Returns version of package, with revision number"""
        v=self._scpv[2]
        if self._scpv[3] != "r0":
            v+="-"+self._scpv[3]
        return v
    def get_category(self):
        """Returns category of package"""
        return self._scpv[0]
    def get_cpv(self):
        """Returns full Category/Package-Version string"""
        return self._cpv
    def get_dependants(self):
        """Retrieves a list of CPVs for all packages depending on this one"""
        raise "Not implemented!"
    def get_compiletime_dependencies(self):
        """Returns a list of first-level compile time dependencies for this package"""
        raise "Not implemented!"
    def get_runtime_dependencies(self):
        """Returns a list of first-level run time dependencies for this package"""
        raise "Not implemented!"
    def is_installed(self):
        """Returns true if this package is installed (merged)"""
        self._initdb()
        return os.path.exists(self._db.getpath())
    def is_overlay(self):
        dir,ovl=portage.portdb.findname2(self._cpv)
        return ovl
    def is_masked(self):
        """Returns true if this package is masked against installation. Note: We blindly assume that
        the package actually exists on disk somewhere."""
        unmasked = portage.portdb.xmatch("match-visible", "=" + self._cpv)
        return self._cpv not in unmasked
    def get_ebuild_path(self):
        """Returns the complete path to the .ebuild file"""
        return portage.portdb.findname(self._cpv)
    def get_package_path(self):
        """Returns the path to where the ChangeLog, Manifest, .ebuild files reside"""
        p=self.get_ebuild_path()
        sp=p.split("/")
        if len(sp):
            return string.join(sp[:-1],"/")
    def get_env_var(self, var):
        """Returns one of the predefined env vars DEPEND, RDEPEND, SRC_URI,...."""
        r=porttree.dbapi.aux_get(self._cpv,[var])
        if len(r)!=1:
            raise "Should only get one element!"
        return r[0]
    def get_contents(self):
        """Returns the full contents, as a dictionary, on the form
        [ '/bin/foo' : [ 'obj', '1052505381', '45ca8b8975d5094cd75bdc61e9933691' ], ... ]"""
        self._initdb()
        if self.is_installed():
            return self._db.getcontents()
        return {}        
    def compare_version(self,other):
        """Compares this package's version to another's CPV; returns -1, 0, 1"""
        v1=self._scpv
        v2=portage.catpkgsplit(other)
        if v1[0] != v2[0] or v1[1] != v2[1]:
            return None
        return portage.pkgcmp(v1[1:],v2[1:])
    def size(self):
        contents = self.get_contents()
        size=0
        uncounted = 0
        files=0
        for x in contents:
            try:
                size += os.stat(x).st_size
                files += 1
            except OSError:
                uncounted += 1
        return [self.get_cpv(), size, files, uncounted]

    def _initdb(self):
        """Internal helper function; loads package information from disk,
        when necessary"""
        if not self._db:
            cat=self.get_category()
            pnv=self.get_name()+"-"+self.get_version()
            self._db=portage.dblink(cat,pnv,"")
#
# Should we add stuff like size, depends, files, here?
#
#

def find_packages(search_key):
    """Returns a list of Package objects that matched the search key."""
    # FIXME: this one failes if search_key contains version suffix
    t=portage.portdb.match(search_key)
    return map(lambda x: Package(x), t)

def find_all_packages(prefilter=None):
    """Returns a list of all known packages, installed or not."""
    t=portage.portdb.cp_all()
    if prefilter:
        t=filter(prefilter,t)
    t2=[]
    for x in t:
        t2 += portage.portdb.cp_list(x)
    return map(lambda x: Package(x), t2)

if __name__ == "__main__":
    print "This module is for import only"

# - get dependencies
# - walk dependency tree

