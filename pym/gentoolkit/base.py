#!/usr/bin/python
#
# Copyright(c) 2009 - 2010, Gentoo Foundation
# Distributed under the terms of the GNU General Public License v2
#
# $Header: $

"""Gentoolkit Base Module class to hold common module operation functions
"""

from __future__ import print_function

__docformat__ = 'epytext'


import errno
import os
import sys
import time
from getopt import gnu_getopt, GetoptError

import gentoolkit
from gentoolkit import errors
#from gentoolkit.textwrap_ import TextWrapper
import gentoolkit.pprinter as pp
from gentoolkit.formatters import format_options


GLOBAL_OPTIONS = (
	("    -h, --help", "display this help message"),
	("    -q, --quiet", "minimal output"),
	("    -C, --no-color", "turn off colors"),
	("    -N, --no-pipe", "turn off pipe detection"),
	("    -V, --version", "display version info")
)


def initialize_configuration():
	"""Setup the standard equery config"""

	# Get terminal size
	term_width = pp.output.get_term_size()[1]
	if term_width < 1:
		# get_term_size() failed. Set a sane default width:
		term_width = 80
	# Terminal size, minus a 1-char margin for text wrapping
	gentoolkit.CONFIG['termWidth'] = term_width - 1
	# Guess color output
	if (gentoolkit.CONFIG['color'] == -1 and (not sys.stdout.isatty() or
		os.getenv("NOCOLOR") in ("yes", "true")) or gentoolkit.CONFIG['color'] == 0):
		pp.output.nocolor()
	gentoolkit.CONFIG['verbose'] = not gentoolkit.CONFIG['piping']


def split_arguments(args):
	"""Separate module name from module arguments"""

	return args.pop(0), args


def main_usage(module_info):
	"""Return the main usage message for analyse"""
	return "%(usage)s %(product)s [%(g_opts)s] %(mod_name)s [%(mod_opts)s]" % {
		'usage': pp.emph("Usage:"),
		'product': pp.productname(module_info["__productname__"]),
		'g_opts': pp.globaloption("global-options"),
		'mod_name': pp.command("module-name"),
		'mod_opts': pp.localoption("module-options")
	}


def print_version(module_info):
	"""Print the version of this tool to the console."""

	print("%(product)s (%(version)s) - %(docstring)s" % {
		"product": pp.productname(module_info["__productname__"]),
		"version": module_info["__version__"],
		"docstring": module_info["__doc__"]
	})


def print_help(module_info, formatted_options=None, with_description=True):
	"""Print description, usage and a detailed help message.

	@param with_description (bool): Option to print module's __doc__ or not
	"""

	if with_description:
		print()
		print(module_info["__doc__"])
		print()
	print(main_usage(module_info))
	print()
	print(pp.globaloption("global options"))
	print(format_options(GLOBAL_OPTIONS))
	print()
	if formatted_options:
		print(pp.command("modules") + " (" + pp.command("short name") + ")")
		print(format_options(formatted_options))
	else:
		print("Error: calling function did not supply formatted options")
		print()


def parse_global_options(global_opts, args, module_info, formatted_options):
	"""Parse global input args and return True if we should display help for
	the called module, else False (or display help and exit from here).
	"""

	need_help = False
	do_help = False
	opts = (opt[0] for opt in global_opts)
	for opt in opts:
		if opt in ('-h', '--help'):
			do_help = True
			if args:
				need_help = True
			else:
				do_help = True
		elif opt in ('-q','--quiet'):
			gentoolkit.CONFIG['quiet'] = True
		elif opt in ('-C', '--no-color', '--nocolor'):
			gentoolkit.CONFIG['color'] = 0
			pp.output.nocolor()
		elif opt in ('-N', '--no-pipe'):
			gentoolkit.CONFIG['piping'] = False
		elif opt in ('-V', '--version'):
			print_version(module_info)
			sys.exit(0)
		elif opt in ('--debug'):
			gentoolkit.CONFIG['debug'] = True
	if do_help:
		print_help( module_info, formatted_options)
		sys.exit(0)
	return need_help


def mod_usage(mod_name="module", arg="pkgspec", optional=False):
	"""Provide a consistant usage message to the calling module.

	@type arg: string
	@param arg: what kind of argument the module takes (pkgspec, filename, etc)
	@type optional: bool
	@param optional: is the argument optional?
	"""

	return "%(usage)s: %(mod_name)s [%(opts)s] %(arg)s" % {
		'usage': pp.emph("Usage"),
		'mod_name': pp.command(mod_name),
		'opts': pp.localoption("options"),
		'arg': ("[%s]" % pp.emph(arg)) if optional else pp.emph(arg)
	}

