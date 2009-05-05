# Copyright(c) 2009, Gentoo Foundation
#
# Licensed under the GNU General Public License, v2
#
# $Header: $

"""Print total size of files contained in a given package"""

__docformat__ = 'epytext'

# =======
# Imports
# =======

import sys
from getopt import gnu_getopt, GetoptError

import gentoolkit.pprinter as pp
from gentoolkit.equery import format_options, mod_usage, Config
from gentoolkit.helpers2 import do_lookup

# =======
# Globals
# =======

QUERY_OPTS = {
	"categoryFilter": None,
	"includeInstalled": False,
	"includePortTree": False,
	"includeOverlayTree": False,
	"includeMasked": True,
	"isRegex": False,
	"matchExact": False,
	"printMatchInfo": False,
	"sizeInBytes": False
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

	# Deprecation warning added 04/09: djanderson
	pp.print_warn("Default action for this module has changed in Gentoolkit 0.3.")
	pp.print_warn("-e, --exact-name is now the default behavior.")
	pp.print_warn("Use globbing to simulate the old behavior (see man equery).")
	pp.print_warn("Use '*' to check all installed packages.")
	print

	print mod_usage(mod_name="size")
	print
	print pp.command("options")
	print format_options((
		(" -h, --help", "display this help message"),
		(" -b, --bytes", "report size in bytes"),
		(" -c, --category CAT", "only search in the category CAT"),
		(" -f, --full-regex", "query is a regular expression")
	))


def display_size(match_set):
	"""Display the total size of all accessible files owned by packages.

	@type match_set: list
	@param match_set: package cat/pkg-ver strings
	"""

	for pkg in match_set:
		(size, files, uncounted) = pkg.size()

		if Config["piping"]:
			info = "%s: total(%d), inaccessible(%d), size(%s)"
			print info % (pkg.cpv, files, uncounted, size)
		else:
			print " * %s" % pp.cpv(pkg.cpv)
			print "Total files : %s".rjust(25) % pp.number(str(files))

			if uncounted:
				pp.print_info(0, "Inaccessible files : %s".rjust(25) %
					pp.number(str(uncounted)))

			if QUERY_OPTS["sizeInBytes"]:
				size_str = pp.number(str(size))
			else:
				size_str = "%s %s" % format_bytes(size)

			pp.print_info(0, "Total size  : %s".rjust(25) % size_str)


def format_bytes(bytes_, precision=2):
	"""Format bytes into human-readable format (IEC naming standard).

	@see: http://mail.python.org/pipermail/python-list/2008-August/503423.html
	@rtype: tuple
	@return: (str(num), str(label))
	"""

	labels = (
		(1<<40L, 'TiB'),
		(1<<30L, 'GiB'),
		(1<<20L, 'MiB'),
		(1<<10L, 'KiB'),
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
	"""Parse module options and update GLOBAL_OPTS"""

	opts = (x[0] for x in module_opts)
	posargs = (x[1] for x in module_opts)
	for opt, posarg in zip(opts, posargs):
		if opt in ('-h', '--help'):
			print_help()
			sys.exit(0)
		elif opt in ('-b', '--bytes'):
			QUERY_OPTS["sizeInBytes"] = True
		elif opt in ('-c', '--category'):
			QUERY_OPTS['categoryFilter'] = posarg
		elif opt in ('-e', '--exact-name'):
			pp.print_warn("-e, --exact-name is now default.")
			pp.print_warn("Use globbing to simulate the old behavior.")
			print
		elif opt in ('-f', '--full-regex'):
			QUERY_OPTS['isRegex'] = True


def main(input_args):
	"""Parse input and run the program"""

	# -e, --exact-name is no longer needed. Kept for compatibility.
	# 04/09 djanderson
	short_opts = "hbc:fe"
	long_opts = ('help', 'bytes', 'category=', 'full-regex', 'exact-name')

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

		display_size(matches)

		first_run = False
