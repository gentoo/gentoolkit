#!/usr/bin/python
#
# Copyright 2010 Brian Dolbec <brian.dolbec@gmail.com>
# Copyright(c) 2010, Gentoo Foundation
# Distributed under the terms of the GNU General Public License v2
#


"""Provides a rebuild file of USE flags or keywords used and by
what packages according to the Installed package database"""


from __future__ import print_function


import os
import sys

import gentoolkit
from gentoolkit.module_base import ModuleBase
from gentoolkit import pprinter as pp
from gentoolkit.enalyze.lib import (get_installed_use, get_flags, FlagAnalyzer,
	KeywordAnalyser)
from gentoolkit.flag import reduce_flags
from gentoolkit.enalyze.output import RebuildPrinter
from gentoolkit.atom import Atom


import portage


def cpv_all_diff_use(
		cpvs=None,
		system_flags=None,
		#  override-able for testing
		_get_flags=get_flags,
		_get_used=get_installed_use
		):
	"""Data gathering and analysis function determines
	the difference between the current default USE flag settings
	and the currently installed pkgs recorded USE flag settings

	@type cpvs: list
	@param cpvs: optional list of [cat/pkg-ver,...] to analyze or
			defaults to entire installed pkg db
	@type: system_flags: list
	@param system_flags: the current default USE flags as defined
			by portage.settings["USE"].split()
	@type _get_flags: function
	@param _get_flags: ovride-able for testing,
			defaults to gentoolkit.enalyze.lib.get_flags
	@param _get_used: ovride-able for testing,
			defaults to gentoolkit.enalyze.lib.get_installed_use
	@rtype dict. {cpv:['flag1', '-flag2',...]}
	"""
	if cpvs is None:
		cpvs = portage.db[portage.root]["vartree"].dbapi.cpv_all()
	cpvs.sort()
	data = {}
	cp_counts = {}
	# pass them in to override for tests
	flags = FlagAnalyzer(system_flags,
		filter_defaults=True,
		target="USE",
		_get_flags=_get_flags,
		_get_used=get_installed_use
	)
	for cpv in cpvs:
		plus, minus, unset = flags.analyse_cpv(cpv)
		atom = Atom("="+cpv)
		atom.slot = portage.db[portage.root]["vartree"].dbapi.aux_get(atom.cpv, ["SLOT"])[0]
		for flag in minus:
			plus.add("-"+flag)
		if len(plus):
			if atom.cp not in data:
				data[atom.cp] = []
			if atom.cp not in cp_counts:
				cp_counts[atom.cp] = 0
			atom.use = list(plus)
			data[atom.cp].append(atom)
			cp_counts[atom.cp] += 1
	return data, cp_counts


def cpv_all_diff_keywords(
		cpvs=None,
		system_keywords=None,
		use_portage=False,
		#  override-able for testing
		keywords=portage.settings["ACCEPT_KEYWORDS"],
		analyser = None
		):
	"""Analyze the installed pkgs 'keywords' for difference from ACCEPT_KEYWORDS

	@param cpvs: optional list of [cat/pkg-ver,...] to analyze or
			defaults to entire installed pkg db
	@param system_keywords: list of the system keywords
	@param keywords: user defined list of keywords to check and report on
			or reports on all relevant keywords found to have been used.
	@param _get_kwds: overridable function for testing
	@param _get_used: overridable function for testing
	@rtype dict. {keyword:{"stable":[cat/pkg-ver,...],
						   "testing":[cat/pkg-ver,...]}
	"""
	if cpvs is None:
		cpvs = portage.db[portage.root]["vartree"].dbapi.cpv_all()
	keyword_users = {}
	cp_counts = {}
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
		if key in ["~", "-"] and keyword not in system_keywords:
			atom = Atom("="+cpv)
			if atom.cp not in keyword_users:
				keyword_users[atom.cp] = []
			if atom.cp not in cp_counts:
				cp_counts[atom.cp] = 0
			if key in ["~"]:
				atom.keyword = keyword
				atom.slot = portage.db[portage.root]["vartree"].dbapi.aux_get(atom.cpv, ["SLOT"])[0]
				keyword_users[atom.cp].append(atom)
				cp_counts[atom.cp] += 1
			elif key in ["-"]:
				#print "adding cpv to missing:", cpv
				atom.keyword = "**"
				atom.slot = portage.db[portage.root]["vartree"].dbapi.aux_get(atom.cpv, ["SLOT"])[0]
				keyword_users[atom.cp].append(atom)
				cp_counts[atom.cp] += 1
	return keyword_users, cp_counts


class Rebuild(ModuleBase):
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
		self.module_name = "rebuild"
		self.options = {
			"use": False,
			"keywords": False,
			"unmask": False,
			"verbose": False,
			"quiet": False,
			"exact": False,
			"pretend": False,
			"prefix": False,
			"portage": True,
			"slot": False
			#"unset": False
		}
		self.module_opts = {
			"-p": ("pretend", "boolean", True),
			"--pretend": ("pretend", "boolean", True),
			"-e": ("exact", "boolean", True),
			"--exact": ("exact", "boolean", True),
			"-s": ("slot", "boolean", True),
			"--slot": ("slot", "boolean", True),
			"-v": ("verbose", "boolean", True),
			"--verbose": ("verbose", "boolean", True),
		}
		self.formatted_options = [
			("    -h, --help",  "Outputs this useage message"),
			("    -p, --pretend", "Does not actually create the files."),
			("    ", "It directs the outputs to the screen"),
			("    -e, --exact", "will atomize the package with a"),
			("  ", "leading '=' and include the version"),
			("    -s, --slot", "will atomize the package with a"),
			("  ", "leading '=' and include the slot")
		]
		self.formatted_args = [
			("    use",
			"causes the action to analyze the installed packages USE flags"),
			("    keywords",
			"causes the action to analyze the installed packages keywords"),
			("    unmask",
			"causes the action to analyze the installed packages " + \
			"current mask status")
		]
		self.short_opts = "hepsv"
		self.long_opts = ("help", "exact", "pretend", "slot", "verbose")
		self.need_queries = True
		self.arg_spec = "TargetSpec"
		self.arg_options = ['use', 'keywords', 'unmask']
		self.arg_option = False
		self.warning = (
			"     CAUTION",
			"This is beta software and some features/options are incomplete,",
			"some features may change in future releases includig its name.",
			"The file generated is saved in your home directory",
			"Feedback will be appreciated, http://bugs.gentoo.org")



	def run(self, input_args, quiet=False):
		"""runs the module

		@param input_args: input arguments to be parsed
		"""
		self.options['quiet'] = quiet
		query = self.main_setup(input_args)
		query = self.validate_query(query)
		if query in ["use"]:
			self.rebuild_use()
		elif query in ["keywords"]:
			self.rebuild_keywords()
		elif query in ["unmask"]:
			self.rebuild_unmask()


	def rebuild_use(self):
		if not self.options["quiet"]:
			print()
			print("  -- Scanning installed packages for USE flag settings that")
			print("     do not match the default settings")
		system_use = portage.settings["USE"].split()
		output = RebuildPrinter(
			"use", self.options["pretend"], self.options["exact"],
				self.options['slot'])
		pkgs, cp_counts = cpv_all_diff_use(system_flags=system_use)
		pkg_count = len(pkgs)
		if self.options["verbose"]:
			print()
			print((pp.emph("  -- Found ") +  pp.number(str(pkg_count)) +
				pp.emph(" packages that need entries")))
			#print pp.emph("     package.use to maintain their current setting")
		pkg_keys = []
		if pkgs:
			pkg_keys = sorted(pkgs)
			#print len(pkgs)
			if self.options["pretend"] and not self.options["quiet"]:
				print()
				print(pp.globaloption(
					"  -- These are the installed packages & use flags " +
					"that were detected"))
				print(pp.globaloption("     to need use flag settings other " +
					"than the defaults."))
				print()
			elif not self.options["quiet"]:
				print("  -- preparing pkgs for file entries")
			for pkg in pkg_keys:
				output(pkg, pkgs[pkg], cp_counts[pkg])
			if self.options['verbose']:
				message = (pp.emph("     ") +
					pp.number(str(pkg_count)) +
					pp.emph(" different packages"))
				print()
				print(pp.globaloption("  -- Totals"))
				print(message)
				#print
				#unique = list(unique_flags)
				#unique.sort()
				#print unique
			if not self.options["pretend"]:
				filepath = os.path.expanduser('~/package.use.test')
				self.save_file(filepath, output.lines)

	def rebuild_keywords(self):
		#print("Module action not yet available")
		#print()
		"""This will scan the installed packages db and analyze the
		keywords used for installation and produce a report on them.
		"""
		system_keywords = portage.settings["ACCEPT_KEYWORDS"].split()
		output = RebuildPrinter(
			"keywords", self.options["pretend"], self.options["exact"],
			self.options['slot'])
		arch = portage.settings["ARCH"]
		if self.options["prefix"]:
			# build a new keyword for testing
			system_keywords = "~" + arch + "-linux"
		if self.options["verbose"] or self.options["prefix"]:
			print("Current system ARCH =", arch)
			print("Current system ACCEPT_KEYWORDS =", system_keywords)
		self.analyser = KeywordAnalyser( arch, system_keywords, portage.db[portage.root]["vartree"].dbapi)
		#self.analyser.set_order(portage.settings["USE"].split())
		# only for testing
		test_use = portage.settings["USE"].split()
		if self.options['prefix'] and 'prefix' not in test_use:
			print("REBUILD_KEYWORDS() 'prefix' flag not found in system",
				"USE flags!!!  appending for testing")
			print()
			test_use.append('prefix')
		self.analyser.set_order(test_use)
		# /end testing

		cpvs = portage.db[portage.root]["vartree"].dbapi.cpv_all()
		#print "Total number of installed ebuilds =", len(cpvs)
		pkgs, cp_counts = cpv_all_diff_keywords(
			cpvs=cpvs,
			system_keywords=system_keywords,
			use_portage=self.options['portage'],
			analyser = self.analyser
			)
		#print([pkgs[p][0].cpv for p in pkgs])
		pkg_keys = []
		if pkgs:
			pkg_keys = sorted(pkgs)
			#print(len(pkgs))
			if self.options["pretend"] and not self.options["quiet"]:
				print()
				print(pp.globaloption(
					"  -- These are the installed packages & keywords " +
					"that were detected"))
				print(pp.globaloption("     to need keyword settings other " +
					"than the defaults."))
				print()
			elif not self.options["quiet"]:
				print("  -- preparing pkgs for file entries")
			for pkg in pkg_keys:
				output(pkg, pkgs[pkg], cp_counts[pkg])
		if not self.options['quiet']:
			if self.analyser.mismatched:
				print("_________________________________________________")
				print(("The following packages were found to have a \n" +
					"different recorded ARCH than the current system ARCH"))
				for cpv in self.analyser.mismatched:
					print("\t", pp.cpv(cpv))
			print("===================================================")
			print("Total number of entries in report =",
				pp.output.red(str(len(pkg_keys))))
			if self.options["verbose"]:
				print("Total number of installed ebuilds =",
					pp.output.red(str(len(cpvs))))
			print()
			if not self.options["pretend"]:
				filepath = os.path.expanduser('~/package.keywords.test')
				self.save_file(filepath, output.lines)


	def rebuild_unmask(self):
		self.not_implemented("unmask")


	def save_file(self, filepath, data):
		"""Writes the data to the file determined by filepath

		@param filepath: string. eg. '/path/to/filename'
		@param data: list of lines to write to filepath
		"""
		if  not self.options["quiet"]:
			print('   - Saving file: %s' %filepath)
		with open(filepath, "w") as output:
			output.write('\n'.join(data))
		print("   - Done")


def main(input_args):
	"""Common starting method by the analyze master
	unless all modules are converted to this class method.

	@param input_args: input args as supplied by equery master module.
	"""
	query_module = Rebuild()
	query_module.run(input_args, gentoolkit.CONFIG['quiet'])

# vim: set ts=4 sw=4 tw=79:

