# Copyright(c) 2009, Gentoo Foundation
#
# Licensed under the GNU General Public License, v2 or higher
#
# $Header: $

"""List all installed packages that have a given USE flag"""

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
	"includeInstalled": False,
	"includePortTree": False,
	"includeOverlayTree": False,
	"includeMasked": True,
	"isRegex": False,             # Necessary for do_lookup, don't change
	"printMatchInfo": False
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
	print mod_usage(mod_name="hasuse", arg="USE-flag")
	print
	print pp.command("options")
	print format_options((
		(" -h, --help", "display this help message"),
		(" -i, --installed",
			"include installed packages in search path (default)"),
		(" -o, --overlay-tree", "include overlays in search path"),
		(" -p, --portage-tree", "include entire portage tree in search path")
	))


def parse_module_options(module_opts):
	"""Parse module options and update GLOBAL_OPTS"""

	# Parse module options
	opts = (x[0] for x in module_opts)
	for opt in opts:
		if opt in ('-h', '--help'):
			print_help()
			sys.exit(0)
		elif opt in ('-i', '--installed'):
			QUERY_OPTS['includeInstalled'] = True
		elif opt in ('-p', '--portage-tree'):
			QUERY_OPTS['includePortTree'] = True
		elif opt in ('-o', '--overlay-tree'):
			QUERY_OPTS['includeOverlayTree'] = True


def print_sequence(seq):
	"""Print every item of a sequence."""

	for item in seq:
		print item


def sort_by_location(query, matches):
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
		useflags = [f.lstrip("+-") for f in pkg.get_env_var("IUSE").split()]
		if query not in useflags:
			continue 

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

	short_opts = "hiIpo"
	long_opts = ('help', 'installed', 'exclude-installed', 'portage-tree',
		'overlay-tree')

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
	elif not (QUERY_OPTS['includeInstalled'] or
		QUERY_OPTS['includePortTree'] or QUERY_OPTS['includeOverlayTree']):
		# Got queries but no search path; set a sane default
		QUERY_OPTS['includeInstalled'] = True

	matches = do_lookup("*", QUERY_OPTS)
	matches.sort()

	#
	# Output
	#

	first_run = True
	for query in queries:
		if not first_run:
			print

		if not Config["piping"]:
			print " * Searching for USE flag %s ... " % pp.useflag(query)

		installed, overlay, porttree = sort_by_location(query, matches)

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
