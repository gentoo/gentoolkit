#!/usr/bin/python

import re
import os
import glob
import stat

import portage
from portage.output import bold, red, blue, yellow, green, nocolor


def parse_conf(conf_file, visited=None, logger=None):
	''' Parses supplied conf_file for libraries pathes.
		conf_file is file or files to parse
		visited is set of files already parsed
	'''
	lib_dirs = set()
	to_parse = set()

	if isinstance(conf_file, basestring):
		conf_file = [conf_file]

	for conf in conf_file:
		try:
			with open(conf) as f:
				for line in f.readlines():
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

							to_parse = to_parse.union(glob.glob(path))
					else:
						lib_dirs.add(line)
		except EnvironmentError:
			logger.warn(yellow('Error when parsing file %s' %conf))

	if visited is None:
		visited = set()

	visited = visited.union(conf_file)
	to_parse = to_parse.difference(visited)
	if to_parse:
		lib_dirs = lib_dirs.union(parse_conf(to_parse, visited, logger=logger))

	return lib_dirs


def prepare_search_dirs(logger, settings):
	''' Lookup for search dirs. Returns tuple with two lists,
		(list_of_bin_dirs, list_of_lib_dirs)
	'''

	bin_dirs = set(['/bin', '/usr/bin', ])
	lib_dirs = set(['/lib', '/usr/lib', ])

	#try:
	with open(os.path.join(portage.root, settings['DEFAULT_ENV_FILE']), 'r') as f:
		for line in f.readlines():
			line = line.strip()
			m = re.match("^export (ROOT)?PATH='([^']+)'", line)
			if m is not None:
				bin_dirs = bin_dirs.union(set(m.group(2).split(':')))
	#except EnvironmentError:
		#logger.debug(yellow('Could not open file %s' % f))

	lib_dirs = parse_conf(settings['DEFAULT_LD_FILE'], logger=logger)
	return (bin_dirs, lib_dirs)


def parse_revdep_config(revdep_confdir):
	''' Parses all files under /etc/revdep-rebuild/ and returns
		tuple of: (masked_dirs, masked_files, search_dirs)'''

	search_dirs = set()
	masked_dirs = set()
	masked_files = set()

	#TODO: remove hard-coded path
	for f in os.listdir(revdep_confdir):
		for line in open(os.path.join('/etc/revdep-rebuild', f)):
			line = line.strip()
			if not line.startswith('#'): #first check for comment, we do not want to regex all lines
				m = re.match('LD_LIBRARY_MASK=\\"([^"]+)\\"', line)
				if m is not None:
					s = m.group(1).split(' ')
					masked_files = masked_files.union(s)
					continue
				m = re.match('SEARCH_DIRS_MASK=\\"([^"]+)\\"', line)
				if m is not None:
					s = m.group(1).split(' ')
					for ss in s:
						masked_dirs = masked_dirs.union(glob.glob(ss))
					continue
				m = re.match('SEARCH_DIRS=\\"([^"]+)\\"', line)
				if m is not None:
					s = m.group(1).split()
					for ss in s:
						search_dirs = search_dirs.union(glob.glob(ss))
					continue

	return (masked_dirs, masked_files, search_dirs)


def collect_libraries_from_dir(dirs, mask, logger):
	''' Collects all libraries from specified list of directories.
		mask is list of pathes, that are ommited in scanning, can be eighter single file or entire directory
		Returns tuple composed of: list of libraries, list of symlinks, and toupe with pair
		(symlink_id, library_id) for resolving dependencies
	'''


	found_directories = []  # contains list of directories found; allow us to reduce number of fnc calls
	found_files = []
	found_symlinks = []
	found_la_files = [] # la libraries
	symlink_pairs = []  # list of pairs symlink_id->library_id

	for d in dirs:
		if d in mask:
			continue

		try:
			for l in os.listdir(d):
				l = os.path.join(d, l)
				if l in mask:
					continue

				if os.path.isdir(l):
					if os.path.islink(l):
						#we do not want scan symlink-directories
						pass
					else:
						found_directories.append(l)
				elif os.path.isfile(l):
					if l.endswith('.so') or '.so.' or l.endswith('.a') in l:
						if l in found_files or l in found_symlinks:
							continue

						if os.path.islink(l):
							found_symlinks.append(l)
							abs_path = os.path.realpath(l)
							if abs_path in found_files:
								i = found_files.index(abs_path)
							else:
								found_files.append(abs_path)
								i = len(found_files)-1
							symlink_pairs.append((len(found_symlinks)-1, i,))
						else:
							found_files.append(l)
						continue
					elif l.endswith('.la'):
						if l in found_la_files:
							continue

						found_la_files.append(l)
					else:
						# sometimes there are binaries in libs' subdir, for example in nagios
						if not os.path.islink(l):
							if l in found_files or l in found_symlinks:
								continue
							prv = os.stat(l)[stat.ST_MODE]
							if prv & stat.S_IXUSR == stat.S_IXUSR or \
									prv & stat.S_IXGRP == stat.S_IXGRP or \
									prv & stat.S_IXOTH == stat.S_IXOTH:
								found_files.append(l)
		except Exception as ex:
			logger.debug(yellow('Exception during collecting libraries: ' + blue('%s')  %str(ex)))


	if found_directories:
		f,a,l,p = collect_libraries_from_dir(found_directories, mask, logger)
		found_files+=f
		found_la_files+=a
		found_symlinks+=l
		symlink_pairs+=p

	return (found_files, found_la_files, found_symlinks, symlink_pairs)


def collect_binaries_from_dir(dirs, mask, logger):
	''' Collects all binaries from specified list of directories.
		mask is list of pathes, that are ommited in scanning, can be eighter single file or entire directory
		Returns list of binaries
	'''

	found_directories = []  # contains list of directories found; allow us to reduce number of fnc calls
	found_files = []

	for d in dirs:
		if d in mask:
			continue

		try:
			for l in os.listdir(d):
				l = os.path.join(d, l)
				if d in mask:
					continue

				if os.path.isdir(l):
					if os.path.islink(l):
						#we do not want scan symlink-directories
						pass
					else:
						found_directories.append(l)
				elif os.path.isfile(l):
					#we're looking for binaries, and with binaries we do not need links, thus we can optimize a bit
					if not os.path.islink(l):
						prv = os.stat(l)[stat.ST_MODE]
						if prv & stat.S_IXUSR == stat.S_IXUSR or \
								prv & stat.S_IXGRP == stat.S_IXGRP or \
								prv & stat.S_IXOTH == stat.S_IXOTH:
							found_files.append(l)
		except Exception as e:
			logger.debug(yellow('Exception during binaries collecting: '+blue('%s') %str(e)))

	if found_directories:
		found_files += collect_binaries_from_dir(found_directories, mask, logger)

	return found_files



if __name__ == '__main__':
	import logging
	bin_dirs, lib_dirs = prepare_search_dirs(logging)

	masked_dirs, masked_files, ld = parse_revdep_config()
	lib_dirs = lib_dirs.union(ld)
	bin_dirs = bin_dirs.union(ld)
	masked_dirs = masked_dirs.union(set(['/lib/modules', '/lib32/modules', '/lib64/modules',]))

	libraries, la_libraries, libraries_links, symlink_pairs = collect_libraries_from_dir(lib_dirs, masked_dirs, logging)
	binaries = collect_binaries_from_dir(bin_dirs, masked_dirs, logging)

	logging.debug('Found: %i binaries and %i libraries.' %(len(binaries), len(libraries)))



