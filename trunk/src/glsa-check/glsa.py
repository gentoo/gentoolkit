# $Header$

# This program is licensed under the GPL, version 2

# WARNING: this code is only tested by a few people and should NOT be used
# on production systems at this stage. There are possible security holes and probably
# bugs in this code. If you test it please report ANY success or failure to
# me (genone@gentoo.org).

# The following planned features are currently on hold:
# - getting GLSAs from http/ftp servers (not really useful without the fixed ebuilds)
# - GPG signing/verification (until key policy is clear)

__author__ = "Marius Mauch <genone@gentoo.org>"

import os, sys, urllib, time, string, portage, codecs, re
import xml.dom.minidom

sys.path.insert(0, "/usr/lib/portage/pym")	# to find portage.py

opMapping = {"le": "<=", "lt": "<", "eq": "=", "gt": ">", "ge": ">="}
NEWLINE_ESCAPE = "!;\\n"	# some random string to mark newlines that should be preserved

def center(text, width):
	"""
	Returns a string containing I{text} that is padded with spaces on both
	sides. If C{len(text) >= width} I{text} is returned unchanged.
	
	@type	text: String
	@param	text: the text to be embedded
	@type	width: Integer
	@param	width: the minimum length of the returned string
	@rtype:		String
	@return:	the expanded string or I{text}
	"""
	if len(text) >= width:
		return text
	margin = (width-len(text))/2
	rValue = " "*margin
	rValue += text
	if 2*margin + len(text) == width:
		rValue += " "*margin
	elif 2*margin + len(text) + 1 == width:
		rValue += " "*(margin+1)
	return rValue


def wrap(text, width, caption=""):
	"""
	Wraps the given text at column I{width}, optionally indenting
	it so that no text is under I{caption}. It's possible to encode 
	hard linebreaks in I{text} with L{NEWLINE_ESCAPE}.
	
	@type	text: String
	@param	text: the text to be wrapped
	@type	width: Integer
	@param	width: the column at which the text should be wrapped
	@type	caption: String
	@param	caption: this string is inserted at the beginning of the 
					 return value and the paragraph is indented up to
					 C{len(caption)}.
	@rtype:		String
	@return:	the wrapped and indented paragraph
	"""
	rValue = ""
	line = caption
	words = text.split()
	indentLevel = len(caption)+1
	for w in words:
		if len(line)+len(w)+1 > width:
			rValue += line+"\n"
			line = " "*indentLevel+w
		elif w.find(NEWLINE_ESCAPE) >= 0:
			if len(line.strip()) > 0:
				rValue += line+" "+w.replace(NEWLINE_ESCAPE, "\n")
			else:
				rValue += line+w.replace(NEWLINE_ESCAPE, "\n")
			line = " "*indentLevel
		else:
			if len(line.strip()) > 0:
				line += " "+w
			else:
				line += w
	if len(line) > 0:
		rValue += line.replace(NEWLINE_ESCAPE, "\n")
	return rValue

def checkconfig(myconfig):
	"""
	takes a portage.config instance and adds GLSA specific keys if
	they are not present. TO-BE-REMOVED (should end up in make.*)
	"""
	mysettings = {
		"GLSA_DIR": portage.settings["PORTDIR"]+"/metadata/glsa/",
		"GLSA_PREFIX": "glsa-",
		"GLSA_SUFFIX": ".xml",
		"CHECKFILE": "/var/cache/edb/glsa",
		"GLSA_SERVER": "www.gentoo.org/security/en/glsa/",	# not completely implemented yet
		"CHECKMODE": "local",								# not completely implemented yet
		"PRINTWIDTH": "76"
	}
	for k in mysettings.keys():
		if not myconfig.has_key(k):
			myconfig[k] = mysettings[k]
	return myconfig

def get_glsa_list(repository, myconfig):
	"""
	Returns a list of all available GLSAs in the given repository
	by comparing the filelist there with the pattern described in
	the config.
	
	@type	repository: String
	@param	repository: The directory or an URL that contains GLSA files
						(Note: not implemented yet)
	@type	myconfig: portage.config
	@param	myconfig: a GLSA aware config instance (see L{checkconfig})
	
	@rtype:		List of Strings
	@return:	a list of GLSA IDs in this repository
	"""
	# TODO: remote fetch code for listing

	rValue = []

	if not os.access(repository, os.R_OK):
		return []
	dirlist = os.listdir(repository)
	prefix = myconfig["GLSA_PREFIX"]
	suffix = myconfig["GLSA_SUFFIX"]
	
	for f in dirlist:
		try:
			if f[:len(prefix)] == prefix:
				rValue.append(f[len(prefix):-1*len(suffix)])
		except IndexError:
			pass
	return rValue

def getListElements(listnode):
	"""
	Get all <li> elements for a given <ol> or <ul> node.
	
	@type	listnode: xml.dom.Node
	@param	listnode: <ul> or <ol> list to get the elements for
	@rtype:		List of Strings
	@return:	a list that contains the value of the <li> elements
	"""
	rValue = []
	if not listnode.nodeName in ["ul", "ol"]:
		raise GlsaFormatException("Invalid function call: listnode is not <ul> or <ol>")
	for li in listnode.childNodes:
		rValue.append(getText(li, format="strip"))
	return rValue

def getText(node, format):
	"""
	This is the main parser function. It takes a node and traverses
	recursive over the subnodes, getting the text of each (and the
	I{link} attribute for <uri> and <mail>). Depending on the I{format}
	parameter the text might be formatted by adding/removing newlines,
	tabs and spaces. This function is only useful for the GLSA DTD,
	it's not applicable for other DTDs.
	
	@type	node: xml.dom.Node
	@param	node: the root node to start with the parsing
	@type	format: String
	@param	format: this should be either I{strip}, I{keep} or I{xml}
					I{keep} just gets the text and does no formatting.
					I{strip} replaces newlines and tabs with spaces and
					replaces multiple spaces with one space.
					I{xml} does some more formatting, depending on the
					type of the encountered nodes.
	@rtype:		String
	@return:	the (formatted) content of the node and its subnodes
	"""
	rValue = ""
	if format in ["strip", "keep"]:
		if node.nodeName in ["uri", "mail"]:
			rValue += node.childNodes[0].data+": "+node.getAttribute("link")
		else:
			for subnode in node.childNodes:
				if subnode.nodeName == "#text":
					rValue += subnode.data
				else:
					rValue += getText(subnode, format)
	else:
		for subnode in node.childNodes:
			if subnode.nodeName == "p":
				for p_subnode in subnode.childNodes:
					if p_subnode.nodeName == "#text":
						rValue += p_subnode.data
					elif p_subnode.nodeName in ["uri", "mail"]:
						rValue += p_subnode.childNodes[0].data
						rValue += " ( "+p_subnode.getAttribute("link")+" )"
				rValue += NEWLINE_ESCAPE
			elif subnode.nodeName == "ul":
				for li in getListElements(subnode):
					rValue += "- "+li+NEWLINE_ESCAPE+" "
			elif subnode.nodeName == "ol":
				i = 0
				for li in getListElements(subnode):
					i = i+1
					rValue += str(i)+". "+li+NEWLINE_ESCAPE+" "
			elif subnode.nodeName == "code":
				rValue += getText(subnode, format="keep").replace("\n", NEWLINE_ESCAPE)
			elif subnode.nodeName == "#text":
				rValue += subnode.data
			else:
				raise GlsaFormatException("Invalid Tag found: ", subnode.nodeName)
	if format == "strip":
		rValue = rValue.strip(" \n\t")
		rValue = re.sub("[\s]{2,}", " ", rValue)
	return rValue

def getMultiTagsText(rootnode, tagname, format):
	"""
	Returns a list with the text of all subnodes of type I{tagname}
	under I{rootnode} (which itself is not parsed) using the given I{format}.
	
	@type	rootnode: xml.dom.Node
	@param	rootnode: the node to search for I{tagname}
	@type	tagname: String
	@param	tagname: the name of the tags to search for
	@type	format: String
	@param	format: see L{getText}
	@rtype:		List of Strings
	@return:	a list containing the text of all I{tagname} childnodes
	"""
	rValue = []
	for e in rootnode.getElementsByTagName(tagname):
		rValue.append(getText(e, format))
	return rValue

def makeAtom(pkgname, versionNode):
	"""
	creates from the given package name and information in the 
	I{versionNode} a (syntactical) valid portage atom.
	
	@type	pkgname: String
	@param	pkgname: the name of the package for this atom
	@type	versionNode: xml.dom.Node
	@param	versionNode: a <vulnerable> or <unaffected> Node that
						 contains the version information for this atom
	@rtype:		String
	@return:	the portage atom
	"""
	return opMapping[versionNode.getAttribute("range")] \
			+pkgname \
			+"-"+getText(versionNode, format="strip")

def makeVersion(versionNode):
	"""
	creates from the information in the I{versionNode} a 
	version string (format <op><version>).
	
	@type	versionNode: xml.dom.Node
	@param	versionNode: a <vulnerable> or <unaffected> Node that
						 contains the version information for this atom
	@rtype:		String
	@return:	the version string
	"""
	return opMapping[versionNode.getAttribute("range")] \
			+getText(versionNode, format="strip")

def getMinUpgrade(vulnerableList, unaffectedList):
	"""
	Checks if the systemstate is matching an atom in
	I{vulnerableList} and returns string describing
	the lowest version for the package that matches an atom in 
	I{unaffectedList} and is greater than the currently installed
	version or None if the system is not affected. Both
	I{vulnerableList} and I{unaffectedList} should have the
	same base package.
	
	@type	vulnerableList: List of Strings
	@param	vulnerableList: atoms matching vulnerable package versions
	@type	unaffectedList: List of Strings
	@param	unaffectedList: atoms matching unaffected package versions
	@rtype:		String | None
	@return:	the lowest unaffected version that is greater than
				the installed version.
	"""
	rValue = None
	for v in vulnerableList:
		installed = portage.db["/"]["vartree"].dbapi.match(v)
		if not installed:
			continue
		for u in unaffectedList:
			for c in portage.db["/"]["porttree"].dbapi.match(u):
				c_pv = portage.catpkgsplit(c)
				i_pv = portage.catpkgsplit(portage.best(installed))
				if portage.pkgcmp(c_pv[1:], i_pv[1:]) > 0 and (rValue == None or portage.pkgcmp(c_pv[1:], rValue) < 0):
					rValue = c_pv[0]+"/"+c_pv[1]+"-"+c_pv[2]
					if c_pv[3] != "r0":		# we don't like -r0 for display
						rValue += "-"+c_pv[3]
	return rValue

# simple Exception classes to catch specific errors
class GlsaTypeException(Exception):
	def __init__(self, doctype):
		Exception.__init__(self, "wrong DOCTYPE: %s" % doctype)

class GlsaFormatExceptio(Exception):
	pass
				
# GLSA xml data wrapper class
class Glsa:
	"""
	This class is a wrapper for the XML data and provides methods to access
	and display the contained data.
	"""
	def __init__(self, myid, myconfig):
		"""
		Simple constructor to set the ID, store the config and gets the 
		XML data by calling C{self.read()}.
		
		@type	myid: String
		@param	myid: String describing the id for the GLSA object (standard
					  GLSAs have an ID of the form YYYYMM-nn)
		@type	myconfig: portage.config
		@param	myconfig: the config that should be used for this object.
		"""
		self.nr = myid
		self.config = myconfig
		self.read()

	def read(self):
		"""
		Here we build the filename from the config and the ID and pass
		it to urllib to fetch it from the filesystem or a remote server.
		
		@rtype:		None
		@return:	None
		"""
		if self.config["CHECKMODE"] == "local":
			repository = "file://" + self.config["GLSA_DIR"]
		else:
			repository = self.config["GLSA_SERVER"]
		myurl = repository + self.config["GLSA_PREFIX"] + str(self.nr) + self.config["GLSA_SUFFIX"]
		self.parse(urllib.urlopen(myurl))
		return None

	def parse(self, myfile):
		"""
		This method parses the XML file and sets up the internal data 
		structures by calling the different helper functions in this
		module.
		
		@type	myfile: String
		@param	myfile: Filename to grab the XML data from
		@rtype:		None
		@returns:	None
		"""
		self.DOM = xml.dom.minidom.parse(myfile)
		if not self.DOM.doctype:
			raise GlsaTypeException(None)
		elif self.DOM.doctype.systemId != "http://www.gentoo.org/dtd/glsa.dtd":
			raise GlsaTypeException(self.DOM.doctype.systemId)
		myroot = self.DOM.getElementsByTagName("glsa")[0]
		if myroot.getAttribute("id") != self.nr:
			raise GlsaFormatException("filename and internal id don't match:" + myroot.getAttribute("id") + " != " + self.nr)

		# the simple (single, required, top-level, #PCDATA) tags first
		self.title = getText(myroot.getElementsByTagName("title")[0], format="strip")
		self.synopsis = getText(myroot.getElementsByTagName("synopsis")[0], format="strip")
		self.announced = getText(myroot.getElementsByTagName("announced")[0], format="strip")
		self.revised = getText(myroot.getElementsByTagName("revised")[0], format="strip")
		
		# now the optional and 0-n toplevel, #PCDATA tags and references
		try:
			self.access = getText(myroot.getElementsByTagName("access")[0], format="strip")
		except IndexError:
			self.access = ""
		self.bugs = getMultiTagsText(myroot, "bug", format="strip")
		self.references = getMultiTagsText(myroot.getElementsByTagName("references")[0], "uri", format="keep")
		
		# and now the formatted text elements
		self.description = getText(myroot.getElementsByTagName("description")[0], format="xml")
		self.workaround = getText(myroot.getElementsByTagName("workaround")[0], format="xml")
		self.resolution = getText(myroot.getElementsByTagName("resolution")[0], format="xml")
		self.impact_text = getText(myroot.getElementsByTagName("impact")[0], format="xml")
		self.impact_type = myroot.getElementsByTagName("impact")[0].getAttribute("type")
		try:
			self.background = getText(myroot.getElementsByTagName("background")[0], format="xml")
		except IndexError:
			self.background = ""					

		# finally the interesting tags (product, affected, package)
		self.glsatype = myroot.getElementsByTagName("product")[0].getAttribute("type")
		self.product = getText(myroot.getElementsByTagName("product")[0], format="strip")
		self.affected = myroot.getElementsByTagName("affected")[0]
		self.packages = {}
		for p in self.affected.getElementsByTagName("package"):
			name = p.getAttribute("name")
			self.packages[name] = {}
			self.packages[name]["arch"] = p.getAttribute("arch")
			self.packages[name]["auto"] = (p.getAttribute("auto") == "yes")
			self.packages[name]["vul_vers"] = [makeVersion(v) for v in p.getElementsByTagName("vulnerable")]
			self.packages[name]["unaff_vers"] = [makeVersion(v) for v in p.getElementsByTagName("unaffected")]
			self.packages[name]["vul_atoms"] = [makeAtom(name, v) for v in p.getElementsByTagName("vulnerable")]
			self.packages[name]["unaff_atoms"] = [makeAtom(name, v) for v in p.getElementsByTagName("unaffected")]
		# TODO: services aren't really used yet
		self.services = self.affected.getElementsByTagName("service")
		return None

	def dump(self, outfile="/dev/stdout", encoding="latin1"):
		"""
		Dumps a plaintext representation of this GLSA to I{outfile} or 
		B{stdout} if it is ommitted. You can specify an alternate
		I{encoding} if needed (default is latin1).
		
		@type	outfile: String
		@param	outfile: Filename to dump the output in 
						 (defaults to "/dev/stdout")
		@type	encoding: The encoding that should be used when writing 
						  to I{outfile}.
		"""
		myfile = codecs.open(outfile, "w", encoding)
		width = int(self.config["PRINTWIDTH"])
		myfile.write(center("GLSA %s: %s" % (self.nr, self.title), width)+"\n")
		myfile.write((width*"=")+"\n")
		myfile.write(wrap(self.synopsis, width, caption="Synopsis:         ")+"\n")
		myfile.write("Announced on:      %s\n" % self.announced)
		myfile.write("Last revised on:   %s\n\n" % self.revised)
		if self.glsatype == "ebuild":
			for pkg in self.packages.keys():
				vul_vers = string.join(self.packages[pkg]["vul_vers"])
				unaff_vers = string.join(self.packages[pkg]["unaff_vers"])
				myfile.write("Affected package:  %s\n" % pkg)
				myfile.write("Affected archs:    ")
				if self.packages[pkg]["arch"] == "*":
					myfile.write("All\n")
				else:
					myfile.write("%s\n" % self.packages[pkg]["arch"])
				myfile.write("Vulnerable:        %s\n" % vul_vers)
				myfile.write("Unaffected:        %s\n\n" % unaff_vers)
		elif self.glsatype == "infrastructure":
			pass
		if len(self.bugs) > 0:
			myfile.write("\nRelated bugs:      ")
			for i in range(0, len(self.bugs)):
				myfile.write(self.bugs[i])
				if i < len(self.bugs)-1:
					myfile.write(", ")
				else:
					myfile.write("\n")				
		if self.background:
			myfile.write("\n"+wrap(self.background, width, caption="Background:       "))
		myfile.write("\n"+wrap(self.description, width, caption="Description:      "))
		myfile.write("\n"+wrap(self.impact_text, width, caption="Impact:           "))
		myfile.write("\n"+wrap(self.workaround, width, caption="Workaround:       "))
		myfile.write("\n"+wrap(self.resolution, width, caption="Resolution:       "))
		myfile.write("\nReferences:        ")
		for r in self.references:
			myfile.write(r+"\n"+19*" ")
		myfile.write("\n")
		myfile.close()
	
	def isVulnerable(self):
		"""
		Tests if the system is affected by this GLSA by checking if any
		vulnerable package versions are installed. Also checks for affected
		architectures.
		
		@rtype:		Boolean
		@returns:	True if the system is affected, False if not
		"""
		vList = []
		rValue = False
		for k in self.packages.keys():
			pkg = self.packages[k]
			if pkg["arch"] == "*" or self.config["ARCH"] in pkg["arch"].split():
				vList += pkg["vul_atoms"]
		for v in vList:
			rValue = rValue or len(portage.db["/"]["vartree"].dbapi.match(v)) > 0
		return rValue
	
	def isApplied(self):
		"""
		Looks if the GLSA IDis in the GLSA checkfile to check if this
		GLSA was already applied.
		
		@rtype:		Boolean
		@returns:	True if the GLSA was applied, False if not
		"""
		aList = portage.grabfile(self.config["CHECKFILE"])
		return (self.nr in aList)

	def inject(self):
		"""
		Puts the ID of this GLSA into the GLSA checkfile, so it won't
		show up on future checks. Should be called after a GLSA is 
		applied or on explicit user request.

		@rtype:		None
		@returns:	None
		"""
		if not self.isApplied():
			checkfile = open(self.config["CHECKFILE"], "a+")
			checkfile.write(self.nr+"\n")
			checkfile.close()
		return None
	
	def getMergeList(self):
		"""
		Returns the list of package-versions that have to be merged to
		apply this GLSA properly. The versions are as low as possible 
		while avoiding downgrades (see L{getMinUpgrade}).
		
		@rtype:		List of Strings
		@return:	list of package-versions that have to be merged
		"""
		rValue = []
		for pkg in self.packages.keys():
			update = getMinUpgrade(self.packages[pkg]["vul_atoms"],
									self.packages[pkg]["unaff_atoms"])
			if update:
				rValue.append(update)
		return rValue
