# Copyright 2003 Karl Trygve Kalleberg <karltk@gentoo.org>
# Copyright 2003 Gentoo Technologies, Inc.
# Distributed under the terms of the GNU General Public License v2
#
# $Header$

include ../../makedefs.mak

all:
	echo "YADDLETHORPE (vb.) (Of offended pooves.) To exit huffily from a boutique."

dist:
	mkdir -p ../../$(distdir)/src/glsa-check/
	cp Makefile glsa.py glsa-check ../../$(distdir)/src/glsa-check/

install:
	install -m 0755 glsa-check $(bindir)/
	install -m 0644 glsa.py $(DESTDIR)/usr/lib/gentoolkit/pym/
