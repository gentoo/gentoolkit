#! /bin/bash
#
# Copyright (c) 2004, Karl Trygve Kalleberg <karltk@gentoo.org>
# Copyright (c) 2004, Gentoo Foundation
#
# Licensed under the GNU General Public License, v2

function tempfilename() {
	fn=$(date "+%s")
	if [ ! -f ${fn}.tmp ] ; then 
		echo ${fn}.tmp
	fi
}

function report_pass() {
	printf "%-40s - passed\n" ${1}
}

function report_failure() {
		printf "%-40s - FAILED!\n" ${1}
}

function assert_samefile() {
	diff $2 $3 && report_pass $1 || report_failure $1
}

function assert_eq() {
	if [ $2 -eq $3 ] ; then
		report_pass $1
	else
		printf "FAIL: $2 ! -eq $3\n"	
		report_failure $1
	fi
}

function assert_ge() {
	if [ $2 -ge $3 ] ; then
		report_pass $1
	else
		printf "FAIL: $2 ! -ge $3\n"
		report_failure $1
	fi
}