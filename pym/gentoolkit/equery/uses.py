# Copyright(c) 2009, Gentoo Foundation
#
# Licensed under the GNU General Public License, v2
#
# $Header: $

"""Display USE flags for a given package"""

from __future__ import print_function

__docformat__ = 'epytext'

# =======
# Imports
# =======

import os
import sys
from functools import partial
from getopt import gnu_getopt, GetoptError
from glob import glob

from portage import settings

import gentoolkit.pprinter as pp
from gentoolkit import errors
from gentoolkit.equery import format_options, mod_usage, CONFIG
from gentoolkit.helpers import uniqify
from gentoolkit.textwrap_ import TextWrapper
from gentoolkit.query import Query
from gentoolkit.flag import get_flags, reduce_flags

# =======
# Globals
# =======

QUERY_OPTS = {"all_versions" : False, "ignore_linguas" : False}

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
	print(mod_usage(mod_name=__name__.split('.')[-1]))
	print()
	print(pp.command("options"))
	print(format_options((
		(" -h, --help", "display this help message"),
		(" -a, --all", "include all package versions"),
		(" -i, --ignore-linguas", "don't show linguas USE flags")
	)))


def display_useflags(output):
	"""Print USE flag descriptions and statuses.

	@type output: list
	@param output: [(inuse, inused, flag, desc, restrict), ...]
		inuse (int) = 0 or 1; if 1, flag is set in make.conf
		inused (int) = 0 or 1; if 1, package is installed with flag enabled
		flag (str) = the name of the USE flag
		desc (str) = the flag's description
		restrict (str) = corresponds to the text of restrict in metadata
	"""

	maxflag_len = len(max([t[2] for t in output], key=len))

	twrap = TextWrapper()
	twrap.width = CONFIG['termWidth']
	twrap.subsequent_indent = " " * (maxflag_len + 8)

	markers = ("-", "+")
	color = (
		partial(pp.useflag, enabled=False), partial(pp.useflag, enabled=True)
	)
	for in_makeconf, in_installed, flag, desc, restrict in output:
		if CONFIG['verbose']:
			flag_name = ""
			if in_makeconf != in_installed:
				flag_name += pp.emph(" %s %s" %
					(markers[in_makeconf], markers[in_installed]))
			else:
				flag_name += (" %s %s" %
					(markers[in_makeconf], markers[in_installed]))

			flag_name += " " + color[in_makeconf](flag.ljust(maxflag_len))
			flag_name += " : "

			# Strip initial whitespace at the start of the description
			# Bug 432530
			if desc:
				desc = desc.lstrip()

			# print description
			if restrict:
				restrict = "(%s %s)" % (pp.emph("Restricted to"),
					pp.cpv(restrict))
				twrap.initial_indent = flag_name
				pp.uprint(twrap.fill(restrict))
				if desc:
					twrap.initial_indent = twrap.subsequent_indent
					pp.uprint(twrap.fill(desc))
				else:
					print(" : <unknown>")
			else:
				if desc:
					twrap.initial_indent = flag_name
					desc = twrap.fill(desc)
					pp.uprint(desc)
				else:
					twrap.initial_indent = flag_name
					print(twrap.fill("<unknown>"))
		else:
			pp.uprint(markers[in_makeconf] + flag)


def get_global_useflags():
	"""Get global and expanded USE flag variables from
	PORTDIR/profiles/use.desc and PORTDIR/profiles/desc/*.desc respectively.

	@rtype: dict
	@return: {'flag_name': 'flag description', ...}
	"""

	global_usedesc = {}
	# Get global USE flag descriptions
	try:
		path = os.path.join(settings["PORTDIR"], 'profiles', 'use.desc')
		with open(path) as open_file:
			for line in open_file:
				if line.startswith('#'):
					continue
				# Ex. of fields: ['syslog', 'Enables support for syslog\n']
				fields = line.split(" - ", 1)
				if len(fields) == 2:
					global_usedesc[fields[0]] = fields[1].rstrip()
	except IOError:
		sys.stderr.write(
			pp.warn(
				"Could not load USE flag descriptions from %s" % pp.path(path)
			)
		)

	del path, open_file
	# Add USE_EXPANDED variables to usedesc hash -- Bug #238005
	for path in glob(os.path.join(settings["PORTDIR"],
		'profiles', 'desc', '*.desc')):
		try:
			with open(path) as open_file:
				for line in open_file:
					if line.startswith('#'):
						continue
					fields = [field.strip() for field in line.split(" - ", 1)]
					if len(fields) == 2:
						expanded_useflag = "%s_%s" % \
							(path.split("/")[-1][0:-5], fields[0])
						global_usedesc[expanded_useflag] = fields[1]
		except IOError:
			sys.stderr.write(
				pp.warn("Could not load USE flag descriptions from %s" % path)
			)

	return global_usedesc


def get_output_descriptions(pkg, global_usedesc):
	"""Prepare descriptions and usage information for each USE flag."""

	if pkg.metadata is None:
		local_usedesc = []
	else:
		local_usedesc = pkg.metadata.use()

	iuse, final_use = get_flags(pkg.cpv, final_setting=True)
	usevar = reduce_flags(iuse)
	usevar.sort()

	if QUERY_OPTS['ignore_linguas']:
		for a in usevar[:]:
			if a.startswith("linguas_"):
				usevar.remove(a)


	if pkg.is_installed():
		used_flags = pkg.use().split()
	else:
		used_flags = settings["USE"].split()

	# store (inuse, inused, flag, desc, restrict)
	output = []
	for flag in usevar:
		inuse = False
		inused = False

		local_use = None
		for use in local_usedesc:
			if use.name == flag:
				local_use = use
				break

		try:
			desc = local_use.description
		except AttributeError:
			try:
				desc = global_usedesc[flag]
			except KeyError:
				desc = ""

		try:
			restrict = local_use.restrict
			restrict = restrict if restrict is not None else ""
		except AttributeError:
			restrict = ""

		if flag in final_use:
			inuse = True
		if flag in used_flags:
			inused = True

		output.append((inuse, inused, flag, desc, restrict))

	return output


def parse_module_options(module_opts):
	"""Parse module options and update QUERY_OPTS"""

	opts = (x[0] for x in module_opts)
	for opt in opts:
		if opt in ('-h', '--help'):
			print_help()
			sys.exit(0)
		elif opt in ('-a', '--all'):
			QUERY_OPTS['all_versions'] = True
		elif opt in ('-i', '--ignore-linguas'):
			QUERY_OPTS['ignore_linguas'] = True


def print_legend():
	"""Print a legend to explain the output format."""

	print("[ Legend : %s - final flag setting for installation]" % pp.emph("U"))
	print("[        : %s - package is installed with flag     ]" % pp.emph("I"))
	print("[ Colors : %s, %s                             ]" % (
		pp.useflag("set", enabled=True), pp.useflag("unset", enabled=False)))


def main(input_args):
	"""Parse input and run the program"""

	short_opts = "hai"
	long_opts = ('help', 'all', 'ignore-linguas')

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
	legend_printed = False
	for query in (Query(x) for x in queries):
		if not first_run:
			print()

		if QUERY_OPTS["all_versions"]:
			matches = query.find(include_masked=True)
		else:
			matches = [query.find_best()]

		if not any(matches):
			raise errors.GentoolkitNoMatches(query)

		matches.sort()

		global_usedesc = get_global_useflags()
		for pkg in matches:

			output = get_output_descriptions(pkg, global_usedesc)
			if output:
				if CONFIG['verbose']:
					if not legend_printed:
						print_legend()
						legend_printed = True
					print((" * Found these USE flags for %s:" %
						pp.cpv(str(pkg.cpv))))
					print(pp.emph(" U I"))
				display_useflags(output)
			else:
				if CONFIG['verbose']:
					sys.stderr.write(
						pp.warn("No USE flags found for %s" % pp.cpv(pkg.cpv))
					)

		first_run = False

# vim: set ts=4 sw=4 tw=79:
