#!/usr/bin/python

"""Default settings"""

from __future__ import print_function

import os
import sys

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
