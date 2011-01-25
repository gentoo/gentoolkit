#!/usr/bin/python
#
# Copyright 2004 Karl Trygve Kalleberg <karltk@gentoo.org>
# Copyright(c) 2010, Gentoo Foundation
# Distributed under the terms of the GNU General Public License v2
#
# $Header$

import errno
import sys
import time

import gentoolkit
from gentoolkit.textwrap_ import TextWrapper
import gentoolkit.pprinter as pp


def format_options(options):
	"""Format module options.

	@type options: list
	@param options: [('option 1', 'description 1'), ('option 2', 'des... )]
	@rtype: str
	@return: formatted options string
	"""

	result = []
	twrap = TextWrapper(width=gentoolkit.CONFIG['termWidth'])
	opts = (x[0] for x in options)
	descs = (x[1] for x in options)
	for opt, desc in zip(opts, descs):
		twrap.initial_indent = pp.emph(opt.ljust(25))
		twrap.subsequent_indent = " " * 25
		result.append(twrap.fill(desc))
	return '\n'.join(result)


def format_filetype(path, fdesc, show_type=False, show_md5=False,
		show_timestamp=False):
	"""Format a path for printing.

	@type path: str
	@param path: the path
	@type fdesc: list
	@param fdesc: [file_type, timestamp, MD5 sum/symlink target]
		file_type is one of dev, dir, obj, sym.
		If file_type is dir, there is no timestamp or MD5 sum.
		If file_type is sym, fdesc[2] is the target of the symlink.
	@type show_type: bool
	@param show_type: if True, prepend the file's type to the formatted string
	@type show_md5: bool
	@param show_md5: if True, append MD5 sum to the formatted string
	@type show_timestamp: bool
	@param show_timestamp: if True, append time-of-creation after pathname
	@rtype: str
	@return: formatted pathname with optional added information
	"""

	ftype = fpath = stamp = md5sum = ""
	if fdesc[0] == "obj":
		ftype = "file"
		fpath = path
		stamp = format_timestamp(fdesc[1])
		md5sum = fdesc[2]
	elif fdesc[0] == "dir":
		ftype = "dir"
		fpath = pp.path(path)
	elif fdesc[0] == "sym":
		ftype = "sym"
		stamp = format_timestamp(fdesc[1])
		tgt = fdesc[2].split()[0]
		if CONFIG["piping"]:
			fpath = path
		else:
			fpath = pp.path_symlink(path + " -> " + tgt)
	elif fdesc[0] == "dev":
		ftype = "dev"
		fpath = path
	else:
		sys.stderr.write(
			pp.error("%s has unknown type: %s" % (path, fdesc[0]))
		)
	result = ""
	if show_type:
		result += "%4s " % ftype
	result += fpath
	if show_timestamp:
		result += "  " + stamp
	if show_md5:
		result += "  " + md5sum
	return result



def format_timestamp(timestamp):
	"""Format a timestamp into, e.g., '2009-01-31 21:19:44' format"""

	return time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(int(timestamp)))

class CpvValueWrapper(object):
	"""Format a cpv and linewrap pre-formatted values"""

	def __init__(self, cpv_width=None, width=None):
		self.cpv_width = cpv_width
		if width is None:
			width = gentoolkit.CONFIG['termWidth']
		self.twrap = TextWrapper(width=width)
		#self.init_indent = len(self.spacer)

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
		if self.cpv_width > 1:
			_cpv = pp.cpv(key+'.'*(self.cpv_width-len(key)))
			if not len(values):
				return _cpv
			self.twrap.initial_indent = _cpv
			self.twrap.subsequent_indent = " " * (self.cpv_width+1)
		else:
			_cpv = pp.cpv(key+' ')
			if not len(values):
				return _cpv
			self.twrap.initial_indent = _cpv
			self.twrap.subsequent_indent = " " * (len(key)+1)

		result.append(self.twrap.fill(values))
		return '\n'.join(result)


