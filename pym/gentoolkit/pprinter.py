#!/usr/bin/python
#
# Copyright 2004 Karl Trygve Kalleberg <karltk@gentoo.org>
# Copyright 2004-2009 Gentoo Foundation
# Distributed under the terms of the GNU General Public License v2
#
# $Header$

"""Provides a consistent color scheme for Gentoolkit scripts."""

__all__ = (
	'command',
	'cpv',
	'die',
	'emph',
	'error',
	'globaloption',
	'installedflag',
	'localoption',
	'number',
	'path',
	'path_symlink',
	'pkgquery',
	'productname',
	'regexpquery',
	'section',
	'slot',
	'subsection',
	'useflag',
	'warn'
)

# =======
# Imports
# =======

import sys
import locale
import codecs

import portage.output as output
from portage import archlist

# =========
# Functions
# =========

# output creates color functions on the fly, which confuses pylint.
# E1101: *%s %r has no %r member*
# pylint: disable-msg=E1101

def command(string):
	"""Returns a program command string."""
	return output.green(string)

def cpv(string):
	"""Returns a category/package-<version> string."""
	return output.green(string)

def die(err, string):
	"""Returns an error string and die with an error code."""
	sys.stderr.write(error(string))
	sys.exit(err)

def emph(string):
	"""Returns a string as emphasized."""
	return output.bold(string)

def error(string):
	"""Prints an error string."""
	return output.red("!!! ") + string + "\n"

def globaloption(string):
	"""Returns a global option string, i.e. the program global options."""
	return output.yellow(string)

def localoption(string):
	"""Returns a local option string, i.e. the program local options."""
	return output.green(string)

def number(string):
	"""Returns a number string."""
	return output.turquoise(string)

def path(string):
	"""Returns a file or directory path string."""
	return output.bold(string)

def path_symlink(string):
	"""Returns a symlink string."""
	return output.turquoise(string)

def pkgquery(string):
	"""Returns a package query string."""
	return output.bold(string)

def productname(string):
	"""Returns a product name string, i.e. the program name."""
	return output.turquoise(string)

def regexpquery(string):
	"""Returns a regular expression string."""
	return output.bold(string)

def section(string):
	"""Returns a string as a section header."""
	return output.turquoise(string)

def slot(string):
	"""Returns a slot string"""
	return output.bold(string)

def subsection(string):
	"""Returns a string as a subsection header."""
	return output.turquoise(string)

def useflag(string, enabled=True):
	"""Returns a USE flag string."""
	return output.red(string) if enabled else output.blue(string)

def keyword(string, stable=True, hard_masked=False):
	"""Returns a keyword string."""
	if stable:
		return output.green(string)
	if hard_masked:
		return output.red(string)
	# keyword masked:
	return output.blue(string)

def masking(mask):
	"""Returns a 'masked by' string."""
	if 'package.mask' in mask or 'profile' in mask:
		# use porthole wrap style to help clarify meaning
		return output.red("M["+mask[0]+"]")
	if mask is not []:
		for status in mask:
			if 'keyword' in status:
				# keyword masked | " [missing keyword] " <=looks better
				return output.blue("["+status+"]")
			if status in archlist:
				return output.green(status)
			if 'unknown' in status:
				return output.yellow(status)
		return output.red(status)
	return ''

def warn(string):
	"""Returns a warning string."""
	return "!!! " + string + "\n"

try:
	unicode
except NameError:
	unicode = str

def uprint(*args, **kw):
	"""Replacement for the builtin print function.

	This version gracefully handles characters not representable in the
	user's current locale (through the errors='replace' handler).

	@see: >>> help(print)
	"""

	sep = kw.pop('sep', ' ')
	end = kw.pop('end', '\n')
	file = kw.pop("file", sys.stdout)
	if kw:
		raise TypeError("got invalid keyword arguments: {0}".format(list(kw)))
	file = getattr(file, 'buffer', file)

	encoding = locale.getpreferredencoding()
	# Make sure that python knows the encoding. Bug 350156
	try:
		# We don't care about what is returned, we just want to
		# verify that we can find a codec.
		codecs.lookup(encoding)
	except LookupError:
		# Python does not know the encoding, so use utf-8.
		encoding = 'utf_8'

	def encoded_args():
		for arg in args:
			if isinstance(arg, bytes):
				yield arg
			else:
				yield unicode(arg).encode(encoding, 'replace')

	sep = sep.encode(encoding, 'replace')
	end = end.encode(encoding, 'replace')
	text = sep.join(encoded_args())
	file.write(text + end)

# vim: set ts=4 sw=4 tw=79:
