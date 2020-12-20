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

import os
import sys
import logging
import subprocess
import time
current_milli_time = lambda: int(round(time.time() * 1000))


from portage.output import bold, red, blue, yellow, nocolor

from .analyse import analyse
from .cache import check_temp_files, read_cache
from .assign import get_slotted_cps
from .settings import DEFAULTS, parse_options
from .stuff import filter_masked
from . import __version__


APP_NAME = sys.argv[0]
VERSION = __version__

__productname__ = "revdep-ng"


# functions

def init_logger(settings):
	"""Creates and iitializes our logger according to the settings"""
	logger = logging.getLogger()
	log_handler = logging.StreamHandler(sys.stdout)
	log_fmt = logging.Formatter('%(msg)s')
	log_handler.setFormatter(log_fmt)
	logger.addHandler(log_handler)
	if settings['quiet']:
		logger.setLevel(logging.ERROR)
	elif settings['VERBOSITY'] == 2:
		logger.setLevel(logging.INFO)
	elif settings['VERBOSITY'] == 3 or settings['debug']:
		logger.setLevel(logging.DEBUG)
	else:
		logger.setLevel(logging.WARNING)
	return logger




def rebuild(logger, assigned, settings):
	"""rebuilds the assigned pkgs"""

	args = list(settings['pass_through_options'])
	if settings['EXACT']:
		_assigned = filter_masked(assigned, logger)
		emerge_command = ['='+a for a in _assigned]
	else:
		_assigned = get_slotted_cps(assigned, logger)
		emerge_command = [a for a in _assigned]
	if settings['PRETEND']:
		args.append('--pretend')
	if settings['VERBOSITY'] >= 2:
		args.append('--verbose')
	elif settings['VERBOSITY'] < 1:
		args.append('--quiet')
	if settings['nocolor']:
		args.extend(['--color', 'n'])

	if len(emerge_command) == 0:
		logger.warning(bold('\nThere is nothing to emerge. Exiting.'))
		return 0

	logger.warning(yellow(
		'\nemerge') +  ' ' + ' '.join(args) +
		' --oneshot --complete-graph=y ' +
		bold(' '.join(emerge_command)))

	stime = current_milli_time()
	_args = ['emerge'] + args + ['--oneshot', '--complete-graph=y'] + emerge_command
	success = subprocess.call(_args)
	ftime = current_milli_time()
	logger.debug("\trebuild(); emerge call for %d ebuilds took: %s seconds"
		% (len(_assigned), str((ftime-stime)/1000.0)))
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

	logger.warning(blue(' * ') +
		yellow('This is the new python coded version'))
	logger.warning(blue(' * ') +
		yellow('Please report any bugs found using it.'))
	logger.warning(blue(' * ') +
		yellow('The original revdep-rebuild script is '
			'installed as revdep-rebuild.sh'))
	logger.warning(blue(' * ') +
		yellow('Please file bugs at: '
			'https://bugs.gentoo.org/'))

	if os.getuid() != 0 and not settings['PRETEND']:
		logger.warning(blue(' * ') +
			yellow('You are not root, adding --pretend to portage options'))
		settings['PRETEND'] = True

	logger.debug("\tmain(), _libs_to_check = %s" % str(_libs_to_check))

	if settings['USE_TMP_FILES'] \
			and check_temp_files(settings['DEFAULT_TMP_DIR'], logger=logger):
		libraries, la_libraries, libraries_links, binaries = read_cache(
			settings['DEFAULT_TMP_DIR'])
		assigned, orphaned = analyse(
			settings=settings,
			logger=logger,
			libraries=libraries,
			la_libraries=la_libraries,
			libraries_links=libraries_links,
			binaries=binaries,
			_libs_to_check=_libs_to_check)
	else:
		assigned, orphaned = analyse(settings, logger, _libs_to_check=_libs_to_check)

	if not assigned and not orphaned:
		logger.warning('\n' + bold('Your system is consistent'))
		# return the correct exit code
		return 0
	elif orphaned:
		# blank line for beter visibility of the following lines
		logger.warning('')
		if settings['library']:
			logger.warning(red(' !!! Dependant orphaned files: ') +
				bold('No installed package was found for the following:'))
		else:
			logger.warning(red(' !!! Broken orphaned files: ') +
				bold('No installed package was found for the following:'))
		for filename in orphaned:
			logger.warning(red('\t* ') + filename)

	success = rebuild(logger, assigned, settings)
	logger.debug("rebuild return code = %i" %success)
	return success


if __name__ == '__main__':
	main(parse_options())

