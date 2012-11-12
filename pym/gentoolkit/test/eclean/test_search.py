#!/usr/bin/python


# Copyright(c) 2009, Gentoo Foundation
# Copyright 2010 Brian Dolbec <brian.dolbec@gmail.com>
#
# License: GPL2/BSD

# $Header$


from __future__ import print_function


from tempfile import NamedTemporaryFile, mkdtemp
import unittest
import re

from gentoolkit.test.eclean.distsupport import *
import gentoolkit.eclean.search as search
from gentoolkit.eclean.search import DistfilesSearch
from gentoolkit.eclean.exclude import parseExcludeFile

"""Tests for eclean's distfiles search functions."""


class DistLimits(DistfilesSearch):
	"""subclass the DistfilesSearch class in order to override a number of
	functions to isolate & test"""

	def __init__(self,
			output=lambda x: None,
			portdb=None,
			vardb=None,
			):
		DistfilesSearch.__init__(self, output, portdb, vardb)
		self.data = None

	def set_data(self, data):
		"""sets the data for the functions to return for
		the test being performed"""
		self.data = data


class TestCheckLimits(unittest.TestCase):
	"""Test the eclean.search.DistfilesSearch._check_limits() group.

	it will test [ _get_default_checks(), _check_limits(),
	_isreg_check_(), _size_check_(), _time_check_(), _filenames_check_()]
	"""

	test_excludes = {
		'blank': {},
		'filenames': {
			'filenames': {'help2man-1.37.1.tar.gz': re.compile('help2man-1.37.1.tar.gz')}
			}
		}

	def setUp(self):
		self.testdata = [
			# test is_reg_limit alone, will give a base clean_me
			{ 'test': 'is_reg_limit',
			'params': (0, 0, self.test_excludes['blank']),
			'results': FILES[:],
			'output': ["   - skipping size limit check",
				"   - skipping time limit check",
				"   - skipping exclude filenames check"
				]
			},
			# test size_limit trip
			{ 'test': 'size_limit',
			'params': (1024000, 0, self.test_excludes['blank']),
			'results': FILES[:3] + FILES[4:],
			'output': [
				"   - skipping time limit check",
				"   - skipping exclude filenames check"
				]
			},
			# test time_limit trip
			{ 'test': 'time_limit',
			'params': (0,1112671872, self.test_excludes['blank']),
			'results': [FILES[4]], # + FILES[5:],
			'output': ["   - skipping size limit check",
				"   - skipping exclude filenames check"
				]
			},
			# test filenames_limit trip
			{ 'test': 'filenames_limit',
			'params': (0, 0, self.test_excludes['filenames']),
			'results': FILES[:1] + FILES[2:],
			'output': ["   - skipping size limit check",
				"   - skipping time limit check",
				]
			}
		]

		self.testwork = TestDisfiles()
		self.testwork.setUp()
		self.workdir = self.testwork.workdir
		self.target_class = DistLimits() #DistCheckLimits()
		self.output = OutputSimulator(self.callback)
		self.target_class.output = self.output
		self.callback_data = []
		self.test_index = 0

	def tearDown(self):
		self.testwork.tearDown()
		#pass

	def get_test(self, num):
		return self.testdata[num]

	def callback(self, id, data):
		self.callback_data.append(data)

	def set_limits(self, test):
		limit = {}
		#set is_reg always to testdata[0]
		t1 = self.testdata[0]
		limit[t1['test']] = {}
		name = test['test']
		limit[name] = {}
		limits = test['limits']
		for i in range(6):
			file = self.testwork.files[i]
			limits = test['limits']
			limit[t1['test']][file] = t1['limits'][i]
			if name != t1['test']:
				limit[name][file] = limits[i]
		return limit


	def test_check_limits(self):
		"""Testing DistfilesSearch._check_limits()"""
		# pass in output=self.output.einfo
		self.target_class.output = self.output.einfo
		run_callbacks = []
		run_results = []
		print()
		# run the tests
		for i in range(4):
			clean_me = {}
			test = self.get_test(i)
			#print("test =", test['test'])
			if not test:
				print("Error getting test data for index:", i)
			#self.target_class.set_data(self.set_limits(test))
			size_chk, time_chk, exclude = test["params"]
			checks = self.target_class._get_default_checks(size_chk, time_chk, exclude, False)
			clean_me = self.target_class._check_limits(self.workdir, checks, clean_me)
			results = sorted(clean_me)
			run_results.append(results)
			self.callback_data.sort()
			run_callbacks.append(self.callback_data)
			self.callback_data = []
			results = None

		# check results
		for i in range(4):
			test = self.get_test(i)
			print("test =", test['test'])
			if not test:
				print("Error getting test data for index:", i)
			test['results'].sort()
			#print("actual=", run_results[i])
			#print("should-be=", test['results'])
			self.failUnlessEqual(run_results[i], test["results"],
				"/ntest_check_limits, test# %d, test=%s, diff=%s"
				%(i, test['test'], str(set(run_results[i]).difference(test['results'])))
			)
			test['output'].sort()
			self.failUnlessEqual(run_callbacks[i], test['output'])


class TestFetchRestricted(unittest.TestCase):
	"""Tests eclean.search.DistfilesSearch._fetch_restricted and _unrestricted
	functions
	"""

	def setUp(self):
		self.vardb = Dbapi(cp_all=[], cpv_all=CPVS,
			props=PROPS, cp_list=[], name="FAKE VARDB")
		self.portdb = Dbapi(cp_all=[], cpv_all=CPVS[:4],
			props=get_props(CPVS[:4]), cp_list=[], name="FAKE PORTDB")
		# set a fetch restricted pkg
		self.portdb._props[CPVS[0]]["RESTRICT"] = 'fetch'
		self.callback_data = []
		self.output = self.output = OutputSimulator(self.callback)
		self.target_class = DistfilesSearch(self.output.einfo, self.portdb, self.vardb)
		self.target_class.portdb = self.portdb
		self.target_class.portdb = self.portdb
		self.results = {}
		self.testdata = {
			'fetch_restricted1':{
					'deprecated':
						{'app-emulation/emul-linux-x86-baselibs-20100220': 'mirror://gentoo/emul-linux-x86-baselibs-20100220.tar.gz'
						},
					'pkgs':
						{'sys-auth/consolekit-0.4.1': 'http://www.freedesktop.org/software/ConsoleKit/dist/ConsoleKit-0.4.1.tar.bz2'
						},
					'output': [
						'!!! "Deprecation Warning: Installed package: app-emulation/emul-linux-x86-baselibs-20100220\n\tIs no longer in the tree or an installed overlay\n'
						]
					},
			'fetch_restricted2':{
					'deprecated':
						{'app-emulation/emul-linux-x86-baselibs-20100220': 'mirror://gentoo/emul-linux-x86-baselibs-20100220.tar.gz'
						},
					'pkgs':
						{'sys-auth/consolekit-0.4.1': 'http://www.freedesktop.org/software/ConsoleKit/dist/ConsoleKit-0.4.1.tar.bz2'
						},
					'output': [
						'!!! "Deprecation Warning: Installed package: app-emulation/emul-linux-x86-baselibs-20100220\n\tIs no longer in the tree or an installed overlay\n',
						'   - Key Error looking up: app-portage/deprecated-pkg-1.0.0'
						]
					},
			'unrestricted1':{
					'deprecated':{
						'app-emulation/emul-linux-x86-baselibs-20100220': 'mirror://gentoo/emul-linux-x86-baselibs-20100220.tar.gz'
						},
					'pkgs': {
						'sys-apps/devicekit-power-014': 'http://hal.freedesktop.org/releases/DeviceKit-power-014.tar.gz',
						'sys-apps/help2man-1.37.1': 'mirror://gnu/help2man/help2man-1.37.1.tar.gz',
						'sys-auth/consolekit-0.4.1': 'http://www.freedesktop.org/software/ConsoleKit/dist/ConsoleKit-0.4.1.tar.bz2',
						'app-emulation/emul-linux-x86-baselibs-20100220': 'mirror://gentoo/emul-linux-x86-baselibs-20100220.tar.gz',
						'media-libs/sdl-pango-0.1.2': 'mirror://sourceforge/sdlpango/SDL_Pango-0.1.2.tar.gz http://zarb.org/~gc/t/SDL_Pango-0.1.2-API-adds.patch'
						},
					'output': [
						'!!! "Deprecation Warning: Installed package: app-emulation/emul-linux-x86-baselibs-20100220\n\tIs no longer in the tree or an installed overlay\n',
						]
					},
			'unrestricted2':{
					'deprecated':{
						'app-emulation/emul-linux-x86-baselibs-20100220': 'mirror://gentoo/emul-linux-x86-baselibs-20100220.tar.gz'
						},
					'pkgs': {
						'sys-apps/devicekit-power-014': 'http://hal.freedesktop.org/releases/DeviceKit-power-014.tar.gz',
						'sys-apps/help2man-1.37.1': 'mirror://gnu/help2man/help2man-1.37.1.tar.gz',
						'sys-auth/consolekit-0.4.1': 'http://www.freedesktop.org/software/ConsoleKit/dist/ConsoleKit-0.4.1.tar.bz2',
						'app-emulation/emul-linux-x86-baselibs-20100220': 'mirror://gentoo/emul-linux-x86-baselibs-20100220.tar.gz',
						'media-libs/sdl-pango-0.1.2': 'mirror://sourceforge/sdlpango/SDL_Pango-0.1.2.tar.gz http://zarb.org/~gc/t/SDL_Pango-0.1.2-API-adds.patch'
						},
					'output': [
						'!!! "Deprecation Warning: Installed package: app-emulation/emul-linux-x86-baselibs-20100220\n\tIs no longer in the tree or an installed overlay\n',
						'   - Key Error looking up: app-portage/deprecated-pkg-1.0.0'
						]
					}
			}


	def callback(self, id, data):
		self.callback_data.append(data)


	def test__fetch_restricted(self):
		self.results = {}
		pkgs, deprecated = self.target_class._fetch_restricted(None, CPVS)
		self.record_results('fetch_restricted1', pkgs, deprecated)

		self.callback_data = []
		cpvs = CPVS[:]
		cpvs.append('app-portage/deprecated-pkg-1.0.0')
		pkgs, deprecated = self.target_class._fetch_restricted(None, cpvs)
		self.record_results('fetch_restricted2', pkgs, deprecated)
		self.check_results("test_fetch_restricted")


	def test_unrestricted(self):
		self.results = {}
		pkgs, deprecated = self.target_class._unrestricted(None, CPVS)
		self.record_results('unrestricted1', pkgs, deprecated)
		self.callback_data = []
		cpvs = CPVS[:]
		cpvs.append('app-portage/deprecated-pkg-1.0.0')
		pkgs, deprecated = self.target_class._unrestricted(None, cpvs)
		self.record_results('unrestricted2', pkgs, deprecated)
		self.check_results("test_unrestricted")


	def check_results(self, test_name):
		print("\nChecking results for %s,............" %test_name)
		for key in sorted(self.results):
			testdata = self.testdata[key]
			results = self.results[key]
			for item in sorted(testdata):
				if sorted(results[item]) == sorted(testdata[item]):
					test = "OK"
				else:
					test = "FAILED"
				print("comparing %s, %s" %(key, item), test)
				self.failUnlessEqual(sorted(testdata[item]), sorted(results[item]),
					"\n%s: %s %s data does not match\nresult=" %(test_name, key, item) +\
					str(results[item]) + "\ntestdata=" + str(testdata[item]))


	def record_results(self, test, pkgs, deprecated):
		self.results[test] = {'pkgs': pkgs,
				'deprecated': deprecated,
				'output': self.callback_data
				}


	def tearDown(self):
		del self.portdb, self.vardb


class TestNonDestructive(unittest.TestCase):
	"""Tests eclean.search.DistfilesSearch._non_destructive and _destructive
	functions, with addition useage tests of fetch_restricted() and _unrestricted()
	"""

	def setUp(self):
		self.vardb = Dbapi(cp_all=[], cpv_all=CPVS,
			props=PROPS, cp_list=[], name="FAKE VARDB")
		self.portdb = Dbapi(cp_all=[], cpv_all=CPVS[:4],
			props=get_props(CPVS[:4]), cp_list=[], name="FAKE PORTDB")
		print(self.portdb)
		# set a fetch restricted pkg
		self.portdb._props[CPVS[0]]["RESTRICT"] = 'fetch'
		self.callback_data = []
		self.output = OutputSimulator(self.callback)
		self.target_class = DistfilesSearch(self.output.einfo, self.portdb, self.vardb)
		search.exclDictExpand = self.exclDictExpand
		self.exclude = parseExcludeFile(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'distfiles.exclude'), self.output.einfo)
		#print(self.callback_data)
		#print(self.exclude)
		self.callback_data = []
		self.results = {}
		self.testdata = {
			'non_destructive1':{
					'deprecated':
						{'app-emulation/emul-linux-x86-baselibs-20100220': 'mirror://gentoo/emul-linux-x86-baselibs-20100220.tar.gz'
						},
					'pkgs': {
						'sys-auth/consolekit-0.4.1': 'http://www.freedesktop.org/software/ConsoleKit/dist/ConsoleKit-0.4.1.tar.bz2',
						'sys-apps/help2man-1.37.1': 'mirror://gnu/help2man/help2man-1.37.1.tar.gz',
						'sys-apps/devicekit-power-014': 'http://hal.freedesktop.org/releases/DeviceKit-power-014.tar.gz',
						'app-emulation/emul-linux-x86-baselibs-20100220': 'mirror://gentoo/emul-linux-x86-baselibs-20100220.tar.gz',
						'media-libs/sdl-pango-0.1.2': 'mirror://sourceforge/sdlpango/SDL_Pango-0.1.2.tar.gz http://zarb.org/~gc/t/SDL_Pango-0.1.2-API-adds.patch'
						},
					'output': [
						'   - getting complete ebuild list',
						'   - getting source file names for 5 ebuilds',
						'!!! "Deprecation Warning: Installed package: app-emulation/emul-linux-x86-baselibs-20100220\n\tIs no longer in the tree or an installed overlay\n'
						]
					},
			'non_destructive2':{
					'deprecated': {
						},
					'pkgs': {
						'sys-apps/devicekit-power-014': 'http://hal.freedesktop.org/releases/DeviceKit-power-014.tar.gz',
						'sys-auth/consolekit-0.4.1': 'http://www.freedesktop.org/software/ConsoleKit/dist/ConsoleKit-0.4.1.tar.bz2',
						'media-libs/sdl-pango-0.1.2': 'mirror://sourceforge/sdlpango/SDL_Pango-0.1.2.tar.gz http://zarb.org/~gc/t/SDL_Pango-0.1.2-API-adds.patch'
						},
					'output': [
						'   - getting complete ebuild list',
						'   - getting source file names for 3 installed ebuilds',
						'   - getting fetch-restricted source file names for 2 remaining ebuilds'
						]
					},
			'non_destructive3':{
					'deprecated':{
						},
					'pkgs': {
						'sys-apps/devicekit-power-014': 'http://hal.freedesktop.org/releases/DeviceKit-power-014.tar.gz',
						'sys-auth/consolekit-0.4.1': 'http://www.freedesktop.org/software/ConsoleKit/dist/ConsoleKit-0.4.1.tar.bz2',
						'app-emulation/emul-linux-x86-baselibs-20100220': 'mirror://gentoo/emul-linux-x86-baselibs-20100220.tar.gz',
						},
					'output': [
						'   - getting complete ebuild list',
						'   - getting source file names for 2 installed ebuilds',
						'   - getting fetch-restricted source file names for 3 remaining ebuilds'
						]
					},
			'destructive1':{
					'deprecated':{
						'app-emulation/emul-linux-x86-baselibs-20100220': 'mirror://gentoo/emul-linux-x86-baselibs-20100220.tar.gz'
						},
					'pkgs': {
						'sys-apps/devicekit-power-014': 'http://hal.freedesktop.org/releases/DeviceKit-power-014.tar.gz',
						'sys-apps/help2man-1.37.1': 'mirror://gnu/help2man/help2man-1.37.1.tar.gz',
						'sys-auth/consolekit-0.4.1': 'http://www.freedesktop.org/software/ConsoleKit/dist/ConsoleKit-0.4.1.tar.bz2',
						'app-emulation/emul-linux-x86-baselibs-20100220': 'mirror://gentoo/emul-linux-x86-baselibs-20100220.tar.gz',
						'media-libs/sdl-pango-0.1.2': 'mirror://sourceforge/sdlpango/SDL_Pango-0.1.2.tar.gz http://zarb.org/~gc/t/SDL_Pango-0.1.2-API-adds.patch'
						},
					'output': [
						'   - processing 5 installed ebuilds', '   - processing excluded',
						'   - (5 of 0 total) additional excluded packages to get source filenames for',
						'!!! "Deprecation Warning: Installed package: app-emulation/emul-linux-x86-baselibs-20100220\n\tIs no longer in the tree or an installed overlay\n'
						]
					},
			'destructive2':{
					'deprecated':{
						},
					'pkgs': {
						},
					'output': [
						'   - processing 0 installed packages',
						'   - processing excluded', '   - (0 of 0 total) additional excluded packages to get source filenames for'
						]
					},
			'destructive3':{
					'deprecated':{
						},
					'pkgs': {
						'app-portage/gentoolkit-0.3.0_rc8-r1': 'mirror://gentoo/gentoolkit-0.3.0_rc8.tar.gz http://dev.gentoo.org/~fuzzyray/distfiles/gentoolkit-0.3.0_rc8.tar.gz',
						'sys-apps/devicekit-power-014': 'http://hal.freedesktop.org/releases/DeviceKit-power-014.tar.gz',
						'app-portage/gentoolkit-0.3.0_rc8': 'mirror://gentoo/gentoolkit-0.3.0_rc8.tar.gz http://dev.gentoo.org/~fuzzyray/distfiles/gentoolkit-0.3.0_rc8.tar.gz',
						'app-portage/gentoolkit-0.2.4.6-r1': 'mirror://gentoo/gentoolkit-0.2.4.6.tar.gz http://dev.gentoo.org/~fuzzyray/distfiles/gentoolkit-0.2.4.6.tar.gz',
						'app-portage/gentoolkit-0.3.0_rc7': 'mirror://gentoo/gentoolkit-0.3.0_rc7.tar.gz http://dev.gentoo.org/~fuzzyray/distfiles/gentoolkit-0.3.0_rc7.tar.gz',
						'app-portage/gentoolkit-0.2.4.6': 'mirror://gentoo/gentoolkit-0.2.4.6.tar.gz http://dev.gentoo.org/~fuzzyray/distfiles/gentoolkit-0.2.4.6.tar.gz',
						'app-portage/eix-0.19.2': 'mirror://sourceforge/eix/eix-0.19.2.tar.xz',
						'app-portage/gentoolkit-0.2.4.5': 'mirror://gentoo/gentoolkit-0.2.4.5.tar.gz http://dev.gentoo.org/~fuzzyray/distfiles/gentoolkit-0.2.4.5.tar.gz',
						'app-portage/gentoolkit-0.3.0_rc9': 'mirror://gentoo/gentoolkit-0.3.0_rc9.tar.gz http://dev.gentoo.org/~fuzzyray/distfiles/gentoolkit-0.3.0_rc9.tar.gz',
						'app-portage/eix-0.20.1': 'mirror://sourceforge/eix/eix-0.20.1.tar.xz',
						'app-portage/eix-0.20.2': 'mirror://berlios/eix/eix-0.20.2.tar.xz'
						},
					'output': [
						'   - processing excluded',
						'   - (10 of 10 total) additional excluded packages to get source filenames for'
						]
					},
			'destructive4':{
					'deprecated':{
						},
					'pkgs': {
						'sys-auth/consolekit-0.4.1':
							'http://www.freedesktop.org/software/ConsoleKit/dist/ConsoleKit-0.4.1.tar.bz2',
						'sys-apps/devicekit-power-014':
							'http://hal.freedesktop.org/releases/DeviceKit-power-014.tar.gz',
						'media-libs/sdl-pango-0.1.2':
							'mirror://sourceforge/sdlpango/SDL_Pango-0.1.2.tar.gz http://zarb.org/~gc/t/SDL_Pango-0.1.2-API-adds.patch'
						},
					'output': [
						'   - processing 3 installed ebuilds',
						'   - processing excluded',
						'   - (3 of 0 total) additional excluded packages to get source filenames for'
						]
					},
			'destructive5':{
					'deprecated':{
						},
					'pkgs': {
						'x11-base/xorg-server-1.7.5': 'http://xorg.freedesktop.org/releases/individual/xserver/xorg-server-1.7.5.tar.bz2',
						'app-portage/gentoolkit-0.3.0_rc8-r1': 'mirror://gentoo/gentoolkit-0.3.0_rc8.tar.gz http://dev.gentoo.org/~fuzzyray/distfiles/gentoolkit-0.3.0_rc8.tar.gz',
						'sys-apps/devicekit-power-014': 'http://hal.freedesktop.org/releases/DeviceKit-power-014.tar.gz',
						'x11-misc/util-macros-1.6.0': 'http://xorg.freedesktop.org/releases/individual/util/util-macros-1.6.0.tar.bz2',
						'app-portage/eix-0.19.2': 'mirror://sourceforge/eix/eix-0.19.2.tar.xz',
						'app-portage/gentoolkit-0.3.0_rc8': 'mirror://gentoo/gentoolkit-0.3.0_rc8.tar.gz http://dev.gentoo.org/~fuzzyray/distfiles/gentoolkit-0.3.0_rc8.tar.gz',
						'app-portage/gentoolkit-0.2.4.6-r1': 'mirror://gentoo/gentoolkit-0.2.4.6.tar.gz http://dev.gentoo.org/~fuzzyray/distfiles/gentoolkit-0.2.4.6.tar.gz',
						'app-portage/gentoolkit-0.3.0_rc7': 'mirror://gentoo/gentoolkit-0.3.0_rc7.tar.gz http://dev.gentoo.org/~fuzzyray/distfiles/gentoolkit-0.3.0_rc7.tar.gz',
						'sys-auth/consolekit-0.4.1': 'http://www.freedesktop.org/software/ConsoleKit/dist/ConsoleKit-0.4.1.tar.bz2',
						'app-portage/gentoolkit-0.2.4.6': 'mirror://gentoo/gentoolkit-0.2.4.6.tar.gz http://dev.gentoo.org/~fuzzyray/distfiles/gentoolkit-0.2.4.6.tar.gz',
						'media-libs/sdl-pango-0.1.2': 'mirror://sourceforge/sdlpango/SDL_Pango-0.1.2.tar.gz http://zarb.org/~gc/t/SDL_Pango-0.1.2-API-adds.patch',
						'x11-libs/pixman-0.16.4': 'http://xorg.freedesktop.org/releases/individual/lib/pixman-0.16.4.tar.bz2',
						'app-portage/gentoolkit-0.2.4.5': 'mirror://gentoo/gentoolkit-0.2.4.5.tar.gz http://dev.gentoo.org/~fuzzyray/distfiles/gentoolkit-0.2.4.5.tar.gz',
						'app-portage/gentoolkit-0.3.0_rc9': 'mirror://gentoo/gentoolkit-0.3.0_rc9.tar.gz http://dev.gentoo.org/~fuzzyray/distfiles/gentoolkit-0.3.0_rc9.tar.gz',
						'app-portage/eix-0.20.1': 'mirror://sourceforge/eix/eix-0.20.1.tar.xz',
						'app-portage/eix-0.20.2': 'mirror://berlios/eix/eix-0.20.2.tar.xz'
						},
					'output': [
						'   - processing 6 installed ebuilds',
						'   - processing excluded',
						'   - (16 of 10 total) additional excluded packages to get source filenames for'
						]
					}
			}


	def callback(self, id, data):
		self.callback_data.append(data)


	def exclDictExpand(self, exclude):
		#print("Using Fake Testing exclDictExpand()")
		return [
			#'app-portage/layman',
			'app-portage/eix',
			'app-portage/gentoolkit',
			#app-portage/portage-utils',
			]


	def test_non_destructive(self):
		self.results = {}
		pkgs, deprecated = self.target_class._non_destructive(destructive=False,
			fetch_restricted=False, pkgs_=None)
		self.record_results('non_destructive1', pkgs, deprecated)

		pkgs = None
		deprecated = None
		self.callback_data = []
		self.vardb._cpv_all=CPVS[:3]
		self.vardb._props=get_props(CPVS[:3])
		self.portdb._cpv_all=CPVS[:]
		self.portdb._props=get_props(CPVS)
		self.target_class.installed_cpvs = None
		pkgs, deprecated = self.target_class._non_destructive(destructive=True,
			fetch_restricted=True, pkgs_=None)
		self.record_results('non_destructive2', pkgs, deprecated)

		pkgs = None
		deprecated = None
		self.callback_data = []
		self.vardb._cpv_all=CPVS[:2]
		self.vardb._props=get_props(CPVS[:2])
		self.portdb._cpv_all=CPVS[:]
		self.portdb._props=get_props(CPVS)
		# set a fetch restricted pkg
		self.portdb._props[CPVS[4]]["RESTRICT"] = 'fetch'
		pkgs = {'sys-apps/devicekit-power-014': 'http://hal.freedesktop.org/releases/DeviceKit-power-014.tar.gz'}
		pkgs, deprecated = self.target_class._non_destructive(destructive=True,
			fetch_restricted=True, pkgs_=pkgs)
		self.record_results('non_destructive3', pkgs, deprecated)
		self.check_results("test_non_destructive")


	def check_results(self, test_name):
		print("\nChecking results for %s,............" %test_name)
		for key in sorted(self.results):
			testdata = self.testdata[key]
			results = self.results[key]
			for item in sorted(testdata):
				if sorted(results[item]) == sorted(testdata[item]):
					test = "OK"
				else:
					test = "FAILED"
				print("comparing %s, %s..." %(key, item), test)
				if test == "FAILED":
					print("", sorted(results[item]), "\n",  sorted(testdata[item]))
				self.failUnlessEqual(sorted(testdata[item]), sorted(results[item]),
					"\n%s: %s, %s data does not match\n"
					%(test_name, key, item) + \
					"result=" + str(results[item]) + "\ntestdata=" + str(testdata[item])
				)


	def record_results(self, test, pkgs, deprecated):
		self.results[test] = {'pkgs': pkgs,
				'deprecated': deprecated,
				'output': self.callback_data
				}

	def test_destructive(self):
		self.results = {}
		pkgs, deprecated = self.target_class._destructive(package_names=False,
			exclude={}, pkgs_=None, installed_included=False )
		self.record_results('destructive1', pkgs, deprecated)

		self.callback_data = []
		self.vardb._cpv_all=CPVS[:3]
		self.vardb._props=get_props(CPVS[:3])
		self.portdb._cpv_all=CPVS[:]
		self.portdb._props=get_props(CPVS)
		pkgs, deprecated = self.target_class._destructive(package_names=True,
			exclude={}, pkgs_=None, installed_included=False )
		self.record_results('destructive2', pkgs, deprecated)

		self.callback_data = []
		cpvs = CPVS[2:4]
		cpvs.extend(CPVS3)
		self.vardb._cpv_all=sorted(cpvs)
		self.vardb._props= PROPS.update(get_props(CPVS3))
		self.portdb._cpv_all=sorted(CPVS + CPVS2)
		self.portdb._props=get_props(CPVS+CPVS2)
		# set a fetch restricted pkg
		self.portdb._props[CPVS[4]]["RESTRICT"] = 'fetch'
		pkgs = {'sys-apps/devicekit-power-014': 'http://hal.freedesktop.org/releases/DeviceKit-power-014.tar.gz'}
		pkgs, deprecated = self.target_class._destructive(package_names=True,
			exclude={}, pkgs_=pkgs, installed_included=True )
		self.record_results('destructive3', pkgs, deprecated)

		self.callback_data = []
		self.vardb._cpv_all=CPVS[:3]
		self.vardb._props=get_props(CPVS[:3])
		self.portdb._cpv_all=CPVS[:]
		self.portdb._props=get_props(CPVS)
		pkgs, deprecated = self.target_class._destructive(package_names=False,
			exclude=self.exclude, pkgs_=None, installed_included=False )
		self.record_results('destructive4', pkgs, deprecated)
		self.check_results("test_destructive")

		self.callback_data = []
		self.vardb._cpv_all=CPVS[:3]
		self.vardb._cpv_all.extend(CPVS3)
		self.vardb._props=get_props(self.vardb._cpv_all)
		self.portdb._cpv_all=CPVS2
		#self.portdb._cpv_all.extend(CPVS2)
		self.portdb._props=PROPS
		pkgs, deprecated = self.target_class._destructive(package_names=False,
			exclude=self.exclude, pkgs_=None, installed_included=False )
		self.record_results('destructive5', pkgs, deprecated)
		self.check_results("test_destructive")


	def tearDown(self):
		del self.portdb, self.vardb


class TestRemoveProtected(unittest.TestCase):
	"""tests the  eclean.search.DistfilesSearch._remove_protected()
	"""

	def setUp(self):
		self.target_class = DistfilesSearch(lambda x: None)
		self.results = {'layman-1.2.5.tar.gz': '/path/to/some/where/layman-1.2.5.tar.gz'}

	def test_remove_protected(self):
		results = self.target_class._remove_protected(PKGS, CLEAN_ME)
		self.failUnlessEqual(results, self.results,
			"\ntest_remove_protected: data does not match\nresult=" +\
			str(results) + "\ntestdata=" + str(self.results))


def test_main():
	suite = unittest.TestLoader()
	suite.loadTestsFromTestCase(TestCheckLimits)
	suite.loadTestsFromTestCase(TestFetchRestricted)
	suite.loadTestsFromTestCase(TestNonDestructive)
	suite.loadTestsFromTestCase(TestRemoveProtected)
	unittest.TextTestRunner(verbosity=2).run(suite)
test_main.__test__ = False


if __name__ == '__main__':
	test_main()
