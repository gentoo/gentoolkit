# Copyright(c) 2009, Gentoo Foundation
#
# Licensed under the GNU General Public License, v2
#
# $Header: $

"""Display a dependency graph for a given package"""

__docformat__ = 'epytext'

# =======
# Imports
# =======

import sys
from getopt import gnu_getopt, GetoptError

import gentoolkit
import gentoolkit.pprinter as pp
from gentoolkit import errors
from gentoolkit.equery import format_options, mod_usage, Config
from gentoolkit.helpers2 import do_lookup, find_best_match

# =======
# Globals
# =======

QUERY_OPTS = {
	"categoryFilter": None,
	"depth": 0,
	"displayUseflags": True,
	"fancyFormat": True,
	"includeInstalled": True,
	"includePortTree": True,
	"includeOverlayTree": True,
	"includeMasked": True,
	"isRegex": False,
	"matchExact": True,
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
	print mod_usage(mod_name="depgraph")
	print
	print pp.command("options")
	print format_options((
		(" -h, --help", "display this help message"),
		(" -U, --no-useflags", "do not show USE flags"),
		(" -l, --linear", "do not use fancy formatting"),
		("     --depth=N", "limit dependency graph to specified depth")
	))


def display_graph(pkg, stats, level=0, seen_pkgs=None, suffix=""):
	"""Display a dependency graph for a package
	
	@type pkg: gentoolkit.package.Package
	@param pkg: package to check dependencies of
	@type level: int
	@param level: current depth level
	@type seen_pkgs: set
	@param seen_pkgs: a set of all packages that have had their deps graphed
	"""

	if not seen_pkgs:
		seen_pkgs = set()

	stats["packages"] += 1
	stats["maxdepth"] = max(stats["maxdepth"], level)

	pfx = ""
	if QUERY_OPTS["fancyFormat"]:
		pfx = (level * " ") + "`-- " 
	pp.print_info(0, pfx + pkg.cpv + suffix)
	
	seen_pkgs.add(pkg.cpv)
	
	deps = pkg.get_runtime_deps() + pkg.get_compiletime_deps()
	deps.extend(pkg.get_postmerge_deps())
	for dep in deps:
		suffix = ""
		depcpv = dep[2]
		deppkg = find_best_match(dep[0] + depcpv)
		if not deppkg:
			print (pfx + dep[0] + depcpv),
			print "(unable to resolve: package masked or removed)"
			continue
		if deppkg.get_cpv() in seen_pkgs:
			continue
		if depcpv.find("virtual") == 0:
			suffix += " (%s)" % pp.cpv(depcpv)
		if dep[1] and QUERY_OPTS["displayUseflags"]:
			suffix += " [%s]" % pp.useflagon(' '.join(dep[1]))
		if (level < QUERY_OPTS["depth"] or QUERY_OPTS["depth"] <= 0):
			seen_pkgs, stats = display_graph(deppkg, stats, level+1,
				seen_pkgs, suffix)

	return seen_pkgs, stats


def parse_module_options(module_opts):
	"""Parse module options and update GLOBAL_OPTS"""

	opts = (x[0] for x in module_opts)
	posargs = (x[1] for x in module_opts)
	for opt, posarg in zip(opts, posargs):
		if opt in ('-h', '--help'):
			print_help()
			sys.exit(0)
		if opt in ('-U', '--no-useflags'):
			QUERY_OPTS["displayUseflags"] = False
		if opt in ('-l', '--linear'):
			QUERY_OPTS["fancyFormat"] = False
		if opt in ('--depth'):
			if posarg.isdigit():
				depth = int(posarg)
			else:
				err = "Module option --depth requires integer (got '%s')" 
				pp.print_error(err % posarg)
				print
				print_help(with_description=False)
				sys.exit(2)
			QUERY_OPTS["depth"] = depth


def main(input_args):
	"""Parse input and run the program"""

	short_opts = "hUl"
	long_opts = ('help', 'no-useflags', 'depth=')

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

	#
	# Output
	#

	first_run = True
	for query in queries:
		if not first_run:
			print

		matches = do_lookup(query, QUERY_OPTS)

		if not matches:
			errors.GentoolkitNoMatches(query)

		for pkg in matches:
			stats = {"maxdepth": 0, "packages": 0}

			if Config['verbose']:
				pp.print_info(3, " * dependency graph for %s:" % pp.cpv(pkg.cpv))
			else:
				pp.print_info(0, "%s:" % pkg.cpv)

			stats = display_graph(pkg, stats)[1]

			if Config['verbose']:
				info = ''.join(["[ ", pp.cpv(pkg.cpv), " stats: packages (",
				pp.number(str(stats["packages"])), "), max depth (",
				pp.number(str(stats["maxdepth"])), ") ]"])
				pp.print_info(0, info)

		first_run = False
