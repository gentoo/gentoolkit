#!/usr/bin/python
#
# Copyright(c) 2004-2010, Gentoo Foundation
#
# Licensed under the GNU General Public License, v2
#
# $Header$

"""Provides common methods on a package query."""

__all__ = (
	'Query',
)

# =======
# Imports
# =======

import fnmatch
import re
from functools import partial
from string import ascii_letters

import portage

from gentoolkit import CONFIG
from gentoolkit import errors
from gentoolkit import helpers
from gentoolkit import pprinter as pp
from gentoolkit.atom import Atom
from gentoolkit.cpv import CPV
from gentoolkit.package import Package
from gentoolkit.sets import get_set_atoms, SETPREFIX

# =======
# Classes
# =======

class Query(CPV):
	"""Provides common methods on a package query."""

	def __init__(self, query, is_regex=False):
		"""Create query object.

		@type is_regex: bool
		@param is_regex: query is a regular expression
		"""

		# We need at least one of these chars for a valid query
		needed_chars = ascii_letters + '*'
		if not set(query).intersection(needed_chars):
			raise errors.GentoolkitInvalidPackage(query)

		# Separate repository
		repository = None
		if query.count(':') == 2:
			query, repository = query.rsplit(':', 1)
		self.query = query.rstrip(':') # Don't leave dangling colon
		self.repo_filter = repository
		self.is_regex = is_regex
		self.query_type = self._get_query_type()

		# Name the rest of the chunks, if possible
		if self.query_type != "set":
			try:
				atom = Atom(self.query)
				self.__dict__.update(atom.__dict__)
			except errors.GentoolkitInvalidAtom:
				CPV.__init__(self, self.query)
				self.operator = ''
				self.atom = self.cpv

	def __repr__(self):
		rx = ''
		if self.is_regex:
			rx = ' regex'
		repo = ''
		if self.repo_filter:
			repo = ' in %s' % self.repo_filter
		return "<%s%s %r%s>" % (self.__class__.__name__, rx, self.query, repo)

	def __str__(self):
		return self.query

	def print_summary(self):
		"""Print a summary of the query."""

		if self.query_type == "set":
			cat_str = ""
			pkg_str = pp.emph(self.query)
		else:
			try:
				cat, pkg = self.category, self.name + self.fullversion
			except errors.GentoolkitInvalidCPV:
				cat = ''
				pkg = self.atom
			if cat and not self.is_regex:
				cat_str = "in %s " % pp.emph(cat.lstrip('><=~!'))
			else:
				cat_str = ""

			if self.is_regex:
				pkg_str = pp.emph(self.query)
			else:
				pkg_str = pp.emph(pkg)

		repo = ''
		if self.repo_filter is not None:
			repo = ' %s' % pp.section(self.repo_filter)

		pp.uprint(" * Searching%s for %s %s..." % (repo, pkg_str, cat_str))

	def smart_find(
		self,
		in_installed=True,
		in_porttree=True,
		in_overlay=True,
		include_masked=True,
		show_progress=True,
		no_matches_fatal=True,
		**kwargs
	):
		"""A high-level wrapper around gentoolkit package-finder functions.

		@type in_installed: bool
		@param in_installed: search for query in VARDB
		@type in_porttree: bool
		@param in_porttree: search for query in PORTDB
		@type in_overlay: bool
		@param in_overlay: search for query in overlays
		@type show_progress: bool
		@param show_progress: output search progress
		@type no_matches_fatal: bool
		@param no_matches_fatal: raise errors.GentoolkitNoMatches
		@rtype: list
		@return: Package objects matching query
		"""

		if in_installed:
			if in_porttree or in_overlay:
				simple_package_finder = partial(
					self.find,
					include_masked=include_masked
				)
				complex_package_finder = helpers.get_cpvs
			else:
				simple_package_finder = self.find_installed
				complex_package_finder = helpers.get_installed_cpvs
		elif in_porttree or in_overlay:
			simple_package_finder = partial(
				self.find,
				include_masked=include_masked,
				in_installed=False
			)
			complex_package_finder = helpers.get_uninstalled_cpvs
		else:
			raise errors.GentoolkitFatalError(
				"Not searching in installed, Portage tree, or overlay. "
				"Nothing to do."
			)

		if self.query_type == "set":
			self.package_finder = simple_package_finder
			matches = self._do_set_lookup(show_progress=show_progress)
		elif self.query_type == "simple":
			self.package_finder = simple_package_finder
			matches = self._do_simple_lookup(
				in_installed=in_installed,
				show_progress=show_progress
			)
		else:
			self.package_finder = complex_package_finder
			matches = self._do_complex_lookup(show_progress=show_progress)

		if self.repo_filter is not None:
			matches = self._filter_by_repository(matches)

		if no_matches_fatal and not matches:
			ii = in_installed and not (in_porttree or in_overlay)
			raise errors.GentoolkitNoMatches(self.query, in_installed=ii)
		return matches

	def find(self, in_installed=True, include_masked=True):
		"""Returns a list of Package objects that matched the query.

		@rtype: list
		@return: matching Package objects
		"""

		if not self.query:
			return []

		try:
			if include_masked:
				matches = portage.db[portage.root]["porttree"].dbapi.xmatch("match-all", self.query)
			else:
				matches = portage.db[portage.root]["porttree"].dbapi.match(self.query)
			if in_installed:
				matches.extend(portage.db[portage.root]["vartree"].dbapi.match(self.query))
		except portage.exception.InvalidAtom as err:
			message = "query.py: find(), query=%s, InvalidAtom=%s" %(
				self.query, str(err))
			raise errors.GentoolkitInvalidAtom(message)

		return [Package(x) for x in set(matches)]

	def find_installed(self):
		"""Return a list of Package objects that matched the search key."""

		try:
			matches = portage.db[portage.root]["vartree"].dbapi.match(self.query)
		# catch the ambiguous package Exception
		except portage.exception.AmbiguousPackageName as err:
			matches = []
			for pkgkey in err.args[0]:
				matches.extend(portage.db[portage.root]["vartree"].dbapi.match(pkgkey))
		except portage.exception.InvalidAtom as err:
			raise errors.GentoolkitInvalidAtom(err)

		return [Package(x) for x in set(matches)]

	def find_best(self, include_keyworded=True, include_masked=True):
		"""Returns the "best" version available.

		Order of preference:
			highest available stable =>
			highest available keyworded =>
			highest available masked

		@rtype: Package object or None
		@return: best of up to three options
		@raise errors.GentoolkitInvalidAtom: if query is not valid input
		"""

		best = keyworded = masked = None
		try:
			best = portage.db[portage.root]["porttree"].dbapi.xmatch("bestmatch-visible", self.query)
		except portage.exception.InvalidAtom as err:
			message = "query.py: find_best(), bestmatch-visible, " + \
				"query=%s, InvalidAtom=%s" %(self.query, str(err))
			raise errors.GentoolkitInvalidAtom(message)
		# xmatch can return an empty string, so checking for None is not enough
		if not best:
			if not (include_keyworded or include_masked):
				return None
			try:
				matches = portage.db[portage.root]["porttree"].dbapi.xmatch("match-all", self.query)
			except portage.exception.InvalidAtom as err:
				message = "query.py: find_best(), match-all, query=%s, InvalidAtom=%s" %(
					self.query, str(err))
				raise errors.GentoolkitInvalidAtom(message)
			masked = portage.best(matches)
			keywordable = []
			for m in matches:
				status = portage.getmaskingstatus(m)
				if 'package.mask' not in status or 'profile' not in status:
					keywordable.append(m)
				if matches:
					keyworded = portage.best(keywordable)
		else:
			return Package(best)
		if include_keyworded and keyworded:
			return Package(keyworded)
		if include_masked and masked:
			return Package(masked)
		return None

	def uses_globbing(self):
		"""Check the query to see if it is using globbing.

		@rtype: bool
		@return: True if query uses globbing, else False
		"""

		if set('!*?[]').intersection(self.query):
			# Is query an atom such as '=sys-apps/portage-2.2*'?
			if self.query[0] != '=':
				return True

		return False

	def is_ranged(self):
		"""Return True if the query appears to be ranged, else False."""

		q = self.query
		return q.startswith(('~', '<', '>')) or q.endswith('*')

	def _do_simple_lookup(self, in_installed=True, show_progress=True):
		"""Find matches for a query which is an atom or cpv."""

		result = []

		if show_progress and CONFIG['verbose']:
			self.print_summary()

		result = self.package_finder()
		if not in_installed:
			result = [x for x in result if not x.is_installed()]

		return result

	def _do_complex_lookup(self, show_progress=True):
		"""Find matches for a query which is a regex or includes globbing."""

		result = []

		if show_progress and not CONFIG["piping"]:
			self.print_summary()

		try:
			cat = CPV(self.query).category
		except errors.GentoolkitInvalidCPV:
			cat = ''

		pre_filter = []
		# The "get_" functions can pre-filter against the whole package key,
		# but since we allow globbing now, we run into issues like:
		# >>> portage.dep.dep_getkey("sys-apps/portage-*")
		# 'sys-apps/portage-'
		# So the only way to guarantee we don't overrun the key is to
		# prefilter by cat only.
		if cat:
			if self.is_regex:
				cat_re = cat
			else:
				cat_re = fnmatch.translate(cat)
			predicate = lambda x: re.match(cat_re, x.split("/", 1)[0])
			pre_filter = self.package_finder(predicate=predicate)

		# Post-filter
		if self.is_regex:
			try:
				re.compile(self.query)
			except re.error:
				raise errors.GentoolkitInvalidRegex(self.query)
			predicate = lambda x: re.search(self.query, x)
		else:
			if cat:
				query_re = fnmatch.translate(self.query)
			else:
				query_re = fnmatch.translate("*/%s" % self.query)
			predicate = lambda x: re.search(query_re, x)
		if pre_filter:
			result = [x for x in pre_filter if predicate(x)]
		else:
			result = self.package_finder(predicate=predicate)

		return [Package(x) for x in result]

	def _do_set_lookup(self, show_progress=True):
		"""Find matches for a query that is a package set."""

		if show_progress and not CONFIG["piping"]:
			self.print_summary()

		setname = self.query[len(SETPREFIX):]
		result = []
		try:
			atoms = get_set_atoms(setname)
		except errors.GentoolkitSetNotFound:
			return result

		q = self.query
		for atom in atoms:
			self.query = atom
			result.extend(self._do_simple_lookup(show_progress=False))
		self.query = q

		return result

	def _filter_by_repository(self, matches):
		"""Filter out packages which do not belong to self.repo_filter."""

		result = []
		for match in matches:
			repo_name = match.repo_name()
			if repo_name == self.repo_filter:
				result.append(match)
			elif (not repo_name and
				self.repo_filter in ('unknown', 'null')):
				result.append(match)

		return result

	def _get_query_type(self):
		"""Determine of what type the query is."""

		if self.query.startswith(SETPREFIX):
			return "set"
		elif self.is_regex or self.uses_globbing():
			return "complex"
		return "simple"
