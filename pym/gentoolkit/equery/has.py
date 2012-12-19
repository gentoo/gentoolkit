# Copyright(c) 2009, Gentoo Foundation
#
# Licensed under the GNU General Public License, v2 or higher
#
# $Header: $

"""List all installed packages that match for a given ENVIRONMENT variable"""

from __future__ import print_function

__docformat__ = 'epytext'

# =======
# Imports
# =======

import sys
from getopt import gnu_getopt, GetoptError

from portage import auxdbkeys

import gentoolkit.pprinter as pp
from gentoolkit import errors
from gentoolkit.equery import format_options, mod_usage, CONFIG
from gentoolkit.package import PackageFormatter, FORMAT_TMPL_VARS
from gentoolkit.query import Query

# =======
# Globals
# =======

QUERY_OPTS = {
	"in_installed": True,
	"in_porttree": False,
	"in_overlay": False,
	"include_masked": True,
	"show_progress": False,
	"package_format": None,
	"package_filter": None,
	"env_var": None
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
	print(mod_usage(mod_name="has", arg="env_var [expr]"))
	print()
	print(pp.command("options"))
	print(format_options((
		(" -h, --help", "display this help message"),
		(" -I, --exclude-installed",
			"exclude installed packages from search path"),
		(" -o, --overlay-tree", "include overlays in search path"),
		(" -p, --portage-tree", "include entire portage tree in search path"),
		(" -F, --format=TMPL", "specify a custom output format"),
		("              TMPL",
			"a format template using (see man page):")
	)))
#	print(" " * 24, ', '.join(pp.emph(x) for x in FORMAT_TMPL_VARS))


def query_in_env(query, env_var, pkg):
	"""Check if the query is in the pkg's environment."""

	try:
		if env_var in ("USE", "IUSE"):
			results = set(
				[x.lstrip("+-") for x in pkg.environment(env_var).split()]
			)
		else:
			results = set(pkg.environment(env_var).split())
	except errors.GentoolkitFatalError:
		# aux_get KeyError or other unexpected result
		return False

	if query in results:
		return True

	return False


def display_pkg(query, env_var, pkg):
	"""Display information for a given package."""

	if CONFIG['verbose']:
		pkgstr = PackageFormatter(
			pkg,
			do_format=True,
			custom_format=QUERY_OPTS["package_format"]
		)
	else:
		pkgstr = PackageFormatter(
			pkg,
			do_format=False,
			custom_format=QUERY_OPTS["package_format"]
		)

	if (QUERY_OPTS["in_installed"] and
		not QUERY_OPTS["in_porttree"] and
		not QUERY_OPTS["in_overlay"]):
		if not 'I' in  pkgstr.location:
			return False
	if (QUERY_OPTS["in_porttree"] and
		not QUERY_OPTS["in_overlay"]):
		if not 'P' in  pkgstr.location:
			return False
	if (QUERY_OPTS["in_overlay"] and
		not QUERY_OPTS["in_porttree"]):
		if not 'O' in  pkgstr.location:
			return False
	pp.uprint(pkgstr)

	return True


def parse_module_options(module_opts):
	"""Parse module options and update QUERY_OPTS"""

	# Parse module options
	opts = (x[0] for x in module_opts)
	posargs = (x[1] for x in module_opts)
	for opt, posarg in zip(opts, posargs):
		if opt in ('-h', '--help'):
			print_help()
			sys.exit(0)
		elif opt in ('-I', '--exclue-installed'):
			QUERY_OPTS['in_installed'] = False
		elif opt in ('-p', '--portage-tree'):
			QUERY_OPTS['in_porttree'] = True
		elif opt in ('-o', '--overlay-tree'):
			QUERY_OPTS['in_overlay'] = True
		elif opt in ('-F', '--format'):
			QUERY_OPTS["package_format"] = posarg
		elif opt in ('--package'):
			QUERY_OPTS["package_filter"] = posarg


def main(input_args):
	"""Parse input and run the program"""

	short_opts = "hiIpoF:" # -i was option for default action
	# --installed is no longer needed, kept for compatibility (djanderson '09)
	long_opts = ('help', 'installed', 'exclude-installed', 'portage-tree',
		'overlay-tree', 'format=', 'package=')

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

	query_scope = QUERY_OPTS['package_filter'] or '*'
	matches = Query(query_scope).smart_find(**QUERY_OPTS)
	matches.sort()

	# split out the first query since it is suppose to be the env_var
	QUERY_OPTS['env_var'] = queries.pop(0)
	env_var = QUERY_OPTS['env_var']

	#
	# Output
	#

	if not queries:
		if not QUERY_OPTS['package_filter']:
			err = "Used ENV_VAR without match_expression or --package"
			raise errors.GentoolkitFatalError(err, is_serious=False)
		else:
			if len(matches) > 1:
				raise errors.AmbiguousPackageName(matches)
			for match in matches:
				env = QUERY_OPTS['env_var']
				print(match.environment(env))

	first_run = True
	got_match = False
	for query in queries:
		if not first_run:
			print()

		if CONFIG['verbose']:
			status = " * Searching for {0} {1} ... "
			pp.uprint(status.format(env_var, pp.emph(query)))

		for pkg in matches:
			if query_in_env(query, env_var, pkg):
				display_pkg(query, env_var, pkg)
				got_match = True
		first_run = False

	if not got_match:
		sys.exit(1)

# vim: set ts=4 sw=4 tw=79:
