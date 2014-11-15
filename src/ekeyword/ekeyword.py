#!/usr/bin/python
# Copyright 2014 Gentoo Foundation
# Distributed under the terms of the GNU General Public License v2
# Written by Mike Frysinger <vapier@gentoo.org>

"""Manage KEYWORDS in ebuilds easily.

This tool provides a simple way to add or update KEYWORDS in a set of ebuilds.
Each command-line argument is processed in order, so that keywords are added to
the current list as they appear, and ebuilds are processed as they appear.

Instead of specifying a specific arch, it's possible to use the word "all".
This causes the change to apply to all keywords presently specified in the
ebuild.

The ^ leader instructs ekeyword to remove the specified arch.

Examples:

  # Mark all existing arches in the ebuild as stable.
  $ %(prog)s all foo-1.ebuild

  # Mark arm as stable and x86 as unstable.
  $ %(prog)s arm ~x86 foo-1.ebuild

  # Mark hppa as unsupported (explicitly adds -hppa).
  $ %(prog)s -hppa foo-1.ebuild

  # Delete alpha keywords from all ebuilds.
  $ %(prog)s ^alpha *.ebuild

  # Mark sparc as stable for foo-1 and m68k as unstable for foo-2.
  $ %(prog)s sparc foo-1.ebuild ~m68k foo-2.ebuild

  # Mark s390 as the same state as amd64.
  $ %(prog)s s390=amd64 foo-1.ebuild
"""

from __future__ import print_function

import argparse
import collections
import difflib
import io
import os
import re
import sys

import portage
from portage.output import colorize, nocolor


VERSION = '1.0 awesome'

# Operation object that describes how to perform a change.
# Args:
#  op: The operation to perform when |ref_arch| is not set:
#      None: Mark |arch| stable
#      '-': Mark |arch| as not applicable (e.g. -foo)
#      '~': Mark |arch| as unstable (e.g. ~foo)
#      '^': Delete |arch| so it isn't listed at all
#  arch: The required arch to update
#  ref_arch: Set |arch| status to this arch (ignoring |op|)
Op = collections.namedtuple('Op', ('op', 'arch', 'ref_arch'))


def warning(msg):
	"""Write |msg| as a warning to stderr"""
	print('warning: %s' % msg, file=sys.stderr)


def keyword_to_arch(keyword):
	"""Given a keyword, strip it down to its arch value

	When an ARCH shows up in KEYWORDS, it may have prefixes like ~ or -.
	Strip all that cruft off to get back to the ARCH.
	"""
	return keyword.lstrip('-~')


def sort_keywords(arches):
	"""Sort |arches| list in the order developers expect

	This is vaguely defined because it is kind of vaguely defined once you get
	past the basic (Linux-only) keywords.

	Args:
	  arches: An iterable of ARCH values.

	Returns:
	  A sorted list of |arches|
	"""
	keywords = []

	# Globs always come first.
	for g in ('-*', '*', '~*'):
		if g in arches:
			arches.remove(g)
			keywords.append(g)

	def arch_key(keyword):
		# Sort independent of leading marker (~ or -).
		arch = keyword_to_arch(keyword)

		# A keyword may have a "-" in it.  We split on that and sort
		# by the two resulting items.  The part after the hyphen is
		# the primary key.
		if '-' in arch:
			arch, plat = arch.split('-', 1)
		else:
			arch, plat = arch, ''

		return (plat, arch)

	keywords += sorted(arches, key=arch_key)

	return keywords


def diff_keywords(old_keywords, new_keywords, format='color-inline'):
	"""Show pretty diff between list of keywords

	Args:
	  old_keywords: The old set of KEYWORDS
	  new_keywords: The new set of KEYWORDS
	  format: The diff style

	Returns:
	  A string containing the diff output ready to shown to the user
	"""
	def show_diff(s):
		output = ''

		for tag, i0, i1, j0, j1 in s.get_opcodes():

			if tag == 'equal':
				output += s.a[i0:i1]

			if tag in ('delete', 'replace'):
				o = s.a[i0:i1]
				if format == 'color-inline':
					o = colorize('bg_darkred', o)
				else:
					o = '-{%s}' % o
				output += o

			if tag in ('insert', 'replace'):
				o = s.b[j0:j1]
				if format == 'color-inline':
					o = colorize('bg_darkgreen', o)
				else:
					o = '+{%s}' % o
				output += o

		return output

	sold = str(' '.join(old_keywords))
	snew = str(' '.join(new_keywords))
	s = difflib.SequenceMatcher(str.isspace, sold, snew, autojunk=False)
	return show_diff(s)


def process_keywords(keywords, ops, arch_status=None):
	"""Process |ops| for |keywords|"""
	new_keywords = set(keywords).copy()

	# Process each op one at a time.
	for op, oarch, refarch in ops:
		# Figure out which keywords we need to modify.
		if oarch == 'all':
			if not arch_status:
				raise ValueError('unable to process "all" w/out profiles.desc')
			old_arches = set([keyword_to_arch(a) for a in new_keywords])
			if op is None:
				# Process just stable keywords.
				arches = [k for k, v in arch_status.items()
				          if v == 'stable' and k in old_arches]
			else:
				# Process all possible keywords.  We use the arch_status as a
				# master list.  If it lacks some keywords, then we might miss
				# somethings here, but not much we can do.
				arches = old_arches
			# We ignore the glob arch as we never want to tweak it.
			if '*' in arches:
				arches.remove('*')
		else:
			arches = (oarch,)

		if refarch:
			# Figure out the state for this arch based on the reference arch.
			# TODO: Add support for "all" keywords.
			# XXX: Should this ignore the '-' state ?  Does it make sense to
			#      sync e.g. "s390" to "-ppc" ?
			refkeyword = [x for x in new_keywords if refarch == keyword_to_arch(x)]
			if not refkeyword:
				op = '^'
			elif refkeyword[0].startswith('~'):
				op = '~'
			elif refkeyword[0].startswith('-'):
				op = '-'
			else:
				op = None

		# Finally do the actual update of the keywords list.
		for arch in arches:
			new_keywords -= set(['%s%s' % (x, arch) for x in ('', '~', '-')])

			if op is None:
				new_keywords.add(arch)
			elif op in ('~', '-'):
				new_keywords.add('%s%s' % (op, arch))
			elif op == '^':
				# Already deleted.  Whee.
				pass
			else:
				raise ValueError('unknown operation %s' % op)

	return new_keywords


def process_content(ebuild, data, ops, arch_status=None, verbose=0,
                    quiet=0, format='color-inline'):
	"""Process |ops| for |data|"""
	# Set up the user display style based on verbose/quiet settings.
	if verbose > 1:
		disp_name = ebuild
		def logit(msg):
			print('%s: %s' % (disp_name, msg))
	elif quiet > 1:
		def logit(msg):
			pass
	else:
		# Chop the full path and the .ebuild suffix.
		disp_name = os.path.basename(ebuild)[:-7]
		def logit(msg):
			print('%s: %s' % (disp_name, msg))

	# Match any KEYWORDS= entry that isn't commented out.
	keywords_re = re.compile(r'^([^#]*\bKEYWORDS=)([\'"])(.*)(\2)(.*)')
	updated = False
	content = []

	# Walk each line of the ebuild looking for KEYWORDS to process.
	for line in data:
		m = keywords_re.match(line)
		if not m:
			content.append(line)
			continue

		# Ok, we've got it, now let's process things.
		old_keywords = set(m.group(3).split())
		new_keywords = process_keywords(
			old_keywords, ops, arch_status=arch_status)

		# Finally let's present the results to the user.
		if (new_keywords != old_keywords) or verbose:
			# Only do the diff work if something actually changed.
			updated = True
			old_keywords = sort_keywords(old_keywords)
			new_keywords = sort_keywords(new_keywords)
			line = '%s"%s"%s\n' % (m.group(1), ' '.join(new_keywords),
			                       m.group(5))
			if format in ('color-inline', 'inline'):
				logit(diff_keywords(old_keywords, new_keywords, format=format))
			else:
				if format == 'long-multi':
					logit(' '.join(['%*s' % (len(keyword_to_arch(x)) + 1, x)
					                for x in old_keywords]))
					logit(' '.join(['%*s' % (len(keyword_to_arch(x)) + 1, x)
					                for x in new_keywords]))
				else:
					deleted_keywords = [x for x in old_keywords
					                    if x not in new_keywords]
					logit('--- %s' % ' '.join(deleted_keywords))
					added_keywords = [x for x in new_keywords
					                  if x not in old_keywords]
					logit('+++ %s' % ' '.join(added_keywords))

		content.append(line)

	if not updated:
		logit('no updates')

	return updated, content


def process_ebuild(ebuild, ops, arch_status=None, verbose=0, quiet=0,
                   dry_run=False, format='color-inline'):
	"""Process |ops| for |ebuild|

	Args:
	  ebuild: The ebuild file to operate on & update in place
	  ops: An iterable of operations (Op objects) to perform on |ebuild|
	  arch_status: A dict mapping default arches to their stability; see the
	               load_profile_data function for more details
	  verbose: Be verbose; show various status messages
	  quiet: Be quiet; only show errors
	  dry_run: Do not make any changes to |ebuild|; show what would be done
	  format: The diff style

    Returns:
      Whether any updates were processed
	"""
	with io.open(ebuild, encoding='utf8') as f:
		updated, content = process_content(
			ebuild, f, ops, arch_status=arch_status,
			verbose=verbose, quiet=quiet, format=format)
		if updated and not dry_run:
			with io.open(ebuild, 'w', encoding='utf8') as f:
				f.writelines(content)
        return updated


def load_profile_data(portdir=None, repo='gentoo'):
	"""Load the list of known arches from the tree

	Args:
	  portdir: The repository to load all data from (and ignore |repo|)
	  repo: Look up this repository by name to locate profile data

	Returns:
	  A dict mapping the keyword to its preferred state:
	  {'x86': 'stable', 'mips': 'dev', ...}
	"""
	if portdir is None:
		portdir = portage.db['/']['vartree'].settings.repositories[repo].location

	arch_status = {}

	try:
		arch_list = os.path.join(portdir, 'profiles', 'arch.list')
		with open(arch_list) as f:
			for line in f:
				line = line.split('#', 1)[0].strip()
				if line:
					arch_status[line] = None
	except IOError:
		pass

	try:
		profile_status = {
			'stable': 0,
			'dev': 1,
			'exp': 2,
			None: 3,
		}
		profiles_list = os.path.join(portdir, 'profiles', 'profiles.desc')
		with open(profiles_list) as f:
			for line in f:
				line = line.split('#', 1)[0].split()
				if line:
					arch, profile, status = line
					arch_status.setdefault(arch, status)
					curr_status = profile_status[arch_status[arch]]
					new_status = profile_status[status]
					if new_status < curr_status:
						arch_status[arch] = status
	except IOError:
		pass

	if arch_status:
		arch_status['all'] = None
	else:
		warning('could not read profile files: %s' % arch_list)
		warning('will not be able to verify args are correct')

	return arch_status


def arg_to_op(arg):
	"""Convert a command line |arg| to an Op"""
	arch_prefixes = ('-', '~', '^')

	op = None
	arch = arg
	refarch = None

	if arg and arg[0] in arch_prefixes:
		op, arch = arg[0], arg[1:]

	if '=' in arch:
		if not op is None:
			raise ValueError('Cannot use an op and a refarch')
		arch, refarch = arch.split('=', 1)

	return Op(op, arch, refarch)


def ignorable_arg(arg, quiet=0):
	"""Whether it's ok to ignore this argument"""
	if os.path.isdir(arg):
		if not quiet:
			warning('ignoring directory %s' % arg)
		return True

	WHITELIST = (
		'Manifest',
		'metadata.xml',
	)
	base = os.path.basename(arg)
	if (base.startswith('ChangeLog') or
	    base in WHITELIST or
	    base.startswith('.') or
	    base.endswith('~')):
		if not quiet:
			warning('ignoring file: %s' % arg)
		return True

	return False


def args_to_work(args, arch_status=None, repo='gentoo', quiet=0):
	"""Process |args| into a list of work itmes (ebuild/arches to update)"""
	work = []
	todo_arches = []
	last_todo_arches = None

	for arg in args:
		if arg.endswith('.ebuild'):
			if not todo_arches:
				todo_arches = last_todo_arches
			if not todo_arches:
				raise ValueError('missing arches to process for %s' % arg)
			work.append([arg, todo_arches])
			last_todo_arches = todo_arches
			todo_arches = []
		else:
			op = arg_to_op(arg)
			if not arch_status or op.arch in arch_status:
				todo_arches.append(op)
			elif not ignorable_arg(arg, quiet=quiet):
				raise ValueError('unknown arch/argument: %s' % arg)

	if todo_arches:
		raise ValueError('missing ebuilds to process!')

	return work


def get_parser():
	"""Return an argument parser for ekeyword"""
	parser = argparse.ArgumentParser(
		description=__doc__,
		formatter_class=argparse.RawDescriptionHelpFormatter)
	parser.add_argument('-n', '--dry-run', default=False, action='store_true',
		help='Show what would be changed, but do not commit')
	parser.add_argument('-v', '--verbose', action='count', default=0,
		help='Be verbose while processing things')
	parser.add_argument('-q', '--quiet', action='count', default=0,
		help='Be quiet while processing things (only show errors)')
	parser.add_argument('--format', default='auto',
		choices=('auto', 'color-inline', 'inline', 'short-multi', 'long-multi'),
		help='Selet output format for showing differences')
	parser.add_argument('-V', '--version', default=False, action='store_true',
		help='Show version information')
	return parser


def main(argv):
	if argv is None:
		argv = sys.argv[1:]

	# Extract the args ourselves.  This is to allow things like -hppa
	# without tripping over the -h/--help flags.  We can't use the
	# parse_known_args function either.
	# This sucks and really wish we didn't need to do this ...
	parse_args = []
	work_args = []
	while argv:
		arg = argv.pop(0)
		if arg.startswith('--'):
			if arg == '--':
				work_args += argv
				break
			else:
				parse_args.append(arg)
			# Handle flags that take arguments.
			if arg in ('--format',):
				if argv:
					parse_args.append(argv.pop(0))
		elif arg[0] == '-' and len(arg) == 2:
			parse_args.append(arg)
		else:
			work_args.append(arg)

	parser = get_parser()
	opts = parser.parse_args(parse_args)
	if opts.version:
		print('version: %s' % VERSION)
		return os.EX_OK
	if not work_args:
		parser.error('need arches/ebuilds to process')

	if opts.format == 'auto':
		if not portage.db['/']['vartree'].settings.get('NOCOLOR', 'false').lower() in ('no', 'false'):
			nocolor()
			opts.format = 'short'
		else:
			opts.format = 'color-inline'

	arch_status = load_profile_data()
	try:
		work = args_to_work(work_args, arch_status=arch_status, quiet=opts.quiet)
	except ValueError as e:
		parser.error(e)

	for ebuild, ops in work:
		process_ebuild(ebuild, ops, arch_status=arch_status,
		               verbose=opts.verbose, quiet=opts.quiet,
		               dry_run=opts.dry_run, format=opts.format)

	return os.EX_OK


if __name__ == '__main__':
	sys.exit(main(sys.argv[1:]))
