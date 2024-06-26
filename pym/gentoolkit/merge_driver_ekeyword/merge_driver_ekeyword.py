#!/usr/bin/python3
#
# Copyright 2020-2024 Gentoo Authors
# Distributed under the terms of the GNU General Public License v2 or later

"""
Custom git merge driver for handling conflicts in KEYWORDS assignments

See https://git-scm.com/docs/gitattributes#_defining_a_custom_merge_driver
"""

import difflib
import os
import shutil
import sys
import tempfile

from typing import Optional
from collections.abc import Sequence

from gentoolkit.ekeyword import ekeyword


KeywordChanges = list[tuple[Optional[list[str]], Optional[list[str]]]]


def keyword_array(keyword_line: str) -> list[str]:
    # Find indices of string inside the double-quotes
    i1: int = keyword_line.find('"') + 1
    i2: int = keyword_line.rfind('"')

    # Split into array of KEYWORDS
    return keyword_line[i1:i2].split(" ")


def keyword_line_changes(old: str, new: str) -> KeywordChanges:
    a: list[str] = keyword_array(old)
    b: list[str] = keyword_array(new)

    s = difflib.SequenceMatcher(a=a, b=b)

    changes: KeywordChanges = []
    for tag, i1, i2, j1, j2 in s.get_opcodes():
        if tag == "replace":
            changes.append(
                (a[i1:i2], b[j1:j2]),
            )
        elif tag == "delete":
            changes.append(
                (a[i1:i2], None),
            )
        elif tag == "insert":
            changes.append(
                (None, b[j1:j2]),
            )
        else:
            assert tag == "equal"
    return changes


def keyword_changes(ebuild1: str, ebuild2: str) -> Optional[KeywordChanges]:
    with open(ebuild1) as e1, open(ebuild2) as e2:
        lines1 = e1.readlines()
        lines2 = e2.readlines()

        diff = difflib.unified_diff(lines1, lines2, n=0)
        assert next(diff) == "--- \n"
        assert next(diff) == "+++ \n"

        hunk: int = 0
        old: str = ""
        new: str = ""

        for line in diff:
            if line.startswith("@@ "):
                if hunk > 0:
                    break
                hunk += 1
            elif line.startswith("-"):
                if old or new:
                    break
                old = line
            elif line.startswith("+"):
                if not old or new:
                    break
                new = line
        else:
            if "KEYWORDS=" in old and "KEYWORDS=" in new:
                return keyword_line_changes(old, new)
        return None


def apply_keyword_changes(ebuild: str, pathname: str, changes: KeywordChanges) -> int:
    result: int = 0

    with tempfile.TemporaryDirectory() as tmpdir:
        # ekeyword will only modify files named *.ebuild, so make a symlink
        ebuild_symlink: str = os.path.join(tmpdir, os.path.basename(pathname))
        os.symlink(os.path.join(os.getcwd(), ebuild), ebuild_symlink)

        for removals, additions in changes:
            args = []
            if removals:
                for rem in removals:
                    # Drop leading '~' and '-' characters and prepend '^'
                    i = 1 if rem[0] in ("~", "-") else 0
                    args.append("^" + rem[i:])
            if additions:
                args.extend(additions)
            args.append(ebuild_symlink)

            result = ekeyword.main(args)
            if result != 0:
                break

    return result


def merge_keywords(O, A, B, P) -> int:
    # Get changes to KEYWORDS= from %O to %B
    if changes := keyword_changes(O, B):
        # Apply %O -> %B changes to %A
        return apply_keyword_changes(A, P, changes)
    return -1


def main(argv: Sequence[str]) -> int:
    if len(argv) != 4:
        return -1

    O = argv[0]  # %O - filename of original
    A = argv[1]  # %A - filename of our current version
    B = argv[2]  # %B - filename of the other branch's version
    P = argv[3]  # %P - original path of the file

    if merge_keywords(O, A, B, P) == 0:
        return 0

    # Try in reverse
    if merge_keywords(O, B, A, P) == 0:
        # Merged file should be left in %A
        shutil.move(B, A)
        return 0

    try:
        os.execlp(
            "git",
            "git",
            "merge-file",
            "-L",
            "HEAD",
            "-L",
            "base",
            "-L",
            "ours",
            A,
            O,
            B,
        )
    except OSError:
        return -1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
