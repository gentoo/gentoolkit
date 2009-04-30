#! /bin/sh
#
# Copyright (c) 2004, Karl Trygve Kalleberg <karltk@gentoo.org>
# Copyright (c) 2004, Gentoo Foundation
#
# Licensed under the GNU General Public License, v2

. common-functions.sh

tmpfile=$(tempfilename)

test_equery_help() {
	equery --help > ${tmpfile}
	assert_samefile ${FUNCNAME} ${tmpfile} test-help.out

}

test_belongs_help() {
	equery belongs --help > ${tmpfile}
	assert_samefile ${FUNCNAME} ${tmpfile} test-belongs-help.out
}

test_changes_help() {
	equery changes --help > ${tmpfile}
	assert_samefile ${FUNCNAME} ${tmpfile} test-changes-help.out
}

test_check_help() {
	equery check --help > ${tmpfile}
	assert_samefile ${FUNCNAME} ${tmpfile} test-check-help.out
}

test_depends_help() {
	equery depends --help > ${tmpfile}
	assert_samefile ${FUNCNAME} ${tmpfile} test-depends-help.out
}

test_depgraph_help() {
	equery depgraph --help > ${tmpfile}
	assert_samefile ${FUNCNAME} ${tmpfile} test-depgraph-help.out
}

test_files_help() {
	equery files --help > ${tmpfile}
	assert_samefile ${FUNCNAME} ${tmpfile} test-files-help.out
}

test_glsa_help() {
	equery glsa --help > ${tmpfile}
	assert_samefile ${FUNCNAME} ${tmpfile} test-glsa-help.out
}

test_hasuses_help() {
	equery hasuses --help > ${tmpfile}
	assert_samefile ${FUNCNAME} ${tmpfile} test-hasuses-help.out
}

test_list_help() {
	equery list --help > ${tmpfile}
	assert_samefile ${FUNCNAME} ${tmpfile} test-list-help.out
}

test_size_help() {
	equery size --help > ${tmpfile}
	assert_samefile ${FUNCNAME} ${tmpfile} test-size-help.out
}

test_stats_help() {
	equery stats --help > ${tmpfile}
	assert_samefile ${FUNCNAME} ${tmpfile} test-stats-help.out
}

test_uses_help() {
	equery uses --help > ${tmpfile}
	assert_samefile ${FUNCNAME} ${tmpfile} test-uses-help.out
}

test_which_help() {
	equery which --help > ${tmpfile}
	assert_samefile ${FUNCNAME} ${tmpfile} test-which-help.out
}


# run tests

if [ "`hostname`" != "sky" ] ; then
	echo "Testing framework is beta and machine dependent; some tests will fail!"
fi

test_equery_help
test_belongs_help
test_check_help
test_changes_help
test_depends_help
test_depgraph_help
test_files_help
test_glsa_help
test_hasuses_help
test_list_help
test_size_help
test_stats_help
test_uses_help
test_which_help

rm -f *.tmp