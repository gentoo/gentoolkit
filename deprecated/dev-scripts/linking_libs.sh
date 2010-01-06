#!/bin/bash

# CHANGES
#
# 20051211: Move most of the logic to check for bad links into get_libnames()
# 	seds, so we don't wrongly sed out whole link lines. Seems to catch more
# 	problems, such as ' or ` or -- in a link.
# 20051210: Prefer qfile from portage-utils over equery if it's available.
# 	Check for ... in "link" lines because configure checks are not links.
# 	Change get_link_generic() to handle whole lines at a time instead of single
# 	words, so get_linklines() works.
# 20051210: Rework get_libnames() to use a new style of grep, because the old
# 	way was broken on some packages from the \b. Also optimize the "Looking for
# 	libraries" section to only grep the log file once for links and cache it;
# 	also only grep the link lines ones for a given library, then parse the
# 	output for static or shared. Should speed things up considerably for large
# 	packages. I get 5 seconds in Analyzing log and 15 in Looking for libs on an
# 	xorg-x11-6.8.99.15 log on second run.
# 	Create get_link_generic() that both sections call with different options.

usage() {
	echo "${0##*/} compilation_log"
	echo "  Checks for -lfoo link commands and finds the library owners."
	exit 1
}

if [[ $# -lt 1 || $1 == -h || $1 == --help ]]; then
	usage
fi


# Finds all lines in a file that involve linking
# get_link_generic(char *grep_opts, char *filename)
get_link_generic() {
	egrep ${1} '\-l\w[^[:space:]]*' ${2} \
		| while read linker; do
			# -linker is passed through to ld and doesn't mean the inker lib.
			# The new -w in grep makes sure they're separate "words", but its
			# "word" characters only include alnum and underscore, so -- gets
			# through.
			# Some configure lines with ... match, so we drop them
			# Some of the configure options match, so we get rid of = for that.
			if \
				[[ "${linker}" != *...* ]] \
				&& [[ "${linker}" != -lib ]] \
				&& [[ "${linker}" != -libs ]]; then
				echo ${linker}
			fi
	done
}

# Note the lack of -o, as compared to get_libnames() egrep
get_linklines() {
	get_link_generic "-w" ${1} | sort | uniq
}

get_libnames() {
    for x; do
	get_link_generic "-o -w" ${x} \
		| sed \
			-e "/^-link/d" \
			-e "/^-lib/d" \
			-e "s:^-l::g" \
			-e "/=/d" \
			-e "/'/d" \
			-e "/^-/d" \
			-e "s:\.*$::g" \
			-e "s:|::g" \
			-e "s:\"::g" \
			-e "/^-link/d" \
			-e "/^-lib/d"
    done | sort | uniq
}

get_libdirs() {
	cat /etc/ld.so.conf | sed -e "/^#/d"
}

check_exists() {
	if [[ -n ${1// } ]]; then
		return 0
	fi

	return 1
}

trace_to_packages() {
	local paths=$1

	check_exists "${paths}"
	local ret=$?
	if [[ $ret -ne 0 ]]; then
		return 1
	fi

	if [[ -x $(which qfile 2> /dev/null) ]]; then
		qfile -q ${paths} | sort | uniq
	elif [[ -x $(which equery 2> /dev/null) ]]; then
		equery -q belongs ${paths} | cut -d'(' -f1
	elif [[ -x $(which rpm 2> /dev/null) ]]; then
		rpm -qf ${paths}
	else
		echo "Couldn't find package query tool! Printing paths instead."
		echo
		for path in ${paths}; do
			echo ${path}
		done
	fi
}

# *64 needs to be first, as *lib is a symlink to it so equery screws up
libdirs="/lib64 /usr/lib64 /lib /usr/lib $(get_libdirs)"

echo "Analyzing log ..."
libnames=$(get_libnames "$@")

#echo libnames=$libnames

echo "Looking for libraries ..."
linker_lines=$(get_linklines ${1})

#echo linker_lines=$linker_lines

for libname in ${libnames}; do
	static=0
	shared=0
	line=$(echo ${linker_lines} | grep "\b-l${libname}\b")
	if echo ${line} | grep -q '\b-static\b'; then
		static=1
	fi
	if ! echo ${line} | grep -q '\b-static\b'; then
		shared=1
	fi
	staticlibname="lib${libname}.a"
	sharedlibname="lib${libname}.so"
	if [[ ${static} -eq 1 ]]; then
		echo -n "  Looking for ${staticlibname} ... "
		for libdir in ${libdirs}; do
			found=0
			if [[ -e ${libdir}/${staticlibname} ]]; then
				libpaths="${libpaths} ${libdir}/${staticlibname}"
				found=1
				echo "OK"
				break
			fi
		done
		if [[ ${found} -ne 1 ]]; then
			echo "Not found!"
		fi
	fi
	if [[ ${shared} -eq 1 ]]; then
		echo -n "  Looking for ${sharedlibname} ... "
		for libdir in ${libdirs}; do
			found=0
			if [[ -e ${libdir}/${sharedlibname} ]]; then
				libpaths="${libpaths} ${libdir}/${sharedlibname}"
				found=1
				echo "OK"
				break
			fi
		done
		if [[ ${found} -ne 1 ]]; then
			echo "Not found!"
		fi
	fi
done

# Add backslashes in front of any + symbols
libpaths=${libpaths//+/\\+}

echo "Looking for build tools (imake, etc) ..."
BUILD_PKGS=$(egrep -h "$@" \
	-e '^(/usr/(X11R6/)?bin/)?rman' \
	-e '^(/usr/(X11R6/)?bin/)?gccmakedep' \
	-e '^(/usr/(X11R6/)?bin/)?makedepend' \
	-e '^(/usr/(X11R6/)?bin/)?imake' \
	-e '^(/usr/(X11R6/)?bin/)?rman' \
	-e '^(/usr/(X11R6/)?bin/)?lndir' \
	-e '^(/usr/(X11R6/)?bin/)?xmkmf' \
	| awk '{ print $1 }' \
	| sort \
	| uniq)

for PKG in ${BUILD_PKGS}; do
	PKG=$(basename ${PKG})
	echo -n "  Looking for ${PKG} ... "
	if [[ -e /usr/bin/${PKG} ]]; then
		echo "OK"
		buildpaths="${buildpaths} ${PKG}"
	else
		echo "Not found!"
	fi
done

echo
echo "Tracing libraries back to packages ..."
echo
trace_to_packages "${libpaths}"

echo
echo "Tracing build tools back to packages ..."
echo

trace_to_packages "${buildpaths}"
