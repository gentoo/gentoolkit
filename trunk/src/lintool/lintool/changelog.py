# Copyright 2002 Gentoo Technologies, Inc
# Distributed under the terms of the GNU General Public License v2.0
# Author Karl Trygve Kalleberg <karltk@gentoo.org>

from test import Test, Regex
import re

class TestHeaders(Test):
  def __init__(self, formatter,options):
    Test.__init__(self,formatter,options)
    self.desc = "Testing for malformed headers"
    self.re = [ (1, # append result of regex match
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

  def checkLine(self, s, ln):
    for i in self.re:
      k = i[1].match(s)
      if k and i[0]:
        self.warnings.append(i[2] + ": " + k.groups()[0] )
      elif k and not i[0]:
        self.warnings.append(i[2])
        
  def report(self):
    if len(self.warnings):
      self.formatter.subwarn("Has illegal or suspect headers:")
      for i in self.warnings:
        self.formatter.subsub(i)

class TestConstructPresence(Test):

  def __init__(self, formatter,options):
    Test.__init__(self,formatter,options)
    self.desc = "Testing for presence of required constructs"
    self.required = [ ["# ChangeLog for " + Regex.category + "/" + Regex.PN,
                       None,
                       None,
                       "proper ChangeLog line" 
                      ],

                      ["\*" + Regex.P + " \([0-9]+ [A-Z][a-z][a-z] 2002\).*",
                       None,
                       None,
                       "proper release entry on the form *package-1.0.0 (01 Apr 2000)"
                      ],

                      ["  [0-9]+ [A-Z][a-z][a-z] 2002; .* <.*@.*> .*:",
                       None,
                       None,
                       "proper changelog entry"
                      ]
                    ]

    for i in self.required:
      i[1] = re.compile("^(" + i[0] + ")")
      
  def checkLine(self, s, ln):
    for i in self.required:
      k = i[1].match(s)
      if k:
        i[2] = 1

  def report(self):
    for i in self.required:
      if not i[2]:
        self.formatter.suberr("Missing " + i[3])

  def hasErrors(self):
    for i in self.required:
      if not i[2]:
        return 1

class TestIndentation(Test):

  def __init__(self, formatter,options):
    Test.__init__(self,formatter,options)
    self.desc = "Testing for proper indentation"
    self.re = re.compile("^(  |[#*].|\n).*")

  def checkLine(self, s, ln):
    k = self.re.match(s)
    if not k:
      self.errors.append(s)

  def report(self):
    for i in self.errors:
      print i.replace(' ','%')

def getTests(formatter,options):
    return [ TestHeaders(formatter,options),
             TestConstructPresence(formatter,options),
             TestIndentation(formatter,options)
             ]
