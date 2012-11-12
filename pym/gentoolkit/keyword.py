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
	'compare_strs',
	'reduce_keywords',
	'determine_keyword'
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
		arch, sep, os = keyword.partition('-')
		self.arch = arch
		self.os = os

	def __eq__(self, other):
		if not isinstance(other, self.__class__):
			return False
		return self.keyword == other.keyword

	def __ne__(self, other):
		return not self == other

	def __lt__(self, other):
		if not isinstance(other, self.__class__):
			raise TypeError("other isn't of %s type, is %s" % (
				self.__class__, other.__class__)
			)
		if self.os < other.os:
			return True
		return self.arch < other.arch

	def __le__(self, other):
		return self == other or self < other

	def __gt__(self, other):
		return not self <= other

	def __ge__(self, other):
		return self == other or self > other

	def __str__(self):
		return self.keyword

	def __repr__(self):
		return "<{0.__class__.__name__} {0.keyword!r}>".format(self)

# =========
# Functions
# =========

def compare_strs(kw1, kw2):
	"""Similar to the builtin cmp, but for keyword strings. Usually called
	as: keyword_list.sort(keyword.compare_strs)

	An alternative is to use the Keyword descriptor directly:
	>>> keyword_list = ['~x86', '~amd64', 'x86']
	>>> kwds = sorted(Keyword(x) for x in keyword_list)

	@see: >>> help(cmp)
	"""

	kw1_arch, sep, kw1_os = kw1.partition('-')
	kw2_arch, sep, kw2_os = kw2.partition('-')
	if kw1_arch != kw2_arch:
		if kw1_os != kw2_os:
			return -1 if kw1_os < kw2_os else 1
		return -1 if kw1_arch < kw2_arch else 1
	if kw1_os == kw2_os:
		return 0
	return -1 if kw1_os < kw2_os else 1


def reduce_keywords(keywords):
	"""Reduce a list of keywords to a unique set of stable keywords.

	Example usage:
		>>> kw = reduce_keywords(['~amd64', 'x86', '~x86'])
		>>> isinstance(kw, set)
		True
		>>> sorted(kw)
		['amd64', 'x86']

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
