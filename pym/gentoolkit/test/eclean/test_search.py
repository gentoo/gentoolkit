# Copyright(c) 2009, Gentoo Foundation
# Copyright: 2006-2008 Brian Harring <ferringb@gmail.com>
# Copyright 2010 Brian Dolbec <brian.dolbec@gmail.com>
#
# License: GPL2/BSD

# $Header$


from __future__ import print_function


import unittest
from test import test_support

from gentoolkit.eclean.search import *

class Dbapi(object):
	"""Fake portage dbapi class used to return
	pre-determined test data in place of a live system

	@param cp_all: list of cat/pkg's to use for testing
				eg: ['app-portage/gentoolkit', 'app-portage/porthole',...]
	@param cpv_all: list of cat/pkg-ver's to use for testing.
	@param props: dictionary of ebuild properties to use for testing.
				eg: {'cpv': {"SRC_URI": 'http://...', "RESTRICT": restriction},}
	@param cp_list: ?????????
	"""

	def __init__(self, cp_all=[], cpv_all=[], props={}, cp_list=[]):
		self._cp_all = cp_all
		self._cpv_all = cpv_all
		self._props = props
		self._cp_list = cp_list

	def cp_all(self):
		return self._cp_all[:]

	def cp_list(self, package):
		#need to determine the data to return
		# and gather some from a live system to use for testing
		pass

	def cpv_all(self):
		return self._cpv_all

	def cpv_exists(self, cpv):
		return cpv in self._cpv_all

	def aux_get(self, cpv, prop_list):
		"""only need stubs for ["SRC_URI","RESTRICT"]
		"""
		props = []
		for prop in prop_list:
			props.append(self._props[cpv][prop])
		return props




"""Tests for eclean's search modules."""

class TestFindDistfiles(unittest.TestCase):
	uris = [
		u'/usr/portage/distfiles/xdg-utils-1.0.2.tgz',
		u'/usr/portage/distfiles/readline60-003',
		u'/usr/portage/distfiles/bash-completion-1.1.tar.bz2',
		u'/usr/portage/distfiles/libgweather-2.26.2.1.tar.bz2',
		u'/usr/portage/distfiles/libwnck-2.26.2.tar.bz2',
		u'/usr/portage/distfiles/gnome-cups-manager-0.33.tar.bz2',
		u'/usr/portage/distfiles/audiofile-0.2.6-constantise.patch.bz2',
		u'/usr/portage/distfiles/vixie-cron-4.1-gentoo-r4.patch.bz2',
		u'/usr/portage/distfiles/evince-2.26.2.tar.bz2',
		u'/usr/portage/distfiles/lxml-2.2.2.tgz'
	]
	filenames = [
		u'audiofile-0.2.6-constantise.patch.bz2',
		u'bash-completion-1.1.tar.bz2',
		u'evince-2.26.2.tar.bz2',
		u'gnome-cups-manager-0.33.tar.bz2',
		u'libgweather-2.26.2.1.tar.bz2',
		u'libwnck-2.26.2.tar.bz2',
		u'lxml-2.2.2.tgz',
		u'readline60-003',
		u'vixie-cron-4.1-gentoo-r4.patch.bz2',
		u'xdg-utils-1.0.2.tgz'
	]

	def test_get_filenames_from_uris(self):
		fns = sorted(get_filenames_from_uris(self.uris))
		print(fns)
		for fn, fn2 in zip(self.filenames, fns):
			self.failUnlessEqual(fn, fn2)


def test_main():
	test_support.run_unittest(TestFindDistfiles)

if __name__ == '__main__':
	test_main()
