# Copyright(c) 2009, Gentoo Foundation
#
# Copyright 2010 Brian Dolbec <brian.dolbec@gmail.com>
# Copyright(c) 2010, Gentoo Foundation
# Distributed under the terms of the GNU General Public License v2
#
# $Header: $

"""General Base Module class to hold common module operation functions
"""

from __future__ import print_function

__docformat__ = 'epytext'


import errno
import sys
import time
from getopt import gnu_getopt, GetoptError

import gentoolkit.pprinter as pp
from gentoolkit.formatters import format_options
from gentoolkit.base import mod_usage
from gentoolkit import CONFIG

class ModuleBase(object):
	"""E-app base module class to parse module options print module help, etc.."""

	def __init__(self):
		self.module_name = None
		self.options = {}
		self.formatted_options = None
		self.short_opts = None
		self.long_opts = None
		self.module_opts = {}
		self.warning = None
		self.need_queries = True
		self.saved_verbose = None


	def print_help(self, with_description=True):
		"""Print description, usage and a detailed help message.

		@type with_description: bool
		@param with_description: if true, print module's __doc__ string
		"""

		if with_description:
			print()
			print(__doc__.strip())
			print()
		if self.warning:
			print()
			for line in self.warning:
				sys.stderr.write(pp.warn(line))
			print()
		print(mod_usage(mod_name=self.module_name, arg=self.arg_spec, optional=self.arg_option))
		print()
		print(pp.command("options"))
		print(format_options( self.formatted_options ))
		if self.formatted_args:
			print()
			print(pp.command(self.arg_spec))
			print(format_options(self.formatted_args))
		print()

	def parse_module_options(self, module_opts):
		"""Parse module options and update self.options"""

		opts = (x[0] for x in module_opts)
		posargs = (x[1] for x in module_opts)
		for opt, posarg in zip(opts, posargs):
			if opt in ('-h', '--help'):
					self.print_help()
					sys.exit(0)
			opt_name, opt_type, opt_setting = self.module_opts[opt]
			if opt_type == 'boolean':
				self.options[opt_name] = opt_setting
			elif opt_type == 'int':
				if posarg.isdigit():
					val = int(posarg)
				else:
					print()
					err = "Module option %s requires integer (got '%s')"
					sys.stdout.write(pp.error(err % (opt,posarg)))
					print()
					self.print_help(with_description=False)
					sys.exit(2)
				self.options[opt_name] = val

	def set_quiet(self, quiet):
		"""sets the class option["quiet"] and option["verbose"] accordingly"""
		if quiet == self.options['quiet']:
			return
		if self.saved_verbose:
			# detected a switch
			verbose = self.options['verbose']
			self.options['verbose']  = self.saved_verbose
			self.saved_verbose = verbose
		elif quiet:
			self.saved_verbose = self.options['verbose']
			self.options['verbose'] = False
		self.options['quiet'] = quiet
		return

	def validate_query(self, query, depth=0):
		"""check that the query meets the modules TargetSpec
		If not it attempts to reduce it to a valid TargetSpec
		or prints the help message and exits
		"""
		if depth > 1:
			return []
		if len(query) > 1:
			query = list(set(self.arg_options).intersection(query))
			#print "reduced query =", query
			query = self.validate_query(query, depth+1)
		if isinstance(query, list):
			query = query[0]
		if query not in self.arg_options:
			print()
			print(pp.error(
				"Error starting module. Incorrect or No TargetSpec specified!"
				))
			print("query = ", query)
			self.print_help()
			sys.exit(2)
		return query


	def main_setup(self, input_args):
		"""Parse input and prepares the program"""

		try:
			module_opts, queries = gnu_getopt(input_args, self.short_opts, self.long_opts)
		except GetoptError as err:
			sys.stderr.write(pp.error("Module %s" % err))
			print()
			self.print_help(with_description=False)
			sys.exit(2)
		self.parse_module_options(module_opts)
		if self.need_queries and not queries:
			self.print_help()
			sys.exit(2)
		return queries


	def not_implemented(self, target):
		"""Prints a standard module not implemented message"""
		print()
		print(pp.error(
			"Sorry %s module and/or target is not implenented yet."
			% pp.emph(self.command_name)))
		print("module: %s, target: %s" %(pp.emph(self.module_name), pp.emph(target)))
		print()

# vim: set ts=4 sw=4 tw=79:
