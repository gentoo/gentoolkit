# Copyright 1999-2009 Gentoo Foundation
# Distributed under the terms of the GNU General Public License v2
# $Header: $

include ../../makedefs.mak

.PHONY: all

all:

dist:
	mkdir -p ../../$(DISTDIR)/src/eshowkw/
	cp Makefile eshowkw eshowkw.1 ../../$(DISTDIR)/src/eshowkw/

install: all
	install -m 0755 eshowkw $(BINDIR)/
	install -m 0644 eshowkw.1 $(MAN1DIR)/

