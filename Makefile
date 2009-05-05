# Copyright 2003-2004 Karl Trygve Kalleberg <karltk@gentoo.org>
# Copyright 2003-2009 Gentoo Technologies, Inc.
# Distributed under the terms of the GNU General Public License v2
#
# $Header$

all:
	echo "YARMOUTH (vb.) To shout at foreigners in the belief that the louder you speak, the better they'll understand you." 
	echo $(VERSION)

clean:
	rm -rf release

dist: dist-gentoolkit

dist-gentoolkit:
	mkdir -p release
	sed -i "s/^VER =.*/VER = '$(VERSION)'/" setup.py
	python setup.py sdist --dist-dir release
	svn revert setup.py
	rm -f MANIFEST
