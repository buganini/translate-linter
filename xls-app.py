#!/usr/bin/env python3

# python3 xls-app.py dch.xls output/

import os
import sys
import xlrd
import re
from xml.sax.saxutils import escape as xml_escape
import json

# https://github.com/translate/translate/blob/master/translate/storage/aresource.py#L219
WHITESPACE = ' \n\t'  # Whitespace that we collapse.
MULTIWHITESPACE = re.compile('[ \n\t]{2}(?!\\\\n)')
def android_escape(text, quote_wrapping_whitespaces=True):
    """Escape all the characters which need to be escaped in an Android XML
    file.
    :param text: Text to escape
    :param quote_wrapping_whitespaces: If True, heading and trailing
           whitespaces will be quoted placing the entire resulting text in
           double quotes.
    """
    if text is None:
        return
    if len(text) == 0:
        return ''
    text = text.replace('\\', '\\\\')
    # This will add non intrusive real newlines to
    # ones in translation improving readability of result
    text = text.replace('\n', '\n\\n')
    text = text.replace('\t', '\\t')
    text = text.replace('\'', '\\\'')
    text = text.replace('"', '\\"')

    # @ needs to be escaped at start
    if text.startswith('@'):
        text = '\\@' + text[1:]
    # Quote strings with more whitespace
    if ((quote_wrapping_whitespaces and (text[0] in WHITESPACE or text[-1] in WHITESPACE))
            or len(MULTIWHITESPACE.findall(text))) > 0:
        return '"%s"' % text
    return text

def split(pat, s):
	ret = []
	lastPos = 0
	while True:
		match = re.search(pat, s)
		if match:
			span = match.span()
			ret.append(s[lastPos:span[0]])
			ret.append(s[span[0]:span[1]])
			s = s[span[1]:]
			lastPos = 0
		else:
			ret.append(s)
			return ret

def aescape(s):
	s = xml_escape(s)
	s = android_escape(s)
	if s in ("@", "?"):
		s = "\\" + s
	return s

def iescape(s):
	return json.dumps(s, ensure_ascii=False)[1:-1]

def strip_note(s):
	return re.sub(r"\([^()]*\)", "", s).strip()

global_key = "Global Key"
android_key = "Android"
android_folder_key = "Android folder"
android_file_key = "Android file"
android_arg_key = "Android arg"
android_default_name = "strings"
ios_key = "iOS"
ios_file_key = "iOS file"
ios_arg_key = "iOS arg"
ios_default_name = "Localizable"

ios_locale_map = {"tw":"zh-Hant", "cn":"zh-Hans", "jp":"ja", "kr":"ko", "cz":"cs", "se":"sv"}
android_locale_map = {"tw":"zh-rTW", "cn":"zh-rCN", "jp":"ja", "kr":"ko", "cz":"cs", "se":"sv", "pt-BR":"pt-rBR"}

ARGUMENT = r"\{\{.*?\}\}"

class Sheet():
	def __init__(self, i, name, sheet):
		self.number = i
		self.name = name
		self.sheet = sheet
		self.nrows = sheet.nrows - 1
		self.ncols = sheet.ncols
		self.cols = {}
		self.dat = {}
		for c in range(0, sheet.ncols):
			value = strip_note(sheet.cell(0, c).value)
			self.cols[value] = c

	def hasCol(self, c):
		return c in self.cols

	def get(self, r, c, default=""):
		try:
			return self.dat[r,c]
		except:
			if type(c) is str:
				if c in self.cols:
					v = self.sheet.cell(r+1, self.cols[c]).value.strip()
					if v == "":
						return default
					else:
						return v
				else:
					return default
			else:
				return self.sheet.cell(r+1, c).value.strip()

	def set(self, r, c, v):
		self.dat[r,c] = v

class Reader():
	def __init__(self, infile, skip_sheet):
		self.xls = xlrd.open_workbook(infile)
		self._sheets = []
		for i,sheet in enumerate(self.xls.sheets()):
			if i in skip_sheet:
				continue
			self._sheets.append(Sheet(i, sheet.name, sheet))

	def sheets(self):
		return self._sheets

def conv(input_path, output_dir, outlog, main_lang_key="en", lang_key = [], skip_sheet = []):
	aF={}
	iF={}
	aKeys = set()
	iKeys = set()

	reader = Reader(input_path, skip_sheet)

	for sheet in reader.sheets():
		if not sheet.hasCol(main_lang_key):
			outlog.write("[Error] Main language key column not found in sheet {0}\n".format(sheet.number))
			return

	for sheet in reader.sheets():
		for r in range(sheet.nrows):
			argIndex = {}
			value = sheet.get(r, main_lang_key)
			keys = split(ARGUMENT, value)[1::2]
			pos = 0
			for k in keys:
				if k not in argIndex:
					argIndex[k] = pos
					pos += 1

			folder = sheet.get(r, android_folder_key).strip("/")

			if folder != "":
				folder += "/"

			aKey = sheet.get(r, android_key)
			iKey = sheet.get(r, ios_key)

			aArg = sheet.get(r, android_arg_key).split(",")
			iArg = sheet.get(r, ios_arg_key).split(",")

			if aKey != "":
				kk = (folder, aKey)
				if kk in aKeys:
					outlog.write("[Warning] Duplicated Android key: {0}\n".format(kk))
				else:
					aKeys.add(kk)

			if iKey != "":
				kk = iKey
				if kk in iKeys:
					outlog.write("[Warning] Duplicated iOS key: {0}\n".format(kk))
				else:
					iKeys.add(kk)

			for lang in [main_lang_key] + lang_key:
				value = sheet.get(r, lang)
				if value == "":
					continue

				if aKey != "":
					va = split(ARGUMENT, value)
					for i in range(1, len(va), 2):
						if va[i] in argIndex:
							ai = argIndex[va[i]]
							if ai < len(aArg):
								arg = aArg[ai]
							else:
								outlog.write("[Error] Sheet \"{0}\": Undefined arg for Android key: {1}[{2}]\n".format(sheet.name, aKey, va[i]))
								return
							va[i] = "%{0}${1}".format(ai+1, arg)
						else:
							outlog.write("[Error] Unexpected variable {0} for Android key {1} in language {2} at sheet {3}\n".format(va[i], aKey, lang, sheet.name))
					for i in range(0, len(va), 2):
						va[i] = va[i].replace("%", "%%")

					file = sheet.get(r, android_file_key, android_default_name)

					if lang == main_lang_key:
						aLang = ""
					else:
						aLang = "-" + android_locale_map.get(lang, lang)

					fk = (folder, aLang, file)
					if fk not in aF:
						aPath = os.path.join(output_dir, "android-strings/{0}values{1}/{2}.xml".format(folder, aLang, file))
						d = os.path.dirname(aPath)
						if not os.path.exists(d):
							os.makedirs(d)
						aF[fk] = open(aPath, "w", encoding="utf-8")
						aF[fk].write("<?xml version=\"1.0\" encoding=\"utf-8\"?>\n<resources>\n");

					aF[fk].write("\t<string name=\"{0}\">{1}</string>\n".format(aKey, aescape("".join(va))))

				if iKey != "":
					va = split(ARGUMENT, value)
					for i in range(1, len(va), 2):
						if va[i] in argIndex:
							ai = argIndex[va[i]]
							if ai < len(iArg):
								arg = iArg[ai]
							else:
								outlog.write("[Error] Sheet \"{0}\": Undefined arg for iOS key: {1}[{2}]\n".format(sheet.name, iKey, va[i]))
								return
							va[i] = "%{0}${1}".format(ai+1, arg)
						else:
							outlog.write("[Error] Unexpected variable {0} for iOS key {1} in language {2} at sheet {3}\n".format(va[i], iKey, lang, sheet.name))
					for i in range(0, len(va), 2):
						va[i] = va[i].replace("%", "%%")

					file = sheet.get(r, ios_file_key, ios_default_name)

					iLang = ios_locale_map.get(lang, lang)
					fk = (iLang, file)
					if fk not in iF:
						iPath = os.path.join(output_dir, "ios-strings/{0}.lproj/{1}.strings".format(iLang, file))
						d = os.path.dirname(iPath)
						if not os.path.exists(d):
							os.makedirs(d)
						iF[fk] = open(iPath, "w", encoding="utf-8")

					iF[fk].write("\"{0}\" = \"{1}\";\n".format(iKey, iescape("".join(va))))

	for fk in aF:
		aF[fk].write("</resources>\n");
		aF[fk].close()

	for fk in iF:
		iF[fk].close()

if __name__ == "__main__":
	main_lang_key = "en"
	lang_key = ["tw"]
	skip_sheet = []

	conv(sys.argv[1], sys.argv[2], sys.stdout, main_lang_key, lang_key, skip_sheet)
