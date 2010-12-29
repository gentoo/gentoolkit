#!/usr/bin/env python

from __future__ import print_function


import re
import sys
import distutils
from distutils import core, log
from glob import glob

import os
import io

sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'pym'))

__version__ = os.getenv('VERSION', default='9999')

cwd = os.getcwd()

# Load EPREFIX from Portage, fall back to the empty string if it fails 
try: 
	from portage.const import EPREFIX 
except ImportError: 
	EPREFIX='/' 


# Bash files that need `VERSION=""` subbed, relative to this dir:
bash_scripts = [os.path.join(cwd, path) for path in (
	'bin/euse',
	'bin/revdep-rebuild'
)]

# Python files that need `__version__ = ""` subbed, relative to this dir:
python_scripts = [os.path.join(cwd, path) for path in (
	'bin/eclean',
	'bin/epkginfo',
	'bin/glsa-check',
	'pym/gentoolkit/eclean/cli.py',
	'pym/gentoolkit/analyse/__init__.py',
	'pym/gentoolkit/equery/__init__.py',
	'pym/gentoolkit/eshowkw/__init__.py'
)]


class set_version(core.Command):
	"""Set python __version__ and bash VERSION to our __version__."""
	description = "hardcode scripts' version using VERSION from environment"
	user_options = []  # [(long_name, short_name, desc),]

	def initialize_options (self):
		pass

	def finalize_options (self):
		pass

	def run(self):
		ver = 'svn' if __version__ == '9999' else __version__
		print("Settings version to %s" % ver)
		def sub(files, pattern):
			for f in files:
				updated_file = []
				with io.open(f, 'r', 1, 'utf_8') as s:
					for line in s:
						newline = re.sub(pattern, '"%s"' % ver, line, 1)
						if newline != line:
							log.info("%s: %s" % (f, newline))
						updated_file.append(newline)
				with io.open(f, 'w', 1, 'utf_8') as s:
					s.writelines(updated_file)
		quote = r'[\'"]{1}'
		bash_re = r'(?<=VERSION=)' + quote + '[^\'"]*' + quote
		sub(bash_scripts, bash_re)
		python_re = r'(?<=^__version__ = )' + quote + '[^\'"]*' + quote
		sub(python_scripts, python_re)


def	load_test():
	"""Only return the real test class if it's actually being run so that we
	don't depend on snakeoil just to install."""

	desc = "run the test suite"
	if 'test' in sys.argv[1:]:
		try:
			from snakeoil import distutils_extensions
		except ImportError:
			sys.stderr.write("Error: We depend on dev-python/snakeoil ")
			sys.stderr.write("to run tests.\n")
			sys.exit(1)
		class test(distutils_extensions.test):
			description = desc
			default_test_namespace = 'gentoolkit.test'
	else:
		class test(core.Command):
			description = desc

	return test

packages = [
	str('.'.join(root.split(os.sep)[1:]))
	for root, dirs, files in os.walk('pym/gentoolkit')
	if '__init__.py' in files
]

test_data = {
	'gentoolkit': [
		'test/eclean/Packages',
		'test/eclean/testdistfiles.tar.gz',
		'test/eclean/distfiles.exclude'
	]
}

core.setup(
	name='gentoolkit',
	version=__version__,
	description='Set of tools that work with and enhance portage.',
	author='',
	author_email='',
	maintainer='Gentoo Portage Tools Team',
	maintainer_email='tools-portage@gentoo.org',
	url='http://www.gentoo.org/proj/en/portage/tools/index.xml',
	download_url='http://distfiles.gentoo.org/distfiles/gentoolkit-%s.tar.gz'\
		% __version__,
	package_dir={'': 'pym'},
	packages=packages,
	package_data = test_data,
	scripts=(glob('bin/*')),
	data_files=(
		(os.path.join(EPREFIX, 'etc/env.d'), ['data/99gentoolkit-env']),
		(os.path.join(EPREFIX, 'etc/revdep-rebuild'), ['data/revdep-rebuild/99revdep-rebuild']),
		(os.path.join(EPREFIX, 'etc/eclean'), glob('data/eclean/*')),
		(os.path.join(EPREFIX, 'usr/share/man/man1'), glob('man/*')),
	),
	cmdclass={
		'test': load_test(),
		'set_version': set_version,
	},
)

# vim: set ts=4 sw=4 tw=79:
