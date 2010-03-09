#!/usr/bin/python
# Copyright 2009 Gentoo Foundation
#
# Distributed under the terms of the GNU General Public License v2
#
# $Header$

__all__ = ['cmp']

# py3k doesn't have cmp emulate it in order to keep testing cmp
# in python-2.x
#XXX: not sure if this is the best place for this
try:
	cmp = cmp
except NameError:
	def cmp(a, b):
		if a == b:
			return 0
		elif a < b:
			return -1
		elif a > b:
			return 1
		# just to be safe, __lt__/ __gt__ above should have thrown
		# something like this already
		raise TypeError("Comparison between onorderable types")
