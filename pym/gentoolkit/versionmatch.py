#! /usr/bin/python
#
# Copyright(c) 2009, Gentoo Foundation
# Licensed under the GNU General Public License, v2
#
# Copyright: 2005-2007 Brian Harring <ferringb@gmail.com>
# License: GPL2/BSD
#
# $Header$

"""Gentoo package version comparison object from pkgcore.ebuild.atom_restricts.

The VersionMatch class allows you to compare package versions according to
Gentoo's versioning rules.

The simplest way to use it is to test simple equality. In this example I've
passed in the keyword arguments op (operator), ver (version), and
rev (revision) explicitly:
>>> from gentoolkit.versionmatch import VersionMatch
>>> VersionMatch(op='=',ver='1',rev='') == VersionMatch(op='=',ver='1',rev='')
True
>>> VersionMatch(op='=',ver='1',rev='') == VersionMatch(op='=',ver='2',rev='')
False

A more flexible way to use it is to pass it a single gentoolkit.package.Package
instance which it uses to determine op, ver and rev:
>>> from gentoolkit.package import Package
>>> from gentoolkit.versionmatch import VersionMatch
>>> pkg1 = Package('sys-apps/portage-2.2')                 
>>> pkg2 = Package('sys-apps/portage-1.6')
>>> VersionMatch(pkg1) == VersionMatch(pkg2)
False

Simple equality tests aren't actually very useful because they don't understand
different operators:
>>> VersionMatch(op='>', ver='1.5', rev='') == \
... VersionMatch(op='=', ver='2', rev='')
False

For more complicated comparisons, we can use the match method:
>>> from gentoolkit.package import Package
>>> from gentoolkit.versionmatch import VersionMatch
>>> pkg1 = Package('>=sys-apps/portage-2.2')
>>> pkg2 = Package('=sys-apps/portage-2.2_rc30')
>>> # An "rc" (release candidate) version compares less than a non "rc" version
... VersionMatch(pkg1).match(pkg2)
False
>>> pkg2 = Package('=sys-apps/portage-2.2-r6')
>>> # But an "r" (revision) version compares greater than a non "r" version
... VersionMatch(pkg1).match(pkg2)
True

@see: gentoolkit.equery.changes for examples of use in gentoolkit.
@see: gentoolkit.package.Package.intersects for a higher level version
      comparison method.
"""

# =======
# Imports
# =======

from portage.versions import vercmp

import gentoolkit
from gentoolkit import errors

# =======
# Classes
# =======

class VersionMatch(object):
	"""Gentoo package version comparison object from pkgcore.ebuild.atom_restricts.

	Any overriding of this class *must* maintain numerical order of
	self.vals, see intersect for reason why. vals also must be a tuple.
	"""
	_convert_op2int = {(-1,):"<", (-1, 0): "<=", (0,):"=",
		(0, 1):">=", (1,):">"}

	_convert_int2op = dict([(v, k) for k, v in _convert_op2int.iteritems()])
	del k, v

	def __init__(self, *args, **kwargs):
		"""This class will either create a VersionMatch instance out of
		a Package instance, or from explicitly passed in operator, version,
		and revision.

		Takes EITHER one arg:
			<gentoolkit.package.Package> instance

			OR

		three keyword args:
			op=str: version comparison to do,
				valid operators are ('<', '<=', '=', '>=', '>', '~')
			ver=str: version to base comparison on
			rev=str: revision to base comparison on
		"""
		if args and isinstance(args[0], (gentoolkit.package.Package,
				self.__class__)):
			self.operator = args[0].operator
			self.version = args[0].version
			self.revision = args[0].revision
			self.fullversion = args[0].fullversion
		elif set(('op', 'ver', 'rev')) == set(kwargs):
			self.operator = kwargs['op']
			self.version = kwargs['ver']
			self.revision = kwargs['rev']
			if not self.revision:
				self.fullversion = self.version
			else:
				self.fullversion = "%s-%s" % (self.version, self.revision)
		else:
			raise TypeError('__init__() takes either a Package instance '
				'argument or op=, ver= and rev= all passed in as keyword args')

		if self.operator != "~" and self.operator not in self._convert_int2op:
			raise errors.GentoolkitInvalidVersion(
				"invalid operator '%s'" % self.operator)

		if self.operator == "~":
			if not self.version:
				raise errors.GentoolkitInvalidVersion(
					"for ~ op, version must be specified")
			self.droprevision = True
			self.values = (0,)
		else:
			self.droprevision = False
			self.values = self._convert_int2op[self.operator]

	def match(self, pkginst):
		"""See whether a passed in VersionMatch or Package instance matches
		self.

		Example usage:
			>>> from gentoolkit.versionmatch import VersionMatch
			>>> VersionMatch(op='>',ver='1.5',rev='').match(
			... VersionMatch(op='=',ver='2.0',rev=''))
			True

		@type pkginst: gentoolkit.versionmatch.VersionMatch OR
		               gentoolkit.package.Package
		@param pkginst: version to compare with self's version
		@rtype: bool
		"""

		if self.droprevision:
			ver1, ver2 = self.version, pkginst.version
		else:
			ver1, ver2 = self.fullversion, pkginst.fullversion

		#print "== VersionMatch.match DEBUG START =="
		#print "ver1:", ver1
		#print "ver2:", ver2
		#print "vercmp(ver2, ver1):", vercmp(ver2, ver1)
		#print "self.values:", self.values
		#print "vercmp(ver2, ver1) in values?",
		#print "vercmp(ver2, ver1) in self.values"
		#print "==  VersionMatch.match DEBUG END  =="

		return vercmp(ver2, ver1) in self.values

	def __str__(self):
		operator = self._convert_op2int[self.values]

		if self.droprevision or not self.revision:
			return "ver %s %s" % (operator, self.version)
		return "ver-rev %s %s-%s" % (operator, self.version, self.revision)

	def __repr__(self):
		return "<%s %s @%#8x>" % (self.__class__.__name__, str(self), id(self))

	@staticmethod
	def _convert_ops(inst):
		if inst.droprevision:
			return inst.values
		return tuple(sorted(set((-1, 0, 1)).difference(inst.values)))

	def __eq__(self, other):
		if self is other:
			return True
		if isinstance(other, self.__class__):
			if (self.droprevision != other.droprevision or
				self.version != other.version or
				self.revision != other.revision):
				return False
			return self._convert_ops(self) == self._convert_ops(other)

		return False

	def __hash__(self):
		return hash((self.droprevision, self.version, self.revision,
			self.values))
