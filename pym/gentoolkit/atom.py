#!/usr/bin/python
#
# Copyright(c) 2009, Gentoo Foundation
#
# Licensed under the GNU General Public License, v2
#
# $Header$

"""Subclasses portage.dep.Atom to provide methods on a Gentoo atom string."""

__all__ = ('Atom',)

# =======
# Imports
# =======

import weakref

import portage

from gentoolkit.cpv import CPV
from gentoolkit.versionmatch import VersionMatch
from gentoolkit import errors

# =======
# Classes
# =======

class Atom(portage.dep.Atom, CPV):
	"""Portage's Atom class with an improved intersects method from pkgcore.

	portage.dep.Atom provides the following instance variables:

	@type operator: str
	@ivar operator: one of ('=', '=*', '<', '>', '<=', '>=', '~', None)
	@type cp: str
	@ivar cp: cat/pkg
	@type cpv: str
	@ivar cpv: cat/pkg-ver (if ver)
	@type slot: str or None
	@ivar slot: slot passed in as cpv:#
	"""

	# Necessary for Portage versions < 2.1.7
	_atoms = weakref.WeakValueDictionary()

	def __init__(self, atom):
		self.atom = atom

		try:
			portage.dep.Atom.__init__(self, atom)
		except portage.exception.InvalidAtom, err:
			raise errors.GentoolkitInvalidAtom(err)

		# Make operator compatible with intersects
		if self.operator is None:
			self.operator = '='

		self.cpv = CPV(self.cpv)

		# use_conditional is USE flag condition for this Atom to be required:
		# For: !build? ( >=sys-apps/sed-4.0.5 ), use_conditional = '!build'
		self.use_conditional = None

	def __repr__(self):
		uc = self.use_conditional
		uc = "%s? " % uc if uc is not None else ''
		return "<%s %r>" % (self.__class__.__name__, "%s%s" % (uc, self.atom))

	def __setattr__(self, name, value):
		object.__setattr__(self, name, value)

	#R0911:121:Atom.intersects: Too many return statements (20/6)
	#R0912:121:Atom.intersects: Too many branches (23/12)
	# pylint: disable-msg=R0911,R0912
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

		@type other: Any "Intersectable" object
		@param other: other package to compare
		@see: L{pkgcore.ebuild.atom}
		"""
		# Our "cp" (cat/pkg) must match exactly:
		if self.cpv.cp != other.cpv.cp:
			# Check to see if one is name only:
			# Avoid slow partitioning if we're definitely not matching
			# (yes, this is hackish, but it's faster):
			if self.cpv.cp[-1:] != other.cpv.cp[-1:]:
				return False

			if ((not self.cpv.category and self.cpv.name == other.cpv.name) or
				(not other.cpv.category and other.cpv.name == self.cpv.name)):
				return True
			return False

		# If one of us is unversioned we intersect:
		if not self.operator or not other.operator:
			return True

		# If we are both "unbounded" in the same direction we intersect:
		if (('<' in self.operator and '<' in other.operator) or
			('>' in self.operator and '>' in other.operator)):
			return True

		# If one of us is an exact match we intersect if the other matches it:
		if self.operator == '=':
			if other.operator == '=*':
				return self.cpv.fullversion.startswith(other.cpv.fullversion)
			return VersionMatch(other.cpv, op=other.operator).match(self.cpv)
		if other.operator == '=':
			if self.operator == '=*':
				return other.cpv.fullversion.startswith(self.cpv.fullversion)
			return VersionMatch(self.cpv, op=self.operator).match(other.cpv)

		# If we are both ~ matches we match if we are identical:
		if self.operator == other.operator == '~':
			return (self.cpv.version == other.cpv.version and
				self.cpv.revision == other.cpv.revision)

		# If we are both glob matches we match if one of us matches the other.
		if self.operator == other.operator == '=*':
			return (self.cpv.fullversion.startswith(other.cpv.fullversion) or
				other.cpv.fullversion.startswith(self.cpv.fullversion))

		# If one of us is a glob match and the other a ~ we match if the glob
		# matches the ~ (ignoring a revision on the glob):
		if self.operator == '=*' and other.operator == '~':
			return other.cpv.fullversion.startswith(self.cpv.version)
		if other.operator == '=*' and self.operator == '~':
			return self.cpv.fullversion.startswith(other.cpv.version)

		# If we get here at least one of us is a <, <=, > or >=:
		if self.operator in ('<', '<=', '>', '>='):
			ranged, other = self, other
			ranged.operator = self.operator
		else:
			ranged, other = other, self
			ranged.operator = other.operator

		if '<' in other.operator or '>' in other.operator:
			# We are both ranged, and in the opposite "direction" (or
			# we would have matched above). We intersect if we both
			# match the other's endpoint (just checking one endpoint
			# is not enough, it would give a false positive on <=2 vs >2)
			return (VersionMatch(other.cpv, op=other.operator).match(ranged) and
				VersionMatch(ranged.cpv, op=ranged.operator).match(other.cpv))

		if other.operator == '~':
			# Other definitely matches its own version. If ranged also
			# does we're done:
			if VersionMatch(ranged.cpv, op=ranged.operator).match(other.cpv):
				return True
			# The only other case where we intersect is if ranged is a
			# > or >= on other's version and a nonzero revision. In
			# that case other will match ranged. Be careful not to
			# give a false positive for ~2 vs <2 here:
			return (ranged.operator in ('>', '>=') and
				VersionMatch(other.cpv, op=other.operator).match(ranged.cpv))

		if other.operator == '=*':
			# a glob match definitely matches its own version, so if
			# ranged does too we're done:
			if VersionMatch(ranged.cpv, op=ranged.operator).match(other.cpv):
				return True
			if '<' in ranged.operator:
				# If other.revision is not defined then other does not
				# match anything smaller than its own fullversion:
				if not other.cpv.revision:
					return False

				# If other.revision is defined then we can always
				# construct a package smaller than other.fullversion by
				# tagging e.g. an _alpha1 on.
				return ranged.cpv.fullversion.startswith(other.cpv.version)
			else:
				# Remaining cases where this intersects: there is a
				# package greater than ranged.fullversion and
				# other.fullversion that they both match.
				return ranged.cpv.fullversion.startswith(other.cpv.version)

		# Handled all possible ops.
		raise NotImplementedError(
			'Someone added an operator without adding it to intersects')

# vim: set ts=4 sw=4 tw=79:
