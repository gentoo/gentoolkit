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

import portage.output as output

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
	return output.blue(string) if enabled else output.red(string)

def keyword(string, stable=True, hard_masked=False):
	"""Returns a keyword string."""
	if stable:
		return output.green(string)
	if hard_masked:
		return output.red(string)
	# keyword masked:
	return output.blue(string)

def warn(string):
	"""Returns a warning string."""
	return "!!! " + string + "\n"

# vim: set ts=4 sw=4 tw=79:
