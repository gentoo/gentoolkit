#!/usr/bin/python
# Copyright 2020 Gentoo Authors
# Distributed under the terms of the GNU General Public License v2
#
# Licensed under the GNU General Public License, v2

"""Routines to load profile information for ekeyword/eshowkw"""

__all__ = (
	'load_profile_data',
)


import os.path
import portage
import sys

from portage import _encodings, _unicode_encode


def warning(msg):
	"""Write |msg| as a warning to stderr"""
	print('warning: %s' % msg, file=sys.stderr)


def load_profile_data(portdir=None, repo='gentoo'):
	"""Load the list of known arches from the tree

	Args:
	  portdir: The repository to load all data from (and ignore |repo|)
	  repo: Look up this repository by name to locate profile data

	Returns:
	  A dict mapping the keyword to its preferred state:
	  {'x86': ('stable', 'arch'), 'mips': ('dev', '~arch'), ...}
	"""
	if portdir is None:
		portdir = portage.db[portage.root]['vartree'].settings.repositories[repo].location

	arch_status = {}

	try:
		arch_list = os.path.join(portdir, 'profiles', 'arch.list')
		with open(_unicode_encode(arch_list, encoding=_encodings['fs']),
				encoding=_encodings['content']) as f:
			for line in f:
				line = line.split('#', 1)[0].strip()
				if line:
					arch_status[line] = None
	except IOError:
		pass

	try:
		profile_status = {
			'stable': 0,
			'dev': 1,
			'exp': 2,
			None: 3,
		}
		profiles_list = os.path.join(portdir, 'profiles', 'profiles.desc')
		with open(_unicode_encode(profiles_list, encoding=_encodings['fs']),
				encoding=_encodings['content']) as f:
			for line in f:
				line = line.split('#', 1)[0].split()
				if line:
					arch, _profile, status = line
					arch_status.setdefault(arch, status)
					curr_status = profile_status[arch_status[arch]]
					new_status = profile_status[status]
					if new_status < curr_status:
						arch_status[arch] = status
	except IOError:
		pass

	if arch_status:
		arch_status['all'] = None
	else:
		warning('could not read profile files: %s' % arch_list)
		warning('will not be able to verify args are correct')

	arches_desc = {}
	try:
		arches_list = os.path.join(portdir, 'profiles', 'arches.desc')
		with open(_unicode_encode(arches_list, encoding=_encodings['fs']),
				encoding=_encodings['content']) as f:
			for line in f:
				line = line.split('#', 1)[0].split()
				if line:
					arch, status = line
					arches_desc[arch] = status
	except IOError:
		# backwards compatibility
		arches_desc = {
			'alpha': 'testing',
			'ia64': 'testing',
			'm68k': 'testing',
			'mips': 'testing',
			'riscv': 'testing',
		}
		for k in arch_status:
			if '-' in k:
				arches_desc[k] = 'testing'

	for k, v in arch_status.items():
		if arches_desc.get(k) == 'testing':
			arch_status[k] = (v, '~arch')
		else:
			# TODO: explicit distinction of transitional, bad values?
			arch_status[k] = (v, 'arch')

	return arch_status
