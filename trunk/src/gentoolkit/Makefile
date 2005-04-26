# Copyright 2004 Karl Trygve Kalleberg <karltk@gentoo.org>
# Copyright 2004 Gentoo Technologies, Inc.
# Distributed under the terms of the GNU General Public License v2
#
# $Header$

include ../../makedefs.mak

all:
	echo "LISTOWEL (n.) The small mat on the bar designed to be more absorbent than the bar, but not as absorbent as your elbows."

dist:
	mkdir -p ../../${distdir}/src/gentoolkit
	cp Makefile AUTHORS README ChangeLog TODO errors.py package.py helpers.py pprinter.py __init__.py ../../${distdir}/src/gentoolkit/

install:
	install -d $(docdir)/gentoolkit
	install -m 0644 AUTHORS README TODO $(docdir)/gentoolkit/
	install -d $(DESTDIR)/usr/lib/gentoolkit/pym/gentoolkit
	install -m 0644 package.py pprinter.py helpers.py errors.py $(DESTDIR)/usr/lib/gentoolkit/pym/gentoolkit/
	install -m 0644 __init__.py $(DESTDIR)/usr/lib/gentoolkit/pym/gentoolkit/
	
