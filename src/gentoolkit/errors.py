#! /usr/bin/python2
#
# Copyright(c) 2004, Karl Trygve Kalleberg <karltk@gentoo.org>
# Copyright(c) 2004, Gentoo Foundation
#
# Licensed under the GNU General Public License, v2
#
# $Header$

class FatalError:
	def __init__(self, s):
		self._message = s
	def get_message(self):
		return self._message