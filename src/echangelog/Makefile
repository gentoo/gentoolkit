# Copyright 2004 Karl Trygve Kalleberg <karltk@gentoo.org>
# Copyright 2004 Gentoo Technologies, Inc.
# Distributed under the terms of the GNU General Public License v2
#
# $Header$

include ../../makedefs.mak

.PHONY: all test

all:

test:
	cd test; bash test.sh

dist:
	mkdir -p ../../$(distdir)/src/echangelog/test/templates
	cp Makefile AUTHORS README ChangeLog echangelog echangelog.1 ../../$(distdir)/src/echangelog/
	cp test/TEST.pm test/test.sh ../../$(distdir)/src/echangelog/test/
	cp test/templates/test.patch test/templates/vcstest-0.0.1.ebuild ../../$(distdir)/src/echangelog/test/templates

install: all
	install -m 0755 echangelog $(bindir)/
	install -d $(docdir)/echangelog	
	install -m 0644 AUTHORS README $(docdir)/echangelog/
	install -m 0644 echangelog.1 $(mandir)/
