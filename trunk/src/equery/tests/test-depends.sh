#! /bin/bash
#
# Copyright (c) 2004, Karl Trygve Kalleberg <karltk@gentoo.org>
# Copyright (c) 2004, Gentoo Foundation
#
# Licensed under the GNU General Public License, v2

. common-functions.sh

tmpfile=$(tempfilename)

test_depends() {
#	equery skel gcc > ${tmpfile}

#	x=$(grep "app-shells/bash" ${tmpfile} | wc -l)
	
#	assert_eq ${FUNCNAME} ${x} 1
	
#	x=$(grep "virtual/libc" ${tmpfile} | wc -l)
#	assert_eq ${FUNCNAME} ${x} 1
}

# Run tests

#test_skel

rm -f ${tmpfile}