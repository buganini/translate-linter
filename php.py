import re

"""
Currently only support these forms:
  $lang["key"] = "value";
"""

class Php(object):
	string_pattern = r'("(?:(?:\\.|[^\\"])*)"|\'(?:(?:\\.|[^\\\'])*)\')'
	equal_pattern = r'\s*=\s*'
	variable_pattern = r'\$([_A-Za-z][_A-Za-z0-9]*)';
	array_subscription_pattern = "".join([variable_pattern, r'\[', string_pattern, r'\]'])
	key_value_pattern = "".join([array_subscription_pattern, equal_pattern, string_pattern])
	key_value_re = re.compile(key_value_pattern, re.S)
	comment_pattern = r'/\\*.*?\\*/'
	tokenizer = re.compile("({0})".format("|".join([key_value_pattern, comment_pattern, ".+?"])), re.S)

	def __init__(self, xml):
		self.xml = xml

	def tokens(self):
		for tk in self.tokenizer.findall(self.xml):
			"""
			return key, value
			"""
			tk = "".join(tk)
			m = self.key_value_re.match(tk)
			if m:
				key = ("array[]=", m.group(1), self.unescape(m.group(2)))
				text = self.unescape(m.group(3))
				yield (key, text)
			else:
				yield ("", tk)


	@staticmethod
	def unescape(s):
		md = {"r":"\r", "n":"\n", "t":"\t", "f":"\f", "v":"\v", "\\":"\\", "\"":"\"", "'":"'", "$":"$"}
		ms = {"\\":"\\", "\"":"\"", "'":"'"}
		r = []
		escape = False
		if s[0]=="\"":
			for c in s[1:-1]:
				if escape:
					if c in md:
						r.append(md[c])
					else:
						r.append("\\")
						r.append(c)
					escape = False
				else:
					if c=="\\":
						escape = True
					else:
						r.append(c)
		else:
			for c in s[1:-1]:
				if escape:
					if c in ms:
						r.append(ms[c])
					else:
						r.append("\\")
						r.append(c)
					escape = False
				else:
					if c=="\\":
						escape = True
					else:
						r.append(c)
		return "".join(r)

	@staticmethod
	def escape(s):
		r = ["\""]
		m = {"\r":"\\r", "\n":"\\n", "\t":"\\t", "\f":"\\f", "\v":"\\v", "\\":"\\\\", "\"":"\\\"", "$":"\\$"}
		for c in s:
			if c in m:
				r.append(m[c])
			else:
				r.append(c)
		r.append("\"")
		return "".join(r)

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
	src = Php(src)

	for outf in sys.argv[i+1:]:
		try:
			dst = open(outf).read()
		except:
			dst = ""
		dpath = os.path.dirname(outf)
		if not os.path.exists(dpath):
			os.makedirs(dpath)
		out = open(outf, "w")
		dst = Php(dst)
		d = {}
		for key, value in dst.tokens():
			if not key:
				continue
			d[key] = value

		for key, value in src.tokens():
			if not key:
				out.write(value)
				continue
			if key not in d and skip_undefined:
				continue
			t = d.get(key, value)
			if t==value and skip_untranslated:
				continue
			out.write('${0}[{1}] = {2}'.format(key[1], Php.escape(key[2]), Php.escape(t)))
			continue
		out.close()
