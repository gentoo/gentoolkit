#! /usr/bin/python2
#
# Copyright(c) 2004, Karl Trygve Kalleberg <karltk@gentoo.org>
# Copyright(c) 2004, Gentoo Foundation
#
# Licensed under the GNU General Public License, v2
#
# $Header$

from errors import FatalError
import portage
from gentoolkit import *

class Package:
	"""Package descriptor. Contains convenience functions for querying the
	state of a package, its contents, name manipulation, ebuild info and
	similar."""

	def __init__(self,cpv):
		self._cpv = cpv
		self._scpv = portage.catpkgsplit(self._cpv)
		
		if not self._scpv:
			raise FatalError("invalid cpv: %s" % cpv)
		self._db = None
		self._settings = settings
		self._settingslock = settingslock

	def get_name(self):
		"""Returns base name of package, no category nor version"""
		return self._scpv[1]

	def get_version(self):
		"""Returns version of package, with revision number"""
		v = self._scpv[2]
		if self._scpv[3] != "r0":
			v += "-" + self._scpv[3]
		return v

	def get_category(self):
		"""Returns category of package"""
		return self._scpv[0]

	def get_settings(self, key):
		"""Returns the value of the given key for this package (useful 
		for package.* files."""
		self._settingslock.acquire()
		self._settings.setcpv(self._cpv)
		v = self._settings[key]
		self._settingslock.release()
		return v

	def get_cpv(self):
		"""Returns full Category/Package-Version string"""
		return self._cpv

	def get_provide(self):
		"""Return a list of provides, if any"""
		if not self.is_installed():
			try:
				x = [self.get_env_var('PROVIDE')]
			except KeyError:
				x = []
			return x
		else:
			return vartree.get_provide(self._cpv)

	def get_dependants(self):
		"""Retrieves a list of CPVs for all packages depending on this one"""
		raise NotImplementedError("Not implemented yet!")

	def get_runtime_deps(self):
		"""Returns a linearised list of first-level run time dependencies for this package, on
		the form [(comparator, [use flags], cpv), ...]"""
		# Try to use the portage tree first, since emerge only uses the tree when calculating dependencies
		try:
			cd = self.get_env_var("RDEPEND", porttree).split()
		except KeyError:
			cd = self.get_env_var("RDEPEND", vartree).split()
		r,i = self._parse_deps(cd)
		return r

	def get_compiletime_deps(self):
		"""Returns a linearised list of first-level compile time dependencies for this package, on
		the form [(comparator, [use flags], cpv), ...]"""
		# Try to use the portage tree first, since emerge only uses the tree when calculating dependencies
		try:
			rd = self.get_env_var("DEPEND", porttree).split()
		except KeyError:
			rd = self.get_env_var("DEPEND", vartree).split()
		r,i = self._parse_deps(rd)
		return r

	def get_postmerge_deps(self):
		"""Returns a linearised list of first-level post merge dependencies for this package, on
		the form [(comparator, [use flags], cpv), ...]"""
		# Try to use the portage tree first, since emerge only uses the tree when calculating dependencies
		try:
			pd = self.get_env_var("PDEPEND", porttree).split()
		except KeyError:
			pd = self.get_env_var("PDEPEND", vartree).split()
		r,i = self._parse_deps(pd)
		return r

	def _parse_deps(self,deps,curuse=[],level=0):
		# store (comparator, [use predicates], cpv)
		r = []
		comparators = ["~","<",">","=","<=",">="]
		end = len(deps)
		i = 0
		while i < end:
			tok = deps[i]
			if tok == ')':
				return r,i
			if tok[-1] == "?":
				tok = tok.replace("?","")
				sr,l = self._parse_deps(deps[i+2:],curuse=curuse+[tok],level=level+1)
				r += sr
				i += l + 3
				continue
			if tok == "||":
				sr,l = self._parse_deps(deps[i+2:],curuse,level=level+1)
				r += sr
				i += l + 3
				continue
			# conjonction, like in "|| ( ( foo bar ) baz )" => recurse
			if tok == "(":
				sr,l = self._parse_deps(deps[i+1:],curuse,level=level+1)
				r += sr
				i += l + 2
				continue
			# pkg block "!foo/bar" => ignore it
			if tok[0] == "!":
				i += 1
				continue
			# pick out comparator, if any
			cmp = ""
			for c in comparators:
				if tok.find(c) == 0:
					cmp = c
			tok = tok[len(cmp):]
			r.append((cmp,curuse,tok))
			i += 1
		return r,i

	def is_installed(self):
		"""Returns true if this package is installed (merged)"""
		self._initdb()
		return os.path.exists(self._db.getpath())

	def is_overlay(self):
		"""Returns true if the package is in an overlay."""
		dir,ovl = portage.portdb.findname2(self._cpv)
		return ovl != settings["PORTDIR"]

	def is_masked(self):
		"""Returns true if this package is masked against installation. Note: We blindly assume that
		the package actually exists on disk somewhere."""
		unmasked = portage.portdb.xmatch("match-visible", "=" + self._cpv)
		return self._cpv not in unmasked

	def get_ebuild_path(self,in_vartree=0):
		"""Returns the complete path to the .ebuild file"""
		if in_vartree:
			return vartree.getebuildpath(self._cpv)
		else:
			return portage.portdb.findname(self._cpv)

	def get_package_path(self):
		"""Returns the path to where the ChangeLog, Manifest, .ebuild files reside"""
		p = self.get_ebuild_path()
		sp = p.split("/")
		if len(sp):
			return "/".join(sp[:-1])

	def get_env_var(self, var, tree=""):
		"""Returns one of the predefined env vars DEPEND, RDEPEND, SRC_URI,...."""
		if tree == "":
			mytree = vartree
			if not self.is_installed():
				mytree = porttree
		else:
			mytree = tree
		r = mytree.dbapi.aux_get(self._cpv,[var])
		if not r:
			raise FatalError("Could not find the package tree")
		if len(r) != 1:
			raise FatalError("Should only get one element!")
		return r[0]

	def get_use_flags(self):
		"""Returns the USE flags active at time of installation"""
		self._initdb()
		if self.is_installed():
			return self._db.getfile("USE")
		return ""

	def get_contents(self):
		"""Returns the full contents, as a dictionary, on the form
		[ '/bin/foo' : [ 'obj', '1052505381', '45ca8b8975d5094cd75bdc61e9933691' ], ... ]"""
		self._initdb()
		if self.is_installed():
			return self._db.getcontents()
		return {}		

	def compare_version(self,other):
		"""Compares this package's version to another's CPV; returns -1, 0, 1"""
		v1 = self._scpv
		v2 = portage.catpkgsplit(other.get_cpv())
		# if category is different
		if v1[0] != v2[0]:
			return cmp(v1[0],v2[0])
		# if name is different
		elif v1[1] != v2[1]:
			return cmp(v1[1],v2[1])
		# Compare versions
		else:
			return portage.pkgcmp(v1[1:],v2[1:])

	def size(self):
		"""Estimates the installed size of the contents of this package, if possible.
		Returns [size, number of files in total, number of uncounted files]"""
		contents = self.get_contents()
		size = 0
		uncounted = 0
		files = 0
		for x in contents:
			try:
				size += os.lstat(x).st_size
				files += 1
			except OSError:
				uncounted += 1
		return [size, files, uncounted]

	def _initdb(self):
		"""Internal helper function; loads package information from disk,
		when necessary"""
		if not self._db:
			cat = self.get_category()
			pnv = self.get_name()+"-"+self.get_version()
			self._db = portage.dblink(cat,pnv,settings["ROOT"],settings)
