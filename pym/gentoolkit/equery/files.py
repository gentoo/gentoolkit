# Copyright(c) 2009, Gentoo Foundation
#
# Licensed under the GNU General Public License, v2
#
# $Header: $

"""List files owned by a given package."""

from __future__ import print_function

__docformat__ = 'epytext'

# =======
# Imports
# =======

import os
import sys
from getopt import gnu_getopt, GetoptError

import portage

import gentoolkit.pprinter as pp
from gentoolkit.equery import (format_filetype, format_options, mod_usage,
	CONFIG)
from gentoolkit.query import Query

# =======
# Globals
# =======

QUERY_OPTS = {
	"in_installed": True,
	"in_porttree": False,
	"in_overlay": False,
	"include_masked": True,
	"output_tree": False,
	"show_progress": (not CONFIG['quiet']),
	"show_type": False,
	"show_timestamp": False,
	"show_MD5": False,
	"type_filter": None
}

FILTER_RULES = (
	'dir', 'obj', 'sym', 'dev', 'path', 'conf', 'cmd', 'doc', 'man', 'info',
	'fifo'
)

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
	print(mod_usage(mod_name="files"))
	print()
	print(pp.command("options"))
	print(format_options((
		(" -h, --help", "display this help message"),
		(" -m, --md5sum", "include MD5 sum in output"),
		(" -s, --timestamp", "include timestamp in output"),
		(" -t, --type", "include file type in output"),
		("     --tree", "display results in a tree (turns off other options)"),
		(" -f, --filter=RULES", "filter output by file type"),
		("              RULES",
			"a comma-separated list (no spaces); choose from:")
	)))
	print(" " * 24, ', '.join(pp.emph(x) for x in FILTER_RULES))


# R0912: *Too many branches (%s/%s)*
# pylint: disable-msg=R0912
def display_files(contents):
	"""Display the content of an installed package.

	@see: gentoolkit.package.Package.parsed_contents
	@type contents: dict
	@param contents: {'path': ['filetype', ...], ...}
	"""

	filenames = list(contents.keys())
	filenames.sort()
	last = []

	for name in filenames:
		if QUERY_OPTS["output_tree"]:
			dirdepth = name.count('/')
			indent = " "
			if dirdepth == 2:
				indent = "   "
			elif dirdepth > 2:
				indent = "   " * (dirdepth - 1)

			basename = name.rsplit("/", dirdepth - 1)
			if contents[name][0] == "dir":
				if len(last) == 0:
					last = basename
					pp.uprint(pp.path(indent + basename[0]))
					continue
				for i, directory in enumerate(basename):
					try:
						if directory in last[i]:
							continue
					except IndexError:
						pass
					last = basename
					if len(last) == 1:
						pp.uprint(pp.path(indent + last[0]))
						continue
					pp.uprint(pp.path(indent + "> /" + last[-1]))
			elif contents[name][0] == "sym":
				pp.uprint(pp.path(indent + "+"), end=' ')
				pp.uprint(pp.path_symlink(basename[-1] + " -> " +
					contents[name][2]))
			else:
				pp.uprint(pp.path(indent + "+ ") + basename[-1])
		else:
			pp.uprint(format_filetype(
				name,
				contents[name],
				show_type=QUERY_OPTS["show_type"],
				show_md5=QUERY_OPTS["show_MD5"],
				show_timestamp=QUERY_OPTS["show_timestamp"]
			))


def filter_by_doc(contents, content_filter):
	"""Return a copy of content filtered by documentation."""

	filtered_content = {}
	for doctype in ('doc' ,'man' ,'info'):
		# List only files from /usr/share/{doc,man,info}
		if doctype in content_filter:
			docpath = os.path.join(os.sep, 'usr', 'share', doctype)
			for path in contents:
				if contents[path][0] == 'obj' and path.startswith(docpath):
					filtered_content[path] = contents[path]

	return filtered_content


def filter_by_command(contents):
	"""Return a copy of content filtered by executable commands."""

	filtered_content = {}
	userpath = os.environ["PATH"].split(os.pathsep)
	userpath = [os.path.normpath(x) for x in userpath]
	for path in contents:
		if (contents[path][0] in ['obj', 'sym'] and
			os.path.dirname(path) in userpath):
			filtered_content[path] = contents[path]

	return filtered_content


def filter_by_path(contents):
	"""Return a copy of content filtered by file paths."""

	filtered_content = {}
	paths = list(reversed(sorted(contents.keys())))
	while paths:
		basepath = paths.pop()
		if contents[basepath][0] == 'dir':
			check_subdirs = False
			for path in paths:
				if (contents[path][0] != "dir" and
					os.path.dirname(path) == basepath):
					filtered_content[basepath] = contents[basepath]
					check_subdirs = True
					break
			if check_subdirs:
				while (paths and paths[-1].startswith(basepath)):
					paths.pop()

	return filtered_content


def filter_by_conf(contents):
	"""Return a copy of content filtered by configuration files."""

	filtered_content = {}
	conf_path = portage.settings["CONFIG_PROTECT"].split()
	conf_path = tuple(os.path.normpath(x) for x in conf_path)
	conf_mask_path = portage.settings["CONFIG_PROTECT_MASK"].split()
	conf_mask_path = tuple(os.path.normpath(x) for x in conf_mask_path)
	for path in contents:
		if contents[path][0] == 'obj' and path.startswith(conf_path):
			if not path.startswith(conf_mask_path):
				filtered_content[path] = contents[path]

	return filtered_content


def filter_by_fifo(contents):
	"""Return a copy of content filtered by fifo entries."""

	filtered_content = {}
	for path in contents:
		if contents[path][0] in ['fif']:
			filtered_content[path] = contents[path]

	return filtered_content


def filter_contents(contents):
	"""Filter files by type if specified by the user.

	@see: gentoolkit.package.Package.parsed_contents
	@type contents: dict
	@param contents: {'path': ['filetype', ...], ...}
	@rtype: dict
	@return: contents with unrequested filetypes stripped
	"""

	if QUERY_OPTS['type_filter']:
		content_filter = QUERY_OPTS['type_filter']
	else:
		return contents

	filtered_content = {}
	if frozenset(('dir', 'obj', 'sym', 'dev')).intersection(content_filter):
		# Filter elements by type (as recorded in CONTENTS)
		for path in contents:
			if contents[path][0] in content_filter:
				filtered_content[path] = contents[path]
	if "cmd" in content_filter:
		filtered_content.update(filter_by_command(contents))
	if "path" in content_filter:
		filtered_content.update(filter_by_path(contents))
	if "conf" in content_filter:
		filtered_content.update(filter_by_conf(contents))
	if frozenset(('doc' ,'man' ,'info')).intersection(content_filter):
		filtered_content.update(filter_by_doc(contents, content_filter))
	if "fifo" in content_filter:
		filtered_content.update(filter_by_fifo(contents))

	return filtered_content


def parse_module_options(module_opts):
	"""Parse module options and update QUERY_OPTS"""

	content_filter = []
	opts = (x[0] for x in module_opts)
	posargs = (x[1] for x in module_opts)
	for opt, posarg in zip(opts, posargs):
		if opt in ('-h', '--help'):
			print_help()
			sys.exit(0)
		elif opt in ('-m', '--md5sum'):
			QUERY_OPTS["show_MD5"] = True
		elif opt in ('-s', '--timestamp'):
			QUERY_OPTS["show_timestamp"] = True
		elif opt in ('-t', '--type'):
			QUERY_OPTS["show_type"] = True
		elif opt in ('--tree'):
			QUERY_OPTS["output_tree"] = True
		elif opt in ('-f', '--filter'):
			f_split = posarg.split(',')
			content_filter.extend(x.lstrip('=') for x in f_split)
			for rule in content_filter:
				if not rule in FILTER_RULES:
					sys.stderr.write(
						pp.error("Invalid filter rule '%s'" % rule)
					)
					print()
					print_help(with_description=False)
					sys.exit(2)
			QUERY_OPTS["type_filter"] = content_filter


def main(input_args):
	"""Parse input and run the program"""

	# -e, --exact-name is legacy option. djanderson '09
	short_opts = "hemstf:"
	long_opts = ('help', 'exact-name', 'md5sum', 'timestamp', 'type', 'tree',
		'filter=')

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

	# Turn off filtering for tree output
	if QUERY_OPTS["output_tree"]:
		QUERY_OPTS["type_filter"] = None

	#
	# Output files
	#

	first_run = True
	for query in queries:
		if not first_run:
			print()

		matches = Query(query).smart_find(**QUERY_OPTS)

		if not matches:
			sys.stderr.write(
				pp.error("No matching packages found for %s" % query)
			)

		matches.sort()

		for pkg in matches:
			if CONFIG['verbose']:
				pp.uprint(" * Contents of %s:" % pp.cpv(str(pkg.cpv)))

			contents = pkg.parsed_contents()
			display_files(filter_contents(contents))

		first_run = False

# vim: set ts=4 sw=4 tw=79:
