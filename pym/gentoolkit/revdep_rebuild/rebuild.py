#!/usr/bin/python
# -*- coding: utf-8 -*-


""" Rebuild module

Main program, cli parsing and api program control and operation

Author: Sławomir Lis <lis.slawek@gmail.com>
	revdep-rebuild original author: Stanislav Brabec
	revdep-rebuild original rewrite Author: Michael A. Smith
Current Maintainer: Paul Varner <fuzzyray@gentoo.org>
Creation date: 2010/10/17
License: BSD
"""

from __future__ import print_function

import os
import sys
import getopt
import logging
from portage.output import bold, red, blue, yellow, green, nocolor

from .analyse import analyse
from .stuff import get_masking_status
from .cache import check_temp_files, read_cache
from .assign import get_slotted_cps
from .settings import DEFAULTS
from . import __version__


APP_NAME = sys.argv[0]
VERSION = __version__

__productname__ = "revdep-ng"


# functions

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


def init_logger(settings):
	"""Creates and iitializes our logger according to the settings"""
	logger = logging.getLogger()
	log_handler = logging.StreamHandler()
	log_fmt = logging.Formatter('%(msg)s')
	log_handler.setFormatter(log_fmt)
	logger.addHandler(log_handler)
	if settings['quiet']:
		logger.setLevel(logging.ERROR)
	elif settings['VERBOSITY'] == 2:
		logger.setLevel(logging.INFO)
	elif settings['debug']:
		logger.setLevel(logging.DEBUG)
	else:
		logger.setLevel(logging.WARNING)
	return logger


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

		do_help = False
		for key, val in opts:
			if key in ('-h', '--help'):
				do_help = True
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
				settings['library'] = settings['library'].union(val.split(','))
			elif key in ('-i', '--ignore'):
				settings['USE_TMP_FILES'] = False

		settings['pass_through_options'] = " " + " ".join(args)
	except getopt.GetoptError:
		#logging.info(red('Unrecognized option\n'))
		print(red('Unrecognized option\n'))
		print_usage()
		sys.exit(2)
	if do_help:
		print_usage()
		sys.exit(0)
	return settings


def rebuild(logger, assigned, settings):
	"""rebuilds the assigned pkgs"""
	
	args = settings['pass_through_options']
	if settings['EXACT']:
		emerge_command = '=' + ' ='.join(assigned)
	else:
		emerge_command = ' '.join(get_slotted_cps(assigned, logger))
	if settings['PRETEND']:
		args += ' --pretend'
	if settings['VERBOSITY'] >= 2:
		args += ' --verbose'
	elif settings['VERBOSITY'] < 1:
		args += ' --quiet'
	if settings['nocolor']:
		args += ' --color n'

	if len(emerge_command) == 0:
		logger.warn(bold('\nThere is nothing to emerge. Exiting.'))
		return 0

	emerge_command = emerge_command

	logger.warn(yellow(
		'\nemerge') + args + 
		' --oneshot --complete-graph=y ' +
		bold(emerge_command))
	
	success = os.system(
		'emerge ' + args + 
		' --oneshot --complete-graph=y ' + 
		emerge_command)
	return success


def main(settings=None, logger=None):
	"""Main program operation method....
	
	@param settings: dict.  defaults to settings.DEFAULTS
	@param logger: python logging module defaults to init_logger(settings)
	@return boolean  success/failure
	"""

	if settings is None:
		print("NO Input settings, using defaults...")
		settings = DEFAULTS.copy()

	if logger is None:
		logger = init_logger(settings)

	_libs_to_check = settings['library']

	if not settings['stdout'].isatty() or settings['nocolor']:
		nocolor()

	#TODO: Development warning
	logger.warn(blue(' * ') + 
		yellow('This is a development version, '
			'so it may not work correctly'))
	logger.warn(blue(' * ') + 
		yellow('The original revdep-rebuild script is '
			'installed as revdep-rebuild.sh'))

	if os.getuid() != 0 and not settings['PRETEND']:
		logger.warn(blue(' * ') + 
			yellow('You are not root, adding --pretend to portage options'))
		settings['PRETEND'] = True

	if settings['library']:
		logger.warn(green(' * ') + 
			"Looking for libraries: %s" % (bold(', '.join(settings['library']))))

	if settings['USE_TMP_FILES'] \
			and check_temp_files(settings['DEFAULT_TMP_DIR'], logger=logger):
		libraries, la_libraries, libraries_links, binaries = read_cache(
			settings['DEFAULT_TMP_DIR'])
		assigned = analyse(
			settings=settings,
			logger=logger,
			libraries=libraries,
			la_libraries=la_libraries, 
			libraries_links=libraries_links,
			binaries=binaries,
			_libs_to_check=_libs_to_check)
	else:
		assigned = analyse(settings, logger, _libs_to_check=_libs_to_check)

	if not assigned:
		logger.warn('\n' + bold('Your system is consistent'))
		# return the correct exit code
		return 0

	has_masked = False
	tmp = []
	for ebuild in assigned:
		if get_masking_status(ebuild):
			has_masked = True
			logger.warn('!!! ' + red('All ebuilds that could satisfy: ') + 
				green(ebuild) + red(' have been masked'))
		else:
			tmp.append(ebuild)
	assigned = tmp

	if has_masked:
		logger.info(red(' * ') + 
			'Unmask all ebuild(s) listed above and call revdep-rebuild '
			'again or manually emerge given packages.')

	success = rebuild(logger, assigned, settings)
	logger.debug("rebuild return code = %i" %success)
	return success
