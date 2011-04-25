#!/bin/bash

import os
import time
import logging
from portage.output import red
from settings import DEFAULTS


def read_cache(temp_path=DEFAULTS['DEFAULT_TMP_DIR']):
	''' Reads cache information needed by analyse function.
		This function does not checks if files exists nor timestamps,
		check_temp_files should be called first
		@param temp_path: directory where all temp files should reside
		@return tuple with values of: libraries, la_libraries, libraries_links, symlink_pairs, binaries
	'''

	ret = {'libraries':[], 'la_libraries':[], 'libraries_links':[], 'binaries':[]}
	try:
		for key,val in ret.iteritems():
			f = open(os.path.join(temp_path, key))
			for line in f.readlines():
				val.append(line.strip())
			#libraries.remove('\n')
			f.close()
	except EnvironmentError:
		pass

	return (ret['libraries'], ret['la_libraries'], ret['libraries_links'], ret['binaries'])


def save_cache(logger=logging, to_save={}, temp_path=DEFAULTS['DEFAULT_TMP_DIR']):
	''' Tries to store caching information.
		@param logger
		@param to_save have to be dict with keys: libraries, la_libraries, libraries_links and binaries
	'''

	if not os.path.exists(temp_path):
		os.makedirs(temp_path)

	try:
		f = open(os.path.join(temp_path, 'timestamp'), 'w')
		f.write(str(int(time.time())))
		f.close()

		for key,val in to_save.iteritems():
			f = open(os.path.join(temp_path, key), 'w')
			for line in val:
				f.write(line + '\n')
			f.close()
	except Exception as ex:
		logger.warn(red('Could not save cache: %s' %str(ex)))



def check_temp_files(temp_path=DEFAULTS['DEFAULT_TMP_DIR'], max_delay=3600):
	''' Checks if temporary files from previous run are still available
		and if they aren't too old
		@param temp_path is directory, where temporary files should be found
		@param max_delay is maximum time difference (in seconds) when those files
				are still considered fresh and useful
		returns True, when files can be used, or False, when they don't
		exists or they are too old
	'''

	if not os.path.exists(temp_path) or not os.path.isdir(temp_path):
		return False

	timestamp_path = os.path.join(temp_path, 'timestamp')
	if not os.path.exists(timestamp_path) or not os.path.isfile(timestamp_path):
		return False

	try:
		f = open(timestamp_path)
		timestamp = int(f.readline())
		f.close()
	except:
		timestamp = 0
		return False

	diff = int(time.time()) - timestamp
	return max_delay > diff



if __name__ == '__main__':
	print 'Preparing cache ... '

	from collect import *

	bin_dirs, lib_dirs = prepare_search_dirs()

	masked_dirs, masked_files, ld = parse_revdep_config()
	lib_dirs = lib_dirs.union(ld)
	bin_dirs = bin_dirs.union(ld)
	masked_dirs = masked_dirs.union(set(['/lib/modules', '/lib32/modules', '/lib64/modules',]))

	libraries, la_libraries, libraries_links, symlink_pairs = collect_libraries_from_dir(lib_dirs, masked_dirs)
	binaries = collect_binaries_from_dir(bin_dirs, masked_dirs)

	save_cache(to_save={'libraries':libraries, 'la_libraries':la_libraries, 'libraries_links':libraries_links, 'binaries':binaries})

	print 'Done.'
