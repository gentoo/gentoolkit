#! /bin/bash
#
# Copyright (c) 2004, Karl Trygve Kalleberg <karltk@gentoo.org>
# Copyright (c) 2004, Gentoo Foundation
#
# Licensed under the GNU General Public License, v2

. common-functions.sh

tmpfile=$(tempfilename)

strip_versioned_files() {
	grep -v "/usr/share/doc"
}

test_files() {
	equery files bash > ${tmpfile}

	x=$(grep man ${tmpfile} | wc -l)
	assert_ge ${FUNCNAME} $x 5
	
	x=$(cat ${tmpfile} | wc -l)
	assert_ge ${FUNCNAME} $x 25
}

test_files_timestamp() {
	equery files --timestamp bash > ${tmpfile}
}

test_files_md5sum() {
	equery files --md5sum bash > ${tmpfile}
}

test_files_type() {

	equery files --type bash > ${tmpfile}

	x=$(grep "file.*/bin/bash$" ${tmpfile} | wc -l)
	assert_eq ${FUNCNAME} $x 1
	
	x=$(grep "symlink.*/bin/rbash" ${tmpfile} | wc -l)
	assert_eq ${FUNCNAME} $x 1
	
	x=$(grep "dir.*/usr/share/man" ${tmpfile} | wc -l)
	assert_ge ${FUNCNAME} $x 1 	
}

# Run tests

test_files
test_files_timestamp
test_files_md5sum
test_files_type

rm ${tmpfile}