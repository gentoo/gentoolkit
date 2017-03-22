# Copyright 2004 Karl Trygve Kalleberg <karltk@gentoo.org>
# Copyright 2004 Gentoo Technologies, Inc.
# Distributed under the terms of the GNU General Public License v2
#
# $Header$

include ../../makedefs.mak

.PHONY: all
all: 

dist: 
	mkdir -p ../../$(DISTDIR)/src/ebump/
	cp Makefile AUTHORS README ChangeLog ebump ebump.1 ../../$(DISTDIR)/src/ebump/

install: all
	install -m 0755 ebump $(BINDIR)/
	install -d $(DOCDIR)/ebump
	install -m 0644 AUTHORS README ChangeLog $(DOCDIR)/ebump/
	install -m 0644 ebump.1 $(MAN1DIR)/
