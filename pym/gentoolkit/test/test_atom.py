# Copyright(c) 2009, Gentoo Foundation
# Copyright: 2006-2008 Brian Harring <ferringb@gmail.com>
#
# License: GPL2/BSD

# $Header$

import unittest

from gentoolkit.atom import *
from gentoolkit.test import cmp

"""Atom test suite (verbatim) from pkgcore."""

class TestGentoolkitAtom(unittest.TestCase):

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
		self.assertEqual2(Atom('cat/pkg'), Atom('cat/pkg'))
		self.assertNotEqual2(Atom('cat/pkg'), Atom('cat/pkgb'))
		self.assertNotEqual2(Atom('cata/pkg'), Atom('cat/pkg'))
		self.assertNotEqual2(Atom('cat/pkg'), Atom('!cat/pkg'))
		self.assertEqual2(Atom('!cat/pkg'), Atom('!cat/pkg'))
		self.assertNotEqual2(Atom('=cat/pkg-0.1:0'),
			Atom('=cat/pkg-0.1'))
		self.assertNotEqual2(Atom('=cat/pkg-1[foon]'),
			Atom('=cat/pkg-1'))
		self.assertEqual2(Atom('=cat/pkg-0'), Atom('=cat/pkg-0'))
		self.assertNotEqual2(Atom('<cat/pkg-2'), Atom('>cat/pkg-2'))
		self.assertNotEqual2(Atom('=cat/pkg-2*'), Atom('=cat/pkg-2'))
		# Portage Atom doesn't have 'negate_version' capability
		#self.assertNotEqual2(Atom('=cat/pkg-2', True), Atom('=cat/pkg-2'))

		# use...
		self.assertNotEqual2(Atom('cat/pkg[foo]'), Atom('cat/pkg'))
		self.assertNotEqual2(Atom('cat/pkg[foo]'),
							 Atom('cat/pkg[-foo]'))
		self.assertEqual2(Atom('cat/pkg[foo,-bar]'),
						  Atom('cat/pkg[-bar,foo]'))

		# repoid not supported by Portage Atom yet
		## repoid
		#self.assertEqual2(Atom('cat/pkg::a'), Atom('cat/pkg::a'))
		#self.assertNotEqual2(Atom('cat/pkg::a'), Atom('cat/pkg::b'))
		#self.assertNotEqual2(Atom('cat/pkg::a'), Atom('cat/pkg'))

		# slots.
		self.assertNotEqual2(Atom('cat/pkg:1'), Atom('cat/pkg'))
		self.assertEqual2(Atom('cat/pkg:2'), Atom('cat/pkg:2'))
		# http://dev.gentoo.org/~tanderson/pms/eapi-2-approved/pms.html#x1-190002.1.2
		self.assertEqual2(Atom('cat/pkg:AZaz09+_.-'), Atom('cat/pkg:AZaz09+_.-'))
		for lesser, greater in (('0.1', '1'), ('1', '1-r1'), ('1.1', '1.2')):
			self.assertTrue(Atom('=d/b-%s' % lesser) <
				Atom('=d/b-%s' % greater),
				msg="d/b-%s < d/b-%s" % (lesser, greater))
			self.assertFalse(Atom('=d/b-%s' % lesser) >
				Atom('=d/b-%s' % greater),
				msg="!: d/b-%s < d/b-%s" % (lesser, greater))
			self.assertTrue(Atom('=d/b-%s' % greater) >
				Atom('=d/b-%s' % lesser),
				msg="d/b-%s > d/b-%s" % (greater, lesser))
			self.assertFalse(Atom('=d/b-%s' % greater) <
				Atom('=d/b-%s' % lesser),
				msg="!: d/b-%s > d/b-%s" % (greater, lesser))

		#self.assertTrue(Atom("!!=d/b-1", eapi=2) > Atom("!=d/b-1"))
		self.assertTrue(Atom("!=d/b-1") < Atom("!!=d/b-1"))
		self.assertEqual(Atom("!=d/b-1"), Atom("!=d/b-1"))

	def test_intersects(self):
		for this, that, result in [
			('cat/pkg', 'pkg/cat', False),
			('cat/pkg', 'cat/pkg', True),
			('cat/pkg:1', 'cat/pkg:1', True),
			('cat/pkg:1', 'cat/pkg:2', False),
			('cat/pkg:1', 'cat/pkg[foo]', True),
			('cat/pkg[foo]', 'cat/pkg[-bar]', True),
			('cat/pkg[foo]', 'cat/pkg[-foo]', False),
			('>cat/pkg-3', '>cat/pkg-1', True),
			('>cat/pkg-3', '<cat/pkg-3', False),
			('>=cat/pkg-3', '<cat/pkg-3', False),
			('>cat/pkg-2', '=cat/pkg-2*', True),
			# Portage vercmp disagrees with this one:
			#('<cat/pkg-2_alpha1', '=cat/pkg-2*', True),
			('=cat/pkg-2', '=cat/pkg-2', True),
			('=cat/pkg-3', '=cat/pkg-2', False),
			('=cat/pkg-2', '>cat/pkg-2', False),
			('=cat/pkg-2', '>=cat/pkg-2', True),
			('~cat/pkg-2', '~cat/pkg-2', True),
			('~cat/pkg-2', '~cat/pkg-2.1', False),
			('=cat/pkg-2*', '=cat/pkg-2.3*', True),
			('>cat/pkg-2.4', '=cat/pkg-2*', True),
			('<cat/pkg-2.4', '=cat/pkg-2*', True),
			('<cat/pkg-1', '=cat/pkg-2*', False),
			('~cat/pkg-2', '>cat/pkg-2-r1', True),
			('~cat/pkg-2', '<=cat/pkg-2', True),
			('=cat/pkg-2-r2*', '<=cat/pkg-2-r20', True),
			('=cat/pkg-2-r2*', '<cat/pkg-2-r20', True),
			('=cat/pkg-2-r2*', '<=cat/pkg-2-r2', True),
			('~cat/pkg-2', '<cat/pkg-2', False),
			('=cat/pkg-1-r10*', '~cat/pkg-1', True),
			('=cat/pkg-1-r1*', '<cat/pkg-1-r1', False),
			('=cat/pkg-1*', '>cat/pkg-2', False),
			('>=cat/pkg-8.4', '=cat/pkg-8.3.4*', False),
			# Repos not yet supported by Portage
			#('cat/pkg::gentoo', 'cat/pkg', True),
			#('cat/pkg::gentoo', 'cat/pkg::foo', False),
			('=sys-devel/gcc-4.1.1-r3', '=sys-devel/gcc-3.3*', False),
			('=sys-libs/db-4*', '~sys-libs/db-4.3.29', True),
		]:
			this_atom = Atom(this)
			that_atom = Atom(that)
			self.assertEqual(
				result, this_atom.intersects(that_atom),
				'%s intersecting %s should be %s' % (this, that, result))
			self.assertEqual(
				result, that_atom.intersects(this_atom),
				'%s intersecting %s should be %s' % (that, this, result))


def test_main():
        suite = unittest.TestLoader().loadTestsFromTestCase(TestGentoolkitAtom)
        unittest.TextTestRunner(verbosity=2).run(suite)
test_main.__test__ = False


if __name__ == '__main__':
	test_main()
