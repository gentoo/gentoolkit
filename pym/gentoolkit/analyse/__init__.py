#!/usr/bin/python
#
# Copyright 2010 Brian Dolbec <brian.dolbec@gmail.com>
# Copyright(c) 2010, Gentoo Foundation
# Copyright 2003-2004 Karl Trygve Kalleberg
# Licensed under the GNU General Public License, v2
#
# $Header: $

"""Gentoo's installed packages analysis and repair tool"""


# Move to Imports section after Python 2.6 is stable


__docformat__ = 'epytext'
# version is dynamically set by distutils sdist
__version__ = "svn"
__productname__ = "analyse"
__authors__ = (
	'Brian Dolbec, <brian.dolbec@gmail.com>'

)

# make an exportable copy of the info for help output
MODULE_INFO = {
	"__docformat__": __docformat__,
	"__doc__": __doc__,
	"__version__": __version__,
	"__productname__": __productname__,
	"__authors__": __authors__

}

import errno
import sys
import time
from getopt import getopt, GetoptError

import portage

import gentoolkit as gen
from gentoolkit import errors
from gentoolkit import pprinter as pp
from gentoolkit.base import (initialize_configuration, split_arguments,
	parse_global_options, print_help)
from gentoolkit.formatters import format_options


NAME_MAP = {
	'a': 'analyse',
	'r': 'rebuild'
}

FORMATTED_OPTIONS = (
		("    (a)nalyse",
		"analyses the installed PKG database USE flag or keyword useage"),
		("    (r)ebuild",
		"analyses the Installed PKG database and generates files suitable"),
		("  ",
		"to replace corrupted or missing /etc/portage/package.* files")
	)

def expand_module_name(module_name):
	"""Returns one of the values of NAME_MAP or raises KeyError"""

	if module_name == 'list':
		# list is a Python builtin type, so we must rename our module
		return 'list_'
	elif module_name in NAME_MAP.values():
		return module_name
	else:
		return NAME_MAP[module_name]


def main():
	"""Parse input and run the program."""

	short_opts = "hqCNV"
	long_opts = (
		'help', 'quiet', 'nocolor', 'no-color', 'no-pipe', 'version', 'debug'
	)

	initialize_configuration()

	try:
		global_opts, args = getopt(sys.argv[1:], short_opts, long_opts)
	except GetoptError as err:
		sys.stderr.write(" \n")
		sys.stderr.write(pp.error("Global %s\n" % err))
		print_help(MODULE_INFO, FORMATTED_OPTIONS, with_description=False)
		sys.exit(2)

	# Parse global options
	need_help = parse_global_options(global_opts, args, MODULE_INFO, FORMATTED_OPTIONS)

	if gen.CONFIG['quiet']:
		gen.CONFIG['verbose'] = False

	try:
		module_name, module_args = split_arguments(args)
	except IndexError:
		print_help(MODULE_INFO,  FORMATTED_OPTIONS)
		sys.exit(2)

	if need_help:
		module_args.append('--help')

	try:
		expanded_module_name = expand_module_name(module_name)
	except KeyError:
		sys.stderr.write(pp.error("Unknown module '%s'" % module_name))
		print_help(MODULE_INFO, FORMATTED_OPTIONS, with_description=False)
		sys.exit(2)

	try:
		loaded_module = __import__(
			expanded_module_name, globals(), locals(), [], -1
		)
		loaded_module.main(module_args)
	except portage.exception.AmbiguousPackageName as err:
		raise errors.GentoolkitAmbiguousPackage(err.args[0])
	except IOError as err:
		if err.errno != errno.EPIPE:
			raise

if __name__ == '__main__':
	main()
