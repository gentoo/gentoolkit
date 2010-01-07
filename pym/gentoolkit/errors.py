# Copyright(c) 2004-2010, Gentoo Foundation
#
# Licensed under the GNU General Public License, v2 or later

"""Exception classes for gentoolkit"""

__all__ = (
	'GentoolkitException',
	'GentoolkitFatalError',
	'GentoolkitAmbiguousPackage',
	'GentoolkitInvalidAtom',
	'GentoolkitInvalidCategory',
	'GentoolkitInvalidPackage',
	'GentoolkitInvalidCPV',
	'GentoolkitInvalidRegex',
	'GentoolkitInvalidVersion',
	'GentoolkitNoMatches'
)

# ==========
# Exceptions
# ==========

class GentoolkitException(Exception):
	"""Base class for gentoolkit exceptions."""
	def __init__(self):
		pass


class GentoolkitFatalError(GentoolkitException):
	"""A fatal error occurred. Usually used to catch Portage exceptions."""
	def __init__(self, err):
		self.err = err

	def __str__(self):
		return "Fatal error: %s" % self.err


class GentoolkitAmbiguousPackage(GentoolkitException):
	"""Got an ambiguous package name."""
	def __init__(self, choices):
		self.choices = choices

	def __str__(self):
		choices = '\n'.join("  %s" % x for x in self.choices)
		return '\n'.join(("Ambiguous package name. Choose from:", choices))


class GentoolkitInvalidAtom(GentoolkitException):
	"""Got a malformed package atom."""
	def __init__(self, atom):
		self.atom = atom

	def __str__(self):
		return "Invalid atom: '%s'" % self.atom


class GentoolkitInvalidCategory(GentoolkitException):
	"""The category was not listed in portage.settings.categories."""
	def __init__(self, category):
		self.category = category

	def __str__(self):
		return "Invalid category: '%s'" % self.category


class GentoolkitInvalidPackage(GentoolkitException):
	"""Got an unknown or invalid package."""
	def __init__(self, package):
		self.package = package

	def __str__(self):
		return "Invalid package: '%s'" % self.package


class GentoolkitInvalidCPV(GentoolkitException):
	"""Got an invalid category/package-ver string."""
	def __init__(self, cpv):
		self.cpv = cpv

	def __str__(self):
		return "Invalid CPV: '%s'" % self.cpv


class GentoolkitInvalidRegex(GentoolkitException):
	"""The regex could not be compiled."""
	def __init__(self, regex):
		self.regex = regex

	def __str__(self):
		return "Invalid regex: '%s'" % self.regex


class GentoolkitInvalidVersion(GentoolkitException):
	"""Got a malformed version."""
	def __init__(self, version):
		self.version = version

	def __str__(self):
		return "Malformed version: '%s'" % self.version


class GentoolkitNoMatches(GentoolkitException):
	"""No packages were found matching the search query."""
	def __init__(self, query, in_installed=False):
		self.query = query
		self.in_installed = in_installed

	def __str__(self):
		inst = 'installed ' if self.in_installed else ''
		return "No %spackages matching '%s'" % (inst, self.query)


# vim: set ts=4 sw=4 tw=79:
