#!/usr/bin/python

"""Analysis module"""

from __future__ import print_function

import os
import re
import time

from portage.output import bold, blue, yellow, green

from .stuff import scan
from .collect import (prepare_search_dirs, parse_revdep_config,
	collect_libraries_from_dir, collect_binaries_from_dir)
from .assign import assign_packages
from .cache import save_cache

current_milli_time = lambda: int(round(time.time() * 1000))


def scan_files(libs_and_bins, cmd_max_args, logger, searchbits):
	'''Calls stuff.scan() and processes the data into a dictionary
	of scanned files information.

	@param libs_and_bins: set of libraries and binaries to scan for lib links.
	@param cmd_max_args: maximum number of files to pass into scanelf calls.
	@param logger: python style Logging function to use for output.
	@returns dict: {bit_length: {soname: {filename: set(needed)}}}
	'''
	stime = current_milli_time()
	scanned_files = {} # {bits: {soname: (filename, needed), ...}, ...}
	lines = scan(['-BF', '%F %f %S %n %M'],
				 libs_and_bins, cmd_max_args, logger)
	ftime = current_milli_time()
	logger.debug("\tscan_files(); total time to get scanelf data is "
		"%d milliseconds" % (ftime-stime))
	stime = current_milli_time()
	count = 0
	for line in lines:
		parts = line.split(' ')
		if len(parts) < 5:
			logger.error("\tscan_files(); error processing lib: %s" % line)
			logger.error("\tscan_files(); parts = %s" % str(parts))
			continue
		filename, sfilename, soname, needed, bits = parts
		filename = os.path.realpath(filename)
		needed = needed.split(',')
		bits = bits[8:] # 8: -> strlen('ELFCLASS')
		if bits not in searchbits:
			continue
		if not soname:
			soname = sfilename

		if bits not in scanned_files:
			scanned_files[bits] = {}
		if soname not in scanned_files[bits]:
			scanned_files[bits][soname] = {}
		if filename not in scanned_files[bits][soname]:
			scanned_files[bits][soname][filename] = set(needed)
			count += 1
		else:
			scanned_files[bits][soname][filename].update(needed)
	ftime = current_milli_time()
	logger.debug("\tscan_files(); total filenames found: %d in %d milliseconds"
		% (count, ftime-stime))
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

							logger.info('\t' + yellow(' * ') + _file +
								' is broken (requires: ' + bold(el)+')')
							broken.append(_file)
	return broken


class LibCheck(object):
	def __init__(self, scanned_files, logger, searchlibs=None, searchbits=None):
		'''LibCheck init function.

		@param scanned_files: optional dictionary if the type created by
				scan_files().  Defaults to the class instance of scanned_files
		@param logger: python style Logging function to use for output.
		@param searchlibs: optional set() of libraries to search for. If defined
				it toggles several settings to configure this class for
				a target search rather than a broken libs search.
		'''
		self.scanned_files = scanned_files
		self.logger = logger
		self.searchlibs = searchlibs
		self.searchbits = sorted(searchbits) or ['32', '64']
		self.logger.debug("\tLibCheck.__init__(), new searchlibs: %s" %(self.searchbits))
		if searchlibs:
			self.smsg = '\tLibCheck.search(), Checking for %s bit dependants'
			self.pmsg = yellow(" * ") + 'Files that depend on: %s (%s bits)'
			self.setlibs = self._setslibs
			self.check = self._checkforlib
		else:
			self.smsg = '\tLibCheck.search(), Checking for broken %s bit libs'
			self.pmsg = green(' * ') + bold('Broken files that requires:') + ' %s (%s bits)'
			self.setlibs = self._setlibs
			self.check = self._checkbroken
		self.sfmsg = "\tLibCheck.search(); Total found: %(count)d libs, %(deps)d files in %(time)d milliseconds"
		self.alllibs = None


	def _setslibs(self, l, b):
		'''Internal function.  Use the class's setlibs variable'''
		self.alllibs = '|'.join(
			[x for x in self.searchlibs if ('lib%s' % (b) in x)]) + '|'
		self.logger.debug("\tLibCheck._setslibs(), new alllibs: %s" %(self.alllibs))


	def _setlibs(self, l, b):
		'''Internal function.  Use the class's setlibs variable'''
		self.alllibs = '|'.join(l) + '|'


	def _checkforlib(self, l):
		'''Internal function.  Use the class's check variable'''
		if l:
			return l+'|' in self.alllibs
		return False


	def _checkbroken(self, l):
		'''Internal function.  Use the class's check variable'''
		if l:
			return l+'|' not in self.alllibs
		return False


	def search(self, scanned_files=None):
		'''Searches the scanned files for broken lib links
		or for libs to search for

		@param scanned_files: optional dictionary if the type created by
				scan_files(). Defaults to the class instance of scanned_files
		@ returns: dict: {bit_length: {found_lib: set(file_paths)}}.
		'''
		stime = current_milli_time()
		count = 0
		fcount = 0
		if not scanned_files:
			scanned_files = self.scanned_files
		found_libs = {}
		for bits in self.searchbits:
			try:
				scanned = scanned_files[bits]
			except KeyError:
				self.logger.debug('There are no %s-bit libraries'%bits) 
				continue
			self.logger.debug(self.smsg % bits)
			self.setlibs(sorted(scanned), bits)
			for soname, filepaths in scanned.items():
				for filename, needed in filepaths.items():
					for l in needed:
						if self.check(l):
							if not bits in found_libs:
								found_libs[bits] = {}
							try:
								found_libs[bits][l].add(filename)
							except KeyError:
								found_libs[bits][l] = set([filename])
								count += 1
							fcount += 1
							self.logger.debug("\tLibCheck.search(); FOUND:"
									" %sbit, %s, %s" % (bits, l, filename))
		ftime = current_milli_time()
		self.logger.debug(self.sfmsg % {'count': count, 'deps': fcount,
			'time': ftime-stime})
		return found_libs


	def process_results(self, found_libs, scanned_files=None):
		'''Processes the search results, logs the files found

		@param found_libs: dictionary of the type returned by search()
		@param scanned_files: optional dictionary if the type created by
				scan_files().  Defaults to the class instance of scanned_files
		@ returns: list: of filepaths from teh search results.
		'''
		stime = current_milli_time()
		if not scanned_files:
			scanned_files = self.scanned_files
		found_pathes = []
		for bits, found in found_libs.items():
			for lib, files in found.items():
				self.logger.info(self.pmsg  % (bold(lib), bits))
				for fp in sorted(files):
					self.logger.info('\t' +yellow('* ') + fp)
					found_pathes.append(fp)
		ftime = current_milli_time()
		self.logger.debug("\tLibCheck.process_results(); total filepaths found: "
			"%d in %d milliseconds" % (len(found_pathes), ftime-stime))
		return found_pathes


def analyse(settings, logger, libraries=None, la_libraries=None,
		libraries_links=None, binaries=None, _libs_to_check=None):
	"""Main program body.  It will collect all info and determine the
	pkgs needing rebuilding.

	@param logger: logger used for logging messages, instance of logging.Logger
				   class. Can be logging (RootLogger).
	@param _libs_to_check Libraries that need to be checked only
	@rtype list: list of pkgs that need rebuilding
	"""

	searchbits = set()
	if _libs_to_check:
		for lib in _libs_to_check:
			if "lib64" in lib:
				searchbits.add('64')
			elif "lib32" in lib:
				searchbits.add('32')
	else:
		_libs_to_check = set()
		searchbits.update(['64', '32'])

	if libraries and la_libraries and libraries_links and binaries:
		logger.info(blue(' * ') +
			bold('Found a valid cache, skipping collecting phase'))
	else:
		#TODO: add partial cache (for ex. only libraries)
		# when found for some reason

		stime = current_milli_time()
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
			'/lib64/modules',
			]
		)
		if '64' not in searchbits:
			masked_dirs.update(['/lib64', '/usr/lib64'])
		elif '32' not in searchbits:
			masked_dirs.update(['/lib32', '/usr/lib32'])

		logger.debug('\tanalyse(), bin directories:')
		for x in sorted(bin_dirs):
			logger.debug('\t\t%s' % (x))
		logger.debug('\tanalyse(), lib directories:')
		for x in sorted(lib_dirs):
			logger.debug('\t\t%s' % (x))
		logger.debug('\tanalyse(), masked directories:')
		for x in sorted(masked_dirs):
			logger.debug('\t\t%s' % (x))
		logger.debug('\tanalyse(), masked files:')
		for x in sorted(masked_files):
			logger.debug('\t\t%s' % (x))

		ftime = current_milli_time()
		logger.debug('\ttime to complete task: %d milliseconds' % (ftime-stime))
		stime = current_milli_time()
		logger.info(green(' * ') +
			bold('Collecting dynamic linking informations'))
		libraries, la_libraries, libraries_links = \
			collect_libraries_from_dir(lib_dirs, masked_dirs, logger)
		binaries = collect_binaries_from_dir(bin_dirs, masked_dirs, logger)
		ftime = current_milli_time()
		logger.debug('\ttime to complete task: %d milliseconds' % (ftime-stime))

		if settings['USE_TMP_FILES']:
			save_cache(logger=logger,
				to_save={'libraries':libraries, 'la_libraries':la_libraries,
					'libraries_links':libraries_links, 'binaries':binaries
				},
			temp_path=settings['DEFAULT_TMP_DIR']
			)


	logger.debug('\tanalyse(), Found %i libraries (+%i symlinks) and %i binaries' %
		(len(libraries), len(libraries_links), len(binaries))
	)
	logger.info(green(' * ') + bold('Scanning files'))

	libs_and_bins = libraries.union(binaries)

	scanned_files = scan_files(libs_and_bins, settings['CMD_MAX_ARGS'],
		logger, searchbits)

	logger.warn(green(' * ') + bold('Checking dynamic linking consistency'))
	logger.debug(
		'\tanalyse(), Searching for %i libs, bins within %i libraries and links'
		% (len(libs_and_bins), len(libraries)+len(libraries_links))
	)

	libcheck = LibCheck(scanned_files, logger, _libs_to_check, searchbits)

	broken_pathes = libcheck.process_results(libcheck.search())

	broken_la = extract_dependencies_from_la(la_libraries,
		libraries.union(libraries_links), _libs_to_check, logger)
	broken_pathes += broken_la

	logger.warn(green(' * ') + bold('Assign files to packages'))

	return assign_packages(broken_pathes, logger, settings)


if __name__ == '__main__':
	print("This script shouldn't be called directly")
