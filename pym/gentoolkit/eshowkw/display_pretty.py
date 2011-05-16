#	vim:fileencoding=utf-8
# Copyright 2010 Gentoo Foundation
# Distributed under the terms of the GNU General Public License v2

from portage.output import colorize
try: # newer python versions
	from itertools import zip_longest
except ImportError: # older python naming
	from itertools import izip_longest as zip_longest

__all__ = ['string_rotator', 'colorize_string', 'align_string', 'rotate_dash', 'print_content', 'display']

def display(plain_list, rotated_list, plain_width, rotated_height, cp, toplist = 'archlist'):
	"""Render defauld display to show the keywords listing"""
	# header
	output = []
	output.append('Keywords for %s:' % colorize('blue', cp))
	# data
	corner_image = [''.ljust(plain_width) for x in range(rotated_height)]
	if toplist != 'archlist':
		corner_image.extend(plain_list)
	data_printout = ['%s%s' % (x, y)
		for x, y in zip_longest(corner_image, rotated_list, fillvalue=corner_image[0])]
	if toplist == 'archlist':
		data_printout.extend(plain_list)
	output.extend(data_printout)
	print(print_content(output))

def align_string(string, align, length):
	"""Align string to the specified alignment (left or right, and after rotation it becomes top and bottom)"""
	if align == 'top' or align == 'left':
		string = string.ljust(length)
	else:
		string = string.rjust(length)
	return string

def colorize_string(color, string):
	"""Add coloring for specified string. Due to rotation we need to do that per character rather than per-line"""
	tmp = []
	for char in list(string):
		# % is whitespace separator so we wont color that :)
		if char != '%':
			tmp.append(colorize(color, char))
		else:
			tmp.append(char)
	return ''.join(tmp)

def rotate_dash(string):
	"""Rotate special strings over 90 degrees for better readability."""
	chars = ['-', '|']
	subs = ['|', '-']
	out = string
	for x,y  in zip(chars, subs):
		if string.find(x) != -1:
			out = out.replace(x, y)
	return out

def print_content(content):
	"""Print out content (strip it out of the temporary %)"""
	return '\n'.join(content).replace('%','')

class string_rotator:
	__DASH_COUNT = 0
	def __getChar(self, string, position, line, bold_separator = False):
		"""Return specified character from the string position"""

		# first figure out what character we want to work with
		# based on order and position in the string
		isdash = False
		if string.startswith('|') or string.startswith('-') or string.startswith('+'):
			split = list(string)
			isdash = True
			self.__DASH_COUNT += 1
		else:
			split = string.split('%')
		char = split[position]
		# bolding
		if not isdash and bold_separator \
				and (line-self.__DASH_COUNT)%2 == 0 \
				and char != ' ':
			char = colorize('bold', char)
		return char

	def rotateContent(self, elements, length, bold_separator = False, strip = True):
		"""
			Rotate string over 90 degrees:
			string -> s
						t
						r
						i
						n
						g
		"""
		# join used to have list of lines rather than list of chars
		tmp = []
		for position in range(length):
			x = ''
			for i, string in enumerate(elements):
				x += ' ' + self.__getChar(rotate_dash(string), position, i, bold_separator)
			# spaces on dashed line should be dashed too
			if x.find('+ -') != -1:
				x = x.replace(' ', '-')
			# strip all chars and remove empty lines
			if not strip or len(x.strip(' |-')) > 0:
				tmp.append(x)
		return tmp
