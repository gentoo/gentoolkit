# Copyright(c) 2009, Gentoo Foundation
# Copyright 2010 Brian Dolbec <brian.dolbec@gmail.com>
#
# License: GPL2/BSD

# $Header$


from __future__ import print_function

import re
import os
import unittest
from tempfile import NamedTemporaryFile, mkdtemp
import subprocess
import portage


dir_mode = 0o774

CPVS = [
	'sys-auth/consolekit-0.4.1',
	'sys-apps/devicekit-power-014',
	'media-libs/sdl-pango-0.1.2',
	'sys-apps/help2man-1.37.1',
	'app-emulation/emul-linux-x86-baselibs-20100220'
	]

PROPS = {
	'sys-apps/devicekit-power-014': {
		'SRC_URI':'http://hal.freedesktop.org/releases/DeviceKit-power-014.tar.gz',
		"RESTRICT": ''},
	'sys-apps/help2man-1.37.1': {
		"SRC_URI": 'mirror://gnu/help2man/help2man-1.37.1.tar.gz',
		"RESTRICT": ''},
	'sys-auth/consolekit-0.4.1': {
		"SRC_URI": 'http://www.freedesktop.org/software/ConsoleKit/dist/ConsoleKit-0.4.1.tar.bz2',
		"RESTRICT": ''},
	'app-emulation/emul-linux-x86-baselibs-20100220': {
		"SRC_URI": 'mirror://gentoo/emul-linux-x86-baselibs-20100220.tar.gz',
		"RESTRICT": 'strip'},
	'media-libs/sdl-pango-0.1.2': {
		"SRC_URI": 'mirror://sourceforge/sdlpango/SDL_Pango-0.1.2.tar.gz http://zarb.org/~gc/t/SDL_Pango-0.1.2-API-adds.patch',
		"RESTRICT": ''},
	'x11-base/xorg-server-1.6.5-r1': {
		"SRC_URI": 'http://xorg.freedesktop.org/releases/individual/xserver/xorg-server-1.6.5.tar.bz2 mirror://gentoo/xorg-server-1.6.5-gentoo-patches-01.tar.bz2',
		"RESTRICT": ''},
	'perl-core/ExtUtils-ParseXS-2.20.0401': {
		"SRC_URI": 'mirror://cpan/authors/id/D/DA/DAGOLDEN//ExtUtils-ParseXS-2.200401.tar.gz',
		"RESTRICT": ''},
	'x11-misc/util-macros-1.3.0': {
		"SRC_URI": 'http://xorg.freedesktop.org/releases/individual/util/util-macros-1.3.0.tar.bz2',
		"RESTRICT": ''},
	'x11-base/xorg-server-1.7.5': {
		"SRC_URI": 'http://xorg.freedesktop.org/releases/individual/xserver/xorg-server-1.7.5.tar.bz2',
		"RESTRICT": ''},
	'app-portage/portage-utils-0.3.1': {
		"SRC_URI": 'mirror://gentoo/portage-utils-0.3.1.tar.bz2',
		"RESTRICT": ''},
	'x11-misc/util-macros-1.5.0': {
		"SRC_URI": 'http://xorg.freedesktop.org/releases/individual/util/util-macros-1.5.0.tar.bz2',
		"RESTRICT": ''},
	'perl-core/Module-Build-0.35': {
		"SRC_URI": 'mirror://cpan/authors/id/D/DA/DAGOLDEN//Module-Build-0.35.tar.gz',
		"RESTRICT": ''},
	'perl-core/ExtUtils-ParseXS-2.22.02': {
		"SRC_URI": 'mirror://cpan/authors/id/D/DA/DAGOLDEN//ExtUtils-ParseXS-2.2202.tar.gz',
		"RESTRICT": ''},
	'perl-core/ExtUtils-ParseXS-2.22.03': {
		"SRC_URI": 'mirror://cpan/authors/id/D/DA/DAGOLDEN//ExtUtils-ParseXS-2.2203.tar.gz',
		"RESTRICT": ''},
	'perl-core/ExtUtils-ParseXS-2.22.01': {
		"SRC_URI": 'mirror://cpan/authors/id/D/DA/DAGOLDEN//ExtUtils-ParseXS-2.2201.tar.gz',
		"RESTRICT": ''},
	'perl-core/Archive-Tar-1.38': {
		"SRC_URI": 'mirror://cpan/authors/id/K/KA/KANE/Archive-Tar-1.38.tar.gz',
		"RESTRICT": ''},
	'perl-core/Archive-Tar-1.58': {
		"SRC_URI": 'mirror://cpan/authors/id/B/BI/BINGOS//Archive-Tar-1.58.tar.gz',
		"RESTRICT": ''},
	'perl-core/Archive-Tar-1.54': {
		"SRC_URI": 'mirror://cpan/authors/id/B/BI/BINGOS//Archive-Tar-1.54.tar.gz',
		"RESTRICT": ''},
	'perl-core/Archive-Tar-1.56': {
		"SRC_URI": 'mirror://cpan/authors/id/B/BI/BINGOS//Archive-Tar-1.56.tar.gz',
		"RESTRICT": ''},
	'app-portage/portage-utils-0.2.1': {
		"SRC_URI": 'mirror://gentoo/portage-utils-0.2.1.tar.bz2',
		"RESTRICT": ''},
	'dev-libs/libisofs-0.6.20-r1': {
		"SRC_URI": 'http://files.libburnia-project.org/releases/libisofs-0.6.20.tar.gz',
		"RESTRICT": ''},
	'perl-core/ExtUtils-ParseXS-2.22.02-r1': {
		"SRC_URI": 'mirror://cpan/authors/id/D/DA/DAGOLDEN//ExtUtils-ParseXS-2.2202.tar.gz',
		"RESTRICT": ''},
	'x11-misc/util-macros-1.6.0': {
		"SRC_URI": 'http://xorg.freedesktop.org/releases/individual/util/util-macros-1.6.0.tar.bz2',
		"RESTRICT": ''},
	'x11-libs/pixman-0.16.0': {
		"SRC_URI": 'http://xorg.freedesktop.org/releases/individual/lib/pixman-0.16.0.tar.bz2',
		"RESTRICT": ''},
	'x11-libs/pixman-0.16.4': {
		"SRC_URI": 'http://xorg.freedesktop.org/releases/individual/lib/pixman-0.16.4.tar.bz2',
		"RESTRICT": ''},
	'x11-libs/pixman-0.17.4': {
		"SRC_URI": 'http://xorg.freedesktop.org/releases/individual/lib/pixman-0.17.4.tar.bz2',
		"RESTRICT": ''},
	'x11-libs/pixman-0.17.2': {
		"SRC_URI": 'http://xorg.freedesktop.org/releases/individual/lib/pixman-0.17.2.tar.bz2',
		"RESTRICT": ''},
	'dev-libs/libburn-0.7.6-r1': {
		"SRC_URI": 'http://files.libburnia-project.org/releases/libburn-0.7.6.pl00.tar.gz',
		"RESTRICT": ''},
	'dev-libs/libburn-0.7.0': {
		"SRC_URI": 'http://files.libburnia-project.org/releases/libburn-0.7.0.pl00.tar.gz',
		"RESTRICT": ''},
	'perl-core/Module-Build-0.34.0201': {
		"SRC_URI": 'mirror://cpan/authors/id/D/DA/DAGOLDEN//Module-Build-0.340201.tar.gz',
		"RESTRICT": ''},
	'dev-libs/libburn-0.6.8': {
		"SRC_URI": 'http://files.libburnia-project.org/releases/libburn-0.6.8.pl00.tar.gz',
		"RESTRICT": ''},
	'dev-libs/libburn-0.7.4': {
		"SRC_URI": 'http://files.libburnia-project.org/releases/libburn-0.7.4.pl00.tar.gz',
		"RESTRICT": ''},
	'perl-core/Module-Build-0.36.03': {
		"SRC_URI": 'mirror://cpan/authors/id/D/DA/DAGOLDEN//Module-Build-0.3603.tar.gz',
		"RESTRICT": ''},
	'perl-core/Module-Build-0.36.01': {
		"SRC_URI": 'mirror://cpan/authors/id/D/DA/DAGOLDEN//Module-Build-0.3601.tar.gz',
		"RESTRICT": ''},
	'x11-base/xorg-server-1.5.3-r6': {
		"SRC_URI": 'http://xorg.freedesktop.org/releases/individual/xserver/xorg-server-1.5.3.tar.bz2 mirror://gentoo/xorg-server-1.5.3-gentoo-patches-08.tar.bz2',
		"RESTRICT": ''},
	'dev-libs/libisofs-0.6.28': {
		"SRC_URI": 'http://files.libburnia-project.org/releases/libisofs-0.6.28.tar.gz',
		"RESTRICT": ''},
	'media-libs/xine-lib-1.1.17': {
		"SRC_URI": 'mirror://sourceforge/xine/xine-lib-1.1.17.tar.bz2 mirror://gentoo/xine-lib-1.1.15-textrel-fix.patch',
		"RESTRICT": ''},
	'media-libs/xine-lib-1.1.18': {
		"SRC_URI": 'mirror://sourceforge/xine/xine-lib-1.1.18.tar.xz mirror://gentoo/xine-lib-1.1.15-textrel-fix.patch mirror://gentoo/xine-lib-1.1.18-compat.c.tbz2',
		"RESTRICT": ''},
	'perl-core/ExtUtils-ParseXS-2.22': {
		"SRC_URI": 'mirror://cpan/authors/id/D/DA/DAGOLDEN//ExtUtils-ParseXS-2.22.tar.gz',
		"RESTRICT": ''},
	'perl-core/ExtUtils-ParseXS-2.21': {
		"SRC_URI": 'mirror://cpan/authors/id/D/DA/DAGOLDEN//ExtUtils-ParseXS-2.21.tar.gz',
		"RESTRICT": ''},
	'x11-base/xorg-server-1.7.5.901': {
		"SRC_URI": 'http://xorg.freedesktop.org/releases/individual/xserver/xorg-server-1.7.5.901.tar.bz2',
		"RESTRICT": ''},
	'dev-libs/libisofs-0.6.24': {
		"SRC_URI": 'http://files.libburnia-project.org/releases/libisofs-0.6.24.tar.gz',
		"RESTRICT": ''},
	'dev-libs/libisofs-0.6.26': {
		"SRC_URI": 'http://files.libburnia-project.org/releases/libisofs-0.6.26.tar.gz',
		"RESTRICT": ''},
	'app-portage/portage-utils-0.3.1': {
		"SRC_URI": 'mirror://gentoo/portage-utils-0.3.1.tar.bz2',
		"RESTRICT": ''},
	'app-portage/gentoolkit-0.3.0_rc8-r1': {
		"SRC_URI": 'mirror://gentoo/gentoolkit-0.3.0_rc8.tar.gz http://dev.gentoo.org/~fuzzyray/distfiles/gentoolkit-0.3.0_rc8.tar.gz',
		"RESTRICT": ''},
	'app-portage/gentoolkit-0.2.4.6-r1': {
		"SRC_URI": 'mirror://gentoo/gentoolkit-0.2.4.6.tar.gz http://dev.gentoo.org/~fuzzyray/distfiles/gentoolkit-0.2.4.6.tar.gz',
		"RESTRICT": ''},
	'app-portage/eix-0.20.2': {
		"SRC_URI": 'mirror://berlios/eix/eix-0.20.2.tar.xz',
		"RESTRICT": ''},
	'app-portage/gentoolkit-0.2.4.5': {
		"SRC_URI": 'mirror://gentoo/gentoolkit-0.2.4.5.tar.gz http://dev.gentoo.org/~fuzzyray/distfiles/gentoolkit-0.2.4.5.tar.gz',
		"RESTRICT": ''},
	'app-portage/portage-utils-0.2.1': {
		"SRC_URI": 'mirror://gentoo/portage-utils-0.2.1.tar.bz2',
		"RESTRICT": ''},
	'app-portage/gentoolkit-0.3.0_rc8': {
		"SRC_URI": 'mirror://gentoo/gentoolkit-0.3.0_rc8.tar.gz http://dev.gentoo.org/~fuzzyray/distfiles/gentoolkit-0.3.0_rc8.tar.gz',
		"RESTRICT": ''},
	'app-portage/gentoolkit-0.2.4.6': {
		"SRC_URI": 'mirror://gentoo/gentoolkit-0.2.4.6.tar.gz http://dev.gentoo.org/~fuzzyray/distfiles/gentoolkit-0.2.4.6.tar.gz',
		"RESTRICT": ''},
	'app-portage/layman-1.3.0-r1': {
		"SRC_URI": 'mirror://sourceforge/layman/layman-1.3.0.tar.gz',
		"RESTRICT": ''},
	'app-portage/gentoolkit-0.3.0_rc7': {
		"SRC_URI": 'mirror://gentoo/gentoolkit-0.3.0_rc7.tar.gz http://dev.gentoo.org/~fuzzyray/distfiles/gentoolkit-0.3.0_rc7.tar.gz',
		"RESTRICT": ''},
	'app-portage/layman-1.3.0': {
		"SRC_URI": 'mirror://sourceforge/layman/layman-1.3.0.tar.gz',
		"RESTRICT": ''},
	'app-portage/layman-1.3.1': {
		"SRC_URI": 'mirror://sourceforge/layman/layman-1.3.1.tar.gz',
		"RESTRICT": ''},
	'app-portage/layman-1.2.6': {
		"SRC_URI": 'mirror://sourceforge/layman/layman-1.2.6.tar.gz',
		"RESTRICT": ''},
	'app-portage/layman-9999': {
		"SRC_URI": '',
		"RESTRICT": ''},
	'app-portage/layman-1.2.5': {
		"SRC_URI": 'mirror://sourceforge/layman/layman-1.2.5.tar.gz',
		"RESTRICT": ''},
	'app-portage/layman-1.3.0_rc1-r3': {
		"SRC_URI": 'mirror://sourceforge/layman/layman-1.3.0_rc1.tar.gz',
		"RESTRICT": ''},
	'app-portage/gentoolkit-0.3.0_rc9': {
		"SRC_URI": 'mirror://gentoo/gentoolkit-0.3.0_rc9.tar.gz http://dev.gentoo.org/~fuzzyray/distfiles/gentoolkit-0.3.0_rc9.tar.gz',
		"RESTRICT": ''},
	'app-portage/eix-0.20.1': {
		"SRC_URI": 'mirror://sourceforge/eix/eix-0.20.1.tar.xz',
		"RESTRICT": ''},
	'app-portage/eix-0.19.2': {
		"SRC_URI": 'mirror://sourceforge/eix/eix-0.19.2.tar.xz',
		"RESTRICT": ''},
	'app-portage/layman-1.3.2-r1': {
		"SRC_URI": 'mirror://sourceforge/layman/layman-1.3.2.tar.gz',
		"RESTRICT": ''},
}

PKGS = {
	'app-portage/layman-1.3.2-r1': 'mirror://sourceforge/layman/layman-1.3.2.tar.gz',
	'app-portage/eix-0.20.1': 'mirror://sourceforge/eix/eix-0.20.1.tar.xz',
	'app-portage/eix-0.19.2': 'mirror://sourceforge/eix/eix-0.19.2.tar.xz',
	'app-portage/gentoolkit-0.3.0_rc9': 'mirror://gentoo/gentoolkit-0.3.0_rc9.tar.gz http://dev.gentoo.org/~fuzzyray/distfiles/gentoolkit-0.3.0_rc9.tar.gz',
	'app-portage/gentoolkit-0.2.4.6': 'mirror://gentoo/gentoolkit-0.2.4.6.tar.gz http://dev.gentoo.org/~fuzzyray/distfiles/gentoolkit-0.2.4.6.tar.gz',
	'media-libs/xine-lib-1.1.18': 'mirror://sourceforge/xine/xine-lib-1.1.18.tar.xz mirror://gentoo/xine-lib-1.1.15-textrel-fix.patch mirror://gentoo/xine-lib-1.1.18-compat.c.tbz2',
	'perl-core/ExtUtils-ParseXS-2.21': 'mirror://cpan/authors/id/D/DA/DAGOLDEN//ExtUtils-ParseXS-2.21.tar.gz',
	'dev-libs/libisofs-0.6.24': 'http://files.libburnia-project.org/releases/libisofs-0.6.24.tar.gz',
	}

CLEAN_ME = {
	'layman-1.3.2.tar.gz': '/path/to/some/where/layman-1.3.2.tar.gz',
	'layman-1.2.5.tar.gz': '/path/to/some/where/layman-1.2.5.tar.gz',
	'eix-0.20.1.tar.xz': '/path/to/some/where/eix-0.20.1.tar.xz',
	'gentoolkit-0.3.0_rc9.tar.gz': '/path/to/some/where/gentoolkit-0.3.0_rc9.tar.gz',
	'xine-lib-1.1.18.tar.xz': '/path/to/some/where/xine-lib-1.1.18.tar.xz',
	'xine-lib-1.1.15-textrel-fix.patch': '/path/to/some/where/xine-lib-1.1.15-textrel-fix.patch',
	'xine-lib-1.1.18-compat.c.tbz2': '/path/to/some/where/xine-lib-1.1.18-compat.c.tbz2',
	'ExtUtils-ParseXS-2.21.tar.gz': '/path/to/some/where/ExtUtils-ParseXS-2.21.tar.gz',
	'libisofs-0.6.24.tar.gz': '/path/to/some/where/libisofs-0.6.24.tar.gz'
	}

CPVS2 = [
	'app-emulation/emul-linux-x86-baselibs-20100220',
	'app-portage/eix-0.19.2', 'app-portage/eix-0.20.1',
	'app-portage/eix-0.20.2',
	'app-portage/gentoolkit-0.2.4.5',
	'app-portage/gentoolkit-0.2.4.6',
	'app-portage/gentoolkit-0.2.4.6-r1',
	'app-portage/gentoolkit-0.3.0_rc7',
	'app-portage/gentoolkit-0.3.0_rc8',
	'app-portage/gentoolkit-0.3.0_rc8-r1',
	'app-portage/gentoolkit-0.3.0_rc9',
	'app-portage/layman-1.2.5',
	'app-portage/layman-1.2.6',
	'app-portage/layman-1.3.0',
	'app-portage/layman-1.3.0-r1',
	'app-portage/layman-1.3.0_rc1-r3',
	'app-portage/layman-1.3.1',
	'app-portage/layman-1.3.2-r1',
	'app-portage/layman-9999',
	'app-portage/portage-utils-0.2.1',
	'app-portage/portage-utils-0.3.1',
	'dev-libs/libburn-0.6.8',
	'dev-libs/libburn-0.7.0',
	'dev-libs/libburn-0.7.4',
	'dev-libs/libburn-0.7.6-r1',
	'dev-libs/libisofs-0.6.20-r1',
	'dev-libs/libisofs-0.6.24',
	'dev-libs/libisofs-0.6.26',
	'dev-libs/libisofs-0.6.28',
	'media-libs/sdl-pango-0.1.2',
	'media-libs/xine-lib-1.1.17',
	'media-libs/xine-lib-1.1.18',
	'perl-core/Archive-Tar-1.38',
	'perl-core/Archive-Tar-1.54',
	'perl-core/Archive-Tar-1.56',
	'perl-core/Archive-Tar-1.58',
	'perl-core/ExtUtils-ParseXS-2.20.0401',
	'perl-core/ExtUtils-ParseXS-2.21',
	'perl-core/ExtUtils-ParseXS-2.22',
	'perl-core/ExtUtils-ParseXS-2.22.01',
	'perl-core/ExtUtils-ParseXS-2.22.02',
	'perl-core/ExtUtils-ParseXS-2.22.02-r1',
	'perl-core/ExtUtils-ParseXS-2.22.03',
	'perl-core/Module-Build-0.34.0201',
	'perl-core/Module-Build-0.35',
	'perl-core/Module-Build-0.36.01',
	'perl-core/Module-Build-0.36.03',
	'sys-apps/devicekit-power-014',
	'sys-apps/help2man-1.37.1',
	'sys-auth/consolekit-0.4.1',
	'x11-base/xorg-server-1.5.3-r6',
	'x11-base/xorg-server-1.6.5-r1',
	'x11-base/xorg-server-1.7.5',
	'x11-base/xorg-server-1.7.5.901',
	'x11-libs/pixman-0.16.0',
	'x11-libs/pixman-0.16.4',
	'x11-libs/pixman-0.17.2',
	'x11-libs/pixman-0.17.4',
	'x11-misc/util-macros-1.3.0',
	'x11-misc/util-macros-1.5.0',
	'x11-misc/util-macros-1.6.0'
	]

FILES = [
	'DeviceKit-power-014.tar.gz',
	'help2man-1.37.1.tar.gz',
	'ConsoleKit-0.4.1.tar.bz2',
	'emul-linux-x86-baselibs-20100220.tar.gz',
	'SDL_Pango-0.1.2.tar.gz',
	'SDL_Pango-0.1.2-API-adds.patch'
	]


CPVS3 = [
	'x11-base/xorg-server-1.7.5',
	'x11-misc/util-macros-1.6.0',
	'x11-libs/pixman-0.16.4',
	#'dev-libs/libisofs-0.6.28',
	#'perl-core/Module-Build-0.36.03',
	#'perl-core/ExtUtils-ParseXS-2.22.02-r1',
	#'perl-core/Archive-Tar-1.56',
	#'app-portage/gentoolkit-0.3.0_rc8-r1',
	#'app-portage/layman-1.3.1',
	#'app-portage/eix-0.20.1',
	]


Exclude= {'packages': {
		'media-libs/sdl-pango': None,
		 },
	'anti-packages': {'app-emulation/emul-linux-x86-baselibs': None},
	'categories': {'app-portage': None,
		'app-portage/gentoolkit': None
		},
	'filenames': {'sys-auth/consolekit-0.4.1': re.compile('sys-auth/consolekit-0.4.1')
		}
	}


def get_props(cpvs):
	props = {}
	for cpv in cpvs:
		props[cpv] = PROPS[cpv].copy()
	return props

class Dbapi(object):
	"""Fake portage dbapi class used to return
	pre-determined test data in place of a live system

	@param cp_all: list of cat/pkg's to use for testing
				eg: ['app-portage/gentoolkit', 'app-portage/porthole',...]
	@param cpv_all: list of cat/pkg-ver's to use for testing.
	@param props: dictionary of ebuild properties to use for testing.
				eg: {'cpv': {"SRC_URI": 'http://...', "RESTRICT": restriction},}
	@param cp_list: ?????????
	"""

	def __init__(self, cp_all=None, cpv_all=None, props=None,
			cp_list=None, name=None):
		self._cp_all = cp_all
		self._cpv_all = cpv_all
		self._props = props
		self._cp_list = cp_list
		self.name = name
		#print(self.name, "DBAPI: cpv_all=")
		#print(self._cpv_all)
		#print(self.name, "DBAPI: props=")
		#print(self._props)

	def cp_all(self):
		return self._cp_all[:]

	def cp_list(self, package):
		#print(self._cp_list)
		if self._cp_list is None or self._cp_list==[]:
			cplist = []
			for cpv in self._cpv_all:
				parts = portage.catpkgsplit(cpv)
				cp='/'.join(parts[:2])
				if cp == package:
					cplist.append(cpv)
			#print("package = %s, cplist = %s" %(package, cplist))
			return cplist
		else:
			return self._cp_list

	def cpv_all(self):
		#print(self.name, type(self._cpv_all), self._cpv_all)
		return self._cpv_all

	def cpv_exists(self, cpv):
		return cpv in self._cpv_all

	def aux_get(self, cpv, prop_list):
		"""only need stubs for ["SRC_URI","RESTRICT"]
		"""
		#print("FAKE DBAPI", cpv, prop_list)
		props = []
		for prop in prop_list:
			if cpv in self._props:
				props.append(self._props[cpv][prop])
			else:
				raise KeyError(self.name)
		#print(self.name,  "DBAPI", cpv, props)
		return props


class OutputSimulator(object):
	"""Simple output accumulator used for testing.
	Simulates eclean.output.OutputControl class """

	def __init__(self, callback):
		self.callback = callback

	def set_data(self, data):
		"""sets the data for the progress_controller to return
		for the test being performed"""
		self.data = data

	def einfo(self, message=""):
		self.callback('einfo', message)

	def eprompt(self, message):
		self.callback('eprompt', message)

	def prettySize(self, size, justify=False, color=None):
		self.callback('prettySize', size)

	def yesNoAllPrompt(self, message="Dummy"):
		self.callback('yesNoAllPrompt', message)

	def progress_controller(self, size, key, clean_list, file_type):
		self.callback('progress_controller', self.data)
		return self.data

	def total(self, mode, size, num_files, verb, action):
		pass

	def list_pkgs(self, pkgs):
		self.callback('list_pkgs', pkgs)


class TestDisfiles(object):

	def __init__(self):
		self.workdir = None
		self.target_file = None
		self.target_symlink = None
		self.test_filepaths = None

	def setUp(self):
		# create the dist dir
		self.tmpdir = mkdtemp()
		#print("New tmpdir =", self.tmpdir)
		os.chmod(self.tmpdir, dir_mode)
		self.workdir = os.path.join(self.tmpdir, 'distfiles')
		dir = os.path.dirname(os.path.abspath(__file__))
		file = os.path.join(dir,"testdistfiles.tar.gz")
		command = "tar -xpf %s -C %s" %(file, self.tmpdir)
		retcode = subprocess.call(command, shell=True)
		# create a symlink as part of the test files
		#print()
		self.target_symlink = "symlink-1.0.0.tar.gz"
		os.symlink(file, os.path.join(self.workdir, self.target_symlink))
		self.files = FILES[:]
		self.files.append(self.target_symlink)
		self.test_filepaths = []
		for file in self.files:
			self.test_filepaths.append(os.path.join(self.workdir, file))

	def tearDown(self):
		for file in self.test_filepaths:
			os.unlink(file)
		#print("deleting workdir =", self.workdir)
		os.rmdir(self.workdir)
		#print("deleting tmpdir =", self.tmpdir)
		os.rmdir(self.tmpdir)


