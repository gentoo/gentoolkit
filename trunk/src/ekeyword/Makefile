# Copyright 2004 Karl Trygve Kalleberg <karltk@gentoo.org>
# Copyright 2004 Gentoo Technologies, Inc.
# Distributed under the terms of the GNU General Public License v2
#
# $Header$

include ../../makedefs.mak

%.1 : %.pod
	pod2man $< > $@

.PHONY: all
all: ekeyword.1

dist: ekeyword.1
	mkdir -p ../../$(distdir)/src/ekeyword
	cp Makefile AUTHORS README TODO ChangeLog ekeyword ekeyword.1 ../../$(distdir)/src/ekeyword/

install: all
	install -m 0755 ekeyword $(bindir)/
	install -d $(docdir)/ekeyword
	install -m 0644 AUTHORS README TODO ChangeLog $(docdir)/ekeyword/
	install -m 0644 ekeyword.1 $(mandir)/

