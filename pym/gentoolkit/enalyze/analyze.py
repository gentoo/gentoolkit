#!/usr/bin/python
#
# Copyright 2010 Brian Dolbec <brian.dolbec@gmail.com>
# Copyright(c) 2010, Gentoo Foundation
# Distributed under the terms of the GNU General Public License v2
#

"""Provides a breakdown list of USE flags or keywords used and by
what packages according to the Installed package database"""

from __future__ import print_function

import sys

import gentoolkit
from gentoolkit.module_base import ModuleBase
from gentoolkit import pprinter as pp
from gentoolkit.flag import get_installed_use, get_flags
from gentoolkit.enalyze.lib import FlagAnalyzer, KeywordAnalyser
from gentoolkit.enalyze.output import nl, AnalysisPrinter
from gentoolkit.package import Package
from gentoolkit.helpers import get_installed_cpvs

import portage


def gather_flags_info(
		cpvs=None,
		system_flags=None,
		include_unset=False,
		target="USE",
		use_portage=False,
		#  override-able for testing
		_get_flags=get_flags,
		_get_used=get_installed_use
		):
	"""Analyze the installed pkgs USE flags for frequency of use

	@type cpvs: list
	@param cpvs: optional list of [cat/pkg-ver,...] to analyze or
			defaults to entire installed pkg db
	@type: system_flags: list
	@param system_flags: the current default USE flags as defined
			by portage.settings["USE"].split()
	@type include_unset: bool
	@param include_unset: controls the inclusion of unset USE flags in the report.
	@type target: string
	@param target: the environment variable being analyzed
			one of ["USE", "PKGUSE"]
	@type _get_flags: function
	@param _get_flags: ovride-able for testing,
			defaults to gentoolkit.enalyze.lib.get_flags
	@param _get_used: ovride-able for testing,
			defaults to gentoolkit.enalyze.lib.get_installed_use
	@rtype dict. {flag:{"+":[cat/pkg-ver,...], "-":[cat/pkg-ver,...], "unset":[]}
	"""
	if cpvs is None:
		cpvs = portage.db[portage.root]["vartree"].dbapi.cpv_all()
	# pass them in to override for tests
	flags = FlagAnalyzer(system_flags,
		filter_defaults=False,
		target=target,
		_get_flags=_get_flags,
		_get_used=get_installed_use
	)
	flag_users = {}
	for cpv in cpvs:
		if cpv.startswith("virtual"):
			continue
		if use_portage:
			plus, minus, unset = flags.analyse_cpv(cpv)
		else:
			pkg = Package(cpv)
			plus, minus, unset = flags.analyse_pkg(pkg)
		for flag in plus:
			if flag in flag_users:
				flag_users[flag]["+"].append(cpv)
			else:
				flag_users[flag] = {"+": [cpv], "-": []}
		for flag in minus:
			if flag in flag_users:
				flag_users[flag]["-"].append(cpv)
			else:
				flag_users[flag] = {"+":[], "-": [cpv]}
		if include_unset:
			for flag in unset:
				if flag in flag_users:
					if "unset" in flag_users[flag]:
						flag_users[flag]["unset"].append(cpv)
					else:
						flag_users[flag]["unset"] = [cpv]
				else:
					flag_users[flag] = {"+": [], "-": [], "unset": [cpv]}
	return flag_users


def gather_keywords_info(
		cpvs=None,
		system_keywords=None,
		use_portage=False,
		#  override-able for testing
		keywords=portage.settings["ACCEPT_KEYWORDS"],
		analyser = None
		):
	"""Analyze the installed pkgs 'keywords' for frequency of use

	@param cpvs: optional list of [cat/pkg-ver,...] to analyze or
			defaults to entire installed pkg db
	@param system_keywords: list of the system keywords
	@param keywords: user defined list of keywords to check and report on
			or reports on all relevant keywords found to have been used.
	@param _get_kwds: overridable function for testing
	@param _get_used: overridable function for testing
	@rtype dict. {keyword:{"stable":[cat/pkg-ver,...], "testing":[cat/pkg-ver,...]}
	"""
	if cpvs is None:
		cpvs = portage.db[portage.root]["vartree"].dbapi.cpv_all()
	keyword_users = {}
	for cpv in cpvs:
		if cpv.startswith("virtual"):
			continue
		if use_portage:
			keyword = analyser.get_inst_keyword_cpv(cpv)
		else:
			pkg = Package(cpv)
			keyword = analyser.get_inst_keyword_pkg(pkg)
		#print "returned keyword =", cpv, keyword, keyword[0]
		key = keyword[0]
		if key in ["~", "-"]:
			_kwd = keyword[1:]
			if _kwd in keyword_users:
				if key in ["~"]:
					keyword_users[_kwd]["testing"].append(cpv)
				elif key in ["-"]:
					#print "adding cpv to missing:", cpv
					keyword_users[_kwd]["missing"].append(cpv)
			else:
				if key in ["~"]:
					keyword_users[_kwd] = {"stable": [],
						"testing": [cpv], "missing": []}
				elif key in ["-"]:
					keyword_users[_kwd] = {"stable": [],
						"testing": [], "missing": [cpv]}
				else:
					keyword_users[_kwd] = {"stable": [cpv],
						"testing": [], "missing": []}
		elif keyword in keyword_users:
				keyword_users[keyword]["stable"].append(cpv)
		else:
				keyword_users[keyword] = {
					"stable": [cpv],
					"testing": [],
					"missing": []
					}
	return keyword_users


class Analyse(ModuleBase):
	"""Installed db analysis tool to query the installed databse
	and produce/output stats for USE flags or keywords/mask.
	The 'rebuild' action output is in the form suitable for file type output
	to create a new package.use, package.keywords, package.unmask
	type files in the event of needing to rebuild the
	/etc/portage/* user configs
	"""
	def __init__(self):
		ModuleBase.__init__(self)
		self.command_name = "enalyze"
		self.module_name = "analyze"
		self.options = {
			"flags": False,
			"keywords": False,
			"packages": False,
			"unset": False,
			"verbose": False,
			"quiet": False,
			'prefix': False,
			'portage': True
		}
		self.module_opts = {
			"-f": ("flags", "boolean", True),
			"--flags": ("flags", "boolean", True),
			"-k": ("keywords", "boolean", True),
			"--keywords": ("keywords", "boolean", True),
			"-u": ("unset", "boolean", True),
			"--unset": ("unset", "boolean", True),
			"-v": ("verbose", "boolean", True),
			"--verbose": ("verbose", "boolean", True),
			"-p": ("prefix", "boolean", True),
			"--prefix": ("prefix", "boolean", True),
			"-G": ("portage", "boolean", False),
			"--portage": ("portage", "boolean", False),
		}
		self.formatted_options = [
			("  -h, --help",  "Outputs this useage message"),
			("  -u, --unset",
			"Additionally include any unset USE flags and the packages"),
			("", "that could use them"),
			("  -v, --verbose",
			"Used in the analyze action to output more detailed information"),
			("  -p, --prefix",
			"Used for testing purposes only, runs report using " +
			"a prefix keyword and 'prefix' USE flag"),
			#(" -G, --portage",
			#"Use portage directly instead of gentoolkit's Package " +
			#"object for some operations. Usually a little faster."),
		]
		self.formatted_args = [
			("  use",
			"Causes the action to analyze the installed packages USE flags"),
			("  pkguse",
			"Causes the action to analyze the installed packages PKGUSE flags"),
			("  ",
			"These are flags that have been set in /etc/portage/package.use"),
			("  keywords",
			"Causes the action to analyze the installed packages keywords"),
			("  packages",
			"Causes the action to analyze the installed packages and the"),
			("  ",
			"USE flags they were installed with"),
			("  unmask",
			"Causes the action to analyze the installed packages"),
			("  ",
			"for those that need to be unmasked")
		]
		self.short_opts = "huvpG"
		self.long_opts = ("help", "unset", "verbose", "prefix") #, "portage")
		self.need_queries = True
		self.arg_spec = "Target"
		self.arg_options = ['use', 'pkguse','keywords', 'packages', 'unmask']
		self.arg_option = False
		self.warning = (
			"   CAUTION",
			"This is beta software and some features/options are incomplete,",
			"some features may change in future releases includig its name.",
			"Feedback will be appreciated, http://bugs.gentoo.org")


	def run(self, input_args, quiet=False):
		"""runs the module

		@param input_args: input arguments to be parsed
		"""
		query = self.main_setup(input_args)
		query = self.validate_query(query)
		self.set_quiet(quiet)
		if query in ["use", "pkguse"]:
			self.analyse_flags(query)
		elif query in ["keywords"]:
			self.analyse_keywords()
		elif query in ["packages"]:
			self.analyse_packages()
		elif query in ["unmask"]:
			self.analyse_unmask()

	def analyse_flags(self, target):
		"""This will scan the installed packages db and analyze the
		USE flags used for installation and produce a report on how
		they were used.

		@type target: string
		@param target: the target to be analyzed, one of ["use", "pkguse"]
		"""
		system_use = portage.settings["USE"].split()
		self.printer = AnalysisPrinter(
				"use",
				self.options["verbose"],
				system_use)
		if self.options["verbose"]:
			cpvs = portage.db[portage.root]["vartree"].dbapi.cpv_all()
			#cpvs = get_installed_cpvs()
			#print "Total number of installed ebuilds =", len(cpvs)
			flag_users = gather_flags_info(cpvs, system_use,
				self.options["unset"], target=target.upper(),
				use_portage=self.options['portage'])
		else:
			cpvs = get_installed_cpvs()
			flag_users = gather_flags_info(cpvs, system_flags=system_use,
				include_unset=self.options["unset"], target=target.upper(),
				use_portage=self.options['portage'])
		#print flag_users
		flag_keys = sorted(flag_users)
		if self.options["verbose"]:
			print(" Flag                                 System  #pkgs   cat/pkg-ver")
			blankline = nl
		elif not self.options['quiet']:
			print(" Flag                                 System  #pkgs")
			blankline = lambda: None
		for flag in flag_keys:
			flag_pos = flag_users[flag]["+"]
			if len(flag_pos):
				self.printer(flag, "+", flag_pos)
				#blankline()
			flag_neg = flag_users[flag]["-"]
			if len(flag_neg):
				self.printer(flag, "-", flag_neg)
				#blankline()
			if "unset" in flag_users[flag] and flag_users[flag]["unset"]:
				flag_unset = flag_users[flag]["unset"]
				self.printer(flag, "unset", flag_unset)
			#blankline()
		if not self.options['quiet']:
			print("===================================================")
			print("Total number of flags in report =",
				pp.output.red(str(len(flag_keys))))
			if self.options["verbose"]:
				print("Total number of installed ebuilds =",
					pp.output.red(str(len([x for x in cpvs]))))
			print()


	def analyse_keywords(self, keywords=None):
		"""This will scan the installed packages db and analyze the
		keywords used for installation and produce a report on them.
		"""
		print()
		system_keywords = portage.settings["ACCEPT_KEYWORDS"]
		arch = portage.settings["ARCH"]
		if self.options["prefix"]:
			# build a new keyword for testing
			system_keywords = "~" + arch + "-linux"
		if self.options["verbose"] or self.options["prefix"]:
			print("Current system ARCH =", arch)
			print("Current system ACCEPT_KEYWORDS =", system_keywords)
		system_keywords = system_keywords.split()
		self.printer = AnalysisPrinter(
				"keywords",
				self.options["verbose"],
				system_keywords)
		self.analyser = KeywordAnalyser( arch, system_keywords, portage.db[portage.root]["vartree"].dbapi)
		#self.analyser.set_order(portage.settings["USE"].split())
		# only for testing
		test_use = portage.settings["USE"].split()
		if self.options['prefix'] and 'prefix' not in test_use:
			print("ANALYSE_KEYWORDS() 'prefix' flag not found in system",
				"USE flags!!!  appending for testing")
			print()
			test_use.append('prefix')
		self.analyser.set_order(test_use)
		# /end testing

		if self.options["verbose"]:
			cpvs = portage.db[portage.root]["vartree"].dbapi.cpv_all()
			#print "Total number of installed ebuilds =", len(cpvs)
			keyword_users = gather_keywords_info(
				cpvs=cpvs,
				system_keywords=system_keywords,
				use_portage=self.options['portage'],
				keywords=keywords, analyser = self.analyser
				)
			blankline = nl
		else:
			keyword_users = gather_keywords_info(
				system_keywords=system_keywords,
				use_portage=self.options['portage'],
				keywords=keywords,
				analyser = self.analyser
				)
			blankline = lambda: None
		#print keyword_users
		keyword_keys = sorted(keyword_users)
		if self.options["verbose"]:
			print(" Keyword               System  #pkgs   cat/pkg-ver")
		elif not self.options['quiet']:
			print(" Keyword               System  #pkgs")
		for keyword in keyword_keys:
			kwd_stable = keyword_users[keyword]["stable"]
			if len(kwd_stable):
				self.printer(keyword, " ", kwd_stable)
				blankline()
			kwd_testing = keyword_users[keyword]["testing"]
			if len(kwd_testing):
				self.printer(keyword, "~", kwd_testing)
				blankline()
			kwd_missing = keyword_users[keyword]["missing"]
			if len(kwd_missing):
				self.printer(keyword, "-", kwd_missing)
				blankline
		if not self.options['quiet']:
			if self.analyser.mismatched:
				print("_________________________________________________")
				print(("The following packages were found to have a \n" +
					"different recorded ARCH than the current system ARCH"))
				for cpv in self.analyser.mismatched:
					print("\t", pp.cpv(cpv))
			print("===================================================")
			print("Total number of keywords in report =",
				pp.output.red(str(len(keyword_keys))))
			if self.options["verbose"]:
				print("Total number of installed ebuilds =",
					pp.output.red(str(len(cpvs))))
			print()


	def analyse_packages(self):
		"""This will scan the installed packages db and analyze the
		USE flags used for installation and produce a report.

		@type target: string
		@param target: the target to be analyzed, one of ["use", "pkguse"]
		"""
		system_use = portage.settings["USE"].split()
		if self.options["verbose"]:
			cpvs = portage.db[portage.root]["vartree"].dbapi.cpv_all()
			key_width = 45
		else:
			cpvs = get_installed_cpvs()
			key_width = 1

		self.printer = AnalysisPrinter(
				"packages",
				self.options["verbose"],
				key_width=key_width)

		cpvs = sorted(cpvs)
		flags = FlagAnalyzer(
					system=system_use,
					filter_defaults=False,
					target="USE"
					)

		if self.options["verbose"]:
			print("   cat/pkg-ver                             USE Flags")
				#   "app-emulation/emul-linux-x86-sdl-20100915 ...."
			blankline = nl
		elif not self.options['quiet']:
			print("   cat/pkg-ver                             USE Flags")
			blankline = lambda: None
		for cpv in cpvs:
			(flag_plus, flag_neg, unset) = flags.analyse_cpv(cpv)
			if self.options["unset"]:
				self.printer(cpv, "", (flag_plus, flag_neg, unset))
			else:
				self.printer(cpv, "", (flag_plus, flag_neg, []))
		if not self.options['quiet']:
			print("===================================================")
			print("Total number of installed ebuilds =",
				pp.output.red(str(len([x for x in cpvs]))))
			print()


	def analyse_unmask(self):
		"""This will scan the installed packages db and analyze the
		unmasking used for installation and produce a report on them.
		"""
		self.not_implemented("unmask")



def main(input_args):
	"""Common starting method by the analyze master
	unless all modules are converted to this class method.

	@param input_args: input args as supplied by equery master module.
	"""
	query_module = Analyse()
	query_module.run(input_args, gentoolkit.CONFIG['quiet'])

# vim: set ts=4 sw=4 tw=79:
