# Copyright 2004 Karl Trygve Kalleberg <karltk@gentoo.org>
# Copyright 2004 Gentoo Technologies, Inc.
# Distributed under the terms of the GNU General Public License v2
#
# $Header$

include ../../makedefs.mak

all:
	echo "DUNCRAGGON (n.) The name of Charles Bronson's retirement cottage."

dist:
	mkdir -p ../../$(distdir)/src/echangelog/
	cp {AUTHORS,README,TODO,ChangeLog,echangelog,echangelog.1} ../../$(distdir)/src/echangelog/

install:
	install -m 0755 echangelog $(bindir)/
	install -d $(docdir)/echangelog	
	install -m 0644 {AUTHORS,README} $(docdir)/echangelog/
	install -m 0644 echangelog.1 $(mandir)/
