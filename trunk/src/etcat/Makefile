# Copyright 2004 Karl Trygve Kalleberg <karltk@gentoo.org>
# Copyright 2004 Gentoo Technologies, Inc.
# Distributed under the terms of the GNU General Public License v2
#
# $Header$

include ../../makedefs.mak

all:

dist:
	mkdir -p ../../$(distdir)/src/etcat
	cp {Makefile,AUTHORS,README,TODO,ChangeLog,etcat,etcat.1} ../../$(distdir)/src/etcat

install:
	install -m 0755 etcat $(bindir)/
	install -d $(docdir)/etcat
	install -m 0644 {README,AUTHORS} $(docdir)/etcat/
	install -m 0644 etcat.1 $(mandir)/
