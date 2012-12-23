#!/usr/bin/env python

from __future__ import print_function


import re
import sys
import distutils
from distutils import core #, log
from glob import glob

import os
import io

sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'pym'))

__version__ = os.getenv('VERSION', default=os.getenv('PVR', default='9999'))

cwd = os.getcwd()

# Load EPREFIX from Portage, fall back to the empty string if it fails
try:
	from portage.const import EPREFIX
except ImportError:
	EPREFIX=''


# Bash files that need `VERSION=""` subbed, relative to this dir:
bash_scripts = [(os.path.join(cwd, path), 'VERSION=') for path in (
	'bin/euse',
	'bin/revdep-rebuild.sh'
)]

# Python files that need `__version__ = ""` subbed, relative to this dir:
python_scripts = [(os.path.join(cwd, path), '__version__ = ') for path in (
	'bin/eclean',
	'bin/epkginfo',
	'bin/glsa-check',
	'pym/gentoolkit/eclean/cli.py',
	'pym/gentoolkit/enalyze/__init__.py',
	'pym/gentoolkit/equery/__init__.py',
	'pym/gentoolkit/eshowkw/__init__.py',
	'pym/gentoolkit/revdep_rebuild/__init__.py'
)]

manpages = [(os.path.join(cwd, path[0]), path[1]) for path in (
	('man/eclean.1', 'ECLEAN'),
	('man/enalyze.1', 'ENALYZE'),
	('man/epkginfo.1', 'EPKGINFO'),
	('man/equery.1', 'EQUERY'),
	('man/eread.1', 'EREAD'),
	('man/eshowkw.1', 'ESHOWKW'),
	('man/euse.1', 'EUSE'),
	('man/glsa-check.1', 'GLSA-CHECK'),
	('man/revdep-rebuild.1', 'REVDEP-REBUILD'),
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
		ver = 'git' if __version__ == '9999' else __version__
		print("Setting version to %s" % ver)
		def sub(files, pattern):
			for f in files:
				updated_file = []
				with io.open(f[0], 'r', 1, 'utf_8') as s:
					for line in s:
						newline = re.sub(pattern %f[1], '"%s"' % ver, line, 1)
						if newline != line:
							#log.info("%s: %s" % (f, newline))
							print("%s: %s" % (f[0], newline.strip('\n')))
						updated_file.append(newline)
				with io.open(f[0], 'w', 1, 'utf_8') as s:
					s.writelines(updated_file)

		quote = r'[\'"]{1}'
		bash_re = r'(?<=%s)' + quote + '[^\'"]*' + quote
		sub(bash_scripts, bash_re)
		python_re = r'(?<=^%s)' + quote + '[^\'"]*' + quote
		sub(python_scripts, python_re)
		man_re = r'(?<=^.TH "%s" "[0-9]" )' + quote + '[^\'"]*' + quote
		sub(manpages, man_re)


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
		(os.path.join(os.sep, EPREFIX.lstrip(os.sep), 'etc/env.d'), ['data/99gentoolkit-env']),
		(os.path.join(os.sep, EPREFIX.lstrip(os.sep), 'etc/revdep-rebuild'), ['data/revdep-rebuild/99revdep-rebuild']),
		(os.path.join(os.sep, EPREFIX.lstrip(os.sep), 'etc/eclean'), glob('data/eclean/*')),
		(os.path.join(os.sep, EPREFIX.lstrip(os.sep), 'usr/share/man/man1'), glob('man/*')),
	),
	cmdclass={
		'test': load_test(),
		'set_version': set_version,
	},
)

# vim: set ts=4 sw=4 tw=79:
