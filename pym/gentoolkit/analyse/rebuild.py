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
from gentoolkit.dbapi import PORTDB, VARDB
from gentoolkit.analyse.base import ModuleBase
from gentoolkit import pprinter as pp
from gentoolkit.analyse.lib import (get_installed_use, get_flags,
	abs_flag, abs_list, FlagAnalyzer)
from gentoolkit.analyse.output import RebuildPrinter

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
	@param cpvs: optional list of [cat/pkg-ver,...] to analyse or
			defaults to entire installed pkg db
	@type: system_flags: list
	@param system_flags: the current default USE flags as defined
			by portage.settings["USE"].split()
	@type _get_flags: function
	@param _get_flags: ovride-able for testing,
			defaults to gentoolkit.analyse.lib.get_flags
	@param _get_used: ovride-able for testing,
			defaults to gentoolkit.analyse.lib.get_installed_use
	@rtype dict. {cpv:['flag1', '-flag2',...]}
	"""
	if cpvs is None:
		cpvs = VARDB.cpv_all()
	cpvs.sort()
	data = {}
	# pass them in to override for tests
	flags = FlagAnalyzer(system_flags,
		filter_defaults=True,
		target="USE",
		_get_flags=_get_flags,
		_get_used=get_installed_use
	)
	for cpv in cpvs:
		plus, minus, unset = flags.analyse_cpv(cpv)
		for flag in minus:
			plus.add("-"+flag)
		if len(plus):
			data[cpv] = list(plus)
	return data


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
		self.module_name = "rebuild"
		self.options = {
			"use": False,
			"keywords": False,
			"unmask": False,
			"verbose": False,
			"quiet": False,
			"exact": False,
			"pretend": False,
			#"unset": False
		}
		self.module_opts = {
			"-p": ("pretend", "boolean", True),
			"--pretend": ("pretend", "boolean", True),
			"-e": ("exact", "boolean", True),
			"--exact": ("exact", "boolean", True),
			"-v": ("verbose", "boolean", True),
			"--verbose": ("verbose", "boolean", True),
		}
		self.formatted_options = [
			("    -h, --help",  "Outputs this useage message"),
			("    -p, --pretend", "Does not actually create the files."),
			("    ", "It directs the outputs to the screen"),
			("    -e, --exact", "will atomize the package with a"),
			("  ", "leading '=' and include the version")
		]
		self.formatted_args = [
			("    use",
			"causes the action to analyse the installed packages USE flags"),
			("    keywords",
			"causes the action to analyse the installed packages keywords"),
			("    unmask",
			"causes the action to analyse the installed packages " + \
			"current mask status")
		]
		self.short_opts = "hepv"
		self.long_opts = ("help", "exact", "pretend", "verbose")
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
		output = RebuildPrinter("use", self.options["pretend"], self.options["exact"])
		pkgs = cpv_all_diff_use(system_flags=system_use)
		pkg_count = len(pkgs)
		if self.options["verbose"]:
			print()
			print((pp.emph("  -- Found ") +  pp.number(str(pkg_count)) +
				pp.emph(" packages that need entries")))
			#print pp.emph("     package.use to maintain their current setting")
		if pkgs:
			pkg_keys = sorted(pkgs)
			#print len(pkgs)
			if self.options["pretend"] and not self.options["quiet"]:
				print()
				print(pp.globaloption(
					"  -- These are the installed packages & flags " +
					"that were detected"))
				print(pp.globaloption("     to need flag settings other " +
					"than the defaults."))
				print()
			elif not self.options["quiet"]:
				print("  -- preparing pkgs for file entries")
			flag_count = 0
			unique_flags = set()
			for pkg in pkg_keys:
				if self.options['verbose']:
					flag_count += len(pkgs[pkg])
					unique_flags.update(abs_list(pkgs[pkg]))
				output(pkg, pkgs[pkg])
			if self.options['verbose']:
				message = (pp.emph("     ") +
					pp.number(str(len(unique_flags))) +
					pp.emph(" unique flags\n") + "     " +
					pp.number(str(flag_count))+
					pp.emph(" flag entries\n") + "     " +
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
				self.save_file(filepath, output.use_lines)

	def rebuild_keywords(self):
		print("Module action not yet available")
		print()

	def rebuild_unmask(self):
		print("Module action not yet available")
		print()


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
	"""Common starting method by the analyse master
	unless all modules are converted to this class method.

	@param input_args: input args as supplied by equery master module.
	"""
	query_module = Rebuild()
	query_module.run(input_args, gentoolkit.CONFIG['quiet'])

# vim: set ts=4 sw=4 tw=79:

