#!/usr/bin/env python

from __future__ import with_statement

import os
import re
import sys
import distutils
from distutils import core, log
from glob import glob

__version__ = os.getenv('VERSION', default='9999')

cwd = os.getcwd()

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
	'pym/gentoolkit/equery/__init__.py'
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
		print "Setting version to %s" % ver
		def sub(files, pattern):
			for f in files:
				updated_file = []
				with open(f) as s:
					for line in s:
						newline = re.sub(pattern, '"%s"' % ver, line, 1)
						if newline != line:
							log.info("%s: %s" % (f, newline))
						updated_file.append(newline)
				with open(f, 'w') as s:
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
	'.'.join(root.split(os.sep)[1:])
	for root, dirs, files in os.walk('pym/gentoolkit')
	if '__init__.py' in files
]

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
	scripts=(glob('bin/*')),
	data_files=(
		('/etc/env.d', ['data/99gentoolkit-env']),
		('/etc/revdep-rebuild', ['data/revdep-rebuild/99revdep-rebuild']),
		('/etc/eclean', glob('data/eclean/*')),
		('/usr/share/man/man1', glob('man/*'))
	),
	cmdclass={
		'test': load_test(),
		'set_version': set_version,
	},
)

# vim: set ts=4 sw=4 tw=79:
