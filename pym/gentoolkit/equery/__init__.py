# Copyright(c) 2009, Gentoo Foundation
#
# Licensed under the GNU General Public License, v2
#
# $Header: $

"""Gentoo package query tool"""

from __future__ import print_function

__all__ = (
	'format_options',
	'format_package_names',
	'mod_usage'
)
__docformat__ = 'epytext'
# version is dynamically set by distutils sdist
__version__ = "svn"

# =======
# Imports
# =======

import errno
import os
import sys
import time
from getopt import getopt, GetoptError

import portage

import gentoolkit
from gentoolkit import CONFIG
from gentoolkit import errors
from gentoolkit import pprinter as pp
from gentoolkit.textwrap_ import TextWrapper

__productname__ = "equery"
__authors__ = (
	'Karl Trygve Kalleberg - Original author',
	'Douglas Anderson - 0.3.0 author'
)

# =======
# Globals
# =======

NAME_MAP = {
	'b': 'belongs',
	'c': 'changes',
	'k': 'check',
	'd': 'depends',
	'g': 'depgraph',
	'f': 'files',
	'h': 'hasuse',
	'l': 'list_',
	'y': 'keywords',
	'a': 'has',
	'm': 'meta',
	's': 'size',
	'u': 'uses',
	'w': 'which'
}

# =========
# Functions
# =========

def print_help(with_description=True):
	"""Print description, usage and a detailed help message.

	@param with_description (bool): Option to print module's __doc__ or not
	"""

	if with_description:
		print(__doc__)
	print(main_usage())
	print()
	print(pp.globaloption("global options"))
	print(format_options((
		(" -h, --help", "display this help message"),
		(" -q, --quiet", "minimal output"),
		(" -C, --no-color", "turn off colors"),
		(" -N, --no-pipe", "turn off pipe detection"),
		(" -V, --version", "display version info")
	)))
	print()
	print(pp.command("modules") + " (" + pp.command("short name") + ")")
	print(format_options((
		(" (b)elongs", "list what package FILES belong to"),
		(" (c)hanges", "list changelog entries for ATOM"),
		(" chec(k)", "verify checksums and timestamps for PKG"),
		(" (d)epends", "list all packages directly depending on ATOM"),
		(" dep(g)raph", "display a tree of all dependencies for PKG"),
		(" (f)iles", "list all files installed by PKG"),
		(" h(a)s", "list all packages for matching ENVIRONMENT data stored in /var/db/pkg"),
		(" (h)asuse", "list all packages that have USE flag"),
		(" ke(y)words", "display keywords for specified PKG"),
		(" (l)ist", "list package matching PKG"),
		(" (m)eta", "display metadata about PKG"),
		(" (s)ize", "display total size of all files owned by PKG"),
		(" (u)ses", "display USE flags for PKG"),
		(" (w)hich", "print full path to ebuild for PKG")
	)))


def expand_module_name(module_name):
	"""Returns one of the values of NAME_MAP or raises KeyError"""

	if module_name == 'list':
		# list is a Python builtin type, so we must rename our module
		return 'list_'
	elif module_name in NAME_MAP.values():
		return module_name
	else:
		return NAME_MAP[module_name]


def format_options(options):
	"""Format module options.

	@type options: list
	@param options: [('option 1', 'description 1'), ('option 2', 'des... )]
	@rtype: str
	@return: formatted options string
	"""

	result = []
	twrap = TextWrapper(width=CONFIG['termWidth'])
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


def initialize_configuration():
	"""Setup the standard equery config"""

	# Get terminal size
	term_width = pp.output.get_term_size()[1]
	if term_width == -1:
		# get_term_size() failed. Set a sane default width:
		term_width = 80

	# Terminal size, minus a 1-char margin for text wrapping
	CONFIG['termWidth'] = term_width - 1

	# Guess color output
	if (CONFIG['color'] == -1 and (not sys.stdout.isatty() or
		os.getenv("NOCOLOR") in ("yes", "true")) or CONFIG['color'] == 0):
		pp.output.nocolor()

	if CONFIG['piping']:
		CONFIG['verbose'] = False

	CONFIG['debug'] = bool(os.getenv('DEBUG', False))


def main_usage():
	"""Return the main usage message for equery"""

	return "%(usage)s %(product)s [%(g_opts)s] %(mod_name)s [%(mod_opts)s]" % {
		'usage': pp.emph("Usage:"),
		'product': pp.productname(__productname__),
		'g_opts': pp.globaloption("global-options"),
		'mod_name': pp.command("module-name"),
		'mod_opts': pp.localoption("module-options")
	}


def mod_usage(mod_name="module", arg="pkgspec", optional=False):
	"""Provide a consistent usage message to the calling module.

	@type arg: string
	@param arg: what kind of argument the module takes (pkgspec, filename, etc)
	@type optional: bool
	@param optional: is the argument optional?
	"""

	return "%(usage)s: %(mod_name)s [%(opts)s] %(arg)s" % {
		'usage': pp.emph("Usage"),
		'mod_name': pp.command(mod_name),
		'opts': pp.localoption("options"),
		'arg': ("[%s]" % pp.emph(arg)) if optional else pp.emph(arg)
	}


def parse_global_options(global_opts, args):
	"""Parse global input args and return True if we should display help for
	the called module, else False (or display help and exit from here).
	"""

	need_help = False
	opts = (opt[0] for opt in global_opts)
	for opt in opts:
		if opt in ('-h', '--help'):
			if args:
				need_help = True
			else:
				print_help()
				sys.exit(0)
		elif opt in ('-q','--quiet'):
			CONFIG['quiet'] = True
		elif opt in ('-C', '--no-color', '--nocolor'):
			CONFIG['color'] = 0
			pp.output.nocolor()
		elif opt in ('-N', '--no-pipe'):
			CONFIG['piping'] = False
		elif opt in ('-V', '--version'):
			print_version()
			sys.exit(0)
		elif opt in ('--debug'):
			CONFIG['debug'] = True

	return need_help


def print_version():
	"""Print the version of this tool to the console."""

	print("%(product)s (%(version)s) - %(docstring)s" % {
		"product": pp.productname(__productname__),
		"version": __version__,
		"docstring": __doc__
	})


def split_arguments(args):
	"""Separate module name from module arguments"""

	return args.pop(0), args


def main():
	"""Parse input and run the program."""

	short_opts = "hqCNV"
	long_opts = (
		'help', 'quiet', 'nocolor', 'no-color', 'no-pipe', 'version', 'debug'
	)

	initialize_configuration()

	try:
		global_opts, args = getopt(sys.argv[1:], short_opts, long_opts)
	except GetoptError as err:
		sys.stderr.write(pp.error("Global %s" % err))
		print_help(with_description=False)
		sys.exit(2)

	# Parse global options
	need_help = parse_global_options(global_opts, args)

	# verbose is shorthand for the very common 'not quiet or piping'
	if CONFIG['quiet'] or CONFIG['piping']:
		CONFIG['verbose'] = False
	else:
		CONFIG['verbose'] = True

	try:
		module_name, module_args = split_arguments(args)
	except IndexError:
		print_help()
		sys.exit(2)

	if need_help:
		module_args.append('--help')

	try:
		expanded_module_name = expand_module_name(module_name)
	except KeyError:
		sys.stderr.write(pp.error("Unknown module '%s'" % module_name))
		print_help(with_description=False)
		sys.exit(2)

	try:
		loaded_module = __import__(
			expanded_module_name, globals(), locals(), [], -1
		)
		loaded_module.main(module_args)
	except portage.exception.AmbiguousPackageName as err:
		raise errors.GentoolkitAmbiguousPackage(err.args[0])
	except IOError as err:
		if err.errno != errno.EPIPE:
			raise

if __name__ == '__main__':
	main()
