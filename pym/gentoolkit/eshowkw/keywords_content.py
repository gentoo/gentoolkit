#	vim:fileencoding=utf-8
# Copyright 2010 Gentoo Foundation
# Distributed under the terms of the GNU General Public License v2

import portage as port
import os
from portage.output import colorize

__all__ = ['keywords_content']

from gentoolkit.eshowkw.display_pretty import colorize_string
from gentoolkit.eshowkw.display_pretty import align_string

class keywords_content:
	class RedundancyChecker:
		def __listRedundant(self, masks, keywords, ignoreslots, slots):
			"""List all redundant packages."""
			if ignoreslots:
				return self.__listRedundantAll(masks, keywords)
			else:
				return self.__listRedundantSlots(masks, keywords, slots)

		def __listRedundantSlots(self, masks, keywords, slots):
			"""Search for redundant packages walking per keywords for specified slot."""
			output = list()
			zipped = list(zip(masks, keywords, slots))
			for slot in self.__uniq(slots):
				ms = list()
				ks = list()
				for m, k, s in zipped:
					if slot == s:
						ms.append(m)
						ks.append(k)
				output.append(self.__compareSelected(ms, ks))
			# this is required because the list itself is not just one level depth
			return list(''.join(output))

		@staticmethod
		def __uniq(seq):
			"""Remove all duplicate elements from list."""
			seen = {}
			result = []
			for item in seq:
				if item in seen:
					continue
				seen[item] = 1
				result.append(item)
			return result

		@staticmethod
		def __cleanKeyword(keyword):
			"""Remove masked arches and hardmasks from keywords since we don't care about that."""
			return ["%s" % x for x in keyword.split()
				if x != '-*' and not x.startswith('-')]

		def __listRedundantAll(self, masks, keywords):
			"""Search for redundant packages using all versions ignoring its slotting."""
			return list(self.__compareSelected(list(masks), list(keywords)))

		def __compareSelected(self, masks, kws):
			"""
			Rotate over list of keywords and compare each element with others.
			Selectively remove each already compared list from the remaining keywords.
			"""
			result = []
			kws.reverse()
			masks.reverse()
			for i in range(len(kws)):
				kw = kws.pop()
				masks.pop()
				if self.__compareKeywordWithRest(kw, kws, masks):
					result.append('#')
				else:
					result.append('o')
			if len(result) == 0:
				result.append('o')
			return ''.join(result)

		def __compareKeywordWithRest(self, keyword, keywords, masks):
			"""Compare keywords with list of keywords."""
			kw = self.__cleanKeyword(keyword)
			for kwi, mask in zip(keywords, masks):
				kwi = self.__cleanKeyword(kwi)
				if kwi and not mask:
					kw = self.__checkShadow(kw, kwi)
				if not kw:
					return True
			return False

		def __checkShadow(self, old, new):
			"""Check if package version is overshadowed by other package version."""
			tmp = set(new)
			tmp.update("~%s" % x for x in new
				if not x.startswith("~"))
			return list(set(old).difference(tmp))

		def __init__(self, masks, keywords, slots, ignore_slots = False):
			"""Query all relevant data for redundancy package checking"""
			self.redundant = self.__listRedundant(masks, keywords, ignore_slots, slots)

	class VersionChecker:
		def __getVersions(self, packages):
			"""Obtain properly aligned version strings without colors."""
			revlength = max([len(self.__getRevision(x)) for x in packages])
			return  [self.__separateVersion(x, revlength) for x in packages]

		def __getRevision(self, cpv):
			"""Get revision informations for each package for nice further alignment"""
			rev = port.catpkgsplit(cpv)[3]
			return rev if rev != 'r0' else ''

		def __separateVersion(self, cpv, revlength):
			return self.__modifyVersionInfo(cpv, port.versions.cpv_getversion(cpv), revlength)

		def __modifyVersionInfo(self, cpv, pv, revlength):
			"""Prefix and suffix version with string based on whether version is installed or masked and its revision."""
			mask = self.__getMaskStatus(cpv)
			install = self.__getInstallStatus(cpv)

			# calculate suffix length
			currevlen = len(self.__getRevision(cpv))
			suffixlen = revlength - currevlen
			# +1 required for the dash in revision
			if suffixlen != 0 and currevlen == 0:
				suffixlen = suffixlen + 1
			suffix = ''
			for x in range(suffixlen):
				suffix = '%s ' % suffix

			if mask and install:
				pv = '[M][I]%s%s' % (pv, suffix)
			elif mask:
				pv = '[M]%s%s' % (pv, suffix)
			elif install:
				pv = '[I]%s%s' % (pv, suffix)
			else:
				pv = '%s%s' % (pv, suffix)
			return pv

		def __getMaskStatus(self, cpv):
			"""Figure out if package is pmasked."""
			try:
				if "package.mask" in port.getmaskingstatus(cpv, settings=self.mysettings):
					return True
			except:
				# occurs when package is not known by portdb
				# so we consider it unmasked
				pass
			return False


		def __getInstallStatus(self, cpv):
			"""Check if package version we test is installed."""
			return self.vartree.cpv_exists(cpv)

		def __init__(self, packages):
			"""Query all relevant data for version data formatting"""
			self.vartree = port.db[port.root]['vartree'].dbapi
			self.mysettings = port.config(local_config=False)
			self.versions = self.__getVersions(packages)
			self.masks = list(map(lambda x: self.__getMaskStatus(x), packages))

	@staticmethod
	def __packages_sort(package_content):
		"""
		Sort packages queried based on version and slot
		%% pn , repo, slot, keywords
		"""
		from operator import itemgetter

		if len(package_content) > 1:
			ver_map = {}
			for cpv in package_content:
				ver_map[cpv[0]] = '-'.join(port.versions.catpkgsplit(cpv[0])[2:])
			def cmp_cpv(cpv1, cpv2):
				return port.versions.vercmp(ver_map[cpv1[0]], ver_map[cpv2[0]])

			package_content.sort(key=port.util.cmp_sort_key(cmp_cpv))

	def __xmatch(self, pdb, package):
		"""xmatch function that searches for all packages over all repos"""
		try:
			mycp = port.dep_expand(package, mydb=pdb, settings=pdb.settings).cp
		except port.exception.AmbiguousPackageName as Arg:
			msg_err = 'Ambiguous package name "%s".\n' % package
			found = 'Possibilities: %s' % Arg
			raise SystemExit('%s%s' % (msg_err, found))
		except port.exception.InvalidAtom:
			msg_err = 'No such package "%s"' % package
			raise SystemExit(msg_err)

		mysplit = mycp.split('/')
		mypkgs = []
		for oroot in pdb.porttrees:
			try:
				file_list = os.listdir(os.path.join(oroot, mycp))
			except OSError:
				continue
			for x in file_list:
				pf = x[:-7] if x[-7:] == '.ebuild' else []
				if pf:
					ps = port.pkgsplit(pf)
					if not ps or ps[0] != mysplit[1]:
						# we got garbage or ebuild with wrong name in the dir
						continue
					ver_match = port.versions.ver_regexp.match("-".join(ps[1:]))
					if ver_match is None or not ver_match.groups():
						# version is not allowed by portage or unset
						continue
					# obtain related data from metadata and append to the pkg list
					keywords, slot = self.__getMetadata(pdb, mysplit[0]+'/'+pf, oroot)
					mypkgs.append([mysplit[0]+'/'+pf, oroot, slot, keywords])

		self.__packages_sort(mypkgs)
		return mypkgs

	def __checkExist(self, pdb, package):
		"""Check if specified package even exists."""
		matches = self.__xmatch(pdb, package)
		if len(matches) <= 0:
			msg_err = 'No such package "%s"' % package
			raise SystemExit(msg_err)
		return list(zip(*matches))

	@staticmethod
	def __getMetadata(pdb, package, repo):
		"""Obtain all required metadata from portage auxdb"""
		try:
			metadata = pdb.aux_get(package, ['KEYWORDS', 'SLOT'], repo)
		except KeyError:
			# portage prints out more verbose error for us if we were lucky
			raise SystemExit('Failed to obtain metadata')
		return metadata

	def __formatKeywords(self, keywords, keywords_list, usebold = False, toplist = 'archlist'):
		"""Loop over all keywords and replace them with nice visual identifier"""
		# the % is fancy separator, we use it to split keywords for rotation
		# so we wont loose the empty spaces
		return ['% %'.join([self.__prepareKeywordChar(arch, i, version.split(), usebold, toplist)
			for i, arch in enumerate(keywords_list)])
				for version in keywords]

	@staticmethod
	def __prepareKeywordChar(arch, field, keywords, usebold = False, toplist = 'archlist'):
		"""
		Convert specified keywords for package into their visual replacements.
		# possibilities:
		# ~arch -> orange ~
		# -arch -> red -
		# arch -> green +
		# -* -> red *
		"""
		keys = [ '~%s' % arch, '-%s' % arch, '%s' % arch, '-*' ]
		values = [
			colorize('darkyellow', '~'),
			colorize('darkred', '-'),
			colorize('darkgreen', '+'),
			colorize('darkred', '*')
		]
		# check what keyword we have
		# here we cant just append space because it would get stripped later
		char = colorize('darkgray','o')
		for k, v in zip(keys, values):
			if k in keywords:
				char = v
				break
		if toplist == 'archlist' and usebold and (field)%2 == 0 and char != ' ':
			char = colorize('bold', char)
		return char

	@staticmethod
	def __formatVersions(versions, align, length):
		"""Append colors and align keywords properly"""
		# % are used as separators for further split so we wont loose spaces and coloring
		tmp = []
		for pv in versions:
			pv = align_string(pv, align, length)
			pv = '%'.join(list(pv))
			if pv.find('[%M%][%I%]') != -1:
				tmp.append(colorize_string('darkyellow', pv))
			elif pv.find('[%M%]') != -1:
				tmp.append(colorize_string('darkred', pv))
			elif pv.find('[%I%]') != -1:
				tmp.append(colorize_string('bold', pv))
			else:
				tmp.append(pv)
		return tmp

	@staticmethod
	def __formatAdditional(additional, color, length):
		"""Align additional items properly"""
		# % are used as separators for further split so we wont loose spaces and coloring
		tmp = []
		for x in additional:
			tmpc = color
			x = align_string(x, 'left', length)
			x = '%'.join(list(x))
			if x == 'o':
				# the value is unset so the color is gray
				tmpc = 'darkgray'
			x = colorize_string(tmpc, x)
			tmp.append(x)
		return tmp

	@staticmethod
	def __prepareContentResult(versions, keywords, redundant, slots, slot_length, repos, linesep):
		"""Parse version fields into one list with proper separators"""
		content = []
		oldslot = ''
		fieldsep = '% %|% %'
		normsep = '% %'
		for v, k, r, s, t in zip(versions, keywords, redundant, slots, repos):
			if oldslot != s:
				oldslot = s
				content.append(linesep)
			else:
				s = '%'.join(list(''.rjust(slot_length)))
			content.append('%s%s%s%s%s%s%s%s%s' % (v, fieldsep, k, fieldsep, r, normsep, s, fieldsep, t))
		return content

	def __init__(self, package, keywords_list, porttree, ignoreslots = False, content_align = 'bottom', usebold = False, toplist = 'archlist'):
		"""Query all relevant data from portage databases."""
		packages, self.repositories, self.slots, self.keywords = self.__checkExist(porttree, package)
		# convert repositories from path to name
		self.repositories = [porttree.getRepositoryName(x) for x in self.repositories]
		self.slot_length = max([len(x) for x in self.slots])
		repositories_length = max([len(x) for x in self.repositories])
		self.keyword_length = len(keywords_list)
		vers =self.VersionChecker(packages)
		self.versions = vers.versions
		masks = vers.masks
		self.version_length = max([len(x) for x in self.versions])
		self.version_count = len(self.versions)
		self.redundant = self.RedundancyChecker(masks, self.keywords, self.slots, ignoreslots).redundant
		redundant_length = max([len(x) for x in self.redundant])

		ver = self.__formatVersions(self.versions, content_align, self.version_length)
		kws = self.__formatKeywords(self.keywords, keywords_list, usebold, toplist)
		red = self.__formatAdditional(self.redundant, 'purple', redundant_length)
		slt = self.__formatAdditional(self.slots, 'bold', self.slot_length)
		rep = self.__formatAdditional(self.repositories, 'yellow', repositories_length)
		# those + nubers are spaces in printout. keywords are multiplied also because of that
		linesep = '%s+%s+%s+%s' % (''.ljust(self.version_length+1, '-'),
			''.ljust(self.keyword_length*2+1, '-'),
			''.ljust(redundant_length+self.slot_length+3, '-'),
			''.ljust(repositories_length+1, '-')
		)

		self.content = self.__prepareContentResult(ver, kws, red, slt, self.slot_length, rep, linesep)
		self.content_length = len(linesep)
		self.cp = port.cpv_getkey(packages[0])
