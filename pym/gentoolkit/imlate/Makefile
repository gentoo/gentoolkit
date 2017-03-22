# Copyright 1999-2009 Gentoo Foundation
# Distributed under the terms of the GNU General Public License v2
# $Header: $

include ../../makedefs.mak

.PHONY: all

all:

dist:
	mkdir -p ../../$(DISTDIR)/src/imlate/
	cp Makefile imlate imlate.1 ../../$(DISTDIR)/src/imlate/

install: all
	install -m 0755 imlate $(BINDIR)/
	install -m 0644 imlate.1 $(MAN1DIR)/

