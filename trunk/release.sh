#! /bin/bash

case $(whoami) in
    karltk)
	publish_path=dev.gentoo.org:public_html/projects/gentoolkit/releases
	publish_public_path="http://dev.gentoo.org/~karltk/projects/gentoolkit/releases"
	portdir=/home/karltk/source/oss/gentoo/gentoo-x86/
	export ECHANGELOG_USER="Karl Trygve Kalleberg <karltk@gentoo.org>"
	;;

    port001)
	publish_path=dev.gentoo.org:public_html/distfiles/gentoolkit/releases
	publish_public_path="http://dev.gentoo.org/~port001/distfiles/gentoolkit/releases"
	portdir=/home/port001/Gentoo/gentoo-x86/
	export ECHANGELOG_USER="Ian Leitch <port001@gentoo.org>"
	;;

    genone)
	publish_path=dev:public_html/distfiles/
	publish_public_path="http://dev.gentoo.org/~genone/distfiles/"
	portdir=/home/gentoo/cvs/gentoo-x86/
	export ECHANGELOG_USER="Marius Mauch <genone@gentoo.org>"
	;;

    agriffis)
	publish_path=gentoo:public_html/dist/
	publish_public_path="http://dev.gentoo.org/~agriffis/dist/"
	portdir=/home/agriffis/portage/
	;;

    *)
	echo "!!! Don't know who $(whoami) is, can't release"
	exit 1
	;;
esac

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

	local ebuild="gentoolkit-dev-${VERSION}${RELEASE_TAG}.ebuild"

	cd ${portdir}/app-portage/gentoolkit-dev || exit
	cp $(most-recent-ebuild) ${ebuild}
	ekeyword ~all ${ebuild}
	sed -i -e "s|SRC_URI=.*|SRC_URI=\"${publish_public_path}/\$\{\P\}.tar.gz\"|" ${ebuild}

	echo "* Generating digest"
	ebuild ${ebuild} digest || exit
	cvs add ${ebuild} || exit
	echangelog "New upstream release"
	echo '* Everything ready. You should:'
	echo '  1) ACCEPT_KEYWORDS="~x86" sudo emerge =gentoolkit-dev-${VERSION}${RELEASE_TAG}'
	echo '  2) repoman ci -m "New upstream release" from `pwd`'
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

