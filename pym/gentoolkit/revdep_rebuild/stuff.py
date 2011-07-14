#!/usr/bin/python

"""Utilities submodule"""


from __future__ import print_function

import subprocess

import portage


# util. functions
def call_program(args):
	''' Calls program with specified parameters
	and returns the stdout as a str object.
	
	@param, args: arument list to pass to subprocess
	@return str
	'''
	subp = subprocess.Popen(args, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
	stdout, stderr = subp.communicate()
	stdout = stdout.decode('utf-8')
	return str(stdout)


def scan(params, files, max_args):
	''' Calls scanelf with given params and files to scan.
		@param params is list of parameters that should
			be passed into scanelf app.
		@param files list of files to scan.
		@param max_args number of files to process at once

		When files count is greater CMD_MAX_ARGS, it'll be divided
		into several parts

		@return scanelf output (joined if was called several times)
	'''
	out = []
	for i in range(0, len(files), max_args):
		out += call_program(
			['scanelf'] + params + files[i:i+max_args]).strip().split('\n')
	return out


def get_masking_status(ebuild):
	"""returns the masking status of an ebuild
	
	@param ebuild: str
	@return list
	"""
	try:
		status = portage.getmaskingstatus(ebuild)
	except KeyError:
		status = ['unavailable']
	return status


def _match_str_in_list(lst, stri):
	"""
	@param lst: list
	@param stri: string
	@return boolean or list menber that matches stri.endswith(member)
	"""
	for item in lst:
		if stri.endswith(item):
			return item
	return False



if __name__ == '__main__':
	print("There is nothing to run here.")
