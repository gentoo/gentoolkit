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

import os


EPREFIX = ''

# the following code is used to set it when
# non-installed code is being run
if 'EPREFIX' in os.environ:
	EPREFIX = os.environ['EPREFIX']
else:
	try:
		import portage.const
		EPREFIX = portage.BPREFIX
	except AttributeError:
		EPREFIX = ''

#print("EPREFIX set to:", EPREFIX)
