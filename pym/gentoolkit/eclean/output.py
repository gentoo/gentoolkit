#!/usr/bin/python

# Copyright 2003-2010 Gentoo Foundation
# Distributed under the terms of the GNU General Public License v2


from __future__ import print_function


import sys
import portage
from portage.output import *
from gentoolkit.pprinter import cpv, number, emph


class OutputControl(object):
	"""Outputs data according to predetermined options and handles any user
	interaction.

	@param options: dictionary of boolean options as determined in cli.py
			used here: interactive, pretend, quiet, accept_all, nocolor.
	"""

	def __init__(self, options):
		if not options:
			# set some defaults
			self.options['interactive'] = False
			self.options['pretend'] = True
			self.options['quiet'] = False
			self.options['accept_all'] = False
			self.options['nocolor'] = False
		else:
			self.options = options
		self.set_colors("normal")

	def set_colors(self, mode):
		"""Sets the colors for the progress_controller
		and prettysize output

		@param mode: string, 1 of ["normal", "deprecated"]
		"""
		if mode == "normal":
			self.pkg_color = cpv        # green
			self.numbers = number  # turquoise
			self.brace = blue
		elif mode == "deprecated":
			self.pkg_color = yellow
			self.numbers =  teal # darkgreen
			self.brace = blue

	def einfo(self, message=""):
		"""Display an info message depending on a color mode.

		@param message: text string to display

		@outputs to stdout.
		"""
		if not  self.options['nocolor']:
			prefix = " "+green('*')
		else:
			prefix = ">>>"
		print(prefix,message)

	def eprompt(self, message):
		"""Display a user question depending on a color mode.

		@param message: text string to display

		@output to stdout
		"""
		if not self.options['nocolor']:
			prefix = " "+red('>')+" "
		else:
			prefix = "??? "
		sys.stdout.write(prefix+message)
		sys.stdout.flush()

	def prettySize(self, size, justify=False, color=None):
		"""int -> byte/kilo/mega/giga converter. Optionally
		justify the result. Output is a string.

		@param size: integer
		@param justify: optional boolean, defaults to False
		@param color: optional color, defaults to green
				as defined in portage.output

		@returns a formatted and (escape sequenced)
				colorized text string
		"""
		if color == None:
			color = self.numbers
		units = [" G"," M"," K"," B"]
		approx = 0
		# by using 1000 as the changeover, the integer portion
		# of the number will never be more than 3 digits long
		# but the true base 2 value of 1024 is used for the actual
		# calulation to maintain better accuracy.
		while len(units) and size >= 1000:
			approx = 1
			size = size / 1024.0
			units.pop()
		sizestr = "%.1f" %(round(size,1)) + units[-1]
		if justify:
			sizestr = " " + self.brace("[ ")  + \
				color(sizestr.rjust(8)) + self.brace(" ]")
		return sizestr

	def yesNoAllPrompt(self, message="Do you want to proceed?"):
		"""Print a prompt until user answer in yes/no/all. Return a
		boolean for answer, and also may affect the 'accept_all' option.

		@param message: optional different input string from the default
				message of: "Do you want to proceed?"
		@outputs to stdout
		@modifies class var options['accept_all']
		@rtype: bool
		"""
		user_string="xxx"
		while not user_string.lower() in ["","y","n","a","yes","no","all"]:
			self.eprompt(message+" [Y/n/a]: ")
			user_string =  sys.stdin.readline().rstrip('\n')
			user_string = user_string.strip()
		if user_string.lower() in ["a","all"]:
			self.options['accept_all'] = True
		answer = user_string.lower() in ["","y","a","yes","all"]
		return answer

	def progress_controller(self, size, key, clean_list, file_type):
		"""Callback function for doCleanup. It outputs data according to the
		options configured.
		Alternatively it handles user interaction for decisions that are
		required.

		@param size: Integer of the file(s) size
		@param key: the filename/pkgname currently being processed
		@param clean_list: list of files being processed.
		"""
		if not self.options['quiet']:
			# pretty print mode
			print(self.prettySize(size,True), self.pkg_color(key))
		elif self.options['pretend'] or self.options['interactive']:
			# file list mode
			for file_ in clean_list:
				print(file_)
		if self.options['pretend']:
			return False
		elif not self.options['interactive'] \
			or self.options['accept_all'] \
			or self.yesNoAllPrompt("Do you want to delete this " + file_type + "?"):
			return True
		return False

	def total(self, mode, size, num_files, verb, action):
		"""outputs the formatted totals to stdout

		@param mode: sets color and message. 1 of ['normal', 'deprecated']
		@param size: total space savings
		@param num_files: total number of files
		@param verb: string eg. 1 of ["would be", "has been"]
		@param action: string eg 1 of ['distfiles', 'packages']
		"""
		self.set_colors(mode)
		if mode =="normal":
			message="Total space from "+red(str(num_files))+" files "+\
				verb+" freed in the " + action + " directory"
			print( " ===========")
			print( self.prettySize(size, True, red), message)
		elif mode == "deprecated":
			message = "Total space from "+red(str(num_files))+" package files\n"+\
				"   Re-run the last command with the -D " +\
				"option to clean them as well"
			print( " ===========")
			print( self.prettySize(size, True, red), message)

	def list_pkgs(self, pkgs):
		"""outputs the packages to stdout

		@param pkgs: dict. of {cat/pkg-ver: src_uri,}
		"""
		indent = ' ' * 12
		keys = sorted(pkgs)
		for key in keys:
			if pkgs[key]:
				saved = ""
			else:
				saved = " ...distfile name(s) not known/saved"
			print( indent,self.pkg_color(key) + saved)
		print()
