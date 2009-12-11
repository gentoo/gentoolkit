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
	'maskflag',
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
	"""Print a program command string."""
	return output.green(string)

def cpv(string):
	"""Print a category/package-<version> string."""
	return output.green(string)

def die(err, string):
	"""Print an error string and die with an error code."""
	sys.stderr.write(error(string))
	sys.exit(err)

def emph(string):
	"""Print a string as emphasized."""
	return output.bold(string)

def error(string):
	"""Prints an error string to stderr."""
	return output.red("!!! ") + string + "\n"

def globaloption(string):
	"""Print a global option string, i.e. the program global options."""
	return output.yellow(string)

def installedflag(string):
	"""Print an installed flag string"""
	return output.bold(string)

def localoption(string):
	"""Print a local option string, i.e. the program local options."""
	return output.green(string)

def maskflag(string):
	"""Print a masking flag string"""
	return output.red(string)

def number(string):
	"""Print a number string"""
	return output.turquoise(string)

def path(string):
	"""Print a file or directory path string"""
	return output.bold(string)

def path_symlink(string):
	"""Print a symlink string."""
	return output.turquoise(string)

def pkgquery(string):
	"""Print a package query string."""
	return output.bold(string)

def productname(string):
	"""Print a product name string, i.e. the program name."""
	return output.turquoise(string)

def regexpquery(string):
	"""Print a regular expression string"""
	return output.bold(string)

def section(string):
	"""Print a string as a section header."""
	return output.turquoise(string)

def slot(string):
	"""Print a slot string"""
	return output.bold(string)

def subsection(string):
	"""Print a string as a subsection header."""
	return output.turquoise(string)

def useflag(string, enabled=True):
	"""Print a USE flag string"""
	return output.green(string) if enabled else output.blue(string)

def warn(string):
	"""Print a warning string to stderr."""
	return "!!! " + string + "\n"

# vim: set ts=4 sw=4 tw=79:
