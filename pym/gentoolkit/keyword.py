#!/usr/bin/python
#
# Copyright(c) 2004-2010, Gentoo Foundation
#
# Licensed under the GNU General Public License, v2
#
# $Header$

"""Provides common methods on Gentoo GLEP 53 keywords.

http://www.gentoo.org/proj/en/glep/glep-0053.html
"""

__all__ = (
	'Keyword',
	'compare_strs'
)

# =======
# Imports
# =======


# =======
# Classes
# =======

class Keyword(object):
	"""Provides common methods on a GLEP 53 keyword."""

	def __init__(self, keyword):
		self.keyword = keyword

	def __str__(self):
		return self.keyword

	def __repr__(self):
		return "<Keyword {0.keyword!r}>".format(self)

# =========
# Functions
# =========

def compare_strs(kw1, kw2):
	"""Similar to the builtin cmp, but for keyword strings. Usually called
	as: keyword_list.sort(keyword.compare_strs)

	An alternative is to use the Keyword descriptor directly:
	>>> kwds = sorted(Keyword(x) for x in keyword_list)

	@see: >>> help(cmp)
	"""

	pass


def reduce_keywords(keywords):
	"""Reduce a list of keywords to a unique set of stable keywords.

	Example usage:
		>>> reduce_keywords(['~amd64', 'x86', '~x86'])
		set(['amd64', 'x86'])

	@type keywords: array
	@rtype: set
	"""
	return set(x.lstrip('~') for x in keywords)


abs_keywords = reduce_keywords


# FIXME: this is unclear
# dj, how about 'deduce_keyword'
# I was trying to avoid a 2nd use of determine_keyword name (in analyse.lib)
# but that one is a little different and not suitable for this task.
def determine_keyword(arch, accepted, keywords):
	"""Determine a keyword from matching a dep's KEYWORDS
	list against the ARCH & ACCEPT_KEYWORDS provided.

	@type arch: string
	@param arch: portage.settings["ARCH"]
	@type accepted: string
	@param accepted: portage.settings["ACCEPT_KEYWORDS"]
	@type keywords: string
	@param keywords: the pkg ebuilds keywords
	"""
	if not keywords:
		return ''
	keys = keywords.split()
	if arch in keys:
		return arch
	keyworded = "~" + arch
	if keyworded in keys:
		return keyworded
	match = list(set(accepted.split(" ")).intersection(keys))
	if len(match) > 1:
		if arch in match:
			return arch
		if keyworded in match:
			return keyworded
		return 'unknown'
	if match:
		return match[0]
	return 'unknown'
