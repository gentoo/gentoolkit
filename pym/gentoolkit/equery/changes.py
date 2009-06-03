# Copyright(c) 2009, Gentoo Foundation
#
# Licensed under the GNU General Public License, v2 or higher
#
# $Header: $

"""Display the  Gentoo ChangeLog entry for the latest installable version of a
given package
"""

# Move to Imports sections when Python 2.6 is stable
from __future__ import with_statement

__author__ = 'Douglas Anderson'
__docformat__ = 'epytext'

# =======
# Imports
# =======

import os
import sys
from getopt import gnu_getopt, GetoptError

from portage.versions import pkgsplit

import gentoolkit.pprinter as pp
from gentoolkit import errors
from gentoolkit.equery import format_options, mod_usage
from gentoolkit.helpers2 import find_best_match, find_packages
from gentoolkit.package import Package
from gentoolkit.versionmatch import VersionMatch

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


def get_logpath(pkg):
	"""Test that the package's ChangeLog path is valid and readable, else
	die.

	@type pkg: gentoolkit.package.Package
	@param pkg: package to find logpath for
	@rtype: str
	@return: a path to a readable ChangeLog
	"""

	logpath = os.path.join(pkg.get_package_path(), 'ChangeLog')
	if not os.path.isfile(logpath) or not os.access(logpath, os.R_OK):
		raise errors.GentoolkitFatalError("%s does not exist or is unreadable"
			% pp.path(logpath))
	
	return logpath


def get_match(query):
	"""Find a valid package to get the ChangeLog path from or raise
	GentoolkitNoMatches.
	"""

	match = matches = None
	match = find_best_match(query)
		
	if not match:
		matches = find_packages(query, include_masked=True)
	else:
		matches = [match]

	if not matches:
		pp.print_warn("Try using an unversioned query with "
			"--from and --to.")
		raise errors.GentoolkitNoMatches(query)

	return matches[0]


def index_changelog(entries):
	"""Convert the list from split_changelog into a dict with VersionMatch
	instance as the index.

	@todo: UPDATE THIS
	@type entries: list
	@param entries: output of split_changelog
	@rtype: dict
	@return: dict with gentoolkit.package.Package instances as keys and the
		corresponding ChangeLog entree as its value
	"""

	result = []
	for entry in entries:
		# Extract the package name from the entry, ex: 
		# *xterm-242 (07 Mar 2009) => xterm-242
		pkg_name = entry.split(' ', 1)[0].lstrip('*')
		if not pkg_name.strip():
			continue
		pkg_split = pkgsplit(pkg_name)
		result.append(
			(VersionMatch(op="=", ver=pkg_split[1], rev=pkg_split[2]), entry))
	
	return result


def is_ranged(atom):
	"""Return True if an atom string appears to be ranged, else False."""

	return atom.startswith(('~', '<', '>')) or atom.endswith('*')


def parse_module_options(module_opts):
	"""Parse module options and update GLOBAL_OPTS"""

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
			set_from(posarg)
		elif opt in ('--to',):
			set_to(posarg)


def print_matching_entries(indexed_entries, pkg, first_run):
	"""Print only the entries which interect with the pkg version."""

	from_restriction = QUERY_OPTS['from']
	to_restriction = QUERY_OPTS['to']

	for entry_set in indexed_entries:
		i, entry = entry_set
		# a little hackery, since versionmatch doesn't store the
		# package key, but intersects checks that it matches.
		i.key = pkg.key
		if from_restriction or to_restriction:
			if from_restriction and not from_restriction.match(i):
				continue
			if to_restriction and not to_restriction.match(i):
				continue
		elif not pkg.intersects(i):
			continue

		if not first_run:
			print "\n"
		print entry.strip()
		first_run = False
	
	return first_run


def set_from(posarg):
	"""Set a starting version to filter the ChangeLog with or die if posarg
	is not a valid version.
	"""

	pkg_split = pkgsplit('null-%s' % posarg)

	if pkg_split and not is_ranged(posarg):
		ver_match = VersionMatch(
			op=">=",
			ver=pkg_split[1], 
			rev=pkg_split[2] if pkg_split[2] != 'r0' else '')
		QUERY_OPTS['from'] = ver_match
	else:
		err = "Module option --from requires valid unranged version (got '%s')"
		pp.print_error(err % posarg)
		print
		print_help(with_description=False)
		sys.exit(2)


def set_limit(posarg):
	"""Set a limit in QUERY_OPTS on how many ChangeLog entries to display or
	die if posarg is not an integer.
	"""

	if posarg.isdigit():
		QUERY_OPTS['limit'] = int(posarg)
	else:
		err = "Module option --limit requires integer (got '%s')"
		pp.print_error(err % posarg)
		print
		print_help(with_description=False)
		sys.exit(2)


def set_to(posarg):
	"""Set an ending version to filter the ChangeLog with or die if posarg
	is not a valid version.
	"""

	pkg_split = pkgsplit('null-%s' % posarg)
	if pkg_split and not is_ranged(posarg):
		ver_match = VersionMatch(
			op="<=",
			ver=pkg_split[1], 
			rev=pkg_split[2] if pkg_split[2] != 'r0' else '')
		QUERY_OPTS['to'] = ver_match
	else:
		err = "Module option --to requires valid unranged version (got '%s')"
		pp.print_error(err % posarg)
		print
		print_help(with_description=False)
		sys.exit(2)


def split_changelog(logpath):
	"""Split the changelog up into individual entries.
	
	@type logpath: str
	@param logpath: valid path to ChangeLog file
	@rtype: list
	@return: individual ChangeLog entrees
	"""

	result = []
	partial_entries = []
	with open(logpath) as log:
		for line in log:
			if line.startswith('#'):
				continue
			elif line.startswith('*'):
				# Append last entry to result...
				entry = ''.join(partial_entries)
				if entry and not entry.isspace():
					result.append(entry)
				# ... and start a new entry
				partial_entries = [line]
			else:
				partial_entries.append(line)
		else:
			# Append the final entry
			entry = ''.join(partial_entries)
			result.append(entry)

	return result


def main(input_args):
	"""Parse input and run the program"""

	short_opts = "hlf"
	long_opts = ('help', 'full', 'from=', 'latest', 'limit=', 'to=')

	try:
		module_opts, queries = gnu_getopt(input_args, short_opts, long_opts)
	except GetoptError, err:
		pp.print_error("Module %s" % err)
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

		ranged_query = None
		if is_ranged(query):
			# Raises GentoolkitInvalidCPV here if invalid
			ranged_query = Package(query)

		pkg = get_match(query)
		logpath = get_logpath(pkg)
		log_entries = split_changelog(logpath)
		if not any(log_entries):
			raise errors.GentoolkitFatalError(
				"%s exists but doesn't contain entries." % pp.path(logpath))
		indexed_entries = index_changelog(log_entries)

		#
		# Output
		#

		if QUERY_OPTS['onlyLatest']:
			print log_entries[0].strip()
		elif QUERY_OPTS['showFullLog']:
			end = QUERY_OPTS['limit'] or len(log_entries)
			for entry in log_entries[:end]:
				print entry
			first_run = False
		elif log_entries and not indexed_entries:
			# We can't match anything, so just print latest:
			print log_entries[0].strip()
		else:
			if ranged_query:
				pkg = ranged_query
			first_run = print_matching_entries(indexed_entries, pkg, first_run)

		first_run = False
