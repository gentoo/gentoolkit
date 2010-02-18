# Copyright 2004 Karl Trygve Kalleberg <karltk@gentoo.org>
# Copyright 2004 Gentoo Technologies, Inc.
# Distributed under the terms of the GNU General Public License v2
#
# $Header$

include ../../makedefs.mak

all:
	echo "HATHERSAGE (n.) The tiny snippets of beard which coat the inside of a washbasin after shaving in it."

dist:
	mkdir -p ../../${distdir}/src/qpkg
	cp Makefile README AUTHORS ChangeLog TODO qpkg qpkg.1 ../../${distdir}/src/qpkg/

install:
	install -d $(docdir)/deprecated/qpkg
	install -m 0755 qpkg $(docdir)/deprecated/qpkg/
	install -m 0644 qpkg.1 README AUTHORS ChangeLog $(docdir)/deprecated/qpkg/
