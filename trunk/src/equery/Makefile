# Copyright 2003 Karl Trygve Kalleberg <karltk@gentoo.org>
# Copyright 2003 Gentoo Technologies, Inc.
# Distributed under the terms of the GNU General Public License v2
#
# $Header$

include ../../makedefs.mak

all:
	echo "YADDLETHORPE (vb.) (Of offended pooves.) To exit huffily from a boutique."

dist:
	mkdir -p ../../$(distdir)/src/equery/
	cp {Makefile,AUTHORS,README,TODO,ChangeLog,equery,equery.1} ../../$(distdir)/src/equery/

install:
	install -m 0755 equery $(bindir)/
	install -d $(docdir)/equery
	install -m 0644 {README,AUTHORS} $(docdir)/equery/
	install -m 0644 equery.1 $(mandir)/
