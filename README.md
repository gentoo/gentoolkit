MOTIVATION
==========

The gentoolkit package contains a collection of useful administration scripts
particular to the Gentoo Linux distribution. It contains rough drafts and
implementations of features that may in time make it into Portage, or into
full-fledged tools in their own right.

CONTENTS
========

gentoolkit
----------
- ebump          - Ebuild revision bumper
- eclean         - tool to clean up outdated distfiles and packages
- ekeyword       - modify package KEYWORDS
- enalyze        - Analyze all installed pkgs or rebuild package.* files
- epkginfo       - wrapper to equery: Display metadata about a given package.
- equery         - replacement for etcat and qpkg
- eread          - script to read portage log items from einfo, ewarn etc.
- eshowkw        - Display keywords for specified package(s)
- euse           - tool to manage USE flags
- imlate         - Displays candidates for keywords for an architecture...
- qpkg           - convient package query tool (deprecated)
- revdep-rebuild - scans/fixes broken shared libs and binaries

IMPROVEMENTS
============

Any suggestions for improvements should be sent to tools-portage@gentoo.org, or
added as a bug assigned to us.

We only accept new contributions if they are written in Bash or Python.
