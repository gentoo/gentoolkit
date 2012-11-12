import unittest

from gentoolkit import equery

class TestEqueryInit(unittest.TestCase):

	def setUp(self):
		pass

	def tearDown(self):
		pass

	def test_expand_module_name(self):
		# Test that module names are properly expanded
		name_map = {
			'a': 'has',
			'b': 'belongs',
			'c': 'changes',
			'k': 'check',
			'd': 'depends',
			'g': 'depgraph',
			'f': 'files',
			'h': 'hasuse',
			'y': 'keywords',
			'l': 'list_',
			'm': 'meta',
			's': 'size',
			'u': 'uses',
			'w': 'which'
		}
		self.failUnlessEqual(equery.NAME_MAP, name_map)
		for short_name, long_name in zip(name_map, name_map.values()):
			self.failUnlessEqual(equery.expand_module_name(short_name),
				long_name)
			self.failUnlessEqual(equery.expand_module_name(long_name),
				long_name)
		unused_keys = set(map(chr, range(0, 256))).difference(name_map.keys())
		for key in unused_keys:
			self.failUnlessRaises(KeyError, equery.expand_module_name, key)


def test_main():
	suite = unittest.TestLoader().loadTestsFromTestCase(TestEqueryInit)
	unittest.TextTestRunner(verbosity=2).run(suite)
test_main.__test__ = False


if __name__ == '__main__':
	test_main()
