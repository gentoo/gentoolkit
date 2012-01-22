#!/usr/bin/python

# Copyright 2003-2010 Gentoo Foundation
# Distributed under the terms of the GNU General Public License v2


from __future__ import print_function


import os
import sys

import gentoolkit.pprinter as pp
from gentoolkit.eclean.pkgindex import PkgIndex


class CleanUp(object):
	"""Performs all cleaning actions to distfiles or package directories.

	@param controller: a progress output/user interaction controller function
					   which returns a Boolean to control file deletion
					   or bypassing/ignoring
	"""

	def __init__(self, controller):
		self.controller = controller

	def clean_dist(self, clean_dict):
		"""Calculate size of each entry for display, prompt user if needed,
		delete files if approved and return the total size of files that
		have been deleted.

		@param clean_dict: dictionary of {'display name':[list of files]}

		@rtype: int
		@return: total size that was cleaned
		"""
		file_type = 'file'
		clean_keys = self._sort_keys(clean_dict)
		clean_size = 0
		# clean all entries one by one
		for key in clean_keys:
			clean_size += self._clean_files(clean_dict[key], key, file_type)
		# return total size of deleted or to delete files
		return clean_size

	def clean_pkgs(self, clean_dict, pkgdir):
		"""Calculate size of each entry for display, prompt user if needed,
		delete files if approved and return the total size of files that
		have been deleted.

		@param clean_dict:  dictionary of  {'display name':[list of files]}
		@param metadata: package index of type portage.getbinpkg.PackageIndex()
		@param pkgdir: path to the package directory to be cleaned

		@rtype: int
		@return: total size that was cleaned
		"""
		file_type = 'binary package'
		clean_keys = self._sort_keys(clean_dict)
		clean_size = 0
		# clean all entries one by one
		for key in clean_keys:
			clean_size += self._clean_files(clean_dict[key], key, file_type)

		#  run 'emaint --fix' here
		if clean_size:
			index_control = PkgIndex(self.controller)
			# emaint is not yet importable so call it
			# print a blank line here for separation
			print()
			clean_size += index_control.call_emaint()
		# return total size of deleted or to delete files
		return clean_size


	def pretend_clean(self, clean_dict):
		"""Shortcut function that calculates total space savings
		for the files in clean_dict.

		@param clean_dict: dictionary of {'display name':[list of files]}
		@rtype: integer
		@return: total size that would be cleaned
		"""
		file_type = 'file'
		clean_keys = self._sort_keys(clean_dict)
		clean_size = 0
		# tally all entries one by one
		for key in clean_keys:
			key_size = self._get_size(clean_dict[key])
			self.controller(key_size, key, clean_dict[key], file_type)
			clean_size += key_size
		return clean_size

	def _get_size(self, key):
		"""Determine the total size for an entry (may be several files)."""
		key_size = 0
		for file_ in key:
			#print file_
			# get total size for an entry (may be several files, and
			# links don't count
			# ...get its statinfo
			try:
				statinfo = os.stat(file_)
				if statinfo.st_nlink == 1:
					key_size += statinfo.st_size
			except EnvironmentError as er:
				print( pp.error(
					"Could not get stat info for:" + file_), file=sys.stderr)
				print( pp.error("Error: %s" %str(er)), file=sys.stderr)
		return key_size

	def _sort_keys(self, clean_dict):
		"""Returns a list of sorted dictionary keys."""
		# sorting helps reading
		clean_keys = sorted(clean_dict)
		return clean_keys

	def _clean_files(self, files, key, file_type):
		"""File removal function."""
		clean_size = 0
		for file_ in files:
			#print file_, type(file_)
			# ...get its statinfo
			try:
				statinfo = os.stat(file_)
			except EnvironmentError as er:
				if not os.path.exists(os.readlink(file_)):
					try:
						os.remove(file_)
						print( pp.error(
							"Removed broken symbolic link " + file_), file=sys.stderr)
						break
					except EnvironmentError as er:
						print( pp.error(
							"Error deleting broken symbolic link " + file_), file=sys.stderr)
						print( pp.error("Error: %s" %str(er)), file=sys.stderr)
						break
				else:
					print( pp.error(
						"Could not get stat info for:" + file_), file=sys.stderr)
					print( pp.error(
						"Error: %s" %str(er)), file=sys.stderr)
			if self.controller(statinfo.st_size, key, file_, file_type):
				# ... try to delete it.
				try:
					os.unlink(file_)
					# only count size if successfully deleted and not a link
					if statinfo.st_nlink == 1:
						clean_size += statinfo.st_size
				except EnvironmentError as er:
					print( pp.error("Could not delete "+file_), file=sys.stderr)
					print( pp.error("Error: %s" %str(er)), file=sys.stderr)
		return clean_size







