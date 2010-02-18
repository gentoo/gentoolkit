"""This modification of textwrap allows it to wrap ANSI colorized text as if
it weren't colorized. It also uses a much simpler word splitting regex to
prevent the splitting of ANSI colors as well as package names and versions."""

import re
import textwrap

class TextWrapper(textwrap.TextWrapper):
	"""Ignore ANSI escape codes while wrapping text"""

	def _split(self, text):
		"""_split(text : string) -> [string]

		Split the text to wrap into indivisible chunks.
		"""
		# Only split on whitespace to avoid mangling ANSI escape codes or
		# package names.
		wordsep_re = re.compile(r'(\s+)')
		chunks = wordsep_re.split(text)
		chunks = [x for x in chunks if x is not None]
		return chunks

	def _wrap_chunks(self, chunks):
		"""_wrap_chunks(chunks : [string]) -> [string]

		Wrap a sequence of text chunks and return a list of lines of
		length 'self.width' or less.  (If 'break_long_words' is false,
		some lines may be longer than this.)  Chunks correspond roughly
		to words and the whitespace between them: each chunk is
		indivisible (modulo 'break_long_words'), but a line break can
		come between any two chunks.  Chunks should not have internal
		whitespace; ie. a chunk is either all whitespace or a "word".
		Whitespace chunks will be removed from the beginning and end of
		lines, but apart from that whitespace is preserved.
		"""
		lines = []
		if self.width <= 0:
			raise ValueError("invalid width %r (must be > 0)" % self.width)

		# Arrange in reverse order so items can be efficiently popped
		# from a stack of chunks.
		chunks.reverse()

		# Regex to strip ANSI escape codes. It's only used for the
		# length calculations of indent and each chuck.
		ansi_re = re.compile('\x1b\[[0-9;]*m')

		while chunks:

			# Start the list of chunks that will make up the current line.
			# cur_len is just the length of all the chunks in cur_line.
			cur_line = []
			cur_len = 0

			# Figure out which static string will prefix this line.
			if lines:
				indent = self.subsequent_indent
			else:
				indent = self.initial_indent

			# Maximum width for this line. Ingore ANSI escape codes.
			width = self.width - len(re.sub(ansi_re, '', indent))

			# First chunk on line is whitespace -- drop it, unless this
			# is the very beginning of the text (ie. no lines started yet).
			if chunks[-1].strip() == '' and lines:
				del chunks[-1]

			while chunks:
				# Ignore ANSI escape codes.
				chunk_len = len(re.sub(ansi_re, '', chunks[-1]))

				# Can at least squeeze this chunk onto the current line.
				if cur_len + chunk_len <= width:
					cur_line.append(chunks.pop())
					cur_len += chunk_len

				# Nope, this line is full.
				else:
					break

			# The current line is full, and the next chunk is too big to
			# fit on *any* line (not just this one).
			# Ignore ANSI escape codes.
			if chunks and len(re.sub(ansi_re, '', chunks[-1])) > width:
				self._handle_long_word(chunks, cur_line, cur_len, width)

			# If the last chunk on this line is all whitespace, drop it.
			if cur_line and cur_line[-1].strip() == '':
				del cur_line[-1]

			# Convert current line back to a string and store it in list
			# of all lines (return value).
			if cur_line:
				lines.append(indent + ''.join(cur_line))

		return lines

# vim: set ts=4 sw=4 tw=79:
