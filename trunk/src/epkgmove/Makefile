# Copyright 2004 Karl Trygve Kalleberg <karltk@gentoo.org>
# Copyright 2004 Gentoo Technologies, Inc.
# Distributed under the terms of the GNU General Public License v2
#
# $Header$

include ../../makedefs.mak

.PHONY: all
all: 

dist: 
	mkdir -p ../../$(distdir)/src/epkgmove/
	cp {Makefile,AUTHORS,README,TODO,ChangeLog,epkgmove} ../../$(distdir)/src/epkgmove/

install: all
	install -m 0755 epkgmove $(bindir)/
	install -d $(docdir)/epkgmove
	install -m 0644 {AUTHORS,README,TODO,ChangeLog} $(docdir)/epkgmove/
#	install -m 0644 epkgmove.1 $(mandir)/
