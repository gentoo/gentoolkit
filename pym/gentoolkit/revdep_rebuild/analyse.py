#!/usr/bin/python

"""Analysis module"""

from __future__ import print_function

import os
import re
import platform
import glob

from portage.output import bold, blue, yellow, green

from .stuff import scan
from .collect import (prepare_search_dirs, parse_revdep_config,
	collect_libraries_from_dir, collect_binaries_from_dir)
from .assign import assign_packages
from .cache import save_cache


def prepare_checks(files_to_check, libraries, bits, cmd_max_args):
	''' Calls scanelf for all files_to_check, 
	then returns found libraries and dependencies
	'''

	# libs found by scanelf
	libs = []
	# list of lists of files (from file_to_check) that uses
	# library (for dependencies[id] and libs[id] => id==id)
	dependencies = []
	for line in scan(
		['-M', str(bits), '-nBF', '%F %n'],
		files_to_check, cmd_max_args
		):

		parts = line.strip().split(' ')
		if len(parts) < 2: # no dependencies?
			continue

		deps = parts[1].split(',')
		for dep in deps:
			if dep in libs:
				index = libs.index(dep)
				dependencies[index].append(parts[0])
			else:
				libs.append(dep)
				dependencies.append([parts[0],])
	
	return (libs, dependencies)


def extract_dependencies_from_la(la, libraries, to_check, logger):
	broken = []

	libnames = []
	for lib in libraries:
		match = re.match('.+\/(.+)\.(so|la|a)(\..+)?', lib)
		if match is not None:
			libname = match.group(1)
			if libname not in libnames:
				libnames += [libname, ]

	for _file in la:
		if not os.path.exists(_file):
			continue

		for line in open(_file, 'r').readlines():
			line = line.strip()
			if line.startswith('dependency_libs='):
				match = re.match("dependency_libs='([^']+)'", line)
				if match is not None:
					for el in match.group(1).split(' '):
						el = el.strip()
						if (len(el) < 1 or el.startswith('-L')
							or el.startswith('-R')
							):
							continue

						if el.startswith('-l') and 'lib'+el[2:] in libnames:
							pass
						elif el in la or el in libraries:
							pass
						else:
							if to_check:
								_break = False
								for tc in to_check:
									if tc in el:
										_break = True
										break
								if not _break:
									continue

							logger.info(yellow(' * ') + _file + 
								' is broken (requires: ' + bold(el)+')')
							broken.append(_file)
	return broken


def find_broken(found_libs, system_libraries, to_check):
	''' Search for broken libraries.
		Check if system_libraries contains found_libs, where
		system_libraries is list of obsolute pathes and found_libs
		is list of library names.
	'''

	# join libraries and looking at it as string
	# is way faster than for-jumping

	broken = []
	syslibs = '|'.join(system_libraries)

	if not to_check:
		for found in found_libs:
			if found + '|' not in syslibs:
				broken.append(found_libs.index(found))
	else:
		for tc in to_check:
			for found in found_libs:
				if tc in found:# and found+'|' not in syslibs:
					broken.append(found_libs.index(found))

	return broken


def main_checks(found_libs, broken_list, dependencies, logger):
	''' Checks for broken dependencies.
		found_libs have to be the same as returned by prepare_checks
		broken_list is list of libraries found by scanelf
		dependencies is the value returned by prepare_checks
	'''

	broken_pathes = []

	for broken in broken_list:
		found = found_libs[broken]
		logger.info('Broken files that requires: ' + bold(found))
		for dep_path in dependencies[broken]:
			logger.info(yellow(' * ') + dep_path)
			broken_pathes.append(dep_path)
	return broken_pathes


def analyse(settings, logger, libraries=None, la_libraries=None,
		libraries_links=None, binaries=None, _libs_to_check=set()):
	"""Main program body.  It will collect all info and determine the
	pkgs needing rebuilding.

	@param logger: logger used for logging messages, instance of logging.Logger
				   class. Can be logging (RootLogger).
	@param _libs_to_check Libraries that need to be checked only
	@rtype list: list of pkgs that need rebuilding
	"""

	if libraries and la_libraries and libraries_links and binaries:
		logger.info(blue(' * ') + 
			bold('Found a valid cache, skipping collecting phase'))
	else:
		#TODO: add partial cache (for ex. only libraries)
		# when found for some reason

		logger.warn(green(' * ') + 
			bold('Collecting system binaries and libraries'))
		bin_dirs, lib_dirs = prepare_search_dirs(logger, settings)

		masked_dirs, masked_files, ld = \
			parse_revdep_config(settings['REVDEP_CONFDIR'])
		lib_dirs.update(ld)
		bin_dirs.update(ld)
		masked_dirs.update([
			'/lib/modules',
			'/lib32/modules',
			'/lib64/modules'
			]
			)

		logger.info(green(' * ') +
			bold('Collecting dynamic linking informations'))
		libraries, la_libraries, libraries_links, symlink_pairs = \
			collect_libraries_from_dir(lib_dirs, masked_dirs, logger)
		binaries = collect_binaries_from_dir(bin_dirs, masked_dirs, logger)

		if settings['USE_TMP_FILES']:
			save_cache(logger=logger, 
				to_save={'libraries':libraries, 'la_libraries':la_libraries,
					'libraries_links':libraries_links, 'binaries':binaries
				},
			temp_path=settings['DEFAULT_TMP_DIR']
			)


	logger.debug('Found '+ str(len(libraries)) + 
		' libraries (+' + str(len(libraries_links)) +
		' symlinks) and ' + str(len(binaries)) +
		' binaries')

	logger.warn(green(' * ') + bold('Checking dynamic linking consistency'))
	logger.debug('Search for ' + str(len(binaries)+len(libraries)) +
		' within ' + str(len(libraries)+len(libraries_links)))
	libs_and_bins = libraries+binaries

	found_libs = []
	dependencies = []

	if _libs_to_check:
		nltc = []
		for ltc in _libs_to_check:
			if os.path.isfile(ltc):
				ltc = scan(['-nBSF', '%S'], [ltc,], settings['CMD_MAX_ARGS'])[0].split()[0]
			nltc += [ltc,]
		_libs_to_check = nltc

	_bits, linkg = platform.architecture()
	if _bits.startswith('32'):
		bits = 32
	elif _bits.startswith('64'):
		bits = 64

	broken = []
	for av_bits in glob.glob('/lib[0-9]*') or ('/lib32',):
		bits = int(av_bits[4:])

		_libraries = libraries+libraries_links

		found_libs, dependencies = prepare_checks(libs_and_bins,
			_libraries, bits, settings['CMD_MAX_ARGS'])
		broken = find_broken(found_libs, _libraries, _libs_to_check)

		bits /= 2
		bits = int(bits)

	broken_la = extract_dependencies_from_la(la_libraries,
		libraries+libraries_links, _libs_to_check, logger)


	broken_pathes = main_checks(found_libs, broken, dependencies, logger)
	broken_pathes += broken_la

	logger.warn(green(' * ') + bold('Assign files to packages'))

	return assign_packages(broken_pathes, logger, settings)



if __name__ == '__main__':
	print("This script shouldn't be called directly")
