#! /bin/bash
#
# Copyright (c) 2004, Karl Trygve Kalleberg <karltk@gentoo.org>
# Copyright (c) 2004, Gentoo Foundation
#
# Licensed under the GNU General Public License, v2

. common-functions.sh

tmpfile=$(tempfilename)

test_list() {
	equery list > ${tmpfile}

# should test tty output as well
#	pkgs=$(cat ${tmpfile} | wc -l)
#	x=$(grep "[I--]" ${tmpfile} | wc -l)
#	assert_eq ${FUNCNAME} ${pkgs} ${x}
	
	x=$(grep "app-shells/bash" ${tmpfile} | wc -l)
	assert_ge ${FUNCNAME} $x 1
}

test_list_installed() {
	test_list
}

test_list_portage_tree() {
	equery list -I -p > ${tmpfile}
}

test_list_overlay_tree() {
	equery list -I -o > ${tmpfile}
}

# Run tests

test_list

rm -f ${tmpfile}