#!/usr/bin/python

"""Data collection module"""

import re
from portage import os
import glob
import stat

import portage
from portage import _encodings, _unicode_encode
from portage.output import blue, yellow
from .settings import parse_revdep_config


def parse_conf(conf_file, visited=None, logger=None):
	''' Parses supplied conf_file for libraries pathes.
		conf_file is file or files to parse
		visited is set of files already parsed
	'''
	lib_dirs = set()
	to_parse = set()

	if isinstance(conf_file, str):
		conf_file = [conf_file]

	for conf in conf_file:
		try:
			with open(_unicode_encode(conf, encoding=_encodings['fs']),
					encoding=_encodings['content']) as _file:
				for line in _file.readlines():
					line = line.strip()
					if line.startswith('#'):
						continue
					elif line.startswith('include'):
						include_line = line.split()[1:]
						for included in include_line:
							if not included.startswith('/'):
								path = os.path.join(os.path.dirname(conf), \
													included)
							else:
								path = included

							to_parse.update(glob.glob(path))
					else:
						lib_dirs.add(line)
		except EnvironmentError:
			logger.warn('\t' + yellow('Error when parsing file %s' %conf))

	if visited is None:
		visited = set()

	visited.update(conf_file)
	to_parse = to_parse.difference(visited)
	if to_parse:
		lib_dirs.update(parse_conf(to_parse, visited, logger=logger))

	return lib_dirs


def prepare_search_dirs(logger, settings):
	''' Lookup for search dirs. Returns tuple with two lists,
		(list_of_bin_dirs, list_of_lib_dirs)
	'''

	bin_dirs = set(['/bin', '/usr/bin', ])
	lib_dirs = set(['/lib', '/usr/lib', ])

	#try:
	with open(_unicode_encode(os.path.join(
		portage.root, settings['DEFAULT_ENV_FILE']),
		encoding=_encodings['fs']), mode='r',
		encoding=_encodings['content']) as _file:
		for line in _file.readlines():
			line = line.strip()
			match = re.match(r"^export (ROOT)?PATH='([^']+)'", line)
			if match is not None:
				bin_dirs.update(set(match.group(2).split(':')))
	#except EnvironmentError:
		#logger.debug('\t' + yellow('Could not open file %s' % f))

	lib_dirs = parse_conf(settings['DEFAULT_LD_FILE'], logger=logger)
	return (bin_dirs, lib_dirs)



def collect_libraries_from_dir(dirs, mask, logger):
	''' Collects all libraries from specified list of directories.
		mask is list of pathes, that are ommited in scanning, can be eighter single file or entire directory
		Returns tuple composed of: list of libraries, list of symlinks, and toupe with pair
		(symlink_id, library_id) for resolving dependencies
	'''

	# contains list of directories found
	# allows us to reduce number of fnc calls
	found_directories = set()
	found_files = set()
	found_symlinks = set()
	found_la_files = set() # la libraries

	for _dir in dirs:
		if _dir in mask:
			continue

		try:
			for _listing in os.listdir(_dir):
				listing = os.path.join(_dir, _listing)
				if listing in mask or _listing in mask:
					continue

				if os.path.isdir(listing):
					if os.path.islink(listing):
						#we do not want scan symlink-directories
						pass
					else:
						found_directories.add(listing)
				elif os.path.isfile(listing):
					if (listing.endswith('.so') or
						listing.endswith('.a') or
						'.so.' in listing
						):

						if os.path.islink(listing):
							found_symlinks.add(listing)
						else:
							found_files.add(listing)
						continue
					elif listing.endswith('.la'):
						if listing in found_la_files:
							continue

						found_la_files.add(listing)
					else:
						# sometimes there are binaries in libs' subdir,
						# for example in nagios
						if not os.path.islink(listing):
							#if listing in found_files or listing in found_symlinks:
								#continue
							prv = os.stat(listing)[stat.ST_MODE]
							if prv & stat.S_IXUSR == stat.S_IXUSR or \
									prv & stat.S_IXGRP == stat.S_IXGRP or \
									prv & stat.S_IXOTH == stat.S_IXOTH:
								found_files.add(listing)
		except Exception as ex:
			logger.debug('\t' +
				yellow('Exception collecting libraries: ' +
				blue('%s')  %str(ex)))

	if found_directories:
		_file, la_file, link = \
			collect_libraries_from_dir(found_directories, mask, logger)
		found_files.update(_file)
		found_la_files.update(la_file)
		found_symlinks.update(link)
	return (found_files, found_la_files, found_symlinks)


def collect_binaries_from_dir(dirs, mask, logger):
	''' Collects all binaries from specified list of directories.
		mask is list of pathes, that are ommited in scanning,
		can be eighter single file or entire directory
		Returns list of binaries
	'''

	# contains list of directories found
	# allows us to reduce number of fnc calls
	found_directories = set()
	found_files = set()

	for _dir in dirs:
		if _dir in mask:
			continue

		try:
			for _listing in os.listdir(_dir):
				listing = os.path.join(_dir, _listing)
				if listing in mask or _listing in mask:
					continue

				if os.path.isdir(listing):
					if os.path.islink(listing):
						#we do not want scan symlink-directories
						pass
					else:
						found_directories.add(listing)
				elif os.path.isfile(listing):
					# we're looking for binaries
					# and with binaries we do not need links
					# thus we can optimize a bit
					if not os.path.islink(listing):
						prv = os.stat(listing)[stat.ST_MODE]
						if prv & stat.S_IXUSR == stat.S_IXUSR or \
								prv & stat.S_IXGRP == stat.S_IXGRP or \
								prv & stat.S_IXOTH == stat.S_IXOTH:
							found_files.add(listing)
		except Exception as ex:
			logger.debug('\t' +
				yellow('Exception during binaries collecting: '+
				blue('%s') %str(ex)))

	if found_directories:
		found_files.update(collect_binaries_from_dir(found_directories, mask, logger))

	return found_files



if __name__ == '__main__':
	import logging
	bin_dirs, lib_dirs = prepare_search_dirs(logging)

	masked_dirs, masked_files, ld = parse_revdep_config()
	lib_dirs.update(ld)
	bin_dirs.update(ld)
	masked_dirs.update(
		set([
			'/lib/modules',
			'/lib32/modules',
			'/lib64/modules',
		])
	)

	libraries, la_libraries, libraries_links = \
		collect_libraries_from_dir(lib_dirs, masked_dirs, logging)
	binaries = collect_binaries_from_dir(bin_dirs, masked_dirs, logging)

	logging.debug(
		'Found: %i binaries and %i libraries.' %(
		len(binaries), len(libraries)))



