#!/usr/bin/python
#
# Copyright 2003-2004 Karl Trygve Kalleberg
# Copyright 2003-2009 Gentoo Technologies, Inc.
# Distributed under the terms of the GNU General Public License v2
#
# $Header$

# =======
# Imports 
# =======

import portage
try:
	from threading import Lock
except ImportError:
	# If we don't have thread support, we don't need to worry about
	# locking the global settings object. So we define a "null" Lock.
	class Lock(object):
		def acquire(self):
			pass
		def release(self):
			pass

# =======
# Globals
# =======

PORTDB = portage.db[portage.root]["porttree"].dbapi
VARDB  = portage.db[portage.root]["vartree"].dbapi
VIRTUALS = portage.db[portage.root]["virtuals"]

Config = {
	"verbosityLevel": 3
}

try:
	settingslock = Lock()
	settings = portage.config(clone=portage.settings)
except portage.exception.PermissionDenied, err:
	sys.stderr.write("Permission denied: '%s'\n" % str(err))
	sys.exit(e.errno)
