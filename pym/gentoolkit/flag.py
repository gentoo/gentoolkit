#!/usr/bin/python
#
# Copyright(c) 2010, Gentoo Foundation
# Distributed under the terms of the GNU General Public License v2
#


"""Provides support functions for USE flag settings and analysis"""


__all__ = (
	'get_iuse',
	'get_installed_use',
	'reduce_flag',
	'reduce_flags',
	'filter_flags',
	'get_all_cpv_use',
	'get_flags'
)


import sys

from gentoolkit.dbapi import PORTDB, VARDB

import portage


def get_iuse(cpv):
	"""Gets the current IUSE flags from the tree

	To be used when a gentoolkit package object is not needed
	@type: cpv: string
	@param cpv: cat/pkg-ver
	@rtype list
	@returns [] or the list of IUSE flags
	"""
	try:
		return PORTDB.aux_get(cpv, ["IUSE"])[0].split()
	except:
		return []


def get_installed_use(cpv, use="USE"):
	"""Gets the installed USE flags from the VARDB

	To be used when a gentoolkit package object is not needed
	@type: cpv: string
	@param cpv: cat/pkg-ver
	@type use: string
	@param use: 1 of ["USE", "PKGUSE"]
	@rtype list
	@returns [] or the list of IUSE flags
	"""
	return VARDB.aux_get(cpv,[use])[0].split()


def reduce_flag(flag):
	"""Absolute value function for a USE flag

	@type flag: string
	@param flag: the use flag to absolute.
	@rtype: string
	@return absolute USE flag
	"""
	if flag[0] in ["+","-"]:
		return flag[1:]
	else:
		return flag


def reduce_flags(the_list):
	"""Absolute value function for a USE flag list

	@type the_list: list
	@param the_list: the use flags to absolute.
	@rtype: list
	@return absolute USE flags
	"""
	r=[]
	for member in the_list:
		r.append(reduce_flag(member))
	return r


def filter_flags(use, use_expand_hidden, usemasked, useforced):
	"""Filter function to remove hidden or otherwise not normally
	visible USE flags from a list.

	@type use: list
	@param use: the USE flag list to be filtered.
	@type use_expand_hidden: list
	@param  use_expand_hidden: list of flags hidden.
	@type usemasked: list
	@param usemasked: list of masked USE flags.
	@type useforced: list
	@param useforced: the forced USE flags.
	@rtype: list
	@return the filtered USE flags.
	"""
	# clean out some environment flags, since they will most probably
	# be confusing for the user
	for f in use_expand_hidden:
		f=f.lower() + "_"
		for x in use:
			if f in x:
				use.remove(x)
	# clean out any arch's
	archlist = portage.settings["PORTAGE_ARCHLIST"].split()
	for a in use[:]:
		if a in archlist:
			use.remove(a)
	# dbl check if any from usemasked  or useforced are still there
	masked = usemasked + useforced
	for a in use[:]:
		if a in masked:
			use.remove(a)
	return use


def get_all_cpv_use(cpv):
	"""Uses portage to determine final USE flags and settings for an emerge

	@type cpv: string
	@param cpv: eg cat/pkg-ver
	@rtype: lists
	@return  use, use_expand_hidden, usemask, useforce
	"""
	use = None
	PORTDB.settings.unlock()
	try:
		PORTDB.settings.setcpv(cpv, use_cache=True, mydb=portage.portdb)
		use = portage.settings['PORTAGE_USE'].split()
		use_expand_hidden = portage.settings["USE_EXPAND_HIDDEN"].split()
		usemask = list(PORTDB.settings.usemask)
		useforce =  list(PORTDB.settings.useforce)
	except KeyError:
		PORTDB.settings.reset()
		PORTDB.settings.lock()
		return [], [], [], []
	# reset cpv filter
	PORTDB.settings.reset()
	PORTDB.settings.lock()
	return use, use_expand_hidden, usemask, useforce


def get_flags(cpv, final_setting=False):
	"""Retrieves all information needed to filter out hidded, masked, etc.
	USE flags for a given package.

	@type cpv: string
	@param cpv: eg. cat/pkg-ver
	@type final_setting: boolean
	@param final_setting: used to also determine the final
		enviroment USE flag settings and return them as well.
	@rtype: list or list, list
	@return IUSE or IUSE, final_flags
	"""
	final_use, use_expand_hidden, usemasked, useforced = get_all_cpv_use(cpv)
	iuse_flags = filter_flags(get_iuse(cpv), use_expand_hidden, usemasked, useforced)
	#flags = filter_flags(use_flags, use_expand_hidden, usemasked, useforced)
	if final_setting:
		final_flags = filter_flags(final_use,  use_expand_hidden, usemasked, useforced)
		return iuse_flags, final_flags
	return iuse_flags
