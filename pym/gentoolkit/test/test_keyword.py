import unittest
import warnings
from tempfile import NamedTemporaryFile
try:
	from test import test_support
except ImportError:
	from test import support as test_support

from portage import os

from gentoolkit import keyword

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
			('~x86-linux', '~x86-solaris')
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


def test_main():
	test_support.run_unittest(TestGentoolkitHelpers2)


if __name__ == '__main__':
	test_main()
