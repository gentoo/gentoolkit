#!/usr/bin/python
#
# Copyright 2010 Brian Dolbec <brian.dolbec@gmail.com>
# Copyright 2010 Gentoo Foundation
# Distributed under the terms of the GNU General Public License v2
#
# $Header$

from __future__ import with_statement
from __future__ import print_function

import os
import sys
import shutil
import random

import gentoolkit.pprinter as pp

__version__= "0.0.1"
__author__ = "Brian Dolbec"
__email__ = "brian.dolbec@gmail.com"


dir_mode = int('0774', 8)
file_mode = int('0644', 8)


def make_dir(path):
	"""create the directory at path

	@param path: full pathname to create
	capable of multiple intermediate directory creations.
	Will Error and exit if the target dir already exits"""
	try:
		os.makedirs(path, dir_mode)
	except EnvironmentError as er:
		print( pp.error("Error creating path:%s" %path), file=sys.stderr)
		print( pp.error("Error: %s" %str(er), file=sys.stderr))
		sys.exit(1)


def make_dist(path, files, clean_dict=None):
	"""Creates a small fake distfiles/binpkg directory @path populated
	with generated files of small random sizes using real names from
	the files list. udates the clean_dict with fullpathname.

	@param path: the path to create the distfiles directory
	@param files: list of file names to populate "path" with
	@param clean_dict: dict of {file-key:[path/file-key,],}
			that will be updated with full file-path-names
	"""
	make_dir(path)
	for file_ in files:
		size = random.randint(1000,5000)
		data = "0" * size
		filepath = os.path.join(path, file_)
		with open(filepath, 'w', file_mode) as new_file:
			new_file.write(data)
		if file_ not in clean_dict:
			# it is included in a multifile target
			continue
		elif clean_dict[file_] == []:
			clean_dict[file_] = filepath
		else:
			file_list = clean_dict[file_]
			for key in range(len(file_list)):
				file_list[key] = os.path.join(path, file_list[key])


def make_pkgs(path, files_dict, clean_dict):
	"""Create a small fake packages directory and call make_dist() to
	create and populate the category dir & package files

	@param path: the path to create the packages directory
	@param files_dict: dictionary of {cat: [pkg1, pkg2,...]}
	"""
	make_dir(path)
	for cat in files_dict.keys():
		make_dist(os.path.join(path,cat),
			files_dict[cat],
			clean_dict)
	# cp the Packages index file to path
	source = os.path.join(os.path.dirname(__file__), 'Packages')
	shutil.copy2(source, path)


def make_symlinks(path, links, targets):
	"""Create some symlinks at path

	@param path: the location to create the symlinks at
	@param links: list of links to create
	@param targets: list of targets to create links for,
			and need to be in the same index order as links
	"""
	for i in range(len(links)):
		os.symlink(os.path.join(path,target[i]),
			os.path.join(path, links[i]))


class TestDirCreation(object):
    """"""

    distfile_list = ['ExtUtils-ParseXS-2.22.tar.gz',
        'xorg-server-1.5.3.tar.bz2',
        'portage-utils-0.2.1.tar.bz2',
        'sysvinit_2.87dsf.orig.tar.gz',
        'sysvinit-2.86.tar.gz',
        'ExtUtils-ParseXS-2.20.tar.gz',
        'libisofs-0.6.22.tar.gz',
        'pixman-0.16.0.tar.bz2',
        'libburn-0.7.2.pl01.tar.gz',
        'libisofs-0.6.24.tar.gz',
        'xorg-server-1.5.3-gentoo-patches-08.tar.bz2',
        'ExtUtils-ParseXS-2.200401.tar.gz',
        'sysvinit-2.87-patches-2.tar.bz2',
        'sysvinit-2.86-kexec.patch',
        'Module-Build-0.3601.tar.gz',
        'libisofs-0.6.20.tar.gz',
        'xine-lib-1.1.17.tar.bz2',
        'pixman-0.14.0.tar.bz2',
        'Archive-Tar-1.52.tar.gz',
        'libburn-0.6.8.pl00.tar.gz',
        'libexif-0.6.17.tar.bz2',
        'portage-utils-0.3.tar.bz2',
        'xine-lib-1.1.15-textrel-fix.patch',
        'Module-Build-0.34.tar.gz',
        'Archive-Tar-1.54.tar.gz',
        'pixman-0.16.2.tar.bz2',
        'libburn-0.7.4.pl00.tar.gz ',
        'Module-Build-0.340201.tar.gz',
        'pixman-0.17.2.tar.bz2',
        'util-macros-1.3.0.tar.bz2',
        'Module-Build-0.35.tar.gz',
        'libburn-0.7.2.pl00.tar.gz',
        'util-macros-1.4.1.tar.bz2',
        'xine-lib-1.1.16.3.tar.bz2',
        'sysvinit-2.86-extra.patch',
        'libburn-0.7.0.pl00.tar.gz',
        'ExtUtils-ParseXS-2.21.tar.gz',
        'libexif-0.6.19.tar.bz2',
        'sysvinit-2.87-patches-1.tar.bz2',
        # now a base pkg with 2 additional symlink targets
        'symlink-test-1.2.3.tar.bz2',
        'target-1',
        'target-2'
        ]

    distfile_symlink = ['symlink-test-1.2.3-symlink1',
        'symlink-test-1.2.3-symlink2']

    dist_clean = {
        'Archive-Tar-1.52.tar.gz': [],
        'ExtUtils-ParseXS-2.20.tar.gz': [],
        'ExtUtils-ParseXS-2.200401.tar.gz': [],
        'ExtUtils-ParseXS-2.21.tar.gz': [],
        'Module-Build-0.34.tar.gz': [],
        'Module-Build-0.340201.tar.gz': [],
        'Module-Build-0.35.tar.gz': [],
        'libburn-0.6.8.pl00.tar.gz': [],
        'libburn-0.7.0.pl00.tar.gz': [],
        'libburn-0.7.2.pl00.tar.gz': [],
        'libburn-0.7.2.pl01.tar.gz': [],
        'libexif-0.6.17.tar.bz2': [],
        'libisofs-0.6.20.tar.gz': [],
        'libisofs-0.6.22.tar.gz': [],
        'pixman-0.14.0.tar.bz2': [],
        'pixman-0.16.0.tar.bz2': [],
        'pixman-0.16.2.tar.bz2': [],
        'portage-utils-0.2.1.tar.bz2': [],
        'sysvinit-2.86.tar.gz': ['sysvinit-2.86.tar.gz',
            'sysvinit-2.86-kexec.patch', 'sysvinit-2.86-extra.patch'],
        'util-macros-1.3.0.tar.bz2': [],
        'xine-lib-1.1.15-textrel-fix.patch': [],
        'xine-lib-1.1.16.3.tar.bz2': [],
        'xorg-server-1.5.3.tar.bz2': ['xorg-server-1.5.3.tar.bz2',
            'xorg-server-1.5.3-gentoo-patches-08.tar.bz2'],
        'symlink-test-1.2.3.tar.bz2': distfile_symlink
    }

    package_dict = {
        'app-arch': ['p7zip-4.65.tbz2', 'p7zip-4.57.tbz2',
            'file-roller-2.26.3.tbz2', 'tar-1.20.tbz2',
            'p7zip-4.58.tbz2', 'file-roller-2.28.2.tbz2',
            'file-roller-2.24.3.tbz2', 'gzip-1.4.tbz2', 'rar-3.9.0.tbz2',
            'bzip2-1.0.5-r1.tbz2', 'cpio-2.10.tbz2', 'tar-1.21-r1.tbz2',
            'cpio-2.10-r1.tbz2', 'file-roller-2.28.1.tbz2', 'cpio-2.9-r2.tbz2',
            'tar-1.22.tbz2', 'cpio-2.9-r3.tbz2'],
        'app-editors': ['nano-2.2.0.tbz2', 'nano-2.1.10.tbz2',
            'nano-2.0.9.tbz2', 'nano-2.2.2.tbz2'],
        'app-portage': ['layman-1.3.0_rc1-r3.tbz2', 'layman-1.2.6.tbz2',
            'portage-utils-0.3.1.tbz2', 'layman-1.3.0.tbz2',
            'layman-1.2.4-r3.tbz2', 'layman-1.2.3.tbz2',
            'layman-1.3.0_rc1.tbz2'],
        'sys-apps': ['shadow-4.0.18.2.tbz2', 'shadow-4.1.2.2.tbz2',
            'openrc-0.6.0-r1.tbz2', 'shadow-4.1.4.2-r1.tbz2',
            'shadow-4.1.4.2-r2.tbz2']
        }

    pkg_clean = {
        'app-arch/p7zip-4.57.tbz2': [],
        'app-arch/file-roller-2.26.3.tbz2': [],
        'app-arch/tar-1.20.tbz2': [],
        'app-arch/p7zip-4.58.tbz2': [],
        'app-arch/file-roller-2.28.2.tbz2': [],
        'app-arch/file-roller-2.24.3.tbz2': [],
        'app-arch/bzip2-1.0.5-r1.tbz2': [],
        'app-arch/cpio-2.10.tbz2': [],
        'app-arch/tar-1.21-r1.tbz2': [],
        'app-arch/cpio-2.9-r2.tbz2': [],
        'app-arch/cpio-2.9-r3.tbz2': [],
        'app-editors/nano-2.2.0.tbz2': [],
        'app-editors/nano-2.1.10.tbz2': [],
        'app-editors/nano-2.0.9.tbz2': [],
        'app-portage/layman-1.3.0_rc1-r3.tbz2': [],
        'app-portage/layman-1.2.6.tbz2': [],
        'app-portage/layman-1.2.4-r3.tbz2': [],
        'app-portage/layman-1.2.3.tbz2': [],
        'app-portage/layman-1.3.0_rc1.tbz2': [],
        'sys-apps/shadow-4.0.18.2.tbz2': [],
        'sys-apps/shadow-4.1.2.2.tbz2': [],
        'sys-apps/shadow-4.1.4.2-r1.tbz2': [],
        }

    def __init__(self, options):
        """Initialization

        @param options: dict.
        """
        self.options = options
        self.targets_init = False
        # create distfiles dir and populate it
        make_dist(self.options['target_path'], self.distfile_list, self.dist_clean)
        # add some symlinks to it
        path = os.path.join(self.options['target_path'], 'distfiles')
        make_symlinks(path, distfile_symlink,
            dist_clean['symlink-test-1.2.3.tar.bz2'])
        # create the packages dir and populate it
        path = os.path.join(self.options['target_path'], 'packages')
        make_pkgs(path, self.package_dict, self.pkg_clean)
        self.targets_init = True

    #def get_
