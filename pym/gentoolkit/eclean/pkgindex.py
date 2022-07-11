#!/usr/bin/python

# Copyright 2003-2010 Gentoo Foundation
# Distributed under the terms of the GNU General Public License v2

import subprocess
import os
import sys

import gentoolkit.pprinter as pp
from gentoolkit.eprefix import EPREFIX

import portage
from portage.module import (
    InvalidModuleName,
    Modules,
)
from portage.emaint.main import TaskHandler


class PkgIndex:
    """Handle the cleaning of the binpkg Package
    Index file

    @type output: class
    @param output: optional output class for printing
    """

    def __init__(self, controller=None):
        self.controller = controller
        # backup command line call
        self.emaint_cmd = "%s/usr/sbin/emaint --fix binhost" % EPREFIX

    def _get_emaint_binhost(self):
        """Obtain a reference to the binhost module class

        @sets: self.binhost to BinhostHandler class
        @rtype: boolean
        """
        try:
            self.emaint_control = Modules()
            self.binhost = self.emaint_control._get_class("binhost")
        except InvalidModuleName as er:
            print(pp.error("Error importing emaint binhost module"), file=sys.stderr)
            print(pp.error("Original error: " + er), file=sys.stderr)
        except:
            return False
        return True

    def clean_pkgs_index(self, quiet):
        """This will clean the binpkgs packages index file

        @param quiet: boolean
        @return: the difference in file size
        """
        file_ = os.path.join(portage.settings["PKGDIR"], "Packages")
        statinfo = os.stat(file_)
        size1 = statinfo.st_size
        show_progress = not quiet
        if self._get_emaint_binhost():
            self.taskmaster = TaskHandler(show_progress_bar=show_progress)
            tasks = [self.binhost]
            self.taskmaster.run_tasks(tasks)
        else:
            self.call_emaint()
        statinfo = os.stat(file_)
        clean_size = size1 - statinfo.st_size
        self.controller(clean_size, "Packages Index", file_, "Index")
        return clean_size

    def call_emaint(self):
        """Run the stand alone emaint script from
        a subprocess call.

        @rtype: integer
        @return: the difference in file size
        """
        try:
            retcode = subprocess.call(self.emaint_cmd, shell=True)
            if retcode < 0:
                print(
                    pp.error("Child was terminated by signal" + str(-retcode)),
                    file=sys.stderr,
                )
        except OSError as e:
            print(pp.error("Execution failed:" + e), file=sys.stderr)
