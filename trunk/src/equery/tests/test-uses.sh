#! /bin/bash
#
# Copyright (c) 2004, Karl Trygve Kalleberg <karltk@gentoo.org>
# Copyright (c) 2004, Gentoo Foundation
#
# Licensed under the GNU General Public License, v2

. common-functions.sh

tmpfile=$(tempfilename)

test_uses() {
	equery uses gcc > ${tmpfile}

	x=$(grep "static" ${tmpfile} | wc -l)
	
	assert_eq ${FUNCNAME} ${x} 1
	
	x=$(cat ${tmpfile} | wc -l)
	assert_ge ${FUNCNAME} $x 7
}

test_uses_all() {
	equery uses -a uclibc > ${tmpfile}

	x=$(grep "static" ${tmpfile} | wc -l)
	assert_eq ${FUNCNAME} ${pkgs} ${x]
	
	x=$(cat ${tmpfile} | wc -l)
	assert_ge ${FUNCNAME} $x 5
	
}

# Run tests

test_uses
test_uses_all

rm -f ${tmpfile}