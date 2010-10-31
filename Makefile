# Copyright 1999-2009 Gentoo Foundation
# Distributed under the terms of the GNU General Public License v2
# $Header: $

include makedefs.mak

TOOLS=ebump echangelog ekeyword eviewcvs imlate
RELEASE="gentoolkit-dev-$(VERSION)$(RELEASE_TAG)"

all:
	@echo "YARMOUTH (vb.) To shout at foreigners in the belief that the louder you speak, the better they'll understand you." 
	@echo "PYVERSION=$(PYVERSION)"
	@echo "VERSION=$(VERSION)"
	@echo "docdir=$(docdir)"
	@echo "bindir=$(bindir)"
	@echo "sbindir=$(sbindir)"
	@echo "mandir=$(mandir)"

# use $(TOOLS) if we have more than one test
test:
	$(MAKE) -C src/echangelog test

clean:
	rm -rf release/
	@for tool in $(TOOLS); do \
		( $(MAKE) -C src/$${tool} clean ) \
	done

dist:
	mkdir -p release/gentoolkit-dev-$(VERSION)$(RELEASE_TAG)
	@for tool in $(TOOLS); do \
		( $(MAKE) -C src/$${tool} distdir=release/$(RELEASE) dist ) \
	done

	cp Makefile AUTHORS README README.Developer TODO COPYING NEWS ChangeLog release/$(RELEASE)/

	@sed -e "s/^VERSION=.*/VERSION=$(VERSION)/" \
		-e "s/^RELEASE_TAG=.*/RELEASE_TAG=$(RELEASE_TAG)/" \
		makedefs.mak > release/$(RELEASE)/makedefs.mak

	( cd release ; tar zcf $(RELEASE).tar.gz $(RELEASE)/ )

install: install-gentoolkit-dev

install-gentoolkit-dev:
	install -d $(docdir)
	install -d $(bindir)
	install -d $(mandir)

	install -m 0644 AUTHORS ChangeLog COPYING NEWS README README.Developer TODO $(docdir)/

	@for tool in $(TOOLS); do \
		( $(MAKE) -C src/$${tool} DESTDIR=$(DESTDIR) install ) \
	done
