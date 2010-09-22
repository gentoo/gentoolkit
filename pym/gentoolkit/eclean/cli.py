#!/usr/bin/python

# Copyright 2003-2010 Gentoo Foundation
# Distributed under the terms of the GNU General Public License v2


from __future__ import print_function


__author__ = "Thomas de Grenier de Latour (tgl), " + \
	"modular re-write by: Brian Dolbec (dol-sen)"
__email__ = "degrenier@easyconnect.fr, " + \
	"brian.dolbec@gmail.com"
__version__ = "svn"
__productname__ = "eclean"
__description__ = "A cleaning tool for Gentoo distfiles and binaries."


import os
import sys
import re
import time
import getopt

import portage
from portage.output import white, yellow, turquoise, green, teal, red

import gentoolkit.pprinter as pp
from gentoolkit.eclean.search import (DistfilesSearch,
	findPackages, port_settings, pkgdir)
from gentoolkit.eclean.exclude import (parseExcludeFile,
	ParseExcludeFileException)
from gentoolkit.eclean.clean import CleanUp
from gentoolkit.eclean.output import OutputControl
#from gentoolkit.eclean.dbapi import Dbapi
from gentoolkit.eprefix import EPREFIX

def printVersion():
	"""Output the version info."""
	print( "%s (%s) - %s" \
			% (__productname__, __version__, __description__))
	print()
	print("Author: %s <%s>" % (__author__,__email__))
	print("Copyright 2003-2009 Gentoo Foundation")
	print("Distributed under the terms of the GNU General Public License v2")


def printUsage(_error=None, help=None):
	"""Print help message. May also print partial help to stderr if an
	error from {'options','actions'} is specified."""

	out = sys.stdout
	if _error:
		out = sys.stderr
	if not _error in ('actions', 'global-options', \
			'packages-options', 'distfiles-options', \
			'merged-packages-options', 'merged-distfiles-options', \
			'time', 'size'):
		_error = None
	if not _error and not help: help = 'all'
	if _error == 'time':
		print( pp.error("Wrong time specification"), file=out)
		print( "Time specification should be an integer followed by a"+
				" single letter unit.", file=out)
		print( "Available units are: y (years), m (months), w (weeks), "+
				"d (days) and h (hours).", file=out)
		print( "For instance: \"1y\" is \"one year\", \"2w\" is \"two"+
				" weeks\", etc. ", file=out)
		return
	if _error == 'size':
		print( pp.error("Wrong size specification"), file=out)
		print( "Size specification should be an integer followed by a"+
				" single letter unit.", file=out)
		print( "Available units are: G, M, K and B.", file=out)
		print("For instance: \"10M\" is \"ten megabytes\", \"200K\" "+
				"is \"two hundreds kilobytes\", etc.", file=out)
		return
	if _error in ('global-options', 'packages-options', 'distfiles-options', \
			'merged-packages-options', 'merged-distfiles-options',):
		print( pp.error("Wrong option on command line."), file=out)
		print( file=out)
	elif _error == 'actions':
		print( pp.error("Wrong or missing action name on command line."), file=out)
		print( file=out)
	print( white("Usage:"), file=out)
	if _error in ('actions','global-options', 'packages-options', \
			'distfiles-options') or help == 'all':
		print( " "+turquoise(__productname__),
			yellow("[global-option] ..."),
			green("<action>"),
			yellow("[action-option] ..."), file=out)
	if _error == 'merged-distfiles-options' or help in ('all','distfiles'):
		print( " "+turquoise(__productname__+'-dist'),
			yellow("[global-option, distfiles-option] ..."), file=out)
	if _error == 'merged-packages-options' or help in ('all','packages'):
		print( " "+turquoise(__productname__+'-pkg'),
			yellow("[global-option, packages-option] ..."), file=out)
	if _error in ('global-options', 'actions'):
		print( " "+turquoise(__productname__),
			yellow("[--help, --version]"), file=out)
	if help == 'all':
		print( " "+turquoise(__productname__+"(-dist,-pkg)"),
			yellow("[--help, --version]"), file=out)
	if _error == 'merged-packages-options' or help == 'packages':
		print( " "+turquoise(__productname__+'-pkg'),
			yellow("[--help, --version]"), file=out)
	if _error == 'merged-distfiles-options' or help == 'distfiles':
		print( " "+turquoise(__productname__+'-dist'),
			yellow("[--help, --version]"), file=out)
	print(file=out)
	if _error in ('global-options', 'merged-packages-options', \
	'merged-distfiles-options') or help:
		print( "Available global", yellow("options")+":", file=out)
		print( yellow(" -C, --nocolor")+
			"            - turn off colors on output", file=out)
		print( yellow(" -d, --destructive")+
			"        - only keep the minimum for a reinstallation", file=out)
		print( yellow(" -e, --exclude-file=<path>")+
			" - path to the exclusion file", file=out)
		print( yellow(" -i, --interactive")+
			"        - ask confirmation before deletions", file=out)
		print( yellow(" -n, --package-names")+
			"      - protect all versions (when --destructive)", file=out)
		print( yellow(" -p, --pretend")+
			"            - only display what would be cleaned", file=out)
		print( yellow(" -q, --quiet")+
			"              - be as quiet as possible", file=out)
		print( yellow(" -t, --time-limit=<time>")+
			"   - don't delete files modified since "+yellow("<time>"), file=out)
		print( "   "+yellow("<time>"), "is a duration: \"1y\" is"+
				" \"one year\", \"2w\" is \"two weeks\", etc. ", file=out)
		print( "   "+"Units are: y (years), m (months), w (weeks), "+
				"d (days) and h (hours).", file=out)
		print( yellow(" -h, --help")+ \
			"               - display the help screen", file=out)
		print( yellow(" -V, --version")+
			"            - display version info", file=out)
		print( file=out)
	if _error == 'actions' or help == 'all':
		print( "Available", green("actions")+":", file=out)
		print( green(" packages")+
			"     - clean outdated binary packages from PKGDIR", file=out)
		print( green(" distfiles")+
			"    - clean outdated packages sources files from DISTDIR", file=out)
		print( file=out)
	if _error in ('packages-options','merged-packages-options') \
	or help in ('all','packages'):
		print( "Available", yellow("options"),"for the",
				green("packages"),"action:", file=out)
		print( yellow(" NONE  :)"), file=out)
		print( file=out)
	if _error in ('distfiles-options', 'merged-distfiles-options') \
	or help in ('all','distfiles'):
		print("Available", yellow("options"),"for the",
				green("distfiles"),"action:", file=out)
		print( yellow(" -f, --fetch-restricted")+
			"   - protect fetch-restricted files (when --destructive)", file=out)
		print( yellow(" -s, --size-limit=<size>")+
			"  - don't delete distfiles bigger than "+yellow("<size>"), file=out)
		print( "   "+yellow("<size>"), "is a size specification: "+
				"\"10M\" is \"ten megabytes\", \"200K\" is", file=out)
		print( "   "+"\"two hundreds kilobytes\", etc.  Units are: "+
				"G, M, K and B.", file=out)
		print( file=out)
	print( "More detailed instruction can be found in",
			turquoise("`man %s`" % __productname__), file=out)


class ParseArgsException(Exception):
	"""For parseArgs() -> main() communications."""
	def __init__(self, value):
		self.value = value # sdfgsdfsdfsd
	def __str__(self):
		return repr(self.value)


def parseSize(size):
	"""Convert a file size "Xu" ("X" is an integer, and "u" in
	[G,M,K,B]) into an integer (file size in Bytes).

	@raise ParseArgsException: in case of failure
	"""
	units = {
		'G': (1024**3),
		'M': (1024**2),
		'K': 1024,
		'B': 1
	}
	try:
		match = re.match(r"^(?P<value>\d+)(?P<unit>[GMKBgmkb])?$",size)
		size = int(match.group('value'))
		if match.group('unit'):
			size *= units[match.group('unit').capitalize()]
	except:
		raise ParseArgsException('size')
	return size


def parseTime(timespec):
	"""Convert a duration "Xu" ("X" is an int, and "u" a time unit in
	[Y,M,W,D,H]) into an integer which is a past EPOCH date.
	Raises ParseArgsException('time') in case of failure.
	(yep, big approximations inside... who cares?).
	"""
	units = {'H' : (60 * 60)}
	units['D'] = units['H'] * 24
	units['W'] = units['D'] * 7
	units['M'] = units['D'] * 30
	units['Y'] = units['D'] * 365
	try:
		# parse the time specification
		match = re.match(r"^(?P<value>\d+)(?P<unit>[YMWDHymwdh])?$",timespec)
		value = int(match.group('value'))
		if not match.group('unit'): unit = 'D'
		else: unit = match.group('unit').capitalize()
	except:
		raise ParseArgsException('time')
	return time.time() - (value * units[unit])


def parseArgs(options={}):
	"""Parse the command line arguments. Raise exceptions on
	errors or non-action modes (help/version). Returns an action, and affect
	the options dict.
	"""

	def optionSwitch(option,opts,action=None):
		"""local function for interpreting command line options
		and setting options accordingly"""
		return_code = True
		for o, a in opts:
			if o in ("-h", "--help"):
				if action:
					raise ParseArgsException('help-'+action)
				else:
					raise ParseArgsException('help')
			elif o in ("-V", "--version"):
				raise ParseArgsException('version')
			elif o in ("-C", "--nocolor"):
				options['nocolor'] = True
				pp.output.nocolor()
			elif o in ("-d", "--destructive"):
				options['destructive'] = True
			elif o in ("-D", "--deprecated"):
				options['deprecated'] = True
			elif o in ("-i", "--interactive") and not options['pretend']:
				options['interactive'] = True
			elif o in ("-p", "--pretend"):
				options['pretend'] = True
				options['interactive'] = False
			elif o in ("-q", "--quiet"):
				options['quiet'] = True
				options['verbose'] = False
			elif o in ("-t", "--time-limit"):
				options['time-limit'] = parseTime(a)
			elif o in ("-e", "--exclude-file"):
				print("cli --exclude option")
				options['exclude-file'] = a
			elif o in ("-n", "--package-names"):
				options['package-names'] = True
			elif o in ("-f", "--fetch-restricted"):
				options['fetch-restricted'] = True
			elif o in ("-s", "--size-limit"):
				options['size-limit'] = parseSize(a)
			elif o in ("-v", "--verbose") and not options['quiet']:
					options['verbose'] = True
			else:
				return_code = False
		# sanity check of --destructive only options:
		for opt in ('fetch-restricted', 'package-names'):
			if (not options['destructive']) and options[opt]:
				if not options['quiet']:
					print( pp.error(
						"--%s only makes sense in --destructive mode." % opt), file=sys.stderr)
				options[opt] = False
		return return_code

	# here are the different allowed command line options (getopt args)
	getopt_options = {'short':{}, 'long':{}}
	getopt_options['short']['global'] = "CdDipqe:t:nhVv"
	getopt_options['long']['global'] = ["nocolor", "destructive",
		"deprecated", "interactive", "pretend", "quiet", "exclude-file=",
		"time-limit=", "package-names", "help", "version",  "verbose"]
	getopt_options['short']['distfiles'] = "fs:"
	getopt_options['long']['distfiles'] = ["fetch-restricted", "size-limit="]
	getopt_options['short']['packages'] = ""
	getopt_options['long']['packages'] = [""]
	# set default options, except 'nocolor', which is set in main()
	options['interactive'] = False
	options['pretend'] = False
	options['quiet'] = False
	options['accept_all'] = False
	options['destructive'] = False
	options['deprecated'] = False
	options['time-limit'] = 0
	options['package-names'] = False
	options['fetch-restricted'] = False
	options['size-limit'] = 0
	options['verbose'] = False
	# if called by a well-named symlink, set the acction accordingly:
	action = None
	# temp print line to ensure it is the svn/branch code running, etc..
	#print(  "###### svn/branch/gentoolkit_eclean ####### ==> ", os.path.basename(sys.argv[0]))
	if os.path.basename(sys.argv[0]) in \
			(__productname__+'-pkg', __productname__+'-packages'):
		action = 'packages'
	elif os.path.basename(sys.argv[0]) in \
			(__productname__+'-dist', __productname__+'-distfiles'):
		action = 'distfiles'
	# prepare for the first getopt
	if action:
		short_opts = getopt_options['short']['global'] \
			+ getopt_options['short'][action]
		long_opts = getopt_options['long']['global'] \
			+ getopt_options['long'][action]
		opts_mode = 'merged-'+action
	else:
		short_opts = getopt_options['short']['global']
		long_opts = getopt_options['long']['global']
		opts_mode = 'global'
	# apply getopts to command line, show partial help on failure
	try:
		opts, args = getopt.getopt(sys.argv[1:], short_opts, long_opts)
	except:
		raise ParseArgsException(opts_mode+'-options')
	# set options accordingly
	optionSwitch(options,opts,action=action)
	# if action was already set, there should be no more args
	if action and len(args):
		raise ParseArgsException(opts_mode+'-options')
	# if action was set, there is nothing left to do
	if action:
		return action
	# So, we are in "eclean --foo action --bar" mode. Parse remaining args...
	# Only two actions are allowed: 'packages' and 'distfiles'.
	if not len(args) or not args[0] in ('packages','distfiles'):
		raise ParseArgsException('actions')
	action = args.pop(0)
	# parse the action specific options
	try:
		opts, args = getopt.getopt(args, \
			getopt_options['short'][action], \
			getopt_options['long'][action])
	except:
		raise ParseArgsException(action+'-options')
	# set options again, for action-specific options
	optionSwitch(options,opts,action=action)
	# any remaning args? Then die!
	if len(args):
		raise ParseArgsException(action+'-options')
	# returns the action. Options dictionary is modified by side-effect.
	return action


def doAction(action,options,exclude={}, output=None):
	"""doAction: execute one action, ie display a few message, call the right
	find* function, and then call doCleanup with its result."""
	# define vocabulary for the output
	if action == 'packages':
		files_type = "binary packages"
	else:
		files_type = "distfiles"
	saved = {}
	deprecated = {}
	# find files to delete, depending on the action
	if not options['quiet']:
		output.einfo("Building file list for "+action+" cleaning...")
	if action == 'packages':
		clean_me = findPackages(
			options,
			exclude=exclude,
			destructive=options['destructive'],
			package_names=options['package-names'],
			time_limit=options['time-limit'],
			pkgdir=pkgdir,
			#port_dbapi=Dbapi(portage.db[portage.root]["porttree"].dbapi),
			#var_dbapi=Dbapi(portage.db[portage.root]["vartree"].dbapi),
		)
	else:
		# accept defaults
		engine = DistfilesSearch(output=options['verbose-output'],
			#portdb=Dbapi(portage.db[portage.root]["porttree"].dbapi),
			#var_dbapi=Dbapi(portage.db[portage.root]["vartree"].dbapi),
		)
		clean_me, saved, deprecated = engine.findDistfiles(
			exclude=exclude,
			destructive=options['destructive'],
			fetch_restricted=options['fetch-restricted'],
			package_names=options['package-names'],
			time_limit=options['time-limit'],
			size_limit=options['size-limit'],
			deprecate = options['deprecated']
		)
	# actually clean files if something was found
	if clean_me:
		# verbose pretend message
		if options['pretend'] and not options['quiet']:
			output.einfo("Here are the "+files_type+" that would be deleted:")
		# verbose non-pretend message
		elif not options['quiet']:
			output.einfo("Cleaning " + files_type  +"...")
		# do the cleanup, and get size of deleted files
		cleaner = CleanUp( output.progress_controller)
		if  options['pretend']:
			clean_size = cleaner.pretend_clean(clean_me)
		elif action in ['distfiles']:
			clean_size = cleaner.clean_dist(clean_me)
		elif action in ['packages']:
			clean_size = cleaner.clean_pkgs(clean_me,
				pkgdir)
		# vocabulary for final message
		if options['pretend']:
			verb = "would be"
		else:
			verb = "were"
		# display freed space
		if not options['quiet']:
			output.total('normal', clean_size, len(clean_me), verb, action)
	# nothing was found, return
	elif not options['quiet']:
		output.einfo("Your "+action+" directory was already clean.")
	if saved and not options['quiet']:
		print()
		print( (pp.emph("   The following ") + yellow("Deprecated") +
			pp.emph(" files were saved from cleaning due to exclusion file entries")))
		output.set_colors('deprecated')
		clean_size = cleaner.pretend_clean(saved)
		output.total('deprecated', clean_size, len(saved), verb, action)
	if deprecated and not options['quiet']:
		print()
		print( (pp.emph("   The following ") + yellow("Deprecated") +
			pp.emph(" installed packages were found")))
		output.set_colors('deprecated')
		output.list_pkgs(deprecated)


def main():
	"""Parse command line and execute all actions."""
	# set default options
	options = {}
	options['nocolor'] = (port_settings["NOCOLOR"] in ('yes','true')
		or not sys.stdout.isatty())
	if options['nocolor']:
		pp.output.nocolor()
	# parse command line options and actions
	try:
		action = parseArgs(options)
	# filter exception to know what message to display
	except ParseArgsException as e:
		if e.value == 'help':
			printUsage(help='all')
			sys.exit(0)
		elif e.value[:5] == 'help-':
			printUsage(help=e.value[5:])
			sys.exit(0)
		elif e.value == 'version':
			printVersion()
			sys.exit(0)
		else:
			printUsage(e.value)
			sys.exit(2)
	output = OutputControl(options)
	options['verbose-output'] = lambda x: None
	if not options['quiet']:
		if options['verbose']:
			options['verbose-output'] = output.einfo
	# parse the exclusion file
	if not 'exclude-file' in options:
		# set it to the default exclude file if it exists
		exclude_file = "%s/etc/%s/%s.exclude" % (EPREFIX,__productname__ , action)
		if os.path.isfile(exclude_file):
			options['exclude-file'] = exclude_file
	if 'exclude-file' in options:
		try:
			exclude = parseExcludeFile(options['exclude-file'],
					options['verbose-output'])
		except ParseExcludeFileException as e:
			print( pp.error(str(e)), file=sys.stderr)
			print( pp.error(
				"Invalid exclusion file: %s" % options['exclude-file']), file=sys.stderr)
			print( pp.error(
				"See format of this file in `man %s`" % __productname__), file=sys.stderr)
			sys.exit(1)
	else:
			exclude = {}
	# security check for non-pretend mode
	if not options['pretend'] and portage.secpass == 0:
		print( pp.error(
			"Permission denied: you must be root or belong to " +
			"the portage group."), file=sys.stderr)
		sys.exit(1)
	# execute action
	doAction(action, options, exclude=exclude,
		output=output)


if __name__ == "__main__":
	"""actually call main() if launched as a script"""
	try:
		main()
	except KeyboardInterrupt:
		print( "Aborted.")
		sys.exit(130)
	sys.exit(0)
