# Copyright 2004 Karl Trygve Kalleberg <karltk@gentoo.org>
# Copyright 2004 Gentoo Technologies, Inc.
# Distributed under the terms of the GNU General Public License v2
#
# $Header$

include ../../makedefs.mak

all:
	echo "PIMPERNE (n.) One of those rubber nodules found on the underneath side of a lavatory seat."

dist:
	mkdir -p ../../$(distdir)/src/euse/
	cp Makefile AUTHORS ChangeLog euse euse.1 ../../$(distdir)/src/euse/

install:
	install -m 0755 euse $(bindir)/
	install -d $(docdir)/euse
	install -m 0644 TODO ChangeLog $(docdir)/euse/
	install -m 0644 euse.1 $(mandir)/
