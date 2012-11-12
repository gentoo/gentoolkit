# Copyright(c) 2009, Gentoo Foundation
#
# Licensed under the GNU General Public License, v2
#
# $Header: $

"""Provides a class for easy calculating dependencies for a given CPV."""

__docformat__ = 'epytext'
__all__ = ('Dependencies',)

# =======
# Imports
# =======

import portage
from portage.dep import paren_reduce

from gentoolkit import errors
from gentoolkit.atom import Atom
from gentoolkit.cpv import CPV
from gentoolkit.helpers import uniqify
from gentoolkit.query import Query

# =======
# Classes
# =======

class Dependencies(Query):
	"""Access a package's dependencies and reverse dependencies.

	Example usage:
		>>> from gentoolkit.dependencies import Dependencies
		>>> portage = Dependencies('sys-apps/portage-9999')
		>>> portage
		<Dependencies 'sys-apps/portage-9999'>
		>>> # All methods return gentoolkit.atom.Atom instances
		... portage.get_depend()
		... # doctest: +ELLIPSIS, +NORMALIZE_WHITESPACE
		[<Atom 'python3? =dev-lang/python-3*'>,
		 <Atom '!python3? >=dev-lang/python-2.7'>, ...]

	"""
	def __init__(self, query, parser=None):
		Query.__init__(self, query)
		self.use = []
		self.depatom = str()

		# Allow a custom parser function:
		self.parser = parser if parser else self._parser

	def __eq__(self, other):
		if self.atom != other.atom:
			return False
		else:
			return True

	def __ne__(self, other):
		return not self == other

	def __hash__(self):
		return hash((self.atom, self.depatom, tuple(self.use)))

	def __repr__(self):
		return "<%s %r>" % (self.__class__.__name__, self.atom)

	def environment(self, envvars):
		"""Returns predefined env vars DEPEND, SRC_URI, etc."""

		# Try to use the Portage tree first, since emerge only uses the tree
		# when calculating dependencies
		try:
			result = portage.db[portage.root]["porttree"].dbapi.aux_get(self.cpv, envvars)
		except KeyError:
			try:
				result = portage.db[portage.root]["vartree"].dbapi.aux_get(self.cpv, envvars)
			except KeyError:
				return []
		return result

	def get_depend(self):
		"""Get the contents of DEPEND and parse it with self.parser."""

		try:
			return self.parser(self.environment(('DEPEND',))[0])
		except portage.exception.InvalidPackageName as err:
			raise errors.GentoolkitInvalidCPV(err)

	def get_pdepend(self):
		"""Get the contents of PDEPEND and parse it with self.parser."""

		try:
			return self.parser(self.environment(('PDEPEND',))[0])
		except portage.exception.InvalidPackageName as err:
			raise errors.GentoolkitInvalidCPV(err)

	def get_rdepend(self):
		"""Get the contents of RDEPEND and parse it with self.parser."""

		try:
			return self.parser(self.environment(('RDEPEND',))[0])
		except portage.exception.InvalidPackageName as err:
			raise errors.GentoolkitInvalidCPV(err)

	def get_all_depends(self):
		"""Get the contents of ?DEPEND and parse it with self.parser."""

		env_vars = ('DEPEND', 'PDEPEND', 'RDEPEND')
		try:
			return self.parser(' '.join(self.environment(env_vars)))
		except portage.exception.InvalidPackageName as err:
			raise errors.GentoolkitInvalidCPV(err)

	def graph_depends(
		self,
		max_depth=1,
		printer_fn=None,
		# The rest of these are only used internally:
		depth=1,
		seen=None,
		depcache=None,
		result=None
	):
		"""Graph direct dependencies for self.

		Optionally gather indirect dependencies.

		@type max_depth: int
		@keyword max_depth: Maximum depth to recurse if.
			<1 means no maximum depth
			>0 means recurse only this depth;
		@type printer_fn: callable
		@keyword printer_fn: If None, no effect. If set, it will be applied to
			each result.
		@rtype: list
		@return: [(depth, pkg), ...]
		"""
		if seen is None:
			seen = set()
		if depcache is None:
			depcache = dict()
		if result is None:
			result = list()

		pkgdep = None
		deps = self.get_all_depends()
		for dep in deps:
			if dep.atom in depcache:
				continue
			try:
				pkgdep = depcache[dep.atom]
			except KeyError:
				pkgdep = Query(dep.atom).find_best()
				depcache[dep.atom] = pkgdep
			if not pkgdep:
				continue
			elif pkgdep.cpv in seen:
				continue
			if depth <= max_depth or max_depth == 0:
				if printer_fn is not None:
					printer_fn(depth, pkgdep, dep)
				result.append((depth,pkgdep))

				seen.add(pkgdep.cpv)
				if depth < max_depth or max_depth == 0:
					# result is passed in and added to directly
					# so rdeps is disposable
					rdeps = pkgdep.deps.graph_depends(
							max_depth=max_depth,
							printer_fn=printer_fn,
							# The rest of these are only used internally:
							depth=depth+1,
							seen=seen,
							depcache=depcache,
							result=result
						)
		return result

	def graph_reverse_depends(
		self,
		pkgset=None,
		max_depth=-1,
		only_direct=True,
		printer_fn=None,
		# The rest of these are only used internally:
		depth=0,
		depcache=None,
		seen=None,
		result=None
	):
		"""Graph direct reverse dependencies for self.

		Example usage:
			>>> from gentoolkit.dependencies import Dependencies
			>>> ffmpeg = Dependencies('media-video/ffmpeg-9999')
			>>> # I only care about installed packages that depend on me:
			... from gentoolkit.helpers import get_installed_cpvs
			>>> # I want to pass in a sorted list. We can pass strings or
			... # Package or Atom types, so I'll use Package to sort:
			... from gentoolkit.package import Package
			>>> installed = sorted(get_installed_cpvs())
			>>> deptree = ffmpeg.graph_reverse_depends(
			...     only_direct=False,  # Include indirect revdeps
			...     pkgset=installed)   # from installed pkgset
			>>> len(deptree)
			24

		@type pkgset: iterable
		@keyword pkgset: sorted pkg cpv strings or anything sublassing
			L{gentoolkit.cpv.CPV} to use for calculate our revdep graph.
		@type max_depth: int
		@keyword max_depth: Maximum depth to recurse if only_direct=False.
			-1 means no maximum depth;
			 0 is the same as only_direct=True;
			>0 means recurse only this many times;
		@type only_direct: bool
		@keyword only_direct: to recurse or not to recurse
		@type printer_fn: callable
		@keyword printer_fn: If None, no effect. If set, it will be applied to
			each L{gentoolkit.atom.Atom} object as it is added to the results.
		@rtype: list
		@return: L{gentoolkit.dependencies.Dependencies} objects
		"""
		if not pkgset:
			err = ("%s kwarg 'pkgset' must be set. "
				"Can be list of cpv strings or any 'intersectable' object.")
			raise errors.GentoolkitFatalError(err % (self.__class__.__name__,))

		if depcache is None:
			depcache = dict()
		if seen is None:
			seen = set()
		if result is None:
			result = list()

		if depth == 0:
			pkgset = tuple(Dependencies(x) for x in pkgset)

		pkgdep = None
		for pkgdep in pkgset:
			try:
				all_depends = depcache[pkgdep]
			except KeyError:
				all_depends = uniqify(pkgdep.get_all_depends())
				depcache[pkgdep] = all_depends

			dep_is_displayed = False
			for dep in all_depends:
				# TODO: Add ability to determine if dep is enabled by USE flag.
				#       Check portage.dep.use_reduce
				if dep.intersects(self):
					pkgdep.depth = depth
					pkgdep.matching_dep = dep
					if printer_fn is not None:
						printer_fn(pkgdep, dep_is_displayed=dep_is_displayed)
					result.append(pkgdep)
					dep_is_displayed = True

			# if --indirect specified, call ourselves again with the dep
			# Do not call if we have already called ourselves.
			if (
				dep_is_displayed and not only_direct and
				pkgdep.cpv not in seen and
				(depth < max_depth or max_depth == -1)
			):

				seen.add(pkgdep.cpv)
				result.append(
					pkgdep.graph_reverse_depends(
						pkgset=pkgset,
						max_depth=max_depth,
						only_direct=only_direct,
						printer_fn=printer_fn,
						depth=depth+1,
						depcache=depcache,
						seen=seen,
						result=result
					)
				)

		if depth == 0:
			return result
		return pkgdep

	def _parser(self, deps, use_conditional=None, depth=0):
		"""?DEPEND file parser.

		@rtype: list
		@return: L{gentoolkit.atom.Atom} objects
		"""
		result = []

		if depth == 0:
			deps = paren_reduce(deps)
		for tok in deps:
			if tok == '||':
				continue
			if tok[-1] == '?':
				use_conditional = tok[:-1]
				continue
			if isinstance(tok, list):
				sub_r = self._parser(tok, use_conditional, depth=depth+1)
				result.extend(sub_r)
				use_conditional = None
				continue
			# FIXME: This is a quick fix for bug #299260.
			#        A better fix is to not discard blockers in the parser,
			#        but to check for atom.blocker in whatever equery/depends
			#        (in this case) and ignore them there.
			# TODO: Test to see how much a performance impact ignoring
			#       blockers here rather than checking for atom.blocker has.
			if tok[0] == '!':
				# We're not interested in blockers
				continue
			# skip it if it's empty
			if tok and tok != '':
				atom = Atom(tok)
				if use_conditional is not None:
					atom.use_conditional = use_conditional
				result.append(atom)
			else:
				message = "dependencies.py: _parser() found an empty " +\
					"dep string token for: %s, deps= %s"
				raise errors.GentoolkitInvalidAtom(message %(self.cpv, deps))

		return result

# vim: set ts=4 sw=4 tw=0:
