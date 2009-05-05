# Copyright 2007 Gentoo Foundation.
# Distributed under the terms of the GNU General Public License v2
#
# $Header$

include ../../makedefs.mak

all:
	echo "CLIXBY (adj.) Politely rude. Bliskly vague. Firmly uninformative."

dist:
	mkdir -p ../../$(distdir)/src/epkginfo
	cp Makefile epkginfo epkginfo.1 ../../$(distdir)/src/epkginfo/

install:
	install -m 0755 epkginfo $(bindir)/
	install -m 0644 epkginfo.1 $(mandir)/
