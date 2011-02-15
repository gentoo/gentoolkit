#!/usr/bin/python
# -*- coding: utf-8 -*-


# Author: Sławomir Lis <lis.slawek@gmail.com>
# revdep-rebuild original author: Stanislav Brabec
# revdep-rebuild original rewrite Author: Michael A. Smith
# Current Maintainer: Paul Varner <fuzzyray@gentoo.org>

# Creation date: 2010/10/17
# License: BSD

import subprocess
import os
import sys
import re
import getopt
import signal
import stat
import time
import glob
import portage
import logging
from portage import portdb
from portage.output import bold, red, blue, yellow, green, nocolor

from analyse import analyse
from stuff import exithandler, get_masking_status
from cache import check_temp_files, read_cache
from assign import get_slotted_cps
from settings import SETTINGS


APP_NAME = sys.argv[0]
VERSION = '0.1-r6'

__productname__ = "revdep-ng"



def print_usage():
    print APP_NAME + ': (' + VERSION +')'
    print
    print 'This is free software; see the source for copying conditions.'
    print
    print 'Usage: ' + APP_NAME + ' [OPTIONS] [--] [EMERGE_OPTIONS]'
    print
    print 'Broken reverse dependency rebuilder, python implementation.'
    print
    print 'Available options:'
    print '''
  -C, --nocolor        Turn off colored output
  -d, --debug          Print debug informations
  -e, --exact          Emerge based on exact package version
  -h, --help           Print this usage
  -i, --ignore         Ignore temporary files from previous runs (also won't create any)
  -L, --library NAME   Emerge existing packages that use the library with NAME
      --library=NAME   NAME can be a full or partial library name
  -l, --no-ld-path     Do not set LD_LIBRARY_PATH
  -o, --no-order       Do not check the build order
                       (Saves time, but may cause breakage.)
  -p, --pretend        Do a trial run without actually emerging anything
                       (also passed to emerge command)
  -q, --quiet          Be less verbose (also passed to emerge command)
  -v, --verbose        Be more verbose (also passed to emerge command)
'''
    print 'Calls emerge, options after -- are ignored by ' + APP_NAME
    print 'and passed directly to emerge.'



# functions


def _match_str_in_list(lst, stri):
    for l in lst:
        if stri.endswith(l):
            return l
    return False


# Runs from here
if __name__ == "__main__":
    logger = logging.getLogger()
    log_handler = logging.StreamHandler()
    log_fmt = logging.Formatter('%(msg)s')
    log_handler.setFormatter(log_fmt)
    logger.addHandler(log_handler)
    logger.setLevel(logging.WARNING)

    _libs_to_check = set()

    try:
        opts, args = getopt.getopt(sys.argv[1:], 'dehiklopqvCL:P', ['nocolor', 'debug', 'exact', 'help', 'ignore',\
            'keep-temp', 'library=', 'no-ld-path', 'no-order', 'pretend', 'no-pretend', 'no-progress', 'quiet', 'verbose'])

        for key, val in opts:
            if key in ('-h', '--help'):
                print_usage()
                sys.exit(0)
            elif key in ('-q', '--quiet'):
                logger.setLevel(logging.ERROR)
                SETTINGS['VERBOSITY'] = 0
            elif key in ('-v', '--verbose'):
                logger.setLevel(logging.INFO)
                SETTINGS['VERBOSITY'] = 2
            elif key in ('-d', '--debug'):
                logger.setLevel(logging.DEBUG)
                SETTINGS['VERBOSITY'] = 3
            elif key in ('-p', '--pretend'):
                SETTINGS['PRETEND'] = True
            elif key == '--no-pretend':
                SETTINGS['NO_PRETEND'] = True
            elif key in ('-e', '--exact'):
                SETTINGS['EXACT'] = True
            elif key in ('-C', '--nocolor', '--no-color'):
                nocolor()
            elif key in ('-L', '--library', '--library='):
                _libs_to_check = _libs_to_check.union(val.split(','))
            elif key in ('-i', '--ignore'):
                SETTINGS['USE_TMP_FILES'] = False

        args = " " + " ".join(args)
    except getopt.GetoptError:
        logging.info(red('Unrecognized option\n'))
        print_usage()
        sys.exit(2)

    if not sys.stdout.isatty():
        nocolor()

    if os.getuid() != 0 and not SETTINGS['PRETEND']:
        logger.warn(blue(' * ') + yellow('You are not root, adding --pretend to portage options'))
        SETTINGS['PRETEND'] = True
    elif not SETTINGS['PRETEND'] and SETTINGS['IS_DEV'] and not SETTINGS['NO_PRETEND']:
        logger.warn(blue(' * ') + yellow('This is a development version, so it may not work correctly'))
        logger.warn(blue(' * ') + yellow('Adding --pretend to portage options anyway'))
        logger.info(blue(' * ') + 'If you\'re sure, you can add --no-pretend to revdep options')
        SETTINGS['PRETEND'] = True


    signal.signal(signal.SIGINT, exithandler)
    signal.signal(signal.SIGTERM, exithandler)
    signal.signal(signal.SIGPIPE, signal.SIG_DFL)

    analyze_cache = {}
    if SETTINGS['USE_TMP_FILES'] and check_temp_files():
        libraries, la_libraries, libraries_links, binaries = read_cache()
        assigned = analyse(libraries=libraries, la_libraries=la_libraries, \
                       libraries_links=libraries_links, binaries=binaries, _libs_to_check=_libs_to_check)
    else:
        assigned = analyse()

    if not assigned:
        logger.warn('\n' + bold('Your system is consistent'))
        sys.exit(0)


    has_masked = False
    tmp = []
    for a in assigned:
        if get_masking_status(a):
            has_masked = True
            logger.warn('!!! ' + red('All ebuilds that could satisfy: ') + green(a) + red(' have been masked'))
        else:
            tmp.append(a)
    assigned = tmp

    if has_masked:
        logger.info(red(' * ') + 'Unmask all ebuild listed above and call revdep-rebuild again or manually emerge given packages.')


    if SETTINGS['EXACT']:
        emerge_command = '=' + ' ='.join(assigned)
    else:
        emerge_command = ' '.join(get_slotted_cps(assigned, logger))
    if SETTINGS['PRETEND']:
        args += ' --pretend'
    if SETTINGS['VERBOSITY'] >= 2:
        args += ' --verbose'
    elif SETTINGS['VERBOSITY'] < 1:
        args += ' --quiet'

    if len(emerge_command) == 0:
        logger.warn(bold('\nThere is nothing to emerge. Exiting.'))
        sys.exit(0)

    emerge_command = args + ' --oneshot ' + emerge_command

    logger.warn(yellow('\nemerge') + bold(emerge_command))
    os.system('emerge ' + emerge_command)

