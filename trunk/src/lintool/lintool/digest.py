# Copyright 2002 Gentoo Technologies, Inc
# Distributed under the terms of the GNU General Public License v2.0
# Author Karl Trygve Kalleberg <karltk@gentoo.org>

from test import Test
import re

class TestSyntax(Test):

  def __init__(self,formatter,options):
    Test.__init__(self,formatter,options)
    self.desc = "Testing for correct syntax"
    self.re = [ re.compile("^(MD5 [a-z0-9]+ [a-zA-Z0-9_+.-]+ [0-9]+)") ]
    self.errors = []
    
  def checkLine(self, s, ln):
    for i in self.re:
      k = i.match(s)
      if not k:
        self.errors.append("Invalid line in digest\n |" + s)
        
  def report(self):
    for i in self.errors:
      self.formatter.suberr(i)

    
def getTests(formatter,options):
  return [ TestSyntax(formatter,options) ]
