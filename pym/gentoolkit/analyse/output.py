#!/usr/bin/python
#
# Copyright(c) 2010, Gentoo Foundation
# Distributed under the terms of the GNU General Public License v2
#

"""Provides various output classes and functions for
both screen and file output
"""

from __future__ import print_function

import gentoolkit
from gentoolkit import pprinter as pp
from gentoolkit.textwrap_ import TextWrapper
from gentoolkit.cpv import split_cpv


def nl(lines=1):
	"""small utility function to print blank lines
	
	@type lines: integer
	@param lines: optional number of blank lines to print
		default = 1
		"""
	print(('\n' * lines))

class AnalysisPrinter(object):
	"""Printing functions"""
	def __init__(self, target, verbose=True, references=None):
		"""@param references: list of accepted keywords or
				the system use flags
				"""
		self.references = references
		self.set_target(target, verbose)

	def set_target(self, target, verbose=True):
		if target in ["use"]:
			if verbose:
				self.print_fn = self.print_use_verbose
			else:
				self.print_fn = self.print_use_quiet
		elif target in ["keywords"]:
			if verbose:
				self.print_fn = self.print_keyword_verbose
			else:
				self.print_fn = self.print_keyword_quiet

	def __call__(self, key, active, pkgs):
		self._format_key(key, active, pkgs)

	def _format_key(self, key, active, pkgs):
		"""Determines the stats for key, formats it and
		calls the pre-determined print function
		"""
		occurred = str(len(pkgs))
		if active in ["-", "~"]:
			_key = active + key
		else:
			_key = key
		if _key in self.references:
			default = "default"
		else:
			default = "......."
		count = ' '*(5-len(occurred)) + occurred
		pkgs.sort()
		self.print_fn(key, active, default, count, pkgs)

	@staticmethod
	def print_use_verbose(key, active, default, count, pkgs):
		"""Verbosely prints a set of use flag info. including the pkgs
		using them.
		"""
		_pkgs = pkgs[:]
		if active in ["+", "-"]:
			_key = pp.useflag((active+key), active=="+")
		else:
			_key = (" " + key)
		cpv = _pkgs.pop(0)
		print(_key,'.'*(35-len(key)), default, pp.number(count), pp.cpv(cpv))
		while _pkgs:
			cpv = _pkgs.pop(0)
			print(' '*52 + pp.cpv(cpv))

	# W0613: *Unused argument %r*
	# pylint: disable-msg=W0613
	@staticmethod
	def print_use_quiet(key, active, default, count, pkgs):
		"""Quietly prints a subset set of USE flag info..
		"""
		if active in ["+", "-"]:
			_key = pp.useflag((active+key), active=="+")
		else:
			_key = (" " + key)
		print(_key,'.'*(35-len(key)), default, pp.number(count))

	@staticmethod
	def print_keyword_verbose(key, stability, default, count, pkgs):
		"""Verbosely prints a set of keywords info. including the pkgs
		using them.
		"""
		_pkgs = pkgs[:]
		_key = (pp.keyword((stability+key),stable=(stability==" "),
			hard_masked=stability=="-"))
		cpv = _pkgs.pop(0)
		print(_key,'.'*(20-len(key)), default, pp.number(count), pp.cpv(cpv))
		while _pkgs:
			cpv = _pkgs.pop(0)
			print(' '*37 + pp.cpv(cpv))

	# W0613: *Unused argument %r*
	# pylint: disable-msg=W0613
	@staticmethod
	def print_keyword_quiet(key, stability, default, count, pkgs):
		"""Quietly prints a subset set of USE flag info..
		"""
		_key = (pp.keyword((stability+key), stable=(stability==" "),
			hard_masked=stability=="-"))
		print(_key,'.'*(20-len(key)), default, pp.number(count))


class RebuildPrinter(object):
	"""Output functions"""
	def __init__(self, target, pretend=True, exact=False):
		"""@param references: list of accepted keywords or
				the system use flags
		"""
		self.target = target
		self.set_target(target)
		self.pretend = pretend
		if pretend:
			self.twrap = TextWrapper(width=gentoolkit.CONFIG['termWidth'])
			self.spacer = '  '
			self.init_indent = len(self.spacer)
		else:
			self.spacer = ''
		self.exact = exact
		self.data = {}


	def set_target(self, target):
		if target in ["use"]:
			self.print_fn = self.print_use
			self.use_lines = [self.header()]
		elif target in ["keywords"]:
			self.print_fn = self.print_keyword
		elif target in ["unmask"]:
			self.print_fn = self.print_mask


	def __call__(self, key, values):
		self._format_key(key, values)


	def _format_key(self, key, values):
		"""Determines the stats for key, formats it and
		calls the pre-determined print function
		"""
		if self.exact:
			_key = "=" + key
		else:
			parts = split_cpv(key)
			_key = '/'.join(parts[:2])
		values.sort()
		self.data[_key] = values
		self.print_fn( _key, values)

	def _format_values(self, key, values):
		"""Format entry values ie. USE flags, keywords,...
		
		@type key: str
		@param key: a pre-formatted cpv
		@type values: list of pre-formatted strings
		@param values: ['flag1', 'flag2',...]
		@rtype: str
		@return: formatted options string
		"""

		result = []
		self.twrap.initial_indent = pp.cpv(key+" ")
		self.twrap.subsequent_indent = " " * (len(key)+1)
		result.append(self.twrap.fill(values))
		return '\n'.join(result)

	def print_use(self, key, values):
		"""Prints a USE flag string.
		"""
		if self.pretend:
			flags = []
			for flag in values:
				flags.append(pp.useflag(flag, (flag[0] != '-')))
			print(self._format_values(self.spacer+key, ' '.join(flags)))
		else:
			line = ' '.join([key, ' '.join(values)])
			self.use_lines.append(line)


	def print_keyword(self):
		pass


	def print_unmask(self):
		pass

	def header(self):
		"""Generates a file header
		"""
		
		h=("# This package.%s file was generated by "
			%self.target +
			"gentoolkit's 'analyse rebuild' module\n"
		)
		return h
