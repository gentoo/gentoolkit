# Copyright 2004 Karl Trygve Kalleberg <karltk@gentoo.org>
# Copyright 2004 Gentoo Technologies, Inc.
# Distributed under the terms of the GNU General Public License v2
#
# $Header$

include ../../makedefs.mak

.PHONY: all
all: 

dist: 
	mkdir -p ../../$(distdir)/src/ebump/
	cp Makefile AUTHORS README ChangeLog ebump ebump.1 ../../$(distdir)/src/ebump/

install: all
	install -m 0755 ebump $(bindir)/
	install -d $(docdir)/ebump
	install -m 0644 AUTHORS README ChangeLog $(docdir)/ebump/
	install -m 0644 ebump.1 $(mandir)/
