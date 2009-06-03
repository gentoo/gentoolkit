# Copyright(c) 2009, Gentoo Foundation
#
# Licensed under the GNU General Public License, v2
#
# $Header: $

"""Check timestamps and MD5sums for files owned by a given installed package"""

__docformat__ = 'epytext'

# =======
# Imports
# =======

import os
import sys
from getopt import gnu_getopt, GetoptError

try:
	import portage.checksum as checksum
except ImportError:
	import portage_checksum as checksum

import gentoolkit.pprinter as pp
from gentoolkit.equery import format_options, mod_usage, Config
from gentoolkit.helpers2 import do_lookup

# =======
# Globals
# =======

QUERY_OPTS = {
	"categoryFilter": None,
	"includeInstalled": False,
	"includeOverlayTree": False,
	"includePortTree": False,
	"checkMD5sum": True,
	"checkTimestamp" : True,
	"isRegex": False,
	"matchExact": True,
	"printMatchInfo": False,
	"showSummary" : True,
	"showPassedFiles" : False,
	"showFailedFiles" : True
}

# =========
# Functions
# =========

def print_help(with_description=True):
	"""Print description, usage and a detailed help message.
	
	@type with_description: bool
	@param with_description: if true, print module's __doc__ string
	"""

	if with_description:
		print __doc__.strip()
		print

	# Deprecation warning added by djanderson, 12/2008
	pp.print_warn("Default action for this module has changed in Gentoolkit 0.3.")
	pp.print_warn("Use globbing to simulate the old behavior (see man equery).")
	pp.print_warn("Use '*' to check all installed packages.")
	print

	print mod_usage(mod_name="check")
	print
	print pp.command("options")
	print format_options((
		(" -h, --help", "display this help message"),
		(" -c, --category CAT", "only check files from packages in CAT"),
		(" -f, --full-regex", "query is a regular expression"),
	))


def parse_module_options(module_opts):
	"""Parse module options and update GLOBAL_OPTS"""

	opts = (x[0] for x in module_opts)
	posargs = (x[1] for x in module_opts)
	for opt, posarg in zip(opts, posargs):
		if opt in ('-h', '--help'):
			print_help()
			sys.exit(0)
		elif opt in ('-c', '--category'):
			QUERY_OPTS['categoryFilter'] = posarg
		elif opt in ('-f', '--full-regex'):
			QUERY_OPTS['isRegex'] = True


def run_checks(files):
	"""Run some basic sanity checks on a package's contents.

	If the file type (ftype) is not a directory or symlink, optionally
	verify MD5 sums or mtimes via verify_obj().

	@see: gentoolkit.packages.get_contents()
	@type files: dict
	@param files: in form {'PATH': ['TYPE', 'TIMESTAMP', 'MD5SUM']}
	@rtype: tuple
	@return:
		passed (int): number of files that passed all checks
		checked (int): number of files checked
		errs (list): check errors' descriptions
	"""

	checked = 0
	passed = 0
	errs = []
	for cfile in files:
		checked += 1
		ftype = files[cfile][0]
		if not os.path.exists(cfile):
			errs.append("%s does not exist" % cfile)
			continue
		elif ftype == "dir":
			if not os.path.isdir(cfile):
				err = "%(cfile)s exists, but is not a directory"
				errs.append(err % locals())
				continue
		elif ftype == "obj":
			new_errs = verify_obj(files, cfile, errs)
			if new_errs != errs:
				errs = new_errs
				continue
		elif ftype == "sym":
			target = files[cfile][2].strip()
			if not os.path.islink(cfile):
				err = "%(cfile)s exists, but is not a symlink"
				errs.append(err % locals())
				continue
			tgt = os.readlink(cfile)
			if tgt != target:
				err = "%(cfile)s does not point to %(target)s"
				errs.append(err % locals())
				continue
		else:
			err = "%(cfile)s has unknown type %(ftype)s"
			errs.append(err % locals())
			continue
		passed += 1

	return passed, checked, errs


def verify_obj(files, cfile, errs):
	"""Verify the MD5 sum and/or mtime and return any errors."""

	if QUERY_OPTS["checkMD5sum"]:
		md5sum = files[cfile][2]
		try: 
			cur_checksum = checksum.perform_md5(cfile, calc_prelink=1)
		except IOError:
			err = "Insufficient permissions to read %(cfile)s"
			errs.append(err % locals())
			return errs
		if cur_checksum != md5sum:
			err = "%(cfile)s has incorrect MD5sum"
			errs.append(err % locals())
			return errs
	if QUERY_OPTS["checkTimestamp"]:
		mtime = int(files[cfile][1])
		st_mtime = os.lstat(cfile).st_mtime
		if st_mtime != mtime:
			err = "%(cfile)s has wrong mtime (is %(st_mtime)d, " + \
				"should be %(mtime)d)"
			errs.append(err % locals())
			return errs

	return errs


def main(input_args):
	"""Parse input and run the program"""

	short_opts = "hac:f"
	long_opts = ('help', 'all', 'category=', 'full-regex')

	try:
		module_opts, queries = gnu_getopt(input_args, short_opts, long_opts)
	except GetoptError, err:
		pp.print_error("Module %s" % err)
		print
		print_help(with_description=False)
		sys.exit(2)

	parse_module_options(module_opts)
	
	if not queries and not QUERY_OPTS["includeInstalled"]:
		print_help()
		sys.exit(2)
	elif queries and not QUERY_OPTS["includeInstalled"]:
		QUERY_OPTS["includeInstalled"] = True
	elif QUERY_OPTS["includeInstalled"]:
		queries = ["*"]

	#
	# Output
	#

	first_run = True
	for query in queries:
		if not first_run:
			print

		matches = do_lookup(query, QUERY_OPTS)

		if not matches:
			pp.print_error("No package found matching %s" % query)

		matches.sort()

		for pkg in matches:
			if Config['verbose']:
				print " * Checking %s ..." % pp.emph(pkg.cpv)
			else:
				print "%s:" % pkg.cpv

			passed, checked, errs = run_checks(pkg.get_contents())

			if Config['verbose']:
				for err in errs:
					pp.print_error(err)

			passed = pp.number(str(passed))
			checked = pp.number(str(checked))
			info = "   %(passed)s out of %(checked)s files passed"
			print info % locals()

			first_run = False
