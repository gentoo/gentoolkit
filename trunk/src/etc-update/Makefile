# Copyright 2004 Karl Trygve Kalleberg <karltk@gentoo.org>
# Copyright 2004 Gentoo Technologies, Inc.
# Distributed under the terms of the GNU General Public License v2
#
# $Header$

include ../../makedefs.mak

all:
	echo "PAPPLE (vb.) To do what babies do to soup with their spoons."

dist:
	mkdir -p ../../$(distdir)/src/etc-update
	cp {Makefile,AUTHORS,README,TODO,ChangeLog,etc-update,etc-update.1} ../../$(distdir)/src/etc-update/

install:
	install -m 0755 etc-update $(bindir)/
	install -d $(docdir)/etc-update
	install -m 0644 {AUTHORS,ChangeLog,README} $(docdir)/etc-update/
	install -m 0644 etc-update.1 $(mandir)/
