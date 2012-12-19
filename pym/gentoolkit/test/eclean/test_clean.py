#!/usr/bin/python
#
# Copyright 2010 Brian Dolbec <brian.dolbec@gmail.com>
# Copyright 2010 Gentoo Foundation
# Distributed under the terms of the GNU General Public License v2
#
# $Header$

from __future__ import print_function

__version__= "0.0.1"
__author__ = "Brian Dolbec"
__email__ = "brian.dolbec@gmail.com"

from getopt import gnu_getopt, GetoptError

import unittest
import os
import sys

import gentoolkit.pprinter as pp

from gentoolkit.eclean.clean import CleanUp


class Controllers(object):
	"""Contains controller methods for use in testing
	the clean module methods"""

	def __init__(self):
		self.gathered_data = []
		self.authorize = True
		self.authorize_list = []
		self.authorize_index = 0

	def authorize_all_controller(self, size, key, clean_list):
		"""data gatherering controller.

		@rtype: Boolean
		@returns: self.authorize which controls the cleaning method
		"""
		self.gathered_data.append([size, key, clean_list])
		return self.authorize

	def authorize_list_controller(self, size, key, clean_list):
		"""data gathering and controller which
		authorizes acoring to a pre-determined list

		@rtype: Boolean
		@return self.authorize_list[self.authorize_index]"""
		self.gathered_data.append([size, key, clean_list])
		index = self.authorize_index
		self.authorize_index =+ 1
		return self.authorize_list[index]


#class TestCleanUp(unittest.TestCase):
#	"""Test module for the various CleanUp class methods
#
#	@param options: dict of module options
#	@param testdata: dict. of path and test parameters
#			as created by the TestDirCreation class"""
#
#	def __init__(self, options, testdata):
#		self.options = options
#		self.tesdata = testdata
#
#
#	def test_symlink_clean():
#		"""Tests the symbolic link portion of the distfiles
#		cleaning"""
#		pass
#
#
#	def test_dist_clean():
#		"""Test the distfiles cleaning"""
#		pass
#
#
#	def test_pkg_clean():
#		"""Test the packages cleaning"""
#		pass
#
#
#	def test_pretend_clean():
#		"""Test the pretend_clean output"""
#		controlller = Controllers().authorize_all_controller
#		clean = CleanUp(controller)
#		clean.pretend_clean(self.dist_clean)
#		data = controller.gathered_data



def useage():
	"""output run options"""
	print("Useage: test_clean [OPTONS] path=test-dir")
	print(" where test-dir is the location to create and populate")
	print("the testing distfiles and packages directories.")
	print("All tests in this module test only the clean.py module functions")
	print()
	print("OPTIONS:")
	print(" -a, --all         run all tests")
	print(" -c, --clean       clean up any previous test dirs & files")
	print(" -D, --distfiles   run the distfiles cleaning test")
	print(" -k, --keep-dirs   keep the test directories and files after the test")
	print(" -p, --pretend     run the test in pretend mode only")
	print(" -P, --packages    run the packages cleaning test")
	print(" -S, --symlinks    run the symlinks test")
	print(" --path            the location to create the temporary distfiles")
	print("                   and packages directories that will be test cleaned")
	print(" --version         test module version")
	print()


def parse_opts():
	"""Parse the options dict

	@return options: dictionary of module options"""
	try:
		opts, args = getopt(sys.argv[1:], 'acDkpPS', ["version",
			"help", "path=", "all", "distfiles", "packages",
			"pretend", "symlinks", "keep-dirs", "clean"])
		#print opts
		#print args
	except GetoptError as e:
		print(e.msg, file=sys.stderr)
		usage()
		sys.exit(1)



def main(cmdline=False):
	"""parse options and run the tests"""

	if cmdline:
		options = parse_opts()


if __name__ == "__main__":
	"""actually call main() if launched as a script"""
	try:
		main(True)
	except KeyboardInterrupt:
		print("Aborted.")
		sys.exit(130)
	sys.exit(0)


