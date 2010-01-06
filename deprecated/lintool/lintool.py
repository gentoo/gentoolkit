#! /usr/bin/python
#
# Copyright 2002 Gentoo Technologies, Inc
# Distributed under the terms of the GNU General Public License v2.0
# Author Karl Trygve Kalleberg <karltk@gentoo.org>
#
# About:
# lintool aims to check the stylistic and syntactical correctness for
# ebuilds, changelogs and digest files for the Gentoo packaging system.
#
# TODO
#
# - Make HTMLFormatter
#

VERSION="0.2.4"

import sys
import getopt

from lintool import ebuild, changelog, digest

class TextFormatter:
  def section(self, s):
    print "\n" + "-"*79
    print " " + s + "\n"
  def bullet(self, s):
    print "* " + s
  def sub(self, s):
    print "- " + s
  def subwarn(self, s):
    print "- (W) " + s
  def suberr(self, s):
    print "- (E) " + s
  def subsub(self, s):
    print " |" + s
  def subsubwarn(self, s):
    print " (W) |" + s
  def subsuberr(self, s):
    print " (E) |" + s
  def line(self,s):
    print s
  def div(self, left, right):
    l = len(left)
    r = len(right)
    return left + " " * (78-l-r) + right

class MunchieFormatter:
  def section(self, s):
    print "[lintool] " + "-" * (78 - len("[lintool] "))
    print "[lintool] " + s + "\n"
  def bullet(self, s):
    print "[lintool] * " + s
  def sub(self, s):
    print "[lintool] - " + s
  def subwarn(self, s):
    print "[lintool] - (W) " + s
  def suberr(self, s):
    print "[lintool] - (E) " + s
  def subsub(self, s):
    print "[lintool] |" + s
  def subsubwarn(self, s):
    print "[lintool]  (W) |" + s
  def subsuberr(self, s):
    print "[lintool] (E) |" + s
  def line(self,s):
    print "[lintool] " + s
  def div(self, left, right):
    l = len("[lintool] " + left)
    r = len(right)
    return left + " " * (78-l-r) + right

formatters = { "text" : TextFormatter(), "munchie" : MunchieFormatter()  }

def extractFilename(path):
  return path

def runTests(tests,results,ins):
  for j in tests:
    j.reset()

  ln = 1
  for i in ins.readlines():
    for j in tests:
      j.checkLine(i, ln)
    ln += 1

  hasWarning = 0
  hasError = 0
  for j in xrange(len(tests)):
    if tests[j].hasErrors():
      results[j][0] += 1
      hasError = 1
    if tests[j].hasWarnings():
      results[j][1] += 1
      hasWarning = 1
  return (hasError, hasWarning)
        
def showStatus(options,tests,formatter,file):
  if options['showDetails'] or options['showSeparate']:
    formatter.section("Status for " + file)
    for j in tests:
      if options['showSeparate'] or options['showDetails']:
        l = len(j.getDesc())
        formatter.bullet(formatter.div(j.getDesc(), ": " + j.getStatus()))
        if options['showDetails']:
          j.report()
  elif options['showShort']:
    allOK = 1
    for j in tests:
      if j.hasErrors():
        allOK = 0
        break
    if allOK:
      formatter.div(file, ": OK")
    else:
      formatter.div(file, ": Not OK")
    # else fall through the bottom    
    
def usage(opts):
  print sys.argv[0], "[options] ebuild [ebuild ebuild ... ]"
  print

  if opts:
    print "Where [options] include:"
    for (short,long_,desc) in opts:
      short_ = ''
      for s in short:
        short_ = short_ + '-' + s + ','
      long_ = '--' + long_
      opt = short_ + long_
      opt = opt.rjust(18)
      print opt + '  ' + desc
    print

def parse_opts(argv):
  options = { 'showSeparate': 0,
              'showTotal': 1,
              'showDetails': 1,
              'showShort': 1,
              'listTests': 0,
              'desiredTests': 0,
              'testMode' : "ebuild",
              'licenseDirs' : [ "/usr/portage/licenses" ],
              'formatter' : 'text'
            }

  opts = (('', 'show-separate',
           'Show short summary of tests for each ebuild checked'),

          ('v', 'version',
           'Show program version'),

          ('', 'no-summary',
           'Do not show total summary'),

          ('', 'no-details',
           'Do not show full details of tests for each ebuild checked'),

          ('', 'ebuild',
           'Files to check are ebuilds'),
          
          ('', 'changelog',
           'Files to check are changelogs'),

          ('', 'digest',
           'Files to check are digests'),

          ('', 'tests=',
           'Comma-separated list of tests to run'),

          ('', 'list-tests',
           'List available tests'),

          ('', 'from-file=<file>',
           'Read ebuilds from <file>'),

          ('', 'formatter=<formatter>',
           "Use 'text' (default) or 'munchie' formatter"),

          ('', 'aux-license-dir=<dir>',
           'Add <dir> to directories to search for licenses'),
            
          ('?h', 'help',
           'Show this help'),
         )

  short_options = ''
  long_options = []
  for (short,long_,desc) in opts:
    short_options = short_options + short
    if '=' in long_:
      long_ = long_.split('=', 1)[0] + '='
    long_options.append(long_)

  try:
    (option_list,args) = getopt.getopt(sys.argv[1:], short_options, long_options)
  except getopt.GetoptError, details:
    print 'Error parsing command line:',str(details)
    sys.exit(1)

  for (option,value) in option_list:
    if option in [ '--no-details' ]:
      options['showShort'] = 1
      options['showDetails'] = 0
    elif option in [ '--show-separate' ]:
      options['showShort'] = 0
      options['showSeparate'] = 1
    elif option in [ '--no-summary']:
      options['showTotal'] = 0
    elif option in [ '--from-file' ]:
      lines = open(value, 'r').readlines()
      lines = [o.strip() for o in lines]
      args = lines + args
    elif option in [ '--tests' ]:
      options['desiredTests'] = value.split(",")
    elif option in [ '--formatter' ]:
      options['formatter'] = value
    elif option in [ '--list-tests' ]:
      options['listTests'] = 1
    elif option in [ '--ebuild' ]:
      options['testMode'] = 'ebuild'
    elif option in [ '--changelog' ]:
      options['testMode'] = 'changelog'
    elif option in [ '--digest' ]:
      options['testMode'] = 'digest'
    elif option in [ '--aux-license-dir' ]:
      options['licenseDirs'].append(value)
    elif option in [ '-v', '--version' ]:
      print "Lintool " + VERSION
      sys.exit(0)
    elif option in [ '-h', '-?', '--help' ]:
      usage(opts)
      sys.exit(0)
    else:
      # shouldn't ever happen. better to be safe
      print "Unknown option - '%s'!" % (option)
      sys.exit(1)

  return (options,args)

def main():
    (options,args) = parse_opts(sys.argv[1:])

    formatter = formatters[options['formatter']]

    # Get test suite for given mode
    if options['testMode'] == "ebuild":
      available_tests = ebuild.getTests(formatter, options)
    elif options['testMode'] == "changelog":
      available_tests = changelog.getTests(formatter, options)
    elif options['testMode'] == "digest":
      available_tests = digest.getTests(formatter, options)

    # List available tests, if that was the users request
    if options['listTests']:
      maxlen = 0
      for i in available_tests:
        maxlen = max(len(i.__class__.__name__), maxlen)
      for i in available_tests:
        n = i.__class__.__name__
        print n + " " * (maxlen - len(n)) + " - " + i.getDesc()

    # Quit with short usage string, if no params given
    if len(args) == 0:
      usage(None)
      sys.exit(1)

    # Create final list of tests to run
    tests = []
    notTests = []
    if options['desiredTests']:
      for i in options['desiredTests']:
        for j in available_tests:
          if len(i) and i[0] == "-":
            notTests.append(i[1:])
          if j.__class__.__name__ == i:
            tests.append(j)
    else:
      tests = available_tests

    if len(notTests):
      for i in available_tests:
        if i.__class__.__name__ not in notTests:
          tests.append(i)
      
    results = [[0, 0] for x in range(len(tests))]

    # Set up for test run
    numFiles = 0
    totalErrors = 0
    totalWarnings = 0

    # Iterate through all files given as arguments, testing each file
    # against the final list of tests
    for i in args:
      fn = extractFilename(i)
      ins = open(i, "r")
      numFiles += 1
      (hasError, hasWarning) = runTests(tests,results,ins)
      totalErrors += hasError
      totalWarnings += hasWarning
      showStatus(options,tests,formatter,fn)

    # Show totals, if options allow it
    if options['showTotal']:
      formatter.section(formatter.div("Summary for all " + str(numFiles) + " " + options['testMode'] + "(s) checked", "#errors/warns"))
      for i in xrange(len(tests)):
        l = len(tests[i].getDesc())
        formatter.line(formatter.div(tests[i].getDesc(), ": %3d / %3d" % (results[i][0], results[i][1])))
      formatter.line(formatter.div("Total number of ebuilds with errors",  \
                                                   "%3d (%3d%%)" % (totalErrors, totalErrors*100/numFiles)))
      formatter.line(formatter.div("Total number of ebuilds with warnings", \
                                                  "%3d (%3d%%)" % (totalWarnings, totalWarnings*100/numFiles)))
    if totalErrors:
        sys.exit(1)

if __name__ == "__main__":
  main()

