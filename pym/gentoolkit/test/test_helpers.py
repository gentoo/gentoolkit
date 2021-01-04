import os
import unittest
import warnings
from tempfile import NamedTemporaryFile, mktemp

from gentoolkit import helpers


class TestFileOwner(unittest.TestCase):

	def setUp(self):
		pass

	def tearDown(self):
		pass

	def test_expand_abspaths(self):
		expand_abspaths = helpers.FileOwner.expand_abspaths

		initial_file_list = ['foo0', '/foo1', '~/foo2', './foo3']
		# This function should only effect foo3, and not ordering:

		final_file_list = [
			'foo0',
			'/foo1',
			'~/foo2',
			os.path.join(os.getcwd(), os.path.normpath(initial_file_list[3]))
		]

		self.assertEqual(expand_abspaths(initial_file_list), final_file_list)

	def test_extend_realpaths(self):
		extend_realpaths = helpers.FileOwner.extend_realpaths

		# Test that symlinks's realpaths are extended
		f1 = NamedTemporaryFile(prefix='equeryunittest')
		f2 = NamedTemporaryFile(prefix='equeryunittest')
		f3 = NamedTemporaryFile(prefix='equeryunittest')
		with warnings.catch_warnings():
			warnings.simplefilter("ignore")
			sym1 = mktemp()
			os.symlink(f1.name, sym1)
			sym2 = mktemp()
			os.symlink(f3.name, sym2)
		# We've created 3 files and 2 symlinks for testing. We're going to pass
		# in only the first two files and both symlinks. sym1 points to f1.
		# Since f1 is already in the list, sym1's realpath should not be added.
		# sym2 points to f3, but f3's not in our list, so sym2's realpath
		# should be added to the list.
		p = [f1.name, f2.name, sym1, sym2]
		p_xr = extend_realpaths(p)

		self.assertEqual(p_xr[0], f1.name)
		self.assertEqual(p_xr[1], f2.name)
		self.assertEqual(p_xr[2], sym1)
		self.assertEqual(p_xr[3], sym2)
		self.assertEqual(p_xr[4], f3.name)

		# Clean up
		os.unlink(sym1)
		os.unlink(sym2)

		# Make sure we raise an exception if we don't get acceptable input
		self.assertRaises(AttributeError, extend_realpaths, 'str')
		self.assertRaises(AttributeError, extend_realpaths, set())


def test_main():
	suite = unittest.TestLoader()
	suite.loadTestsFromTestCase(TestFileOwner)
	unittest.TextTestRunner(verbosity=2).run(suite)
test_main.__test__ = False


if __name__ == '__main__':
	test_main()
