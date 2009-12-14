# Copyright(c) 2009, Gentoo Foundation
#
# Licensed under the GNU General Public License, v2 or higher
#
# $Header: $

"""Displays the ChangeLog entry for the latest installable version of an atom"""

# Move to Imports sections when Python 2.6 is stable
from __future__ import with_statement

__docformat__ = 'epytext'

# =======
# Imports
# =======

import os
import sys
from getopt import gnu_getopt, GetoptError

import gentoolkit.pprinter as pp
from gentoolkit import errors
from gentoolkit.atom import Atom
from gentoolkit.equery import format_options, mod_usage
from gentoolkit.helpers import ChangeLog, find_best_match, find_packages

# =======
# Globals
# =======

QUERY_OPTS = {
	'onlyLatest': False,
	'showFullLog': False,
	'limit': None,
	'from': None,
	'to': None
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
	print mod_usage(mod_name="changes")
	print
	print pp.emph("examples")
	print (" c portage                                # show latest visible "
	       "version's entry")
	print " c portage --full --limit=3               # show 3 latest entries"
	print " c '=sys-apps/portage-2.1.6*'             # use atom syntax"
	print " c portage --from=2.2_rc20 --to=2.2_rc30  # use version ranges"
	print
	print pp.command("options")
	print format_options((
		(" -h, --help", "display this help message"),
		(" -l, --latest", "display only the latest ChangeLog entry"),
		(" -f, --full", "display the full ChangeLog"),
		("     --limit=NUM",
			"limit the number of entries displayed (with --full)"),
		("     --from=VER", "set which version to display from"),
		("     --to=VER", "set which version to display to"),
	))


def get_match(query):
	"""Find a valid package from which to get the ChangeLog path.

	@raise GentoolkitNoMatches: if no matches found
	"""

	match = matches = None
	match = find_best_match(query)

	if not match:
		matches = find_packages(query, include_masked=True)
	else:
		matches = [match]

	if not matches:
		raise errors.GentoolkitNoMatches(query)

	return matches[0]


def is_ranged(atom):
	"""Return True if an atom string appears to be ranged, else False."""

	return atom.startswith(('~', '<', '>')) or atom.endswith('*')


def parse_module_options(module_opts):
	"""Parse module options and update QUERY_OPTS"""

	opts = (x[0] for x in module_opts)
	posargs = (x[1] for x in module_opts)
	for opt, posarg in zip(opts, posargs):
		if opt in ('-h', '--help'):
			print_help()
			sys.exit(0)
		elif opt in ('-f', '--full'):
			QUERY_OPTS['showFullLog'] = True
		elif opt in ('-l', '--latest'):
			QUERY_OPTS['onlyLatest'] = True
		elif opt in ('--limit',):
			set_limit(posarg)
		elif opt in ('--from',):
			QUERY_OPTS['from'] = posarg
		elif opt in ('--to',):
			QUERY_OPTS['to'] = posarg


def print_entries(entries):
	"""Print entries and strip trailing whitespace from the last entry."""

	len_entries = len(entries)
	for i, entry in enumerate(entries):    # , start=1): in py2.6
		i += 1
		if i < len_entries:
			print entry
		else:
			print entry.strip()


def set_limit(posarg):
	"""Set a limit in QUERY_OPTS on how many ChangeLog entries to display.

	Die if posarg is not an integer.
	"""

	if posarg.isdigit():
		QUERY_OPTS['limit'] = int(posarg)
	else:
		err = "Module option --limit requires integer (got '%s')"
		sys.stderr.write(pp.error(err % posarg))
		print
		print_help(with_description=False)
		sys.exit(2)


def main(input_args):
	"""Parse input and run the program"""

	short_opts = "hlf"
	long_opts = ('help', 'full', 'from=', 'latest', 'limit=', 'to=')

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

	first_run = True
	for query in queries:
		if not first_run:
			print

		match = get_match(query)
		changelog_path = os.path.join(match.package_path(), 'ChangeLog')
		changelog = ChangeLog(changelog_path)

		#
		# Output
		#

		if (QUERY_OPTS['onlyLatest'] or (
			changelog.entries and not changelog.indexed_entries
		)):
			print changelog.latest.strip()
		else:
			end = QUERY_OPTS['limit'] or len(changelog.indexed_entries)
			if QUERY_OPTS['to'] or QUERY_OPTS['from']:
				print_entries(
					changelog.entries_matching_range(
						from_ver=QUERY_OPTS['from'],
						to_ver=QUERY_OPTS['to']
					)[:end]
				)
			elif QUERY_OPTS['showFullLog']:
				print_entries(changelog.full[:end])
			else:
				# Raises GentoolkitInvalidAtom here if invalid
				atom = Atom(query) if is_ranged(query) else '=' + str(match.cpv)
				print_entries(changelog.entries_matching_atom(atom)[:end])

		first_run = False

# vim: set ts=4 sw=4 tw=79:
