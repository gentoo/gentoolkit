# Copyright 2005 Gentoo Technologies, Inc.
# Distributed under the terms of the GNU General Public License v2
#
# $Header$

include ../../makedefs.mak

%.1 : %.pod
	pod2man $< > $@

.PHONY: all
all: eviewcvs.1

dist: eviewcvs.1
	mkdir -p ../../$(DISTDIR)/src/eviewcvs/
	cp Makefile AUTHORS README eviewcvs eviewcvs.pod eviewcvs.1 ../../$(DISTDIR)/src/eviewcvs/

install: all
	install -m 0755 eviewcvs $(BINDIR)/
	install -d $(DOCDIR)/eviewcvs
	install -m 0644 AUTHORS README $(DOCDIR)/eviewcvs/
	install -m 0644 eviewcvs.1 $(MAN1DIR)/

clean:
	$(RM) eviewcvs.1
