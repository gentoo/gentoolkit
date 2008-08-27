# Copyright 2004 Karl Trygve Kalleberg <karltk@gentoo.org>
# Copyright 2004 Gentoo Technologies, Inc.
# Distributed under the terms of the GNU General Public License v2
#
# $Header$

include ../../makedefs.mak

all:

dist:
	mkdir -p ../../$(distdir)/src/ego/
	cp Makefile AUTHORS README TODO ChangeLog ego ../../$(distdir)/src/ego/

install: all
	install -d $(docdir)/ego	
	install -m 0644 AUTHORS README ego $(docdir)/ego/

