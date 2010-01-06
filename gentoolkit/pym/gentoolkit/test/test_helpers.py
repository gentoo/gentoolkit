import os
import unittest
import warnings
from tempfile import NamedTemporaryFile
from test import test_support

from gentoolkit import helpers


class TestFileOwner(unittest.TestCase):

	def setUp(self):
		pass

	def tearDown(self):
		pass

	def test_extend_realpaths(self):
		extend_realpaths = helpers.FileOwner.extend_realpaths

		# Test that symlinks's realpaths are extended
		f1 = NamedTemporaryFile(prefix='equeryunittest')
		f2 = NamedTemporaryFile(prefix='equeryunittest')
		f3 = NamedTemporaryFile(prefix='equeryunittest')
		with warnings.catch_warnings():
			warnings.simplefilter("ignore")
			sym1 = os.tmpnam()
			os.symlink(f1.name, sym1)
			sym2 = os.tmpnam()
			os.symlink(f3.name, sym2)
		# We've created 3 files and 2 symlinks for testing. We're going to pass
		# in only the first two files and both symlinks. sym1 points to f1.
		# Since f1 is already in the list, sym1's realpath should not be added.
		# sym2 points to f3, but f3's not in our list, so sym2's realpath
		# should be added to the list.
		p = [f1.name, f2.name, sym1, sym2]
		p_xr = extend_realpaths(p)

		self.failUnlessEqual(p_xr[0], f1.name)
		self.failUnlessEqual(p_xr[1], f2.name)
		self.failUnlessEqual(p_xr[2], sym1)
		self.failUnlessEqual(p_xr[3], sym2)
		self.failUnlessEqual(p_xr[4], f3.name)

		# Clean up
		os.unlink(sym1)
		os.unlink(sym2)

		# Make sure we raise an exception if we don't get acceptable input
		self.failUnlessRaises(AttributeError, extend_realpaths, 'str')
		self.failUnlessRaises(AttributeError, extend_realpaths, set())


class TestGentoolkitHelpers(unittest.TestCase):

	def test_compare_package_strings(self):
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
			self.failUnless(
				helpers.compare_package_strings(vt[0], vt[1]) == -1
			)
		# Check greater than
		for vt in version_tests:
			self.failUnless(
				helpers.compare_package_strings(vt[1], vt[0]) == 1
			)
		# Check equal
		vt = ('sys-auth/pambase-20080318', 'sys-auth/pambase-20080318')
		self.failUnless(
			helpers.compare_package_strings(vt[0], vt[1]) == 0
		)

	def test_uses_globbing(self):
		globbing_tests = [
			('sys-apps/portage-2.1.6.13', False),
			('>=sys-apps/portage-2.1.6.13', False),
			('<=sys-apps/portage-2.1.6.13', False),
			('~sys-apps/portage-2.1.6.13', False),
			('=sys-apps/portage-2*', False),
			('sys-*/*-2.1.6.13', True),
			('sys-app?/portage-2.1.6.13', True),
			('sys-apps/[bp]ortage-2.1.6.13', True),
			('sys-apps/[!p]ortage*', True)
		]

		for gt in globbing_tests:
			self.failUnless(
				helpers.uses_globbing(gt[0]) == gt[1]
			)


def test_main():
	test_support.run_unittest(TestGentoolkitHelpers2)


if __name__ == '__main__':
	test_main()
