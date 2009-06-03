#!/usr/bin/python
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
from portage.versions import catpkgsplit, vercmp

import gentoolkit.pprinter as pp
from gentoolkit import settings, settingslock, PORTDB, VARDB
from gentoolkit import errors
from gentoolkit.versionmatch import VersionMatch

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

	def __eq__(self, other):
		return hash(self) == hash(other)

	def __ne__(self, other):
		return hash(self) != hash(other)

	def __lt__(self, other):
		if not isinstance(other, self.__class__):
			raise TypeError("other isn't of %s type, is %s" %
				(self.__class__, other.__class__))

		if self.category != other.category:
			return self.category < other.category
		elif self.name != other.name:
			return self.name < other.name
		else:
			# FIXME: this cmp() hack is for vercmp not using -1,0,1
			# See bug 266493; this was fixed in portage-2.2_rc31
			#return portage.vercmp(self.fullversion, other.fullversion)
			result = cmp(portage.vercmp(self.fullversion, other.fullversion), 0)
			if result == -1:
				return True
			else:
				return False

	def __gt__(self, other):
		return not self.__lt__(other)

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
		try:
			self._settingslock.acquire()
			self._settings.setcpv(self.cpv)
			result = self._settings[key]
		finally:
			self._settingslock.release()
		return result

	def get_cpv(self):
		"""Returns full Category/Package-Version string"""
		return self.cpv

	def get_provide(self):
		"""Return a list of provides, if any"""
		if self.is_installed():
			result = VARDB.get_provide(self.cpv)
		else:
			try:
				result = [self.get_env_var('PROVIDE')]
			except KeyError:
				result = []
		return result

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
			rdepends = self.get_env_var("RDEPEND", PORTDB).split()
		except KeyError:
			rdepends = self.get_env_var("RDEPEND", VARDB).split()
		return self._parse_deps(rdepends)[0]

	def get_compiletime_deps(self):
		"""Returns a linearised list of first-level compile time dependencies
		for this package, on the form [(comparator, [use flags], cpv), ...]
		"""
		# Try to use the portage tree first, since emerge only uses the tree 
		# when calculating dependencies
		try:
			depends = self.get_env_var("DEPEND", PORTDB).split()
		except KeyError:
			depends = self.get_env_var("DEPEND", VARDB).split()
		return self._parse_deps(depends)[0]

	def get_postmerge_deps(self):
		"""Returns a linearised list of first-level post merge dependencies 
		for this package, on the form [(comparator, [use flags], cpv), ...]
		"""
		# Try to use the portage tree first, since emerge only uses the tree 
		# when calculating dependencies
		try:
			postmerge_deps = self.get_env_var("PDEPEND", PORTDB).split()
		except KeyError:
			postmerge_deps = self.get_env_var("PDEPEND", VARDB).split()
		return self._parse_deps(postmerge_deps)[0]

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

		@type other: L{gentoolkit.package.Package}
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
			return VersionMatch(other).match(self)
		if other.operator == '=':
			if self.operator == '=*':
				return other.fullversion.startswith(self.fullversion)
			return VersionMatch(self).match(other)

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
				VersionMatch(other).match(ranged) and
				VersionMatch(ranged).match(other))

		if other.operator == '~':
			# Other definitely matches its own version. If ranged also
			# does we're done:
			if VersionMatch(ranged).match(other):
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
		ebuild, tree = portage.portdb.findname2(self.cpv)
		return tree != self._portdir_path

	def is_masked(self):
		"""Returns true if this package is masked against installation. 
		Note: We blindly assume that the package actually exists on disk
		somewhere."""
		unmasked = portage.portdb.xmatch("match-visible", self.cpv)
		return self.cpv not in unmasked

	def get_ebuild_path(self, in_vartree=False):
		"""Returns the complete path to the .ebuild file"""
		if in_vartree:
			return VARDB.getebuildpath(self.cpv)
		return PORTDB.findname(self.cpv)

	def get_package_path(self):
		"""Returns the path to where the ChangeLog, Manifest, .ebuild files
		reside"""
		ebuild_path = self.get_ebuild_path()
		path_split = ebuild_path.split("/")
		if path_split:
			return os.sep.join(path_split[:-1])

	def get_env_var(self, var, tree=None):
		"""Returns one of the predefined env vars DEPEND, RDEPEND,
		SRC_URI,...."""
		if tree == None:
			tree = VARDB
			if not self.is_installed():
				tree = PORTDB
		result = tree.aux_get(self.cpv, [var])
		if not result:
			raise errors.GentoolkitFatalError("Could not find the package tree")
		if len(result) != 1:
			raise errors.GentoolkitFatalError("Should only get one element!")
		return result[0]

	def get_use_flags(self):
		"""Returns the USE flags active at time of installation"""
		self._initdb()
		if self.is_installed():
			return self._db.getfile("USE")

	def get_contents(self):
		"""Returns the full contents, as a dictionary, in the form
		['/bin/foo' : [ 'obj', '1052505381', '45ca8b89751...' ], ... ]"""
		self._initdb()
		if self.is_installed():
			return self._db.getcontents()
		return {}		

	def size(self):
		"""Estimates the installed size of the contents of this package,
		if possible.
		Returns (size, number of files in total, number of uncounted files)
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
		return (size, files, uncounted)

	def _initdb(self):
		"""Internal helper function; loads package information from disk,
		when necessary.
		"""
		if not self._db:
			self._db = portage.dblink(
				self.category,
				"%s-%s" % (self.name, self.fullversion),
				settings["ROOT"],
				settings
			)


class PackageFormatter(object):
	"""When applied to a L{gentoolkit.package.Package} object, determine the
	location (Portage Tree vs. overlay), install status and masked status. That
	information can then be easily formatted and displayed.
	
	Example usage:
		>>> from gentoolkit.helpers2 import find_packages
		>>> from gentoolkit.package import PackageFormatter
		>>> pkgs = [PackageFormatter(x) for x in find_packages('gcc')]
		>>> for pkg in pkgs:
		...     # Only print packages that are installed and from the Portage
		...     # tree
		...     if set('IP').issubset(pkg.location):
		...             print pkg
		... 
		[IP-] [  ] sys-devel/gcc-4.3.2-r3 (4.3)

	@type pkg: L{gentoolkit.package.Package}
	@param pkg: package to format
	@type format: L{bool}
	@param format: Whether to format the package name or not. 
		Essentially C{format} should be set to False when piping or when
		quiet output is desired. If C{format} is False, only the location
		attribute will be created to save time.
	"""

	def __init__(self, pkg, format=True):
		location = ''
		maskmodes = ['  ', ' ~', ' -', 'M ', 'M~', 'M-']

		self.pkg = pkg
		self.format = format
		if format:
			self.arch = settings["ARCH"]
			self.mask = maskmodes[self.get_mask_status()]
			self.slot = pkg.get_env_var("SLOT")
		self.location = self.get_package_location()

	def __repr__(self):
		return "<%s %s @%#8x>" % (self.__class__.__name__, self.pkg, id(self))

	def __str__(self):
		if self.format:
			return "[%(location)s] [%(mask)s] %(package)s (%(slot)s)" % {
				'location': self.location,
				'mask': pp.maskflag(self.mask),
				'package': pp.cpv(self.pkg.cpv),
				'slot': self.slot
			}
		else:
			return self.pkg.cpv

	def get_package_location(self):
		"""Get the physical location of a package on disk.

		@rtype: str
		@return: one of:
			'-P-' : Not installed and from the Portage tree
			'--O' : Not installed and from an overlay
			'IP-' : Installed and from the Portage tree
			'I-O' : Installed and from an overlay
		"""

		result = ['-', '-', '-']

		if self.pkg.is_installed():
			result[0] = 'I'
		if self.pkg.is_overlay():
			result[2] = 'O'
		else:
			result[1] = 'P'

		return ''.join(result)

	def get_mask_status(self):
		"""Get the mask status of a given package. 

		@type pkg: L{gentoolkit.package.Package}
		@param pkg: pkg to get mask status of
		@type arch: str
		@param arch: output of gentoolkit.settings["ARCH"]
		@rtype: int
		@return: an index for this list: ["  ", " ~", " -", "M ", "M~", "M-"]
			0 = not masked
			1 = keyword masked
			2 = arch masked
			3 = hard masked
			4 = hard and keyword masked,
			5 = hard and arch masked
		"""

		keywords = self.pkg.get_env_var("KEYWORDS").split()
		mask_status = 0
		if self.pkg.is_masked():
			mask_status += 3
		if ("~%s" % self.arch) in keywords:
			mask_status += 1
		elif ("-%s" % self.arch) in keywords or "-*" in keywords:
			mask_status += 2

		return mask_status
