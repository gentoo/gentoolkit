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
	mkdir -p ../../$(distdir)/src/eviewcvs/
	cp Makefile AUTHORS README eviewcvs eviewcvs.pod eviewcvs.1 ../../$(distdir)/src/eviewcvs/

install: all
	install -m 0755 eviewcvs $(bindir)/
	install -d $(docdir)/eviewcvs	
	install -m 0644 AUTHORS README $(docdir)/eviewcvs/
	install -m 0644 eviewcvs.1 $(mandir)/

clean:
	$(RM) eviewcvs.1
