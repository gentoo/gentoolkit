# Copyright 2004 Karl Trygve Kalleberg <karltk@gentoo.org>
# Copyright 2004 Gentoo Technologies, Inc.
# Distributed under the terms of the GNU General Public License v2
#
# $Header$

include ../../makedefs.mak

all:
	echo "BOTOLPHS Huge benign tumors which archdeacons and old chemistry teachers affect to wear on the sides of their noses."

dist:
	mkdir -p ../../$(distdir)/src/old-scripts/
	cp dep-clean{,.1} ../../$(distdir)/src/old-scripts/
	cp pkg-clean{,.1} ../../$(distdir)/src/old-scripts/
	cp ewhich{,.1} ../../$(distdir)/src/old-scripts/
	cp mkebuild{,.1} ../../$(distdir)/src/old-scripts/
	cp pkg-size{,.1} ../../$(distdir)/src/old-scripts/

install:
	install -m 0755 dep-clean $(bindir)/
	install -m 0755 pkg-clean $(bindir)/
	install -m 0755 ewhich $(bindir)/
	install -m 0755 mkebuild $(bindir)/
	install -m 0755 pkg-size $(bindir)/

	install -m 0644 dep-clean.1 $(mandir)/
	install -m 0644 pkg-clean.1 $(mandir)/
	install -m 0644 ewhich.1 $(mandir)/
	install -m 0644 mkebuild.1 $(mandir)/
	install -m 0644 pkg-size.1 $(mandir)/
