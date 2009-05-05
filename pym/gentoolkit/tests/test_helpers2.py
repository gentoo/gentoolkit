import unittest
from test import test_support

from gentoolkit import helpers2

class TestGentoolkitHelpers2(unittest.TestCase):

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
				helpers2.compare_package_strings(vt[0], vt[1]) == -1
			)
		# Check greater than
		for vt in version_tests:
			self.failUnless(
				helpers2.compare_package_strings(vt[1], vt[0]) == 1
			)
		# Check equal
		vt = ('sys-auth/pambase-20080318', 'sys-auth/pambase-20080318')
		self.failUnless(
			helpers2.compare_package_strings(vt[0], vt[1]) == 0
		)

def test_main():
	test_support.run_unittest(TestGentoolkitHelpers2)

if __name__ == '__main__':
	test_main()
