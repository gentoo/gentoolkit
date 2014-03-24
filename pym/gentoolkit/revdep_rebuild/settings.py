#!/usr/bin/python

"""Default settings"""

from __future__ import print_function

import getopt
import os
import sys
import re
import glob

import portage

DEFAULTS = {
		'DEFAULT_LD_FILE': os.path.join(portage.root, 'etc/ld.so.conf'),
		'DEFAULT_ENV_FILE': os.path.join(portage.root, 'etc/profile.env'),
		'REVDEP_CONFDIR': os.path.join(portage.root, 'etc/revdep-rebuild/'),
		'PKG_DIR': os.path.join(portage.root, 'var/db/pkg/'),
		'DEFAULT_TMP_DIR': os.path.join(portage.root, '/var/cache/revdep-rebuild'), #cache default location

		# number of maximum allowed files to be parsed at once
		'CMD_MAX_ARGS': 1000,

		'PRETEND': False,     #pretend only
		'EXACT': False,      #exact package version
		#if program should use temporary files from previous run
		'USE_TMP_FILES': True,

		#True for dev. version, False for stable
		#used when IS_DEV is True, False forces to call emerge with --pretend
		# can be set True from the cli with the --no-pretend option
		'IS_DEV': True,
		'NO_PRETEND': False,
		'VERBOSITY': 1,

		'quiet': False,
		'nocolor': False,
		'library': set(),
		'no-progress': False,
		'debug': False,
		'no-ld-path': False,
		'no-order': False,
		'pass_through_options': '',
		'stdout': sys.stdout,
		'stdin': sys.stdin,
		'stderr': sys.stderr
		}


def print_usage():
	"""Outputs the help message"""
	print( APP_NAME + ': (' + VERSION +')')
	print()
	print('This is free software; see the source for copying conditions.')
	print()
	print('Usage: ' + APP_NAME + ' [OPTIONS] [--] [EMERGE_OPTIONS]')
	print()
	print('Broken reverse dependency rebuilder, python implementation.')
	print()
	print('Available options:')
	print('''
  -C, --nocolor         Turn off colored output
  -d, --debug           Print debug informations
  -e, --exact           Emerge based on exact package version
  -h, --help            Print this usage
  -i, --ignore          Ignore temporary files from previous runs
                        (also won't create any)
  -L, --library NAME    Unconditionally emerge existing packages that use
      --library=NAME    the library with NAME. NAME can be a full or partial
                        library name
  -l, --no-ld-path      Do not set LD_LIBRARY_PATH
  -o, --no-order        Do not check the build order
                        (Saves time, but may cause breakage.)
  -p, --pretend         Do a trial run without actually emerging anything
                        (also passed to emerge command)
  -q, --quiet           Be less verbose (also passed to emerge command)
  -v, --verbose         Be more verbose (also passed to emerge command)
''')
	print( 'Calls emerge, options after -- are ignored by ' + APP_NAME)
	print('and passed directly to emerge.')


def parse_options():
	"""Parses the command line options an sets settings accordingly"""

	# TODO: Verify: options: no-ld-path, no-order, no-progress
	#are not appliable

	settings = DEFAULTS.copy()
	try:
		opts, args = getopt.getopt(sys.argv[1:],
			'dehiklopqvCL:P',
			['nocolor', 'debug', 'exact', 'help', 'ignore',
			'keep-temp', 'library=', 'no-ld-path', 'no-order',
			'pretend', 'no-pretend', 'no-progress', 'quiet', 'verbose'])

		for key, val in opts:
			if key in ('-h', '--help'):
				print_usage()
				sys.exit(0)
			elif key in ('-q', '--quiet'):
				settings['quiet'] = True
				settings['VERBOSITY'] = 0
			elif key in ('-v', '--verbose'):
				settings['VERBOSITY'] = 2
			elif key in ('-d', '--debug'):
				settings['debug'] = True
				settings['VERBOSITY'] = 3
			elif key in ('-p', '--pretend'):
				settings['PRETEND'] = True
			elif key == '--no-pretend':
				settings['NO_PRETEND'] = True
			elif key in ('-e', '--exact'):
				settings['EXACT'] = True
			elif key in ('-C', '--nocolor', '--no-color'):
				settings['nocolor'] = True
			elif key in ('-L', '--library', '--library='):
				settings['library'].update(val.split(','))
			elif key in ('-i', '--ignore'):
				settings['USE_TMP_FILES'] = False

		settings['pass_through_options'] = " " + " ".join(args)
	except getopt.GetoptError:
		#logging.info(red('Unrecognized option\n'))
		print(red('Unrecognized option\n'))
		print_usage()
		sys.exit(2)

	return settings


def parse_revdep_config(revdep_confdir):
	''' Parses all files under and returns
		tuple of: (masked_dirs, masked_files, search_dirs)'''

	search_dirs = set()
	masked_dirs = set()
	masked_files = set()

	for _file in os.listdir(revdep_confdir):
		for line in open(os.path.join(revdep_confdir, _file)):
			line = line.strip()
			#first check for comment, we do not want to regex all lines
			if not line.startswith('#'):
				match = re.match('LD_LIBRARY_MASK=\\"([^"]+)\\"', line)
				if match is not None:
					masks = match.group(1).split(' ')
					masked_files.update(masks)
					continue
				match = re.match('SEARCH_DIRS_MASK=\\"([^"]+)\\"', line)
				if match is not None:
					searches = match.group(1).split(' ')
					for search in searches:
						masked_dirs.update(glob.glob(search))
					continue
				match = re.match('SEARCH_DIRS=\\"([^"]+)\\"', line)
				if match is not None:
					searches = match.group(1).split()
					for search in searches:
						search_dirs.update(glob.glob(search))
					continue

	print (masked_dirs, masked_files, search_dirs)
	return (masked_dirs, masked_files, search_dirs)

