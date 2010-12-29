# Copyright(c) 2009, Gentoo Foundation
#
# Licensed under the GNU General Public License, v2
#
# $Header: $

"""List all packages that depend on a atom given query"""

from __future__ import print_function

__docformat__ = 'epytext'

# =======
# Imports
# =======

import sys
from getopt import gnu_getopt, GetoptError

import gentoolkit.pprinter as pp
from gentoolkit.dependencies import Dependencies
from gentoolkit.equery import format_options, mod_usage, CONFIG
from gentoolkit.helpers import get_cpvs, get_installed_cpvs
from gentoolkit.cpv import CPV

# =======
# Globals
# =======

QUERY_OPTS = {
	"include_masked": False,
	"only_direct": True,
	"max_depth": -1,
}

# =======
# Classes
# =======

class DependPrinter(object):
	"""Output L{gentoolkit.dependencies.Dependencies} objects."""
	def __init__(self, verbose=True):
		self.verbose = verbose

		if verbose:
			self.print_fn = self.print_verbose
		else:
			self.print_fn = self.print_quiet

	def __call__(self, dep, dep_is_displayed=False):
		self.format_depend(dep, dep_is_displayed)

	@staticmethod
	def print_verbose(indent, cpv, use_conditional, depatom):
		"""Verbosely prints a set of dep strings."""

		sep = ' ? ' if (depatom and use_conditional) else ''
		pp.uprint(indent + pp.cpv(cpv), "(" + use_conditional +
			sep + depatom + ")")

	# W0613: *Unused argument %r*
	# pylint: disable-msg=W0613
	@staticmethod
	def print_quiet(indent, cpv, use_conditional, depatom):
		"""Quietly prints a subset set of dep strings."""

		pp.uprint(indent + cpv)

	def format_depend(self, dep, dep_is_displayed):
		"""Format a dependency for printing.

		@type dep: L{gentoolkit.dependencies.Dependencies}
		@param dep: the dependency to display
		"""

		# Don't print blank lines
		if dep_is_displayed and not self.verbose:
			return

		depth = getattr(dep, 'depth', 0)
		indent = " " * depth
		mdep = dep.matching_dep
		use_conditional = ""
		if mdep.use_conditional:
			use_conditional = " & ".join(
				pp.useflag(u) for u in mdep.use_conditional.split()
			)
		if mdep.operator == '=*':
			formatted_dep = '=%s*' % str(mdep.cpv)
		else:
			formatted_dep = mdep.operator + str(mdep.cpv)
		if mdep.slot:
			formatted_dep += pp.emph(':') + pp.slot(mdep.slot)
		if mdep.use:
			useflags = pp.useflag(','.join(mdep.use.tokens))
			formatted_dep += (pp.emph('[') + useflags + pp.emph(']'))

		if dep_is_displayed:
			indent = indent + " " * len(str(dep.cpv))
			self.print_fn(indent, '', use_conditional, formatted_dep)
		else:
			self.print_fn(indent, str(dep.cpv), use_conditional, formatted_dep)

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
	print(mod_usage(mod_name="depends"))
	print()
	print(pp.command("options"))
	print(format_options((
		(" -h, --help", "display this help message"),
		(" -a, --all-packages",
			"include dependencies that are not installed (slow)"),
		(" -D, --indirect",
			"search both direct and indirect dependencies"),
		("     --depth=N", "limit indirect dependency tree to specified depth")
	)))


def parse_module_options(module_opts):
	"""Parse module options and update QUERY_OPTS"""

	opts = (x[0] for x in module_opts)
	posargs = (x[1] for x in module_opts)
	for opt, posarg in zip(opts, posargs):
		if opt in ('-h', '--help'):
			print_help()
			sys.exit(0)
		elif opt in ('-a', '--all-packages'):
			QUERY_OPTS['include_masked'] = True
		elif opt in ('-D', '--indirect'):
			QUERY_OPTS['only_direct'] = False
		elif opt in ('--depth'):
			if posarg.isdigit():
				depth = int(posarg)
			else:
				err = "Module option --depth requires integer (got '%s')"
				sys.stdout.write(pp.error(err % posarg))
				print()
				print_help(with_description=False)
				sys.exit(2)
			QUERY_OPTS["max_depth"] = depth


def main(input_args):
	"""Parse input and run the program"""
	short_opts = "hadD" # -d, --direct was old option for default action
	long_opts = ('help', 'all-packages', 'direct', 'indirect', 'depth=')

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

	dep_print = DependPrinter(verbose=CONFIG['verbose'])

	first_run = True
	got_match = False
	for query in queries:
		if not first_run:
			print()

		pkg = Dependencies(query)
		if QUERY_OPTS['include_masked']:
			pkggetter = get_cpvs
		else:
			pkggetter = get_installed_cpvs

		if CONFIG['verbose']:
			print(" * These packages depend on %s:" % pp.emph(pkg.cpv))
		if pkg.graph_reverse_depends(
			pkgset=sorted(pkggetter(), key=CPV),
			max_depth=QUERY_OPTS["max_depth"],
			only_direct=QUERY_OPTS["only_direct"],
			printer_fn=dep_print
		):
			got_match = True

		first_run = False

	if not got_match:
		sys.exit(1)

# vim: set ts=4 sw=4 tw=79:
