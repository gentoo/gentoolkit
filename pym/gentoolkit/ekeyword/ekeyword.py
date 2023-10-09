#!/usr/bin/python
# Copyright 2014-2023 Gentoo Authors
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

import argparse
import collections
import difflib
import os
import re
import subprocess
import sys

from gentoolkit.profile import load_profile_data

import portage
from portage.output import colorize, nocolor


__version__ = "@VERSION@"

# Operation object that describes how to perform a change.
# Args:
#  op: The operation to perform when |ref_arch| is not set:
#      None: Mark |arch| stable
#      '-': Mark |arch| as not applicable (e.g. -foo)
#      '~': Mark |arch| as unstable (e.g. ~foo)
#      '^': Delete |arch| so it isn't listed at all
#  arch: The required arch to update
#  ref_arch: Set |arch| status to this arch (ignoring |op|)
Op = collections.namedtuple("Op", ("op", "arch", "ref_arch"))


def warning(msg):
    """Write |msg| as a warning to stderr"""
    print("warning: %s" % msg, file=sys.stderr)


def keyword_to_arch(keyword):
    """Given a keyword, strip it down to its arch value

    When an ARCH shows up in KEYWORDS, it may have prefixes like ~ or -.
    Strip all that cruft off to get back to the ARCH.
    """
    return keyword.lstrip("-~")


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
    for g in ("-*", "*", "~*"):
        if g in arches:
            arches.remove(g)
            keywords.append(g)

    def arch_key(keyword):
        """Callback for python sorting functions

        Used to turn a Gentoo keyword into a sortable form.
        """
        # Sort independent of leading marker (~ or -).
        arch = keyword_to_arch(keyword)

        # A keyword may have a "-" in it.  We split on that and sort
        # by the two resulting items.  The part after the hyphen is
        # the primary key.
        if "-" in arch:
            arch, plat = arch.split("-", 1)
        else:
            arch, plat = arch, ""

        return (plat, arch)

    keywords += sorted(arches, key=arch_key)

    return keywords


def diff_keywords(old_keywords, new_keywords, style="color-inline"):
    """Show pretty diff between list of keywords

    Args:
      old_keywords: The old set of KEYWORDS
      new_keywords: The new set of KEYWORDS
      style: The diff style

    Returns:
      A string containing the diff output ready to shown to the user
    """

    def show_diff(s):
        output = ""

        for tag, i0, i1, j0, j1 in s.get_opcodes():
            if tag == "equal":
                output += s.a[i0:i1]

            if tag in ("delete", "replace"):
                o = s.a[i0:i1]
                if style == "color-inline":
                    o = colorize("bg_darkred", o)
                else:
                    o = "-{%s}" % o
                output += o

            if tag in ("insert", "replace"):
                o = s.b[j0:j1]
                if style == "color-inline":
                    o = colorize("bg_darkgreen", o)
                else:
                    o = "+{%s}" % o
                output += o

        return output

    sold = str(" ".join(old_keywords))
    snew = str(" ".join(new_keywords))
    s = difflib.SequenceMatcher(str.isspace, sold, snew, autojunk=False)
    return show_diff(s)


def process_keywords(keywords, ops, arch_status=None):
    """Process |ops| for |keywords|"""
    new_keywords = set(keywords).copy()

    # Process each op one at a time.
    for op, oarch, refarch in ops:
        # Figure out which keywords we need to modify.
        if oarch == "all":
            if arch_status is None:
                raise ValueError('unable to process "all" w/out profiles.desc')
            old_arches = {keyword_to_arch(a) for a in new_keywords}
            if op is None:
                # Process just stable keywords.
                arches = [
                    k
                    for k, v in arch_status.items()
                    if v[1] == "arch" and k in old_arches
                ]
            else:
                # Process all possible keywords.  We use the arch_status as a
                # master list.  If it lacks some keywords, then we might miss
                # somethings here, but not much we can do.
                arches = list(old_arches)

            # We ignore the glob arch as we never want to tweak it.
            if "*" in arches:
                arches.remove("*")

            # For keywords that are explicitly disabled, do not update.  When
            # people use `ekeyword ~all ...` or `ekeyword all ...`, they rarely
            # (if ever) want to change a '-sparc' to 'sparc' or '-sparc' to
            # '~sparc'.  We force people to explicitly do `ekeyword sparc ...`
            # in these cases.
            arches = [x for x in arches if "-" + x not in new_keywords]
        else:
            arches = [oarch]

        if refarch:
            # Figure out the state for this arch based on the reference arch.
            # TODO: Add support for "all" keywords.
            # XXX: Should this ignore the '-' state ?  Does it make sense to
            #      sync e.g. "s390" to "-ppc" ?
            refkeyword = [x for x in new_keywords if refarch == keyword_to_arch(x)]
            if not refkeyword:
                op = "^"
            elif refkeyword[0].startswith("~"):
                op = "~"
            elif refkeyword[0].startswith("-"):
                op = "-"
            else:
                op = None

        # Finally do the actual update of the keywords list.
        for arch in arches:
            new_keywords -= {f"{x}{arch}" for x in ("", "~", "-")}

            if op is None:
                new_keywords.add(arch)
            elif op in ("~", "-"):
                new_keywords.add(f"{op}{arch}")
            elif op == "^":
                # Already deleted.  Whee.
                pass
            else:
                raise ValueError("unknown operation %s" % op)

    return new_keywords


def process_content(
    ebuild, data, ops, arch_status=None, verbose=0, quiet=0, style="color-inline"
):
    """Process |ops| for |data|"""
    # Set up the user display style based on verbose/quiet settings.
    if verbose > 1:
        disp_name = ebuild

        def logit(msg):
            print(f"{disp_name}: {msg}")

    elif quiet > 1:

        def logit(_msg):
            pass

    else:
        # Chop the full path and the .ebuild suffix.
        disp_name, _, _ = os.path.basename(ebuild).partition(".ebuild")

        def logit(msg):
            print(f"{disp_name}: {msg}")

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
        old_keywords_original = m.group(3).split()  # preserve original order
        old_keywords = set(old_keywords_original)
        new_keywords = process_keywords(old_keywords, ops, arch_status=arch_status)

        were_sorted_already = old_keywords_original == sort_keywords(
            old_keywords_original
        )

        # Finally let's present the results to the user.
        if (
            (new_keywords != old_keywords)
            or (not ops and not were_sorted_already)
            or verbose
        ):
            # Only do the diff work if something actually changed.
            updated = True

            if not ops:
                # We're sorting only so we want to compare with the
                # unsorted original (or changes in order will not show)
                old_keywords = old_keywords_original
            else:
                # We changed keywords so let's diff sorted versions
                # so that keywords changes are easy to spot
                old_keywords = sort_keywords(old_keywords)

            new_keywords = sort_keywords(new_keywords)
            line = '{}"{}"{}\n'.format(m.group(1), " ".join(new_keywords), m.group(5))
            if style in ("color-inline", "inline"):
                logit(diff_keywords(old_keywords, new_keywords, style=style))
            else:
                if style == "long-multi":
                    logit(
                        " ".join(
                            [
                                "%*s" % (len(keyword_to_arch(x)) + 1, x)
                                for x in old_keywords
                            ]
                        )
                    )
                    logit(
                        " ".join(
                            [
                                "%*s" % (len(keyword_to_arch(x)) + 1, x)
                                for x in new_keywords
                            ]
                        )
                    )
                else:
                    deleted_keywords = [
                        x for x in old_keywords if x not in new_keywords
                    ]
                    logit("--- %s" % " ".join(deleted_keywords))
                    added_keywords = [x for x in new_keywords if x not in old_keywords]
                    logit("+++ %s" % " ".join(added_keywords))

        content.append(line)

    if not updated:
        logit("no updates")

    return updated, content


def process_ebuild(
    ebuild,
    ops,
    arch_status=None,
    verbose=0,
    quiet=0,
    dry_run=False,
    style="color-inline",
    manifest=False,
):
    """Process |ops| for |ebuild|

    Args:
      ebuild: The ebuild file to operate on & update in place
      ops: An iterable of operations (Op objects) to perform on |ebuild|
      arch_status: A dict mapping default arches to their stability; see the
                   load_profile_data function for more details
      verbose: Be verbose; show various status messages
      quiet: Be quiet; only show errors
      dry_run: Do not make any changes to |ebuild|; show what would be done
      style: The diff style

    Returns:
      Whether any updates were processed
    """
    with open(ebuild, encoding="utf8") as f:
        updated, content = process_content(
            ebuild,
            f,
            ops,
            arch_status=arch_status,
            verbose=verbose,
            quiet=quiet,
            style=style,
        )
        if updated and not dry_run:
            with open(ebuild, "w", encoding="utf8") as f:
                f.writelines(content)
            if manifest:
                subprocess.check_call(["ebuild", ebuild, "manifest"])
    return updated


def portage_settings():
    """Return the portage settings we care about."""
    # Portage creates the db member on the fly which confuses the linter.
    return portage.db[portage.root]["vartree"].settings


def arg_to_op(arg):
    """Convert a command line |arg| to an Op"""
    arch_prefixes = ("-", "~", "^")

    op = None
    arch = arg
    refarch = None

    if arg and arg[0] in arch_prefixes:
        op, arch = arg[0], arg[1:]

    if "=" in arch:
        if not op is None:
            raise ValueError("Cannot use an op and a refarch")
        arch, refarch = arch.split("=", 1)

    return Op(op, arch, refarch)


def ignorable_arg(arg, quiet=0):
    """Whether it's ok to ignore this argument"""
    if os.path.isdir(arg):
        if not quiet:
            warning("ignoring directory %s" % arg)
        return True

    WHITELIST = (
        "Manifest",
        "metadata.xml",
    )
    base = os.path.basename(arg)
    if base in WHITELIST or base.startswith(".") or base.endswith("~"):
        if not quiet:
            warning("ignoring file: %s" % arg)
        return True

    return False


def args_to_work(args, arch_status=None, _repo=None, quiet=0):
    """Process |args| into a list of work itmes (ebuild/arches to update)"""
    work = []
    todo_arches = []
    last_todo_arches = []

    for arg in args:
        if ignorable_arg(arg, quiet=quiet):
            pass
        elif os.path.isfile(arg):
            if not todo_arches:
                todo_arches = last_todo_arches
            work.append([arg, todo_arches])
            last_todo_arches = todo_arches
            todo_arches = []
        else:
            op = arg_to_op(arg)
            if not arch_status or op.arch in arch_status:
                todo_arches.append(op)
            else:
                raise ValueError("unknown arch/argument: %s" % arg)

    if todo_arches:
        raise ValueError("missing ebuilds to process!")

    return work


def get_parser():
    """Return an argument parser for ekeyword"""
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument(
        "-m",
        "--manifest",
        default=False,
        action="store_true",
        help="Run `ebuild manifest` on the ebuild after modifying it",
    )
    parser.add_argument(
        "-n",
        "--dry-run",
        default=False,
        action="store_true",
        help="Show what would be changed, but do not commit",
    )
    parser.add_argument(
        "-v",
        "--verbose",
        action="count",
        default=0,
        help="Be verbose while processing things",
    )
    parser.add_argument(
        "-q",
        "--quiet",
        action="count",
        default=0,
        help="Be quiet while processing things (only show errors)",
    )
    parser.add_argument(
        "--format",
        default="auto",
        dest="style",
        choices=("auto", "color-inline", "inline", "short-multi", "long-multi"),
        help="Select output format for showing differences",
    )
    parser.add_argument(
        "-V",
        "--version",
        action="version",
        version=__version__,
        help="Show version information",
    )
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
        if arg.startswith("--"):
            if arg == "--":
                work_args += argv
                break
            else:
                parse_args.append(arg)
            # Handle flags that take arguments.
            if arg in ("--format",):
                if argv:
                    parse_args.append(argv.pop(0))
        elif len(arg) == 2 and arg[0] == "-":
            parse_args.append(arg)
        else:
            work_args.append(arg)

    parser = get_parser()
    opts = parser.parse_args(parse_args)
    if not work_args:
        parser.error("need ebuilds to process")

    if opts.style == "auto":
        if not (
            portage_settings().get("NO_COLOR")
            or portage_settings().get("NOCOLOR", "false").lower() in ("no", "false")
        ):
            nocolor()
            opts.style = "short"
        else:
            opts.style = "color-inline"

    arch_status = load_profile_data()
    try:
        work = args_to_work(work_args, arch_status=arch_status, quiet=opts.quiet)
    except ValueError as e:
        parser.error(e)

    for ebuild, ops in work:
        process_ebuild(
            ebuild,
            ops,
            arch_status=arch_status,
            verbose=opts.verbose,
            quiet=opts.quiet,
            dry_run=opts.dry_run,
            style=opts.style,
            manifest=opts.manifest,
        )

    return os.EX_OK


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
