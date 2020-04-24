#!/usr/bin/python
# Copyright 2020 Gentoo Authors
# Distributed under the terms of the GNU General Public License v2
#
# Licensed under the GNU General Public License, v2

import os.path
import unittest

from gentoolkit.profile import load_profile_data


TESTDIR = os.path.join(os.path.dirname(__file__), '../ekeyword/tests')


class TestLoadProfileData(unittest.TestCase):
	"""Tests for load_profile_data"""

	def _test(self, subdir):
		portdir = os.path.join(TESTDIR, 'profiles', subdir)
		return load_profile_data(portdir=portdir)

	def testLoadBoth(self):
		"""Test loading both arch.list and profiles.desc"""
		ret = self._test('both')
		self.assertIn('arm', ret)
		self.assertEqual(ret['arm'], ('stable', 'arch'))
		self.assertIn('arm64', ret)
		self.assertEqual(ret['arm64'], ('exp', 'arch'))

	def testLoadArchOnly(self):
		"""Test loading only arch.list"""
		ret = self._test('arch-only')
		self.assertIn('arm', ret)
		self.assertEqual(ret['arm'], (None, 'arch'))
		self.assertIn('x86-solaris', ret)

	def testLoadProfilesOnly(self):
		"""Test loading only profiles.desc"""
		ret = self._test('profiles-only')
		self.assertIn('arm', ret)
		self.assertEqual(ret['arm'], ('stable', 'arch'))
		self.assertIn('arm64', ret)
		self.assertEqual(ret['arm64'], ('exp', 'arch'))

	def testLoadArchesDesc(self):
		"""Test loading arch.list, arches.desc and profiles.desc"""
		ret = self._test('arches-desc')
		self.assertIn('arm', ret)
		self.assertEqual(ret['arm'], ('stable', 'arch'))
		self.assertIn('arm64', ret)
		self.assertEqual(ret['arm64'], ('exp', 'arch'))
		self.assertIn('alpha', ret)
		self.assertEqual(ret['alpha'], ('stable', '~arch'))
		self.assertIn('sparc-fbsd', ret)
		self.assertEqual(ret['sparc-fbsd'], ('exp', '~arch'))

	def testLoadNone(self):
		"""Test running when neither files exists"""
		ret = self._test('none')
		self.assertEqual(ret, {})
