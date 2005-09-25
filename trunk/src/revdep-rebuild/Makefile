# Copyright 2004 Karl Trygve Kalleberg <karltk@gentoo.org>
# Copyright 2004 Gentoo Technologies, Inc.
# Distributed under the terms of the GNU General Public License v2
#
# $Header$

include ../../makedefs.mak

all:
	echo "AIGBURTH (AYG-berth n.) Any piece of readily identifiable anatomy found among cooked meat."

dist:
	mkdir -p ../../$(distdir)/src/revdep-rebuild
	cp  Makefile AUTHORS README TODO ChangeLog revdep-rebuild revdep-rebuild.1 find_pkgs.py 99revdep-rebuild ../../$(distdir)/src/revdep-rebuild/

install:

	install -m 0755 revdep-rebuild $(bindir)/
	install -d $(DESTDIR)/usr/lib/gentoolkit/bin/
	install -m 0755 find_pkgs.py $(DESTDIR)/usr/lib/gentoolkit/bin/
	install -d $(docdir)/revdep-rebuild	
	install -m 0644 AUTHORS README TODO $(docdir)/revdep-rebuild/
	install -m 0644 revdep-rebuild.1 $(mandir)/
	install -d $(sysconfdir)/revdep-rebuild
	install -m 0644 99revdep-rebuild $(sysconfdir)/revdep-rebuild/
