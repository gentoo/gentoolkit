#!/usr/bin/python
#
# Copyright 2010 Brian Dolbec <brian.dolbec@gmail.com>
# Copyright 2002-2010 Gentoo Technologies, Inc.
# Distributed under the terms of the GNU General Public License v2 or later
#
# $Header$

"""'revdep-rebuild' scans libraries and binaries for missing shared library dependencies and attempts to fix them by re-emerging
those broken binaries and shared libraries. It is useful when an upgraded package breaks other software packages that are
dependent upon the upgraded package.
"""

from __future__ import print_function

import sys
# This block ensures that ^C interrupts are handled quietly.
try:
	import signal

	def exithandler(signum,frame):
		signal.signal(signal.SIGINT, signal.SIG_IGN)
		signal.signal(signal.SIGTERM, signal.SIG_IGN)
		print()
		sys.exit(1)

	signal.signal(signal.SIGINT, exithandler)
	signal.signal(signal.SIGTERM, exithandler)
	signal.signal(signal.SIGPIPE, signal.SIG_DFL)


except KeyboardInterrupt:
	print()
	sys.exit(1)

from gentoolkit import errors
from gentoolkit.revdep_rebuild import rebuild

try:
	success = rebuild.main(rebuild.parse_options())
	sys.exit(success)
except errors.GentoolkitException as err:
	if '--debug' in sys.argv:
		raise
	else:
		from gentoolkit import pprinter as pp
		sys.stderr.write(pp.error(str(err)))
		print()
		print("Add '--debug' to global options for traceback.")
		sys.exit(1)
