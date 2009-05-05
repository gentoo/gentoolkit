# Copyright 2006 Gentoo Technologies, Inc.
# Distributed under the terms of the GNU General Public License v2
#
# $Header$

include ../../makedefs.mak

all:
	echo "ELY (n.) The first, tiniest inkling you get that something, somewhere, has gone terribly wrong."

dist:
	mkdir -p ../../$(distdir)/src/eread
	cp AUTHORS Makefile eread eread.1 ../../$(distdir)/src/eread/

install:

	install -m 0755 eread $(bindir)/
	install -d $(docdir)/eread
	install -m 0644 AUTHORS $(docdir)/eread/
	install -m 0644 eread.1 $(mandir)/
