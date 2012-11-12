import unittest
import warnings
from tempfile import NamedTemporaryFile, mktemp

from gentoolkit import query
from gentoolkit import errors


class TestQuery(unittest.TestCase):

	def setUp(self):
		pass

	def tearDown(self):
		pass

	def test_init(self):
		# valid queries must have at least one ascii letter or '*'
		invalid_queries = [
			'',
			'1',
			'/',
			'-1',
			'1/1',
		]
		for q in invalid_queries:
			self.failUnlessRaises(errors.GentoolkitInvalidPackage,
				query.Query, q
			)

		q1 = query.Query('gentoolkit')
		q1_tests = [
			(q1.query, 'gentoolkit'),
			(q1.is_regex, False),
			(q1.repo_filter, None),
			(q1.query_type, "simple")
		]
		for t in q1_tests:
			self.failUnlessEqual(t[0], t[1])

		q2 = query.Query('gentoolkit-.*', is_regex=True)
		q2_tests = [
			(q2.query, 'gentoolkit-.*'),
			(q2.is_regex, True),
			(q2.repo_filter, None),
			(q2.query_type, "complex")
		]
		for t in q2_tests:
			self.failUnlessEqual(t[0], t[1])

		q3 = query.Query('*::gentoo')
		q3_tests = [
			(q3.query, '*'),
			(q3.is_regex, False),
			(q3.repo_filter, 'gentoo'),
			(q3.query_type, "complex")
		]
		for t in q3_tests:
			self.failUnlessEqual(t[0], t[1])

		q4 = query.Query('gcc:4.3')
		q4_tests = [
			(q4.query, 'gcc:4.3'),
			(q4.is_regex, False),
			(q4.repo_filter, None),
			(q4.query_type, "simple")
		]
		for t in q4_tests:
			self.failUnlessEqual(t[0], t[1])

		q5 = query.Query('@system')
		q5_tests = [
			(q5.query, '@system'),
			(q5.is_regex, False),
			(q5.repo_filter, None),
			(q5.query_type, "set")
		]
		for t in q5_tests:
			self.failUnlessEqual(t[0], t[1])

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
				query.Query(gt[0]).uses_globbing() == gt[1]
			)


def test_main():
	suite = unittest.TestLoader().loadTestsFromTestCase(TestQuery)
	unittest.TextTestRunner(verbosity=2).run(suite)
test_main.__test__ = False


if __name__ == '__main__':
	test_main()
