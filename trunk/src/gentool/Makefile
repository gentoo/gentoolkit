# Copyright 2003 Karl Trygve Kalleberg <karltk@gentoo.org>
# Copyright 2003 Gentoo Technologies, Inc.
# Distributed under the terms of the GNU General Public License v2
#
# $Header$

include ../../makedefs.mak

all:
	echo "YADDLETHORPE (vb.) (Of offended pooves.) To exit huffily from a boutique."

dist:
	mkdir -p ../../$(distdir)/src/gentool/
	cp {AUTHORS,README,TODO,ChangeLog,gentool,gentool.1} ../../$(distdir)/src/gentool/

install:
	install -m 0755 gentool $(bindir)/
	install -d $(docdir)/gentool
	install -m 0644 {README,AUTHORS} $(docdir)/gentool/
	install -m 0644 gentool.1 $(mandir)/
