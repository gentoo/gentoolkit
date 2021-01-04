# Copyright(c) 2009-2010, Gentoo Foundation
#
# Licensed under the GNU General Public License, v2 or higher

"""Miscellaneous helper functions and classes.

@note: find_* functions that previously lived here have moved to
	   the query module, where they are called as: Query('portage').find_*().
"""

__all__ = (
	'FileOwner',
	'get_cpvs',
	'get_installed_cpvs',
	'get_uninstalled_cpvs',
	'get_bintree_cpvs',
	'uniqify',
)
__docformat__ = 'epytext'

# =======
# Imports
# =======

import os
import re
from functools import partial
from itertools import chain

import portage
from portage import _encodings, _unicode_encode

from gentoolkit import pprinter as pp
from gentoolkit import errors
from gentoolkit.atom import Atom
from gentoolkit.cpv import CPV
from gentoolkit.versionmatch import VersionMatch
# This has to be imported below to stop circular import.
#from gentoolkit.package import Package

# =======
# Classes
# =======

class FileOwner:
	"""Creates a function for locating the owner of filename queries.

	Example usage:
		>>> from gentoolkit.helpers import FileOwner
		>>> findowner = FileOwner()
		>>> findowner(('/bin/grep',))
		[(<Package 'sys-apps/grep-2.12'>, '/bin/grep')]
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
		except (TypeError, re.error) as err:
			raise errors.GentoolkitInvalidRegex(err)

		use_match = False
		if ((self.is_regex or query_re_string.startswith(r'^\/'))
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
	def expand_abspaths(paths):
		"""Expand any relative paths (./file) to their absolute paths.

		@type paths: list
		@param paths: file path strs
		@rtype: list
		@return: the original list with any relative paths expanded
		@raise AttributeError: if paths does not have attribute 'extend'
		"""

		osp = os.path
		expanded_paths = []
		for path in paths:
			if path.startswith('./'):
				expanded_paths.append(osp.abspath(path))
			else:
				expanded_paths.append(path)

		return expanded_paths

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
			if osp.realpath(x) not in paths])

		return paths

	def _prepare_search_regex(self, queries):
		"""Create a regex out of the queries"""

		queries = list(queries)
		if self.is_regex:
			return '|'.join(queries)
		else:
			result = []
			# Trim trailing and multiple slashes from queries
			slashes = re.compile(r'/+')
			queries = self.expand_abspaths(queries)
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

def get_cpvs(predicate=None, include_installed=True):
	"""Get all packages in the Portage tree and overlays. Optionally apply a
	predicate.

	Example usage:
		>>> from gentoolkit.helpers import get_cpvs
		>>> len(set(get_cpvs()))
		33518
		>>> fn = lambda x: x.startswith('app-portage')
		>>> len(set(get_cpvs(fn, include_installed=False)))
		137

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

	if not predicate:
		predicate = lambda x: x

	all_cps = portage.db[portage.root]["porttree"].dbapi.cp_all()

	all_cpvs = iter(x for x in chain.from_iterable(
		portage.db[portage.root]["porttree"].dbapi.cp_list(x)
		for x in all_cps) if predicate(x))

	all_installed_cpvs = set(get_installed_cpvs(predicate))

	if include_installed:
		for cpv in all_cpvs:
			if cpv in all_installed_cpvs:
				all_installed_cpvs.remove(cpv)
			yield cpv
		for cpv in all_installed_cpvs:
			yield cpv
	else:
		for cpv in all_cpvs:
			if cpv not in all_installed_cpvs:
				yield cpv


get_uninstalled_cpvs = partial(get_cpvs, include_installed=False)


def get_installed_cpvs(predicate=None):
	"""Get all installed packages. Optionally apply a predicate.

	@type predicate: function
	@param predicate: a function to filter the package list with
	@rtype: generator
	@return: a generator that yields unsorted installed cat/pkg-ver strings
		from VARDB
	"""

	if not predicate:
		predicate = lambda x: x

	installed_cps = portage.db[portage.root]["vartree"].dbapi.cp_all()

	installed_cpvs = iter(x for x in chain.from_iterable(
		portage.db[portage.root]["vartree"].dbapi.cp_list(x)
		for x in installed_cps) if predicate(x))

	for cpv in installed_cpvs:
		yield cpv


def get_bintree_cpvs(predicate=None):
	"""Get all binary packages available. Optionally apply a predicate.

	@type predicate: function
	@param predicate: a function to filter the package list with
	@rtype: generator
	@return: a generator that yields unsorted binary package cat/pkg-ver strings
		from BINDB
	"""

	if not predicate:
		predicate = lambda x: x

	installed_cps = portage.db[portage.root]["bintree"].dbapi.cp_all()

	installed_cpvs = iter(x for x in chain.from_iterable(
		portage.db[portage.root]["bintree"].dbapi.cp_list(x)
		for x in installed_cps) if predicate(x))

	for cpv in installed_cpvs:
		yield cpv


def print_file(path):
	"""Display the contents of a file."""

	with open(_unicode_encode(path, encoding=_encodings['fs']), mode="rb") as open_file:
		lines = open_file.read()
		pp.uprint(lines.strip())


def print_sequence(seq):
	"""Print every item of a sequence."""

	for item in seq:
		pp.uprint(item)


def uniqify(seq, preserve_order=True):
	"""Return a uniqified list. Optionally preserve order."""

	if preserve_order:
		seen = set()
		result = [x for x in seq if x not in seen and not seen.add(x)]
	else:
		result = list(set(seq))

	return result

# vim: set ts=4 sw=4 tw=79:
