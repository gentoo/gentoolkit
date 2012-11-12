import sys
import unittest
import warnings
from tempfile import NamedTemporaryFile

from gentoolkit import keyword
from gentoolkit.test import cmp

class TestGentoolkitKeyword(unittest.TestCase):

	def test_compare_strs(self):
		compare_strs = keyword.compare_strs

		# Test ordering of keyword strings
		version_tests = [
			# different archs
			('amd64', 'x86'),
			# stable vs. unstable
			('amd64-linux', '~amd64-linux'),
			# different OSes
			('~x86-linux', '~x86-solaris'),
			# OS vs. no OS
			('x86', '~amd64-linux')
		]
		# Check less than
		for vt in version_tests:
			self.failUnless(compare_strs(vt[0], vt[1]) == -1)
		# Check greater than
		for vt in version_tests:
			self.failUnless(compare_strs(vt[1], vt[0]) == 1)
		# Check equal
		vt = ('~amd64-linux', '~amd64-linux')
		self.failUnless(compare_strs(vt[0], vt[1]) == 0)

		kwds_presort = [
			'~amd64', '~amd64-linux', '~ppc', '~ppc-macos', '~x86',
			'~x86-linux', '~x86-macos', '~x86-solaris'
		]
		kwds_postsort = [
			'~amd64', '~ppc', '~x86', '~amd64-linux', '~x86-linux',
			'~ppc-macos', '~x86-macos', '~x86-solaris'
		]
		if sys.hexversion < 0x3000000:
			self.failUnlessEqual(sorted(kwds_presort, cmp=compare_strs), kwds_postsort)
		self.failUnlessEqual(sorted(kwds_presort, key = keyword.Keyword), kwds_postsort)


def test_main():
	suite = unittest.TestLoader().loadTestsFromTestCase(
		TestGentoolkitKeyword)
	unittest.TextTestRunner(verbosity=2).run(suite)
test_main.__test__ = False


if __name__ == '__main__':
	test_main()
