#!/usr/bin/python

# Copyright 2003-2010 Gentoo Foundation
# Distributed under the terms of the GNU General Public License v2


#from __future__ import print_function

"""Eprefix support module to set the EPREFIX variable
used in all gentoolkit modules

Example useage:  from gentoolkit.eprefix import EPREFIX
then in code add it to the filepath eg.:
	exclude_file = "%s/etc/%s/%s.exclude" % (EPREFIX,__productname__ , action)

"""
# Load EPREFIX from Portage, fall back to the empty string if it fails
try:
	from portage.const import EPREFIX
except ImportError:
	EPREFIX = ''

if __name__ == "__main__":
	print("EPREFIX set to:", EPREFIX)
