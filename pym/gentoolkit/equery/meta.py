# Copyright(c) 2009, Gentoo Foundation
#
# Licensed under the GNU General Public License, v2 or higher
#
# $Header: $

"""Display metadata about a given package."""

from __future__ import print_function

__docformat__ = 'epytext'

# =======
# Imports
# =======

import re
import os
import sys
from getopt import gnu_getopt, GetoptError
from functools import partial

import gentoolkit.pprinter as pp
from gentoolkit import errors
from gentoolkit.keyword import Keyword
from gentoolkit.equery import format_options, mod_usage, CONFIG
from gentoolkit.helpers import print_sequence, print_file
from gentoolkit.textwrap_ import TextWrapper
from gentoolkit.query import Query

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
	'license': False,
	'maintainer': False,
	'stablereq': False,
	'useflags': False,
	'upstream': False,
	'xml': False
}

STABLEREQ_arches = {
	'alpha': 'alpha@gentoo.org',
	'amd64': 'amd64@gentoo.org',
	'arm': 'arm@gentoo.org',
	'hppa': 'hppa@gentoo.org',
	'ia64': 'ia64@gentoo.org',
	'm68k': 'm68k@gentoo.org',
	'ppc64': 'ppc64@gentoo.org',
	'ppc': 'ppc@gentoo.org',
	's390': 's390@gentoo.org',
	'sh': 'sh@gentoo.org',
	'sparc': 'sparc@gentoo.org',
	'x86': 'x86@gentoo.org',
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
		print(__doc__.strip())
		print()
	if with_usage:
		print(mod_usage(mod_name="meta"))
		print()
	print(pp.command("options"))
	print(format_options((
		(" -h, --help", "display this help message"),
		(" -d, --description", "show an extended package description"),
		(" -H, --herd", "show the herd(s) for the package"),
		(" -k, --keywords", "show keywords for all matching package versions"),
		(" -l, --license", "show licenses for the best maching version"),
		(" -m, --maintainer", "show the maintainer(s) for the package"),
		(" -S, --stablreq", "show STABLEREQ arches (cc's) for all matching package versions"),
		(" -u, --useflags", "show per-package USE flag descriptions"),
		(" -U, --upstream", "show package's upstream information"),
		(" -x, --xml", "show the plain metadata.xml file")
	)))

def stablereq(matches):
	"""Produce the list of cc's for a STABLREQ bug
	@type matches: array
	@param matches: set of L{gentoolkit.package.Package} instances whose
		'key' are all the same.
	@rtype: dict
	@return: a dict with L{gentoolkit.package.Package} instance keys and
		'array of cc's to be added to a STABLEREQ bug.
	"""
	result = {}
	for pkg in matches:
		keywords_str = pkg.environment(('KEYWORDS'), prefer_vdb=False)
		# get any unstable keywords
		keywords = set([x.lstrip('~') for x in keywords_str.split() if'~' in x])
		stable_arches = set(list(STABLEREQ_arches))
		cc_keywords = stable_arches.intersection(keywords)
		# add cc's
		result[pkg] = [STABLEREQ_arches[x] for x in cc_keywords]
	return result

def filter_keywords(matches):
	"""Filters non-unique keywords per slot.

	Does not filter arch mask keywords (-). Besides simple non-unique keywords,
	also remove unstable keywords (~) if a higher version in the same slot is
	stable. This view makes version bumps easier for package maintainers.

	@type matches: array
	@param matches: set of L{gentoolkit.package.Package} instances whose
		'key' are all the same.
	@rtype: dict
	@return: a dict with L{gentoolkit.package.Package} instance keys and
		'array of keywords not found in a higher version of pkg within the
		same slot' values.
	"""
	def del_archmask(keywords):
		"""Don't add arch_masked to filter set."""
		return [x for x in keywords if not x.startswith('-')]

	def add_unstable(keywords):
		"""Add unstable keyword for all stable keywords to filter set."""
		result = list(keywords)
		result.extend(
			['~%s' % x for x in keywords if not x.startswith(('-', '~'))]
		)
		return result

	result = {}
	slot_map = {}
	# Start from the newest
	rev_matches = reversed(matches)
	for pkg in rev_matches:
		keywords_str, slot = pkg.environment(('KEYWORDS', 'SLOT'),
			prefer_vdb=False)
		keywords = keywords_str.split()
		result[pkg] = [x for x in keywords if x not in slot_map.get(slot, [])]
		try:
			slot_map[slot].update(del_archmask(add_unstable(keywords)))
		except KeyError:
			slot_map[slot] = set(del_archmask(add_unstable(keywords)))

	return result


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
			maintstr += " - %s" % (maint.restrict,) if maint.restrict else ''
			maintstr += "\n%s" % (
				(maint.description,) if maint.description else ''
			)
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


def format_keywords(keywords):
	"""Sort and colorize keywords for display."""

	result = []

	for kw in sorted(keywords, key=Keyword):
		if kw.startswith('-'):
			# arch masked
			kw = pp.keyword(kw, stable=False, hard_masked=True)
		elif kw.startswith('~'):
			# keyword masked
			kw = pp.keyword(kw, stable=False, hard_masked=False)
		else:
			# stable
			kw = pp.keyword(kw, stable=True, hard_masked=False)
		result.append(kw)

	return ' '.join(result)


def format_keywords_line(pkg, fmtd_keywords, slot, verstr_len):
	"""Format the entire keywords line for display."""

	ver = pkg.fullversion
	result = "%s:%s: %s" % (ver, pp.slot(slot), fmtd_keywords)
	if CONFIG['verbose'] and fmtd_keywords:
		result = format_line(fmtd_keywords, "%s:%s: " % (ver, pp.slot(slot)),
			" " * (verstr_len + 2))

	return result


def format_stablereq_line(pkg, fmtd_ccs, slot):
	"""Format the entire stablereq line for display (no indented linewrapping)
	"""
	return "%s:%s: %s" % (pkg.fullversion, pp.slot(slot), fmtd_ccs)


def format_homepage(homepage):
	"""format the homepage(s) entries for dispaly"""
	result = []
	for page in homepage.split():
		result.append(format_line(page, "Homepage:    ", " " * 13))
	return result


# R0912: *Too many branches (%s/%s)*
# pylint: disable-msg=R0912
def call_format_functions(best_match, matches):
	"""Call information gathering functions and display the results."""

	if CONFIG['verbose']:
		repo = best_match.repo_name()
		pp.uprint(" * %s [%s]" % (pp.cpv(best_match.cp), pp.section(repo)))

	got_opts = False
	if any(QUERY_OPTS.values()):
		# Specific information requested, less formatting
		got_opts = True

	if QUERY_OPTS["herd"] or not got_opts:
		herds = best_match.metadata.herds(include_email=True)
		if any(not h[0] for h in herds):
			print(pp.warn("The packages metadata.xml has an empty <herd> tag"),
				file = sys.stderr)
			herds = [x for x in herds if x[0]]
		herds = format_herds(herds)
		if QUERY_OPTS["herd"]:
			print_sequence(format_list(herds))
		else:
			for herd in herds:
				pp.uprint(format_line(herd, "Herd:        ", " " * 13))

	if QUERY_OPTS["maintainer"] or not got_opts:
		maints = format_maintainers(best_match.metadata.maintainers())
		if QUERY_OPTS["maintainer"]:
			print_sequence(format_list(maints))
		else:
			if not maints:
				pp.uprint(format_line([], "Maintainer:  ", " " * 13))
			else:
				for maint in maints:
					pp.uprint(format_line(maint, "Maintainer:  ", " " * 13))

	if QUERY_OPTS["upstream"] or not got_opts:
		upstream = format_upstream(best_match.metadata.upstream())
		homepage = format_homepage(best_match.environment("HOMEPAGE"))
		if QUERY_OPTS["upstream"]:
			upstream = format_list(upstream)
		else:
			upstream = format_list(upstream, "Upstream:    ", " " * 13)
		print_sequence(upstream)
		print_sequence(homepage)

	if not got_opts:
		pkg_loc = best_match.package_path()
		pp.uprint(format_line(pkg_loc, "Location:    ", " " * 13))

	if QUERY_OPTS["keywords"] or not got_opts:
		# Get {<Package 'dev-libs/glib-2.20.5'>: [u'ia64', u'm68k', ...], ...}
		keyword_map = filter_keywords(matches)

		for match in matches:
			slot = match.environment('SLOT')
			verstr_len = len(match.fullversion) + len(slot)
			fmtd_keywords = format_keywords(keyword_map[match])
			keywords_line = format_keywords_line(
				match, fmtd_keywords, slot, verstr_len
			)
			if QUERY_OPTS["keywords"]:
				pp.uprint(keywords_line)
			else:
				indent = " " * (16 + verstr_len)
				pp.uprint(format_line(keywords_line, "Keywords:    ", indent))

	if QUERY_OPTS["description"]:
		desc = best_match.metadata.descriptions()
		print_sequence(format_list(desc))

	if QUERY_OPTS["useflags"]:
		useflags = format_useflags(best_match.metadata.use())
		print_sequence(format_list(useflags))

	_license = best_match.environment(["LICENSE"])
	if QUERY_OPTS["license"]:
		_license = format_list(_license)
	else:
		_license = format_list(_license, "License:     ", " " * 13)
	print_sequence(_license)

	if QUERY_OPTS["stablereq"]:
		# Get {<Package 'dev-libs/glib-2.20.5'>: [u'ia64', u'm68k', ...], ...}
		stablereq_map = stablereq(matches)
		for match in matches:
			slot = match.environment('SLOT')
			verstr_len = len(match.fullversion) + len(slot)
			fmtd_ccs = ','.join(sorted(stablereq_map[match]))
			stablereq_line = format_stablereq_line(
				match, fmtd_ccs, slot
			)
			#print("STABLEREQ:", )
			pp.uprint(stablereq_line)

	if QUERY_OPTS["xml"]:
		print_file(os.path.join(best_match.package_path(), 'metadata.xml'))


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

	return result


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
		elif opt in ('-l', '--license'):
			QUERY_OPTS["license"] = True
		elif opt in ('-m', '--maintainer'):
			QUERY_OPTS["maintainer"] = True
		elif opt in ('-k', '--keywords'):
			QUERY_OPTS["keywords"] = True
		elif opt in ('-S', '--stablereq'):
			QUERY_OPTS["stablereq"] = True
		elif opt in ('-u', '--useflags'):
			QUERY_OPTS["useflags"] = True
		elif opt in ('-U', '--upstream'):
			QUERY_OPTS["upstream"] = True
		elif opt in ('-x', '--xml'):
			QUERY_OPTS["xml"] = True


def main(input_args):
	"""Parse input and run the program."""

	short_opts = "hdHklmSuUx"
	long_opts = ('help', 'description', 'herd', 'keywords', 'license',
		'maintainer', 'stablereq', 'useflags', 'upstream', 'xml')

	try:
		module_opts, queries = gnu_getopt(input_args, short_opts, long_opts)
	except GetoptError as err:
		sys.stderr.write(pp.error("Module %s" % err))
		print()
		print_help(with_description=False)
		sys.exit(2)

	parse_module_options(module_opts)

	# Find queries' Portage directory and throw error if invalid
	if not queries:
		print_help()
		sys.exit(2)

	first_run = True
	for query in (Query(x) for x in queries):
		best_match = query.find_best()
		matches = query.find(include_masked=True)
		if best_match is None or not matches:
			raise errors.GentoolkitNoMatches(query)

		if best_match.metadata is None:
			print(pp.warn("Package {0} is missing "
				"metadata.xml".format(best_match.cpv)),
				file = sys.stderr)
			continue

		if not first_run:
			print()

		matches.sort()
		call_format_functions(best_match, matches)

		first_run = False

# vim: set ts=4 sw=4 tw=79:
