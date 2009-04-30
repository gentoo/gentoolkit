#! /bin/bash
#
# Copyright (c) 2004, Karl Trygve Kalleberg <karltk@gentoo.org>
# Copyright (c) 2004, Gentoo Foundation
#
# Licensed under the GNU General Public License, v2

. common-functions.sh

tmpfile=$(tempfilename)

test_belongs() {
	equery belongs $(which gcc) > ${tmpfile}

	x=$(grep "gcc-config" ${tmpfile} | wc -l)
	
	assert_eq ${FUNCNAME} ${x} 1
}

# Run tests

test_belongs

rm -f ${tmpfile}