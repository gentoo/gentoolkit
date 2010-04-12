#!/usr/bin/python
#
# Copyright 2003-2004 Karl Trygve Kalleberg
# Copyright 2003-2004 Gentoo Technologies, Inc.
# Distributed under the terms of the GNU General Public License v2
#
# $Header$
# Author: Karl Trygve Kalleberg <karltk@gentoo.org>
#
# Portions written ripped from 
# - etcat, by Alistair Tse <liquidx@gentoo.org>
#

__author__ = "Karl Trygve Kalleberg"
__email__ = "karltk@gentoo.org"
__version__ = "0.1.1"
__productname__ = "gentoolkit"
__description__ = "Gentoolkit Common Library"

import os
import sys
try:
	import portage
except ImportError:
	sys.path.insert(0, "/usr/lib/portage/pym")
	import portage
import re
try:
	from threading import Lock
except ImportError:
	# If we don't have thread support, we don't need to worry about
	# locking the global settings object. So we define a "null" Lock.
	class Lock:
		def acquire(self):
			pass
		def release(self):
			pass

try:
	import portage.exception as portage_exception
except ImportError:
	import portage_exception

try:
	settingslock = Lock()
	settings = portage.config(clone=portage.settings)
	porttree = portage.db[portage.root]["porttree"]
	vartree  = portage.db[portage.root]["vartree"]
except portage_exception.PermissionDenied, e:
	sys.stderr.write("Permission denied: '%s'\n" % str(e))
	sys.exit(e.errno)

Config = {
	"verbosityLevel": 3
}

from helpers import *
from package import *
