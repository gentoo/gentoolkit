VERSION=0.2.0
PYVERSION="`python-config | sed 's/-l//' | sed 's/ -lm.*//'`"
DESTDIR=
docdir=$(DESTDIR)/usr/share/doc/gentoolkit-$(VERSION)
bindir=$(DESTDIR)/usr/bin
sbindir=$(DESTDIR)/usr/sbin
mandir=$(DESTDIR)/usr/share/man/man1

all:
	echo $(PYVERSION)
	echo $(VERSION)
	echo $(docdir)
	echo $(bindir)
	echo $(sbindir)
	echo $(mandir)
			
install:

	install -d $(docdir)
	install -d $(bindir)
	install -d $(sbindir)
	install -d $(mandir)
			
	install -m 0644 {AUTHORS,ChangeLog,COPYING,NEWS,README,TODO} $(docdir)/

	install -m 0755 src/gentool/gentool $(bindir)/
	install -d $(docdir)/gentool
	install -m 0644 src/gentool/{README,AUTHORS} $(docdir)/gentool/
	install -m 0644 src/gentool/gentool.1 $(mandir)/
	
	install -m 0755 src/etcat/etcat $(bindir)/
	install -d $(docdir)/etcat
	install -m 0644 src/etcat/{README,AUTHORS} $(docdir)/etcat/
	install -m 0644 src/etcat/etcat.1 $(mandir)/

	install -m 0755 src/qpkg/qpkg $(bindir)/
	install -d $(docdir)/qpkg	
	install -m 0644 src/qpkg/{README,AUTHORS,ChangeLog} $(docdir)/qpkg/
	install -m 0644 src/qpkg/qpkg.1 $(mandir)/
	
	install -m 0755 src/etc-update/etc-update $(bindir)/
	install -d $(docdir)/etc-update
	install -m 0644 src/etc-update/{AUTHORS,ChangeLog,README} $(docdir)/etc-update/
	install -m 0644 src/etc-update/etc-update.1 $(mandir)/
	
	install -m 0755 src/ekeyword/ekeyword $(bindir)/
	install -d $(docdir)/ekeyword
	install -m 0644 src/ekeyword/{AUTHORS,README} $(docdir)/ekeyword/
	install -m 0644 src/ekeyword/ekeyword.1 $(mandir)/

	install -m 0755 src/echangelog/echangelog $(bindir)/
	install -d $(docdir)/echangelog	
	install -m 0644 src/echangelog/{AUTHORS,README} $(docdir)/echangelog/
	install -m 0644 src/echangelog/echangelog.1 $(mandir)/
        
	install -m 0755 src/revdep-rebuild/revdep-rebuild $(sbindir)/
	install -d $(docdir)/revdep-rebuild	
	install -m 0644 src/revdep-rebuild/{AUTHORS,README,TODO} $(docdir)/revdep-rebuild/
	install -m 0644 src/revdep-rebuild/revdep-rebuild.1 $(mandir)/
