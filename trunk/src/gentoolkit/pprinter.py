#!/usr/bin/python
#
# Copyright 2004 Karl Trygve Kalleberg <karltk@gentoo.org>
# Copyright 2004 Gentoo Foundation
# Distributed under the terms of the GNU General Public License v2
#
# $Header$

import gentoolkit
import output
import sys

def print_error(s):
	"""Prints an error string to stderr."""
	sys.stderr.write(output.red("!!! ") + s + "\n")

def print_info(lv, s, line_break = True):
	"""Prints an informational string to stdout."""
	if gentoolkit.Config["verbosityLevel"] >= lv:
		sys.stdout.write(s)
		if line_break:
			sys.stdout.write("\n")

def print_warn(s):
	"""Print a warning string to stderr."""
	sys.stderr.write("!!! " + s + "\n")
	
def die(err, s):
	"""Print an error string and die with an error code."""
	print_error(s)
	sys.exit(-err)

# Colour settings

def cpv(s):
	"""Print a category/package-<version> string."""
	return output.green(s)

def slot(s):
	"""Print a slot string"""
	return output.white(s)
	
def useflag(s):
	"""Print a USE flag strign"""
	return output.blue(s)

def useflagon(s):
	"""Print an enabled USE flag string"""
	# FIXME: Collapse into useflag with parameter
	return output.red(s)

def useflagoff(s):
	"""Print a disabled USE flag string"""
	# FIXME: Collapse into useflag with parameter
	return output.blue(s)
	
def maskflag(s):
	"""Print a masking flag string"""
	return output.red(s)

def installedflag(s):
	"""Print an installed flag string"""
	return output.white(s)
	
def number(s):
	"""Print a number string"""
	return output.turquoise(s)

def pkgquery(s):
	"""Print a package query string."""
	return output.white(s)

def regexpquery(s):
	"""Print a regular expression string"""
	return output.white(s)

def path(s):
	"""Print a file or directory path string"""
	return output.white(s)

def path_symlink(s):
	"""Print a symlink string."""
	return output.turquoise(s)

def productname(s):
	"""Print a product name string, i.e. the program name."""
	return output.turquoise(s)
	
def globaloption(s):
	"""Print a global option string, i.e. the program global options."""
	return output.yellow(s)

def localoption(s):
	"""Print a local option string, i.e. the program local options."""
	return output.green(s)

def command(s):
	"""Print a program command string."""
	return output.green(s)
	
def section(s):
	"""Print a string as a section header."""
	return output.turquoise(s)	

def subsection(s):
	"""Print a string as a subsection header."""
	return output.turquoise(s)
	
def emph(s):
	"""Print a string as emphasized."""
	return output.white(s)