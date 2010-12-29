# Copyright(c) 2010, Gentoo Foundation
#
# Licensed under the GNU General Public License, v2 or higher
#
# $Header$

"""Provides access to Portage sets api"""

__docformat__ = 'epytext'

import portage
try:
	import portage.sets
	_sets_available = True
	SETPREFIX = portage.sets.SETPREFIX
except ImportError:
	_sets_available = False
	SETPREFIX = "@"

from gentoolkit import errors
from gentoolkit.atom import Atom


_set_config = None
def _init_set_config():
	global _set_config
	if _set_config is None:
		_set_config = portage.sets.load_default_config(
			portage.settings, portage.db[portage.root])

def get_available_sets():
	"""Returns all available sets."""

	if _sets_available:
		_init_set_config()
		return _set_config.getSets()
	return {}

def get_set_atoms(setname):
	"""Return atoms belonging to the given set

	@type setname: string
	@param setname: Name of the set
	@rtype list
	@return: List of atoms in the given set
	"""

	if _sets_available:
		_init_set_config()
		try:
			return set([Atom(str(x))
				for x in _set_config.getSetAtoms(setname)])
		except portage.sets.PackageSetNotFound:
			raise errors.GentoolkitSetNotFound(setname)
	raise errors.GentoolkitSetNotFound(setname)

# vim: set ts=4 sw=4 tw=79:
