# Copyright 2003-2004 Karl Trygve Kalleberg <karltk@gentoo.org>
# Copyright 2003-2004 Gentoo Technologies, Inc.
# Distributed under the terms of the GNU General Public License v2
#
# $Header$

include makedefs.mak


all:
	echo "YARMOUTH (vb.) To shout at foreigners in the belief that the louder you speak, the better they'll understand you." 
	echo $(PYVERSION)
	echo $(VERSION)
	echo $(docdir)
	echo $(bindir)
	echo $(sbindir)
	echo $(mandir)

dist:
	echo "Err0r: Must use either dist-gentoolkit or dist-gentoolkit-dev"

dist-gentoolkit-dev:
	echo "You wish..."

dist-gentoolkit:
	mkdir -p dist/gentoolkit-$(VERSION)
	for x in gentool etcat euse qpkg revdep-rebuild old-scripts ; do \
		( cd src/$$x ; make distdir=dist/gentoolkit-$(VERSION) dist ) \
	done
	cp {Makefile,AUTHORS,README,TODO,COPYING,NEWS,ChangeLog} dist/gentoolkit-$(VERSION)/
	cat makedefs.mak | sed "s/^VERSION=.*/VERSION=$(VERSION)/" > dist/gentoolkit-$(VERSION)/makedefs.mak
	( cd dist ; tar zcf gentoolkit-$(VERSION).tar.gz gentoolkit-$(VERSION)/ )

install:
	echo "Err0r: Must use either install-gentoolkit or install-gentoolkit-dev"


install-gentoolkit:

	install -d $(docdir)
	install -d $(bindir)
	install -d $(sbindir)
	install -d $(mandir)

	install -m 0644 {AUTHORS,ChangeLog,COPYING,NEWS,README,TODO} $(docdir)/

	for x in gentool etcat euse qpkg revdep-rebuild old-scripts ; do \
		( cd src/$$x ; make DESTDIR=$(DESTDIR) install )  \
	done

install-gentoolkit-dev:

# FIXME: we override the docdir for the -dev package, should be prettier
	docdir=$(DESTDIR)/usr/share/doc/gentoolkit-dev-$(VERSION)

	install -d $(docdir)
	install -d $(bindir)
	install -d $(sbindir)
	install -d $(mandir)

	install -m 0644 {AUTHORS,ChangeLog,COPYING,NEWS,README,README.Developer,TODO} $(docdir)/

	for x in ekeyword echangelog ; do
		( cd src/$(x) ; make DESTDIR=$(DESTDIR) install ) 
