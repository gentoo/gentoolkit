# Copyright(c) 2004-2009, Gentoo Foundation
#
# Licensed under the GNU General Public License, v2 or later

"""Exception classes for gentoolkit"""

__all__ = [
	'FatalError',
	'GentoolkitException',
	'GentoolkitInvalidAtom',
	'GentoolkitInvalidCategory',
	'GentoolkitInvalidPackageName',
	'GentoolkitInvalidCPV',
	'GentoolkitInvalidRegex',
	'GentoolkitInvalidVersion',
	'GentoolkitNoMatches'
]

# =======
# Imports
# =======

import sys

import gentoolkit.pprinter as pp

# ==========
# Exceptions
# ==========

class GentoolkitException(Exception):
	"""Base class for gentoolkit exceptions"""
	def __init__(self):
		pass


class GentoolkitFatalError(GentoolkitException):
	"""A fatal error occurred. Usually used to catch Portage exceptions."""
	def __init__(self, err):
		pp.print_error("Fatal error: %s" % err)
		sys.exit(2)


class GentoolkitInvalidAtom(GentoolkitException):
	"""Got a malformed package atom"""
	def __init__(self, atom):
		pp.print_error("Invalid atom: '%s'" % atom)
		sys.exit(2)


class GentoolkitInvalidCategory(GentoolkitException):
	"""The category was not listed in portage.settings.categories"""
	def __init__(self, category):
		pp.print_error("Invalid category: '%s'" % category)
		if not category:
			pp.print_error("Try --category=cat1,cat2 with no spaces.")
		sys.exit(2)


class GentoolkitInvalidPackageName(GentoolkitException):
	"""Got an unknown package name"""
	def __init__(self, package):
		pp.print_error("Invalid package name: '%s'" % package)
		sys.exit(2)


class GentoolkitInvalidCPV(GentoolkitException):
	"""Got an unknown package name"""
	def __init__(self, cpv):
		pp.print_error("Invalid CPV: '%s'" % cpv)
		sys.exit(2)


class GentoolkitInvalidRegex(GentoolkitException):
	"""The regex could not be compiled"""
	def __init__(self, regex):
		pp.print_error("Invalid regex: '%s'" % regex)
		sys.exit(2)


class GentoolkitInvalidVersion(GentoolkitException):
	"""Got a malformed version"""
	def __init__(self, version):
		pp.print_error("Malformed version: '%s'" % version)
		sys.exit(2)


class GentoolkitNoMatches(GentoolkitException):
	"""No packages were found matching the search query"""
	def __init__(self, query):
		pp.print_error("No packages matching '%s'" % query)
		sys.exit(2)


# XXX: Deprecated
class FatalError:
	def __init__(self, s):
		self._message = s
	def get_message(self):
		return self._message
