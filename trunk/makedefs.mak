# Copyright 2003 Karl Trygve Kalleberg <karltk@gentoo.org>
# Copyright 2003 Gentoo Technologies, Inc.
# Distributed under the terms of the GNU General Public License v2
#
# $Header$

# Override this on command line when making a release, ie 'dist'

VERSION=9.9.9
RELEASE_TAG=
# python-config is not installed on all arches Bug #113386
#PYVERSION="`python-config | sed 's/-l//' | sed 's/ -lm.*//'`"
PYVERSION="`LC_COLLATE=C; python -V 2>&1 | tr '[:upper:]' '[:lower:]' | sed -e 's/ //g;s/\([0-9]\.[0-9]\)\.[0-9]/\1/'`"
DESTDIR=

docdir=$(DESTDIR)/usr/share/doc/gentoolkit-$(VERSION)$(RELEASE_TAG)
bindir=$(DESTDIR)/usr/bin
sbindir=$(DESTDIR)/usr/sbin
mandir=$(DESTDIR)/usr/share/man/man1
sysconfdir=$(DESTDIR)/etc
