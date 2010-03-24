# Copyright(c) 2009, Gentoo Foundation
#
# Licensed under the GNU General Public License, v2
#
# $Header: $

"""Print total size of files contained in a given package"""

from __future__ import print_function

__docformat__ = 'epytext'

# =======
# Imports
# =======

import sys
from getopt import gnu_getopt, GetoptError

import gentoolkit.pprinter as pp
from gentoolkit.equery import format_options, mod_usage, CONFIG
from gentoolkit.query import Query

# =======
# Globals
# =======

QUERY_OPTS = {
	"in_installed": True,
	"in_porttree": False,
	"in_overlay": False,
	"include_masked": True,
	"is_regex": False,
	"show_progress": False,
	"size_in_bytes": False
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

	print(mod_usage(mod_name="size"))
	print()
	print(pp.command("options"))
	print(format_options((
		(" -h, --help", "display this help message"),
		(" -b, --bytes", "report size in bytes"),
		(" -f, --full-regex", "query is a regular expression")
	)))


def display_size(match_set):
	"""Display the total size of all accessible files owned by packages.

	@type match_set: list
	@param match_set: package cat/pkg-ver strings
	"""

	for pkg in match_set:
		size, files, uncounted = pkg.size()

		if CONFIG['verbose']:
			pp.uprint(" * %s" % pp.cpv(str(pkg.cpv)))
			print("Total files : %s".rjust(25) % pp.number(str(files)))

			if uncounted:
				print(("Inaccessible files : %s".rjust(25) %
					pp.number(str(uncounted))))

			if QUERY_OPTS["size_in_bytes"]:
				size_str = pp.number(str(size))
			else:
				size_str = "%s %s" % format_bytes(size)

			print("Total size  : %s".rjust(25) % size_str)
		else:
			info = "%s: total(%d), inaccessible(%d), size(%s)"
			pp.uprint(info % (str(pkg.cpv), files, uncounted, size))


def format_bytes(bytes_, precision=2):
	"""Format bytes into human-readable format (IEC naming standard).

	@see: http://mail.python.org/pipermail/python-list/2008-August/503423.html
	@rtype: tuple
	@return: (str(num), str(label))
	"""

	labels = (
		(1<<40, 'TiB'),
		(1<<30, 'GiB'),
		(1<<20, 'MiB'),
		(1<<10, 'KiB'),
		(1, 'bytes')
	)

	if bytes_ == 0:
		return (pp.number('0'), 'bytes')
	elif bytes_ == 1:
		return (pp.number('1'), 'byte')

	for factor, label in labels:
		if not bytes_ >= factor:
			continue

		float_split = str(bytes_/float(factor)).split('.')
		integer = float_split[0]
		decimal = float_split[1]
		if int(decimal[0:precision]):
			float_string = '.'.join([integer, decimal[0:precision]])
		else:
			float_string = integer

		return (pp.number(float_string), label)


def parse_module_options(module_opts):
	"""Parse module options and update QUERY_OPTS"""

	opts = (x[0] for x in module_opts)
	for opt in opts:
		if opt in ('-h', '--help'):
			print_help()
			sys.exit(0)
		elif opt in ('-b', '--bytes'):
			QUERY_OPTS["size_in_bytes"] = True
		elif opt in ('-e', '--exact-name'):
			sys.stderr.write(pp.warn("-e, --exact-name is now default."))
			warning = pp.warn("Use globbing to simulate the old behavior.")
			sys.stderr.write(warning)
			print()
		elif opt in ('-f', '--full-regex'):
			QUERY_OPTS['is_regex'] = True


def main(input_args):
	"""Parse input and run the program"""

	# -e, --exact-name is no longer needed. Kept for compatibility.
	# 04/09 djanderson
	short_opts = "hbfe"
	long_opts = ('help', 'bytes', 'full-regex', 'exact-name')

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
			sys.stderr.write(pp.error("No package found matching %s" % query))

		matches.sort()

		display_size(matches)

		first_run = False

# vim: set ts=4 sw=4 tw=79:
