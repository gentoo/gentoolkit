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
import platform
from portage import portdb
from portage.output import bold, red, blue, yellow, green, nocolor

APP_NAME = sys.argv[0]
VERSION = '0.1-r3'


__productname__ = "revdep-ng"



# configuration variables
DEFAULT_LD_FILE = 'etc/ld.so.conf'
DEFAULT_ENV_FILE = 'etc/profile.env'


# global variables
PRINT_DEBUG = False      #program in debug mode

PRETEND = False     #pretend only
EXACT = False      #exact package version
USE_TMP_FILES = True #if program should use temporary files from previous run
DEFAULT_TMP_DIR = '/tmp/revdep-rebuild' #cache default location
VERBOSITY = 1      #verbosity level; 0-quiet, 1-norm., 2-verbose

IS_DEV = True       #True for dev. version, False for stable
#used when IS_DEV is True, False forces to call emerge with --pretend
# can be set True from the cli with the --no-pretend option
NO_PRETEND = False 



# util. functions
def call_program(args):
    ''' Calls program with specified parameters and returns stdout '''
    subp = subprocess.Popen(args, stdout=subprocess.PIPE, \
                                stderr=subprocess.PIPE)
    stdout, stderr = subp.communicate()
    return stdout


def print_v(verbosity, args):
    """Prints to stdout according to the verbosity level 
    and the global VERBOSITY level
    
    @param verbosity: integer
    @param args: string to print
    """
    if verbosity > VERBOSITY:
        return
    print args


def exithandler(signum, frame):
    print 'Signal caught!'
    print 'Bye!'
    signal.signal(signal.SIGINT, signal.SIG_IGN)
    signal.signal(signal.SIGTERM, signal.SIG_IGN)
    sys.exit(1)


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
def parse_conf(conf_file=None, visited=None):
    ''' Parses supplied conf_file for libraries pathes.
        conf_file is file or files to parse
        visited is set of files already parsed
    '''

    if conf_file is None:
        conf_file = os.path.join(portage.root, DEFAULT_LD_FILE)

    lib_dirs = set()
    to_parse = set()

    if isinstance(conf_file, basestring):
        conf_file = [conf_file]

    for conf in conf_file:
        try:
            with open(conf) as f:
                for line in f.readlines():
                    line = line.strip()
                    if line.startswith('#'):
                        continue
                    elif line.startswith('include'):
                        include_line = line.split()[1:]
                        for included in include_line:
                            if not included.startswith('/'):
                                path = os.path.join(os.path.dirname(conf), \
                                                    included)
                            else:
                                path = included

                            to_parse = to_parse.union(glob.glob(path))
                    else:
                        lib_dirs.add(line)
        except EnvironmentError:
            print_v(2, 'Error when parsing file %s' %conf)

    if visited is None:
        visited = set()

    visited = visited.union(conf_file)
    to_parse = to_parse.difference(visited)
    if to_parse:
        lib_dirs = lib_dirs.union(parse_conf(to_parse, visited))

    return lib_dirs


def prepare_search_dirs():
    ''' Lookup for search dirs. Returns tuple with two lists,
        (list_of_bin_dirs, list_of_lib_dirs)
    '''

    bin_dirs = set(['/bin', '/usr/bin', ])
    lib_dirs = set(['/lib', '/usr/lib', ])

    try:
        with open(os.path.join(portage.root, DEFAULT_ENV_FILE), 'r') as f:
            for line in f.readlines():
                line = line.strip()
                m = re.match("^export (ROOT)?PATH='([^']+)'", line)
                if m is not None:
                    bin_dirs = bin_dirs.union(set(m.group(2).split(':')))
    except EnvironmentError:
        print_v(2, 'Could not open file %s' % f)

    lib_dirs = parse_conf()
    return (bin_dirs, lib_dirs)


def parse_revdep_config():
    ''' Parses all files under /etc/revdep-rebuild/ and returns
        tuple of: (masked_dirs, masked_files, search_dirs)'''

    search_dirs = set()
    masked_dirs = set()
    masked_files = set()

    for f in os.listdir('/etc/revdep-rebuild/'):
        for line in open(os.path.join('/etc/revdep-rebuild', f)):
            line = line.strip()
            if not line.startswith('#'): #first check for comment, we do not want to regex all lines
                m = re.match('LD_LIBRARY_MASK=\\"([^"]+)\\"', line)
                if m is not None:
                    s = m.group(1).split(' ')
                    masked_files = masked_files.union(s)
                    continue
                m = re.match('SEARCH_DIRS_MASK=\\"([^"]+)\\"', line)
                if m is not None:
                    s = m.group(1).split(' ')
                    for ss in s:
                        masked_dirs = masked_dirs.union(glob.glob(ss))
                    continue
                m = re.match('SEARCH_DIRS=\\"([^"]+)\\"', line)
                if m is not None:
                    s = m.group(1).split()
                    for ss in s:
                        search_dirs = search_dirs.union(glob.glob(ss))
                    continue

    return (masked_dirs, masked_files, search_dirs)


def collect_libraries_from_dir(dirs, mask):
    ''' Collects all libraries from specified list of directories.
        mask is list of pathes, that are ommited in scanning, can be eighter single file or entire directory
        Returns tuple composed of: list of libraries, list of symlinks, and toupe with pair
        (symlink_id, library_id) for resolving dependencies
    '''


    found_directories = []  # contains list of directories found; allow us to reduce number of fnc calls
    found_files = []
    found_symlinks = []
    found_la_files = [] # la libraries
    symlink_pairs = []  # list of pairs symlink_id->library_id

    for d in dirs:
        if d in mask:
            continue

        try:
            for l in os.listdir(d):
                l = os.path.join(d, l)
                if l in mask:
                    continue

                if os.path.isdir(l):
                    if os.path.islink(l):
                        #we do not want scan symlink-directories
                        pass
                    else:
                        found_directories.append(l)
                elif os.path.isfile(l):
                    if l.endswith('.so') or '.so.' in l:
                        if l in found_files or l in found_symlinks:
                            continue

                        if os.path.islink(l):
                            found_symlinks.append(l)
                            abs_path = os.path.realpath(l)
                            if abs_path in found_files:
                                i = found_files.index(abs_path)
                            else:
                                found_files.append(abs_path)
                                i = len(found_files)-1
                            symlink_pairs.append((len(found_symlinks)-1, i,))
                        else:
                            found_files.append(l)
                        continue
                    elif l.endswith('.la'):
                        if l in found_la_files:
                            continue

                        found_la_files.append(l)
                    else:
                        # sometimes there are binaries in libs' subdir, for example in nagios
                        if not os.path.islink(l):
                            if l in found_files or l in found_symlinks:
                                continue
                            prv = os.stat(l)[stat.ST_MODE]
                            if prv & stat.S_IXUSR == stat.S_IXUSR or \
                                    prv & stat.S_IXGRP == stat.S_IXGRP or \
                                    prv & stat.S_IXOTH == stat.S_IXOTH:
                                found_files.append(l)
        except:
            pass


    if found_directories:
        f,a,l,p = collect_libraries_from_dir(found_directories, mask)
        found_files+=f
        found_la_files+=a
        found_symlinks+=l
        symlink_pairs+=p

    return (found_files, found_la_files, found_symlinks, symlink_pairs)


def collect_binaries_from_dir(dirs, mask):
    ''' Collects all binaries from specified list of directories.
        mask is list of pathes, that are ommited in scanning, can be eighter single file or entire directory
        Returns list of binaries
    '''

    found_directories = []  # contains list of directories found; allow us to reduce number of fnc calls
    found_files = []

    for d in dirs:
        if d in mask:
            continue

        try:
            for l in os.listdir(d):
                l = os.path.join(d, l)
                if d in mask:
                    continue

                if os.path.isdir(l):
                    if os.path.islink(l):
                        #we do not want scan symlink-directories
                        pass
                    else:
                        found_directories.append(l)
                elif os.path.isfile(l):
                    #we're looking for binaries, and with binaries we do not need links, thus we can optimize a bit
                    if not os.path.islink(l):
                        prv = os.stat(l)[stat.ST_MODE]
                        if prv & stat.S_IXUSR == stat.S_IXUSR or \
                                prv & stat.S_IXGRP == stat.S_IXGRP or \
                                prv & stat.S_IXOTH == stat.S_IXOTH:
                            found_files.append(l)
        except:
            pass

    if found_directories:
        found_files += collect_binaries_from_dir(found_directories, mask)

    return found_files


def _match_str_in_list(lst, stri):
    for l in lst:
        if stri.endswith(l):
            return l
    return False


def prepare_checks(files_to_check, libraries, bits):
    ''' Calls scanelf for all files_to_check, then returns found libraries and dependencies
    '''

    libs = [] # libs found by scanelf
    dependencies = [] # list of lists of files (from file_to_check) that uses
                      # library (for dependencies[id] and libs[id] => id==id)

    for line in call_program(['scanelf', '-M', str(bits), '-nBF', '%F %n',]+files_to_check).strip().split('\n'):
        r = line.strip().split(' ')
        if len(r) < 2: # no dependencies?
            continue

        deps = r[1].split(',')
        for d in deps:
            if d in libs:
                i = libs.index(d)
                dependencies[i].append(r[0])
            else:
                libs.append(d)
                dependencies.append([r[0],])
    return (libs, dependencies)


def extract_dependencies_from_la(la, libraries, to_check):
    broken = []
    for f in la:
        if not os.path.exists(f):
            continue

        for line in open(f, 'r').readlines():
            line = line.strip()
            if line.startswith('dependency_libs='):
                m = re.match("dependency_libs='([^']+)'", line)
                if m is not None:
                    for el in m.group(1).split(' '):
                        el = el.strip()
                        if len(el) < 1 or el.startswith('-'):
                            continue

                        if el in la or el in libraries:
                            pass
                        else:
                            if to_check:
                                _break = False
                                for tc in to_check:
                                    if tc in el:
                                        _break = True
                                        break
                                if not _break:
                                    continue

                            print_v(1, yellow(' * ') + f + ' is broken (requires: ' + bold(el))
                            broken.append(f)
    return broken



def find_broken(found_libs, system_libraries, to_check):
    ''' Search for broken libraries.
        Check if system_libraries contains found_libs, where
        system_libraries is list of obsolute pathes and found_libs
        is list of library names.
    '''

    # join libraries and looking at it as string is way too faster than for-jumping

    broken = []
    sl = '|'.join(system_libraries)

    if not to_check:
        for f in found_libs:
            if f+'|' not in sl:
                broken.append(found_libs.index(f))
    else:
        for tc in to_check:
            for f in found_libs:
                if tc in f:# and f+'|' not in sl:
                    broken.append(found_libs.index(f))

    return broken


def main_checks(found_libs, broken, dependencies):
    ''' Checks for broken dependencies.
        found_libs have to be the same as returned by prepare_checks
        broken is list of libraries found by scanelf
        dependencies is the value returned by prepare_checks
    '''

    broken_pathes = []

    for b in broken:
        f = found_libs[b]
        print_v(1, 'Broken files that requires: ' + bold(f))
        for d in dependencies[b]:
            print_v(1, yellow(' * ') + d)
            broken_pathes.append(d)
    return broken_pathes


def assign_packages(broken, output):
    ''' Finds and returns packages that owns files placed in broken.
        Broken is list of files
    '''
    assigned = set()
    for group in os.listdir('/var/db/pkg'):
        for pkg in os.listdir('/var/db/pkg/' + group):
            f = '/var/db/pkg/' + group + '/' + pkg + '/CONTENTS'
            if os.path.exists(f):
                try:
                    with open(f, 'r') as cnt:
                        for line in cnt.readlines():
                            m = re.match('^obj (/[^ ]+)', line)
                            if m is not None:
                                m = m.group(1)
                                if m in broken:
                                    found = group+'/'+pkg
                                    if found not in assigned:
                                        assigned.add(found)
                                    print_v(1, '\t' + m + ' -> ' + bold(found))
                except:
                    output(1, red(' !! Failed to read ' + f))

    return assigned


def get_best_match(cpv, cp):
    """Tries to find another version of the pkg with the same slot
    as the deprecated installed version.  Failing that attempt to get any version
    of the same app
    
    @param cpv: string
    @param cp: string
    @rtype tuple: ([cpv,...], SLOT)
    """

    slot = portage.db[portage.root]["vartree"].dbapi.aux_get(cpv, ["SLOT"])
    print_v(1, yellow('Warning: ebuild "' + cpv + '" not found.'))
    print_v(1, 'Looking for %s:%s' %(cp, slot))
    try:
        m = portdb.match('%s:%s' %(cp, slot))
    except portage.exception.InvalidAtom:
        m = None

    if not m:
        print_v(1, red('Could not find ebuild for %s:%s' %(cp, slot)))
        slot = ['']
        m = portdb.match(cp)
        if not m:
            print_v(1, red('Could not find ebuild for ' + cp))
    return m, slot


def get_slotted_cps(cpvs):
    """Uses portage to reduce the cpv list into a cp:slot list and returns it
    """
    from portage.versions import catpkgsplit
    from portage import portdb

    cps = []
    for cpv in cpvs:
        parts = catpkgsplit(cpv)
        cp = parts[0] + '/' + parts[1]
        try:
            slot = portdb.aux_get(cpv, ["SLOT"])
        except KeyError:
            m, slot = get_best_match(cpv, cp)
            if not m:
                print_v(1, red("Installed package: %s is no longer available" %cp))
                continue

        if slot[0]:
            cps.append(cp + ":" + slot[0])
        else:
            cps.append(cp)

    return cps


def read_cache(temp_path=DEFAULT_TMP_DIR):
    ''' Reads cache information needed by analyse function.
        This function does not checks if files exists nor timestamps,
        check_temp_files should be called first
        @param temp_path: directory where all temp files should reside
        @return tuple with values of: libraries, la_libraries, libraries_links, symlink_pairs, binaries
    '''

    ret = {'libraries':[], 'la_libraries':[], 'libraries_links':[], 'binaries':[]}
    try:
        for key,val in ret.iteritems():
            f = open(os.path.join(temp_path, key))
            for line in f.readlines():
                val.append(line.strip())
            #libraries.remove('\n')
            f.close()
    except EnvironmentError:
        pass

    return (ret['libraries'], ret['la_libraries'], ret['libraries_links'], ret['binaries'])


def save_cache(to_save, temp_path=DEFAULT_TMP_DIR):
    ''' Tries to store caching information.
        @param to_save have to be dict with keys: libraries, la_libraries, libraries_links and binaries
    '''

    if not os.path.exists(temp_path):
        os.makedirs(temp_path)

    f = open(os.path.join(temp_path, 'timestamp'), 'w')
    f.write(str(int(time.time())))
    f.close()

    for key,val in to_save.iteritems():
        f = open(os.path.join(temp_path, key), 'w')
        for line in val:
            f.write(line + '\n')
        f.close()


def analyse(output=print_v, libraries=None, la_libraries=None, libraries_links=None, binaries=None):
    """Main program body.  It will collect all info and determine the
    pkgs needing rebuilding.

    @param output: optional print/data gathering routine. Defaults to print_v
            which prints to sys.stdout. Refer to print_v parameters for more detail.
    @rtype list: list of pkgs that need rebuilding
    """

    if libraries and la_libraries and libraries_links and binaries:
        output(1, blue(' * ') + bold('Found a valid cache, skipping collecting phase'))
    else:
        #TODO: add partial cache (for ex. only libraries) when found for some reason

        output(1, green(' * ') + bold('Collecting system binaries and libraries'))
        bin_dirs, lib_dirs = prepare_search_dirs()

        masked_dirs, masked_files, ld = parse_revdep_config()
        lib_dirs = lib_dirs.union(ld)
        bin_dirs = bin_dirs.union(ld)
        masked_dirs = masked_dirs.union(set(['/lib/modules', '/lib32/modules', '/lib64/modules',]))

        output(1, green(' * ') + bold('Collecting dynamic linking informations'))
        libraries, la_libraries, libraries_links, symlink_pairs = collect_libraries_from_dir(lib_dirs, masked_dirs)
        binaries = collect_binaries_from_dir(bin_dirs, masked_dirs)

        if USE_TMP_FILES:
            save_cache(to_save={'libraries':libraries, 'la_libraries':la_libraries, 'libraries_links':libraries_links, 'binaries':binaries})


    output(2, 'Found '+ str(len(libraries)) + ' libraries (+' + str(len(libraries_links)) + ' symlinks) and ' + str(len(binaries)) + ' binaries')

    output(1, green(' * ') + bold('Checking dynamic linking consistency'))
    output(2,'Search for ' + str(len(binaries)+len(libraries)) + ' within ' + str(len(libraries)+len(libraries_links)))
    libs_and_bins = libraries+binaries

    #l = []
    #for line in call_program(['scanelf', '-M', '64', '-BF', '%F',] + libraries).strip().split('\n'):
        #l.append(line)
    #libraries = l

    found_libs = []
    dependencies = []


    _bits, linkg = platform.architecture()
    if _bits.startswith('32'):
        bits = 32
    elif _bits.startswith('64'):
        bits = 64

    for av_bits in glob.glob('/lib[0-9]*') or ('/lib32',):
        bits = int(av_bits[4:])
        _libraries = call_program(['scanelf', '-M', str(bits), '-BF', '%F',] + libraries+libraries_links).strip().split('\n')

        found_libs, dependencies = prepare_checks(libs_and_bins, _libraries, bits)

        broken = find_broken(found_libs, _libraries, _libs_to_check)
        broken_la = extract_dependencies_from_la(la_libraries, _libraries, _libs_to_check)

        bits /= 2
        bits = int(bits)

    broken_pathes = main_checks(found_libs, broken, dependencies)
    broken_pathes += broken_la

    output(1, green(' * ') + bold('Assign files to packages'))

    return assign_packages(broken_pathes, output)


def check_temp_files(temp_path=DEFAULT_TMP_DIR, max_delay=3600):
    ''' Checks if temporary files from previous run are still available
        and if they aren't too old
        @param temp_path is directory, where temporary files should be found
        @param max_delay is maximum time difference (in seconds) when those files
                are still considered fresh and useful
        returns True, when files can be used, or False, when they don't
        exists or they are too old
    '''

    if not os.path.exists(temp_path) or not os.path.isdir(temp_path):
        return False

    timestamp_path = os.path.join(temp_path, 'timestamp')
    if not os.path.exists(timestamp_path) or not os.path.isfile(timestamp_path):
        return False

    try:
        f = open(timestamp_path)
        timestamp = int(f.readline())
        f.close()
    except:
        timestamp = 0
        return False

    diff = int(time.time()) - timestamp
    return max_delay > diff


# Runs from here
if __name__ == "__main__":
    _libs_to_check = set()

    try:
        opts, args = getopt.getopt(sys.argv[1:], 'dehiklopqvCL:P', ['nocolor', 'debug', 'exact', 'help', 'ignore',\
            'keep-temp', 'library=', 'no-ld-path', 'no-order', 'pretend', 'no-pretend', 'no-progress', 'quiet', 'verbose'])

        for key, val in opts:
            if key in ('-h', '--help'):
                print_usage()
                sys.exit(0)
            elif key in ('-q', '--quiet'):
                VERBOSITY = 0
            elif key in ('-v', '--verbose'):
                VERBOSITY = 2
            elif key in ('-d', '--debug'):
                PRINT_DEBUG = True
            elif key in ('-p', '--pretend'):
                PRETEND = True
            elif key == '--no-pretend':
                NO_PRETEND = True
            elif key in ('-e', '--exact'):
                EXACT = True
            elif key in ('-C', '--nocolor', '--no-color'):
                nocolor()
            elif key in ('-L', '--library', '--library='):
                _libs_to_check = _libs_to_check.union(val.split(','))
            elif key in ('-i', '--ignore'):
                USE_TMP_FILES = False

        args = " " + " ".join(args)
    except getopt.GetoptError:
        print_v(1, red('Unrecognized option\n'))
        print_usage()
        sys.exit(2)

    if not sys.stdout.isatty():
        nocolor()

    if os.getuid() != 0 and not PRETEND:
        print_v(1, blue(' * ') + yellow('You are not root, adding --pretend to portage options'))
        PRETEND = True
    elif not PRETEND and IS_DEV and not NO_PRETEND:
        print_v(1, blue(' * ') + yellow('This is a development version, so it may not work correctly'))
        print_v(1, blue(' * ') + yellow('Adding --pretend to portage options anyway'))
        print_v(1, blue(' * ') + 'If you\'re sure, you can add --no-pretend to revdep options')
        PRETEND = True


    signal.signal(signal.SIGINT, exithandler)
    signal.signal(signal.SIGTERM, exithandler)
    signal.signal(signal.SIGPIPE, signal.SIG_DFL)

    analyze_cache = {}
    if USE_TMP_FILES and check_temp_files():
        libraries, la_libraries, libraries_links, binaries = read_cache()
        assigned = analyse(libraries=libraries, la_libraries=la_libraries, \
                       libraries_links=libraries_links, binaries=binaries)
    else:
        assigned = analyse()

    if not assigned:
        print_v(1, '\n' + bold('Your system is consistent'))
        sys.exit(0)

    if EXACT:
        emerge_command = '=' + ' ='.join(assigned)
    else:
        emerge_command = ' '.join(get_slotted_cps(assigned))
    if PRETEND:
        args += ' --pretend'
    if VERBOSITY >= 2:
        args += ' --verbose'
    elif VERBOSITY < 1:
        args += ' --quiet'

    if len(emerge_command) == 0:
        print_v(1, bold('\nThere is nothing to emerge. Exiting.'))
        sys.exit(0)

    emerge_command = args + ' --oneshot ' + emerge_command


    #if PRETEND:
    print_v(1, yellow('\nemerge') + bold(emerge_command))
    #else:
        #call_program(emerge_command.split())
    os.system('emerge ' + emerge_command)

