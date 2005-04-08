#! /bin/bash

if [ "$(whoami)" == "karltk" ] ; then
	publish_path=dev.gentoo.org:public_html/projects/gentoolkit/releases
	publish_public_path="http://dev.gentoo.org/~karltk/projects/gentoolkit/releases"
	portdir=/home/karltk/source/oss/gentoo/gentoo-x86/
	export ECHANGELOG_USER="Karl Trygve Kalleberg <karltk@gentoo.org>"
elif [ "$(whoami)" == "port001" ] ; then
	publish_path=dev.gentoo.org:public_html/distfiles/gentoolkit/releases
	publish_public_path="http://dev.gentoo.org/~port001/distfiles/gentoolkit/releases"
	portdir=/home/port001/Gentoo/gentoo-x86/
	export ECHANGELOG_USER="Ian Leitch <port001@gentoo.org>"
elif [ "$(whoami)" == "genone" ]; then
	publish_path=dev:public_html/distfiles/
	publish_public_path="http://dev.gentoo.org/~genone/distfiles/"
	portdir=/home/gentoo/cvs/gentoo-x86/
	export ECHANGELOG_USER="Marius Mauch <genone@gentoo.org>"
else
	echo "!!! Don't know who $(whoami) is, can't release"
	exit 1
fi


function most-recent-ebuild() {
	# FIXME: actually pick the most recent one
	ls gentoolkit-dev-*.ebuild | tail -n 1
}

function release-dev() {

	echo "* Building .tar.bz"
	make VERSION=${VERSION} RELEASE_TAG=${RELEASE_TAG} dist-gentoolkit-dev > /dev/null || exit

	echo "* Uploading .tar.bz"
	scp release/gentoolkit-dev-${VERSION}${RELEASE_TAG}.tar.gz ${publish_path} || exit

	
	echo "* Generating new ebuild"

	local finalebuild="gentoolkit-dev-${VERSION}${RELEASE_TAG}.ebuild"

	cd ${portdir}/app-portage/gentoolkit-dev || exit
	ebuild=$(most-recent-ebuild)
	cat ${ebuild} | sed \
		-e 's/KEYWORDS=.*/KEYWORDS="~x86 ~ppc ~sparc ~mips ~alpha ~arm ~hppa ~amd64 ~ia64 ~ppc64 ~s390 ~ppc-macos"/' \
		-e "s|SRC_URI=.*|SRC_URI=\"${publish_public_path}/\$\{\P\}.tar.gz\"|" \
		> ${finalebuild} || exit

	echo "* Generating digest"
	ebuild ${finalebuild} digest || exit
	cvs add ${finalebuild} || exit
	echangelog "New upstream release."
	echo '* Everything ready. You should:'
	echo '  1) ACCEPT_KEYWORDS="~x86" sudo emerge =gentoolkit-dev-${VERSION}${RELEASE_TAG}'
	echo '  2) repoman ci -m "New upstraem release." from `pwd`'
}


if [ -z "${VERSION}" ] ; then
	echo "!!! You must set the VERSION env var"
	exit 1
fi

if [ -z "${RELEASE_TAG}" ] ; then
	echo "No RELEASE_TAG found, presumably okay"
fi


if [ "$1" == "dev" ] ; then
	release-dev
elif [ "$1" == "main" ] ; then
	echo "!!! Unsupported atm, feel free to add code;)"
	exit 1
else
	echo "!!! You must select to release either 'dev' or 'main', as parameter to release.sh"
	exit 1
fi

