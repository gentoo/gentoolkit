#!/usr/bin/python
#
# Copyright 2004-2010, Gentoo Foundation
#
# Licensed under the GNU General Public License, v2
#
# $Header$

"""Provides common methods on a package query."""

__all__ = (
	'Query',
)

# =======
# Imports
# =======

from gentoolkit.cpv import CPV
#from gentoolkit.helpers import *

# =======
# Classes
# =======

class Query(CPV):
	"""Provides common methods on a package query."""

	def __init__(self, cpv):
		if isinstance(cpv, CPV):
			self.cpv = cpv
		else:
			self.cpv = CPV(cpv)
		del cpv
