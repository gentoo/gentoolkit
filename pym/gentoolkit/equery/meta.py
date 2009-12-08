# Copyright(c) 2009, Gentoo Foundation
#
# Licensed under the GNU General Public License, v2 or higher
#
# $Header: $

"""Display metadata about a given package"""

# Move to Imports section after Python-2.6 is stable
from __future__ import with_statement

__docformat__ = 'epytext'

# =======
# Imports
# =======

import os
import re
import sys
from getopt import gnu_getopt, GetoptError

import gentoolkit.pprinter as pp
from gentoolkit import errors
from gentoolkit.equery import format_options, mod_usage, CONFIG
from gentoolkit.helpers import find_packages, print_sequence, print_file
from gentoolkit.textwrap_ import TextWrapper

# =======
# Globals
# =======

# E1101: Module 'portage.output' has no $color member
# portage.output creates color functions dynamically
# pylint: disable-msg=E1101

QUERY_OPTS = {
	'current': False,
	'description': False,
	'herd': False,
	'keywords': False,
	'maintainer': False,
	'useflags': False,
	'upstream': False,
	'xml': False
}

# =========
# Functions
# =========

def print_help(with_description=True, with_usage=True):
	"""Print description, usage and a detailed help message.

	@type with_description: bool
	@param with_description: if true, print module's __doc__ string
	"""

	if with_description:
		print __doc__.strip()
		print
	if with_usage:
		print mod_usage(mod_name="meta")
		print
	print pp.command("options")
	print format_options((
		(" -h, --help", "display this help message"),
		(" -d, --description", "show an extended package description"),
		(" -H, --herd", "show the herd(s) for the package"),
		(" -k, --keywords", "show keywords for all matching package versions"),
		(" -m, --maintainer", "show the maintainer(s) for the package"),
		(" -u, --useflags", "show per-package USE flag descriptions"),
		(" -U, --upstream", "show package's upstream information"),
		(" -x, --xml", "show the plain metadata.xml file")
	))


def format_herds(herds):
	"""Format herd information for display."""

	result = []
	for herd in herds:
		herdstr = ''
		email = "(%s)" % herd[1] if herd[1] else ''
		herdstr = herd[0]
		if CONFIG['verbose']:
			herdstr += " %s" % (email,)
		result.append(herdstr)

	return result


def format_maintainers(maints):
	"""Format maintainer information for display."""

	result = []
	for maint in maints:
		maintstr = ''
		maintstr = maint.email
		if CONFIG['verbose']:
			maintstr += " (%s)" % (maint.name,) if maint.name else ''
			maintstr += "\n%s" % (maint.description,) \
				if maint.description else ''
		result.append(maintstr)

	return result


def format_upstream(upstream):
	"""Format upstream information for display."""

	def _format_upstream_docs(docs):
		result = []
		for doc in docs:
			doc_location = doc[0]
			doc_lang = doc[1]
			docstr = doc_location
			if doc_lang is not None:
				docstr += " (%s)" % (doc_lang,)
			result.append(docstr)
		return result

	def _format_upstream_ids(ids):
		result = []
		for id_ in ids:
			site = id_[0]
			proj_id = id_[1]
			idstr = "%s ID: %s" % (site, proj_id)
			result.append(idstr)
		return result

	result = []
	for up in upstream:
		upmaints = format_maintainers(up.maintainers)
		for upmaint in upmaints:
			result.append(format_line(upmaint, "Maintainer:  ", " " * 13))

		for upchange in up.changelogs:
			result.append(format_line(upchange, "ChangeLog:   ", " " * 13))

		updocs = _format_upstream_docs(up.docs)
		for updoc in updocs:
			result.append(format_line(updoc, "Docs:       ", " " * 13))

		for upbug in up.bugtrackers:
			result.append(format_line(upbug, "Bugs-to:     ", " " * 13))

		upids = _format_upstream_ids(up.remoteids)
		for upid in upids:
			result.append(format_line(upid, "Remote-ID:   ", " " * 13))

	return result


def format_useflags(useflags):
	"""Format USE flag information for display."""

	result = []
	for flag in useflags:
		result.append(pp.useflag(flag.name))
		result.append(flag.description)
		result.append("")

	return result


def format_keywords(match):
	"""Format keywords information for display."""

	kwsplit = match.get_env_var('KEYWORDS').split()
	ver = match.cpv.fullversion
	keywords = ''
	for kw in kwsplit:
		if kw.startswith('~'):
			keywords += " %s" % pp.useflag(kw, enabled=True)
		else:
			keywords += " %s" % pp.useflag(kw, enabled=False)

	if CONFIG['verbose']:
		result = format_line(
			keywords, "%s: " % pp.cpv(ver), " " * (len(ver) + 2)
			)
	else:
		result = "%s:%s" % (ver, keywords)

	return result

# R0912: *Too many branches (%s/%s)*
# pylint: disable-msg=R0912
def call_format_functions(matches):
	"""Call information gathering functions and display the results."""

	# Choose a good package to reference metadata from
	ref_pkg = get_reference_pkg(matches)

	if CONFIG['verbose']:
		repo = ref_pkg.get_repo_name()
		print " * %s [%s]" % (pp.cpv(ref_pkg.cpv.cp), pp.section(repo))

	got_opts = False
	if any(QUERY_OPTS.values()):
		# Specific information requested, less formatting
		got_opts = True

	if not got_opts:
		pkg_loc = ref_pkg.get_package_path()
		print format_line(pkg_loc, "Location:    ", " " * 13)

	if QUERY_OPTS["herd"] or not got_opts:
		herds = format_herds(ref_pkg.metadata.get_herds(include_email=True))
		if QUERY_OPTS["herd"]:
			print_sequence(format_list(herds))
		else:
			for herd in herds:
				print format_line(herd, "Herd:        ", " " * 13)

	if QUERY_OPTS["maintainer"] or not got_opts:
		maints = format_maintainers(ref_pkg.metadata.get_maintainers())
		if QUERY_OPTS["maintainer"]:
			print_sequence(format_list(maints))
		else:
			if not maints:
				print format_line([], "Maintainer:  ", " " * 13)
			else:
				for maint in maints:
					print format_line(maint, "Maintainer:  ", " " * 13)

	if QUERY_OPTS["upstream"] or not got_opts:
		upstream = format_upstream(ref_pkg.metadata.get_upstream())
		if QUERY_OPTS["upstream"]:
			upstream = format_list(upstream)
		else:
			upstream = format_list(upstream, "Upstream:    ", " " * 13)
		print_sequence(upstream)

	if QUERY_OPTS["keywords"] or not got_opts:
		for match in matches:
			kwds = format_keywords(match)
			if QUERY_OPTS["keywords"]:
				print kwds
			else:
				indent = " " * (15 + len(match.cpv.fullversion))
				print format_line(kwds, "Keywords:    ", indent)

	if QUERY_OPTS["description"]:
		desc = ref_pkg.metadata.get_descriptions()
		print_sequence(format_list(desc))

	if QUERY_OPTS["useflags"]:
		useflags = format_useflags(ref_pkg.metadata.get_useflags())
		print_sequence(format_list(useflags))

	if QUERY_OPTS["xml"]:
		print_file(os.path.join(ref_pkg.get_package_path(), 'metadata.xml'))


def format_line(line, first="", subsequent="", force_quiet=False):
	"""Wrap a string at word boundaries and optionally indent the first line
	and/or subsequent lines with custom strings.

	Preserve newlines if the longest line is not longer than
	CONFIG['termWidth']. To force the preservation of newlines and indents,
	split the string into a list and feed it to format_line via format_list.

	@see: format_list()
	@type line: string
	@param line: text to format
	@type first: string
	@param first: text to prepend to the first line
	@type subsequent: string
	@param subsequent: text to prepend to subsequent lines
	@type force_quiet: boolean
	@rtype: string
	@return: A wrapped line
	"""

	if line:
		line = line.expandtabs().strip("\n").splitlines()
	else:
		if force_quiet:
			return
		else:
			return first + "None specified"

	if len(first) > len(subsequent):
		wider_indent = first
	else:
		wider_indent = subsequent

	widest_line_len = len(max(line, key=len)) + len(wider_indent)

	if widest_line_len > CONFIG['termWidth']:
		twrap = TextWrapper(width=CONFIG['termWidth'], expand_tabs=False,
			initial_indent=first, subsequent_indent=subsequent)
		line = " ".join(line)
		line = re.sub("\s+", " ", line)
		line = line.lstrip()
		result = twrap.fill(line)
	else:
		# line will fit inside CONFIG['termWidth'], so preserve whitespace and
		# newlines
		line[0] = first + line[0]          # Avoid two newlines if len == 1

		if len(line) > 1:
			line[0] = line[0] + "\n"
			for i in range(1, (len(line[1:-1]) + 1)):
				line[i] = subsequent + line[i] + "\n"
			line[-1] = subsequent + line[-1]  # Avoid two newlines on last line

		if line[-1].isspace():
			del line[-1]                # Avoid trailing blank lines

		result = "".join(line)

	return result.encode("utf-8")


def format_list(lst, first="", subsequent="", force_quiet=False):
	"""Feed elements of a list to format_line().

	@see: format_line()
	@type lst: list
	@param lst: list to format
	@type first: string
	@param first: text to prepend to the first line
	@type subsequent: string
	@param subsequent: text to prepend to subsequent lines
	@rtype: list
	@return: list with element text wrapped at CONFIG['termWidth']
	"""

	result = []
	if lst:
		# Format the first line
		line = format_line(lst[0], first, subsequent, force_quiet)
		result.append(line)
		# Format subsequent lines
		for elem in lst[1:]:
			if elem:
				result.append(format_line(elem, subsequent, subsequent,
					force_quiet))
			else:
				# We don't want to send a blank line to format_line()
				result.append("")
	else:
		if CONFIG['verbose']:
			if force_quiet:
				result = None
			else:
				# Send empty list, we'll get back first + `None specified'
				result.append(format_line(lst, first, subsequent))

	return result


def get_reference_pkg(matches):
	"""Find a package in the Portage tree to reference."""

	pkg = None
	while list(reversed(matches)):
		pkg = matches.pop()
		if not pkg.is_overlay():
			break

	return pkg


def parse_module_options(module_opts):
	"""Parse module options and update QUERY_OPTS"""

	opts = (x[0] for x in module_opts)
	for opt in opts:
		if opt in ('-h', '--help'):
			print_help()
			sys.exit(0)
		elif opt in ('-d', '--description'):
			QUERY_OPTS["description"] = True
		elif opt in ('-H', '--herd'):
			QUERY_OPTS["herd"] = True
		elif opt in ('-m', '--maintainer'):
			QUERY_OPTS["maintainer"] = True
		elif opt in ('-k', '--keywords'):
			QUERY_OPTS["keywords"] = True
		elif opt in ('-u', '--useflags'):
			QUERY_OPTS["useflags"] = True
		elif opt in ('-U', '--upstream'):
			QUERY_OPTS["upstream"] = True
		elif opt in ('-x', '--xml'):
			QUERY_OPTS["xml"] = True


def main(input_args):
	"""Parse input and run the program."""

	short_opts = "hdHkmuUx"
	long_opts = ('help', 'description', 'herd', 'keywords', 'maintainer',
		'useflags', 'upstream', 'xml')

	try:
		module_opts, queries = gnu_getopt(input_args, short_opts, long_opts)
	except GetoptError, err:
		sys.stderr.write(pp.error("Module %s" % err))
		print
		print_help(with_description=False)
		sys.exit(2)

	parse_module_options(module_opts)

	# Find queries' Portage directory and throw error if invalid
	if not queries:
		print_help()
		sys.exit(2)

	first_run = True
	for query in queries:
		matches = find_packages(query, include_masked=True)
		if not matches:
			raise errors.GentoolkitNoMatches(query)

		if not first_run:
			print

		matches.sort()
		call_format_functions(matches)

		first_run = False

# vim: set ts=4 sw=4 tw=79:
