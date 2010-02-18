# Copyright(c) 2009-2010, Gentoo Foundation
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

import gentoolkit.pprinter as pp
from gentoolkit import errors
from gentoolkit.equery import format_options, mod_usage, CONFIG
from gentoolkit.helpers import do_lookup
from gentoolkit.package import PackageFormatter

# =======
# Globals
# =======

QUERY_OPTS = {
	"categoryFilter": None,
	"includeInstalled": True,
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
		(" -I, --exclude-installed",
			"exclude installed packages from search path"),
		(" -o, --overlay-tree", "include overlays in search path"),
		(" -p, --portage-tree", "include entire portage tree in search path")
	))


def display_useflags(query, pkg):
	"""Display USE flag information for a given package."""

	try:
		useflags = [x.lstrip("+-") for x in pkg.environment("IUSE").split()]
	except errors.GentoolkitFatalError:
		# aux_get KeyError or other unexpected result
		return

	if query not in useflags:
		return

	if CONFIG['verbose']:
		fmt_pkg = PackageFormatter(pkg, do_format=True)
	else:
		fmt_pkg = PackageFormatter(pkg, do_format=False)

	if (QUERY_OPTS["includeInstalled"] and
		not QUERY_OPTS["includePortTree"] and
		not QUERY_OPTS["includeOverlayTree"]):
		if not 'I' in fmt_pkg.location:
			return
	if (QUERY_OPTS["includePortTree"] and
		not QUERY_OPTS["includeOverlayTree"]):
		if not 'P' in fmt_pkg.location:
			return
	if (QUERY_OPTS["includeOverlayTree"] and
		not QUERY_OPTS["includePortTree"]):
		if not 'O' in fmt_pkg.location:
			return
	print fmt_pkg



def parse_module_options(module_opts):
	"""Parse module options and update QUERY_OPTS"""

	# Parse module options
	opts = (x[0] for x in module_opts)
	for opt in opts:
		if opt in ('-h', '--help'):
			print_help()
			sys.exit(0)
		elif opt in ('-I', '--exclue-installed'):
			QUERY_OPTS['includeInstalled'] = False
		elif opt in ('-p', '--portage-tree'):
			QUERY_OPTS['includePortTree'] = True
		elif opt in ('-o', '--overlay-tree'):
			QUERY_OPTS['includeOverlayTree'] = True


def main(input_args):
	"""Parse input and run the program"""

	short_opts = "hiIpo" # -i was option for default action
	# --installed is no longer needed, kept for compatibility (djanderson '09)
	long_opts = ('help', 'installed', 'exclude-installed', 'portage-tree',
		'overlay-tree')

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

	matches = do_lookup("*", QUERY_OPTS)
	matches.sort()

	#
	# Output
	#

	first_run = True
	for query in queries:
		if not first_run:
			print

		if CONFIG['verbose']:
			print " * Searching for USE flag %s ... " % pp.emph(query)

		for pkg in matches:
			display_useflags(query, pkg)
		first_run = False

# vim: set ts=4 sw=4 tw=79:
