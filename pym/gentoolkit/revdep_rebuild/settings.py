#!/usr/bin/python

import os
import portage

SETTINGS = {
		'DEFAULT_LD_FILE': os.path.join(portage.root, 'etc/ld.so.conf'),
		'DEFAULT_ENV_FILE': os.path.join(portage.root, 'etc/profile.env'),
		'REVDEP_CONFDIR': os.path.join(portage.root, 'etc/revdep-rebuild/'),
		'PKG_DIR': os.path.join(portage.root, 'var/db/pkg/'),
		'DEFAULT_TMP_DIR': '/tmp/revdep-rebuild', #cache default location


		'USE_TMP_FILES': True, #if program should use temporary files from previous run
		'CMD_MAX_ARGS': 1000, # number of maximum allowed files to be parsed at once

		'PRETEND': False,     #pretend only
		'EXACT': False,      #exact package version
		'USE_TMP_FILES': True, #if program should use temporary files from previous run

		'IS_DEV': True,       #True for dev. version, False for stable
				#used when IS_DEV is True, False forces to call emerge with --pretend
				# can be set True from the cli with the --no-pretend option
		'NO_PRETEND': False,
		'VERBOSITY': 1,
	}
