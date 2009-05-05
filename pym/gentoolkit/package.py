#! /usr/bin/python
#
# Copyright(c) 2004, Karl Trygve Kalleberg <karltk@gentoo.org>
# Copyright(c) 2004-2009, Gentoo Foundation
#
# Licensed under the GNU General Public License, v2
#
# $Header$

# =======
# Imports 
# =======

import os

import portage
from portage import catpkgsplit
from portage.versions import vercmp

from gentoolkit import *
from gentoolkit import errors

# =======
# Globals
# =======

PORTDB = portage.db[portage.root]["porttree"].dbapi
VARDB  = portage.db[portage.root]["vartree"].dbapi

# =======
# Classes
# =======

class Package(object):
	"""Package descriptor. Contains convenience functions for querying the
	state of a package, its contents, name manipulation, ebuild info and
	similar."""

	def __init__(self, arg):

		self._cpv = arg
		self.cpv = self._cpv

		if self.cpv[0] in ('<', '>'):
			if self.cpv[1] == '=':
				self.operator = self.cpv[:2]
				self.cpv = self.cpv[2:]
			else:
				self.operator = self.cpv[0]
				self.cpv = self.cpv[1:]
		elif self.cpv[0] == '=':
			if self.cpv[-1] == '*':
				self.operator = '=*'
				self.cpv = self.cpv[1:-1]
			else:
				self.cpv = self.cpv[1:]
				self.operator = '='
		elif self.cpv[0] == '~':
			self.operator = '~'
			self.cpv = self.cpv[1:]
		else:
			self.operator = '='
			self._cpv = '=%s' % self._cpv

		if not portage.dep.isvalidatom(self._cpv):
			raise errors.GentoolkitInvalidCPV(self._cpv)

		cpv_split = portage.catpkgsplit(self.cpv)

		try:
			self.key = "/".join(cpv_split[:2])
		except TypeError:
			# catpkgsplit returned None
			raise errors.GentoolkitInvalidCPV(self._cpv)

		cpv_split = list(cpv_split)
		if cpv_split[0] == 'null':
			cpv_split[0] = ''
		if cpv_split[3] == 'r0':
			cpv_split[3] = ''
		self.cpv_split = cpv_split
		self._scpv = self.cpv_split # XXX: namespace compatability 03/09

		self._db = None
		self._settings = settings
		self._settingslock = settingslock
		self._portdir_path = os.path.realpath(settings["PORTDIR"])

		self.category = self.cpv_split[0]
		self.name = self.cpv_split[1]
		self.version = self.cpv_split[2]
		self.revision = self.cpv_split[3]
		if not self.revision:
			self.fullversion = self.version
		else:
			self.fullversion = "%s-%s" % (self.version, self.revision)

	def __repr__(self):
		return "<%s %s @%#8x>" % (self.__class__.__name__, self._cpv, id(self))

	def __cmp__(self, other):
		# FIXME: __cmp__ functions dissallowed in py3k; need __lt__, __gt__.
		if not isinstance(other, self.__class__):
			raise TypeError("other isn't of %s type, is %s" %
				(self.__class__, other.__class__))

		if self.category != other.category:
			return cmp(self.category, other.category)
		elif self.name != other.name:
			return cmp(self.name, other.name)
		else:
			# FIXME: this cmp() hack is for vercmp not using -1,0,1
			# See bug 266493; this was fixed in portage-2.2_rc31
			#return portage.vercmp(self.fullversion, other.fullversion)
			return cmp(portage.vercmp(self.fullversion, other.fullversion), 0)

	def __eq__(self, other):
		return hash(self) == hash(other)

	def __ne__(self, other):
		return hash(self) != hash(other)

	def __hash__(self):
		return hash(self._cpv)

	def __contains__(self, key):
		return key in self._cpv
	
	def __str__(self):
		return self._cpv

	def get_name(self):
		"""Returns base name of package, no category nor version"""
		return self.name

	def get_version(self):
		"""Returns version of package, with revision number"""
		return self.fullversion

	def get_category(self):
		"""Returns category of package"""
		return self.category

	def get_settings(self, key):
		"""Returns the value of the given key for this package (useful 
		for package.* files."""
		self._settingslock.acquire()
		self._settings.setcpv(self.cpv)
		v = self._settings[key]
		self._settingslock.release()
		return v

	def get_cpv(self):
		"""Returns full Category/Package-Version string"""
		return self.cpv

	def get_provide(self):
		"""Return a list of provides, if any"""
		if not self.is_installed():
			try:
				x = [self.get_env_var('PROVIDE')]
			except KeyError:
				x = []
			return x
		else:
			return vartree.get_provide(self.cpv)

	def get_dependants(self):
		"""Retrieves a list of CPVs for all packages depending on this one"""
		raise NotImplementedError("Not implemented yet!")

	def get_runtime_deps(self):
		"""Returns a linearised list of first-level run time dependencies for 
		this package, on the form [(comparator, [use flags], cpv), ...]
		"""
		# Try to use the portage tree first, since emerge only uses the tree 
		# when calculating dependencies
		try:
			cd = self.get_env_var("RDEPEND", porttree).split()
		except KeyError:
			cd = self.get_env_var("RDEPEND", vartree).split()
		r,i = self._parse_deps(cd)
		return r

	def get_compiletime_deps(self):
		"""Returns a linearised list of first-level compile time dependencies
		for this package, on the form [(comparator, [use flags], cpv), ...]
		"""
		# Try to use the portage tree first, since emerge only uses the tree 
		# when calculating dependencies
		try:
			rd = self.get_env_var("DEPEND", porttree).split()
		except KeyError:
			rd = self.get_env_var("DEPEND", vartree).split()
		r,i = self._parse_deps(rd)
		return r

	def get_postmerge_deps(self):
		"""Returns a linearised list of first-level post merge dependencies 
		for this package, on the form [(comparator, [use flags], cpv), ...]
		"""
		# Try to use the portage tree first, since emerge only uses the tree 
		# when calculating dependencies
		try:
			pd = self.get_env_var("PDEPEND", porttree).split()
		except KeyError:
			pd = self.get_env_var("PDEPEND", vartree).split()
		r,i = self._parse_deps(pd)
		return r

	def intersects(self, other):
		"""Check if a passed in package atom "intersects" this atom.

		Lifted from pkgcore.

		Two atoms "intersect" if a package can be constructed that
		matches both:
		  - if you query for just "dev-lang/python" it "intersects" both
			"dev-lang/python" and ">=dev-lang/python-2.4"
		  - if you query for "=dev-lang/python-2.4" it "intersects"
			">=dev-lang/python-2.4" and "dev-lang/python" but not
			"<dev-lang/python-2.3"

		@type other: gentoolkit.package.Package
		@param other: other package to compare
		@see: pkgcore.ebuild.atom.py
		"""
		# Our "key" (cat/pkg) must match exactly:
		if self.key != other.key:
			return False

		# If we are both "unbounded" in the same direction we intersect:
		if (('<' in self.operator and '<' in other.operator) or
			('>' in self.operator and '>' in other.operator)):
			return True

		# If one of us is an exact match we intersect if the other matches it:
		if self.operator == '=':
			if other.operator == '=*':
				return self.fullversion.startswith(other.fullversion)
			return VersionMatch(frompkg=other).match(self)
		if other.operator == '=':
			if self.operator == '=*':
				return other.fullversion.startswith(self.fullversion)
			return VersionMatch(frompkg=self).match(other)

		# If we are both ~ matches we match if we are identical:
		if self.operator == other.operator == '~':
			return (self.version == other.version and
					self.revision == other.revision)

		# If we are both glob matches we match if one of us matches the other.
		if self.operator == other.operator == '=*':
			return (self.fullver.startswith(other.fullver) or
					other.fullver.startswith(self.fullver))

		# If one of us is a glob match and the other a ~ we match if the glob
		# matches the ~ (ignoring a revision on the glob):
		if self.operator == '=*' and other.operator == '~':
			return other.fullversion.startswith(self.version)
		if other.operator == '=*' and self.operator == '~':
			return self.fullversion.startswith(other.version)

		# If we get here at least one of us is a <, <=, > or >=:
		if self.operator in ('<', '<=', '>', '>='):
			ranged, other = self, other
		else:
			ranged, other = other, self

		if '<' in other.operator or '>' in other.operator:
			# We are both ranged, and in the opposite "direction" (or
			# we would have matched above). We intersect if we both
			# match the other's endpoint (just checking one endpoint
			# is not enough, it would give a false positive on <=2 vs >2)
			return (
				VersionMatch(frompkg=other).match(ranged) and
				VersionMatch(frompkg=ranged).match(other))

		if other.operator == '~':
			# Other definitely matches its own version. If ranged also
			# does we're done:
			if VersionMatch(frompkg=ranged).match(other):
				return True
			# The only other case where we intersect is if ranged is a
			# > or >= on other's version and a nonzero revision. In
			# that case other will match ranged. Be careful not to
			# give a false positive for ~2 vs <2 here:
			return ranged.operator in ('>', '>=') and VersionMatch(
				other.operator, other.version, other.revision).match(ranged)

		if other.operator == '=*':
			# a glob match definitely matches its own version, so if
			# ranged does too we're done:
			if VersionMatch(
				ranged.operator, ranged.version, ranged.revision).match(other):
				return True
			if '<' in ranged.operator:
				# If other.revision is not defined then other does not
				# match anything smaller than its own fullver:
				if not other.revision:
					return False

				# If other.revision is defined then we can always
				# construct a package smaller than other.fullver by
				# tagging e.g. an _alpha1 on.
				return ranged.fullversion.startswith(other.version)
			else:
				# Remaining cases where this intersects: there is a
				# package greater than ranged.fullver and
				# other.fullver that they both match.
				return ranged.fullversion.startswith(other.version)

		# Handled all possible ops.
		raise NotImplementedError(
			'Someone added an operator without adding it to intersects')


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
			# conjunction, like in "|| ( ( foo bar ) baz )" => recurse
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
		"""Returns True if this package is installed (merged)"""
		return VARDB.cpv_exists(self.cpv)

	def is_overlay(self):
		"""Returns True if the package is in an overlay."""
		dir,ovl = portage.portdb.findname2(self.cpv)
		return ovl != self._portdir_path

	def is_masked(self):
		"""Returns true if this package is masked against installation. 
		Note: We blindly assume that the package actually exists on disk
		somewhere."""
		unmasked = portage.portdb.xmatch("match-visible", self.cpv)
		return self.cpv not in unmasked

	def get_ebuild_path(self,in_vartree=0):
		"""Returns the complete path to the .ebuild file"""
		if in_vartree:
			return vartree.getebuildpath(self.cpv)
		else:
			return portage.portdb.findname(self.cpv)

	def get_package_path(self):
		"""Returns the path to where the ChangeLog, Manifest, .ebuild files
		reside"""
		p = self.get_ebuild_path()
		sp = p.split("/")
		if sp:
			# FIXME: use os.path.join
			return "/".join(sp[:-1])

	def get_env_var(self, var, tree=""):
		"""Returns one of the predefined env vars DEPEND, RDEPEND,
		SRC_URI,...."""
		if tree == "":
			mytree = vartree
			if not self.is_installed():
				mytree = porttree
		else:
			mytree = tree
		try:
			r = mytree.dbapi.aux_get(self.cpv,[var])
		except KeyError:
			# aux_get raises KeyError if it encounters a bad digest, etc
			raise
		if not r:
			raise errors.GentoolkitFatalError("Could not find the package tree")
		if len(r) != 1:
			raise errors.GentoolkitFatalError("Should only get one element!")
		return r[0]

	def get_use_flags(self):
		"""Returns the USE flags active at time of installation"""
		self._initdb()
		if self.is_installed():
			return self._db.getfile("USE")
		return ""

	def get_contents(self):
		"""Returns the full contents, as a dictionary, in the form
		[ '/bin/foo' : [ 'obj', '1052505381', '45ca8b89751...' ], ... ]"""
		self._initdb()
		if self.is_installed():
			return self._db.getcontents()
		return {}		

	# XXX >
	def compare_version(self,other):
		"""Compares this package's version to another's CPV; returns -1, 0, 1.
		
		Deprecated in favor of __cmp__.
		"""
		v1 = self.cpv_split
		v2 = catpkgsplit(other.get_cpv())
		# if category is different
		if v1[0] != v2[0]:
			return cmp(v1[0],v2[0])
		# if name is different
		elif v1[1] != v2[1]:
			return cmp(v1[1],v2[1])
		# Compare versions
		else:
			return portage.pkgcmp(v1[1:],v2[1:])
	# < XXX

	def size(self):
		"""Estimates the installed size of the contents of this package,
		if possible.
		Returns [size, number of files in total, number of uncounted files]
		"""
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
		when necessary.
		"""
		if not self._db:
			self._db = portage.dblink(
				category,
				"%s-%s" % (self.name, self.fullversion),
				settings["ROOT"],
				settings
			)
			

class VersionMatch(object):
	"""Package restriction implementing Gentoo ebuild version comparison rules.
	From pkgcore.ebuild.atom_restricts.

	Any overriding of this class *must* maintain numerical order of
	self.vals, see intersect for reason why. vals also must be a tuple.
	"""
	_convert_op2int = {(-1,):"<", (-1, 0): "<=", (0,):"=",
		(0, 1):">=", (1,):">"}

	_convert_int2op = dict([(v, k) for k, v in _convert_op2int.iteritems()])
	del k, v

	def __init__(self, **kwargs):
		"""This class will either create a VersionMatch instance out of
		a Package instance, or from explicitly passed in operator, version,
		and revision.

		Possible args:
			frompkg=<gentoolkit.package.Package> instance

			OR

			op=str: version comparison to do,
				valid operators are ('<', '<=', '=', '>=', '>', '~')
			ver=str: version to base comparison on
			rev=str: revision to base comparison on
		"""
		if 'frompkg' in kwargs and kwargs['frompkg']:
			self.operator = kwargs['frompkg'].operator
			self.version = kwargs['frompkg'].version
			self.revision = kwargs['frompkg'].revision
			self.fullversion = kwargs['frompkg'].fullversion
		elif set(('op', 'ver', 'rev')) == set(kwargs):
			self.operator = kwargs['op']
			self.version = kwargs['ver']
			self.revision = kwargs['rev']
			if not self.revision:
				self.fullversion = self.version
			else:
				self.fullversion = "%s-%s" % (self.version, self.revision)
		else:
			raise TypeError('__init__() takes either a Package instance '
				'via frompkg= or op=, ver= and rev= all passed in')

		if self.operator != "~" and self.operator not in self._convert_int2op:
			# FIXME: change error
			raise errors.InvalidVersion(self.ver, self.rev,
				"invalid operator, '%s'" % operator)

		if self.operator == "~":
			if not self.version:
				raise ValueError(
					"for ~ op, version must be specified")
			self.droprevision = True
			self.values = (0,)
		else:
			self.droprevision = False
			self.values = self._convert_int2op[self.operator]

	def match(self, pkginst):
		if self.droprevision:
			ver1, ver2 = self.version, pkginst.version
		else:
			ver1, ver2 = self.fullversion, pkginst.fullversion

		#print "== VersionMatch.match DEBUG START =="
		#print "ver1:", ver1
		#print "ver2:", ver2
		#print "vercmp(ver2, ver1):", vercmp(ver2, ver1)
		#print "self.values:", self.values
		#print "vercmp(ver2, ver1) in values?",
		#print "vercmp(ver2, ver1) in self.values"
		#print "==  VersionMatch.match DEBUG END  =="

		return vercmp(ver2, ver1) in self.values

	def __str__(self):
		s = self._convert_op2int[self.values]

		if self.droprevision or not self.revision:
			return "ver %s %s" % (s, self.version)
		return "ver-rev %s %s-%s" % (s, self.version, self.revision)

	def __repr__(self):
		return "<%s %s @%#8x>" % (self.__class__.__name__, str(self), id(self))

	@staticmethod
	def _convert_ops(inst):
		if inst.droprevision:
			return inst.values
		return tuple(sorted(set((-1, 0, 1)).difference(inst.values)))

	def __eq__(self, other):
		if self is other:
			return True
		if isinstance(other, self.__class__):
			if (self.droprevsion != other.droprevsion or
				self.version != other.version or
				self.revision != other.revision):
				return False
			return self._convert_ops(self) == self._convert_ops(other)

		return False

	def __hash__(self):
		return hash((self.droprevision, self.version, self.revision,
			self.values))
