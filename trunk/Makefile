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

dist-gentoolkit:
	mkdir -p release/gentoolkit-$(VERSION)$(RELEASE_TAG)
	rm -rf release/gentoolkit-$(VERSION)$(RELEASE_TAG)/
	for x in eclean equery eread etcat euse qpkg gentoolkit revdep-rebuild glsa-check genpkgindex epkginfo; do \
		( cd src/$$x ; $(MAKE) distdir=release/gentoolkit-$(VERSION)$(RELEASE_TAG) dist ) \
	done
	cp Makefile AUTHORS README TODO COPYING NEWS ChangeLog release/gentoolkit-$(VERSION)$(RELEASE_TAG)/
	cp src/99gentoolkit-env release/gentoolkit-$(VERSION)$(RELEASE_TAG)/src/
	cat makedefs.mak | \
		sed "s/^VERSION=.*/VERSION=$(VERSION)/" | \
		sed "s/^RELEASE_TAG=.*/RELEASE_TAG=$(RELEASE_TAG)/" \
		> release/gentoolkit-$(VERSION)$(RELEASE_TAG)/makedefs.mak
	( cd release ; tar zcf gentoolkit-$(VERSION)$(RELEASE_TAG).tar.gz gentoolkit-$(VERSION)$(RELEASE_TAG)/ )

install:
	echo "Err0r: Must use either install-gentoolkit or install-gentoolkit-dev"
	exit 1

install-gentoolkit:

	install -d $(docdir)
	install -d $(bindir)
	install -d $(sbindir)
	install -d $(mandir)
	install -d $(sysconfdir)/env.d

	install -m 0644 AUTHORS ChangeLog COPYING NEWS README TODO $(docdir)/
	install -m 0644 src/99gentoolkit-env $(sysconfdir)/env.d/

	for x in eclean equery eread etcat euse qpkg gentoolkit revdep-rebuild glsa-check genpkgindex epkginfo; do \
		( cd src/$$x ; $(MAKE) DESTDIR=$(DESTDIR) install )  \
	done


# FIXME: If run from the CVS tree, the documentation will be installed in
#        $(DESTDIR)/usr/share/doc/gentoolkit-$(VERSION), not gentoolkit-dev-$(VERSION)
install-gentoolkit-dev:

	install -d $(docdir)
	install -d $(bindir)
	install -d $(mandir)

	install -m 0644 AUTHORS ChangeLog COPYING NEWS README README.Developer TODO $(docdir)/

	for x in ekeyword echangelog ego ebump gensync eviewcvs ; do \
		( cd src/$$x ; $(MAKE) DESTDIR=$(DESTDIR) install ) \
	done
