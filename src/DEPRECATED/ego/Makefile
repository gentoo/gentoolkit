# Copyright 2004 Karl Trygve Kalleberg <karltk@gentoo.org>
# Copyright 2004 Gentoo Technologies, Inc.
# Distributed under the terms of the GNU General Public License v2
#
# $Header$

include ../../makedefs.mak

all:

dist:
	mkdir -p ../../$(DISTDIR)/src/ego/
	cp Makefile AUTHORS README ChangeLog ego ../../$(DISTDIR)/src/ego/

install: all
	install -d $(DOCDIR)/ego
	install -m 0644 AUTHORS README ego $(DOCDIR)/ego/

