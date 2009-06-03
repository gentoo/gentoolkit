# Copyright(c) 2009, Gentoo Foundation
#
# Licensed under the GNU General Public License, v2 or higher

"""Improved versions of the original helpers functions.

As a convention, functions ending in '_packages' or '_match{es}' return
Package objects, while functions ending in 'cpvs' return a sequence of strings.
Functions starting with 'get_' return a set of packages by default and can be
filtered, while functions starting with 'find_' return nothing unless the 
query matches one or more packages.

This should be merged into helpers when a clean path is found.
"""

# Move to Imports section after Python 2.6 is stable
from __future__ import with_statement

__all__ = (
	'compare_package_strings',
	'do_lookup',
	'find_best_match',
	'find_installed_packages',
	'find_packages',
	'get_cpvs',
	'get_installed_cpvs',
	'get_uninstalled_cpvs',
	'uses_globbing'
)
__author__ = 'Douglas Anderson'
__docformat__ = 'epytext'

# =======
# Imports 
# =======

import re
import fnmatch
from functools import partial

import portage
from portage.util import unique_array

import gentoolkit
import gentoolkit.pprinter as pp
from gentoolkit import Config, PORTDB, VARDB
from gentoolkit import errors
from gentoolkit.package import Package

# =========
# Functions
# =========

def compare_package_strings(pkg1, pkg2):
	"""Similar to the builtin cmp, but for package strings. Usually called
	as: package_list.sort(compare_package_strings)

	An alternative is to use the Package descriptor from gentoolkit.package
	>>> pkgs = [Package(x) for x in package_list]
	>>> pkgs.sort()

	@see: >>> help(cmp)
	"""

	pkg1 = portage.versions.catpkgsplit(pkg1)
	pkg2 = portage.versions.catpkgsplit(pkg2)
	# Compare categories
	if pkg1[0] != pkg2[0]:
		return cmp(pkg1[0], pkg2[0])
	# Compare names
	elif pkg1[1] != pkg2[1]:
		return cmp(pkg1[1], pkg2[1])
	# Compare versions
	else:
		return portage.versions.pkgcmp(pkg1[1:], pkg2[1:])


def do_lookup(query, query_opts):
	"""A high-level wrapper around gentoolkit package-finder functions.

	@type query: str
	@param query: pkg, cat/pkg, pkg-ver, cat/pkg-ver, atom or regex
	@type query_opts: dict
	@param query_opts: user-configurable options from the calling module
		Currently supported options are:

		categoryFilter     = str or None
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
		pp.die(2, "Not searching in installed, portage tree or overlay."
			" Nothing to do.")

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

	# pylint: Too many branches (18/12)
	# pylint: disable-message=R0912
	result = []

	if query_opts["printMatchInfo"] and not Config["piping"]:
		print_query_info(query, query_opts)

	cats = prepare_categories(query_opts["categoryFilter"])
	cat = split_query(query)[0]

	pre_filter = []
	# The "get_" functions can pre-filter against the whole package key, 
	# but since we allow globbing now, we run into issues like:
	# >>> portage.dep.dep_getkey("sys-apps/portage-*")
	# 'sys-apps/portage-'
	# So the only way to guarantee we don't overrun the key is to 
	# prefilter by cat only.
	if cats:
		pre_filter = package_finder(predicate=lambda x: x.startswith(cats))
	if cat:
		if query_opts["isRegex"]:
			cat_re = cat
		else:
			cat_re = fnmatch.translate(cat)
			# [::-1] reverses a sequence, so we're emulating an ".rreplace()"
			# except we have to put our "new" string on backwards
			cat_re = cat_re[::-1].replace('$', '*./', 1)[::-1]
		predicate = lambda x: re.match(cat_re, x)
		if pre_filter:
			pre_filter = [x for x in pre_filter if predicate(x)]
		else:
			pre_filter = package_finder(predicate=predicate)
	
	# Post-filter
	if query_opts["isRegex"]:
		predicate = lambda x: re.match(query, x)
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

	cats = prepare_categories(query_opts["categoryFilter"])
	if query_opts["printMatchInfo"] and not Config["piping"]:
		print_query_info(query, query_opts)

	result = package_finder(query)
	if not query_opts["includeInstalled"]:
		result = [x for x in result if not x.is_installed()]

	if cats:
		result = [x for x in result if x.cpv.startswith(cats)]

	return result


def find_best_match(query):
	"""Return the highest unmasked version of a package matching query.
	
	@type query: str
	@param query: can be of the form: pkg, pkg-ver, cat/pkg, cat/pkg-ver, atom
	@rtype: str or None
	"""

	match = PORTDB.xmatch("bestmatch-visible", query)

	return Package(match) if match else None


def find_installed_packages(query):
	"""Return a list of Package objects that matched the search key."""

	try:
		matches = VARDB.match(query)
	# catch the ambiguous package Exception
	except portage.exception.AmbiguousPackageName, err:
		matches = []
		for pkgkey in err[0]:
			matches.extend(VARDB.match(pkgkey))
	except portage.exception.InvalidAtom, err:
		pp.print_warn("Invalid Atom: '%s'" % str(err))
		return []

	return [Package(x) for x in matches]


def find_packages(query, include_masked=False):
	"""Returns a list of Package objects that matched the query.

	@type query: str
	@param query: can be of the form: pkg, pkg-ver, cat/pkg, cat/pkg-ver, atom
	@rtype: list
	@return: matching Package objects
	"""

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

	return [Package(x) for x in unique_array(matches)]


def get_cpvs(predicate=None, include_installed=True):
	"""Get all packages in the Portage tree and overlays. Optionally apply a 
	predicate.
	
	Example usage:
		>>> from gentoolkit.helpers2 import get_cpvs
		>>> len(get_cpvs())
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
	@rtype: list
	@return: ['cat/portdir_pkg-1', 'cat/overlay_pkg-2', ...]
	"""

	if predicate:
		all_cps = [x for x in PORTDB.cp_all() if predicate(x)]
	else:
		all_cps = PORTDB.cp_all()

	all_cpvs = []
	for pkgkey in all_cps:
		all_cpvs.extend(PORTDB.cp_list(pkgkey))

	result = set(all_cpvs)
	all_installed_cpvs = get_installed_cpvs(predicate)

	if include_installed:
		result.update(all_installed_cpvs)
	else:
		result.difference_update(all_installed_cpvs)

	return list(result)


# pylint thinks this is a global variable
# pylint: disable-msg=C0103
get_uninstalled_cpvs = partial(get_cpvs, include_installed=False)


def get_installed_cpvs(predicate=None):
	"""Get all installed packages. Optionally apply a predicate.
	
	@type predicate: function
	@param predicate: a function to filter the package list with
	@rtype: unsorted list
	@return: ['cat/installed_pkg-1', 'cat/installed_pkg-2', ...]
	"""

	if predicate:
		all_installed_cps = [x for x in VARDB.cp_all() if predicate(x)]
	else:
		all_installed_cps = VARDB.cp_all()

	result = []
	for pkgkey in all_installed_cps:
		result.extend(VARDB.cp_list(pkgkey))

	return list(result)


def prepare_categories(category_filter):
	"""Return a tuple of validated categories. Expand globs.

	Example usage:
		>>> prepare_categories('app-portage,sys-apps')
		('app-portage', 'sys-apps')
	"""
	
	if not category_filter:
		return tuple()

	cats = [x.lstrip('=') for x in category_filter.split(',')]
	valid_cats = portage.settings.categories
	good_cats = []
	for cat in cats:
		if set('!*?[]').intersection(set(cat)):
			good_cats.extend(fnmatch.filter(valid_cats, cat))
		elif cat in valid_cats:
			good_cats.append(cat)
		else:
			raise errors.GentoolkitInvalidCategory(cat)

	return tuple(good_cats)


def print_query_info(query, query_opts):
	"""Print info about the query to the screen."""

	cats = prepare_categories(query_opts["categoryFilter"])
	cat, pkg, ver, rev = split_query(query)
	del ver, rev
	if cats:
		cat_str = "in %s " % ', '.join([pp.emph(x) for x in cats])
	elif cat and not query_opts["isRegex"]:
		cat_str = "in %s " % pp.emph(cat)
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


def split_query(query):
	"""Split a query into category, name, version and revision.

	@type query: str
	@param query: pkg, cat/pkg, pkg-ver, cat/pkg-ver, atom or regex
	@rtype: tuple
	@return: (category, pkg_name, version, revision)
		Each tuple element is a string or empty string ("").
	"""

	result = portage.versions.catpkgsplit(query)

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
		pp.print_error("Too many slashes ('/').")
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

	@rtype: bool
	@return: True if query uses globbing, else False
	"""

	if set('!*?[]').intersection(set(query)):
		if portage.dep.get_operator(query):
			# Query may be an atom such as '=sys-apps/portage-2.2*'
			pass
		else:
			return True

	return False
