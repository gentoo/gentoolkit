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

test:
	make -C src/echangelog test

clean:
	rm -rf release/*

dist:
	echo "Error: Must use either dist-gentoolkit or dist-gentoolkit-dev"
	exit 1

dist-gentoolkit-dev:
	mkdir -p release/gentoolkit-dev-$(VERSION)$(RELEASE_TAG)
	for x in ekeyword echangelog ego ebump gensync eviewcvs ; do \
		( cd src/$$x ; $(MAKE) distdir=release/gentoolkit-dev-$(VERSION)$(RELEASE_TAG) dist ) \
	done
	cp Makefile AUTHORS README README.Developer TODO COPYING NEWS ChangeLog release/gentoolkit-dev-$(VERSION)$(RELEASE_TAG)/
	cat makedefs.mak | \
		sed "s/^VERSION=.*/VERSION=$(VERSION)/" | \
		sed "s/^RELEASE_TAG=.*/RELEASE_TAG=$(RELEASE_TAG)/" | \
		sed "s:^docdir=.*:docdir=\$$(DESTDIR)/usr/share/doc/gentoolkit-dev-\$$(VERSION)\$$(RELEASE_TAG):" \
		> release/gentoolkit-dev-$(VERSION)$(RELEASE_TAG)/makedefs.mak
	( cd release ; tar zcf gentoolkit-dev-$(VERSION)$(RELEASE_TAG).tar.gz gentoolkit-dev-$(VERSION)$(RELEASE_TAG)/ )

install:
	echo "Error: Must use either install-gentoolkit or install-gentoolkit-dev"
	exit 1

# FIXME: If run from the CVS tree, the documentation will be installed in
#        $(DESTDIR)/usr/share/doc/gentoolkit-$(VERSION), not gentoolkit-dev-$(VERSION)
install-gentoolkit-dev:

	install -d $(docdir)
	install -d $(bindir)
	install -d $(mandir)

	install -m 0644 AUTHORS ChangeLog COPYING NEWS README README.Developer TODO $(docdir)/

	for x in ekeyword echangelog ego ebump eviewcvs ; do \
		( cd src/$$x ; $(MAKE) DESTDIR=$(DESTDIR) install ) \
	done
