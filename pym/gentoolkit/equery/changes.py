# Copyright(c) 2009, Gentoo Foundation
#
# Licensed under the GNU General Public License, v2 or higher
#
# $Header: $

"""Displays the ChangeLog entry for the latest installable version of an atom"""

from __future__ import print_function

__docformat__ = 'epytext'

# =======
# Imports
# =======

import sys
import os
from getopt import gnu_getopt, GetoptError

import gentoolkit.pprinter as pp
from gentoolkit import errors
from gentoolkit.atom import Atom
from gentoolkit.equery import format_options, mod_usage
from gentoolkit.helpers import ChangeLog
from gentoolkit.query import Query

# =======
# Globals
# =======

QUERY_OPTS = {
	'only_latest': False,
	'show_full_log': False,
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
		print(__doc__.strip())
		print()
	print(mod_usage(mod_name="changes"))
	print()
	print(pp.emph("examples"))
	print (" c portage                                # show latest visible "
	       "version's entry")
	print(" c portage --full --limit=3               # show 3 latest entries")
	print(" c '=sys-apps/portage-2.1.6*'             # use atom syntax")
	print(" c portage --from=2.2_rc60 --to=2.2_rc70  # use version ranges")
	print()
	print(pp.command("options"))
	print(format_options((
		(" -h, --help", "display this help message"),
		(" -l, --latest", "display only the latest ChangeLog entry"),
		(" -f, --full", "display the full ChangeLog"),
		("     --limit=NUM",
			"limit the number of entries displayed (with --full)"),
		("     --from=VER", "set which version to display from"),
		("     --to=VER", "set which version to display to"),
	)))


def parse_module_options(module_opts):
	"""Parse module options and update QUERY_OPTS"""

	opts = (x[0] for x in module_opts)
	posargs = (x[1] for x in module_opts)
	for opt, posarg in zip(opts, posargs):
		if opt in ('-h', '--help'):
			print_help()
			sys.exit(0)
		elif opt in ('-f', '--full'):
			QUERY_OPTS['show_full_log'] = True
		elif opt in ('-l', '--latest'):
			QUERY_OPTS['only_latest'] = True
		elif opt in ('--limit',):
			set_limit(posarg)
		elif opt in ('--from',):
			QUERY_OPTS['from'] = posarg
		elif opt in ('--to',):
			QUERY_OPTS['to'] = posarg


def print_entries(entries):
	"""Print entries and strip trailing whitespace from the last entry."""

	len_entries = len(entries)
	for i, entry in enumerate(entries, start=1):
		if i < len_entries:
			pp.uprint(entry)
		else:
			pp.uprint(entry.strip())


def set_limit(posarg):
	"""Set a limit in QUERY_OPTS on how many ChangeLog entries to display.

	Die if posarg is not an integer.
	"""

	if posarg.isdigit():
		QUERY_OPTS['limit'] = int(posarg)
	else:
		err = "Module option --limit requires integer (got '%s')"
		sys.stderr.write(pp.error(err % posarg))
		print()
		print_help(with_description=False)
		sys.exit(2)


def main(input_args):
	"""Parse input and run the program"""

	short_opts = "hlf"
	long_opts = ('help', 'full', 'from=', 'latest', 'limit=', 'to=')

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

	first_run = True
	got_match = False
	for query in (Query(x) for x in queries):
		if not first_run:
			print()

		match = query.find_best()
		if match is None:
			continue

		got_match = True
		changelog_path = os.path.join(match.package_path(), 'ChangeLog')
		changelog = ChangeLog(changelog_path)

		#
		# Output
		#

		if (QUERY_OPTS['only_latest'] or (
			changelog.entries and not changelog.indexed_entries
		)):
			pp.uprint(changelog.latest.strip())
		else:
			end = QUERY_OPTS['limit'] or len(changelog.indexed_entries)
			if QUERY_OPTS['to'] or QUERY_OPTS['from']:
				print_entries(
					changelog.entries_matching_range(
						from_ver=QUERY_OPTS['from'],
						to_ver=QUERY_OPTS['to']
					)[:end]
				)
			elif QUERY_OPTS['show_full_log']:
				print_entries(changelog.full[:end])
			else:
				# Raises GentoolkitInvalidAtom here if invalid
				if query.is_ranged():
					atom = Atom(str(query))
				else:
					atom = '=' + str(match.cpv)
				print_entries(changelog.entries_matching_atom(atom)[:end])

		first_run = False

	if not got_match:
		sys.exit(1)

# vim: set ts=4 sw=4 tw=79:
