# Copyright(c) 2009, Gentoo Foundation
#
# Licensed under the GNU General Public License, v2
#
# $Header: $

"""List all packages owning a particular file

Note: Normally, only one package will own a file. If multiple packages own
      the same file, it usually consitutes a problem, and should be reported.
"""

__docformat__ = 'epytext'

# =======
# Imports
# =======

import re
import sys
from getopt import gnu_getopt, GetoptError

import gentoolkit.pprinter as pp
from gentoolkit.equery import format_filetype, format_options, mod_usage, \
	Config
from gentoolkit.helpers2 import get_installed_cpvs
from gentoolkit.package import Package

# =======
# Globals
# =======

QUERY_OPTS = {
	"fullRegex": False,
	"earlyOut": False,
	"nameOnly": False
}

# =========
# Functions
# =========

def parse_module_options(module_opts):
	"""Parse module options and update GLOBAL_OPTS"""

	opts = (x[0] for x in module_opts)
	for opt in opts:
		if opt in ('-h','--help'):
			print_help()
			sys.exit(0)
		elif opt in ('-c', '--category'):
			# Remove this warning after a reasonable amount of time
			# (djanderson, 2/2009)
			pp.print_warn("Module option -c, --category not implemented")
			print
		elif opt in ('-e', '--early-out', '--earlyout'):
			if opt == '--earlyout':
				pp.print_warn("Use of --earlyout is deprecated.")
				pp.print_warn("Please use --early-out.")
				print
			QUERY_OPTS['earlyOut'] = True
		elif opt in ('-f', '--full-regex'):
			QUERY_OPTS['fullRegex'] = True
		elif opt in ('-n', '--name-only'):
			QUERY_OPTS['nameOnly'] = True


def prepare_search_regex(queries):
	"""Create a regex out of the queries"""

	if QUERY_OPTS["fullRegex"]:
		result = queries
	else:
		result = []
		# Trim trailing and multiple slashes from queries
		slashes = re.compile('/+')
		for query in queries:
			query = slashes.sub('/', query).rstrip('/')
			if query.startswith('/'):
				query = "^%s$" % re.escape(query)
			else:
				query = "/%s$" % re.escape(query)
			result.append(query)

	result = "|".join(result)

	return re.compile(result)


def print_help(with_description=True):
	"""Print description, usage and a detailed help message.
	
	@type with_description: bool
	@param with_description: if true, print module's __doc__ string
	"""

	if with_description:
		print __doc__.strip()
		print
	print mod_usage(mod_name="belongs", arg="filename")
	print
	print pp.command("options")
	print format_options((
		(" -h, --help", "display this help message"),
		(" -f, --full-regex", "supplied query is a regex" ),
		(" -e, --early-out", "stop when first match is found"),
		(" -n, --name-only", "don't print the version")
	))


def main(input_args):
	"""Parse input and run the program"""

	# -c, --category is not implemented
	short_opts = "hc:fen"
	long_opts = ('help', 'category=', 'full-regex', 'early-out', 'earlyout',
		'name-only')

	try:
		module_opts, queries = gnu_getopt(input_args, short_opts, long_opts)
	except GetoptError, err:
		pp.print_error("Module %s" % err)
		print
		print_help(with_description=False)
		sys.exit(2)

	parse_module_options(module_opts)

	if not queries:
		print_help()
		sys.exit(2)

	query_re = prepare_search_regex(queries)

	if Config['verbose']:
		pp.print_info(3, " * Searching for %s ... "
			% (pp.regexpquery(",".join(queries))))
	
	matches = get_installed_cpvs()
	
	# Print matches to screen or pipe
	found_match = False
	for pkg in [Package(x) for x in matches]:
		files = pkg.get_contents()
		for cfile in files:
			if query_re.search(cfile):
				if QUERY_OPTS["nameOnly"]:
					pkg_str = pkg.key
				else:
					pkg_str = pkg.cpv
				if Config['verbose']:
					file_str = pp.path(format_filetype(cfile, files[cfile]))
					print "%s (%s)" % (pkg_str, file_str)
				else:
					print pkg_str

				found_match = True

		if found_match and QUERY_OPTS["earlyOut"]:
			break
