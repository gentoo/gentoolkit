# Copyright(c) 2009, Gentoo Foundation
#
# Licensed under the GNU General Public License, v2
#
# $Header: $

"""List files owned by a given package"""

__docformat__ = 'epytext'

# =======
# Imports
# =======

import os
import sys
from getopt import gnu_getopt, GetoptError

import gentoolkit
import gentoolkit.pprinter as pp
from gentoolkit.equery import format_filetype, format_options, mod_usage, \
	Config
from gentoolkit.helpers2 import do_lookup

# =======
# Globals
# =======

QUERY_OPTS = {
	"categoryFilter": None,
	"includeInstalled": True,
	"includePortTree": False,
	"includeOverlayTree": False,
	"includeMasked": True,
	"isRegex": False,
	"matchExact": True,
	"outputTree": False,
	"printMatchInfo": (not Config['quiet']),
	"showType": False,
	"showTimestamp": False,
	"showMD5": False,
	"typeFilter": None
}

FILTER_RULES = ('dir', 'obj', 'sym', 'dev', 'path', 'conf', 'cmd', 'doc',
	'man', 'info')

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
	print mod_usage(mod_name="files")
	print
	print pp.command("options")
	print format_options((
		(" -h, --help", "display this help message"),
		(" -m, --md5sum", "include MD5 sum in output"),
		(" -s, --timestamp", "include timestamp in output"),
		(" -t, --type", "include file type in output"),
		("     --tree", "display results in a tree (turns off other options)"),
		(" -f, --filter=RULES", "filter output by file type"),
		("              RULES", 
			"a comma-separated list (no spaces); choose from:")
	))
	print " " * 24, ', '.join(pp.emph(x) for x in FILTER_RULES)


def display_files(contents):
	"""Display the content of an installed package.

	@see: gentoolkit.package.Package.get_contents
	@type contents: dict
	@param contents: {'path': ['filetype', ...], ...}
	"""

	filenames = contents.keys()
	filenames.sort()
	last = []

	for name in filenames:
		if QUERY_OPTS["outputTree"]:
			basename = name.split("/")[1:]
			if contents[name][0] == "dir":
				if len(last) == 0:
					last = basename
					print pp.path(" /" + basename[0])
					continue
				numol = 0
				for i, directory in enumerate(basename):
					try:
						if directory in last[i]:
							numol = i + 1
							continue
					# W0704: Except doesn't do anything
					# pylint: disable-msg=W0704
					except IndexError:
						pass
					last = basename
					if len(last) == 1:
						print pp.path(" " + last[0])
						continue
					ind = " " * (numol * 3)
					print pp.path(ind + "> " + "/" + last[-1])
			elif contents[name][0] == "sym":
				print pp.path(" " * (len(last) * 3) + "+"),
				print pp.path_symlink(basename[-1] + " -> " + contents[name][2])
			else: 
				print pp.path(" " * (len(last) * 3) + "+ ") + basename[-1]
		else:
			pp.print_info(0, format_filetype(
				name,
				contents[name],
				show_type=QUERY_OPTS["showType"],
				show_md5=QUERY_OPTS["showMD5"],
				show_timestamp=QUERY_OPTS["showTimestamp"]))


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
	conf_path = gentoolkit.settings["CONFIG_PROTECT"].split()
	conf_path = tuple(os.path.normpath(x) for x in conf_path)
	conf_mask_path = gentoolkit.settings["CONFIG_PROTECT_MASK"].split()
	conf_mask_path = tuple(os.path.normpath(x) for x in conf_mask_path)
	for path in contents:
		if contents[path][0] == 'obj' and path.startswith(conf_path):
			if not path.startswith(conf_mask_path):
				filtered_content[path] = contents[path]

	return filtered_content


def filter_contents(contents):
	"""Filter files by type if specified by the user.

	@see: gentoolkit.package.Package.get_contents
	@type contents: dict
	@param contents: {'path': ['filetype', ...], ...}
	@rtype: dict
	@return: contents with unrequested filetypes stripped
	"""

	if QUERY_OPTS['typeFilter']:
		content_filter = QUERY_OPTS['typeFilter']
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
	
	return filtered_content


def parse_module_options(module_opts):
	"""Parse module options and update GLOBAL_OPTS"""

	content_filter = []
	opts = (x[0] for x in module_opts)
	posargs = (x[1] for x in module_opts)
	for opt, posarg in zip(opts, posargs):
		if opt in ('-h', '--help'):
			print_help()
			sys.exit(0)
		elif opt in ('-e', '--exact-name'):
			QUERY_OPTS["matchExact"] = True
		elif opt in ('-m', '--md5sum'):
			QUERY_OPTS["showMD5"] = True
		elif opt in ('-s', '--timestamp'):
			QUERY_OPTS["showTimestamp"] = True
		elif opt in ('-t', '--type'):
			QUERY_OPTS["showType"] = True
		elif opt in ('--tree'):
			QUERY_OPTS["outputTree"] = True
		elif opt in ('-f', '--filter'):
			f_split = posarg.split(',')
			content_filter.extend(x.lstrip('=') for x in f_split)
			for rule in content_filter:
				if not rule in FILTER_RULES:
					pp.print_error("Invalid filter rule '%s'" % rule)
					print
					print_help(with_description=False)
					sys.exit(2)
			QUERY_OPTS["typeFilter"] = content_filter


def main(input_args):
	"""Parse input and run the program"""

	short_opts = "hemstf:"
	long_opts = ('help', 'exact-name', 'md5sum', 'timestamp', 'type', 'tree',
		'filter=') 

	try:
		module_opts, queries = gnu_getopt(input_args, short_opts, long_opts)
	except GetoptError, err:
		pp.print_error("Module %s" % err)
		print
		print_help(with_description=False)
		sys.exit(2)

	parse_module_options(module_opts)
	
	if not queries:
		print_help()
		sys.exit(2)

	# Turn off filtering for tree output
	if QUERY_OPTS["outputTree"]:
		QUERY_OPTS["typeFilter"] = None

	#
	# Output files
	#

	first_run = True
	for query in queries:
		if not first_run:
			print

		matches = do_lookup(query, QUERY_OPTS)

		if not matches:
			pp.print_error("No matching packages found for %s" % query)

		for pkg in matches:
			if Config['verbose']:
				print " * Contents of %s:" % pp.cpv(pkg.cpv)

			contents = pkg.get_contents()
			display_files(filter_contents(contents))

		first_run = False
