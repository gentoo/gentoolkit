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
from gentoolkit.formatters import CpvValueWrapper
from gentoolkit.cpv import split_cpv


def nl(lines=1):
	"""small utility function to print blank lines

	@type lines: integer
	@param lines: optional number of blank lines to print
		default = 1
		"""
	print(('\n' * lines))

class AnalysisPrinter(CpvValueWrapper):
	"""Printing functions"""
	def __init__(self, target, verbose=True, references=None, key_width=1, width=None):
		"""@param references: list of accepted keywords or
				the system use flags
				"""
		self.references = references
		self.key_width = key_width
		self.width = width
		CpvValueWrapper.__init__(self, cpv_width=key_width, width=width)
		self.set_target(target, verbose)

	def set_target(self, target, verbose=True):
		if target in ["use"]:
			if verbose:
				self.print_fn = self.print_use_verbose
			else:
				self.print_fn = self.print_use_quiet
			self._format_key = self._format_use_keyword
		elif target in ["keywords"]:
			if verbose:
				self.print_fn = self.print_keyword_verbose
			else:
				self.print_fn = self.print_keyword_quiet
			self._format_key = self._format_use_keyword
		elif target in ["packages"]:
			if verbose:
				self.print_fn = self.print_pkg_verbose
			else:
				self.print_fn = self.print_pkg_quiet
			self._format_key = self._format_pkg

	def __call__(self, key, active, data):
		self._format_key(key, active, data)

	def _format_use_keyword(self, key, active, pkgs):
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

	# W0613: *Unused argument %r*
	# pylint: disable-msg=W0613
	def _format_pkg(self, key, active, flags):
		"""Determines the stats for key, formats it and
		calls the pre-determined print function
		"""
		(plus, minus, cleaned) = flags
		_plus = []
		_minus = []
		for flag in plus:
			_flag = flag.strip()
			if _flag:
				_plus.append(_flag)
		for flag in minus:
			_flag = flag.strip()
			if _flag:
				_minus.append(_flag)
		#print("cpv=", key, "_plus=", _plus, "_minus=", _minus)
		self.print_fn(key, (plus, minus, cleaned))

	def print_pkg_verbose(self, cpv, flags):
		"""Verbosely prints the pkg's use flag info.
		"""
		(plus, minus, cleaned) = flags
		_flags = []
		for flag in plus:
			_flags.append(pp.useflag((flag), True))
		for flag in minus:
			_flags.append(pp.useflag(('-'+flag), False))
		
		print(self._format_values(cpv, ", ".join(_flags)))

	def print_pkg_quiet(self, cpv, flags):
		"""Verbosely prints the pkg's use flag info.
		"""
		(plus, minus, cleaned) = flags
		_flags = []
		for flag in plus:
			_flags.append(pp.useflag((flag), True))
		for flag in minus:
			_flags.append(pp.useflag(('-'+flag), False))
		
		print(self._format_values(cpv, ", ".join(_flags)))


class RebuildPrinter(CpvValueWrapper):
	"""Output functions"""
	def __init__(self, target, pretend=True, exact=False, key_width=1, width=None):
		"""@param references: list of accepted keywords or
				the system use flags
		"""
		self.target = target
		self.set_target(target)
		self.pretend = pretend
		CpvValueWrapper.__init__(self, cpv_width=key_width, width=width)
		if pretend:
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
