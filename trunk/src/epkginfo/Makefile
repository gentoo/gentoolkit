# Copyright 2007 Gentoo Foundation.
# Distributed under the terms of the GNU General Public License v2
#
# $Header$

include ../../makedefs.mak

all:
	echo "ABWONG (AB-wong vb.) To bounce cheerfully on a bed."

dist:
	mkdir -p ../../$(distdir)/src/epkginfo
	cp Makefile epkginfo ../../$(distdir)/src/epkginfo/

install:
	install -d $(DESTDIR)/usr/lib/gentoolkit/bin/
	install -m 0755 epkginfo $(DESTDIR)/usr/lib/gentoolkit/bin/
