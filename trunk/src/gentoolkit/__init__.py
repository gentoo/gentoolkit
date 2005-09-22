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
sys.path.insert(0, "/usr/lib/portage/pym")
import portage
import re
import string
import types
from threading import Lock

settingslock = Lock()
settings = portage.config(clone=portage.settings)
porttree = portage.db[portage.root]["porttree"]
vartree  = portage.db[portage.root]["vartree"]
virtuals = portage.db[portage.root]["virtuals"]

Config = {
	"verbosityLevel": 3
}

from helpers import *
from package import *
