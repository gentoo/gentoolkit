#!/usr/bin/python
#
# Copyright(c) 2004, Karl Trygve Kalleberg <karltk@gentoo.org>
# Copyright(c) 2004-2010, Gentoo Foundation
#
# Licensed under the GNU General Public License, v2
#
# $Header$

"""Provides an interface to package information stored by package managers.

The Package class is the heart of much of Gentoolkit. Given a CPV
(category/package-version) string, it can reveal the package's status in the
tree and VARDB (/var/db/), provide rich comparison and sorting, and expose
important parts of Portage's back-end.

Example usage:
	>>> portage = Package('sys-apps/portage-2.1.6.13')
	>>> portage.ebuild_path()
	'/usr/portage/sys-apps/portage/portage-2.1.6.13.ebuild'
	>>> portage.is_masked()
	False
	>>> portage.is_installed()
	True
"""

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
	"""Exposes the state of a given CPV."""

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

	@property
	def metadata(self):
		"""Instantiate a L{gentoolkit.metadata.MetaData} object here."""

		if self._metadata is None:
			metadata_path = os.path.join(
				self.package_path(), 'metadata.xml'
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

	def environment(self, envvars, prefer_vdb=True, no_fallback=False):
		"""Returns one or more of the predefined environment variables.

		Available envvars are:
		----------------------
			BINPKGMD5  COUNTER         FEATURES   LICENSE  SRC_URI
			CATEGORY   CXXFLAGS        HOMEPAGE   PDEPEND  USE
			CBUILD     DEFINED_PHASES  INHERITED  PF
			CFLAGS     DEPEND          IUSE       PROVIDE
			CHOST      DESCRIPTION     KEYWORDS   RDEPEND
			CONTENTS   EAPI            LDFLAGS    SLOT

		Example usage:
			>>> pkg = Package('sys-apps/portage-2.1.6.13')
			>>> pkg.environment('USE')
			'elibc_glibc kernel_linux userland_GNU x86'
			>>> pkg.environment(('USE', 'IUSE'))
			['elibc_glibc kernel_linux userland_GNU x86',
				'build doc epydoc selinux linguas_pl']

		@type envvars: str or array
		@param envvars: one or more of (DEPEND, SRC_URI, etc.)
		@type prefer_vdb: bool
		@keyword prefer_vdb: if True, look in the vardb before portdb, else
			reverse order. Specifically KEYWORDS will get more recent
			information by preferring portdb.
		@type no_fallback: bool
		@keyword no_fallback: query only the preferred db
		@rtype: str or list
		@return: str if envvars is str, list if envvars is array
		@raise KeyError: if key is not found in requested db(s)
		"""

		got_string = False
		if isinstance(envvars, basestring):
			got_string = True
			envvars = (envvars,)
		if prefer_vdb:
			try:
				result = VARDB.aux_get(str(self.cpv), envvars)
			except KeyError:
				try:
					if no_fallback:
						raise KeyError
					result = PORTDB.aux_get(str(self.cpv), envvars)
				except KeyError:
					err = "aux_get returned unexpected results"
					raise errors.GentoolkitFatalError(err)
		else:
			try:
				result = PORTDB.aux_get(str(self.cpv), envvars)
			except KeyError:
				try:
					if no_fallback:
						raise KeyError
					result = VARDB.aux_get(str(self.cpv), envvars)
				except KeyError:
					err = "aux_get returned unexpected results"
					raise errors.GentoolkitFatalError(err)

		if got_string:
			return result[0]
		return result

	def exists(self):
		"""Return True if package exists in the Portage tree, else False"""

		return bool(PORTDB.cpv_exists(str(self.cpv)))

	@staticmethod
	def settings(key):
		"""Returns the value of the given key for this package (useful
		for package.* files."""

		if settings.locked:
			settings.unlock()
		try:
			result = settings[key]
		finally:
			settings.lock()
		return result

	def mask_status(self):
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

	def mask_reason(self):
		"""Shortcut to L{portage.getmaskingreason}.

		@rtype: None or tuple
		@return: empty tuple if pkg not masked OR
			('mask reason', 'mask location')
		"""

		try:
			result = portage.getmaskingreason(str(self.cpv),
				settings=settings,
				portdb=PORTDB,
				return_location=True)
			if result is None:
				result = tuple()
		except KeyError:
			# getmaskingstatus doesn't support packages without ebuilds in the
			# Portage tree.
			result = None

		return result

	def ebuild_path(self, in_vartree=False):
		"""Returns the complete path to the .ebuild file.

		Example usage:
			>>> pkg.ebuild_path()
			'/usr/portage/sys-apps/portage/portage-2.1.6.13.ebuild'
			>>> pkg.ebuild_path(in_vartree=True)
			'/var/db/pkg/sys-apps/portage-2.1.6.13/portage-2.1.6.13.ebuild'
		"""

		if in_vartree:
			return VARDB.findname(str(self.cpv))
		return PORTDB.findname(str(self.cpv))

	def package_path(self, in_vartree=False):
		"""Return the path to where the ebuilds and other files reside."""

		if in_vartree:
			return self.dblink.getpath()
		return os.sep.join(self.ebuild_path().split(os.sep)[:-1])

	def repo_id(self):
		"""Using the package path, determine the repository id.

		@rtype: str
		@return: /usr/<THIS>portage</THIS>/category/name/
		"""

		return self.package_path().split(os.sep)[-3]

	def use(self):
		"""Returns the USE flags active at time of installation."""

		return self.dblink.getstring("USE")

	def parsed_contents(self):
		"""Returns the parsed CONTENTS file.

		@rtype: dict
		@return: {'/full/path/to/obj': ['type', 'timestamp', 'md5sum'], ...}
		"""

		return self.dblink.getcontents()

	def size(self):
		"""Estimates the installed size of the contents of this package.

		@rtype: tuple
		@return: (size, number of files in total, number of uncounted files)
		"""

		contents = self.parsed_contents()
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

		return self.dblink.exists()

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
			maskmode = maskmodes[self.format_mask_status()[0]]
			return "[%(location)s] [%(mask)s] %(package)s:%(slot)s" % {
				'location': self.location,
				'mask': pp.keyword(
					maskmode,
					stable=not maskmode.strip(),
					hard_masked=set(('M', 'X', '-')).intersection(maskmode)
				),
				'package': pp.cpv(str(self.pkg.cpv)),
				'slot': pp.slot(self.pkg.environment("SLOT"))
			}
		else:
			return str(self.pkg.cpv)

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
		masking_status = self.pkg.mask_status()
		if masking_status is None:
			return (6, [])

		if ("~%s keyword" % self.pkg.settings("ARCH")) in masking_status:
			result += 1
		if "missing keyword" in masking_status:
			result += 2
		if set(('profile', 'package.mask')).intersection(masking_status):
			result += 3

		return (result, masking_status)


# vim: set ts=4 sw=4 tw=79:
