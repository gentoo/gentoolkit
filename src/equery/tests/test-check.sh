#! /bin/bash
#
# Copyright (c) 2004, Karl Trygve Kalleberg <karltk@gentoo.org>
# Copyright (c) 2004, Gentoo Foundation
#
# Licensed under the GNU General Public License, v2

. common-functions.sh

tmpfile=$(tempfilename)

test_check() {
	equery check gcc > ${tmpfile}

	x=$(grep "sys-devel/gcc" ${tmpfile} | wc -l)
	
	assert_ge ${FUNCNAME} ${x} 1
	
	x=$(egrep "[0-9]+ out of [0-9]+" ${tmpfile} | wc -l)
	assert_ge ${FUNCNAME} ${x} 1
}

test_check_permissions() {
	equery check sudo > ${tmpfile}

	x=$(grep "app-admin/sudo" ${tmpfile} | wc -l)
	
	assert_ge ${FUNCNAME} ${x} 1
	
	x=$(egrep "[0-9]+ out of [0-9]+" ${tmpfile} | wc -l)
	assert_ge ${FUNCNAME} ${x} 1
}

# Run tests

test_check
test_check_permissions

rm -f ${tmpfile}
