#! /bin/bash
#
# Copyright (c) 2004, Karl Trygve Kalleberg <karltk@gentoo.org>
# Copyright (c) 2004, Gentoo Foundation
#
# Licensed under the GNU General Public License, v2

. common-functions.sh

tmpfile=$(tempfilename)

test_which() {
	file=$(equery which gcc)
	
	assert_exists ${FUNCNAME} ${file}
}

# Run tests

test_which

rm -f ${tmpfile}