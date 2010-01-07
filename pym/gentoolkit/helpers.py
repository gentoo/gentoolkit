# Copyright(c) 2009-2010, Gentoo Foundation
#
# Licensed under the GNU General Public License, v2 or higher
#
# $Header$

"""Improved versions of the original helpers functions.

As a convention, functions ending in '_packages' or '_match{es}' return
Package objects, while functions ending in 'cpvs' return a sequence of strings.
Functions starting with 'get_' return a set of packages by default and can be
filtered, while functions starting with 'find_' return nothing unless the
query matches one or more packages.
"""

# Move to Imports section after Python 2.6 is stable
from __future__ import with_statement

__all__ = (
	'ChangeLog',
	'FileOwner',
	'compare_package_strings',
	'do_lookup',
	'find_best_match',
	'find_installed_packages',
	'find_packages',
	'get_cpvs',
	'get_installed_cpvs',
	'get_uninstalled_cpvs',
	'uniqify',
	'uses_globbing',
	'split_cpv'
)
__docformat__ = 'epytext'

# =======
# Imports
# =======

import fnmatch
import os
import re
from functools import partial
from itertools import chain

import portage
from portage.versions import catpkgsplit, pkgcmp

from gentoolkit import pprinter as pp
from gentoolkit import CONFIG
from gentoolkit import errors
from gentoolkit.atom import Atom
from gentoolkit.cpv import CPV
from gentoolkit.dbapi import PORTDB, VARDB
from gentoolkit.versionmatch import VersionMatch
# This has to be imported below to stop circular import.
#from gentoolkit.package import Package

# =======
# Classes
# =======

class ChangeLog(object):
	"""Provides methods for working with a Gentoo ChangeLog file.

	Example usage:
		>>> from gentoolkit.helpers import ChangeLog
		>>> portage = ChangeLog('/usr/portage/sys-apps/portage/ChangeLog')
		>>> print portage.latest.strip()
		*portage-2.2_rc50 (15 Nov 2009)

		  15 Nov 2009; Zac Medico <zmedico@gentoo.org> +portage-2.2_rc50.ebuild:
		  2.2_rc50 bump. This includes all fixes in 2.1.7.5.
		>>> len(portage.full)
		75
		>>> len(portage.entries_matching_range(
		...     from_ver='2.2_rc40',
		...     to_ver='2.2_rc50'))
		11

	"""
	def __init__(self, changelog_path, invalid_entry_is_fatal=False):
		if not (os.path.isfile(changelog_path) and
			os.access(changelog_path, os.R_OK)):
			raise errors.GentoolkitFatalError(
				"%s does not exist or is unreadable" % pp.path(changelog_path)
			)
		self.changelog_path = changelog_path
		self.invalid_entry_is_fatal = invalid_entry_is_fatal

		# Process the ChangeLog:
		self.entries = self._split_changelog()
		self.indexed_entries = self._index_changelog()
		self.full = self.entries
		self.latest = self.entries[0]

	def __repr__(self):
		return "<%s %r>" % (self.__class__.__name__, self.changelog_path)

	def entries_matching_atom(self, atom):
		"""Return entries whose header versions match atom's version.

		@type atom: L{gentoolkit.atom.Atom} or str
		@param atom: a atom to find matching entries against
		@rtype: list
		@return: entries matching atom
		@raise errors.GentoolkitInvalidAtom: if atom is a string and malformed
		"""
		result = []

		if not isinstance(atom, Atom):
			atom = Atom(atom)

		for entry_set in self.indexed_entries:
			i, entry = entry_set
			# VersionMatch doesn't store .cp, so we'll force it to match here:
			i.cpv.cp = atom.cpv.cp
			if atom.intersects(i):
				result.append(entry)

		return result

	def entries_matching_range(self, from_ver=None, to_ver=None):
		"""Return entries whose header versions are within a range of versions.

		@type from_ver: str
		@param from_ver: valid Gentoo version
		@type to_ver: str
		@param to_ver: valid Gentoo version
		@rtype: list
		@return: entries between from_ver and to_ver
		@raise errors.GentoolkitFatalError: if neither vers are set
		@raise errors.GentoolkitInvalidVersion: if either ver is invalid
		"""
		result = []

		# Make sure we have at least one version set
		if not (from_ver or to_ver):
			raise errors.GentoolkitFatalError(
				"Need to specifiy 'from_ver' or 'to_ver'"
			)

		# Create a VersionMatch instance out of from_ver
		from_restriction = None
		if from_ver:
			try:
				from_ver_rev = CPV("null-%s" % from_ver)
			except errors.GentoolkitInvalidCPV:
				raise errors.GentoolkitInvalidVersion(from_ver)
			from_restriction = VersionMatch(from_ver_rev, op='>=')

		# Create a VersionMatch instance out of to_ver
		to_restriction = None
		if to_ver:
			try:
				to_ver_rev = CPV("null-%s" % to_ver)
			except errors.GentoolkitInvalidCPV:
				raise errors.GentoolkitInvalidVersion(to_ver)
			to_restriction = VersionMatch(to_ver_rev, op='<=')

		# Add entry to result if version ranges intersect it
		for entry_set in self.indexed_entries:
			i, entry = entry_set
			if from_restriction and not from_restriction.match(i):
				continue
			if to_restriction and not to_restriction.match(i):
				continue
			result.append(entry)

		return result

	def _index_changelog(self):
		"""Use the output of L{self._split_changelog} to create an index list
		of L{gentoolkit.versionmatch.VersionMatch} objects.

		@rtype: list
		@return: tuples containing a VersionMatch instance for the release
			version of each entry header as the first item and the entire entry
			as the second item
		@raise ValueError: if self.invalid_entry_is_fatal is True and we hit an
			invalid entry
		"""

		result = []
		for entry in self.entries:
			# Extract the package name from the entry header, ex:
			# *xterm-242 (07 Mar 2009) => xterm-242
			pkg_name = entry.split(' ', 1)[0].lstrip('*')
			if not pkg_name.strip():
				continue
			try:
				entry_ver = CPV(pkg_name)
			except errors.GentoolkitInvalidCPV:
				if self.invalid_entry_is_fatal:
					raise ValueError(entry_ver)
				continue

			result.append((VersionMatch(entry_ver, op='='), entry))

		return result

	def _split_changelog(self):
		"""Split the ChangeLog into individual entries.

		@rtype: list
		@return: individual ChangeLog entries
		"""

		result = []
		partial_entries = []
		with open(self.changelog_path) as log:
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


class FileOwner(object):
	"""Creates a function for locating the owner of filename queries.

	Example usage:
		>>> from gentoolkit.helpers import FileOwner
		>>> findowner = FileOwner()
		>>> findowner(('/usr/bin/vim',))
		[(<Package app-editors/vim-7.2.182>, '/usr/bin/vim')]
	"""
	def __init__(self, is_regex=False, early_out=False, printer_fn=None):
		"""Instantiate function.

		@type is_regex: bool
		@param is_regex: funtion args are regular expressions
		@type early_out: bool
		@param early_out: return when first result is found (safe)
		@type printer_fn: callable
		@param printer_fn: If defined, will be passed useful information for
			printing each result as it is found.
		"""
		self.is_regex = is_regex
		self.early_out = early_out
		self.printer_fn = printer_fn

	def __call__(self, queries):
		"""Run the function.

		@type queries: iterable
		@param queries: filepaths or filepath regexes
		"""
		query_re_string = self._prepare_search_regex(queries)
		try:
			query_re = re.compile(query_re_string)
		except (TypeError, re.error), err:
			raise errors.GentoolkitInvalidRegex(err)

		use_match = False
		if ((self.is_regex or query_re_string.startswith('^\/'))
			and '|' not in query_re_string ):
			# If we were passed a regex or a single path starting with root,
			# we can use re.match, else use re.search.
			use_match = True

		pkgset = get_installed_cpvs()

		return self.find_owners(query_re, use_match=use_match, pkgset=pkgset)

	def find_owners(self, query_re, use_match=False, pkgset=None):
		"""Find owners and feed data to supplied output function.

		@type query_re: _sre.SRE_Pattern
		@param query_re: file regex
		@type use_match: bool
		@param use_match: use re.match or re.search
		@type pkgset: iterable or None
		@param pkgset: list of packages to look through
		"""
		# FIXME: Remove when lazyimport supports objects:
		from gentoolkit.package import Package

		if use_match:
			query_fn = query_re.match
		else:
			query_fn = query_re.search

		results = []
		found_match = False
		for pkg in sorted([Package(x) for x in pkgset]):
			files = pkg.parsed_contents()
			for cfile in files:
				match = query_fn(cfile)
				if match:
					results.append((pkg, cfile))
					if self.printer_fn is not None:
						self.printer_fn(pkg, cfile)
					if self.early_out:
						found_match = True
						break
			if found_match:
				break
		return results

	@staticmethod
	def extend_realpaths(paths):
		"""Extend a list of paths with the realpaths for any symlinks.

		@type paths: list
		@param paths: file path strs
		@rtype: list
		@return: the original list plus the realpaths for any symlinks
			so long as the realpath doesn't already exist in the list
		@raise AttributeError: if paths does not have attribute 'extend'
		"""

		osp = os.path
		paths.extend([osp.realpath(x) for x in paths
			if osp.islink(x) and osp.realpath(x) not in paths])

		return paths

	def _prepare_search_regex(self, queries):
		"""Create a regex out of the queries"""

		queries = list(queries)
		if self.is_regex:
			return '|'.join(queries)
		else:
			result = []
			# Trim trailing and multiple slashes from queries
			slashes = re.compile('/+')
			queries = self.extend_realpaths(queries)
			for query in queries:
				query = slashes.sub('/', query).rstrip('/')
				if query.startswith('/'):
					query = "^%s$" % re.escape(query)
				else:
					query = "/%s$" % re.escape(query)
				result.append(query)
		result = "|".join(result)
		return result

# =========
# Functions
# =========

def compare_package_strings(pkg1, pkg2):
	"""Similar to the builtin cmp, but for package strings. Usually called
	as: package_list.sort(compare_package_strings)

	An alternative is to use the CPV descriptor from gentoolkit.cpv:
	>>> cpvs = sorted(CPV(x) for x in package_list)

	@see: >>> help(cmp)
	"""

	pkg1 = catpkgsplit(pkg1)
	pkg2 = catpkgsplit(pkg2)
	if pkg1[0] != pkg2[0]:
		return cmp(pkg1[0], pkg2[0])
	elif pkg1[1] != pkg2[1]:
		return cmp(pkg1[1], pkg2[1])
	else:
		return pkgcmp(pkg1[1:], pkg2[1:])


def do_lookup(query, query_opts):
	"""A high-level wrapper around gentoolkit package-finder functions.

	@type query: str
	@param query: pkg, cat/pkg, pkg-ver, cat/pkg-ver, atom, glob or regex
	@type query_opts: dict
	@param query_opts: user-configurable options from the calling module
		Currently supported options are:

		includeInstalled   = bool
		includePortTree    = bool
		includeOverlayTree = bool
		isRegex            = bool
		printMatchInfo     = bool           # Print info about the search

	@rtype: list
	@return: Package objects matching query
	"""

	if query_opts["includeInstalled"]:
		if query_opts["includePortTree"] or query_opts["includeOverlayTree"]:
			simple_package_finder = partial(find_packages, include_masked=True)
			complex_package_finder = get_cpvs
		else:
			simple_package_finder = find_installed_packages
			complex_package_finder = get_installed_cpvs
	elif query_opts["includePortTree"] or query_opts["includeOverlayTree"]:
		simple_package_finder = partial(find_packages, include_masked=True)
		complex_package_finder = get_uninstalled_cpvs
	else:
		raise errors.GentoolkitFatalError(
			"Not searching in installed, Portage tree, or overlay. "
			"Nothing to do."
		)

	is_simple_query = True
	if query_opts["isRegex"] or uses_globbing(query):
		is_simple_query = False

	if is_simple_query:
		matches = _do_simple_lookup(query, simple_package_finder, query_opts)
	else:
		matches = _do_complex_lookup(query, complex_package_finder, query_opts)

	return matches


def _do_complex_lookup(query, package_finder, query_opts):
	"""Find matches for a query which is a regex or includes globbing."""

	# FIXME: Remove when lazyimport supports objects:
	from gentoolkit.package import Package

	result = []

	if query_opts["printMatchInfo"] and not CONFIG["piping"]:
		print_query_info(query, query_opts)

	cat = split_cpv(query)[0]

	pre_filter = []
	# The "get_" functions can pre-filter against the whole package key,
	# but since we allow globbing now, we run into issues like:
	# >>> portage.dep.dep_getkey("sys-apps/portage-*")
	# 'sys-apps/portage-'
	# So the only way to guarantee we don't overrun the key is to
	# prefilter by cat only.
	if cat:
		if query_opts["isRegex"]:
			cat_re = cat
		else:
			cat_re = fnmatch.translate(cat)
			# [::-1] reverses a sequence, so we're emulating an ".rreplace()"
			# except we have to put our "new" string on backwards
			cat_re = cat_re[::-1].replace('$', '*./', 1)[::-1]
		predicate = lambda x: re.match(cat_re, x)
		pre_filter = package_finder(predicate=predicate)

	# Post-filter
	if query_opts["isRegex"]:
		predicate = lambda x: re.search(query, x)
	else:
		if cat:
			query_re = fnmatch.translate(query)
		else:
			query_re = fnmatch.translate("*/%s" % query)
		predicate = lambda x: re.search(query_re, x)
	if pre_filter:
		result = [x for x in pre_filter if predicate(x)]
	else:
		result = package_finder(predicate=predicate)

	return [Package(x) for x in result]


def _do_simple_lookup(query, package_finder, query_opts):
	"""Find matches for a query which is an atom or string."""

	result = []

	if query_opts["printMatchInfo"] and CONFIG['verbose']:
		print_query_info(query, query_opts)

	result = package_finder(query)
	if not query_opts["includeInstalled"]:
		result = [x for x in result if not x.is_installed()]

	return result


def find_best_match(query):
	"""Return the highest unmasked version of a package matching query.

	@type query: str
	@param query: can be of the form: pkg, pkg-ver, cat/pkg, cat/pkg-ver, atom
	@rtype: str or None
	@raise portage.exception.InvalidAtom: if query is not valid input
	"""
	# FIXME: Remove when lazyimport supports objects:
	from gentoolkit.package import Package

	try:
		match = PORTDB.xmatch("bestmatch-visible", query)
	except portage.exception.InvalidAtom, err:
		raise errors.GentoolkitInvalidAtom(err)

	return Package(match) if match else None


def find_installed_packages(query):
	"""Return a list of Package objects that matched the search key."""
	# FIXME: Remove when lazyimport supports objects:
	from gentoolkit.package import Package

	try:
		matches = VARDB.match(query)
	# catch the ambiguous package Exception
	except portage.exception.AmbiguousPackageName, err:
		matches = []
		for pkgkey in err[0]:
			matches.extend(VARDB.match(pkgkey))
	except portage.exception.InvalidAtom, err:
		raise errors.GentoolkitInvalidAtom(err)

	return [Package(x) for x in matches]


def find_packages(query, include_masked=False):
	"""Returns a list of Package objects that matched the query.

	@type query: str
	@param query: can be of the form: pkg, pkg-ver, cat/pkg, cat/pkg-ver, atom
	@type include_masked: bool
	@param include_masked: include masked packages
	@rtype: list
	@return: matching Package objects
	"""
	# FIXME: Remove when lazyimport supports objects:
	from gentoolkit.package import Package

	if not query:
		return []

	try:
		if include_masked:
			matches = PORTDB.xmatch("match-all", query)
		else:
			matches = PORTDB.match(query)
		matches.extend(VARDB.match(query))
	except portage.exception.InvalidAtom, err:
		raise errors.GentoolkitInvalidAtom(str(err))

	return [Package(x) for x in set(matches)]


def get_cpvs(predicate=None, include_installed=True):
	"""Get all packages in the Portage tree and overlays. Optionally apply a
	predicate.

	Example usage:
		>>> from gentoolkit.helpers import get_cpvs
		>>> len(set(get_cpvs()))
		26065
		>>> fn = lambda x: x.startswith('app-portage')
		>>> len(get_cpvs(fn, include_installed=False))
		112

	@type predicate: function
	@param predicate: a function to filter the package list with
	@type include_installed: bool
	@param include_installed:
		If True: Return the union of all_cpvs and all_installed_cpvs
		If False: Return the difference of all_cpvs and all_installed_cpvs
	@rtype: generator
	@return: a generator that yields unsorted cat/pkg-ver strings from the
		Portage tree
	"""

	if predicate:
		all_cps = iter(x for x in PORTDB.cp_all() if predicate(x))
	else:
		all_cps = PORTDB.cp_all()

	all_cpvs = chain.from_iterable(PORTDB.cp_list(x) for x in all_cps)
	all_installed_cpvs = get_installed_cpvs(predicate)

	if include_installed:
		for cpv in chain(all_cpvs, all_installed_cpvs):
			yield cpv
	else:
		# Consume the smaller pkg set:
		installed_cpvs = set(all_installed_cpvs)
		for cpv in all_cpvs:
			if cpv not in installed_cpvs:
				yield cpv


# pylint thinks this is a global variable
# pylint: disable-msg=C0103
get_uninstalled_cpvs = partial(get_cpvs, include_installed=False)


def get_installed_cpvs(predicate=None):
	"""Get all installed packages. Optionally apply a predicate.

	@type predicate: function
	@param predicate: a function to filter the package list with
	@rtype: generator
	@return: a generator that yields unsorted installed cat/pkg-ver strings
		from VARDB
	"""

	if predicate:
		installed_cps = iter(x for x in VARDB.cp_all() if predicate(x))
	else:
		installed_cps = VARDB.cp_all()

	for cpv in chain.from_iterable(VARDB.cp_list(x) for x in installed_cps):
		yield cpv


def print_query_info(query, query_opts):
	"""Print info about the query to the screen."""

	cat, pkg = split_cpv(query)[:2]
	if cat and not query_opts["isRegex"]:
		cat_str = "in %s " % pp.emph(cat.lstrip('><=~!'))
	else:
		cat_str = ""

	if query_opts["isRegex"]:
		pkg_str = query
	else:
		pkg_str = pkg

	print " * Searching for %s %s..." % (pp.emph(pkg_str), cat_str)


def print_file(path):
	"""Display the contents of a file."""

	with open(path) as open_file:
		lines = open_file.read()
		print lines.strip()


def print_sequence(seq):
	"""Print every item of a sequence."""

	for item in seq:
		print item


def split_cpv(query):
	"""Split a cpv into category, name, version and revision.

	@type query: str
	@param query: pkg, cat/pkg, pkg-ver, cat/pkg-ver, atom or regex
	@rtype: tuple
	@return: (category, pkg_name, version, revision)
		Each tuple element is a string or empty string ("").
	"""

	result = catpkgsplit(query)

	if result:
		result = list(result)
		if result[0] == 'null':
			result[0] = ''
		if result[3] == 'r0':
			result[3] = ''
	else:
		result = query.split("/")
		if len(result) == 1:
			result = ['', query, '', '']
		else:
			result = result + ['', '']

	if len(result) != 4:
		raise errors.GentoolkitInvalidPackageName(query)

	return tuple(result)


def uniqify(seq, preserve_order=True):
	"""Return a uniqified list. Optionally preserve order."""

	if preserve_order:
		seen = set()
		result = [x for x in seq if x not in seen and not seen.add(x)]
	else:
		result = list(set(seq))

	return result


def uses_globbing(query):
	"""Check the query to see if it is using globbing.

	@type query: str
	@param query: user input package query
	@rtype: bool
	@return: True if query uses globbing, else False
	"""

	if set('!*?[]').intersection(query):
		# Is query an atom such as '=sys-apps/portage-2.2*'?
		if query[0] != '=':
			return True

	return False

# vim: set ts=4 sw=4 tw=79:
