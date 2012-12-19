#!/usr/bin/python

# Copyright 2003-2010 Gentoo Foundation
# Distributed under the terms of the GNU General Public License v2


from __future__ import print_function


import os
import sys
import re
import portage

from gentoolkit.pprinter import warn

# Misc. shortcuts to some portage stuff:
listdir = portage.listdir

FILENAME_RE = [re.compile(r'(?P<pkgname>[-a-zA-z0-9\+]+)(?P<ver>-\d+\S+)'),
	re.compile(r'(?P<pkgname>[-a-zA-z]+)(?P<ver>_\d+\S+)'),
	re.compile(r'(?P<pkgname>[-a-zA-z_]+)(?P<ver>\d\d+\S+)'),
	re.compile(r'(?P<pkgname>[-a-zA-z0-9_]+)(?P<ver>-default\S+)'),
	re.compile(r'(?P<pkgname>[-a-zA-z0-9]+)(?P<ver>_\d\S+)'),
	re.compile(r'(?P<pkgname>[-a-zA-z0-9\+\.]+)(?P<ver>-\d+\S+)'),
	re.compile(r'(?P<pkgname>[-a-zA-z0-9\+\.]+)(?P<ver>.\d+\S+)')]

debug_modules = []

def dprint(module, message):
	if module in debug_modules:
		print(message)

def isValidCP(cp):
	"""Check whether a string is a valid cat/pkg-name.

	This is for 2.0.51 vs. CVS HEAD compatibility, I've not found any function
	for that which would exists in both. Weird...

	@param cp: catageory/package string
	@rtype: bool
	"""

	if not '/' in cp:
		return False
	try:
		portage.cpv_getkey(cp+"-0")
	except:
		return False
	else:
		return True


class ParseExcludeFileException(Exception):
	"""For parseExcludeFile() -> main() communication.

	@param value: Error message string
	"""
	def __init__(self, value):
		self.value = value
	def __str__(self):
		return repr(self.value)


def parseExcludeFile(filepath, output):
	"""Parses an exclusion file.

	@param filepath: file containing the list of cat/pkg's to exclude
	@param output: --verbose enabled output method or "lambda x: None"

	@rtype: dict
	@return: an exclusion dict
	@raise ParseExcludeFileException: in case of fatal error
	"""

	exclude = {
			'categories': {},
			'packages': {},
			'anti-packages': {},
			'filenames': {}
		}
	output("Parsing Exclude file: " + filepath)
	try:
		file_ = open(filepath,"r")
	except IOError:
		raise ParseExcludeFileException("Could not open exclusion file: " +
			filepath)
	filecontents = file_.readlines()
	file_.close()
	cat_re = re.compile('^(?P<cat>[a-zA-Z0-9]+-[a-zA-Z0-9]+)(/\*)?$')
	cp_re = re.compile('^(?P<cp>[-a-zA-Z0-9_]+/[-a-zA-Z0-9_]+)$')
	# used to output the line number for exception error reporting
	linenum = 0
	for line in filecontents:
		# need to increment it here due to continue statements.
		linenum += 1
		line = line.strip()
		if not len(line): # skip blank a line
			continue
		if line[0] == '#': # skip a comment line
			continue
		#print( "parseExcludeFile: line=", line)
		try: # category matching
			cat = cat_re.match(line).group('cat')
			#print( "parseExcludeFile: found cat=", cat)
		except:
			pass
		else:
			if not cat in portage.settings.categories:
				raise ParseExcludeFileException("Invalid category: "+cat +
					" @line # " + str(linenum))
			exclude['categories'][cat] = None
			continue
		dict_key = 'packages'
		if line[0] == '!': # reverses category setting
			dict_key = 'anti-packages'
			line = line[1:]
		try: # cat/pkg matching
			cp = cp_re.match(line).group('cp')
			#print( "parseExcludeFile: found cp=", cp)
			if isValidCP(cp):
				exclude[dict_key][cp] = None
				continue
			else:
				raise ParseExcludeFileException("Invalid cat/pkg: "+cp +
					" @line # " + str(linenum))
		except:
			pass
		#raise ParseExcludeFileException("Invalid line: "+line)
		try: # filename matching.
			exclude['filenames'][line] = re.compile(line)
			#print( "parseExcludeFile: found filenames", line)
		except:
			try:
				exclude['filenames'][line] = re.compile(re.escape(line))
				#print( "parseExcludeFile: found escaped filenames", line)
			except:
				raise ParseExcludeFileException("Invalid file name/regular " +
					"expression: @line # " + str(linenum) + " line=" +line)
	output("Exclude file parsed. Found " +
		"%d categories, %d packages, %d anti-packages %d filenames"
		%(len(exclude['categories']), len(exclude['packages']),
		len(exclude['anti-packages']), len(exclude['filenames'])))
	#print()
	#print( "parseExcludeFile: final exclude_dict = ", exclude)
	#print()
	return exclude

def cp_all(categories, portdb=portage.portdb ):
		"""temp function until the new portdb.cp_all([cat,...])
		behaviour is fully available.

		@param categories: list of categories to get all packages for
				eg. ['app-portage', 'sys-apps',...]
		@rtype: list of cat/pkg's  ['foo/bar', 'foo/baz']
		"""
		try:
			cps = portdb.cp_all(categories)
			# NOTE: the following backup code should be removed
			# when all available versions of portage have the
			# categories parameter in cp_all()
		except:  # new behaviour not available
			#~ message =  "Exception: eclean.exclude.cp_all() " +\
				#~ "new portdb.cp_all() behavior not found. using fallback code"
			#~ print( warn(message), file=sys.stderr)
			cps = []
			# XXX: i smell an access to something which is really out of API...
			_pkg_dir_name_re = re.compile(r'^\w[-+\w]*$')
			for tree in portdb.porttrees:
				for cat in categories:
					for pkg in listdir(os.path.join(tree,cat),
								EmptyOnError=1, ignorecvs=1, dirsonly=1):
						if not _pkg_dir_name_re.match(pkg) or pkg == "CVS":
							continue
						cps.append(cat+'/'+pkg)
		#print( "cp_all: new cps list=", cps)
		return cps

def exclDictExpand(exclude):
	"""Returns a dictionary of all CP/CPV from porttree which match
	the exclusion dictionary.
	"""
	d = {}
	if 'categories' in exclude:
		# replace the following cp_all call with
		# portage.portdb.cp_all([cat1, cat2])
		# when it is available in all portage versions.
		cps = cp_all(exclude['categories'])
		for cp in cps:
			d[cp] = None
	if 'packages' in exclude:
		for cp in exclude['packages']:
			d[cp] = None
	if 'anti-packages' in exclude:
		for cp in exclude['anti-packages']:
			if cp in d:
				del d[cp]
	return d

def exclDictMatchCP(exclude,pkg):
	"""Checks whether a CP matches the exclusion rules."""
	if pkg is None:
		return False
	if 'anti-packages' in exclude and pkg in exclude['anti-packages']:
		return False
	if 'packages' in exclude and pkg in exclude['packages']:
		return True
	try:
		cat = pkg.split('/')[0]
	except:
		dprint( "exclude", "exclDictMatchCP: Invalid package name: " +\
			"%s, Could not determine category" %pkg)
		cat = ''
	if 'categories' in exclude and cat in exclude['categories']:
			return True
	return False

def exclDictExpandPkgname(exclude):
	"""Returns a set of all pkgnames  from porttree which match
	the exclusion dictionary.
	"""
	p = set()
	if 'categories' in exclude:
		# replace the following cp_all call with
		# portage.portdb.cp_all([cat1, cat2])
		# when it is available in all portage versions.
		cps = cp_all(exclude['categories'])
		for cp in cps:
			pkgname = cp.split('/')[1]
			p.add(pkgname)
	if 'packages' in exclude:
		for cp in exclude['packages']:
			pkgname = cp.split('/')[1]
			p.add(pkgname)
	if 'anti-packages' in exclude:
		for cp in exclude['anti-packages']:
			if cp in p:
				p.remove(cp)
	return p


def exclMatchFilename(exclude_names, filename):
	"""Attempts to split the package name out of a filename
	and then checks if it matches any exclusion rules.

	This is intended to be run on the cleaning list after all
	normal checks and removal of protected files.  This will reduce
	the number of files to perform this last minute check on

	@param exclude_names: a set of pkgnames to exlcude
	@param filename:

	@rtype: bool
	"""
	found = False
	index = 0
	while not found and index < len(FILENAME_RE):
		found = FILENAME_RE[index].match(filename)
		index += 1
	if not found:
		dprint( "exclude", "exclMatchFilename: filename: " +\
			"%s, Could not determine package name" %filename)
		return False
	pkgname = found.group('pkgname')
	dprint("exclude", "exclMatchFilename: found pkgname = " +
		"%s, %s, %d, %s" %(pkgname, str(pkgname in exclude_names),
		index-1, filename))
	return (pkgname in exclude_names)

