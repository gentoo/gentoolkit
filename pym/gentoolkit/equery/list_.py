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
from gentoolkit.equery import format_options, format_package_names, \
	mod_usage, Config
from gentoolkit.helpers2 import do_lookup, get_installed_cpvs
from gentoolkit.package import Package

# =======
# Globals
# =======

QUERY_OPTS = {
	"categoryFilter": None,
	"duplicates": False,
	"includeInstalled": False,
	"includePortTree": False,
	"includeOverlayTree": False,
	"includeMasked": True,
	"isRegex": False,
	"printMatchInfo": True
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
		(" -i, --installed", "list installed packages matching query"),
		(" -o, --overlay-tree", "list packages in overlays"),
		(" -p, --portage-tree", "list packages in the main portage tree")
	))


def adjust_query_environment(queries):
	"""Make sure the search environment is good to go."""

	if not queries and not (QUERY_OPTS["duplicates"] or
		QUERY_OPTS["includeInstalled"] or QUERY_OPTS["includePortTree"] or 
		QUERY_OPTS["includeOverlayTree"]):
		print_help()
		sys.exit(2)
	elif queries and not (QUERY_OPTS["duplicates"] or
		QUERY_OPTS["includeInstalled"] or QUERY_OPTS["includePortTree"] or 
		QUERY_OPTS["includeOverlayTree"]):
		QUERY_OPTS["includeInstalled"] = True
	elif not queries and (QUERY_OPTS["duplicates"] or
		QUERY_OPTS["includeInstalled"] or QUERY_OPTS["includePortTree"] or 
		QUERY_OPTS["includeOverlayTree"]):
		queries = ["*"]

	# Only search installed packages when listing duplicate packages
	if QUERY_OPTS["duplicates"]:
		QUERY_OPTS["includeInstalled"] = True
		QUERY_OPTS["includePortTree"] = False
		QUERY_OPTS["includeOverlayTree"] = False

	return queries


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
		elif opt in ('-i', '--installed'):
			QUERY_OPTS['includeInstalled'] = True
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


def print_sequence(seq):
	"""Print every item of a sequence."""

	for item in seq:
		print item


def sort_by_location(matches):
	"""Take a list of packages and sort them by location.
	
	@rtype: tuple
	@return:
		installed: list of all packages in matches that are in the vdb
		overlay: list of all packages in matches that reside in an overlay
		porttree: list of all packages that are not in the vdb or an overlay
	"""

	all_installed_packages = set()
	if QUERY_OPTS["includeInstalled"]:
		all_installed_packages = set(Package(x) for x in get_installed_cpvs())

	# Cache package sets
	installed = []
	overlay = []
	porttree = []

	for pkg in matches:
		if QUERY_OPTS["includeInstalled"]:
			if pkg in all_installed_packages:
				installed.append(pkg)
				continue
		if pkg.is_overlay():
			if QUERY_OPTS["includeOverlayTree"]:
				overlay.append(pkg)
			continue
		if QUERY_OPTS["includePortTree"]:
			porttree.append(pkg)

	return installed, overlay, porttree


def main(input_args):
	"""Parse input and run the program"""

	short_opts = "hc:defiIop" # -I was used to turn off -i when it was
	                          # the default action, -e is now default

	# 04/09: djanderson
	# --exclude-installed is no longer needed. Kept for compatibility.
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
	queries = adjust_query_environment(queries)

	first_run = True
	for query in queries:
		if not first_run:
			print

		matches = do_lookup(query, QUERY_OPTS)

		# Find duplicate packages
		if QUERY_OPTS["duplicates"]:
			matches = get_duplicates(matches)

		matches.sort()

		installed, overlay, porttree = sort_by_location(matches)

		#
		# Output
		#

		if QUERY_OPTS["includeInstalled"]:
			print " * installed packages:"
			if not Config["piping"]:
				installed = format_package_names(installed, 1)
			print_sequence(installed)

		if QUERY_OPTS["includePortTree"]:
			portdir = pp.path(gentoolkit.settings["PORTDIR"])
			print " * Portage tree (%s):" % portdir 
			if not Config["piping"]:
				porttree = format_package_names(porttree, 2)
			print_sequence(porttree)

		if QUERY_OPTS["includeOverlayTree"]:
			portdir_overlay = pp.path(gentoolkit.settings["PORTDIR_OVERLAY"])
			print " * overlay tree (%s):" % portdir_overlay
			if not Config["piping"]:
				overlay = format_package_names(overlay, 3)
			print_sequence(overlay)

		first_run = False
