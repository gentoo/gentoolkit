#!/usr/bin/python
# Copyright 2014 Gentoo Foundation
# Distributed under the terms of the GNU General Public License v2
# Written by Mike Frysinger <vapier@gentoo.org>

"""Unittests for ekeyword"""

import os
import subprocess
import tempfile
import unittest

from unittest import mock

from gentoolkit.ekeyword import ekeyword


TESTDIR = os.path.join(os.path.dirname(__file__), 'tests')


class TestSortKeywords(unittest.TestCase):
	"""Tests for sort_keywords"""

	def _test(self, input_data, exp_data):
		"""Sort |input_data| and make sure it matches |exp_data|"""
		output_data = ekeyword.sort_keywords(input_data.split())
		self.assertEqual(exp_data.split(), output_data)

	def testNull(self):
		"""Verify whitespace is collapsed"""
		self._test('', '')
		self._test('   		 ', '')

	def testGlob(self):
		"""Verify globs get sorted before all others"""
		self._test('* arm', '* arm')
		self._test('arm -* x86', '-* arm x86')
		self._test('hppa ~* amd64', '~* amd64 hppa')

	def testMixedPlatform(self):
		"""Verify core arches get sorted before all w/suffix"""
		self._test('arm-linux alpha amd64-fbsd hppa',
		           'alpha hppa amd64-fbsd arm-linux')

	def testPrefixes(self):
		"""Verify -/~ and such get ignored for sorting"""
		self._test('-hppa arm ~alpha -* ~arm-linux',
		           '-* ~alpha arm -hppa ~arm-linux')

	def testPlatform(self):
		"""Verify we sort based on platform first"""
		self._test('x86-linux ppc-macos x86-fbsd amd64-linux amd64-fbsd',
		           'amd64-fbsd x86-fbsd amd64-linux x86-linux ppc-macos')


class TestDiffKeywords(unittest.TestCase):
	"""Tests for diff_keywords"""

	def testEmpty(self):
		"""Test when there is no content to diff"""
		ret = ekeyword.diff_keywords([], [])
		self.assertEqual(ret, '')

	def testSame(self):
		"""Test when there is no difference"""
		ret = ekeyword.diff_keywords(['a b c'], ['a b c'])
		self.assertEqual(ret, 'a b c')

	def testInsert(self):
		"""Test when content is simply added"""
		ret = ekeyword.diff_keywords(['a'], ['~a'])
		self.assertNotEqual(ret, '')

	def testDelete(self):
		"""Test when content is simply deleted"""
		ret = ekeyword.diff_keywords(['~a'], ['a'])
		self.assertNotEqual(ret, '')

	def testReplace(self):
		"""Test when some content replaces another"""
		ret = ekeyword.diff_keywords(['~a'], ['-a'])
		self.assertNotEqual(ret, '')

	def _testSmokeStyle(self, style):
		return ekeyword.diff_keywords(
			['~a', 'b', '-abcde'],
			['a', '-b', '-abxde'], style=style)

	def testSmokeStyleColor(self):
		"""Run a full smoke test for color-inline style"""
		ret = self._testSmokeStyle('color-inline')
		self.assertNotEqual(ret, '')

	def testSmokeStyleNoColor(self):
		"""Run a full smoke test for non-color-inline style"""
		self._testSmokeStyle('nocolor')


class TestProcessKeywords(unittest.TestCase):
	"""Tests for process_keywords"""

	def _test(self, keywords, ops, exp, arch_status=None):
		# This func doesn't return sorted results (which is fine),
		# so do so ourselves to get stable tests.
		ret = ekeyword.process_keywords(
			keywords.split(), ops, arch_status=arch_status)
		self.assertEqual(sorted(ret), sorted(exp.split()))

	def testAdd(self):
		ops = (
			ekeyword.Op(None, 'arm', None),
			ekeyword.Op('~', 's390', None),
			ekeyword.Op('-', 'sh', None),
		)
		self._test('moo', ops, 'arm ~s390 -sh moo')

	def testModify(self):
		ops = (
			ekeyword.Op(None, 'arm', None),
			ekeyword.Op('~', 's390', None),
			ekeyword.Op('-', 'sh', None),
		)
		self._test('~arm s390 ~sh moo', ops, 'arm ~s390 -sh moo')

	def testDelete(self):
		ops = (
			ekeyword.Op('^', 'arm', None),
			ekeyword.Op('^', 's390', None),
			ekeyword.Op('^', 'x86', None),
		)
		self._test('arm -s390 ~x86 bar', ops, 'bar')

	def testSync(self):
		ops = (
			ekeyword.Op('=', 'arm64', 'arm'),
			ekeyword.Op('=', 'ppc64', 'ppc'),
			ekeyword.Op('=', 'amd64', 'x86'),
			ekeyword.Op('=', 'm68k', 'mips'),
			ekeyword.Op('=', 'ia64', 'alpha'),
			ekeyword.Op('=', 'sh', 'sparc'),
			ekeyword.Op('=', 's390', 's390x'),
			ekeyword.Op('=', 'boo', 'moo'),
		)
		self._test(
			'arm64 arm '
			'~ppc64 ~ppc '
			'~amd64 x86 '
			'm68k ~mips '
			'-ia64 alpha '
			'sh -sparc '
			's390 '
			'moo ',
			ops,
			'arm64 arm ~ppc64 ~ppc amd64 x86 ~m68k ~mips ia64 alpha '
			'-sh -sparc boo moo')

	def testAllNoStatus(self):
		ops = (
			ekeyword.Op(None, 'all', None),
		)
		self.assertRaises(ValueError, self._test, '', ops, '')

	def testAllStable(self):
		ops = (
			ekeyword.Op(None, 'all', None),
		)
		arch_status = {
			'alpha': ('stable', '~arch'),
			'arm':   ('stable', 'arch'),
			'm68k':  ('exp', '~arch'),
			's390':  ('exp', 'arch'),
		}
		self._test('* ~alpha ~arm ~m68k ~mips ~s390 ~arm-linux', ops,
		           '* ~alpha arm ~m68k ~mips s390 ~arm-linux', arch_status)

	def testAllUnstable(self):
		ops = (
			ekeyword.Op('~', 'all', None),
		)
		arch_status = {
			'alpha': ('stable', '~arch'),
			'arm':   ('stable', 'arch'),
			'm68k':  ('exp', '~arch'),
			's390':  ('exp', 'arch'),
		}
		self._test('-* ~* * alpha arm m68k s390 arm-linux', ops,
		           '-* ~* * ~alpha ~arm ~m68k ~s390 ~arm-linux', arch_status)

	def testAllMultiUnstableStable(self):
		ops = (
			ekeyword.Op('~', 'all', None),
			ekeyword.Op(None, 'all', None),
		)
		arch_status = {
			'alpha': ('stable', '~arch'),
			'arm':   ('stable', 'arch'),
			'm68k':  ('exp', '~arch'),
			's390':  ('exp', 'arch'),
		}
		self._test('-* ~* * alpha arm m68k s390', ops,
		           '-* ~* * ~alpha arm ~m68k s390', arch_status)

	def testAllDisabled(self):
		"""Make sure ~all does not change -arch to ~arch"""
		ops = (
			ekeyword.Op('~', 'all', None),
		)
		self._test('alpha -sparc ~x86', ops,
		           '~alpha -sparc ~x86', {})


class TestProcessContent(unittest.TestCase):
	"""Tests for process_content"""

	def _testKeywords(self, line):
		ops = (
			ekeyword.Op(None, 'arm', None),
			ekeyword.Op('~', 'sparc', None),
		)
		return ekeyword.process_content(
			'file', ['%s\n' % line], ops, quiet=True)

	def testKeywords(self):
		"""Basic KEYWORDS mod"""
		updated, ret = self._testKeywords('KEYWORDS=""')
		self.assertTrue(updated)
		self.assertEqual(ret, ['KEYWORDS="arm ~sparc"\n'])

	def testKeywordsIndented(self):
		"""Test KEYWORDS indented by space"""
		updated, ret = self._testKeywords(' 	 	KEYWORDS=""')
		self.assertTrue(updated)
		self.assertEqual(ret, [' 	 	KEYWORDS="arm ~sparc"\n'])

	def testKeywordsSingleQuote(self):
		"""Test single quoted KEYWORDS"""
		updated, ret = self._testKeywords("KEYWORDS=' '")
		self.assertTrue(updated)
		self.assertEqual(ret, ['KEYWORDS="arm ~sparc"\n'])

	def testKeywordsComment(self):
		"""Test commented out KEYWORDS"""
		updated, ret = self._testKeywords('# KEYWORDS=""')
		self.assertFalse(updated)
		self.assertEqual(ret, ['# KEYWORDS=""\n'])

	def testKeywordsCode(self):
		"""Test code leading KEYWORDS"""
		updated, ret = self._testKeywords('[[ ${PV} ]] && KEYWORDS=""')
		self.assertTrue(updated)
		self.assertEqual(ret, ['[[ ${PV} ]] && KEYWORDS="arm ~sparc"\n'])

	def testKeywordsEmpty(self):
		"""Test KEYWORDS not set at all"""
		updated, ret = self._testKeywords(' KEYWORDS=')
		self.assertFalse(updated)
		self.assertEqual(ret, [' KEYWORDS=\n'])

	def _testSmoke(self, style='color-inline', verbose=0, quiet=0):
		ops = (
			ekeyword.Op(None, 'arm', None),
			ekeyword.Op('~', 'sparc', None),
		)
		ekeyword.process_content(
			'asdf', ['KEYWORDS="arm"'], ops, verbose=verbose,
			quiet=quiet, style=style)

	def testSmokeQuiet(self):
		"""Smoke test for quiet mode"""
		self._testSmoke(quiet=10)

	def testSmokeVerbose(self):
		"""Smoke test for verbose mode"""
		self._testSmoke(verbose=10)

	def testSmokeStyleColor(self):
		"""Smoke test for color-inline style"""
		self._testSmoke('color-inline')

	def testSmokeStyleInline(self):
		"""Smoke test for inline style"""
		self._testSmoke('inline')

	def testSmokeStyleShortMulti(self):
		"""Smoke test for short-multi style"""
		self._testSmoke('short-multi')

	def testSmokeStyleLongMulti(self):
		"""Smoke test for long-multi style"""
		self._testSmoke('long-multi')


class TestProcessEbuild(unittest.TestCase):
	"""Tests for process_ebuild

	This is fairly light as most code is in process_content.
	"""

	def _process_ebuild(self, *args, **kwargs):
		"""Set up a writable copy of an ebuild for process_ebuild()"""
		with tempfile.NamedTemporaryFile() as tmp:
			with open(tmp.name, 'wb') as fw:
				with open(os.path.join(TESTDIR, 'process-1.ebuild'), 'rb') as f:
					orig_content = f.read()
					fw.write(orig_content)
			ekeyword.process_ebuild(tmp.name, *args, **kwargs)
			with open(tmp.name, 'rb') as f:
				return (orig_content, f.read())

	def _testSmoke(self, dry_run):
		ops = (
			ekeyword.Op(None, 'arm', None),
			ekeyword.Op('~', 'sparc', None),
		)
		orig_content, new_content = self._process_ebuild(ops, dry_run=dry_run)
		if dry_run:
			self.assertEqual(orig_content, new_content)
		else:
			self.assertNotEqual(orig_content, new_content)

	def testSmokeNotDry(self):
		self._testSmoke(False)

	def testSmokeDry(self):
		self._testSmoke(True)

	def testManifestUpdated(self):
		"""Verify `ebuild ... manifest` runs on updated files"""
		with mock.patch.object(subprocess, 'check_call') as m:
			self._process_ebuild((ekeyword.Op('~', 'arm', None),),
			                     manifest=True)
		m.assert_called_once_with(['ebuild', mock.ANY, 'manifest'])

	def testManifestNotUpdated(self):
		"""Verify we don't run `ebuild ... manifest` on unmodified files"""
		with mock.patch.object(subprocess, 'check_call') as m:
			self._process_ebuild((ekeyword.Op(None, 'arm', None),),
			                     manifest=True)
		self.assertEqual(m.call_count, 0)


class TestArgToOps(unittest.TestCase):
	"""Tests for arg_to_op()"""

	def _test(self, arg, op):
		self.assertEqual(ekeyword.arg_to_op(arg), ekeyword.Op(*op))

	def testStable(self):
		self._test('arm', (None, 'arm', None))

	def testUnstable(self):
		self._test('~ppc64', ('~', 'ppc64', None))

	def testDisabled(self):
		self._test('-sparc', ('-', 'sparc', None))

	def testDeleted(self):
		self._test('^x86-fbsd', ('^', 'x86-fbsd', None))

	def testSync(self):
		self._test('s390=x86', (None, 's390', 'x86'))


class TestMain(unittest.TestCase):
	"""Tests for the main entry point"""

	def testSmoke(self):
		ekeyword.main(['arm', '--dry-run', os.path.join(TESTDIR, 'process-1.ebuild')])

	def testVersion(self):
		with self.assertRaises(SystemExit) as e:
			ekeyword.main(['--version', '--dry-run'])
		self.assertEqual(e.exception.code, os.EX_OK)

	def testEmptyString(self):
		with self.assertRaises(SystemExit) as e:
			ekeyword.main(['', os.path.join(TESTDIR, 'process-1.ebuild')])
		self.assertNotEqual(e.exception.code, os.EX_OK)


if __name__ == '__main__':
	unittest.main()
