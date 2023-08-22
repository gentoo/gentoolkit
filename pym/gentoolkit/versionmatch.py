#! /usr/bin/python
#
# Copyright(c) 2009 Gentoo Foundation
# Licensed under the GNU General Public License, v2
#
# Copyright: 2005-2007 Brian Harring <ferringb@gmail.com>
# License: GPL2/BSD

"""Gentoo version comparison object from pkgcore.ebuild.atom_restricts."""

# =======
# Imports
# =======

from portage.versions import vercmp

from gentoolkit import errors
from gentoolkit.cpv import CPV

# =======
# Classes
# =======


class VersionMatch:
    """Gentoo version comparison object from pkgcore.ebuild.atom_restricts.

    Any overriding of this class *must* maintain numerical order of
    self.vals, see intersect for reason why. vals also must be a tuple.
    """

    _convert_op2int = {(-1,): "<", (-1, 0): "<=", (0,): "=", (0, 1): ">=", (1,): ">"}

    _convert_int2op = {v: k for k, v in _convert_op2int.items()}

    def __init__(self, cpv, op="="):
        """Initialize a VersionMatch instance.

        @type cpv: L{gentoolkit.cpv.CPV}
        @param cpv: cpv object
        @type op: str
        @keyword op: operator
        """

        if not isinstance(cpv, (CPV, self.__class__)):
            err = "cpv must be a gentoolkit.cpv.CPV "
            err += "or gentoolkit.versionmatch.VersionMatch instance"
            raise ValueError(err)
        self.cpv = cpv
        self.operator = op
        self.version = cpv.version
        self.revision = cpv.revision
        self.fullversion = cpv.fullversion

        if self.operator != "~" and self.operator not in self._convert_int2op:
            raise errors.GentoolkitInvalidVersion(
                "invalid operator '%s'" % self.operator
            )

        if self.operator == "~":
            if not self.version:
                raise errors.GentoolkitInvalidVersion("for ~ op, ver must be specified")
            self.droprevision = True
            self.values = (0,)
        else:
            self.droprevision = False
            self.values = self._convert_int2op[self.operator]

    def match(self, other):
        """See whether a passed in VersionMatch or CPV instance matches self.

        Example usage:
                >>> from gentoolkit.versionmatch import VersionMatch
                >>> from gentoolkit.cpv import CPV
                >>> VersionMatch(CPV('foo/bar-1.5'), op='>').match(
                ... VersionMatch(CPV('foo/bar-2.0')))
                True

        @type other: gentoolkit.versionmatch.VersionMatch OR
           gentoolkit.cpv.CPV
        @param other: version to compare with self's version
        @rtype: bool
        """

        if self.droprevision:
            ver1, ver2 = self.version, other.version
        else:
            ver1, ver2 = self.fullversion, other.fullversion

        return vercmp(ver2, ver1) in self.values

    def __str__(self):
        operator = self._convert_op2int[self.values]

        if self.droprevision or not self.revision:
            return f"ver {operator} {self.version}"
        return f"ver-rev {operator} {self.version}-{self.revision}"

    def __repr__(self):
        return f"<{self.__class__.__name__} {str(self)!r}>"

    @staticmethod
    def _convert_ops(inst):
        if inst.droprevision:
            return inst.values
        return tuple(sorted({-1, 0, 1}.difference(inst.values)))

    def __eq__(self, other):
        if self is other:
            return True
        if isinstance(other, self.__class__):
            if (
                self.droprevision != other.droprevision
                or self.version != other.version
                or self.revision != other.revision
            ):
                return False
            return self._convert_ops(self) == self._convert_ops(other)

        return False

    def __ne__(self, other):
        return not self == other

    def __hash__(self):
        return hash((self.droprevision, self.version, self.revision, self.values))


# vim: set ts=4 sw=4 tw=79:
