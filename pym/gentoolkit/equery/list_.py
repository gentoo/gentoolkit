# Copyright(c) 2009, Gentoo Foundation
#
# Licensed under the GNU General Public License, v2 or higher
#
# $Header: $

"""List installed packages matching the query pattern"""

__docformat__ = 'epytext'

# =======
# Imports
# =======

import sys
from getopt import gnu_getopt, GetoptError

import gentoolkit
import gentoolkit.pprinter as pp
from gentoolkit.equery import format_options, mod_usage, Config
from gentoolkit.helpers2 import do_lookup, get_installed_cpvs
from gentoolkit.package import Package, PackageFormatter

# =======
# Globals
# =======

QUERY_OPTS = {
	"categoryFilter": None,
	"duplicates": False,
	"includeInstalled": True,
	"includePortTree": False,
	"includeOverlayTree": False,
	"includeMasked": True,
	"isRegex": False,
	"printMatchInfo": (not Config['quiet'])
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
		print __doc__.strip()
		print
	# Deprecation warning added 04/09: djanderson
	pp.print_warn("Default action for this module has changed in Gentoolkit 0.3.")
	pp.print_warn("-e, --exact-name is now the default behavior.")
	pp.print_warn("Use globbing to simulate the old behavior (see man equery).")
	pp.print_warn("Use '*' to check all installed packages.")
	print

	print mod_usage(mod_name="list")
	print
	print pp.command("options")
	print format_options((
		(" -h, --help", "display this help message"),
		(" -c, --category CAT", "only search in the category CAT"),
		(" -d, --duplicates", "list only installed duplicate packages"),
		(" -f, --full-regex", "query is a regular expression"),
		(" -I, --exclude-installed",
			"exclude installed packages from output"),
		(" -o, --overlay-tree", "list packages in overlays"),
		(" -p, --portage-tree", "list packages in the main portage tree")
	))


def get_duplicates(matches):
	"""Return only packages that have more than one version installed."""

	dups = {}
	result = []
	for pkg in matches:
		if pkg.key in dups:
			dups[pkg.key].append(pkg)
		else:
			dups[pkg.key] = [pkg]

	for cpv in dups.values():
		if len(cpv) > 1:
			result.extend(cpv)

	return result


def parse_module_options(module_opts):
	"""Parse module options and update GLOBAL_OPTS"""

	opts = (x[0] for x in module_opts)
	posargs = (x[1] for x in module_opts)
	for opt, posarg in zip(opts, posargs):
		if opt in ('-h', '--help'):
			print_help()
			sys.exit(0)
		elif opt in ('-a', '--all'):
			QUERY_OPTS['listAllPackages'] = True
		elif opt in ('-c', '--category'):
			QUERY_OPTS['categoryFilter'] = posarg
		elif opt in ('-I', '--exclude-installed'):
			QUERY_OPTS['includeInstalled'] = False
		elif opt in ('-p', '--portage-tree'):
			QUERY_OPTS['includePortTree'] = True
		elif opt in ('-o', '--overlay-tree'):
			QUERY_OPTS['includeOverlayTree'] = True
		elif opt in ('-f', '--full-regex'):
			QUERY_OPTS['isRegex'] = True
		elif opt in ('-e', '--exact-name'):
			pp.print_warn("-e, --exact-name is now default.")
			pp.print_warn("Use globbing to simulate the old behavior.")
			print
		elif opt in ('-d', '--duplicates'):
			QUERY_OPTS['duplicates'] = True


def main(input_args):
	"""Parse input and run the program"""

	short_opts = "hc:defiIop" # -i, -e were options for default actions

	# 04/09: djanderson
	# --installed is no longer needed. Kept for compatibility.
	# --exact-name is no longer needed. Kept for compatibility.
	long_opts = ('help', 'all', 'category=', 'installed', 'exclude-installed',
	'portage-tree', 'overlay-tree', 'full-regex', 'exact-name', 'duplicates')

	try:
		module_opts, queries = gnu_getopt(input_args, short_opts, long_opts)
	except GetoptError, err:
		pp.print_error("Module %s" % err)
		print
		print_help(with_description=False)
		sys.exit(2)

	parse_module_options(module_opts)

	# Only search installed packages when listing duplicate packages
	if QUERY_OPTS["duplicates"]:
		QUERY_OPTS["includeInstalled"] = True
		QUERY_OPTS["includePortTree"] = False
		QUERY_OPTS["includeOverlayTree"] = False

	if not queries:
		print_help()
		sys.exit(2)

	first_run = True
	for query in queries:
		if not first_run:
			print

		matches = do_lookup(query, QUERY_OPTS)

		# Find duplicate packages
		if QUERY_OPTS["duplicates"]:
			matches = get_duplicates(matches)

		matches.sort()

		#
		# Output
		#

		for pkg in matches:
			if Config['verbose']:
				pkgstr = PackageFormatter(pkg, format=True)
			else:
				pkgstr = PackageFormatter(pkg, format=False)

			if (QUERY_OPTS["includeInstalled"] and
				not QUERY_OPTS["includePortTree"] and
				not QUERY_OPTS["includeOverlayTree"]):
				if not 'I' in pkgstr.location:
					continue
			if (QUERY_OPTS["includePortTree"] and
				not QUERY_OPTS["includeOverlayTree"]):
				if not 'P' in pkgstr.location:
					continue
			if (QUERY_OPTS["includeOverlayTree"] and
				not QUERY_OPTS["includePortTree"]):
				if not 'O' in pkgstr.location:
					continue
			print pkgstr

		first_run = False
