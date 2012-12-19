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
		>>> pkg_md.herds()
		[]
		>>> for maint in pkg_md.maintainers():
		...     print('{0} ({1})'.format(maint.email, maint.name))
		...
		nixphoeni@gentoo.org (Joe Sapp)
		>>> for flag in pkg_md.use():
		...     print(flag.name, '->', flag.description)
		...
		rtf -> Enable export to RTF
		gnome-print -> Enable pretty Python printing with gnome-print
		>>> upstream = pkg_md.upstream()
		>>> upstream  # doctest: +ELLIPSIS, +NORMALIZE_WHITESPACE
		[<_Upstream {'node': <Element 'upstream' at 0x...>,
		  'remoteids': [], 'docs': [],
		  'maintainers':
		  [<_Maintainer 'Thomas_Hinkle@alumni.brown.edu'>],
		  'changelogs': [], 'bugtrackers': []}>]
		>>> upstream[0].maintainers[0].name
		'Thomas Mills Hinkle'
"""

__all__ = ('MetaData',)
__docformat__ = 'epytext'

# =======
# Imports
# =======

import os
import re
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
		of Portage greater than 2.2. Should be DEPEND string with < and >
		converted to &lt; and &gt; respectively.
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
		self.maintainers = self.upstream_maintainers()
		self.changelogs = self.upstream_changelogs()
		self.docs = self.upstream_documentation()
		self.bugtrackers = self.upstream_bugtrackers()
		self.remoteids = self.upstream_remoteids()

	def __repr__(self):
		return "<%s %r>" % (self.__class__.__name__, self.__dict__)

	def upstream_bugtrackers(self):
		"""Retrieve upstream bugtracker location from xml node."""
		return [e.text for e in self.node.findall('bugs-to')]

	def upstream_changelogs(self):
		"""Retrieve upstream changelog location from xml node."""
		return [e.text for e in self.node.findall('changelog')]

	def upstream_documentation(self):
		"""Retrieve upstream documentation location from xml node."""
		result = []
		for elem in self.node.findall('doc'):
			lang = elem.get('lang')
			result.append((elem.text, lang))
		return result

	def upstream_maintainers(self):
		"""Retrieve upstream maintainer information from xml node."""
		return [_Maintainer(m) for m in self.node.findall('maintainer')]

	def upstream_remoteids(self):
		"""Retrieve upstream remote ID from xml node."""
		return [(e.text, e.get('type')) for e in self.node.findall('remote-id')]


class MetaData(object):
	"""Access metadata.xml"""

	def __init__(self, metadata_path):
		"""Parse a valid metadata.xml file.

		@type metadata_path: str
		@param metadata_path: path to a valid metadata.xml file
		@raise IOError: if C{metadata_path} can not be read
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
			try:
				self._herdstree = etree.parse(herds_path)
			except IOError:
				# For some trees, herds.xml may not exist. Bug #300108.
				return None

		# Some special herds are not listed in herds.xml
		if herd in ('no-herd', 'maintainer-wanted', 'maintainer-needed'):
			return None

		for node in self._herdstree.getiterator('herd'):
			if node.findtext('name') == herd:
				return node.findtext('email')

	def herds(self, include_email=False):
		"""Return a list of text nodes for <herd>.

		@type include_email: bool
		@keyword include_email: if True, also look up the herd's email
		@rtype: list
		@return: if include_email is False, return a list of strings;
		         if include_email is True, return a list of tuples containing:
					 [('herd1', 'herd1@gentoo.org'), ('no-herd', None);
		"""

		result = []
		for elem in self._xml_tree.findall('herd'):
			text = elem.text
			if text is None:
				text = ''
			if include_email:
				herd_mail = self._get_herd_email(text)
				result.append((text, herd_mail))
			else:
				result.append(text)

		return result

	def descriptions(self):
		"""Return a list of text nodes for <longdescription>.

		@rtype: list
		@return: package description in string format
		@todo: Support the C{lang} attribute
		"""

		if self._descriptions is not None:
			return self._descriptions

		long_descriptions = self._xml_tree.findall("longdescription")
		self._descriptions = [e.text for e in long_descriptions]
		return self._descriptions

	def maintainers(self):
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

	def use(self):
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

	def upstream(self):
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
