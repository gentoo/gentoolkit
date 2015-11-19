#	vim:fileencoding=utf-8
# Copyright 2001-2010 Gentoo Foundation
# Distributed under the terms of the GNU General Public License v2

__all__ = ['keywords_header']

import portage
import os
from portage import settings as ports
from portage.output import colorize
from gentoolkit.eshowkw.display_pretty import colorize_string
from gentoolkit.eshowkw.display_pretty import align_string

# Copied from ekeyword
def load_profile_data(portdir=None, repo='gentoo'):
	"""Load the list of known arches from the tree

	Args:
	  portdir: The repository to load all data from (and ignore |repo|)
	  repo: Look up this repository by name to locate profile data

	Returns:
	  A dict mapping the keyword to its preferred state:
	  {'x86': 'stable', 'mips': 'dev', ...}
	"""
	if portdir is None:
		portdir = portage.db['/']['vartree'].settings.repositories[repo].location

	arch_status = {}

	try:
		arch_list = os.path.join(portdir, 'profiles', 'arch.list')
		with open(arch_list) as f:
			for line in f:
				line = line.split('#', 1)[0].strip()
				if line:
					arch_status[line] = None
	except IOError:
		pass

	try:
		profile_status = {
			'stable': 0,
			'dev': 1,
			'exp': 2,
			None: 3,
		}
		profiles_list = os.path.join(portdir, 'profiles', 'profiles.desc')
		with open(profiles_list) as f:
			for line in f:
				line = line.split('#', 1)[0].split()
				if line:
					arch, _profile, status = line
					arch_status.setdefault(arch, status)
					curr_status = profile_status[arch_status[arch]]
					new_status = profile_status[status]
					if new_status < curr_status:
						arch_status[arch] = status
	except IOError:
		pass

	if arch_status:
		arch_status['all'] = None
	else:
		warning('could not read profile files: %s' % arch_list)
		warning('will not be able to verify args are correct')

	return arch_status

def gen_arch_list(status):
	_arch_status = load_profile_data()
	if status == "stable":
		return [arch for arch in _arch_status if _arch_status[arch] == "stable"]
	elif status == "dev":
		return [arch for arch in _arch_status if _arch_status[arch] == "dev"]
	elif status == "exp":
		return [arch for arch in _arch_status if _arch_status[arch] == "exp"]
	else:
		raise TypeError

class keywords_header:
	__IMPARCHS = gen_arch_list("stable")
	__DEV_ARCHS = gen_arch_list("dev")
	__EXP_ARCHS = gen_arch_list("exp")
	__ADDITIONAL_FIELDS = [ 'eapi', 'unused', 'slot' ]
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
			elif tmp2 in self.__EXP_ARCHS:
				tmp.append(colorize_string('darkgray', keyword))
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
