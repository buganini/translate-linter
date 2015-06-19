#!/usr/bin/env python

import re

class Resource(object):
	string_pattern = r'<string[^>/-]*>.*?</string>'
	string_array_pattern = r'<string-array[^>/-]*>.*?</string-array>'
	plurals_pattern = r'<plurals[^>/-]*>.*?</plurals>'
	closed_string_pattern = r'<string[^>/-]*/>'
	closed_string_array_pattern = r'<string-array[^>/-]*/>'
	closed_plurals_pattern = r'<plurals[^>/-]*/>'
	tokenizer = re.compile("({0})".format("|".join([string_pattern, closed_string_pattern, string_array_pattern, closed_string_array_pattern, plurals_pattern, closed_plurals_pattern, ".+?"])), re.S)
	attributes_re = re.compile(r'<\S+(.*?)>', re.S)
	text_re = re.compile(r'<string[^>-]*>(.*?)</string>', re.S)
	item_re = re.compile(r'(\s*)<item([^>]*)>(.*?)</item>', re.S)
	name_re = re.compile(r'\s*name="(.*?)"', re.S)
	translatable_re = re.compile(r'\s*translatable="(.*?)"', re.S)
	qty_re = re.compile(r'\s*quantity="(.*?)"', re.S)
	trail_re = re.compile(r'.*?</item>(\s*)</\S+?>', re.S)

	def __init__(self, xml):
		self.xml = xml
		self.string_re = re.compile(self.string_pattern, re.S)
		self.string_array_re = re.compile(self.string_array_pattern, re.S)
		self.plurals_re = re.compile(self.plurals_pattern, re.S)
		self.closed_string_re = re.compile(self.closed_string_pattern, re.S)
		self.closed_string_array_re = re.compile(self.closed_string_array_pattern, re.S)
		self.closed_plurals_re = re.compile(self.closed_plurals_pattern, re.S)

	def tokens(self):
		for tk in self.tokenizer.findall(self.xml):
			"""
			return type, name, attr, value, format_hint
			"""
			if self.string_re.match(tk):
				attr = self.get_attributes(tk)
				name = self.get_name(attr)
				if self.get_translatable(attr)=="false":
					yield ("", "", "", tk, "")
				else:
					yield ("string", name, attr, self.get_text(tk), "")
			elif self.string_array_re.match(tk):
				attr = self.get_attributes(tk)
				name = self.get_name(attr)
				items = self.item_re.findall(tk)
				value = []
				for ws, iattr, text in items:
					value.append(text)
				if items:
					sep = items[0][0]
				else:
					sep = ""
				trail = self.get_trail(tk)
				if self.get_translatable(attr)=="false":
					yield ("", "", "", tk, "")
				else:
					yield ("string-array", name, attr, value, (sep, trail))
			elif self.plurals_re.match(tk):
				attr = self.get_attributes(tk)
				name = self.get_name(attr)
				items = self.item_re.findall(tk)
				value = {}
				for ws, iattr, text in items:
					value[self.get_qty(iattr)] = text
				if items:
					sep = items[0][0]
				else:
					sep = ""
				trail = self.get_trail(tk)
				yield ("plurals", name, attr, value, (sep, trail))
			elif self.closed_string_re.match(tk):
				attr = self.get_attributes(tk)
				name = self.get_name(attr)
				if self.get_translatable(attr)=="false":
					yield ("", "", "", tk, "")
				else:
					yield ("string", name, attr, "", "")
			elif self.closed_string_array_re.match(tk):
				pass
			elif self.closed_plurals_re.match(tk):
				pass
			else:
				yield ("", "", "", tk, "")

	@classmethod
	def get_attributes(cls, tag):
		m = cls.attributes_re.match(tag)
		if m:
			return m.group(1)
		return ""

	@classmethod
	def get_name(cls, attr):
		m = cls.name_re.match(attr)
		if m:
			return m.group(1)
		return ""

	@classmethod
	def get_translatable(cls, attr):
		m = cls.name_re.match(attr)
		if m:
			return m.group(1)
		return ""

	@classmethod
	def get_qty(cls, attr):
		m = cls.qty_re.match(attr)
		if m:
			return m.group(1)
		return ""

	@classmethod
	def get_trail(cls, tag):
		m = cls.trail_re.match(tag)
		if m:
			return m.group(1)
		return ""

	@classmethod
	def get_text(cls, tag):
		m = cls.text_re.match(tag)
		if m:
			return m.group(1)
		return ""


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
	src = Resource(src)

	for outf in sys.argv[i+1:]:
		try:
			dst = open(outf).read()
		except:
			dst = ""
		dpath = os.path.dirname(outf)
		if not os.path.exists(dpath):
			os.makedirs(dpath)
		out = open(outf, "w")
		dst = Resource(dst)
		d = {}
		for type, name, attr, value, format_hint in dst.tokens():
			if not type:
				continue
			d[(type, name)] = value

		for type, name, attr, value, format_hint in src.tokens():
			if type=="":
				out.write(value)
				continue
			if type=="string":
				if (type, name) not in d and skip_undefined:
					continue
				t = d.get((type, name), value)
				if t==value and skip_untranslated:
					continue
				out.write('<string{0}>{1}</string>'.format(attr, t))
				continue
			if type=="string-array":
				if (type, name) not in d and skip_undefined:
					continue
				t = d.get((type, name), value)
				untranslated = True
				if len(t) != len(value):
					untranslated = False
				else:
					for i in range(len(t)):
						if t[i] != value[i]:
							untranslated = False
							break
				if untranslated and skip_untranslated:
					continue
				out.write('<string-array{0}>'.format(attr))
				for i in range(len(value)):
					out.write('{0}<item>{1}</item>'.format(format_hint[0], t[i]))
				out.write("{0}</string-array>".format(format_hint[1]))
				continue
			if type=="plurals":
				if (type, name) not in d and skip_undefined:
					continue
				t = d.get((type, name), value)
				untranslated = True
				if len(t) != len(value):
					untranslated = False
				else:
					for k in t:
						if k not in value:
							untranslated = False
							break
						if t[k] != value[k]:
							untranslated = False
							break
				if untranslated and skip_untranslated:
					continue
				out.write("<plurals{0}>".format(attr))
				for k in t:
					out.write('{0}<item quantity="{1}">{2}</item>'.format(format_hint[0], k, t[k]))
				out.write("{0}</plurals>".format(format_hint[1]))
		out.close()
