# Copyright(c) 2009, Gentoo Foundation
#
# Licensed under the GNU General Public License, v2
#
# $Header: $

"""List all packages owning a particular file

Note: Normally, only one package will own a file. If multiple packages own
      the same file, it usually constitutes a problem, and should be reported.
"""

from __future__ import print_function

__docformat__ = 'epytext'

# =======
# Imports
# =======

import sys
from getopt import gnu_getopt, GetoptError

import gentoolkit.pprinter as pp
from gentoolkit.equery import (format_filetype, format_options, mod_usage,
	CONFIG)
from gentoolkit.helpers import FileOwner

# =======
# Globals
# =======

QUERY_OPTS = {
	"full_regex": False,
	"early_out": False,
	"name_only": False
}

# =======
# Classes
# =======

class BelongsPrinter(object):
	"""Outputs a formatted list of packages that claim to own a files."""

	def __init__(self, verbose=True, name_only=False):
		if verbose:
			self.print_fn = self.print_verbose
		else:
			self.print_fn = self.print_quiet

		self.name_only = name_only

	def __call__(self, pkg, cfile):
		self.print_fn(pkg, cfile)

	# W0613: *Unused argument %r*
	# pylint: disable-msg=W0613
	def print_quiet(self, pkg, cfile):
		"Format for minimal output."
		if self.name_only:
			name = pkg.cp
		else:
			name = str(pkg.cpv)
		pp.uprint(name)

	def print_verbose(self, pkg, cfile):
		"Format for full output."
		file_str = pp.path(format_filetype(cfile, pkg.parsed_contents()[cfile]))
		if self.name_only:
			name = pkg.cp
		else:
			name = str(pkg.cpv)
		pp.uprint(pp.cpv(name), "(" + file_str + ")")

# =========
# Functions
# =========

def parse_module_options(module_opts):
	"""Parse module options and update QUERY_OPTS"""

	opts = (x[0] for x in module_opts)
	for opt in opts:
		if opt in ('-h','--help'):
			print_help()
			sys.exit(0)
		elif opt in ('-e', '--early-out', '--earlyout'):
			if opt == '--earlyout':
				sys.stderr.write(pp.warn("Use of --earlyout is deprecated."))
				sys.stderr.write(pp.warn("Please use --early-out."))
				print()
			QUERY_OPTS['early_out'] = True
		elif opt in ('-f', '--full-regex'):
			QUERY_OPTS['full_regex'] = True
		elif opt in ('-n', '--name-only'):
			QUERY_OPTS['name_only'] = True


def print_help(with_description=True):
	"""Print description, usage and a detailed help message.

	@type with_description: bool
	@param with_description: if true, print module's __doc__ string
	"""

	if with_description:
		print(__doc__.strip())
		print()
	print(mod_usage(mod_name="belongs", arg="filename"))
	print()
	print(pp.command("options"))
	print(format_options((
		(" -h, --help", "display this help message"),
		(" -f, --full-regex", "supplied query is a regex" ),
		(" -e, --early-out", "stop when first match is found"),
		(" -n, --name-only", "don't print the version")
	)))


def main(input_args):
	"""Parse input and run the program"""

	short_opts = "h:fen"
	long_opts = ('help', 'full-regex', 'early-out', 'earlyout',
		'name-only')

	try:
		module_opts, queries = gnu_getopt(input_args, short_opts, long_opts)
	except GetoptError as err:
		sys.stderr.write(pp.error("Module %s" % err))
		print()
		print_help(with_description=False)
		sys.exit(2)

	parse_module_options(module_opts)

	if not queries:
		print_help()
		sys.exit(2)

	if CONFIG['verbose']:
		pp.uprint(" * Searching for %s ... " % (
			pp.regexpquery(",".join(queries)))
		)

	printer_fn = BelongsPrinter(
		verbose=CONFIG['verbose'], name_only=QUERY_OPTS['name_only']
	)

	find_owner = FileOwner(
		is_regex=QUERY_OPTS['full_regex'],
		early_out=QUERY_OPTS['early_out'],
		printer_fn=printer_fn
	)

	if not find_owner(queries):
		sys.exit(1)

# vim: set ts=4 sw=4 tw=79:
