#!/usr/bin/python

"""Assign module
Functions used for determining the package the broken lib belongs to.
"""

from __future__ import print_function

import errno
import os
import io
import re
import time
current_milli_time = lambda: int(round(time.time() * 1000))

import portage
from portage import portdb
from portage.output import bold, red, yellow, green

# Make all str conversions unicode
try:
	str = unicode
except NameError:
	pass


class _file_matcher(object):
	"""
	Compares files by basename and parent directory (device, inode),
	so comparisons work regardless of directory symlinks. If a
	parent directory does not exist, the realpath of the parent
	directory is used instead of the (device, inode). When multiple
	files share the same parent directory, stat is only called
	once per directory, and the result is cached internally.
	"""
	def __init__(self):
		self._file_ids = {}
		self._added = {}

	def _file_id(self, filename):
		try:
			return self._file_ids[filename]
		except KeyError:
			try:
				st = os.stat(filename)
			except OSError as e:
				if e.errno != errno.ENOENT:
					raise
				file_id = (os.path.realpath(filename),)
			else:
				file_id = (st.st_dev, st.st_ino)

			self._file_ids[filename] = file_id
			return file_id

	def _file_key(self, filename):
		head, tail = os.path.split(filename)
		key = self._file_id(head) + (tail,)
		return key

	def add(self, filename):
		self._added[self._file_key(filename)] = filename

	def intersection(self, other):
		for file_key in self._added:
			match = other._added.get(file_key)
			if match is not None:
				yield match


def assign_packages(broken, logger, settings):
	''' Finds and returns packages that owns files placed in broken.
		Broken is list of files
	'''
	stime = current_milli_time()

	broken_matcher = _file_matcher()
	for filename in broken:
		broken_matcher.add(filename)

	assigned_pkgs = set()
	assigned_filenames = set()
	for group in os.listdir(settings['PKG_DIR']):
		grppath = settings['PKG_DIR'] + group
		if not os.path.isdir(grppath):
			continue
		for pkg in os.listdir(grppath):
			pkgpath = settings['PKG_DIR'] + group + '/' + pkg
			if not os.path.isdir(pkgpath):
				continue
			f = pkgpath + '/CONTENTS'
			if os.path.exists(f):
				contents_matcher = _file_matcher()
				try:
					with io.open(f, 'r', encoding='utf_8') as cnt:
						for line in cnt.readlines():
							m = re.match('^obj (/[^ ]+)', line)
							if m is not None:
								contents_matcher.add(m.group(1))
				except Exception as e:
					logger.warning(red(' !! Failed to read ' + f))
					logger.warning(red(' !! Error was:' + str(e)))
				else:
					for m in contents_matcher.intersection(broken_matcher):
						found = group+'/'+pkg
						assigned_pkgs.add(found)
						assigned_filenames.add(m)
						logger.info('\t' + green('* ') + m +
									' -> ' + bold(found))

	broken_filenames = set(broken)
	orphaned = broken_filenames.difference(assigned_filenames)
	ftime = current_milli_time()
	logger.debug("\tassign_packages(); assigned "
		"%d packages, %d orphans in %d milliseconds"
		% (len(assigned_pkgs), len(orphaned), ftime-stime))

	return (assigned_pkgs, orphaned)


def get_best_match(cpv, cp, logger):
	"""Tries to find another version of the pkg with the same slot
	as the deprecated installed version.  Failing that attempt to get any version
	of the same app

	@param cpv: string
	@param cp: string
	@rtype tuple: ([cpv,...], SLOT)
	"""

	slot = portage.db[portage.root]["vartree"].dbapi.aux_get(cpv, ["SLOT"])[0]
	logger.warning('\t%s "%s" %s.' % (yellow('* Warning:'), cpv,bold('ebuild not found.')))
	logger.debug('\tget_best_match(); Looking for %s:%s' %(cp, slot))
	try:
		match = portdb.match('%s:%s' %(cp, slot))
	except portage.exception.InvalidAtom:
		match = None

	if not match:
		logger.warning('\t' + red('!!') + ' ' + yellow(
			'Could not find ebuild for %s:%s' %(cp, slot)))
		slot = ['']
		match = portdb.match(cp)
		if not match:
			logger.warning('\t' + red('!!') + ' ' +
				yellow('Could not find ebuild for ' + cp))
	return match, slot


def get_slotted_cps(cpvs, logger):
	"""Uses portage to reduce the cpv list into a cp:slot list and returns it
	"""
	from portage.versions import catpkgsplit
	from portage import portdb

	cps = []
	for cpv in cpvs:
		parts = catpkgsplit(cpv)
		if not parts:
			logger.warning(('\t' + red("Failed to split the following pkg: "
				"%s, not a valid cat/pkg-ver" %cpv)))
			continue

		cp = parts[0] + '/' + parts[1]
		try:
			slot = portdb.aux_get(cpv, ["SLOT"])
		except KeyError:
			match, slot = get_best_match(cpv, cp, logger)
			if not match:
				logger.warning('\t' + red("Installed package: "
					"%s is no longer available" %cp))
				continue

		if slot[0]:
			cps.append(cp + ":" + slot[0])
		else:
			cps.append(cp)

	return cps



if __name__ == '__main__':
	print('Nothing to call here')
