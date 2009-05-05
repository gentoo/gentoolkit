# Copyright(c) 2009, Gentoo Foundation
#
# Licensed under the GNU General Public License, v2
#
# $Header: $

"""List all direct dependencies matching a given query"""

__docformat__ = 'epytext'

# =======
# Imports
# =======

import sys
from getopt import gnu_getopt, GetoptError

from portage.util import unique_array

import gentoolkit.pprinter as pp
from gentoolkit.equery import format_options,  mod_usage, Config
from gentoolkit.helpers2 import compare_package_strings, do_lookup, \
	find_packages, get_cpvs, get_installed_cpvs
from gentoolkit.package import Package

# =======
# Globals
# =======

QUERY_OPTS = {
	"categoryFilter": None,
	"includeInstalled": True,
	"includePortTree": False,
	"includeOverlayTree": False,
	"isRegex": False,
	"matchExact": True,
	"onlyDirect": True,
	"onlyInstalled": True,
	"printMatchInfo": True,
	"indentLevel": 0,
	"depth": -1
}

# Used to cache and detect looping
PKGSEEN = set()
PKGDEPS = {}
DEPPKGS = {}

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
	print mod_usage(mod_name="depends")
	print
	print pp.command("options")
	print format_options((
		(" -h, --help", "display this help message"),
		(" -a, --all-packages", 
			"include packages that are not installed (slow)"),
		(" -D, --indirect",
			"search both direct and indirect dependencies"),
		("     --depth=N", "limit indirect dependency tree to specified depth")
	))


def cache_package_list(pkg_cache=None):
	"""Ensure that the package cache is set."""

	if not pkg_cache:
		if QUERY_OPTS["onlyInstalled"]:
			# TODO: move away from using strings here
			packages = get_installed_cpvs()
		else:
			packages = get_cpvs()
		packages.sort(compare_package_strings)
		pkg_cache = packages
	else:
		packages = pkg_cache
	
	return packages


def display_dependencies(cpv_is_displayed, dependency, cpv):
	"""Output dependencies calculated by find_dependencies.
	
	@type cpv_is_displayed: bool
	@param cpv_is_displayed: if True, the cpv has already been printed
	@see: gentoolkit.package.get_*_deps()
	@type dependency: tuple
	@param dependency: (comparator, [use flags], cpv)
	@type cpv: string
	@param cpv: cat/pkg-ver
	"""

	atom = pp.pkgquery(dependency[0] + dependency[2])
	indent = " " * (QUERY_OPTS["indentLevel"] * 2)
	useflags = pp.useflag(" & ".join(dependency[1]))

	if not cpv_is_displayed:
		if dependency[1]:
			if not Config["piping"] and Config["verbosityLevel"] >= 3:
				print indent + pp.cpv(cpv),
				print "(" + useflags + " ? " + atom + ")"
			else:
				print indent + cpv
		else:
			if not Config["piping"] and Config["verbosityLevel"] >= 3:
				print indent + pp.cpv(cpv),
				print "(" + atom + ")"
			else:
				print indent + cpv
	elif not Config["piping"] and Config["verbosityLevel"] >= 3:
		indent = indent + " " * len(cpv)
		if dependency[1]:
			print indent + " (" + useflags + " ? " + atom + ")"
		else:
			print indent + " (" + atom + ")"	


def find_dependencies(matches, pkg_cache):
	"""Find dependencies for the packaged named in queries.

	@type queries: list
	@param queries: packages to find the dependencies for
	"""

	for pkg in [Package(x) for x in cache_package_list(pkg_cache)]:
		if not pkg.cpv in PKGDEPS:
			try:
				deps = pkg.get_runtime_deps() + pkg.get_compiletime_deps()
				deps.extend(pkg.get_postmerge_deps())
			except KeyError:
				# If the ebuild is not found... 
				continue
			# Remove duplicate deps
			deps = unique_array(deps)
			PKGDEPS[pkg.cpv] = deps
		else:
			deps = PKGDEPS[pkg.cpv]

		cpv_is_displayed = False
		for dependency in deps:
			# TODO: (old) determine if dependency is enabled by USE flag
			# Find all packages matching the dependency
			depstr = dependency[0] + dependency[2]
			if not depstr in DEPPKGS:
				depcpvs = find_packages(depstr)
				DEPPKGS[depstr] = depcpvs
			else:
				depcpvs = DEPPKGS[depstr]

			for depcpv in depcpvs:
				is_match = False
				if depcpv in matches:
					is_match = True

				if is_match:
					display_dependencies(cpv_is_displayed, dependency, pkg.cpv)
					cpv_is_displayed = True
					break

		# if --indirect specified, call ourselves again with the dependency
		# Do not call if we have already called ourselves.
		if (cpv_is_displayed and not QUERY_OPTS["onlyDirect"] and 
			pkg not in PKGSEEN and 
			(QUERY_OPTS["indentLevel"] < QUERY_OPTS["depth"] or
			QUERY_OPTS["depth"] == -1)):

			PKGSEEN.add(pkg)
			QUERY_OPTS["indentLevel"] += 1
			find_dependencies([pkg], pkg_cache)
			QUERY_OPTS["indentLevel"] -= 1
 

def parse_module_options(module_opts):
	"""Parse module options and update GLOBAL_OPTS"""

	opts = (x[0] for x in module_opts)
	posargs = (x[1] for x in module_opts)
	for opt, posarg in zip(opts, posargs):
		if opt in ('-h', '--help'):
			print_help()
			sys.exit(0)
		elif opt in ('-a', '--all-packages'):
			QUERY_OPTS["onlyInstalled"] = False
		elif opt in ('-d', '--direct'):
			continue
		elif opt in ('-D', '--indirect'):
			QUERY_OPTS["onlyDirect"] = False
		elif opt in ('--depth'):
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

	short_opts = "hadD" # -d, --direct was old option for default action
	long_opts = ('help', 'all-packages', 'direct', 'indirect', 'depth=')

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

		if matches:
			find_dependencies(matches, None)
		else:
			pp.print_error("No matching package found for %s" % query)

		first_run = False
