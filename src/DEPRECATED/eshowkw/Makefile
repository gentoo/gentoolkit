# Copyright 1999-2009 Gentoo Foundation
# Distributed under the terms of the GNU General Public License v2
# $Header: $

include ../../makedefs.mak

.PHONY: all

all:

dist:
	mkdir -p ../../$(distdir)/src/eshowkw/
	cp Makefile eshowkw eshowkw.1 ../../$(distdir)/src/eshowkw/

install: all
	install -m 0755 eshowkw $(bindir)/
	install -m 0644 eshowkw.1 $(mandir)/

