#!/bin/sh

source /etc/init.d/functions.sh

VCSTEST="echangelog-test/vcstest"
_ROOT=$(pwd)

export ECHANGELOG_USER="Just a test <echangelogtest@gentoo.org>"

#MD5_INIT="34d54bc2ab1a2154b0c7bd5cdd7f6119"
MD5_INIT="34d54bc2ab1a2154b0c7bd5cdd7f6119"
#MD5_PATCH="d910ab6b76cfb48b68e11ae1f06612bb"
MD5_PATCH="db1ab89bb7374824d0f198078f79a83f"
#MD5_REVBUMP="8e36650a644ba49cc13bcbe93fdb2d2d"
MD5_REVBUMP="31ddfa60d2ae4dd1fccd7e3d2bd2c06c"
#MD5_COPYRIGHT="55a6097d8e3913a9feb0dff250649c00"
MD5_COPYRIGHT="6f39fa409ea14bb6506347c53f6dee50"
#MD5_OBSOLETE="6c30d84f603f5f0e4b09a88d9cfdaaa8"
MD5_OBSOLETE="0aedadf159c6f3add97a3f79fb867221"
#MD5_FINAL="cdd58fea5cfcef5820013d82ccbe0e89"
MD5_FINAL="17eb0df69f501cc6fdaffebd118b7764"

function md5() {
	local fname=$1
	echo $(md5sum ${fname} | awk '{ print $1 }')
}

function ech() {
	local bin=$1
	local msg=$2

	perl -I$(dirname $(dirname ${bin})) ${bin} "${msg}"
}

function make_test() {
	local root=$1
	local vcs=$2

	local echangelog="${root}/tmp/echangelog"
	local tmp="${root}/tmp/${vcs}"
	local template="${root}/templates"

	cd $root
	mkdir -p ${tmp}
	cd ${tmp}
	
	[[ "${vcs}" == "cvs" ]] && mkdir -p ${tmp}/cvsroot
	[[ "${vcs}" == "svn" ]] && mkdir -p ${tmp}/svnroot

	if [[ "${vcs}" == "git" ]];
	then
		git init
		touch .gitignore
		git add .gitignore
		git commit -a -m 'Initial Commit'
	elif [[ "${vcs}" == "svn" ]];
	then
		svnadmin create svnroot
		svn co file://${tmp}/svnroot svn
		cd svn
	elif [[ "${vcs}" == "cvs" ]];
	then
		CVSROOT="${tmp}/cvsroot" cvs init
		mkdir cvsroot/cvs
		cvs -d:local:${tmp}/cvsroot co cvs
		cd cvs
	fi

	mkdir -p ${VCSTEST}

	cp ${template}/vcstest-0.0.1.ebuild ${VCSTEST}
	${vcs} add $(dirname ${VCSTEST})
	if [[ "${vcs}" == "cvs" ]];
	then
		${vcs} add ${VCSTEST}
		${vcs} add "${VCSTEST}/vcstest-0.0.1.ebuild"
	fi

	cd ${VCSTEST}
	ech ${echangelog} 'New ebuild for bug <id>.'

	if [[ "${MD5_INIT}" != "$(md5 ChangeLog)" ]];
	then
		eerror "WRONG MD5_INIT!"
	fi

	mkdir files
	cp ${template}/test.patch files
	if [[ "${vcs}" == "cvs" ]];
	then
		${vcs} add files/
		${vcs} add files/test.patch
	else
		${vcs} add files
	fi

	ech ${echangelog} "Added adittional patch to fix foo."

	if [[ "${MD5_PATCH}" != "$(md5 ChangeLog)" ]];
	then
		eerror "WRONG MD5_PATCH!"
	fi

	if [[ "${vcs}" == "svn" ]];
	then
		${vcs} commit -m 'New ebuild for bug <id>.' ../
	else
		${vcs} commit -m 'New ebuild for bug <id>.'
	fi

	[[ "${vcs}" == "cvs" ]] && sed -i -e 's:# $Header\: .*$:# $Header\: $:' ChangeLog

	cp vcstest-0.0.1.ebuild vcstest-0.0.1-r1.ebuild
	${vcs} add vcstest-0.0.1-r1.ebuild

	ech ${echangelog} "Revbump..."

	if [[ "${MD5_REVBUMP}" != "$(md5 ChangeLog)" ]];
	then
		eerror "WRONG MD5_REVBUMP!"
	fi

	sed -i -e 's:# Copyright 1999-2009 Gentoo Foundation:# Copyright 1999-2010 Gentoo Foundation:' vcstest-0.0.1.ebuild
	ech ${echangelog} "Revbump...; Just copyright changed."

	if [[ "${MD5_COPYRIGHT}" != "$(md5 ChangeLog)" ]];
	then
		eerror "WRONG MD5_COPYRIGHT!"
	fi

	if [[ "${vcs}" == "cvs" ]];
	then
		rm -f files/test.patch
		${vcs} remove files/test.patch
	else
		${vcs} rm files/test.patch
	fi

	ech ${echangelog} "Revbump...; Just copyright changed; Removed obsolete patch."

	if [[ "${MD5_OBSOLETE}" != "$(md5 ChangeLog)" ]];
	then
		eerror "WRONG MD5_OBSOLETE!"
	fi

	echo>>vcstest-0.0.1.ebuild
	ech ${echangelog} "Revbump...; Just copyright changed; Removed obsolete patch; Modified more then just the copyright."

	if [[ "${MD5_FINAL}" != "$(md5 ChangeLog)" ]];
	then
		eerror "WRONG MD5_FINAL!"
	fi
}

[[ -d "${_ROOT}/tmp" ]] && rm -rf ${_ROOT}/tmp
mkdir -p ${_ROOT}/tmp

ebegin "Preparing echangelog"

if [[ -e ../echangelog ]];
then
	cp ../echangelog "${_ROOT}/tmp" || set $?
	sed -i -e 's:use POSIX qw.*:use POSIX qw(setlocale getcwd);\nuse TEST qw(strftime);:' "${_ROOT}/tmp/echangelog" || set $?
	eend ${1:-0} || exit ${1}
else
	eerror "error"
	eend ${1:-1}
	exit 1
fi

if [[ -x $(which git) ]];
then
	ebegin "Starting test with git"
	make_test $_ROOT "git" || set $?
	eend ${1:-0} 
fi

if [[ -x $(which cvs) ]];
then
	ebegin "Starting test with cvs"
	make_test $_ROOT "cvs" || set $?
	eend ${1:-0}
fi

if [[ -x $(which svn) ]];
then
	ebegin "Starting test with svn"
	make_test $_ROOT "svn" || set $?
	eend ${1:-0}
fi

rm -rf "${_ROOT}/tmp"
