# Copyright(c) 2009, Gentoo Foundation
#
# Licensed under the GNU General Public License, v2
#
# $Header: $

"""Display the path to the ebuild that would be used by Portage with the current
configuration
"""

from __future__ import print_function

__docformat__ = 'epytext'

# =======
# Imports
# =======

import os
import sys
from getopt import gnu_getopt, GetoptError


import gentoolkit.pprinter as pp
from gentoolkit import errors
from gentoolkit.equery import format_options, mod_usage
from gentoolkit.query import Query

# =======
# Globals
# =======

QUERY_OPTS = {
	"include_masked": False,
	"ebuild":False
	}

# =========
# Functions
# =========

def print_help(with_description=True):
	"""Print description, usage and a detailed help message.

	@type with_description: bool
	@param with_description: if true, print module's __doc__ string
	"""

	if with_description:
		print(__doc__.strip())
		print()
	print(mod_usage(mod_name="which"))
	print()
	print(pp.command("options"))
	print(format_options((
		(" -h, --help", "display this help message"),
		(" -m, --include-masked", "return highest version ebuild available"),
		(" -e, --ebuild", "print the ebuild")
	)))

def print_ebuild(ebuild_path):
	"""Output the ebuild to std_out"""
	with open(ebuild_path) as f:
		lines = f.readlines()
		print("\n\n")
		print("".join(lines))
		print("\n")

def parse_module_options(module_opts):
	"""Parse module options and update QUERY_OPTS"""

	opts = (x[0] for x in module_opts)
	for opt in opts:
		if opt in ('-h', '--help'):
			print_help()
			sys.exit(0)
		elif opt in ('-m', '--include-masked'):
			QUERY_OPTS['include_masked'] = True
		elif opt in ('-e', '--ebuild'):
			QUERY_OPTS['ebuild'] = True


def main(input_args):
	"""Parse input and run the program"""

	short_opts = "hme"
	long_opts = ('help', 'include-masked', 'ebuild')

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

	for query in (Query(x) for x in queries):
		matches = query.find(
			include_masked=QUERY_OPTS['include_masked'],
			in_installed=False
		)
		if matches:
			pkg = sorted(matches).pop()
			ebuild_path = pkg.ebuild_path()
			if ebuild_path:
				pp.uprint(os.path.normpath(ebuild_path))
				if QUERY_OPTS['ebuild']:
					print_ebuild(ebuild_path)
			else:
				sys.stderr.write(
					pp.warn("No ebuilds to satisfy %s" % pkg.cpv)
				)
		else:
			raise errors.GentoolkitNoMatches(query)

# vim: set ts=4 sw=4 tw=79:
