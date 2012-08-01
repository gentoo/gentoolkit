#!/usr/bin/python
#
# Copyright 2009 Gentoo Foundation
# Distributed under the terms of the GNU General Public License v2
#
# $Header$

"""Provides access to Portage database api
	Note: this file is deprecated, please replace all use
	of these variable with the assigned calls.  That will
	take advantage of them being lazy-loaded.
"""

from __future__ import print_function

print("gentoolkit.dbapi is deprecated.\n",
	"Please migrate to using the assigned calls directly")

import portage

BINDB = portage.db[portage.root]["bintree"].dbapi
PORTDB = portage.db[portage.root]["porttree"].dbapi
VARDB = portage.db[portage.root]["vartree"].dbapi
#virtuals = portage.db[portage.root]["virtuals"]

# vim: set ts=8 sw=4 tw=79:
