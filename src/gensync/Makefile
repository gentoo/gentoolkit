# Copyright 2004 Karl Trygve Kalleberg <karltk@gentoo.org>
# Copyright 2004 Gentoo Technologies, Inc.
# Distributed under the terms of the GNU General Public License v2
#
# $Header$

include ../../makedefs.mak

.PHONY: all
all: 

dist: 
	mkdir -p ../../$(distdir)/src/gensync/
	cp Makefile AUTHORS README TODO ChangeLog \
	   gensync gensync.1 gensync.conf \
	   bmg-main.syncsource bmg-gnome-current.syncsource \
	    ../../$(distdir)/src/gensync/

install: all
	install -d $(docdir)/deprecated/gensync
	install -m 0755 gensync $(docdir)/deprecated/gensync/
	install -m 0644 AUTHORS README TODO ChangeLog $(docdir)/deprecated/gensync/
	install -m 0644 gensync.1 $(docdir)/deprecated/gensync/
	install -m 0644 gensync.conf bmg-main.syncsource bmg-gnome-current.syncsource $(docdir)/deprecated/gensync/
