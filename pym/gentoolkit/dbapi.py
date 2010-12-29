#!/usr/bin/python
#
# Copyright 2009 Gentoo Foundation
# Distributed under the terms of the GNU General Public License v2
#
# $Header$

"""Provides access to Portage database api"""

import portage

BINDB = portage.db[portage.root]["bintree"].dbapi
PORTDB = portage.db[portage.root]["porttree"].dbapi
VARDB = portage.db[portage.root]["vartree"].dbapi
#virtuals = portage.db[portage.root]["virtuals"]

# vim: set ts=8 sw=4 tw=79:
