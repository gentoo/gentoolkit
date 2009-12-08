#!/usr/bin/python
#
# Copyright(c) 2009, Gentoo Foundation
#
# Licensed under the GNU General Public License, v2
#
# $Header$

"""Provides an easy-to-use python interface to Gentoo's metadata.xml file.

	Example usage:
		>>> from gentoolkit.metadata import MetaData
		>>> pkg_md = MetaData('/usr/portage/app-misc/gourmet/metadata.xml')
		>>> pkg_md
		<MetaData '/usr/portage/app-misc/gourmet/metadata.xml'>
		>>> pkg_md.get_herds()
		['no-herd']
		>>> for maint in pkg_md.get_maintainers():
		...     print "{0} ({1})".format(maint.email, maint.name)
		...
		nixphoeni@gentoo.org (Joe Sapp)
		>>> for flag in pkg_md.get_useflags():
		...     print flag.name, "->", flag.description
		...
		rtf -> Enable export to RTF
		gnome-print -> Enable printing support using gnome-print
		>>> upstream = pkg_md.get_upstream()
		>>> upstream
		[<_Upstream {'docs': [], 'remoteid': [], 'maintainer':
		 [<_Maintainer 'Thomas_Hinkle@alumni.brown.edu'>], 'bugtracker': [],
		 'changelog': []}>]
		>>> upstream[0].maintainer[0].name
		'Thomas Mills Hinkle'
"""

# Move to Imports section after Python-2.6 is stable
from __future__ import with_statement

__all__ = ('MetaData',)
__docformat__ = 'epytext'

# =======
# Imports
# =======

import re
import os
import xml.etree.cElementTree as etree

from portage import settings

# =======
# Classes
# =======

class _Maintainer(object):
	"""An object for representing one maintainer.

	@type email: str or None
	@ivar email: Maintainer's email address. Used for both Gentoo and upstream.
	@type name: str or None
	@ivar name: Maintainer's name. Used for both Gentoo and upstream.
	@type description: str or None
	@ivar description: Description of what a maintainer does. Gentoo only.
	@type restrict: str or None
	@ivar restrict: e.g. &gt;=portage-2.2 means only maintains versions
		of Portage greater than 2.2.
	@type status: str or None
	@ivar status: If set, either 'active' or 'inactive'. Upstream only.
	"""

	def __init__(self, node):
		self.email = None
		self.name = None
		self.description = None
		self.restrict = node.get('restrict')
		self.status = node.get('status')
		maint_attrs = node.getchildren()
		for attr in maint_attrs:
			setattr(self, attr.tag, attr.text)

	def __repr__(self):
		return "<%s %r>" % (self.__class__.__name__, self.email)


class _Useflag(object):
	"""An object for representing one USE flag.

	@todo: Is there any way to have a keyword option to leave in
		<pkg> and <cat> for later processing?
	@type name: str or None
	@ivar name: USE flag
	@type restrict: str or None
	@ivar restrict: e.g. &gt;=portage-2.2 means flag is only avaiable in
		versions greater than 2.2
	@type description: str
	@ivar description: description of the USE flag
	"""

	def __init__(self, node):
		self.name = node.get('name')
		self.restrict = node.get('restrict')
		_desc = ''
		if node.text:
			_desc = node.text
		for child in node.getchildren():
			_desc += child.text if child.text else ''
			_desc += child.tail if child.tail else ''
		# This takes care of tabs and newlines left from the file
		self.description = re.sub('\s+', ' ', _desc)

	def __repr__(self):
		return "<%s %r>" % (self.__class__.__name__, self.name)


class _Upstream(object):
	"""An object for representing one package's upstream.

	@type maintainers: list
	@ivar maintainers: L{_Maintainer} objects for each upstream maintainer
	@type changelogs: list
	@ivar changelogs: URLs to upstream's ChangeLog file in str format
	@type docs: list
	@ivar docs: Sequence of tuples containing URLs to upstream documentation
		in the first slot and 'lang' attribute in the second, e.g.,
		[('http.../docs/en/tut.html', None), ('http.../doc/fr/tut.html', 'fr')]
	@type bugtrackers: list
	@ivar bugtrackers: URLs to upstream's bugtracker. May also contain an email
		address if prepended with 'mailto:'
	@type remoteids: list
	@ivar remoteids: Sequence of tuples containing the project's hosting site
		name in the first slot and the project's ID name or number for that
		site in the second, e.g., [('sourceforge', 'systemrescuecd')]
	"""

	def __init__(self, node):
		self.node = node
		self.maintainers = self.get_upstream_maintainers()
		self.changelogs = self.get_upstream_changelogs()
		self.docs = self.get_upstream_documentation()
		self.bugtrackers = self.get_upstream_bugtrackers()
		self.remoteids = self.get_upstream_remoteids()

	def __repr__(self):
		return "<%s %r>" % (self.__class__.__name__, self.__dict__)

	def get_upstream_bugtrackers(self):
		"""Retrieve upstream bugtracker location from xml node."""
		return [e.text for e in self.node.findall('bugs-to')]

	def get_upstream_changelogs(self):
		"""Retrieve upstream changelog location from xml node."""
		return [e.text for e in self.node.findall('changelog')]

	def get_upstream_documentation(self):
		"""Retrieve upstream documentation location from xml node."""
		result = []
		for elem in self.node.findall('doc'):
			lang = elem.get('lang')
			result.append((elem.text, lang))
		return result

	def get_upstream_maintainers(self):
		"""Retrieve upstream maintainer information from xml node."""
		return [_Maintainer(m) for m in self.node.findall('maintainer')]

	def get_upstream_remoteids(self):
		"""Retrieve upstream remote ID from xml node."""
		return [(e.text, e.get('type')) for e in self.node.findall('remote-id')]


class MetaData(object):
	"""Access metadata.xml"""

	def __init__(self, metadata_path):
		"""Parse a valid metadata.xml file.

		@type metadata_path: str
		@ivar metadata_path: path to a valid metadata.xml file
		@raise IOError: if C{matadata_path} can not be read
		"""

		self.metadata_path = metadata_path
		self._xml_tree = etree.parse(metadata_path)

		# Used for caching
		self._herdstree = None
		self._descriptions = None
		self._maintainers = None
		self._useflags = None
		self._upstream = None

	def __repr__(self):
		return "<%s %r>" % (self.__class__.__name__, self.metadata_path)

	def _get_herd_email(self, herd):
		"""Get a herd's email address.

		@type herd: str
		@param herd: herd whose email you want
		@rtype: str or None
		@return: email address or None if herd is not in herds.xml
		@raise IOError: if $PORTDIR/metadata/herds.xml can not be read
		"""

		if self._herdstree is None:
			herds_path = os.path.join(settings['PORTDIR'], 'metadata/herds.xml')
			self._herdstree = etree.parse(herds_path)

		# Some special herds are not listed in herds.xml
		if herd in ('no-herd', 'maintainer-wanted', 'maintainer-needed'):
			return None

		for node in self._herdstree.getiterator('herd'):
			if node.findtext('name') == herd:
				return node.findtext('email')

	def get_herds(self, include_email=False):
		"""Return a list of text nodes for <herd>.

		@type include_email: bool
		@keyword include_email: if True, also look up the herd's email
		@rtype: list
		@return: if include_email is False, return a list of string;
		         if include_email is True, return a list of tuples containing:
					 [('herd1', 'herd1@gentoo.org'), ('no-herd', None);
		"""

		result = []
		for elem in self._xml_tree.findall('herd'):
			if include_email:
				herd_mail = self._get_herd_email(elem.text)
				result.append((elem.text, herd_mail))
			else:
				result.append(elem.text)

		return result

	def get_descriptions(self):
		"""Return a list of text nodes for <longdescription>.

		@rtype: list
		@return: package description in string format
		@todo: Support the C{lang} attribute
		"""

		if self._descriptions is not None:
			return self._descriptions

		self._descriptions = [
			e.text for e in self._xml_tree.findall("longdescription")
		]
		return self._descriptions

	def get_maintainers(self):
		"""Get maintainers' name, email and description.

		@rtype: list
		@return: a sequence of L{_Maintainer} objects in document order.
		"""

		if self._maintainers is not None:
			return self._maintainers

		self._maintainers = []
		for node in self._xml_tree.findall('maintainer'):
			self._maintainers.append(_Maintainer(node))

		return self._maintainers

	def get_useflags(self):
		"""Get names and descriptions for USE flags defined in metadata.

		@rtype: list
		@return: a sequence of L{_Useflag} objects in document order.
		"""

		if self._useflags is not None:
			return self._useflags

		self._useflags = []
		for node in self._xml_tree.getiterator('flag'):
			self._useflags.append(_Useflag(node))

		return self._useflags

	def get_upstream(self):
		"""Get upstream contact information.

		@rtype: list
		@return: a sequence of L{_Upstream} objects in document order.
		"""

		if self._upstream is not None:
			return self._upstream

		self._upstream = []
		for node in self._xml_tree.findall('upstream'):
			self._upstream.append(_Upstream(node))

		return self._upstream

# vim: set ts=4 sw=4 tw=79:
