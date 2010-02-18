#!/usr/bin/python
#
# Copyright(c) 2009-2010, Gentoo Foundation
#
# Licensed under the GNU General Public License, v2
#
# $Header$

import unittest
from test import test_support

from gentoolkit.cpv import *

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

def test_main():
	test_support.run_unittest(TestGentoolkitCPV)

if __name__ == '__main__':
	test_main()
