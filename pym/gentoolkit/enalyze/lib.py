#!/usr/bin/python
#
# Copyright 2010 Brian Dolbec <brian.dolbec@gmail.com>
# Copyright(c) 2010, Gentoo Foundation
# Distributed under the terms of the GNU General Public License v2
#


"""Provides support functions to enalyze modules"""

import sys

from gentoolkit import errors
from gentoolkit.keyword import reduce_keywords
from gentoolkit.flag import (reduce_flags, get_flags, get_all_cpv_use,
	filter_flags, get_installed_use, get_iuse, defaulted_flags)
#from gentoolkit.package import Package

import portage


class FlagAnalyzer(object):
	"""Specialty functions for analysing an installed package's
	USE flags.  Can be used for single or mulitple use without
	needing to be reset unless the system USE flags are changed.

	@type system: list or set
	@param system: the default system USE flags.
	@type _get_flags: function
	@param _get_flags: Normally defaulted, can be overriden for testing
	@type _get_used: function
	@param _get_used: Normally defaulted, can be overriden for testing
		"""
	def __init__(self,
		system,
		filter_defaults=False,
		target="USE",
		_get_flags=get_flags,
		_get_used=get_installed_use
	):
		self.get_flags = _get_flags
		self.get_used = _get_used
		self.filter_defaults = filter_defaults
		self.target = target
		self.reset(system)

	def reset(self, system):
		"""Resets the internal system USE flags and use_expand variables
		to the new setting. The use_expand variable is handled internally.

		@type system: list or set
		@param system: the default system USE flags.
		"""
		self.system = set(system)
		self.use_expand = portage.settings['USE_EXPAND'].lower().split()

	def analyse_cpv(self, cpv):
		"""Gets all relavent USE flag info for a cpv and breaks them down
		into 3 sets, plus (package.use enabled), minus ( package.use disabled),
		unset.

		@param cpv: string. 'cat/pkg-ver'
		@rtype tuple of sets
		@return (plus, minus, unset) sets of USE flags
		"""
		installed = set(self.get_used(cpv, self.target))
		_iuse = self.get_flags(cpv)
		iuse =  set(reduce_flags(_iuse))
		iuse_defaults = defaulted_flags(_iuse)
		return self._analyse(installed, iuse, iuse_defaults)

	def _analyse(self, installed, iuse, iuse_defaults):
		"""Analyzes the supplied info and returns the flag settings
		that differ from the defaults

		@type installed: set
		@param installed: the installed with use flags
		@type iuse: set
		@param iuse: the current ebuilds IUSE
		"""
		defaults = self.system.intersection(iuse)
		# update defaults with iuse_defaults
		defaults.update(iuse_defaults['+'])
		defaults = defaults.difference(iuse_defaults['-'])
		usedflags = iuse.intersection(set(installed))
		if self.filter_defaults:
			plus = usedflags.difference(defaults)
		else:
			plus = usedflags
		minus = defaults.difference(usedflags)
		unset = iuse.difference(defaults, plus, minus)
		cleaned_unset = self.remove_expanding(unset)
		return (plus, minus, cleaned_unset)

	def analyse_pkg(self, pkg):
		"""Gets all relevent USE flag info for a pkg and breaks them down
		into 3 sets, plus (package.use enabled), minus ( package.use disabled),
		unset.

		@param pkg: gentoolkit.package.Package object
		@rtype tuple of sets
		@return (plus, minus, unset) sets of USE flags
		"""
		installed = set(self.pkg_used(pkg))
		#print("installed =", installed)
		_iuse =  self.pkg_flags(pkg)
		iuse =  set(reduce_flags(_iuse))
		iuse_defaults = defaulted_flags(_iuse)
		#print("iuse =", iuse)
		return self._analyse(installed, iuse, iuse_defaults)

	def pkg_used(self, pkg):
		if self.target == "USE":
			return pkg.use().split()
		return pkg.environment(self.target).split()

	def pkg_flags(self, pkg):
		final_use, use_expand_hidden, usemasked, useforced = \
			get_all_cpv_use(pkg.cpv)
		flags = pkg.environment("IUSE", prefer_vdb=False).split()
		return filter_flags(flags, use_expand_hidden, usemasked, useforced)

	def redundant(self, cpv, iuse):
		"""Checks for redundant settings.
		future function. Not yet implemented.
		"""
		pass

	def remove_expanding(self, flags):
		"""Remove unwanted USE_EXPAND flags
		from unset IUSE sets

		@param flags: short list or set of USE flags
		@rtype set
		@return USE flags
		"""
		_flags = set(flags)
		for expander in self.use_expand:
			for flag in flags:
				if expander in flag:
					_flags.remove(flag)
			if not _flags:
				break
		return _flags


class KeywordAnalyser(object):
	"""Specialty functions for analysing the installed package db for
	keyword useage and the packages that used them.

	Note: should be initialized with the internal set_order() before use.
	See internal set_order() for more details.
	This class of functions can be used for single cpv checks or
	used repeatedly for an entire package db.

	@type  arch: string
	@param arch: the system ARCH setting
	@type  accept_keywords: list
	@param accept_keywords: eg. ['x86', '~x86']
	@type  get_aux: function, defaults to: portage.db[portage.root]["vartree"].dbapi.aux_get
	@param vardb: vardb class of functions, needed=aux_get()
		to return => KEYWORDS & USE flags for a cpv
		= aux_get(cpv, ["KEYWORDS", "USE"])
	"""

	# parsing order to determine appropriate keyword used for installation
	normal_order = ['stable', 'testing', 'prefix', 'testing_prefix', 'missing']
	prefix_order = ['prefix', 'testing_prefix', 'stable', 'testing', 'missing']
	parse_range = list(range(len(normal_order)))


	def __init__(self, arch, accept_keywords, vardb=portage.db[portage.root]["vartree"].dbapi):
		self.arch = arch
		self.accept_keywords = accept_keywords
		self.vardb = vardb
		self.prefix = ''
		self.parse_order = None
		self.check_key = {
			'stable': self._stable,
			'testing': self._testing,
			'prefix': self._prefix,
			'testing_prefix': self._testing_prefix,
			'missing': self._missing
			}
		self.mismatched = []

	def determine_keyword(self, keywords, used, cpv):
		"""Determine the keyword from the installed USE flags and
		the KEYWORDS that was used to install a package.

		@param keywords: list of keywords available to install a pkg
		@param used: list of USE flalgs recorded for the installed pkg
		@rtype: string
		@return a keyword or null string
		"""
		used = set(used)
		kwd = None
		result = ''
		if keywords:
			absolute_kwds = reduce_keywords(keywords)
			kwd = list(used.intersection(absolute_kwds))
			#if keywords == ['~ppc64']:
				#print "Checked keywords for kwd", keywords, used, "kwd =", kwd
		if not kwd:
			#print "Checking for kwd against portage.archlist"
			absolute_kwds = reduce_keywords(keywords)
			# check for one against archlist then re-check
			kwd = list(absolute_kwds.intersection(portage.archlist))
			#print "determined keyword =", kwd
		if len(kwd) == 1:
			key = kwd[0]
			#print "determined keyword =", key
		elif not kwd:
			#print "kwd != 1", kwd, cpv
			result = self._missing(self.keyword, keywords)
		else: # too many, try to narrow them dowm
			#print "too many kwd's, trying to match against arch"
			_kwd = list(set(kwd).intersection(self.arch))
			key = ''
			if _kwd:
				#print "found one! :)", _kwd
				key = _kwd
			else: # try re-running the short list against archlist
				#print "Checking kwd for _kwd against portage.archlist"
				_kwd = list(set(kwd).intersection(portage.archlist))
				if _kwd and len(_kwd) == 1:
					#print "found one! :)", _kwd
					key = _kwd[0]
				else:
					#print " :( didn't work, _kwd =", _kwd, "giving up on:", cpv
					result = self._missing(self.keyword, keywords)
		i = 0
		while not result and i in self.parse_range:
			parsekey = self.parse_order[i]
			result = self.check_key[parsekey](key, keywords)
			i += 1
		return result

	def _stable(self, key, keywords):
		"""test for a normal stable keyword"""
		if key in keywords:
			return key
		return ''

	def _testing(self, key, keywords):
		"""test for a normal testing keyword"""
		if ("~" + key) in keywords:
			return "~" + key
		return ''

	def _prefix(self, key, keywords):
		"""test for a stable prefix keyword"""
		if not self.prefix:
			return ''
		_key = '-'.join([key, self.prefix])
		if _key in keywords:
			#print key, "is in", keywords
			return _key
		return ''

	def _testing_prefix(self, key, keywords):
		"""test for a testing prefix keyword"""
		if not self.prefix:
			return ''
		_key = "~" +'-'.join([key, self.prefix])
		if _key in keywords:
			#print key, "is in", keywords
			return _key
		return ''

	def _missing(self, key, keywords):
		"""generates a missing keyword to return"""
		if self.prefix and key != self.keyword:
			_key = '-'.join([key, self.prefix])
		else:
			_key = '-' + key
		#print "_missisng :(  _key =", _key
		return _key

	def get_inst_keyword_cpv(self, cpv):
		"""Determines the installed with keyword for cpv

		@type cpv: string
		@param cpv: an installed CAT/PKG-VER
		@rtype: string
		@returns a keyword determined to have been used to install cpv
		"""
		keywords, used = self.vardb.aux_get(cpv, ["KEYWORDS", "USE"])
		keywords = keywords.split()
		used = used.split()
		return self._parse(keywords, used, cpv=cpv)

	def get_inst_keyword_pkg(self, pkg):
		"""Determines the installed with keyword for cpv

		@param pkg: gentoolkit.package.Package object
		@rtype: string
		@returns a keyword determined to have been used to install cpv
		"""
		keywords, used = pkg.environment(["KEYWORDS", "USE"],
			prefer_vdb=True, fallback=False)
		keywords = keywords.split()
		used = used.split()
		return self._parse(keywords, used, pkg=pkg)

	def _parse(self, keywords, used, pkg=None, cpv=None):
		if pkg:
			_cpv = pkg.cpv
		else:
			_cpv = cpv
		if not self.parse_order:
			self.set_order(used)
		keyword = self.keyword
		# sanity check
		if self.arch not in used:
			#print "Found a mismatch = ", cpv, self.arch, used
			self.mismatched.append(_cpv)
		if keyword in keywords:
			#print "keyword", keyword, "is in", keywords
			return keyword
		elif "~"+keyword in keywords:
			#print "~keyword", keyword, "is in", keywords
			return "~"+keyword
		else:
			keyword = self.determine_keyword(keywords, used, _cpv)
			if not keyword:
				raise errors.GentoolkitUnknownKeyword(_cpv, ' '.join(keywords), used)
			return keyword

	def set_order(self, used):
		"""Used to set the parsing order to determine a keyword
		used for installation.

		This is needed due to the way prefix arch's and keywords
		work with portage.  It looks for the 'prefix' flag. A positive result
		sets it to the prefix order and keyword.

		@type used: list
		@param used: a list of pkg USE flags or the system USE flags"""
		if 'prefix' in used:
			#print "SET_ORDER() Setting parse order to prefix"
			prefix = None
			self.parse_order = self.prefix_order
			for key in self.accept_keywords:
				#print "SET_ORDER()  '"+key+"'"
				if '-' in key:
					#print "SET_ORDER()found prefix keyword :", key
					if self.arch in key:
						prefix = key.split('-')[1]
						#print "prefix =", prefix
						self.prefix = prefix
			self.keyword = '-'.join([self.arch, prefix])
		else:
			#print "SET_ORDER() Setting parse order to normal"
			self.parse_order = self.normal_order
			self.keyword = self.arch
		#print "SET_ORDER() completed: prefix =", self.prefix, ", keyword =", \
		#   self.keyword, "parse order =",self.parse_order
		#print

