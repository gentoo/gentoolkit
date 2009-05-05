# Copyright 2004 Karl Trygve Kalleberg <karltk@gentoo.org>
# Copyright 2004 Gentoo Technologies, Inc.
# Distributed under the terms of the GNU General Public License v2
#
# $Header$

include ../../makedefs.mak

all:
	echo "ABWONG (AB-wong vb.) To bounce cheerfully on a bed."

dist:
	mkdir -p ../../$(distdir)/src/genpkgindex
	cp Makefile genpkgindex genpkgindex.1 ../../$(distdir)/src/genpkgindex/

install:
	install -m 0755 genpkgindex $(bindir)/
	install -m 0644 genpkgindex.1 $(mandir)/
