#!/usr/bin/python

import subprocess


# util. functions
def call_program(args):
    ''' Calls program with specified parameters and returns stdout '''
    subp = subprocess.Popen(args, stdout=subprocess.PIPE, \
                                stderr=subprocess.PIPE)
    stdout, stderr = subp.communicate()
    return stdout


def scan(params, files, max_args):
    ''' Calls scanelf with given params and files to scan.
        @param params is list of parameters that should be passed into scanelf app.
        @param files list of files to scan.
        @param max_args number of files to process at once

        When files count is greater CMD_MAX_ARGS, it'll be divided
        into several parts

        @return scanelf output (joined if was called several times)
    '''
    out = []
    for i in range(0, len(files), max_args):
        out += call_program(['scanelf'] + params + files[i:i+max_args]).strip().split('\n')
    return out



def exithandler(signum, frame):
    sys.exit(1)



if __name__ == '__main__':
    print "There is nothing to run here."
