#!/usr/bin/python

"""Default settings"""

import argparse
import os
import sys
import re
import glob

import portage
from portage import _encodings, _unicode_encode

portage_root = str(portage.root)

DEFAULTS = {
		'DEFAULT_LD_FILE': os.path.join(portage_root, 'etc/ld.so.conf'),
		'DEFAULT_ENV_FILE': os.path.join(portage_root, 'etc/profile.env'),
		'REVDEP_CONFDIR': os.path.join(portage_root, 'etc/revdep-rebuild/'),
		'PKG_DIR': os.path.join(portage_root, 'var/db/pkg/'),
		'DEFAULT_TMP_DIR': os.path.join(portage_root, '/tmp/revdep-rebuild' if os.getgid() else '/var/cache/revdep-rebuild'), #cache default location

		# number of maximum allowed files to be parsed at once
		'CMD_MAX_ARGS': 1000,

		'PRETEND': False,     #pretend only
		'EXACT': False,      #exact package version
		#if program should use temporary files from previous run
		'USE_TMP_FILES': True,

		'VERBOSITY': 1,

		'quiet': False,
		'nocolor': False,
		'library': set(),
		'no-progress': False,
		'debug': False,
		'no-ld-path': False,
		'no-order': False,
		'pass_through_options': [],
		'stdout': sys.stdout,
		'stdin': sys.stdin,
		'stderr': sys.stderr
		}


def parse_options():
	"""Parses the command line options an sets settings accordingly"""

	# TODO: Verify: options: no-ld-path, no-order, no-progress
	#are not appliable
	from .rebuild import VERSION, APP_NAME
	settings = DEFAULTS.copy()

	parser = argparse.ArgumentParser(
		description='Broken reverse dependency rebuilder, python implementation.',
		epilog='Calls emerge, options after -- are ignored by %s '
				'and passed directly to emerge.' % APP_NAME,
		add_help=False
		)

	parser.add_argument('-h', '--help',
					 action='help',
					 help='Print this usage and exit')
	parser.add_argument('-V', '--version',
					 action='version',
					 help='Show version informations',
					 version='%(prog)s ' + VERSION)

	parser.add_argument('-i', '--ignore',
					 action='store_true',
					 help='Ignore temporary files from previous runs '
						'(also won\'t create any)')

	parser.add_argument('-L', '--library',
					 action='append',
					 help='Unconditionally emerge existing packages that use '
						'the library with NAME. NAME can be a full path, full '
						'or partial name')
	parser.add_argument('-l', '--no-ld-path',
					 action='store_true',
					 help='Do not set LD_LIBRARY_PATH')
	parser.add_argument('-o', '--no-order',
					 action='store_true',
					 help='Do not check the build order '
						'(Saves time, but may cause breakage.)')
	parser.add_argument('-p', '--pretend',
					 action='store_true',
					 help='Do a trial run without actually emerging anything '
						'(also passed to emerge command)')

	parser.add_argument('-C', '--nocolor',
					 action='store_true',
					 help='Turn off colored output')
	parser.add_argument('-q', '--quiet',
					 action='store_true',
					 help='Be less verbose (also passed to emerge command)')
	parser.add_argument('-v', '--verbose',
					 action='store_true',
					 help='Be more verbose (also passed to emerge command)')
	parser.add_argument('-d', '--debug',
					 action='store_true',
					 help='Print debug informations')

	parser.add_argument('portage_options', nargs='*')

	args = parser.parse_args()
	settings['VERBOSITY'] = 3 if args.debug else 2 if args.verbose else 0 if args.quiet else 1
	settings['quiet'] = args.quiet
	settings['PRETEND'] = args.pretend
	settings['nocolor'] = args.nocolor
	if args.library:
		settings['library'] = set(settings['library']) | set(args.library)
	settings['USE_TMP_FILES'] = not args.ignore
	settings['pass_through_options'] = list(settings['pass_through_options']) + args.portage_options

	return settings


def _parse_dirs_to_set(dir_str):
	'''Changes space-delimited directory list into set with them
	'''
	_ret = set()
	for search in dir_str.split():
		if search == '-*':
			break
		_ret.update(glob.glob(search))
	return _ret


def parse_revdep_config(revdep_confdir):
	''' Parses all files under and returns
		tuple of: (masked_dirs, masked_files, search_dirs)'''

	search_dirs = os.environ.get('SEARCH_DIRS', '')
	masked_dirs = os.environ.get('SEARCH_DIRS_MASK', '')
	masked_files = os.environ.get('LD_LIBRARY_MASK', '')

	for _file in os.listdir(revdep_confdir):
		for line in open(_unicode_encode(os.path.join(revdep_confdir, _file),
				encoding=_encodings['fs']), encoding=_encodings['content']):
			line = line.strip()
			#first check for comment, we do not want to regex all lines
			if not line.startswith('#'):
				match = re.match(r'LD_LIBRARY_MASK=\"([^"]+)"', line)
				if match is not None:
					masked_files += ' ' + match.group(1)
					continue
				match = re.match(r'SEARCH_DIRS_MASK=\"([^"]+)"', line)
				if match is not None:
					masked_dirs += ' ' + match.group(1)
					continue
				match = re.match(r'SEARCH_DIRS="([^"]+)"', line)
				if match is not None:
					search_dirs += ' ' + match.group(1)
					continue

	masked_files = set(masked_files.split(' '))
	masked_dirs = _parse_dirs_to_set(masked_dirs)
	search_dirs = _parse_dirs_to_set(search_dirs)

	return (masked_dirs, masked_files, search_dirs)

