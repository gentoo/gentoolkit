# Copyright(c) 2009, Gentoo Foundation
# Copyright 2010 Brian Dolbec <brian.dolbec@gmail.com>
#
# License: GPL2/BSD

# $Header$


from __future__ import print_function

import os
import unittest
from tempfile import NamedTemporaryFile, mkdtemp
import subprocess



dir_mode = 0774

CPVS = [u'sys-auth/consolekit-0.4.1', u'sys-apps/devicekit-power-014',
	u'media-libs/sdl-pango-0.1.2', u'sys-apps/help2man-1.37.1',
	u'app-emulation/emul-linux-x86-baselibs-20100220'
]

PROPS = {
	u'sys-apps/devicekit-power-014': {u'SRC_URI':
		u'http://hal.freedesktop.org/releases/DeviceKit-power-014.tar.gz',
		u"RESTRICT": u''},
	u'sys-apps/help2man-1.37.1': {u"SRC_URI": u'mirror://gnu/help2man/help2man-1.37.1.tar.gz',
		u"RESTRICT": u''},
	u'sys-auth/consolekit-0.4.1': { u"SRC_URI":
		u'http://www.freedesktop.org/software/ConsoleKit/dist/ConsoleKit-0.4.1.tar.bz2',
		u"RESTRICT": u''},
	u'app-emulation/emul-linux-x86-baselibs-20100220': {
		u"SRC_URI": u'mirror://gentoo/emul-linux-x86-baselibs-20100220.tar.gz',
		u"RESTRICT": u'strip'},
	u'media-libs/sdl-pango-0.1.2': {
		u"SRC_URI": u'mirror://sourceforge/sdlpango/SDL_Pango-0.1.2.tar.gz http://zarb.org/~gc/t/SDL_Pango-0.1.2-API-adds.patch',
		u"RESTRICT": u''}
}

FILES = [
	u'DeviceKit-power-014.tar.gz',
	u'help2man-1.37.1.tar.gz',
	u'ConsoleKit-0.4.1.tar.bz2',
	u'emul-linux-x86-baselibs-20100220.tar.gz',
	u'SDL_Pango-0.1.2.tar.gz',
	u'SDL_Pango-0.1.2-API-adds.patch'
]


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
		#need to determine the data to return
		# and gather some from a live system to use for testing
		pass

	def cpv_all(self):
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
				raise KeyError, self.name
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


