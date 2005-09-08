# Copyright 2004 Karl Trygve Kalleberg <karltk@gentoo.org>
# Copyright 2004 Gentoo Technologies, Inc.
# Distributed under the terms of the GNU General Public License v2
#
# $Header$

include ../../makedefs.mak

all:

dist:
	mkdir -p ../../$(distdir)/src/eclean
	cp eclean eclean.1 Makefile *.exclude ../../$(distdir)/src/eclean
	cp AUTHORS THANKS TODO ChangeLog ../../$(distdir)/src/eclean

install:
	install -m 0755 eclean $(bindir)/
	ln -sf eclean $(bindir)/eclean-pkg
	ln -sf eclean $(bindir)/eclean-dist
	install -d $(sysconfdir)/eclean
	install -m 0644 distfiles.exclude packages.exclude $(sysconfdir)/eclean/
	install -d $(docdir)/eclean
	install -m 0644 AUTHORS THANKS TODO ChangeLog $(docdir)/eclean/
	install -m 0644 eclean.1 $(mandir)/
