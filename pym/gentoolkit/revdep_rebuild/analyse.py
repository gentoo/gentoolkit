#!/usr/bin/python

from __future__ import print_function

import os
import re
import platform
import glob

from portage.output import bold, red, blue, yellow, green, nocolor

from stuff import scan
from collect import prepare_search_dirs, parse_revdep_config, collect_libraries_from_dir, collect_binaries_from_dir
from assign import assign_packages
from cache import save_cache


def prepare_checks(files_to_check, libraries, bits, cmd_max_args):
	''' Calls scanelf for all files_to_check, then returns found libraries and dependencies
	'''

	libs = [] # libs found by scanelf
	dependencies = [] # list of lists of files (from file_to_check) that uses
					  # library (for dependencies[id] and libs[id] => id==id)

	for line in scan(['-M', str(bits), '-nBF', '%F %n'], files_to_check, cmd_max_args):
	#call_program(['scanelf', '-M', str(bits), '-nBF', '%F %n',]+files_to_check).strip().split('\n'):
		r = line.strip().split(' ')
		if len(r) < 2: # no dependencies?
			continue

		deps = r[1].split(',')
		for d in deps:
			if d in libs:
				i = libs.index(d)
				dependencies[i].append(r[0])
			else:
				libs.append(d)
				dependencies.append([r[0],])
	
	return (libs, dependencies)


def extract_dependencies_from_la(la, libraries, to_check, logger):
	broken = []

	libnames = []
	for l in libraries:
		m = re.match('.+\/(.+)\.(so|la|a)(\..+)?', l)
		if m is not None:
			ln = m.group(1)
			if ln not in libnames:
				libnames += [ln, ]

	for f in la:
		if not os.path.exists(f):
			continue

		for line in open(f, 'r').readlines():
			line = line.strip()
			if line.startswith('dependency_libs='):
				m = re.match("dependency_libs='([^']+)'", line)
				if m is not None:
					for el in m.group(1).split(' '):
						el = el.strip()
						if len(el) < 1 or el.startswith('-L') or el.startswith('-R'):
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

							logger.info(yellow(' * ') + f + ' is broken (requires: ' + bold(el)+')')
							broken.append(f)
	return broken


def find_broken(found_libs, system_libraries, to_check):
	''' Search for broken libraries.
		Check if system_libraries contains found_libs, where
		system_libraries is list of obsolute pathes and found_libs
		is list of library names.
	'''

	# join libraries and looking at it as string is way too faster than for-jumping

	broken = []
	sl = '|'.join(system_libraries)

	if not to_check:
		for f in found_libs:
			if f+'|' not in sl:
				broken.append(found_libs.index(f))
	else:
		for tc in to_check:
			for f in found_libs:
				if tc in f:# and f+'|' not in sl:
					broken.append(found_libs.index(f))

	return broken


def main_checks(found_libs, broken, dependencies, logger):
	''' Checks for broken dependencies.
		found_libs have to be the same as returned by prepare_checks
		broken is list of libraries found by scanelf
		dependencies is the value returned by prepare_checks
	'''

	broken_pathes = []

	for b in broken:
		f = found_libs[b]
		logger.info('Broken files that requires: ' + bold(f))
		for d in dependencies[b]:
			logger.info(yellow(' * ') + d)
			broken_pathes.append(d)
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
		logger.info(blue(' * ') + bold('Found a valid cache, skipping collecting phase'))
	else:
		#TODO: add partial cache (for ex. only libraries) when found for some reason

		logger.warn(green(' * ') + bold('Collecting system binaries and libraries'))
		bin_dirs, lib_dirs = prepare_search_dirs(logger, settings)

		masked_dirs, masked_files, ld = parse_revdep_config(settings['REVDEP_CONFDIR'])
		lib_dirs.update(ld)
		bin_dirs.update(ld)
		masked_dirs = masked_dirs.union(set(['/lib/modules', '/lib32/modules', '/lib64/modules',]))

		logger.info(green(' * ') + bold('Collecting dynamic linking informations'))
		libraries, la_libraries, libraries_links, symlink_pairs = collect_libraries_from_dir(lib_dirs, masked_dirs, logger)
		binaries = collect_binaries_from_dir(bin_dirs, masked_dirs, logger)

		if settings['USE_TMP_FILES']:
			save_cache(logger=logger, 
				to_save={'libraries':libraries, 'la_libraries':la_libraries,
					'libraries_links':libraries_links, 'binaries':binaries
				},
			temp_path=settings['DEFAULT_TMP_DIR']
			)


	logger.debug('Found '+ str(len(libraries)) + ' libraries (+' + str(len(libraries_links)) + ' symlinks) and ' + str(len(binaries)) + ' binaries')

	logger.warn(green(' * ') + bold('Checking dynamic linking consistency'))
	logger.debug('Search for ' + str(len(binaries)+len(libraries)) + ' within ' + str(len(libraries)+len(libraries_links)))
	libs_and_bins = libraries+binaries

	#l = []
	#for line in call_program(['scanelf', '-M', '64', '-BF', '%F',] + libraries).strip().split('\n'):
		#l.append(line)
	#libraries = l

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

	import time
	broken = []
	for av_bits in glob.glob('/lib[0-9]*') or ('/lib32',):
		bits = int(av_bits[4:])

		#_libraries = scan(['-M', str(bits), '-BF', '%F'], libraries+libraries_links, settings['CMD_MAX_ARGS'])
		_libraries = libraries+libraries_links

		found_libs, dependencies = prepare_checks(libs_and_bins, _libraries, bits, settings['CMD_MAX_ARGS'])
		broken = find_broken(found_libs, _libraries, _libs_to_check)

		bits /= 2
		bits = int(bits)

	broken_la = extract_dependencies_from_la(la_libraries, libraries+libraries_links, _libs_to_check, logger)


	broken_pathes = main_checks(found_libs, broken, dependencies, logger)
	broken_pathes += broken_la

	logger.warn(green(' * ') + bold('Assign files to packages'))

	return assign_packages(broken_pathes, logger, settings)



if __name__ == '__main__':
	print("This script shouldn't be called directly")
