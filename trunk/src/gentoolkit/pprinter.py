#!/usr/bin/python
#
# Copyright 2004 Karl Trygve Kalleberg <karltk@gentoo.org>
# Copyright 2004 Gentoo Foundation
# Distributed under the terms of the GNU General Public License v2
#
# $Header$

import gentoolkit
import output
import sys

def print_error(s):
    sys.stderr.write(output.red("!!! ") + s + "\n")

def print_info(lv, s, line_break = True):
    if gentoolkit.Config["verbosityLevel"] >= lv:
        sys.stdout.write(s)
        if line_break:
            sys.stdout.write("\n")

def print_warn(s):
    sys.stderr.write("!!! " + s + "\n")
    
def die(err, s):
    error(s)
    sys.exit(-err)

# Colour settings

def cpv(s):
    return output.green(s)

def slot(s):
    return output.white(s)
    
def useflag(s):
    return output.blue(s)

def useflagon(s):
    return output.red(s)

def useflagoff(s):
    return output.blue(s)
    
def maskflag(s):
    return output.red(s)

def installedflag(s):
    return output.white(s)
    
def number(s):
    return output.turquoise(s)

def pkgquery(s):
    return output.white(s)

def regexpquery(s):
    return output.white(s)

def path(s):
    return output.white(s)

def path_symlink(s):
    return output.turquoise(s)

def productname(s):
    return output.turquoise(s)
    
def globaloption(s):
    return output.yellow(s)

def localoption(s):
    return output.green(s)

def command(s):
    return output.green(s)
    
def section(s):
    return output.turquoise(s)    

def subsection(s):
    return output.turquoise(s)
    
def emph(s):
    return output.white(s)    