import re

class Properties(object):
	string_pattern = r'"((?:\\.|[^\\"])*)"'
	equal_pattern = r'\s*=\s*'
	string_pair_pattern = "".join([string_pattern, equal_pattern, string_pattern, "\s*;"])
	comment_pattern = r'/\\*.*?\\*/'
	tokenizer = re.compile("({0})".format("|".join([string_pair_pattern, comment_pattern, ".+?"])), re.S)
	string_pair_re = re.compile(string_pair_pattern)

	def __init__(self, xml):
		self.xml = xml

	def tokens(self):
		for tk in self.tokenizer.findall(self.xml):
			"""
			return type, name, value
			"""
			tk = "".join(tk)
			m = self.string_pair_re.match(tk)
			if m:
				name = m.group(1)
				text = m.group(2)
				yield ("string", name, text)
			else:
				yield ("", "", tk)


if __name__ == "__main__":
	import os
	import sys

	skip_undefined = False
	skip_untranslated = False

	for i in range(1, len(sys.argv)):
		if sys.argv[i]=="--skip-untranslated":
			skip_untranslated = True
		elif sys.argv[i]=="--skip-undefined":
			skip_undefined = True
		elif sys.argv[i] in ("-h", "--help"):
			print("Usage: {0} input output1 [output2...]\n"
			"\t--skip-untranslated\n"
			"\t--skip-undefined\n"
				.format(sys.argv[0])
			)
			sys.exit()
		else:
			break

	src = Properties(open(sys.argv[i]).read())

	for outf in sys.argv[i+1:]:
		try:
			dst = open(outf).read()
		except:
			dst = ""
		dpath = os.path.dirname(outf)
		if not os.path.exists(dpath):
			os.makedirs(dpath)
		out = open(outf, "w")
		dst = Properties(dst)
		d = {}
		for type, name, value in dst.tokens():
			if not type:
				continue
			d[(type, name)] = value

		for type, name, value in src.tokens():
			if type=="":
				out.write(value)
				continue
			if type=="string":
				if (type, name) not in d and skip_undefined:
					continue
				t = d.get((type, name), value)
				if t==value and skip_untranslated:
					continue
				out.write('"{0}" = "{1}";'.format(name, t))
				continue
		out.close()
