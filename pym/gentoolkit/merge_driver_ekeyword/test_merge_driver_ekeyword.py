#!/usr/bin/python
# Copyright 2024 Gentoo Authors
# Distributed under the terms of the GNU General Public License v2

"""Unittests for merge_driver_ekeyword"""

import itertools
import os
import pathlib
import pytest
import shutil
import tempfile

from gentoolkit.merge_driver_ekeyword import merge_driver_ekeyword


TESTDIR = pathlib.Path(__file__).parent / "tests"
TESTDIRS = [os.path.dirname(x) for x in TESTDIR.rglob("common-ancestor.ebuild")]
TESTDATA = itertools.product(TESTDIRS, (False, True))


def file_contents(filename):
    with open(filename) as file:
        return file.readlines()


@pytest.mark.parametrize("testdir,reverse", TESTDATA)
def test_merge(testdir, reverse):
    with tempfile.TemporaryDirectory() as tmpdir:
        shutil.copytree(testdir, tmpdir, dirs_exist_ok=True)

        O = os.path.join(tmpdir, "common-ancestor.ebuild")
        if reverse:
            A = os.path.join(tmpdir, "B.ebuild")
            B = os.path.join(tmpdir, "A.ebuild")
        else:
            A = os.path.join(tmpdir, "A.ebuild")
            B = os.path.join(tmpdir, "B.ebuild")
        P = "expected.ebuild"
        expected = os.path.join(tmpdir, P)

        # A.ebuild and B.ebuild can be merged iff expected.ebuild exists.
        if os.path.exists(expected):
            assert 0 == merge_driver_ekeyword.main([O, A, B, P])
            assert file_contents(expected) == file_contents(A)
        else:
            assert -1 == merge_driver_ekeyword.merge_keywords(O, A, B, P)
            assert -1 == merge_driver_ekeyword.merge_keywords(O, B, A, P)
