# Copyright(c) 2009, Gentoo Foundation
#
# Licensed under the GNU General Public License, v2
#
# $Header: $

"""Checks timestamps and MD5 sums for files owned by a given installed package"""

from __future__ import print_function

__docformat__ = 'epytext'

# =======
# Imports
# =======

import os
import sys
from functools import partial
from getopt import gnu_getopt, GetoptError

import portage.checksum as checksum

import gentoolkit.pprinter as pp
from gentoolkit import errors
from gentoolkit.equery import format_options, mod_usage, CONFIG
from gentoolkit.query import Query

# =======
# Globals
# =======

QUERY_OPTS = {
	"in_installed": True,
	"in_porttree": False,
	"in_overlay": False,
	"check_MD5sum": True,
	"check_timestamp" : True,
	"is_regex": False,
	"only_failures": False,
	"show_progress": False,
}

# =======
# Classes
# =======

class VerifyContents(object):
	"""Verify installed packages' CONTENTS files.

	The CONTENTS file contains timestamps and MD5 sums for each file owned
	by a package.
	"""
	def __init__(self, printer_fn=None):
		"""Create a VerifyObjects instance.

		@type printer_fn: callable
		@param printer_fn: if defined, will be applied to each result as found
		"""
		self.check_sums = True
		self.check_timestamps = True
		self.printer_fn = printer_fn

		self.is_regex = False

	def __call__(
		self,
		pkgs,
		is_regex=False,
		check_sums=True,
		check_timestamps=True
	):
		self.is_regex = is_regex
		self.check_sums = check_sums
		self.check_timestamps = check_timestamps

		result = {}
		for pkg in pkgs:
			# _run_checks returns tuple(n_passed, n_checked, err)
			check_results = self._run_checks(pkg.parsed_contents())
			result[pkg.cpv] = check_results
			if self.printer_fn is not None:
				self.printer_fn(pkg.cpv, check_results)

		return result

	def _run_checks(self, files):
		"""Run some basic sanity checks on a package's contents.

		If the file type (ftype) is not a directory or symlink, optionally
		verify MD5 sums or mtimes via L{self._verify_obj}.

		@see: gentoolkit.packages.get_contents()
		@type files: dict
		@param files: in form {'PATH': ['TYPE', 'TIMESTAMP', 'MD5SUM']}
		@rtype: tuple
		@return:
			n_passed (int): number of files that passed all checks
			n_checked (int): number of files checked
			errs (list): check errors' descriptions
		"""
		n_checked = 0
		n_passed = 0
		errs = []
		for cfile in files:
			n_checked += 1
			ftype = files[cfile][0]
			real_cfile = os.environ.get('ROOT', '') + cfile
			if not os.path.exists(real_cfile):
				errs.append("%s does not exist" % cfile)
				continue
			elif ftype == "dir":
				if not os.path.isdir(real_cfile):
					err = "%(cfile)s exists, but is not a directory"
					errs.append(err % locals())
					continue
			elif ftype == "obj":
				obj_errs = self._verify_obj(files, cfile, real_cfile, errs)
				if len(obj_errs) > len(errs):
					errs = obj_errs[:]
					continue
			elif ftype == "sym":
				target = files[cfile][2].strip()
				if not os.path.islink(real_cfile):
					err = "%(cfile)s exists, but is not a symlink"
					errs.append(err % locals())
					continue
				tgt = os.readlink(real_cfile)
				if tgt != target:
					err = "%(cfile)s does not point to %(target)s"
					errs.append(err % locals())
					continue
			else:
				err = "%(cfile)s has unknown type %(ftype)s"
				errs.append(err % locals())
				continue
			n_passed += 1

		return n_passed, n_checked, errs

	def _verify_obj(self, files, cfile, real_cfile, errs):
		"""Verify the MD5 sum and/or mtime and return any errors."""

		obj_errs = errs[:]
		if self.check_sums:
			md5sum = files[cfile][2]
			try:
				cur_checksum = checksum.perform_md5(real_cfile, calc_prelink=1)
			except IOError:
				err = "Insufficient permissions to read %(cfile)s"
				obj_errs.append(err % locals())
				return obj_errs
			if cur_checksum != md5sum:
				err = "%(cfile)s has incorrect MD5sum"
				obj_errs.append(err % locals())
				return obj_errs
		if self.check_timestamps:
			mtime = int(files[cfile][1])
			st_mtime = int(os.lstat(real_cfile).st_mtime)
			if st_mtime != mtime:
				err = (
					"%(cfile)s has wrong mtime (is %(st_mtime)d, should be "
					"%(mtime)d)"
				)
				obj_errs.append(err % locals())
				return obj_errs

		return obj_errs

# =========
# Functions
# =========

def print_help(with_description=True):
	"""Print description, usage and a detailed help message.

	@type with_description: bool
	@param with_description: if true, print module's __doc__ string
	"""

	if with_description:
		print(__doc__.strip())
		print()

	# Deprecation warning added by djanderson, 12/2008
	depwarning = (
		"Default action for this module has changed in Gentoolkit 0.3.",
		"Use globbing to simulate the old behavior (see man equery).",
		"Use '*' to check all installed packages.",
		"Use 'foo-bar/*' to filter by category."
	)
	for line in depwarning:
		sys.stderr.write(pp.warn(line))
	print()

	print(mod_usage(mod_name="check"))
	print()
	print(pp.command("options"))
	print(format_options((
		(" -h, --help", "display this help message"),
		(" -f, --full-regex", "query is a regular expression"),
		(" -o, --only-failures", "only display packages that do not pass"),
	)))


def checks_printer(cpv, data, verbose=True, only_failures=False):
	"""Output formatted results of pkg file(s) checks"""
	seen = []

	n_passed, n_checked, errs = data
	n_failed = n_checked - n_passed
	if only_failures and not n_failed:
		return
	else:
		if verbose:
			if not cpv in seen:
				pp.uprint("* Checking %s ..." % (pp.emph(str(cpv))))
				seen.append(cpv)
		else:
			pp.uprint("%s:" % cpv, end=' ')

	if verbose:
		for err in errs:
			sys.stderr.write(pp.error(err))

	if verbose:
		n_passed = pp.number(str(n_passed))
		n_checked = pp.number(str(n_checked))
		info = "   %(n_passed)s out of %(n_checked)s files passed"
		print(info % locals())
		print()
	else:
		print("failed(%s)" % n_failed)


def parse_module_options(module_opts):
	"""Parse module options and update QUERY_OPTS"""

	opts = (x[0] for x in module_opts)
	for opt in opts:
		if opt in ('-h', '--help'):
			print_help()
			sys.exit(0)
		elif opt in ('-f', '--full-regex'):
			QUERY_OPTS['is_regex'] = True
		elif opt in ('-o', '--only-failures'):
			QUERY_OPTS['only_failures'] = True


def main(input_args):
	"""Parse input and run the program"""

	short_opts = "hof"
	long_opts = ('help', 'only-failures', 'full-regex')

	try:
		module_opts, queries = gnu_getopt(input_args, short_opts, long_opts)
	except GetoptError as err:
		sys.stderr.write(pp.error("Module %s" % err))
		print()
		print_help(with_description=False)
		sys.exit(2)

	parse_module_options(module_opts)

	if not queries:
		print_help()
		sys.exit(2)

	first_run = True
	for query in (Query(x, QUERY_OPTS['is_regex']) for x in queries):
		if not first_run:
			print()

		matches = query.smart_find(**QUERY_OPTS)

		if not matches:
			raise errors.GentoolkitNoMatches(query, in_installed=True)

		matches.sort()

		printer = partial(
			checks_printer,
			verbose=CONFIG['verbose'],
			only_failures=QUERY_OPTS['only_failures']
		)
		check = VerifyContents(printer_fn=printer)
		check(matches)

		first_run = False

# vim: set ts=4 sw=4 tw=79:
