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
	mkdir -p ../../$(DISTDIR)/src/ekeyword
	cp Makefile AUTHORS README ChangeLog ekeyword ekeyword.1 ../../$(DISTDIR)/src/ekeyword/

install: all
	install -m 0755 ekeyword $(BINDIR)/
	install -d $(DOCDIR)/ekeyword
	install -m 0644 AUTHORS README ChangeLog $(DOCDIR)/ekeyword/
	install -m 0644 ekeyword.1 $(MAN1DIR)/

clean:
	$(RM) ekeyword.1
