# Copyright(c) 2009, Gentoo Foundation
# Copyright 2010 Brian Dolbec <brian.dolbec@gmail.com>
#
# License: GPL2/BSD

# $Header$


from __future__ import print_function


from tempfile import NamedTemporaryFile, mkdtemp
import unittest
import re

try:
	from test import test_support
except ImportError:
	from test import support as test_support

from gentoolkit.test.eclean.distsupport import *
from gentoolkit.eclean.search import DistfilesSearch


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
			checks = self.target_class._get_default_checks(size_chk, time_chk, exclude)
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
			props=self.get_props(CPVS[:4]), cp_list=[], name="FAKE PORTDB")
		# set a fetch restricted pkg
		self.portdb._props[CPVS[0]]["RESTRICT"] = u'fetch'
		self.callback_data = []
		self.output = self.output = OutputSimulator(self.callback)
		self.target_class = DistfilesSearch(self.output.einfo, self.portdb, self.vardb)
		self.target_class.portdb = self.portdb
		self.target_class.portdb = self.portdb
		self.testdata = {
			'fetch_restricted1':{
					'deprecated':
						{u'app-emulation/emul-linux-x86-baselibs-20100220': u'mirror://gentoo/emul-linux-x86-baselibs-20100220.tar.gz'
						},
					'pkgs':
						{u'sys-auth/consolekit-0.4.1': u'http://www.freedesktop.org/software/ConsoleKit/dist/ConsoleKit-0.4.1.tar.bz2'
						},
					'output': [
						u'!!! "Deprecation Warning: Installed package: app-emulation/emul-linux-x86-baselibs-20100220\n\tIs no longer in the tree or an installed overlay\n'
						]
					},
			'fetch_restricted2':{
					'deprecated':
						{u'app-emulation/emul-linux-x86-baselibs-20100220': u'mirror://gentoo/emul-linux-x86-baselibs-20100220.tar.gz'
						},
					'pkgs':
						{u'sys-auth/consolekit-0.4.1': u'http://www.freedesktop.org/software/ConsoleKit/dist/ConsoleKit-0.4.1.tar.bz2'
						},
					'output': [
						u'!!! "Deprecation Warning: Installed package: app-emulation/emul-linux-x86-baselibs-20100220\n\tIs no longer in the tree or an installed overlay\n',
						'   - Key Error looking up: app-portage/deprecated-pkg-1.0.0'
						]
					},
			'unrestricted1':{
					'deprecated':{
						u'app-emulation/emul-linux-x86-baselibs-20100220': u'mirror://gentoo/emul-linux-x86-baselibs-20100220.tar.gz'
						},
					'pkgs': {
						u'sys-apps/devicekit-power-014': u'http://hal.freedesktop.org/releases/DeviceKit-power-014.tar.gz',
						u'sys-apps/help2man-1.37.1': u'mirror://gnu/help2man/help2man-1.37.1.tar.gz',
						u'sys-auth/consolekit-0.4.1': u'http://www.freedesktop.org/software/ConsoleKit/dist/ConsoleKit-0.4.1.tar.bz2',
						u'app-emulation/emul-linux-x86-baselibs-20100220': u'mirror://gentoo/emul-linux-x86-baselibs-20100220.tar.gz',
						u'media-libs/sdl-pango-0.1.2': u'mirror://sourceforge/sdlpango/SDL_Pango-0.1.2.tar.gz http://zarb.org/~gc/t/SDL_Pango-0.1.2-API-adds.patch'
						},
					'output': [
						u'!!! "Deprecation Warning: Installed package: app-emulation/emul-linux-x86-baselibs-20100220\n\tIs no longer in the tree or an installed overlay\n',
						]
					},
			'unrestricted2':{
					'deprecated':{
						u'app-emulation/emul-linux-x86-baselibs-20100220': u'mirror://gentoo/emul-linux-x86-baselibs-20100220.tar.gz'
						},
					'pkgs': {
						u'sys-apps/devicekit-power-014': u'http://hal.freedesktop.org/releases/DeviceKit-power-014.tar.gz',
						u'sys-apps/help2man-1.37.1': u'mirror://gnu/help2man/help2man-1.37.1.tar.gz',
						u'sys-auth/consolekit-0.4.1': u'http://www.freedesktop.org/software/ConsoleKit/dist/ConsoleKit-0.4.1.tar.bz2',
						u'app-emulation/emul-linux-x86-baselibs-20100220': u'mirror://gentoo/emul-linux-x86-baselibs-20100220.tar.gz',
						u'media-libs/sdl-pango-0.1.2': u'mirror://sourceforge/sdlpango/SDL_Pango-0.1.2.tar.gz http://zarb.org/~gc/t/SDL_Pango-0.1.2-API-adds.patch'
						},
					'output': [
						u'!!! "Deprecation Warning: Installed package: app-emulation/emul-linux-x86-baselibs-20100220\n\tIs no longer in the tree or an installed overlay\n',
						'   - Key Error looking up: app-portage/deprecated-pkg-1.0.0'
						]
					}
			}



	def get_props(self, cpvs):
		props = {}
		for cpv in cpvs:
			props[cpv] = PROPS[cpv]
		return props


	def callback(self, id, data):
		self.callback_data.append(data)


	def test__fetch_restricted(self):
		pkgs, deprecated = self.target_class._fetch_restricted(None, CPVS)
		self.results = {
			'fetch_restricted1': {
				'pkgs': pkgs,
				'deprecated': deprecated,
				'output': self.callback_data
				}
			}

		self.callback_data = []
		cpvs = CPVS[:]
		cpvs.append('app-portage/deprecated-pkg-1.0.0')
		pkgs, deprecated = self.target_class._fetch_restricted(None, cpvs)
		self.results['fetch_restricted2'] = {
				'pkgs': pkgs,
				'deprecated': deprecated,
				'output': self.callback_data
				}

		for key in sorted(self.results):
			testdata = self.testdata[key]
			results = self.results[key]
			for item in sorted(testdata):
				self.failUnlessEqual(sorted(testdata[item]), sorted(results[item]),
					"\ntest_fetch_restricted: %s %s data does not match\nresult=" %(key, item) +\
					str(results[item]) + "\ntestdata=" + str(testdata[item]))



	def test_unrestricted(self):
		pkgs, deprecated = self.target_class._unrestricted(None, CPVS)
		self.results = {
			'unrestricted1': {
				'pkgs': pkgs,
				'deprecated': deprecated,
				'output': self.callback_data
				}
			}
		self.callback_data = []
		cpvs = CPVS[:]
		cpvs.append('app-portage/deprecated-pkg-1.0.0')
		pkgs, deprecated = self.target_class._unrestricted(None, cpvs)
		self.results['unrestricted2'] = {
				'pkgs': pkgs,
				'deprecated': deprecated,
				'output': self.callback_data
				}
		for key in sorted(self.results):
			testdata = self.testdata[key]
			results = self.results[key]
			for item in sorted(testdata):
				self.failUnlessEqual( sorted(testdata[item]), sorted(results[item]),
					"\ntest_unrestricted: %s %s data does not match\nresult=" %(key, item) +\
					str(results[item]) + "\ntestdata=" + str(testdata[item]))




def test_main():

	# Run tests
	test_support.run_unittest(TestCheckLimits('test_check_limits'))
	test_support.run_unittest( TestFetchRestricted('test__fetch_restricted'))
	test_support.run_unittest( TestFetchRestricted('test_unrestricted'))


if __name__ == '__main__':
	test_main()
