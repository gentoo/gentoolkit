# Copyright 2002 Gentoo Technologies, Inc
# Distributed under the terms of the GNU General Public License v2.0
# Author Karl Trygve Kalleberg <karltk@gentoo.org>

class Test:
  def __init__(self, formatter,options=None):
    self.formatter = formatter
    self.errors = []
    self.warnings = []
  def reset(self):
    self.errors = []
    self.warnings = []
  def hasWarnings(self):
    return len(self.warnings)
  def hasErrors(self):
    return len(self.errors)
  def getDesc(self):
    return self.desc
  def getStatus(self):
    if self.hasErrors():
      return "failed"
    else:
      return "passed"

class Regex:
  PN       = "[a-zA-Z_.-]+"
  PV       = "[a-z0-9A-Z_.-]+"
  P        =  PN + "-" + PV + "(-r[0-9]+)?"
  category = "[a-z0-9]+-[a-z0-9]+"
  full     = category + "/" + P
