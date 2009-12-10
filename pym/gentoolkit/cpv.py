#!/usr/bin/python
#
# Copyright(c) 2009, Gentoo Foundation
#
# Licensed under the GNU General Public License, v2
#
# $Header$

"""Provides attributes and methods for a category/package-version string."""

__all__ = ('CPV',)

# =======
# Imports
# =======

from portage.versions import catpkgsplit, vercmp

from gentoolkit import errors

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
	"""

	def __init__(self, cpv):
		if not cpv:
			raise errors.GentoolkitInvalidCPV(cpv)
		self.scpv = cpv

		values = split_cpv(cpv)
		self.category = values[0]
		self.name = values[1]
		self.version = values[2]
		self.revision = values[3]
		del values

		if not self.name:
			raise errors.GentoolkitInvalidCPV(cpv)

		sep = '/' if self.category else ''
		self.cp = sep.join((self.category, self.name))

		sep = '-' if self.revision else ''
		self.fullversion = sep.join((self.version, self.revision))
		del sep

	def __eq__(self, other):
		if not isinstance(other, self.__class__):
			raise TypeError("other isn't of %s type, is %s" % (
				self.__class__, other.__class__)
			)
		return self.scpv == other.scpv

	def __ne__(self, other):
		if not isinstance(other, self.__class__):
			raise TypeError("other isn't of %s type, is %s" % (
				self.__class__, other.__class__)
			)
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
			result = cmp(vercmp(self.fullversion, other.fullversion), 0)
			if result == -1:
				return True
			else:
				return False

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
		return self.scpv


# =========
# Functions
# =========

def split_cpv(cpv):
	"""Split a cpv into category, name, version and revision.

	Inlined from helpers because of circular imports.

	@type cpv: str
	@param cpv: pkg, cat/pkg, pkg-ver, cat/pkg-ver, atom or regex
	@rtype: tuple
	@return: (category, pkg_name, version, revision)
		Each tuple element is a string or empty string ("").
	"""

	result = catpkgsplit(cpv)

	if result:
		result = list(result)
		if result[0] == 'null':
			result[0] = ''
		if result[3] == 'r0':
			result[3] = ''
	else:
		result = cpv.split("/")
		if len(result) == 1:
			result = ['', cpv, '', '']
		else:
			result = result + ['', '']

	return tuple(result)

# vim: set ts=4 sw=4 tw=79:
