#!/bin/sh

# Load functions.sh
. "/etc/init.d/functions.sh"

SUPPORTED_VCS="cvs svn git"
VCSTEST="echangelog-test/vcstest"
_ROOT=$(pwd)

export ECHANGELOG_USER="Just a test <echangelogtest@gentoo.org>"

MD5_INIT="21ac109c53cf02378593a4f613b2bb55"
MD5_PATCH="f3fa1cacae3bf51d6188278e6a5fd0c6"
MD5_REVBUMP="e474aa136f06e2a001320240b2ae92bd"
MD5_COPYRIGHT="9ce45576db5489c4f109ed9ef9ffe05e"
MD5_OBSOLETE="f0079450e03e69741502776a6b8138dc"
MD5_FINAL="a3954786368fd92d8466bc65cbf689fc"

md5() {
	local fname=$1
	echo $(md5sum ${fname} | awk '{ print $1 }')
}

ech() {
	local bin=$1
	shift
	local msg="${*}"

	perl -I$(dirname $(dirname ${bin})) $bin $msg
}

make_test() {
	local root=$1
	local vcs=$2

	local echangelog="${root}/tmp/echangelog"
	local tmp="${root}/tmp/${vcs}"
	local template="${root}/templates"

	cd $root
	mkdir -p ${tmp}
	cd ${tmp}

	[ "${vcs}" = "cvs" ] && mkdir -p ${tmp}/cvsroot
	[ "${vcs}" = "svn" ] && mkdir -p ${tmp}/svnroot

	if [ "${vcs}" = "git" ]; then
		git init
		touch .gitignore
		git add .gitignore
		git commit -a -m 'Initial Commit'
	elif [ "${vcs}" = "svn" ]; then
		svnadmin create svnroot
		svn co file://${tmp}/svnroot svn
		cd svn
	elif [ "${vcs}" = "cvs" ]; then
		CVSROOT="${tmp}/cvsroot" cvs init
		mkdir cvsroot/cvs
		cvs -d:local:${tmp}/cvsroot co cvs
		cd cvs
	fi

	mkdir -p ${VCSTEST}

	cp ${template}/vcstest-0.0.1.ebuild ${VCSTEST}
	${vcs} add $(dirname ${VCSTEST})
	if [ "${vcs}" = "cvs" ]; then
		${vcs} add ${VCSTEST}
		${vcs} add "${VCSTEST}/vcstest-0.0.1.ebuild"
	fi

	cd ${VCSTEST}
	ech ${echangelog} --vcs $vcs 'New ebuild for bug <id>.'

	if [ "${MD5_INIT}" != "$(md5 ChangeLog)" ]; then
		eerror "WRONG MD5_INIT!"
	fi

	mkdir files
	cp ${template}/test.patch files
	if [ "${vcs}" = "cvs" ]; then
		${vcs} add files/
		${vcs} add files/test.patch
	else
		${vcs} add files
	fi

	ech ${echangelog} --vcs $vcs "Added adittional patch to fix foo."

	if [ "${MD5_PATCH}" != "$(md5 ChangeLog)" ]; then
		eerror "WRONG MD5_PATCH!"
	fi

	if [ "${vcs}" = "svn" ]; then
		${vcs} commit -m 'New ebuild for bug <id>.' ../
	else
		${vcs} commit -m 'New ebuild for bug <id>.'
	fi

	[ "${vcs}" = "cvs" ] && sed -i -e 's:# $Header\: .*$:# $Header\: $:' ChangeLog

	cp vcstest-0.0.1.ebuild vcstest-0.0.1-r1.ebuild
	${vcs} add vcstest-0.0.1-r1.ebuild

	ech ${echangelog} --vcs $vcs "Revbump..."

	if [ "${MD5_REVBUMP}" != "$(md5 ChangeLog)" ]; then
		eerror "WRONG MD5_REVBUMP!"
	fi

	sed -i -e 's:# Copyright 1999-2009 Gentoo Foundation:# Copyright 1999-2010 Gentoo Foundation:' vcstest-0.0.1.ebuild
	ech ${echangelog} --vcs $vcs "Revbump...; Just copyright changed."

	if [ "${MD5_COPYRIGHT}" != "$(md5 ChangeLog)" ]; then
		eerror "WRONG MD5_COPYRIGHT!"
	fi

	if [ "${vcs}" = "cvs" ]; then
		rm -f files/test.patch
		${vcs} remove files/test.patch
	else
		${vcs} rm files/test.patch
	fi

	ech ${echangelog} --vcs $vcs "Revbump...; Just copyright changed; Removed obsolete patch."

	if [ "${MD5_OBSOLETE}" != "$(md5 ChangeLog)" ]; then
		eerror "WRONG MD5_OBSOLETE!"
	fi

	echo>>vcstest-0.0.1.ebuild
	ech ${echangelog} --vcs $vcs "Revbump...; Just copyright changed; Removed obsolete patch; Modified more then just the copyright."

	if [ "${MD5_FINAL}" != "$(md5 ChangeLog)" ]; then
		eerror "WRONG MD5_FINAL!"
	fi
}

[ -d "${_ROOT}/tmp" ] && rm -rf ${_ROOT}/tmp
mkdir -p ${_ROOT}/tmp

ebegin "Preparing echangelog"

if [ -e "../echangelog" ]; then
	cp ../echangelog "${_ROOT}/tmp" || set $?
	sed -i -e 's:use POSIX qw.*:use POSIX qw(setlocale getcwd);\nuse TEST qw(strftime);:' "${_ROOT}/tmp/echangelog" || set $?
	eend ${1:-0} || exit ${1}
else
	eerror "error"
	eend ${1:-1}
	exit 1
fi

for vcs in $SUPPORTED_VCS; do
	if [ -x "$(which ${vcs} 2>/dev/null)" ]; then
		ebegin "Starting test with ${vcs}"
		make_test $_ROOT "${vcs}" || set $?
		eend ${1:-0}
	else
		ewarn "No ${vcs} executable found, skipping test..."
	fi
done
