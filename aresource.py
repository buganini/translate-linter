import os
import sys
import re
import itertools

class Resource(object):
	string_pattern = r'<string[^>-]*>.*?</string>'
	string_array_pattern = r'<string-array[^>-]*>.*?</string-array>'
	plurals_pattern = r'<plurals[^>-]*>.*?</plurals>'
	tokenizer = re.compile("({0})".format("|".join([string_pattern, string_array_pattern, plurals_pattern, ".+?"])), re.S)
	attributes_re = re.compile(r'<\S+(.*?)>', re.S)
	text_re = re.compile(r'<string[^>-]*>(.*?)</string>', re.S)
	item_re = re.compile(r'(\s*)<item([^>]*)>(.*?)</item>', re.S)
	name_re = re.compile(r'\s*name="(.*?)"', re.S)
	qty_re = re.compile(r'\s*quantity="(.*?)"', re.S)
	trail_re = re.compile(r'.*?</item>(\s*)</\S+?>', re.S)

	def __init__(self, xml):
		self.xml = xml
		self.string_re = re.compile(self.string_pattern, re.S)
		self.string_array_re = re.compile(self.string_array_pattern, re.S)
		self.plurals_re = re.compile(self.plurals_pattern, re.S)

	def tokens(self):
		for tk in self.tokenizer.findall(self.xml):
			"""
			return type, name, attr, value, format_hint
			"""
			if self.string_re.match(tk):
				attr = self.get_attributes(tk)
				name = self.get_name(attr)
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

src = Resource(open(sys.argv[1]).read())

for f in sys.argv[2:]:
	try:
		dst = open(f).read()
	except:
		dst = ""
	dpath = os.path.dirname(f)
	if not os.path.exists(dpath):
		os.makedirs(dpath)
	out = open(f, "w")
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
			out.write('<string{0}>{1}</string>'.format(attr, d.get((type, name), value)))
			continue
		if type=="string-array":
			out.write('<string-array{0}>'.format(attr))
			t = d.get((type, name), value)
			for i in range(len(value)):
				out.write('{0}<item>{1}</item>'.format(format_hint[0], t[i]))
			out.write("{0}</string-array>".format(format_hint[1]))
			continue
		if type=="plurals":
			out.write("<plurals{0}>".format(attr))
			t = d.get((type, name), value)
			for k in t:
				out.write('{0}<item quantity="{1}">{2}</item>'.format(format_hint[0], k, t[k]))
			out.write("{0}</plurals>".format(format_hint[1]))
	out.close()
