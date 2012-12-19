# Copyright(c) 2005 Jason Stubbs <jstubbs@gentoo.org>
# Copyright(c) 2005-2006 Brian Harring <ferringb@gmail.com>
# Copyright(c) 2009-2010 Gentoo Foundation
#
# Licensed under the GNU General Public License, v2
#
# $Header$

"""Provides attributes and methods for a category/package-version string."""

__all__ = (
	'CPV',
	'compare_strs',
	'split_cpv'
)

# =======
# Imports
# =======

import re

from portage.versions import catpkgsplit, vercmp, pkgcmp

from gentoolkit import errors

# =======
# Globals
# =======

isvalid_version_re = re.compile("^(?:cvs\\.)?(?:\\d+)(?:\\.\\d+)*[a-z]?"
	"(?:_(p(?:re)?|beta|alpha|rc)\\d*)*$")
isvalid_cat_re = re.compile("^(?:[a-zA-Z0-9][-a-zA-Z0-9+._]*(?:/(?!$))?)+$")
_pkg_re = re.compile("^[a-zA-Z0-9+._]+$")
# Prefix specific revision is of the form -r0<digit>+.<digit>+
isvalid_rev_re = re.compile(r'(\d+|0\d+\.\d+)')

# =======
# Classes
# =======

class CPV(object):
	"""Provides methods on a category/package-version string.

	Will also correctly split just a package or package-version string.

	Example usage:
		>>> from gentoolkit.cpv import CPV
		>>> cpv = CPV('sys-apps/portage-2.2-r1')
		>>> cpv.category, cpv.name, cpv.fullversion
		('sys-apps', 'portage', '2.2-r1')
		>>> str(cpv)
		'sys-apps/portage-2.2-r1'
		>>> # An 'rc' (release candidate) version is less than non 'rc' version:
		... CPV('sys-apps/portage-2') > CPV('sys-apps/portage-2_rc10')
		True
	"""

	def __init__(self, cpv, validate=False):
		self.cpv = cpv
		self._category = None
		self._name = None
		self._version = None
		self._revision = None
		self._cp = None
		self._fullversion = None

		self.validate = validate
		if validate and not self.name:
			raise errors.GentoolkitInvalidCPV(cpv)

	@property
	def category(self):
		if self._category is None:
			self._set_cpv_chunks()
		return self._category

	@property
	def name(self):
		if self._name is None:
			self._set_cpv_chunks()
		return self._name

	@property
	def version(self):
		if self._version is None:
			self._set_cpv_chunks()
		return self._version

	@property
	def revision(self):
		if self._revision is None:
			self._set_cpv_chunks()
		return self._revision

	@property
	def cp(self):
		if self._cp is None:
			sep = '/' if self.category else ''
			self._cp = sep.join((self.category, self.name))
		return self._cp

	@property
	def fullversion(self):
		if self._fullversion is None:
			sep = '-' if self.revision else ''
			self._fullversion = sep.join((self.version, self.revision))
		return self._fullversion

	def _set_cpv_chunks(self):
		chunks = split_cpv(self.cpv, validate=self.validate)
		self._category = chunks[0]
		self._name = chunks[1]
		self._version = chunks[2]
		self._revision = chunks[3]

	def __eq__(self, other):
		if not isinstance(other, self.__class__):
			return False
		return self.cpv == other.cpv

	def __hash__(self):
		return hash(self.cpv)

	def __ne__(self, other):
		return not self == other

	def __lt__(self, other):
		if not isinstance(other, self.__class__):
			raise TypeError("other isn't of %s type, is %s" % (
				self.__class__, other.__class__)
			)

		if self.category != other.category:
			return self.category < other.category
		elif self.name != other.name:
			return self.name < other.name
		else:
			# FIXME: this cmp() hack is for vercmp not using -1,0,1
			# See bug 266493; this was fixed in portage-2.2_rc31
			#return vercmp(self.fullversion, other.fullversion)
			return vercmp(self.fullversion, other.fullversion) < 0

	def __gt__(self, other):
		if not isinstance(other, self.__class__):
			raise TypeError("other isn't of %s type, is %s" % (
				self.__class__, other.__class__)
			)
		return not self <= other

	def __le__(self, other):
		if not isinstance(other, self.__class__):
			raise TypeError("other isn't of %s type, is %s" % (
				self.__class__, other.__class__)
			)
		return self < other or self == other

	def __ge__(self, other):
		if not isinstance(other, self.__class__):
			raise TypeError("other isn't of %s type, is %s" % (
				self.__class__, other.__class__)
			)
		return self > other or self == other

	def __repr__(self):
		return "<%s %r>" % (self.__class__.__name__, str(self))

	def __str__(self):
		return self.cpv


# =========
# Functions
# =========

def compare_strs(pkg1, pkg2):
	"""Similar to the builtin cmp, but for package strings. Usually called
	as: package_list.sort(cpv.compare_strs)

	An alternative is to use the CPV descriptor from gentoolkit.cpv:
	>>> package_list = ['sys-apps/portage-9999', 'media-video/ffmpeg-9999']
	>>> cpvs = sorted(CPV(x) for x in package_list)

	@see: >>> help(cmp)
	"""

	pkg1 = catpkgsplit(pkg1)
	pkg2 = catpkgsplit(pkg2)
	if pkg1[0] != pkg2[0]:
		return -1 if pkg1[0] < pkg2[0] else 1
	elif pkg1[1] != pkg2[1]:
		return -1 if pkg1[1] < pkg2[1] else 1
	else:
		return pkgcmp(pkg1[1:], pkg2[1:])


def split_cpv(cpv, validate=True):
	"""Split a cpv into category, name, version and revision.

	Modified from pkgcore.ebuild.cpv

	@type cpv: str
	@param cpv: pkg, cat/pkg, pkg-ver, cat/pkg-ver
	@rtype: tuple
	@return: (category, pkg_name, version, revision)
		Each tuple element is a string or empty string ("").
	"""

	category = name = version = revision = ''

	try:
		category, pkgver = cpv.rsplit("/", 1)
	except ValueError:
		pkgver = cpv
	if validate and category and not isvalid_cat_re.match(category):
		raise errors.GentoolkitInvalidCPV(cpv)
	pkg_chunks = pkgver.split("-")
	lpkg_chunks = len(pkg_chunks)
	if lpkg_chunks == 1:
		return (category, pkg_chunks[0], version, revision)
	if isvalid_rev(pkg_chunks[-1]):
		if lpkg_chunks < 3:
			# needs at least ('pkg', 'ver', 'rev')
			raise errors.GentoolkitInvalidCPV(cpv)
		rev = pkg_chunks.pop(-1)
		if rev:
			revision = rev

	if isvalid_version_re.match(pkg_chunks[-1]):
		version = pkg_chunks.pop(-1)

	if not isvalid_pkg_name(pkg_chunks):
		raise errors.GentoolkitInvalidCPV(cpv)
	name = '-'.join(pkg_chunks)

	return (category, name, version, revision)


def isvalid_pkg_name(chunks):
	if not chunks[0]:
		# this means a leading -
		return False
	mf = _pkg_re.match
	if not all(not s or mf(s) for s in chunks):
		return False
	if chunks[-1].isdigit() or not chunks[-1]:
		# not allowed.
		return False
	return True


def isvalid_rev(s):
	return s and s[0] == 'r' and isvalid_rev_re.match(s[1:])

# vim: set ts=4 sw=4 tw=79:
