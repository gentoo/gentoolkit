#!/usr/bin/python
#
# Copyright(c) 2009, Gentoo Foundation
#
# Licensed under the GNU General Public License, v2
#
# $Header$

import unittest

from gentoolkit.cpv import *
from gentoolkit.test import cmp

class TestGentoolkitCPV(unittest.TestCase):

	def assertEqual2(self, o1, o2):
		# logic bugs hidden behind short circuiting comparisons for metadata
		# is why we test the comparison *both* ways.
		self.assertEqual(o1, o2)
		c = cmp(o1, o2)
		self.assertEqual(c, 0,
			msg="checking cmp for %r, %r, aren't equal: got %i" % (o1, o2, c))
		self.assertEqual(o2, o1)
		c = cmp(o2, o1)
		self.assertEqual(c, 0,
			msg="checking cmp for %r, %r,aren't equal: got %i" % (o2, o1, c))

	def assertNotEqual2(self, o1, o2):
		# is why we test the comparison *both* ways.
		self.assertNotEqual(o1, o2)
		c = cmp(o1, o2)
		self.assertNotEqual(c, 0,
			msg="checking cmp for %r, %r, not supposed to be equal, got %i"
				% (o1, o2, c))
		self.assertNotEqual(o2, o1)
		c = cmp(o2, o1)
		self.assertNotEqual(c, 0,
			msg="checking cmp for %r, %r, not supposed to be equal, got %i"
				% (o2, o1, c))

	def test_comparison(self):
		self.assertEqual2(CPV('pkg'), CPV('pkg'))
		self.assertNotEqual2(CPV('pkg'), CPV('pkg1'))
		self.assertEqual2(CPV('cat/pkg'), CPV('cat/pkg'))
		self.assertNotEqual2(CPV('cat/pkg'), CPV('cat/pkgb'))
		self.assertNotEqual2(CPV('cata/pkg'), CPV('cat/pkg'))
		self.assertEqual2(CPV('cat/pkg-0.1'), CPV('cat/pkg-0.1'))
		self.assertNotEqual2(CPV('cat/pkg-1.0'), CPV('cat/pkg-1'))
		self.assertEqual2(CPV('cat/pkg-0'), CPV('cat/pkg-0'))
		self.assertEqual2(CPV('cat/pkg-1-r1'), CPV('cat/pkg-1-r1'))
		self.assertNotEqual2(CPV('cat/pkg-2-r1'), CPV('cat/pkg-2-r10'))
		self.assertEqual2(CPV('cat/pkg-1_rc2'), CPV('cat/pkg-1_rc2'))
		self.assertNotEqual2(CPV('cat/pkg-2_rc2-r1'), CPV('cat/pkg-2_rc1-r1'))

	def test_compare_strs(self):
		# Test ordering of package strings, Portage has test for vercmp,
		# so just do the rest
		version_tests = [
			# different categories
			('sys-apps/portage-2.1.6.8', 'sys-auth/pambase-20080318'),
			# different package names
			('sys-apps/pkgcore-0.4.7.15-r1', 'sys-apps/portage-2.1.6.8'),
			# different package versions
			('sys-apps/portage-2.1.6.8', 'sys-apps/portage-2.2_rc25')
		]
		# Check less than
		for vt in version_tests:
			self.failUnless(compare_strs(vt[0], vt[1]) == -1)
		# Check greater than
		for vt in version_tests:
			self.failUnless(compare_strs(vt[1], vt[0]) == 1)
		# Check equal
		vt = ('sys-auth/pambase-20080318', 'sys-auth/pambase-20080318')
		self.failUnless(compare_strs(vt[0], vt[1]) == 0)

	def test_chunk_splitting(self):
		all_tests = [
			# simple
			('sys-apps/portage-2.2', {
				'category': 'sys-apps',
				'name': 'portage',
				'cp': 'sys-apps/portage',
				'version': '2.2',
				'revision': '',
				'fullversion': '2.2'
			}),
			# with rc
			('sys-apps/portage-2.2_rc10', {
				'category': 'sys-apps',
				'name': 'portage',
				'cp': 'sys-apps/portage',
				'version': '2.2_rc10',
				'revision': '',
				'fullversion': '2.2_rc10'
			}),
			# with revision
			('sys-apps/portage-2.2_rc10-r1', {
				'category': 'sys-apps',
				'name': 'portage',
				'cp': 'sys-apps/portage',
				'version': '2.2_rc10',
				'revision': 'r1',
				'fullversion': '2.2_rc10-r1'
			}),
			# with dash (-) in name (Bug #316961)
			('c-portage', {
				'category': '',
				'name': 'c-portage',
				'cp': 'c-portage',
				'version': '',
				'revision': '',
				'fullversion': ''
			}),
			# with dash (-) in name (Bug #316961)
			('sys-apps/c-portage-2.2_rc10-r1', {
				'category': 'sys-apps',
				'name': 'c-portage',
				'cp': 'sys-apps/c-portage',
				'version': '2.2_rc10',
				'revision': 'r1',
				'fullversion': '2.2_rc10-r1'
			}),
		]

		for test in all_tests:
			cpv = CPV(test[0])
			keys = ('category', 'name', 'cp', 'version', 'revision', 'fullversion')
			for k in keys:
				self.failUnlessEqual(
					getattr(cpv, k), test[1][k]
				)


def test_main():
	suite = unittest.TestLoader().loadTestsFromTestCase(TestGentoolkitCPV)
	unittest.TextTestRunner(verbosity=2).run(suite)
test_main.__test__ = False


if __name__ == '__main__':
	test_main()
