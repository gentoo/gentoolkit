# Copyright(c) 2009, Gentoo Foundation
#
# Licensed under the GNU General Public License, v2
#
# $Header: $

"""Display USE flags for a given package"""

# Move to imports section when Python 2.6 is stable
from __future__ import with_statement

__docformat__ = 'epytext'

# =======
# Imports
# =======

import os
import re
import sys
from getopt import gnu_getopt, GetoptError
from glob import glob
import xml.etree.cElementTree as ET

from portage.util import unique_array

import gentoolkit
import gentoolkit.pprinter as pp
from gentoolkit import errors
from gentoolkit.equery import format_options, mod_usage, Config
from gentoolkit.helpers2 import compare_package_strings, find_best_match, \
	find_packages
from gentoolkit.textwrap_ import TextWrapper

# =======
# Globals
# =======

QUERY_OPTS = {"allVersions" : False}

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
	print mod_usage(mod_name=__name__.split('.')[-1])
	print
	print pp.command("options")
	print format_options((
		(" -h, --help", "display this help message"),
		(" -a, --all", "include all package versions")
	))


def display_useflags(output):
	"""Print USE flag descriptions and statuses.

	@type output: list
	@param output: [(inuse, inused, flag, desc, restrict), ...]
		 inuse (int) = 0 or 1; if 1, flag is set in make.conf
		 inused (int) = 0 or 1; if 1, package is installed with flag enabled
		 flag (str) = the name of the USE flag
		 desc (str) = the flag's description
		 restrict (str) = corresponds to the text of restrict in metadata
	"""

	maxflag_len = len(max([t[2] for t in output], key=len))

	twrap = TextWrapper()
	twrap.width = Config['termWidth']
	twrap.subsequent_indent = " " * (maxflag_len + 8)

	markers = ("-", "+")
	color = [pp.useflagoff, pp.useflagon]
	for in_makeconf, in_installed, flag, desc, restrict in output:
		if Config['verbose']:
			flag_name = ""
			if in_makeconf != in_installed:
				flag_name += pp.emph(" %s %s" % 
					(markers[in_makeconf], markers[in_installed]))
			else:
				flag_name += (" %s %s" % 
					(markers[in_makeconf], markers[in_installed]))

			flag_name += " " + color[in_makeconf](flag.ljust(maxflag_len))
			flag_name += " : "

			# print description
			if restrict:
				restrict = "(%s %s)" % (pp.emph("Restricted to"), 
					pp.cpv(restrict))
				twrap.initial_indent = flag_name
				print twrap.fill(restrict)
				if desc:
					twrap.initial_indent = twrap.subsequent_indent
					print twrap.fill(desc)
				else:
					print " : <unknown>"
			else:
				if desc:
					twrap.initial_indent = flag_name
					desc = twrap.fill(desc)
					print desc
				else:
					twrap.initial_indent = flag_name
					print twrap.fill("<unknown>")
		else:
			print markers[in_makeconf] + flag


def get_global_useflags():
	"""Get global and expanded USE flag variables from
	PORTDIR/profiles/use.desc and PORTDIR/profiles/desc/*.desc respectively.

	@rtype: dict
	@return: {'flag_name': 'flag description', ...}
	"""

	global_usedesc = {}
	# Get global USE flag descriptions
	try:
		path = os.path.join(gentoolkit.settings["PORTDIR"], 'profiles', 
			'use.desc')
		with open(path) as open_file:
			for line in open_file:
				if line.startswith('#'):
					continue
				# Ex. of fields: ['syslog', 'Enables support for syslog\n']
				fields = line.split(" - ", 1)
				if len(fields) == 2:
					global_usedesc[fields[0]] = fields[1].rstrip()
	except IOError:
		pp.print_warn("Could not load USE flag descriptions from %s" %
			pp.path(path))

	del path, open_file
	# Add USE_EXPANDED variables to usedesc hash -- Bug #238005
	for path in glob(os.path.join(gentoolkit.settings["PORTDIR"],
			'profiles', 'desc', '*.desc')):
		try:
			with open(path) as open_file:
				for line in open_file:
					if line.startswith('#'):
						continue
					fields = [field.strip() for field in line.split(" - ", 1)]
					if len(fields) == 2:
						expanded_useflag = "%s_%s" % \
							(path.split("/")[-1][0:-5], fields[0])
						global_usedesc[expanded_useflag] = fields[1]
		except IOError:
			pp.print_warn("Could not load USE flag descriptions from %s" %
				path)

	return global_usedesc


def get_local_useflags(pkg):
	"""Parse package-specific flag descriptions from a package's metadata.xml.
	
	@see: http://www.gentoo.org/proj/en/glep/glep-0056.html
	@type pkg: gentoolkit.package.Package
	@param pkg: the package to find useflags for
	@rtype: dict
	@return: {string: tuple}
		string = flag's name
		tuple = (description, restrictions)
	"""

	result = {}

	metadata = os.path.join(pkg.get_package_path(), 'metadata.xml')
	try:
		xml_tree = ET.parse(metadata)
	except IOError:
		pp.print_error("Could not open %s" % metadata)
		return result

	for node in xml_tree.getiterator("flag"):
		name = node.get("name")
		restrict = node.get("restrict")
		# ElementTree handles nested element text in a funky way.
		# So we need to dump the raw XML and parse it manually.
		flagxml = ET.tostring(node)
		flagxml = re.sub("\s+", " ", flagxml)
		flagxml = re.sub("\n\t", "", flagxml)
		flagxml = re.sub("<(pkg|cat)>([^<]*)</(pkg|cat)>",
			pp.cpv("%s" % r"\2"), flagxml)
		flagtext = re.sub("<.*?>", "", flagxml)
		result[name] = (flagtext, restrict)

	return result


def get_matches(query):
	"""Get packages matching query."""

	if not QUERY_OPTS["allVersions"]:
		matches = [find_best_match(query)]
		if None in matches:
			matches = find_packages(query, include_masked=False)
			if matches:
				matches = sorted(matches, compare_package_strings)[-1:]
	else:
		matches = find_packages(query, include_masked=True)

	if not matches:
		raise errors.GentoolkitNoMatches(query)
	
	return matches


def get_output_descriptions(pkg, global_usedesc):
	"""Prepare descriptions and usage information for each USE flag."""

	local_usedesc = get_local_useflags(pkg)
	iuse = pkg.get_env_var("IUSE")

	if iuse:
		usevar = unique_array([x.lstrip('+-') for x in iuse.split()])
		usevar.sort()
	else:
		usevar = []

	if pkg.is_installed():
		used_flags = pkg.get_use_flags().split()
	else:
		used_flags = gentoolkit.settings["USE"].split()

	# store (inuse, inused, flag, desc, restrict)
	output = []
	for flag in usevar:
		inuse = False
		inused = False
		try:
			desc = local_usedesc[flag][0]
		except KeyError:
			try:
				desc = global_usedesc[flag]
			except KeyError:
				desc = ""
		try:
			restrict = local_usedesc[flag][1]
		except KeyError:
			restrict = ""

		if flag in pkg.get_settings("USE").split():
			inuse = True
		if flag in used_flags:
			inused = True

		output.append((inuse, inused, flag, desc, restrict))
	
	return output


def parse_module_options(module_opts):
	"""Parse module options and update GLOBAL_OPTS"""

	opts = (x[0] for x in module_opts)
	for opt in opts:
		if opt in ('-h', '--help'):
			print_help()
			sys.exit(0)
		elif opt in ('-a', '--all'):
			QUERY_OPTS['allVersions'] = True


def print_legend(query):
	"""Print a legend to explain the output format."""

	print "[ Legend : %s - flag is set in make.conf       ]" % pp.emph("U")
	print "[        : %s - package is installed with flag ]" % pp.emph("I")
	print "[ Colors : %s, %s                         ]" % (
		pp.useflagon("set"), pp.useflagoff("unset"))


def main(input_args):
	"""Parse input and run the program"""

	short_opts = "ha"
	long_opts = ('help', 'all')

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

	#
	# Output
	#

	first_run = True
	for query in queries:
		if not first_run:
			print

		if Config['verbose']:
			print " * Searching for %s ..." % pp.pkgquery(query)

		matches = get_matches(query)
		matches.sort()

		global_usedesc = get_global_useflags()
		for pkg in matches:

			output = get_output_descriptions(pkg, global_usedesc)
			if output:
				if Config['verbose']:
					print_legend(query)
					print (" * Found these USE flags for %s:" %
						pp.cpv(pkg.cpv))
					print pp.emph(" U I")
				display_useflags(output)
			else:
				if Config['verbose']:
					pp.print_warn("No USE flags found for %s" %
						pp.cpv(pkg.cpv))

		first_run = False
