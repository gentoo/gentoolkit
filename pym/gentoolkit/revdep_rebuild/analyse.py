#!/usr/bin/python

"""Analysis module"""

from __future__ import print_function

import os
import re

from portage.output import bold, blue, yellow, green

from .stuff import scan
from .collect import (prepare_search_dirs, parse_revdep_config,
	collect_libraries_from_dir, collect_binaries_from_dir)
from .assign import assign_packages
from .cache import save_cache


def scan_files(libs_and_bins, cmd_max_args, logger):

	scanned_files = {} # {bits: {soname: (filename, needed), ...}, ...}
	for line in scan(['-nBF', '%F %f %S %n %M'],
					 libs_and_bins, cmd_max_args, logger):
		parts = line.split(' ')
		if len(parts) < 5:
			logger.error("scan_files(); error processing lib: %s" % line)
			logger.error("scan_files(); parts = %s" % str(parts))
			continue
		filename, sfilename, soname, needed, bits = parts
		filename = os.path.realpath(filename)
		needed = needed.split(',')
		bits = bits[8:] # 8: -> strlen('ELFCLASS')
		if not soname:
			soname = sfilename

		if bits not in scanned_files:
			scanned_files[bits] = {}
		if soname not in scanned_files[bits]:
			scanned_files[bits][soname] = {}
		if filename not in scanned_files[bits][soname]:
			scanned_files[bits][soname][filename] = set(needed)
		else:
			scanned_files[bits][soname][filename].update(needed)

	return scanned_files



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


def find_broken2(scanned_files, logger):
	broken_libs = {}
	for bits, libs in scanned_files.items():
		logger.debug('find_broken2(), Checking for %s bit libs' % bits)
		alllibs = '|'.join(sorted(libs)) + '|'
		#print(alllibs)
		#print()
		for soname, filepaths in libs.items():
			for filename, needed in filepaths.items():
				for l in needed:
					if l+'|' not in alllibs:
						try:
							broken_libs[bits][l].add(filename)
						except KeyError:
							try:
								broken_libs[bits][l] = set([filename])
							except KeyError:
								broken_libs = {bits: {l: set([filename])}}
	return broken_libs


def main_checks2(broken, scanned_files, logger):
	broken_pathes = []
	for bits, _broken in broken.items():
		for lib, files in _broken.items():
			logger.info('Broken files that requires: %s (%s bits)' % (bold(lib), bits))
			for fp in sorted(files):
				logger.info(yellow(' * ') + fp)
				broken_pathes.append(fp)
	return broken_pathes


def analyse(settings, logger, libraries=None, la_libraries=None,
		libraries_links=None, binaries=None, _libs_to_check=None):
	"""Main program body.  It will collect all info and determine the
	pkgs needing rebuilding.

	@param logger: logger used for logging messages, instance of logging.Logger
				   class. Can be logging (RootLogger).
	@param _libs_to_check Libraries that need to be checked only
	@rtype list: list of pkgs that need rebuilding
	"""

	if _libs_to_check == None:
		_libs_to_check = set()
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
		masked_dirs.update(
			set([
				'/lib/modules',
				'/lib32/modules',
				'/lib64/modules',
			])
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


	logger.debug('analyse(), Found %i libraries (+%i symlinks) and %i binaries' %
		(len(libraries), len(libraries_links), len(binaries))
	)
	logger.info(green(' * ') + bold('Scanning files'))

	libs_and_bins = set(libraries + binaries)

	scanned_files = scan_files(libs_and_bins, settings['CMD_MAX_ARGS'], logger)

	logger.warn(green(' * ') + bold('Checking dynamic linking consistency'))
	logger.debug('analyse(), Searching for %i libs, bins within %i libraries and links' %
		(len(libs_and_bins), len(libraries)+len(libraries_links))
	)

	broken = find_broken2(scanned_files, logger)
	broken_pathes = main_checks2(broken, scanned_files, logger)

	broken_la = extract_dependencies_from_la(la_libraries,
		libraries+libraries_links, _libs_to_check, logger)
	broken_pathes += broken_la

	logger.warn(green(' * ') + bold('Assign files to packages'))

	return assign_packages(broken_pathes, logger, settings)


if __name__ == '__main__':
	print("This script shouldn't be called directly")
