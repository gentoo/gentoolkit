# Copyright 2002 Gentoo Technologies, Inc
# Distributed under the terms of the GNU General Public License v2.0
# Author Karl Trygve Kalleberg <karltk@gentoo.org>

from test import Test
import re
import os
import os.path
import string

class TestSpaces(Test):

  def __init__(self, formatter, options):
    Test.__init__(self, formatter, options)
    self.desc = "Testing for correct formatting"
    self.re_spaces = [ re.compile("^([ ][ ]*)([a-zA-Z\.].*)"),
                       re.compile("(.*)([ \t]+)\n") ]
    self.re_backslash = re.compile("([^#]*\S)((\s\s+|\t))\\\\")
    self.reset()
    
  def checkLine(self, s, ln):
    for r in self.re_spaces:
      k = r.match(s)
      if k:
        spcs = k.groups()[1]
        rest = k.groups()[0]
        self.spaces.append((ln, spcs.replace(" ", "%").replace("\t","%") + rest))
      else:
        k = self.re_backslash.match(s)
        if k:
          head = k.group(1)
          spcs = k.group(2)
          tail = "\\"
          self.backslashes.append((ln, head + len(spcs) * "%" + tail))

  def hasErrors(self):
    return 0
  def hasWarnings(self):
    return len(self.spaces) + len(self.backslashes)

  def reset(self):
    self.spaces = []
    self.backslashes = []
      
  def report(self):
    if len(self.spaces):
      self.formatter.subwarn("Has illegal space characters (marked by %):")
      for i in self.spaces:
        self.formatter.subsub("[line " + str(i[0]) + "]:" + i[1])
    if len(self.backslashes):
      self.formatter.subwarn("Has illegal white space (marked by %), only one space character allowed:")
      for i in self.backslashes:
        self.formatter.subsub("[line " + str(i[0]) + "]:" + i[1])

class TestHeaders(Test):

  def __init__(self, formatter, options):
    Test.__init__(self,formatter, options)
    self.desc = "Testing for malformed headers"
    self.want = [ [ 0, # count
                    re.compile("^(# Copyright .*2002.*)"), 
                    "Copyright statement" ],
                  [ 0, # count
                    re.compile("^(# " + "\$" + "Header:.*" + "\$)"), # Don't want CVS to fix this
                    "$" + "Header:" + "$" ], # Don't want CVS to fix this either
                  [ 0, # count
                    re.compile("^(# Distributed under the terms of the GNU General Public License.*)"),
                    "GPL license" ] ]
    self.dontwant = [ (1, # append result of regex match
                 re.compile("^(# Copyright 1999-(2000|2001).*)"),
                 "Suspect copyright year"), 
                (1,
                 re.compile("^(# /home.*)"),
                 "Suspect path in header"),
                (0, # don't append result of regex match
                 re.compile("^(# Author.*)"),
                 "Use of Author field in the header is deprecated. Put name in ChangeLog"),
                (0,
                 re.compile("^(# Maintainer.*)"),
                 "Use of Maintainer field in the header is deprecated. Put name in ChangeLog"),
                (1,
                 re.compile("^(# /space.*)"),
                 "Suspect path in header")]

  def reset(self):
     for i in self.want:
        i[0] = 0
     self.errors = []
     self.warnings = []

  def hasErrors(self):
    num_error = 0
    for i in self.want:
      if i[0] == 0:
        num_error += 1
    return num_error 

  def checkLine(self, s, ln):
    for i in self.dontwant:
      k = i[1].match(s)
      if k and i[0]:
        self.warnings.append(i[2] + ": " + k.groups()[0] )
      elif k and not i[0]:
        self.warnings.append(i[2])
    for i in self.want:
      k = i[1].match(s)
      if k:
        i[0] += 1
        
  def report(self):
    illegal_headers = len(self.warnings)
    for i in self.want:
      if i[0] == 0:
        illegal_headers += 1 
    if illegal_headers:
      self.formatter.subwarn("Has illegal or suspect headers:")
      for i in self.warnings:
        self.formatter.subwarn(i)
      for i in self.want:
        if i[0] == 0:
          self.formatter.suberr("Missing " + i[2])

class TestTry(Test):

  def __init__(self,formatter, options):
    Test.__init__(self,formatter, options)
    self.desc = "Testing for occurence of deprecated try"
    self.re = [ re.compile("^([ \t][ \t]*try.*)"),
                re.compile("(.*=.* try .*)") ]

  def checkLine(self, s, ln):
    for i in self.re:
      k = i.match(s)
      if k:
        self.errors.append(k.groups()[0])

  def report(self):
    if len(self.errors):
      self.formatter.suberr("Uses try, which is deprecated")
      for i in self.errors:
        self.formatter.subsub(i)

class TestA(Test):

  def __init__(self, formatter, options):
    Test.__init__(self,formatter, options)
    self.desc = "Testing for superfluous A=${P}.tar.gz"
    self.re = re.compile("(^A=.*)")

  def checkLine(self, s, ln):
    k = self.re.match(s)
    if k:
      self.errors.append(k.groups()[0])

  def report(self):
    if len(self.errors):
      self.formatter.suberr("Contains superfluous " + self.errors[0])
        
class TestDepend(Test):

  def __init__(self, formatter, options):
    Test.__init__(self,formatter, options)
    self.desc = "Testing for empty DEPEND"
    self.re = re.compile("DEPEND=\"\"")

  def checkLine(self, s, ln):
    k = self.re.match(s)
    if k:
      self.warnings.append("")

  def report(self):
    if len(self.warnings):
      self.formatter.subwarn("DEPEND is suspiciously empty")

class TestHomepage(Test):

  def __init__(self, formatter,options):
    Test.__init__(self,formatter,options)
    self.desc = "Testing for empty HOMEPAGE"
    self.re = re.compile("HOMEPAGE=\"\"")

  def checkLine(self, s, ln):
    k = self.re.match(s)
    if k:
      self.warnings.append("")

  def report(self):
    if len(self.warnings):
      self.formatter.subwarn("Is HOMEPAGE really supposed to be empty ?")

class TestDescription(Test):

  def __init__(self, formatter, options):
    Test.__init__(self,formatter, options)
    self.desc = "Testing for empty DESCRIPTION"
    self.re = re.compile("DESCRIPTION=\"\"")

  def checkLine(self, s, ln):
    k = self.re.match(s)
    if k:
      self.errors.append("")

  def report(self):
    if len(self.errors):
      self.formatter.suberr("DESCRIPTION must not be empty")

class TestEnvVarPresence(Test):

  def __init__(self, formatter, options):
    Test.__init__(self,formatter, options)
    self.desc = "Testing for presence of env vars"
    self.re = []
    self.found = []
    self.required = [ ("SRC_URI", "See 2.4"),
                      ("DESCRIPTION", "See policy, 2.8"),
                      ("HOMEPAGE", "See policy, 2.8"),
                      ("DEPEND", "See policy, 2.2"),
                      ("LICENSE", "See policy, 2.6"),
                      ("SLOT", "See policy, 2.5"),
                      ("KEYWORDS", "See policy, 2.3"),
                      ("IUSE", "See policy, 2.7")
                      ]
    self.desired = [ ("RDEPEND", "Is RDEPEND == DEPEND ? See policy, 2.2") ]


    for i in self.required:
      self.re.append(re.compile("^(" + i[0] + ")="))
    for i in self.desired:
      self.re.append(re.compile("^(" + i[0] + ")="))
      
  def checkLine(self, s, ln):
    for i in self.re:
      k = i.match(s)
      if k:
        self.found.append(k.group(1))

  def report(self):
    for i in self.required:
      if i[0] not in self.found:
        self.formatter.suberr("Missing " + i[0] + ". " + i[1])
    for i in self.desired:
      if i[0] not in self.found:
        self.formatter.subwarn("Missing " + i[0] + ". " + i[1])

  def hasWarnings(self):
    for i in self.desired:
      if i[0] not in self.found:
        return 1

  def hasErrors(self):
    for i in self.required:
      if i[0] not in self.found:
        return 1

class TestLicense(Test):
  def __init__(self, formatter, options):
    Test.__init__(self,formatter, options)
    self.desc = "Testing for proper LICENSE"
    self.re = re.compile("^LICENSE=\"(.*)\"")
    self.license_dirs = options['licenseDirs']
    self.licenses = self.loadLicenses()
    
  def loadLicenses(self):
    licenses = []
    for i in self.license_dirs:
      try:
        candidates = os.listdir(i)
      except:
        self.formatter.line("!!! License directory '" + i + "' does not exist")
        continue
      for j in candidates:
        if os.path.isfile(i + "/" + j):
          licenses.append(j)
    return licenses

  def checkLine(self, s, ln):
    k = self.re.match(s)
    if k:
      print k.group(1)
      licenses = string.split(k.group(1), " ")
      for i in licenses:
    	if i not in self.licenses:
    	  self.errors.append("License '" + i + "' not known")

  def report(self):
    for i in self.errors:
      self.formatter.suberr(i)
    	  
class TestUseFlags(Test):
  def __init__(self, formatter, options):
    Test.__init__(self,formatter, options)
    self.desc = "Testing for sane USE flag usage"
    self.re = re.compile("[^#]*use ([a-z0-9\+]+).*")
    self.useflags = self.loadUseFlags()

  def loadUseFlags(self):
    ins = open("/usr/portage/profiles/use.desc")
    rex = re.compile("^([a-z0-9]+)[ \t]+-.*");
    useflags = []
    for i in ins.readlines():
      k = rex.match(i)
      if k:
        useflags.append(k.group(1))
    return useflags
    
  def checkLine(self, s, ln):
    k = self.re.match(s)
    if k:
      flag = k.group(1)
      if flag not in self.useflags:
        l = k.start(1)
        # We want to try and figure pretty exactly if we've hit a real instnce
        # of the use command or just some random mumbling inside a string
        numApostrophes = 0
        numBackticks = 0
        numTicks = 0
        for i in xrange(l,0,-1):
          if s[i] == '\"' and (i == 0 or (i > 0 and s[i-1] != '\\')):
            numApostrophes += 1
          if s[i] == '\'' and (i == 0 or (i > 0 and s[i-1] != '\\')):
            numTicks += 1
          if s[i] == '`' and (i == 0 or (i > 0 and s[i-1] != '\\')):
            numBackticks += 1

        if numApostrophes % 2 == 0:
          foundError = 1
        elif numBackticks % 2 and numTicks % 2 == 0:
          foundError = 1
        else:
          foundError = 0

        if foundError:
          self.errors.append("Unknown USE flag '" + flag + "'")

  def report(self):
    for i in self.errors:
      self.formatter.suberr(i)


def getTests(formatter,options):
  return [ TestSpaces(formatter,options),
           TestHeaders(formatter,options),
           TestTry(formatter,options),
           TestA(formatter,options),
           TestDepend(formatter,options),
           TestHomepage(formatter,options),
           TestDescription(formatter,options),
           TestEnvVarPresence(formatter,options),
           TestUseFlags(formatter,options),
           TestLicense(formatter,options) ]
