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
	>>> portage = Package('sys-apps/portage-9999')
	>>> portage.ebuild_path()
	'/usr/portage/sys-apps/portage/portage-9999.ebuild'
	>>> portage.is_masked()
	True
	>>> portage.is_installed()
	False
"""

__all__ = (
	'Package',
	'PackageFormatter',
	'FORMAT_TMPL_VARS'
)

# =======
# Globals
# =======

FORMAT_TMPL_VARS = (
	'$location', '$mask', '$mask2', '$cp', '$cpv', '$category', '$name',
	'$version', '$revision', '$fullversion', '$slot', '$repo', '$keywords'
)

# =======
# Imports
# =======

import os
from string import Template

import portage
from portage.util import LazyItemsDict

import gentoolkit.pprinter as pp
from gentoolkit import errors
from gentoolkit.cpv import CPV
from gentoolkit.keyword import determine_keyword
from gentoolkit.flag import get_flags
from gentoolkit.eprefix import EPREFIX

# =======
# Settings
# =======

def _NewPortageConfig(local_config):
	ret = portage.config(local_config=local_config,
			eprefix=EPREFIX if EPREFIX else None,
			config_root=os.environ.get('PORTAGE_CONFIGROOT', None),
			target_root=os.environ.get('ROOT', None))
	ret.lock()
	return ret
default_settings = _NewPortageConfig(local_config=True)
nolocal_settings = _NewPortageConfig(local_config=False)

# =======
# Classes
# =======

class Package(CPV):
	"""Exposes the state of a given CPV."""

	def __init__(self, cpv, validate=False, local_config=True):
		if isinstance(cpv, CPV):
			self.__dict__.update(cpv.__dict__)
		else:
			CPV.__init__(self, cpv, validate=validate)

		if validate and not all(
			hasattr(self, x) for x in ('category', 'version')
		):
			# CPV allows some things that Package must not
			raise errors.GentoolkitInvalidPackage(self.cpv)

		if local_config:
			self._settings = default_settings
		else:
			self._settings = nolocal_settings

		# Set dynamically
		self._package_path = None
		self._dblink = None
		self._metadata = None
		self._deps = None
		self._portdir_path = None

	def __repr__(self):
		return "<%s %r>" % (self.__class__.__name__, self.cpv)

	def __hash__(self):
		return hash(self.cpv)

	def __contains__(self, key):
		return key in self.cpv

	def __str__(self):
		return str(self.cpv)

	@property
	def metadata(self):
		"""Instantiate a L{gentoolkit.metadata.MetaData} object here."""

		from gentoolkit.metadata import MetaData

		if self._metadata is None:
			metadata_path = os.path.join(
				self.package_path(), 'metadata.xml'
			)
			try:
				self._metadata = MetaData(metadata_path)
			except IOError as error:
				import errno
				if error.errno != errno.ENOENT:
					raise
				return None

		return self._metadata

	@property
	def dblink(self):
		"""Instantiate a L{portage.dbapi.vartree.dblink} object here."""

		if self._dblink is None:
			self._dblink = portage.dblink(
				self.category,
				"%s-%s" % (self.name, self.fullversion),
				self._settings["ROOT"],
				self._settings
			)

		return self._dblink

	@property
	def deps(self):
		"""Instantiate a L{gentoolkit.dependencies.Dependencies} object here."""

		from gentoolkit.dependencies import Dependencies

		if self._deps is None:
			self._deps = Dependencies(self.cpv)

		return self._deps

	def environment(self, envvars, prefer_vdb=True, fallback=True):
		"""Returns one or more of the predefined environment variables.

		Some available envvars are:
		----------------------
			BINPKGMD5  COUNTER         FEATURES   LICENSE  SRC_URI
			CATEGORY   CXXFLAGS        HOMEPAGE   PDEPEND  USE
			CBUILD     DEFINED_PHASES  INHERITED  PF
			CFLAGS     DEPEND          IUSE       PROVIDE
			CHOST      DESCRIPTION     KEYWORDS   RDEPEND
			CONTENTS   EAPI            LDFLAGS    SLOT

		Example usage:
			>>> pkg = Package('sys-apps/portage-9999')
			>>> pkg.environment('USE')
			''
			>>> pkg.environment(('USE', 'IUSE'))
			... # doctest: +NORMALIZE_WHITESPACE
			['', 'build doc epydoc +ipc pypy1_9 python2 python3
			 selinux xattr']

		@type envvars: str or array
		@param envvars: one or more of (DEPEND, SRC_URI, etc.)
		@type prefer_vdb: bool
		@keyword prefer_vdb: if True, look in the vardb before portdb, else
			reverse order. Specifically KEYWORDS will get more recent
			information by preferring portdb.
		@type fallback: bool
		@keyword fallback: query only the preferred db if False
		@rtype: str or list
		@return: str if envvars is str, list if envvars is array
		@raise KeyError: if key is not found in requested db(s)
		"""

		got_string = False
		if isinstance(envvars, str):
			got_string = True
			envvars = (envvars,)
		if prefer_vdb:
			try:
				result = portage.db[portage.root][
					'vartree'].dbapi.aux_get(
					self.cpv, envvars)
			except KeyError:
				try:
					if not fallback:
						raise KeyError
					result = portage.db[portage.root][
						'porttree'].dbapi.aux_get(
						self.cpv, envvars)
				except KeyError:
					raise errors.GentoolkitFatalError(
						'aux_get returned unexpected '
						'results')
		else:
			try:
				result = portage.db[portage.root][
					'porttree'].dbapi.aux_get(
					self.cpv, envvars)
			except KeyError:
				try:
					if not fallback:
						raise KeyError
					result = portage.db[portage.root][
						'vartree'].dbapi.aux_get(
						self.cpv, envvars)
				except KeyError:
					raise errors.GentoolkitFatalError(
						'aux_get returned unexpected '
						'results')

		if got_string:
			return result[0]
		return result

	def exists(self):
		"""Return True if package exists in the Portage tree, else False"""

		return bool(portage.db[portage.root]["porttree"].dbapi.cpv_exists(self.cpv))

	def settings(self, key):
		"""Returns the value of the given key for this package (useful
		for package.* files."""

		if self._settings.locked:
			self._settings.unlock()
		try:
			result = self._settings[key]
		finally:
			self._settings.lock()
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

		if self._settings.locked:
			self._settings.unlock()
		try:
			result = portage.getmaskingstatus(self.cpv,
				settings=self._settings,
				portdb=portage.db[portage.root]["porttree"].dbapi)
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
			result = portage.getmaskingreason(self.cpv,
				settings=self._settings,
				portdb=portage.db[portage.root]["porttree"].dbapi,
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
			>>> pkg = Package('sys-apps/portage-9999')
			>>> pkg.ebuild_path()
			'/usr/portage/sys-apps/portage/portage-9999.ebuild'
			>>> pkg.ebuild_path(in_vartree=True)
			'/var/db/pkg/sys-apps/portage-9999/portage-9999.ebuild'
		"""

		if in_vartree:
			return portage.db[portage.root]["vartree"].dbapi.findname(self.cpv)
		return portage.db[portage.root]["porttree"].dbapi.findname(self.cpv)

	def package_path(self, in_vartree=False):
		"""Return the path to where the ebuilds and other files reside."""

		if in_vartree:
			return self.dblink.getpath()
		return os.sep.join(self.ebuild_path().split(os.sep)[:-1])

	def repo_name(self, fallback=True):
		"""Determine the repository name.

		@type fallback: bool
		@param fallback: if the repo_name file does not exist, return the
			repository name from the path
		@rtype: str
		@return: output of the repository metadata file, which stores the
			repo_name variable, or try to get the name of the repo from
			the path.
		@raise GentoolkitFatalError: if fallback is False and repo_name is
			not specified by the repository.
		"""

		try:
			return self.environment('repository')
		except errors.GentoolkitFatalError:
			if fallback:
				return self.package_path().split(os.sep)[-3]
			raise

	def use(self):
		"""Returns the USE flags active at time of installation."""

		return self.dblink.getstring("USE")

	def use_status(self):
		"""Returns the USE flags active for installation."""

		iuse, final_flags = get_flags(self.cpv, final_setting=True)
		return final_flags

	def parsed_contents(self, prefix_root=False):
		"""Returns the parsed CONTENTS file.

		@rtype: dict
		@return: {'/full/path/to/obj': ['type', 'timestamp', 'md5sum'], ...}
		"""

		contents = self.dblink.getcontents()

		# Portage will automatically prepend ROOT.  Undo that.
		if not prefix_root:
			myroot = self._settings["ROOT"]
			if myroot != '/':
				ret = {}
				for key, val in self.dblink.getcontents().iteritems():
					ret['/' + os.path.relpath(key, myroot)] = val
				contents = ret

		return contents

	def size(self):
		"""Estimates the installed size of the contents of this package.

		@rtype: tuple
		@return: (size, number of files in total, number of uncounted files)
		"""

		seen = set()
		size = n_files = n_uncounted = 0
		for path in self.parsed_contents(prefix_root=True):
			try:
				st = os.lstat(path)
			except OSError:
				continue

			# Remove hardlinks by checking for duplicate inodes. Bug #301026.
			file_inode = st.st_ino
			if file_inode in seen:
				continue
			seen.add(file_inode)

			try:
				size += st.st_size
				n_files += 1
			except OSError:
				n_uncounted += 1

		return (size, n_files, n_uncounted)

	def is_installed(self):
		"""Returns True if this package is installed (merged)."""

		return self.dblink.exists()

	def is_overlay(self):
		"""Returns True if the package is in an overlay."""

		ebuild, tree = portage.db[portage.root]["porttree"].dbapi.findname2(self.cpv)
		if not ebuild:
			return None
		if self._portdir_path is None:
			self._portdir_path = os.path.realpath(self._settings["PORTDIR"])
		return (tree and tree != self._portdir_path)

	def is_masked(self):
		"""Returns True if this package is masked against installation.

		@note: We blindly assume that the package actually exists on disk.
		"""

		unmasked = portage.db[portage.root]['porttree'].dbapi.xmatch(
			'match-visible', self.cpv)
		return self.cpv not in unmasked


class PackageFormatter(object):
	"""When applied to a L{gentoolkit.package.Package} object, determine the
	location (Portage Tree vs. overlay), install status and masked status. That
	information can then be easily formatted and displayed.

	Example usage:
		>>> from gentoolkit.query import Query
		>>> from gentoolkit.package import PackageFormatter
		>>> import portage.output
		>>> q = Query('gcc')
		>>> pkgs = [PackageFormatter(x) for x in q.find()]
		>>> havecolor = portage.output.havecolor
		>>> portage.output.havecolor = False
		>>> for pkg in pkgs:
		...     # Only print packages that are installed and from the Portage
		...     # tree
		...     if set('IP').issubset(pkg.location):
		...             print(pkg)
		...
		[IP-] [  ] sys-devel/gcc-4.5.4:4.5
		>>> portage.output.havecolor = havecolor

	@type pkg: L{gentoolkit.package.Package}
	@param pkg: package to format
	@type do_format: bool
	@param do_format: Whether to format the package name or not.
		Essentially C{do_format} should be set to False when piping or when
		quiet output is desired. If C{do_format} is False, only the location
		attribute will be created to save time.
	"""

	_tmpl_verbose = "[$location] [$mask] $cpv:$slot"
	_tmpl_quiet = "$cpv"

	def __init__(self, pkg, do_format=True, custom_format=None):
		self._pkg = None
		self._do_format = do_format
		self._str = None
		self._location = None
		if not custom_format:
			if do_format:
				custom_format = self._tmpl_verbose
			else:
				custom_format = self._tmpl_quiet
		self.tmpl = Template(custom_format)
		self.format_vars = LazyItemsDict()
		self.pkg = pkg

	def __repr__(self):
		return "<%s %s @%#8x>" % (self.__class__.__name__, self.pkg, id(self))

	def __str__(self):
		if self._str is None:
			self._str = self.tmpl.safe_substitute(self.format_vars)
		return self._str

	@property
	def location(self):
		if self._location is None:
			self._location = self.format_package_location()
		return self._location

	@property
	def pkg(self):
		"""Package to format"""
		return self._pkg

	@pkg.setter
	def pkg(self, value):
		if self._pkg == value:
			return
		self._pkg = value
		self._location = None

		fmt_vars = self.format_vars
		self.format_vars.clear()
		fmt_vars.addLazySingleton("location",
			lambda: getattr(self, "location"))
		fmt_vars.addLazySingleton("mask", self.format_mask)
		fmt_vars.addLazySingleton("mask2", self.format_mask_status2)
		fmt_vars.addLazySingleton("cpv", self.format_cpv)
		fmt_vars.addLazySingleton("cp", self.format_cpv, "cp")
		fmt_vars.addLazySingleton("category", self.format_cpv, "category")
		fmt_vars.addLazySingleton("name", self.format_cpv, "name")
		fmt_vars.addLazySingleton("version", self.format_cpv, "version")
		fmt_vars.addLazySingleton("revision", self.format_cpv, "revision")
		fmt_vars.addLazySingleton("fullversion", self.format_cpv,
			"fullversion")
		fmt_vars.addLazySingleton("slot", self.format_slot)
		fmt_vars.addLazySingleton("repo", self.pkg.repo_name)
		fmt_vars.addLazySingleton("keywords", self.format_keywords)

	def format_package_location(self):
		"""Get the install status (in /var/db/?) and origin (from an overlay
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
			["  ", " ~", " -", "M ", "M~", "M-", "??"]
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

	def format_mask_status2(self):
		"""Get the mask status of a given package.
		"""
		mask = self.pkg.mask_status()
		if mask:
			return pp.masking(mask)
		else:
			arch = self.pkg.settings("ARCH")
			keywords = self.pkg.environment('KEYWORDS')
			mask =  [determine_keyword(arch,
				portage.settings["ACCEPT_KEYWORDS"],
				keywords)]
		return pp.masking(mask)

	def format_mask(self):
		maskmodes = ['  ', ' ~', ' -', 'M ', 'M~', 'M-', '??']
		maskmode = maskmodes[self.format_mask_status()[0]]
		return pp.keyword(
			maskmode,
			stable=not maskmode.strip(),
			hard_masked=set(('M', '?', '-')).intersection(maskmode)
		)

	def format_cpv(self, attr=None):
		if attr is None:
			value = self.pkg.cpv
		else:
			value = getattr(self.pkg, attr)
		if self._do_format:
			return pp.cpv(value)
		else:
			return value

	def format_slot(self):
		value = self.pkg.environment("SLOT")
		if self._do_format:
			return pp.slot(value)
		else:
			return value

	def format_keywords(self):
		value = self.pkg.environment("KEYWORDS")
		if self._do_format:
			return pp.keyword(value)
		else:
			return value


# vim: set ts=4 sw=4 tw=79:
