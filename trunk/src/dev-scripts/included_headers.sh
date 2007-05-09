#!/bin/bash

# CHANGES
#
# 20051211: Add qfile use from portage-utils, prefer over equery. Create new
# 	function track_headers() to handle package manager queries for both
# 	relative and absolute headers. Split relative and absolute queries into two
# 	separate places, since relative aren't quite as reliable. Prefer headers
# 	found in the tarball over those in /usr/include. Also, note which headers
# 	weren't considered in the calculation and the reasons why not.

location=${1}

usage() {
	echo "${0##*/} [ -d ] source_location"
	echo "  Returns owners of all include files used. ${0##*/} defaults to"
	echo "  files in /usr/include, so if a file with the same name within the"
	echo "  source is the actual one used, false dependencies may be printed."
	echo
	echo "  -d"
	echo "    Show debug output: Print files not found"
	exit 1
}

decho() {
	if [[ -n "${DEBUG}" ]]; then
		echo "${1}"
	fi
}

if [[ $# -le 0 ]] || [[ $# -ge 3 ]]; then
	usage
fi

# Handle command-line options
while getopts d options; do
	case ${options} in
		d)	DEBUG=1
			;;
		*)	usage
			;;
	esac
done
# Reset post-option stuff to positional parameters
shift $((OPTIND - 1))

get_absolute_includes() {
	grep '^#[[:space:]]*include' -r ${1} | grep '.*.[ch]' | grep -e '<' -e '>' \
	| cut -d':' -f2 | cut -d'<' -f2 | cut -d'>' -f1 | grep '.*.[ch]' \
	| sort | uniq
}

get_relative_includes() {
	grep '^#[[:space:]]*include' -r ${1} | grep '.*.[ch]' | grep -e '"' -e '"' \
	| cut -d':' -f2 | cut -d'"' -f2 | cut -d'"' -f1 | grep '.*.[ch]' \
	| sort | uniq
}

track_headers() {
	if [[ -x $(which qfile 2> /dev/null) ]]; then
		qfile ${@} | cut -d'(' -f1 | sort | uniq
	elif [[ -x $(which equery 2> /dev/null) ]]; then
		equery -q belongs ${@} | cut -d'(' -f1
	elif [[ -x $(which rpm 2> /dev/null) ]]; then
		rpm -qf ${@}
	else
		echo "Couldn't find package query tool! Printing headerpaths instead."
		echo
		for header in ${@}; do
			echo ${header}
		done
	fi
}

echo "Analyzing source ... "
absolute_headers="$(get_absolute_includes ${1})"
relative_headers="$(get_relative_includes ${1})"

echo "Looking for absolute headers ... "
echo
for header in ${absolute_headers}; do
	absheader="/usr/include/${header}"
	if [[ -e ${absheader} ]]; then
		abs_headerpaths="${abs_headerpaths} ${absheader}"
		echo "  Looking for ${absheader} ... OK"
	else
		# Try as a relative header in case people use -I with <>
		relative_headers="${relative_headers} ${header}"
		decho "  Looking for ${absheader} ... Not found!"
	fi
done

echo
echo "Looking for relative headers ... "
echo
for header in ${relative_headers}; do
	fullheader=${header}
	header=${header##*/}
	# Prefer headers in tarball over /usr/include
	header_options=$(find ${location} -name ${header} | grep ${fullheader})
	if [[ -z ${header_options} ]]; then
		header_options="$(find /usr/include -name ${header} | grep ${fullheader})"
		header_loc="/usr/include"
	else
		decho "  Local header ${header} ... Not considering."
		local_headers="${local_headers} ${header}"
		continue
	fi
	count="0"
	for found in ${header_options}; do
		(( count++ ))
	done
	if [[ ${count} -ge 2 ]]; then
		echo "  Looking for ${header} ... "
		echo "    More than one option found for ${header} in ${header_loc}."
		echo "    Not considering ${header}."
		duplicate_headers="${duplicate_headers} ${header}"
		continue
	elif [[ ${count} -le 0 ]]; then
		decho "  Looking for ${header} ... Not found!"
		unfound_headers="${unfound_headers} ${header}"
		continue
	fi
	header=${header_options}
	if [[ -e ${header} ]] && [[ ${header_loc} = /usr/include ]]; then
		rel_headerpaths="${rel_headerpaths} ${header}"
		echo "  Looking for ${header} ... OK"
	else
		decho "  Looking for ${header} ... Not found!"
	fi
done

echo "Tracing headers back to packages ..."
echo
echo "Headers ignored because they exist in the tarball:"
echo
for header in ${local_headers}; do
	echo "${header}"
done
echo
echo "Headers ignored because of duplicates in /usr/include:"
echo
for header in ${duplicate_headers}; do
	echo "${header}"
done
echo
echo "Headers ignored because they weren't found:"
echo
for header in ${unfound_headers}; do
	echo "${header}"
done
echo
echo "Absolute headers:"
echo
track_headers ${abs_headerpaths}
echo
echo "Relative headers:"
echo
track_headers ${rel_headerpaths}
