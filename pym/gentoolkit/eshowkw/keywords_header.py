#	vim:fileencoding=utf-8
# Copyright 2001-2010 Gentoo Foundation
# Distributed under the terms of the GNU General Public License v2

__all__ = ['keywords_header']

from portage import settings as ports
from portage.output import colorize
from gentoolkit.eshowkw.display_pretty import colorize_string
from gentoolkit.eshowkw.display_pretty import align_string

class keywords_header:
	__IMPARCHS = [ 'arm', 'amd64', 'x86' ]
	__ADDITIONAL_FIELDS = [ 'unused', 'slot' ]
	__EXTRA_FIELDS = [ 'repo' ]

	@staticmethod
	def __readKeywords():
		"""Read all available keywords from portage."""
		return [x for x in ports.archlist()
			if not x.startswith('~')]

	@staticmethod
	def __sortKeywords(keywords, prefix = False, required_keywords = []):
		"""Sort keywords with short archs first"""
		# user specified only some keywords to display
		if len(required_keywords) != 0:
			tmpkeywords = [k for k in keywords
				if k in required_keywords]
			# idiots might specify non-existant archs
			if len(tmpkeywords) != 0:
				keywords = tmpkeywords

		normal = [k for k in keywords
			if len(k.split('-')) == 1]
		normal.sort()

		if prefix:
			longer = [k for k in keywords
				if len(k.split('-')) != 1]
			longer.sort()
			normal.extend(longer)
		return normal

	def __readAdditionalFields(self):
		"""Prepare list of aditional fileds displayed by eshowkw (2nd part)"""
		return self.__ADDITIONAL_FIELDS

	def __readExtraFields(self):
		"""Prepare list of extra fileds displayed by eshowkw (3rd part)"""
		return self.__EXTRA_FIELDS

	def __formatKeywords(self, keywords, align, length):
		"""Append colors and align keywords properly"""
		tmp = []
		for keyword in keywords:
			tmp2 = keyword
			keyword = align_string(keyword, align, length)
			# % are used as separators for further split so we wont loose spaces and coloring
			keyword = '%'.join(list(keyword))
			if tmp2 in self.__IMPARCHS:
				tmp.append(colorize_string('darkyellow', keyword))
			else:
				tmp.append(keyword)
		return tmp

	@staticmethod
	def __formatAdditional(additional, align, length):
		"""Align additional items properly"""
		# % are used as separators for further split so we wont loose spaces and coloring
		return ['%'.join(align_string(x, align, length)) for x in additional]

	def __prepareExtra(self, extra, align, length):
		content = []
		content.append(''.ljust(length, '-'))
		content.extend(self.__formatAdditional(extra, align, length))
		return content

	def __prepareResult(self, keywords, additional, align, length):
		"""Parse keywords and additional fields into one list with proper separators"""
		content = []
		content.append(''.ljust(length, '-'))
		content.extend(self.__formatKeywords(keywords, align, length))
		content.append(''.ljust(length, '-'))
		content.extend(self.__formatAdditional(additional, align, length))
		return content

	def __init__(self, prefix = False, required_keywords = [], keywords_align = 'bottom'):
		"""Initialize keywords header."""
		additional = self.__readAdditionalFields()
		extra = self.__readExtraFields()
		self.keywords = self.__sortKeywords(self.__readKeywords(), prefix, required_keywords)
		self.length = max(
			max([len(x) for x in self.keywords]),
			max([len(x) for x in additional]),
			max([len(x) for x in extra])
		)
		#len(max([max(self.keywords, key=len), max(additional, key=len)], key=len))
		self.keywords_count = len(self.keywords)
		self.additional_count = len(additional)
		self.extra_count = len(extra)
		self.content = self.__prepareResult(self.keywords, additional, keywords_align, self.length)
		self.extra = self.__prepareExtra(extra, keywords_align, self.length)
