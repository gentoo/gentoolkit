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
from gentoolkit.equery import format_options, mod_usage, CONFIG
from gentoolkit.helpers import do_lookup, get_installed_cpvs
from gentoolkit.package import Package, PackageFormatter

# =======
# Globals
# =======

QUERY_OPTS = {
	"duplicates": False,
	"includeInstalled": True,
	"includePortTree": False,
	"includeOverlayTree": False,
	"includeMasked": True,
	"includeMaskReason": False,
	"isRegex": False,
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

	# Deprecation warning added by djanderson, 12/2008
	depwarning = (
		"Default action for this module has changed in Gentoolkit 0.3.",
		"Use globbing to simulate the old behavior (see man equery).",
		"Use '*' to check all installed packages.",
		"Use 'foo-bar/*' to filter by category."
	)
	for line in depwarning:
		sys.stderr.write(pp.warn(line))
	print

	print mod_usage(mod_name="list")
	print
	print pp.command("options")
	print format_options((
		(" -h, --help", "display this help message"),
		(" -d, --duplicates", "list only installed duplicate packages"),
		(" -f, --full-regex", "query is a regular expression"),
		(" -m, --mask-reason", "include reason for package mask"),
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
		if pkg.cpv.cp in dups:
			dups[pkg.cpv.cp].append(pkg)
		else:
			dups[pkg.cpv.cp] = [pkg]

	for cpv in dups.values():
		if len(cpv) > 1:
			result.extend(cpv)

	return result


def parse_module_options(module_opts):
	"""Parse module options and update QUERY_OPTS"""

	opts = (x[0] for x in module_opts)
	posargs = (x[1] for x in module_opts)
	for opt, posarg in zip(opts, posargs):
		if opt in ('-h', '--help'):
			print_help()
			sys.exit(0)
		elif opt in ('-I', '--exclude-installed'):
			QUERY_OPTS['includeInstalled'] = False
		elif opt in ('-p', '--portage-tree'):
			QUERY_OPTS['includePortTree'] = True
		elif opt in ('-o', '--overlay-tree'):
			QUERY_OPTS['includeOverlayTree'] = True
		elif opt in ('-f', '--full-regex'):
			QUERY_OPTS['isRegex'] = True
		elif opt in ('-m', '--mask-reason'):
			QUERY_OPTS['includeMaskReason'] = True
		elif opt in ('-e', '--exact-name'):
			sys.stderr.write(pp.warn("-e, --exact-name is now default."))
			sys.stderr.write(
				pp.warn("Use globbing to simulate the old behavior.")
			)
			print
		elif opt in ('-d', '--duplicates'):
			QUERY_OPTS['duplicates'] = True


def main(input_args):
	"""Parse input and run the program"""

	short_opts = "hdefiImop" # -i, -e were options for default actions

	# 04/09: djanderson
	# --all is no longer needed. Kept for compatibility.
	# --installed is no longer needed. Kept for compatibility.
	# --exact-name is no longer needed. Kept for compatibility.
	long_opts = ('help', 'all', 'installed', 'exclude-installed',
	'mask-reason', 'portage-tree', 'overlay-tree', 'full-regex', 'exact-name',
	'duplicates')

	try:
		module_opts, queries = gnu_getopt(input_args, short_opts, long_opts)
	except GetoptError, err:
		sys.stderr.write(pp.error("Module %s" % err))
		print
		print_help(with_description=False)
		sys.exit(2)

	parse_module_options(module_opts)

	# Only search installed packages when listing duplicate packages
	if QUERY_OPTS["duplicates"]:
		QUERY_OPTS["includeInstalled"] = True
		QUERY_OPTS["includePortTree"] = False
		QUERY_OPTS["includeOverlayTree"] = False
		QUERY_OPTS["includeMaskReason"] = False

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
			if CONFIG['verbose']:
				pkgstr = PackageFormatter(pkg, do_format=True)
			else:
				pkgstr = PackageFormatter(pkg, do_format=False)

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

			if QUERY_OPTS["includeMaskReason"]:
				ms_int, ms_orig = pkgstr.format_mask_status()
				if not ms_int > 2:
					# ms_int is a number representation of mask level.
					# Only 2 and above are "hard masked" and have reasons.
					continue
				mask_reason = pkg.mask_reason()
				if not mask_reason:
					# Package not on system or not masked
					continue
				elif not any(mask_reason):
					print " * No mask reason given"
				else:
					status = ', '.join(ms_orig)
					explanation = mask_reason[0]
					mask_location = mask_reason[1]
					print " * Masked by %r" % status
					print " * %s:" % mask_location
					print '\n'.join(
						[' * %s' % line.lstrip(' #')
							for line in explanation.splitlines()]
						)

		first_run = False

# vim: set ts=4 sw=4 tw=79:
