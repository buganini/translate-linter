#!/usr/bin/env python

import re

class Ini(object):
	key_pattern = '([^=\r\n]+?)'
	value_pattern = '([^\r\n;]*)'
	equal_pattern = r'([ \t\f\v]*=[ \t\f\v]*)'
	string_pair_pattern = "".join([key_pattern, equal_pattern, value_pattern])
	section_pattern = '\\[([^\\[\\]\r\n]+)\\]'
	comment_pattern = '(;[^\r\n]*)'
	tokenizer = re.compile("({0})".format("|".join([string_pair_pattern, section_pattern, comment_pattern, ".+?"])), re.S)
	string_pair_re = re.compile(string_pair_pattern)
	section_re = re.compile(section_pattern)
	comment_re = re.compile(comment_pattern)

	def __init__(self, xml):
		self.xml = xml

	def tokens(self):
		section = ""
		for tk in self.tokenizer.findall(self.xml):
			"""
			return type, name, value
			"""
			if self.string_pair_re.match(tk[0]):
				name = tk[1]
				eq = tk[2]
				text = tk[3]
				yield ("key-value", (section, name), eq, text)
			elif self.section_re.match(tk[0]):
				section = tk[4]
				yield ("section", "", "", section)
			else:
				yield ("", "", "", tk[0])


if __name__ == "__main__":
	import os
	import sys

	remove_trailing_spaces = False
	skip_undefined = False
	skip_untranslated = False

	for i in range(1, len(sys.argv)):
		if sys.argv[i]=="--skip-untranslated":
			skip_untranslated = True
		elif sys.argv[i]=="--skip-undefined":
			skip_undefined = True
		elif sys.argv[i]=="--remove-trailing-spaces":
			remove_trailing_spaces = True
		elif sys.argv[i] in ("-h", "--help"):
			print("Usage: {0} input output1 [output2...]\n"
			"\t--skip-untranslated\n"
			"\t--skip-undefined\n"
			"\t--remove-trailing-spaces\n"
				.format(sys.argv[0])
			)
			sys.exit()
		else:
			break

	src = open(sys.argv[i]).read()
	if remove_trailing_spaces:
		bak = src
		src = re.sub(r"\s*$", "", src, flags=re.M)
	src = Ini(src)

	for outf in sys.argv[i+1:]:
		try:
			dst = open(outf).read()
		except:
			dst = ""
		dpath = os.path.dirname(os.path.realpath(outf))
		if not os.path.exists(dpath):
			os.makedirs(dpath)
		out = open(outf, "w")
		dst = Ini(dst)
		d = {}
		for type, name, eq, value in dst.tokens():
			if type!="key-value":
				continue
			d[name] = value

		for type, name, eq, value in src.tokens():
			if type=="":
				out.write(value)
				continue
			if type=="section":
				out.write('[{0}]'.format(value))
				continue
			if type=="key-value":
				if name not in d and skip_undefined:
					continue
				t = d.get(name, value)
				if t==value and skip_untranslated:
					continue
				out.write('{0}{1}{2}'.format(name[1], eq, t))
				continue
		out.close()
