#!/usr/bin/python

"""Utilities submodule"""


from __future__ import print_function

import subprocess

import portage
from portage.output import green, red


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
	return stdout


def scan(params, files, max_args, logger):
	''' Calls scanelf with given params and files to scan.
		@param params is list of parameters that should
			be passed into scanelf app.
		@param files list of files to scan.
		@param max_args number of files to process at once

		When files count is greater CMD_MAX_ARGS, it'll be divided
		into several parts

		@return scanelf output (joined if was called several times)
	'''
	logger.debug("\tscan(), scanelf params = %s, # files: %d" % (params, len(files)))
	# change it to a sorted list for group processing
	_files = sorted(files)
	out = []
	for i in range(0, len(_files), max_args):
		output = call_program(
			['scanelf'] + params + _files[i:i+max_args]).strip().split('\n')
		output = [x for x in output if x != '']
		if output:
			out.extend(output)
	logger.debug("\tscan(), final output length: %d" % len(out))
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


def filter_masked(assigned, logger):
	'''Filter out masked pkgs/ebuilds'''

	def is_masked(ebuild):
		if get_masking_status(ebuild):
			logger.warn(' !!! ' + red('All ebuilds that could satisfy: ') +
				green(ebuild) + red(' have been masked'))
			return True
		return False

	has_masked = False
	tmp = []
	for ebuild in assigned:
		if not is_masked(ebuild):
			tmp.append(ebuild)
		else:
			has_masked = True
	if has_masked:
		logger.info('\t' + red('* ') +
			'Unmask all ebuild(s) listed above and call revdep-rebuild '
			'again or manually emerge given packages.')
	return tmp




if __name__ == '__main__':
	print("There is nothing to run here.")
