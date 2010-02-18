# Copyright(c) 2009-2010, Gentoo Foundation
#
# Licensed under the GNU General Public License, v2
#
# $Header: $

"""Display a direct dependency graph for a given package"""

__docformat__ = 'epytext'

# =======
# Imports
# =======

import sys
from functools import partial
from getopt import gnu_getopt, GetoptError

import gentoolkit.pprinter as pp
from gentoolkit import errors
from gentoolkit.equery import format_options, mod_usage, CONFIG
from gentoolkit.helpers import do_lookup

# =======
# Globals
# =======

QUERY_OPTS = {
	"depth": 1,
	"noAtom": False,
	"noIndent": False,
	"noUseflags": False,
	"includeInstalled": True,
	"includePortTree": True,
	"includeOverlayTree": True,
	"includeMasked": True,
	"isRegex": False,
	"matchExact": True,
	"printMatchInfo": (not CONFIG['quiet'])
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
	print "Default depth is set to 1 (direct only). Use --depth=0 for no max."
	print
	print mod_usage(mod_name="depgraph")
	print
	print pp.command("options")
	print format_options((
		(" -h, --help", "display this help message"),
		(" -A, --no-atom", "do not show dependency atom"),
		(" -U, --no-useflags", "do not show USE flags"),
		(" -l, --linear", "do not format the graph by indenting dependencies"),
		("     --depth=N", "limit dependency graph to specified depth")
	))


def parse_module_options(module_opts):
	"""Parse module options and update QUERY_OPTS"""

	opts = (x[0] for x in module_opts)
	posargs = (x[1] for x in module_opts)
	for opt, posarg in zip(opts, posargs):
		if opt in ('-h', '--help'):
			print_help()
			sys.exit(0)
		if opt in ('-A', '--no-atom'):
			QUERY_OPTS["noAtom"] = True
		if opt in ('-U', '--no-useflags'):
			QUERY_OPTS["noUseflags"] = True
		if opt in ('-l', '--linear'):
			QUERY_OPTS["noIndent"] = True
		if opt in ('--depth'):
			if posarg.isdigit():
				depth = int(posarg)
			else:
				err = "Module option --depth requires integer (got '%s')"
				sys.stderr.write(pp.error(err % posarg))
				print
				print_help(with_description=False)
				sys.exit(2)
			QUERY_OPTS["depth"] = depth


def depgraph_printer(
	depth,
	pkg,
	dep,
	no_use=False,
	no_atom=False,
	no_indent=False,
	initial_pkg=False
):
	"""Display L{gentoolkit.dependencies.Dependencies.graph_depends} results.

	@type depth: int
	@param depth: depth of indirection, used to calculate indent
	@type pkg: L{gentoolkit.package.Package}
	@param pkg: "best match" package matched by B{dep}
	@type dep: L{gentoolkit.atom.Atom}
	@param dep: dependency that matched B{pkg}
	@type no_use: bool
	@param no_use: don't output USE flags
	@type no_atom: bool
	@param no_atom: don't output dep atom
	@type no_indent: bool
	@param no_indent: don't output indent based on B{depth}
	@type initial_pkg: bool
	@param initial_pkg: somewhat of a hack used to print the root package of
		the graph with absolutely no indent
	"""
	indent = '' if no_indent or initial_pkg else ' ' + (' ' * depth)
	decorator = '[%3d] ' % depth if no_indent else '`-- '
	use = ''
	try:
		atom = '' if no_atom else ' (%s)' % dep.atom
		if not no_use and dep is not None and dep.use:
			use = ' [%s]' % ' '.join(
				pp.useflag(x, enabled=True) for x in dep.use.tokens
			)
	except AttributeError:
		# 'NoneType' object has no attribute 'atom'
		atom = ''
	try:
		print ''.join((indent, decorator, pp.cpv(str(pkg.cpv)), atom, use))
	except AttributeError:
		# 'NoneType' object has no attribute 'cpv'
		print ''.join((indent, decorator, "(no match for %r)" % dep.atom))


def make_depgraph(pkg, printer_fn):
	"""Create and display depgraph for each package."""

	if CONFIG['verbose']:
		print " * direct dependency graph for %s:" % pp.cpv(str(pkg.cpv))
	else:
		print "%s:" % str(pkg.cpv)

	# Print out the first package
	printer_fn(0, pkg, None, initial_pkg=True)

	deps = pkg.deps.graph_depends(
		max_depth=QUERY_OPTS['depth'],
		printer_fn=printer_fn,
		# Use this to set this pkg as the graph's root; better way?
		result=[(0, pkg)]
	)

	if CONFIG['verbose']:
		pkgname = pp.cpv(str(pkg.cpv))
		n_packages = pp.number(str(len(deps)))
		max_seen = pp.number(str(max(x[0] for x in deps)))
		info = "[ %s stats: packages (%s), max depth (%s) ]"
		print info % (pkgname, n_packages, max_seen)


def main(input_args):
	"""Parse input and run the program"""

	short_opts = "hAUl"
	long_opts = ('help', 'no-atom', 'no-useflags', 'depth=')

	try:
		module_opts, queries = gnu_getopt(input_args, short_opts, long_opts)
	except GetoptError, err:
		sys.stderr.write(pp.error("Module %s" % err))
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
			raise errors.GentoolkitNoMatches(query)

		if CONFIG['verbose']:
			printer = partial(
				depgraph_printer,
				no_atom=QUERY_OPTS['noAtom'],
				no_indent=QUERY_OPTS['noIndent'],
				no_use=QUERY_OPTS['noUseflags']
			)
		else:
			printer = partial(
				depgraph_printer,
				no_atom=True,
				no_indent=True,
				no_use=True
			)

		for pkg in matches:
			make_depgraph(pkg, printer)

		first_run = False

# vim: set ts=4 sw=4 tw=79:
