#	vim:fileencoding=utf-8
# Copyright 2010 Gentoo Foundation
# Distributed under the terms of the GNU General Public License v2

__package__ = 'gentoolkit.eshowkw'
__version__ = 'svn'
__author__ = "Tomáš Chvátal <scarabeus@gentoo.org>"

import sys, os, fnmatch
import argparse
from portage import output as porto
from portage import settings as ports
from portage import config as portc
from portage import portdbapi as portdbapi
from portage import db as portdb

from .keywords_header import keywords_header
from .keywords_content import keywords_content
from .display_pretty import string_rotator
from .display_pretty import display

ignore_slots = False
bold = False
order = 'bottom'
topper = 'versionlist'

def process_display(package, keywords, dbapi):
	portdata = keywords_content(package, keywords.keywords, dbapi, ignore_slots, order, bold, topper)
	if topper == 'archlist':
		header = string_rotator().rotateContent(keywords.content, keywords.length, bold)
		extra = string_rotator().rotateContent(keywords.extra, keywords.length, bold, False)
		# -1 : space is taken in account and appended by us
		filler = ''.ljust(portdata.slot_length-1)
		header = ['%s%s%s' % (x, filler, y) for x, y in zip(header, extra)]
		content = portdata.content
		header_length = portdata.version_length
		content_length = keywords.length
	else:
		header = string_rotator().rotateContent(portdata.content, portdata.content_length, bold)
		content = keywords.content
		sep = [''.ljust(keywords.length) for x in range(portdata.slot_length-1)]
		content.extend(sep)
		content.extend(keywords.extra)
		header_length = keywords.length
		content_length = portdata.version_length
	display(content, header, header_length, content_length, portdata.cp, topper)

def process_args(argv):
	"""Option parsing via argc"""
	parser = argparse.ArgumentParser(prog=__package__,
		formatter_class=argparse.ArgumentDefaultsHelpFormatter,
		description='Display keywords for specified package or for package that is in pwd.')

	parser.add_argument('-v', '--version', action='version', version=__version__, help='show package version and exit')

	parser.add_argument('package', nargs='*', default=None, help='Packages to check.')

	parser.add_argument('-a', '--arch', nargs='+', default=[], help='Display only specified arch(s)')

	parser.add_argument('-A', '--align', nargs='?', default='bottom', choices=['top', 'bottom'],
		help='Specify alignment for descriptions.')
	parser.add_argument('-T', '--top-position', nargs='?', default='archlist', choices=['archlist', 'versionlist'],
		help='Specify which fields we want to have in top listing.')

	parser.add_argument('-B', '--bold', action='store_true', default=False,
		help='Print out each other column in bold for easier visual separation.')
	parser.add_argument('-C', '--color', action='store_true', default=False,
		help='Force colored output')
	parser.add_argument('-O', '--overlays', action='store_true', default=False,
		help='Search also overlays')
	parser.add_argument('-P', '--prefix', action='store_true', default=False,
		help='Display prefix keywords in output.')
	parser.add_argument('-S', '--ignore-slot', action='store_true', default=False,
		help='Treat slots as irelevant during detection of redundant pacakges.')

	return parser.parse_args(args=argv)

def main(argv, indirect = False):
	global ignore_slots, bold, order, topper

	#opts parsing
	opts = process_args(argv)
	ignore_slots = opts.ignore_slot
	use_overlays = opts.overlays
	# user can do both --arch=a,b,c or --arch a b c
	if len(opts.arch) > 1:
		opts.arch = ','.join(opts.arch)
	highlight_arch = ''.join(opts.arch).split(',')
	bold = opts.bold
	order = opts.align
	topper = opts.top_position
	prefix = opts.prefix
	color = opts.color
	package = opts.package

	# equery support
	if indirect and len(package) <= 0:
		msg_err = 'No packages specified'
		raise SystemExit(msg_err)

	# disable colors when redirected and they are not forced on
	if not color and not sys.stdout.isatty():
		# disable colors
		porto.nocolor()
	keywords = keywords_header(prefix, highlight_arch, order)
	if len(package) > 0:
		dbapi = portdb[ports['ROOT']]['porttree'].dbapi
		if not use_overlays:
			dbapi.porttrees = [dbapi.porttree_root]
		map(lambda x: process_display(x, keywords, dbapi), package)
	else:
		currdir = os.getcwd()
		# check if there are actualy some ebuilds
		ebuilds = ['%s' % x for x in os.listdir(currdir)
			if fnmatch.fnmatch(x, '*.ebuild')]
		if len(ebuilds) <= 0:
			msg_err = 'No ebuilds at "%s"' % currdir
			raise SystemExit(msg_err)
		package= '%s/%s' % (os.path.basename(os.path.abspath('../')), os.path.basename(currdir))
		ourtree = os.path.abspath('../../')
		overlays = '%s %s' % (ports['PORTDIR_OVERLAY'], ourtree)
		mysettings = portc(env={'PORTDIR_OVERLAY': overlays})
		dbapi = portdbapi(mysettings=mysettings)
		# specify that we want just our nice tree we are in cwd
		dbapi.porttrees = [ourtree]
		process_display(package, keywords, dbapi)
	return 0

if __name__ == '__main__':
	sys.exit(main(sys.argv[1:]))
