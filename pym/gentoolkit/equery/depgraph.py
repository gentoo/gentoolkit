# Copyright(c) 2009, Gentoo Foundation
#
# Licensed under the GNU General Public License, v2
#
# $Header: $

"""Display a direct dependency graph for a given package"""

from __future__ import print_function

__docformat__ = 'epytext'

# =======
# Imports
# =======

import sys
from functools import partial
from getopt import gnu_getopt, GetoptError

import portage

import gentoolkit.pprinter as pp
from gentoolkit import errors
from gentoolkit.equery import format_options, mod_usage, CONFIG
from gentoolkit.keyword import determine_keyword
from gentoolkit.query import Query

# =======
# Globals
# =======

QUERY_OPTS = {
	"depth": 1,
	"no_atom": False,
	"no_indent": False,
	"no_useflags": False,
	"no_mask": False,
	"in_installed": True,
	"in_porttree": True,
	"in_overlay": True,
	"include_masked": True,
	"show_progress": (not CONFIG['quiet'])
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
	print("Default depth is set to 1 (direct only). Use --depth=0 for no max.")
	print()
	print(mod_usage(mod_name="depgraph"))
	print()
	print(pp.command("options"))
	print(format_options((
		(" -h, --help", "display this help message"),
		(" -A, --no-atom", "do not show dependency atom"),
		(" -M, --no-mask", "do not show masking status"),
		(" -U, --no-useflags", "do not show USE flags"),
		(" -l, --linear", "do not format the graph by indenting dependencies"),
		("     --depth=N", "limit dependency graph to specified depth")
	)))


def parse_module_options(module_opts):
	"""Parse module options and update QUERY_OPTS"""

	opts = (x[0] for x in module_opts)
	posargs = (x[1] for x in module_opts)
	for opt, posarg in zip(opts, posargs):
		if opt in ('-h', '--help'):
			print_help()
			sys.exit(0)
		if opt in ('-A', '--no-atom'):
			QUERY_OPTS["no_atom"] = True
		if opt in ('-U', '--no-useflags'):
			QUERY_OPTS["no_useflags"] = True
		if opt in ('-M', '--no-mask'):
			QUERY_OPTS["no_mask"] = True
		if opt in ('-l', '--linear'):
			QUERY_OPTS["no_indent"] = True
		if opt in ('--depth'):
			if posarg.isdigit():
				depth = int(posarg)
			else:
				err = "Module option --depth requires integer (got '%s')"
				sys.stderr.write(pp.error(err % posarg))
				print()
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
	initial_pkg=False,
	no_mask=False
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
	atom = ''
	mask = ''
	try:
		if not no_atom:
			if dep.operator == '=*':
				atom += ' (=%s*)' % dep.cpv
			else:
				atom += ' (%s%s)' % (dep.operator, dep.cpv)
		if not no_use and dep is not None and dep.use:
			use = ' [%s]' % ' '.join(
				pp.useflag(x, enabled=True) for x in dep.use.tokens
			)
	except AttributeError:
		# 'NoneType' object has no attribute 'atom'
		pass
	if pkg and not no_mask:
		mask = pkg.mask_status()
		if not mask:
			mask = [determine_keyword(portage.settings["ARCH"],
				portage.settings["ACCEPT_KEYWORDS"],
				pkg.environment('KEYWORDS'))]
		mask = pp.masking(mask)
	try:
		pp.uprint(' '.join(
			(indent, decorator, pp.cpv(str(pkg.cpv)), atom, mask, use)
			))
	except AttributeError:
		# 'NoneType' object has no attribute 'cpv'
		pp.uprint(''.join((indent, decorator, "(no match for %r)" % dep.atom)))


def make_depgraph(pkg, printer_fn):
	"""Create and display depgraph for each package."""

	print()
	if CONFIG['verbose']:
		pp.uprint(" * " + pp.subsection("dependency graph for ") +
			pp.cpv(str(pkg.cpv)))
	else:
		pp.uprint("%s:" % pkg.cpv)

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
		pp.uprint(info % (pkgname, n_packages, max_seen))


def main(input_args):
	"""Parse input and run the program"""

	short_opts = "hAMUl"
	long_opts = ('help', 'no-atom', 'no-useflags', 'no-mask', 'depth=')

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

	#
	# Output
	#

	first_run = True
	for query in (Query(x) for x in queries):
		if not first_run:
			print()

		matches = query.smart_find(**QUERY_OPTS)

		if not matches:
			raise errors.GentoolkitNoMatches(query)

		matches.sort()

		if CONFIG['verbose']:
			printer = partial(
				depgraph_printer,
				no_atom=QUERY_OPTS['no_atom'],
				no_indent=QUERY_OPTS['no_indent'],
				no_use=QUERY_OPTS['no_useflags'],
				no_mask=QUERY_OPTS['no_mask']
			)
		else:
			printer = partial(
				depgraph_printer,
				no_atom=True,
				no_indent=True,
				no_use=True,
				no_mask=True
			)

		for pkg in matches:
			make_depgraph(pkg, printer)

		first_run = False

# vim: set ts=4 sw=4 tw=79:
