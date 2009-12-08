#!/usr/bin/python
#
# Copyright(c) 2004, Karl Trygve Kalleberg <karltk@gentoo.org>
# Copyright(c) 2004-2009, Gentoo Foundation
#
# Licensed under the GNU General Public License, v2
#
# $Header$

"""Provides classes for accessing Portage db information for a given package."""

__all__ = (
	'Package',
	'PackageFormatter'
)

# =======
# Imports
# =======

import os

import portage
from portage import settings

import gentoolkit.pprinter as pp
from gentoolkit import errors
from gentoolkit.cpv import CPV
from gentoolkit.dbapi import PORTDB, VARDB
from gentoolkit.dependencies import Dependencies
from gentoolkit.metadata import MetaData

# =======
# Classes
# =======

class Package(CPV):
	"""Provides methods for ascertaining the state of a given CPV."""

	def __init__(self, cpv):
		if isinstance(cpv, CPV):
			self.cpv = cpv
		else:
			self.cpv = CPV(cpv)
		del cpv

		if not all(getattr(self.cpv, x) for x in ('category', 'version')):
			# CPV allows some things that Package must not
			raise errors.GentoolkitInvalidPackage(str(self.cpv))

		# Set dynamically
		self._package_path = None
		self._dblink = None
		self._metadata = None
		self._deps = None
		self._portdir_path = None

	def __repr__(self):
		return "<%s %r>" % (self.__class__.__name__, str(self.cpv))

	def __eq__(self, other):
		if not hasattr(other, 'cpv'):
			return False
		return self.cpv == other.cpv

	def __ne__(self, other):
		return not self == other

	def __lt__(self, other):
		return self.cpv < other.cpv

	def __gt__(self, other):
		return self.cpv > other.cpv

	def __hash__(self):
		return hash(str(self.cpv))

	def __contains__(self, key):
		return key in str(self.cpv)

	def __str__(self):
		return str(self.cpv)

	def _get_trees(self):
		"""Return dbapi objects for each repository that contains self."""

		result = []
		if self.is_installed():
			result.append(VARDB)
		if self.exists():
			result.append(PORTDB)
		if not result:
			raise errors.GentoolkitFatalError("Could not find package tree")

		return result

	@property
	def metadata(self):
		"""Instantiate a L{gentoolkit.metadata.MetaData} object here."""

		if self._metadata is None:
			metadata_path = os.path.join(
				self.get_package_path(), 'metadata.xml'
			)
			self._metadata = MetaData(metadata_path)

		return self._metadata

	@property
	def dblink(self):
		"""Instantiate a L{portage.dbapi.vartree.dblink} object here."""

		if self._dblink is None:
			self._dblink = portage.dblink(
				self.cpv.category,
				"%s-%s" % (self.cpv.name, self.cpv.fullversion),
				settings["ROOT"],
				settings
			)

		return self._dblink

	@property
	def deps(self):
		"""Instantiate a L{gentoolkit.dependencies.Dependencies} object here."""

		if self._deps is None:
			self._deps = Dependencies(self.cpv)

		return self._deps

	def exists(self):
		"""Return True if package exists in the Portage tree, else False"""

		return bool(PORTDB.cpv_exists(str(self.cpv)))

	@staticmethod
	def get_settings(key):
		"""Returns the value of the given key for this package (useful
		for package.* files."""

		if settings.locked:
			settings.unlock()
		try:
			result = settings[key]
		finally:
			settings.lock()
		return result

	def get_mask_status(self):
		"""Shortcut to L{portage.getmaskingstatus}.

		@rtype: None or list
		@return: a list containing none or some of:
			'profile'
			'package.mask'
			license(s)
			"kmask" keyword
			'missing keyword'
		"""

		if settings.locked:
			settings.unlock()
		try:
			result = portage.getmaskingstatus(str(self.cpv),
				settings=settings,
				portdb=PORTDB)
		except KeyError:
			# getmaskingstatus doesn't support packages without ebuilds in the
			# Portage tree.
			result = None

		return result

	def get_mask_reason(self):
		"""Shortcut to L{portage.getmaskingreason}.

		@rtype: None or tuple
		@return: empty tuple if pkg not masked OR
			('mask reason', 'mask location')
		"""

		try:
			result = portage.getmaskingreason(str(self.cpv),
				settings=settings,
				PORTDB=PORTDB,
				return_location=True)
			if result is None:
				result = tuple()
		except KeyError:
			# getmaskingstatus doesn't support packages without ebuilds in the
			# Portage tree.
			result = None

		return result

	def get_provide(self):
		"""Return a list of provides, if any"""

		if self.is_installed():
			result = VARDB.get_provide(str(self.cpv))
		else:
			try:
				result = [self.get_env_var('PROVIDE')]
			except KeyError:
				result = []
		return result

	def get_ebuild_path(self, in_vartree=False):
		"""Returns the complete path to the .ebuild file.

		Example usage:
			>>> pkg.get_ebuild_path()
			'/usr/portage/sys-apps/portage/portage-2.1.6.13.ebuild'
			>>> pkg.get_ebuild_path(in_vartree=True)
			'/var/db/pkg/sys-apps/portage-2.1.6.13/portage-2.1.6.13.ebuild'
		"""

		if in_vartree:
			return VARDB.findname(str(self.cpv))
		return PORTDB.findname(str(self.cpv))

	def get_package_path(self):
		"""Return the path to where the ebuilds and other files reside."""

		if self._package_path is None:
			path_split = self.get_ebuild_path().split(os.sep)
			self._package_path = os.sep.join(path_split[:-1])

		return self._package_path

	def get_repo_name(self):
		"""Using the package path, determine the repo name.

		@rtype: str
		@return: /usr/<THIS>portage</THIS>/cat-egory/name/
		"""

		return self.get_package_path().split(os.sep)[-3]

	def get_env_var(self, var, tree=None):
		"""Returns one of the predefined env vars DEPEND, SRC_URI, etc."""

		if tree is None:
			tree = self._get_trees()[0]
		try:
			result = tree.aux_get(str(self.cpv), [var])
			if len(result) != 1:
				raise errors.GentoolkitFatalError
		except (KeyError, errors.GentoolkitFatalError):
			err = "aux_get returned unexpected results"
			raise errors.GentoolkitFatalError(err)
		return result[0]

	def get_use_flags(self):
		"""Returns the USE flags active at time of installation."""

		return self.dblink.getstring("USE")

	def get_contents(self):
		"""Returns the parsed CONTENTS file.

		@rtype: dict
		@return: {'/full/path/to/obj': ['type', 'timestamp', 'md5sum'], ...}
		"""

		return self.dblink.getcontents()

	def get_size(self):
		"""Estimates the installed size of the contents of this package.

		@rtype: tuple
		@return: (size, number of files in total, number of uncounted files)
		"""

		contents = self.get_contents()
		size = n_uncounted = n_files = 0
		for cfile in contents:
			try:
				size += os.lstat(cfile).st_size
				n_files += 1
			except OSError:
				n_uncounted += 1
		return (size, n_files, n_uncounted)

	def is_installed(self):
		"""Returns True if this package is installed (merged)"""

		return VARDB.cpv_exists(str(self.cpv))

	def is_overlay(self):
		"""Returns True if the package is in an overlay."""

		ebuild, tree = PORTDB.findname2(str(self.cpv))
		if not ebuild:
			return None
		if self._portdir_path is None:
			self._portdir_path = os.path.realpath(settings["PORTDIR"])
		return (tree and tree != self._portdir_path)

	def is_masked(self):
		"""Returns true if this package is masked against installation.
		Note: We blindly assume that the package actually exists on disk
		somewhere."""

		unmasked = PORTDB.xmatch("match-visible", str(self.cpv))
		return str(self.cpv) not in unmasked


class PackageFormatter(object):
	"""When applied to a L{gentoolkit.package.Package} object, determine the
	location (Portage Tree vs. overlay), install status and masked status. That
	information can then be easily formatted and displayed.

	Example usage:
		>>> from gentoolkit.helpers import find_packages
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
		quiet output is desired. If C{do_format} is False, only the location
		attribute will be created to save time.
	"""

	def __init__(self, pkg, do_format=True):
		self.pkg = pkg
		self.do_format = do_format
		self.location = self.format_package_location() or ''

	def __repr__(self):
		return "<%s %s @%#8x>" % (self.__class__.__name__, self.pkg, id(self))

	def __str__(self):
		if self.do_format:
			maskmodes = ['  ', ' ~', ' -', 'M ', 'M~', 'M-', 'XX']
			return "[%(location)s] [%(mask)s] %(package)s (%(slot)s)" % {
				'location': self.location,
				'mask': pp.maskflag(maskmodes[self.format_mask_status()[0]]),
				'package': pp.cpv(str(self.pkg.cpv)),
				'slot': self.pkg.get_env_var("SLOT")
			}
		else:
			return self.pkg.cpv

	def format_package_location(self):
		"""Get the install status (in /var/db/?) and origin (from and overlay
		and the Portage tree?).

		@rtype: str
		@return: one of:
			'I--' : Installed but ebuild doesn't exist on system anymore
			'-P-' : Not installed and from the Portage tree
			'--O' : Not installed and from an overlay
			'IP-' : Installed and from the Portage tree
			'I-O' : Installed and from an overlay
		"""

		result = ['-', '-', '-']

		if self.pkg.is_installed():
			result[0] = 'I'

		overlay = self.pkg.is_overlay()
		if overlay is None:
			pass
		elif overlay:
			result[2] = 'O'
		else:
			result[1] = 'P'

		return ''.join(result)

	def format_mask_status(self):
		"""Get the mask status of a given package.

		@rtype: tuple: (int, list)
		@return: int = an index for this list:
			["  ", " ~", " -", "M ", "M~", "M-", "XX"]
			0 = not masked
			1 = keyword masked
			2 = arch masked
			3 = hard masked
			4 = hard and keyword masked,
			5 = hard and arch masked
			6 = ebuild doesn't exist on system anymore

			list = original output of portage.getmaskingstatus
		"""

		result = 0
		masking_status = self.pkg.get_mask_status()
		if masking_status is None:
			return (6, [])

		if ("~%s keyword" % self.pkg.get_settings("ARCH")) in masking_status:
			result += 1
		if "missing keyword" in masking_status:
			result += 2
		if set(('profile', 'package.mask')).intersection(masking_status):
			result += 3

		return (result, masking_status)


# vim: set ts=4 sw=4 tw=79:
