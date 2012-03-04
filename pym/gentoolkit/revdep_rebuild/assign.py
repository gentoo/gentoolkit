#!/usr/bin/python

"""Assign module
Functions used for determining the package the broken lib belongs to.
"""

from __future__ import print_function

import os
import re

import portage
from portage.versions import catpkgsplit
from portage import portdb
from portage.output import bold, red, yellow

# ignore these files or directories if found
IGNORED = ['.cache', 'world', 'world~', 'world.bak']

def assign_packages(broken, logger, settings):
	''' Finds and returns packages that owns files placed in broken.
		Broken is list of files
	'''
	assigned = set()
	for group in os.listdir(settings['PKG_DIR']):
		if group in IGNORED:
			continue
		elif os.path.isfile(settings['PKG_DIR'] + group):
			if not group.startswith('.keep_'):
				logger.warn(yellow(" * Invalid category found in the installed pkg db: ") +
					bold(settings['PKG_DIR'] + group))
			continue
		for pkg in os.listdir(settings['PKG_DIR'] + group):
			if '-MERGING-' in pkg:
				logger.warn(yellow(" * Invalid/incomplete package merge found in the installed pkg db: ") +
						bold(settings['PKG_DIR'] + pkg))
				continue
			_file = settings['PKG_DIR'] + group + '/' + pkg + '/CONTENTS'
			if os.path.exists(_file):
				try:
					with open(_file, 'r') as cnt:
						for line in cnt:
							matches = re.match('^obj (/[^ ]+)', line)
							if matches is not None:
								match = matches.group(1)
								if match in broken:
									found = group+'/'+pkg
									if found not in assigned:
										assigned.add(found)
									logger.info('\t' + match + ' -> '
										+ bold(found))
				except Exception as ex:
					logger.warn(red(' !! Failed to read ' + _file) +
						" Original exception was:\n" + str(ex))

	return assigned


def get_best_match(cpv, cp, logger):
	"""Tries to find another version of the pkg with the same slot
	as the deprecated installed version.  Failing that attempt to get any version
	of the same app

	@param cpv: string
	@param cp: string
	@rtype tuple: ([cpv,...], SLOT)
	"""

	slot = portage.db[portage.root]["vartree"].dbapi.aux_get(cpv, ["SLOT"])
	logger.warn(yellow('Warning: ebuild "' + cpv + '" not found.'))
	logger.info('Looking for %s:%s' %(cp, slot))
	try:
		match = portdb.match('%s:%s' %(cp, slot))
	except portage.exception.InvalidAtom:
		match = None

	if not match:
		logger.warn(red('!!') + ' ' + yellow(
			'Could not find ebuild for %s:%s' %(cp, slot)))
		slot = ['']
		match = portdb.match(cp)
		if not match:
			logger.warn(red('!!') + ' ' + 
				yellow('Could not find ebuild for ' + cp))
	return match, slot


def get_slotted_cps(cpvs, logger):
	"""Uses portage to reduce the cpv list into a cp:slot list and returns it
	"""

	cps = []
	for cpv in cpvs:
		parts = catpkgsplit(cpv)
		cp = parts[0] + '/' + parts[1]
		try:
			slot = portdb.aux_get(cpv, ["SLOT"])
		except KeyError:
			match, slot = get_best_match(cpv, cp, logger)
			if not match:
				logger.warn(red("Installed package: "
					"%s is no longer available" %cp))
				continue

		if slot[0]:
			cps.append(cp + ":" + slot[0])
		else:
			cps.append(cp)

	return cps



if __name__ == '__main__':
	print('Nothing to call here')
