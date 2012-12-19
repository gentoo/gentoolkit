# Copyright(c) 2009, Gentoo Foundation
#
# Licensed under the GNU General Public License, v2 or higher
#
# $Header: $

"""List installed packages matching the query pattern"""

from __future__ import print_function

__docformat__ = 'epytext'

# =======
# Imports
# =======

import sys
from getopt import gnu_getopt, GetoptError

import gentoolkit
import gentoolkit.pprinter as pp
from gentoolkit import errors
from gentoolkit.equery import format_options, mod_usage, CONFIG
from gentoolkit.helpers import get_installed_cpvs
from gentoolkit.helpers import get_bintree_cpvs
from gentoolkit.package import PackageFormatter, FORMAT_TMPL_VARS
from gentoolkit.query import Query

# =======
# Globals
# =======

QUERY_OPTS = {
	"duplicates": False,
	"in_installed": True,
	"in_porttree": False,
	"in_overlay": False,
	"include_mask_reason": False,
	"is_regex": False,
	"show_progress": (not CONFIG['quiet']),
	"package_format": None,
	"binpkgs-missing": False
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

	# Deprecation warning added by djanderson, 12/2008
	depwarning = (
		"Default action for this module has changed in Gentoolkit 0.3.",
		"Use globbing to simulate the old behavior (see man equery).",
		"Use '*' to check all installed packages.",
		"Use 'foo-bar/*' to filter by category."
	)
	for line in depwarning:
		sys.stderr.write(pp.warn(line))
	print()

	print(mod_usage(mod_name="list"))
	print()
	print(pp.command("options"))
	print(format_options((
		(" -h, --help", "display this help message"),
		(" -d, --duplicates", "list only installed duplicate packages"),
		(" -b, --binpkgs-missing", "list only installed packages without a corresponding binary package"),
		(" -f, --full-regex", "query is a regular expression"),
		(" -m, --mask-reason", "include reason for package mask"),
		(" -I, --exclude-installed",
			"exclude installed packages from output"),
		(" -o, --overlay-tree", "list packages in overlays"),
		(" -p, --portage-tree", "list packages in the main portage tree"),
		(" -F, --format=TMPL", "specify a custom output format"),
        ("              TMPL",
			"a format template using (see man page):")
	)))
	print(" " * 24, ', '.join(pp.emph(x) for x in FORMAT_TMPL_VARS))


def get_duplicates(matches):
	"""Return only packages that have more than one version installed."""

	dups = {}
	result = []
	for pkg in matches:
		if pkg.cp in dups:
			dups[pkg.cp].append(pkg)
		else:
			dups[pkg.cp] = [pkg]

	for cpv in dups.values():
		if len(cpv) > 1:
			result.extend(cpv)

	return result


def get_binpkgs_missing(matches):
	"""Return only packages that do not have a corresponding binary package."""

	result = []
	binary_packages = set(get_bintree_cpvs())
	matched_packages = set(x.cpv for x in matches)
	missing_binary_packages = set(matched_packages.difference(binary_packages))

	for pkg in matches:
		if pkg.cpv in missing_binary_packages:
			result.append(pkg)
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
			QUERY_OPTS['in_installed'] = False
		elif opt in ('-p', '--portage-tree'):
			QUERY_OPTS['in_porttree'] = True
		elif opt in ('-o', '--overlay-tree'):
			QUERY_OPTS['in_overlay'] = True
		elif opt in ('-f', '--full-regex'):
			QUERY_OPTS['is_regex'] = True
		elif opt in ('-m', '--mask-reason'):
			QUERY_OPTS['include_mask_reason'] = True
		elif opt in ('-e', '--exact-name'):
			sys.stderr.write(pp.warn("-e, --exact-name is now default."))
			sys.stderr.write(
				pp.warn("Use globbing to simulate the old behavior.")
			)
			print()
		elif opt in ('-d', '--duplicates'):
			QUERY_OPTS['duplicates'] = True
		elif opt in ('-b', '--binpkgs-missing'):
			QUERY_OPTS['binpkgs-missing'] = True
		elif opt in ('-F', '--format'):
			QUERY_OPTS["package_format"] = posarg


def main(input_args):
	"""Parse input and run the program"""

	short_opts = "hdbefiImopF:" # -i, -e were options for default actions

	# 04/09: djanderson
	# --all is no longer needed. Kept for compatibility.
	# --installed is no longer needed. Kept for compatibility.
	# --exact-name is no longer needed. Kept for compatibility.
	long_opts = ('help', 'all', 'installed', 'exclude-installed',
		'mask-reason', 'portage-tree', 'overlay-tree', 'format=', 'full-regex',
		'exact-name', 'duplicates', 'binpkgs-missing')

	try:
		module_opts, queries = gnu_getopt(input_args, short_opts, long_opts)
	except GetoptError as err:
		sys.stderr.write(pp.error("Module %s" % err))
		print()
		print_help(with_description=False)
		sys.exit(2)

	parse_module_options(module_opts)

	# Only search installed packages when listing duplicate or missing binary packages
	if QUERY_OPTS["duplicates"] or QUERY_OPTS["binpkgs-missing"]:
		QUERY_OPTS["in_installed"] = True
		QUERY_OPTS["in_porttree"] = False
		QUERY_OPTS["in_overlay"] = False
		QUERY_OPTS["include_mask_reason"] = False

	if not queries:
		print_help()
		sys.exit(2)

	first_run = True
	for query in (Query(x, QUERY_OPTS['is_regex']) for x in queries):
		if not first_run:
			print()

		# if we are in quiet mode, do not raise GentoolkitNoMatches exception
		# instead we raise GentoolkitNonZeroExit to exit with an exit value of 3
		try:
			matches = query.smart_find(**QUERY_OPTS)
		except errors.GentoolkitNoMatches:
			if CONFIG['verbose']:
				raise
			else:
				raise errors.GentoolkitNonZeroExit(3)

		# Find duplicate packages
		if QUERY_OPTS["duplicates"]:
			matches = get_duplicates(matches)

		# Find missing binary packages
		if QUERY_OPTS["binpkgs-missing"]:
			matches = get_binpkgs_missing(matches)

		matches.sort()

		#
		# Output
		#

		for pkg in matches:
			pkgstr = PackageFormatter(
				pkg,
				do_format=CONFIG['verbose'],
				custom_format=QUERY_OPTS["package_format"]
			)

			if (QUERY_OPTS["in_porttree"] and
				not QUERY_OPTS["in_overlay"]):
				if not 'P' in pkgstr.location:
					continue
			if (QUERY_OPTS["in_overlay"] and
				not QUERY_OPTS["in_porttree"]):
				if not 'O' in pkgstr.location:
					continue
			pp.uprint(pkgstr)

			if QUERY_OPTS["include_mask_reason"]:
				ms_int, ms_orig = pkgstr.format_mask_status()
				if ms_int < 3:
					# ms_int is a number representation of mask level.
					# Only 2 and above are "hard masked" and have reasons.
					continue
				mask_reason = pkg.mask_reason()
				if not mask_reason:
					# Package not on system or not masked
					continue
				elif not any(mask_reason):
					print(" * No mask reason given")
				else:
					status = ', '.join(ms_orig)
					explanation = mask_reason[0]
					mask_location = mask_reason[1]
					pp.uprint(" * Masked by %r" % status)
					pp.uprint(" * %s:" % mask_location)
					pp.uprint('\n'.join(
						[' * %s' % line.lstrip(' #')
							for line in explanation.splitlines()]
						))

		first_run = False

# vim: set ts=4 sw=4 tw=79:
