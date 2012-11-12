import unittest
import py_compile

import os
osp = os.path

"""Does a basic syntax check by compiling all modules. From Portage."""

pym_dirs = os.walk(osp.dirname(osp.dirname(osp.dirname(__file__))))
blacklist_dirs = frozenset(('.svn', 'test'))

class TestForSyntaxErrors(unittest.TestCase):

	def test_compileability(self):
		compileables = []
		for thisdir, subdirs, files in pym_dirs:
			if os.path.basename(thisdir) in blacklist_dirs:
				continue
			compileables.extend([
				osp.join(thisdir, f)
				for f in files
				if osp.splitext(f)[1] == '.py'
			])

		for c in compileables:
			py_compile.compile(c, doraise=True)


def test_main():
	suite = unittest.TestLoader().loadTestsFromTestCase(
		TestForSyntaxErrors)
	unittest.TextTestRunner(verbosity=2).run(suite)
test_main.__test__ = False


if __name__ == '__main__':
	test_main()
