# Copyright 1999-2009 Gentoo Foundation
# Distributed under the terms of the GNU General Public License v2
# $Header: $

# Override this on command line when making a release, ie 'dist'
VERSION ?= 9.9.9
RELEASE_TAG ?=
RELEASE ?= "gentoolkit-dev-$(VERSION)$(RELEASE_TAG)"

# python-config is not installed on all arches Bug #113386
PYVERSION ?= "`LC_COLLATE=C; python -V 2>&1 | tr '[:upper:]' '[:lower:]' | sed -e 's/ //g;s/\([0-9]\.[0-9]\)\.[0-9]/\1/'`"
DESTDIR ?=

PREFIX ?= /usr
DOCDIR ?= $(DESTDIR)$(PREFIX)/share/doc/gentoolkit-dev-$(VERSION)$(RELEASE_TAG)
BINDIR ?= $(DESTDIR)$(PREFIX)/bin
SBINDIR ?= $(DESTDIR)$(PREFIX)/sbin
MANDIR ?= $(DESTDIR)$(PREFIX)/share/man
MAN1DIR ?= $(MANDIR)/man1
SYSCONFDIR ?= $(DESTDIR)/etc

# skeletons
all:
clean:
