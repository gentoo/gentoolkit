#!/usr/bin/env python

from distutils.core import setup

__version__ = open("VERSION").read().strip()

setup(
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
	packages=(
		'gentoolkit',
		'gentoolkit.equery',
		'gentoolkit.glsa'
	),
	scripts=(
		'bin/eclean',
		'bin/epkginfo',
		'bin/equery',
		'bin/eread',
		'bin/euse',
		'bin/glsa-check',
		'bin/revdep-rebuild'
	),
	data_files=(
		('/etc/env.d', ['data/99gentoolkit-env']),
		('/etc/revdep-rebuild', ['data/revdep-rebuild/99revdep-rebuild']),
		('/etc/eclean', [
			'data/eclean/distfiles.exclude',
			'data/eclean/packages.exclude'
		]),
		('/usr/share/man/man1', [
			'man/eclean.1',
			'man/epkginfo.1',
			'man/equery.1',
			'man/eread.1',
			'man/euse.1',
			'man/glsa-check.1',
			'man/revdep-rebuild.1'
		 ])
	)
)
