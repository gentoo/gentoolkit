# /usr/bin/python2
#
# Copyright(c) 2004, Karl Trygve Kalleberg <karltk@gentoo.org>
# Copyright(c) 2004, Gentoo Foundation
#
# Licensed under the GNU General Public License, v2
#
# $Header$

import portage
from gentoolkit import *
from package import *
from portage_util import unique_array

def find_packages(search_key, masked=False):
	"""Returns a list of Package objects that matched the search key."""
	try:
		if masked:
			t = portage.db["/"]["porttree"].dbapi.xmatch("match-all", search_key)
			t += portage.db["/"]["vartree"].dbapi.match(search_key)
		else:
			t = portage.db["/"]["porttree"].dbapi.match(search_key)
			t += portage.db["/"]["vartree"].dbapi.match(search_key)
	# catch the "amgigous package" Exception
	except ValueError, e:
		if type(e[0]) == types.ListType:
			t = []
			for cp in e[0]:
				if masked:
					t += portage.db["/"]["porttree"].dbapi.xmatch("match-all", cp)
					t += portage.db["/"]["vartree"].dbapi.match(cp)
				else:
					t += portage.db["/"]["porttree"].dbapi.match(cp)
					t += portage.db["/"]["vartree"].dbapi.match(cp)
		else:
			raise ValueError(e)
	# Make the list of packages unique
	t = unique_array(t)
	t.sort()
	return [Package(x) for x in t]

def find_installed_packages(search_key, masked=False):
	"""Returns a list of Package objects that matched the search key."""
	try:
			t = portage.db["/"]["vartree"].dbapi.match(search_key)
	# catch the "amgigous package" Exception
	except ValueError, e:
		if type(e[0]) == types.ListType:
			t = []
			for cp in e[0]:
				t += portage.db["/"]["vartree"].dbapi.match(cp)
		else:
			raise ValueError(e)
	return [Package(x) for x in t]

def find_best_match(search_key):
	"""Returns a Package object for the best available installed candidate that
	matched the search key."""
	t = portage.db["/"]["vartree"].dep_bestmatch(search_key)
	if t:
		return Package(t)
	return None

def find_system_packages(prefilter=None):
	"""Returns a tuple of lists, first list is resolved system packages,
	second is a list of unresolved packages."""
	pkglist = settings.packages
	resolved = []
	unresolved = []
	for x in pkglist:
		cpv = x.strip()
		if len(cpv) and cpv[0] == "*":
			pkg = find_best_match(cpv)
			if pkg:
				resolved.append(pkg)
			else:
				unresolved.append(cpv)
	return (resolved, unresolved)

def find_world_packages(prefilter=None):
	"""Returns a tuple of lists, first list is resolved world packages,
	seond is unresolved package names."""
	f = open(portage.root+portage.WORLD_FILE)
	pkglist = f.readlines()
	resolved = []
	unresolved = []
	for x in pkglist:
		cpv = x.strip()
		if len(cpv) and cpv[0] != "#":
			pkg = find_best_match(cpv)
			if pkg:
				resolved.append(pkg)
			else:
				unresolved.append(cpv)
	return (resolved,unresolved)

def find_all_installed_packages(prefilter=None):
	"""Returns a list of all installed packages, after applying the prefilter
	function"""
	t = vartree.dbapi.cpv_all()
	if prefilter:
		t = filter(prefilter,t)
	return [Package(x) for x in t]

def find_all_uninstalled_packages(prefilter=None):
	"""Returns a list of all uninstalled packages, after applying the prefilter
	function"""
	alist = find_all_packages(prefilter)
	return [x for x in alist if not x.is_installed()]

def find_all_packages(prefilter=None):
	"""Returns a list of all known packages, installed or not, after applying
	the prefilter function"""
	t = porttree.dbapi.cp_all()
	t += vartree.dbapi.cp_all()
	if prefilter:
		t = filter(prefilter,t)
	t = unique_array(t)
	t2 = []
	for x in t:
		t2 += porttree.dbapi.cp_list(x)
		t2 += vartree.dbapi.cp_list(x)
		t2 = unique_array(t2)
	return [Package(x) for x in t2]

def split_package_name(name):
	"""Returns a list on the form [category, name, version, revision]. Revision will
	be 'r0' if none can be inferred. Category and version will be empty, if none can
	be inferred."""
	r = portage.catpkgsplit(name)
	if not r:
		r = name.split("/")
		if len(r) == 1:
			return ["", name, "", "r0"]
		else:
			return r + ["", "r0"]
	if r[0] == 'null':
		r[0] = ''
	return r

def sort_package_list(pkglist):
	"""Returns the list ordered in the same way portage would do with lowest version
	at the head of the list."""
	pkglist.sort(Package.compare_version)
	return pkglist

if __name__ == "__main__":
	print "This module is for import only"


