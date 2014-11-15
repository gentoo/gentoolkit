# Copyright 2004 Karl Trygve Kalleberg <karltk@gentoo.org>
# Copyright 2004 Gentoo Technologies, Inc.
# Distributed under the terms of the GNU General Public License v2
#
# $Header$

include ../../makedefs.mak

.PHONY: all test

all:

clean:
	$(RM) -r test/tmp

test:
	cd test; sh test.sh

echangelog.1:
	pod2man echangelog > echangelog.1

dist: echangelog.1
	mkdir -p ../../$(DISTDIR)/src/echangelog/test/templates
	cp Makefile AUTHORS README ChangeLog echangelog echangelog.1 ../../$(DISTDIR)/src/echangelog/
	cp test/TEST.pm test/test.sh ../../$(DISTDIR)/src/echangelog/test/
	cp test/templates/test.patch test/templates/vcstest-0.0.1.ebuild ../../$(DISTDIR)/src/echangelog/test/templates

install: all echangelog.1
	install -m 0755 echangelog $(BINDIR)/
	install -d $(DOCDIR)/echangelog
	install -m 0644 AUTHORS README $(DOCDIR)/echangelog/
	install -m 0644 echangelog.1 $(MAN1DIR)/
