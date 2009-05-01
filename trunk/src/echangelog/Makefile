# Copyright 2004 Karl Trygve Kalleberg <karltk@gentoo.org>
# Copyright 2004 Gentoo Technologies, Inc.
# Distributed under the terms of the GNU General Public License v2
#
# $Header$

include ../../makedefs.mak

#%.1 : %.pod
#	pod2man $< > $@

.PHONY: all

#all: echangelog.1
all:

#dist: echangelog.1
dist:
	mkdir -p ../../$(distdir)/src/echangelog/
	cp Makefile AUTHORS README TODO ChangeLog echangelog echangelog.pod echangelog.1 ../../$(distdir)/src/echangelog/

install: all
	install -m 0755 echangelog $(bindir)/
	install -d $(docdir)/echangelog	
	install -m 0644 AUTHORS README $(docdir)/echangelog/
	install -m 0644 echangelog.1 $(mandir)/
