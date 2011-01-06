# Copyright(c) 2004-2009, Gentoo Foundation
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
	'GentoolkitNoMatches',
	'GentoolkitSetNotFound',
	'GentoolkitUnknownKeyword',
	'GentoolkitNonZeroExit'
)

# ==========
# Exceptions
# ==========

class GentoolkitException(Exception):
	"""Base class for gentoolkit exceptions."""
	def __init__(self, is_serious=True):
		self.is_serious = is_serious


class GentoolkitFatalError(GentoolkitException):
	"""A fatal error occurred. Usually used to catch Portage exceptions."""
	def __init__(self, err, is_serious=True):
		GentoolkitException.__init__(self, is_serious=is_serious)
		self.err = err

	def __str__(self):
		return "Fatal error: %s" % self.err


class GentoolkitAmbiguousPackage(GentoolkitException):
	"""Got an ambiguous package name."""
	def __init__(self, choices, is_serious=False):
		GentoolkitException.__init__(self, is_serious=is_serious)
		self.choices = choices

	def __str__(self):
		choices = '\n'.join("  %s" % x for x in self.choices)
		return '\n'.join(("Ambiguous package name. Choose from:", choices))


class GentoolkitInvalidAtom(GentoolkitException):
	"""Got a malformed package atom."""
	def __init__(self, atom, is_serious=False):
		GentoolkitException.__init__(self, is_serious=is_serious)
		self.atom = atom

	def __str__(self):
		return "Invalid atom: '%s'" % self.atom


class GentoolkitSetNotFound(GentoolkitException):
	"""Got unknown set."""
	def __init__(self, setname, is_serious=False):
		GentoolkitException.__init__(self, is_serious=is_serious)
		self.setname = setname

	def __str__(self):
		return "Unknown set: '%s'" % self.setname


class GentoolkitInvalidCategory(GentoolkitException):
	"""The category was not listed in portage.settings.categories."""
	def __init__(self, category, is_serious=False):
		GentoolkitException.__init__(self, is_serious=is_serious)
		self.category = category

	def __str__(self):
		return "Invalid category: '%s'" % self.category


class GentoolkitInvalidPackage(GentoolkitException):
	"""Got an unknown or invalid package."""
	def __init__(self, package, is_serious=False):
		GentoolkitException.__init__(self, is_serious=is_serious)
		self.package = package

	def __str__(self):
		return "Invalid package: '%s'" % self.package


class GentoolkitInvalidCPV(GentoolkitException):
	"""Got an invalid category/package-ver string."""
	def __init__(self, cpv, is_serious=False):
		GentoolkitException.__init__(self, is_serious=is_serious)
		self.cpv = cpv

	def __str__(self):
		return "Invalid CPV: '%s'" % self.cpv


class GentoolkitInvalidRegex(GentoolkitException):
	"""The regex could not be compiled."""
	def __init__(self, regex, is_serious=False):
		GentoolkitException.__init__(self, is_serious=is_serious)
		self.regex = regex

	def __str__(self):
		return "Invalid regex: '%s'" % self.regex


class GentoolkitInvalidVersion(GentoolkitException):
	"""Got a malformed version."""
	def __init__(self, version, is_serious=False):
		GentoolkitException.__init__(self, is_serious=is_serious)
		self.version = version

	def __str__(self):
		return "Malformed version: '%s'" % self.version


class GentoolkitNoMatches(GentoolkitException):
	"""No packages were found matching the search query."""
	def __init__(self, query, in_installed=False, is_serious=False):
		GentoolkitException.__init__(self, is_serious=is_serious)
		self.query = query
		self.in_installed = in_installed

	def __str__(self):
		inst = 'installed ' if self.in_installed else ''
		return "No %spackages matching '%s'" % (inst, self.query)


class GentoolkitUnknownKeyword(GentoolkitException):
	"""No packages were found matching the search query."""
	def __init__(self, query, keywords, use, is_serious=True):
		GentoolkitException.__init__(self, is_serious=is_serious)
		self.query = query
		self.keywords = keywords
		self.use = use

	def __str__(self):
		return ("Unable to determine the install keyword for:\n" +
			"'%s', KEYWORDS = '%s'\nUSE flags = '%s'"
			% (self.query, self.keywords, self.use))


class GentoolkitNonZeroExit(GentoolkitException):
	"""Used to signal, that a non-fatal, no warning error occurred.
	   The primary use case is for not returning any data."""
	def __init__(self, return_code=1, is_serious=False):
		GentoolkitException.__init__(self, is_serious=is_serious)
		self.return_code = return_code

# vim: set ts=4 sw=4 tw=79:
