#!/usr/bin/env python

# python xls-app.py dch.xls output/

import os
import sys
import xlrd
import re
from translate.storage.aresource import AndroidResourceUnit
from xml.sax.saxutils import escape as xml_escape
import json

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
	s = AndroidResourceUnit.escape(s)
	return s

def iescape(s):
	return json.dumps(s, ensure_ascii=False)[1:-1]

def strip(s):
	return re.sub(r"\([^()]*\)", "", s).strip()

android_key = u"Android"
android_folder_key = u"Android folder"
android_file_key = u"Android file"
android_arg_key = u"Android arg"
android_default_name = u"strings"
ios_key = u"iOS"
ios_file_key = u"iOS file"
ios_arg_key = u"iOS arg"
ios_default_name = u"Localizable"

ios_locale_map = {"tw":"zh-Hant", "cn":"zh-Hans"}
android_locale_map = {"tw":"zh-rTW", "cn":"zh-rCN"}

main_lang_key = u"en"
lang_key = [u"tw", u"cn", u"jp", u"kr", u"ru", u"de", u"fr", u"it", u"es", u"pt", u"hu", u"cz", u"nl", u"pl", u"se", u"el"]
skip_sheet = [0,1,2]

aF={}
iF={}

xls = xlrd.open_workbook(sys.argv[1])

for sheet in xls.sheets():
	if sheet.number in skip_sheet:
		continue

	lang_key_col = {}
	main_lang_key_col = -1
	android_key_col = -1
	android_folder_key_col = -1
	android_file_key_col = -1
	android_arg_key_col = -1
	ios_key_col = -1
	ios_file_key_col = -1
	ios_arg_key_col = -1
	for c in range(0, sheet.ncols):
		value = strip(sheet.cell(0, c).value)
		if value == android_key:
			android_key_col = c
		if value == android_folder_key:
			android_folder_key_col = c
		if value == android_file_key:
			android_file_key_col = c
		if value == android_arg_key:
			android_arg_key_col = c
		if value == ios_key:
			ios_key_col = c
		if value == ios_file_key:
			ios_file_key_col = c
		if value == ios_arg_key:
			ios_arg_key_col = c
		if value == main_lang_key:
			main_lang_key_col = c
		lang_key_col[value] = c

	if main_lang_key_col < 0:
		print("Main language key column not found in sheet {0}".format(sheet.number))
		sys.exit(1)

	if android_key_col < 0:
		print("Android key column not found in sheet {0}".format(sheet.number))
		sys.exit(1)

	if ios_key_col < 0:
		print("iOS key column not found")
		sys.exit(1)

	for lang in lang_key:
		if lang not in lang_key_col:
			print("{0} key column not found".format(lang))
			sys.exit(1)


	for r in range(1, sheet.nrows):
		argMap = {}
		value = sheet.cell(r, main_lang_key_col).value.strip()
		keys = split("%[^%]+%", value)[1::2]
		pos = 0
		for k in keys:
			if k not in argMap:
				argMap[k] = pos
				pos += 1

		for lang in [main_lang_key] + lang_key:
			aKey = sheet.cell(r, android_key_col).value
			iKey = sheet.cell(r, ios_key_col).value

			if android_arg_key_col < 0:
				aArg = []
			else:
				aArg = sheet.cell(r, android_arg_key_col).value.split(u",")

			if ios_arg_key_col < 0:
				iArg = []
			else:
				iArg = sheet.cell(r, ios_arg_key_col).value.split(u",")

			value = sheet.cell(r, lang_key_col[lang]).value.strip()
			if value == u"":
				continue

			if aKey != "":
				va = split("%[^%]+%", value)
				for i in range(1, len(va), 2):
					ai = argMap[va[i]]
					if ai < len(aArg):
						arg = aArg[ai]
					else:
						print("Sheet \"{0}\": Undefined arg for Android key: {1}[{2}]".format(sheet.name, aKey, va[i]))
						sys.exit()
					va[i] = u"%{0}${1}".format(ai+1, arg)

				for i in range(0, len(va), 2):
					va[i] = va[i].replace(u"%", u"%%")

				if android_folder_key_col < 0:
					folder = u""
				else:
					folder = unicode(sheet.cell(r, android_folder_key_col).value).strip(u"/ ")

				if folder != u"":
					folder += u"/"

				if android_file_key_col < 0:
					file = android_default_name
				else:
					file = sheet.cell(r, android_file_key_col).value

				if file == u"":
					file = android_default_name

				if lang == main_lang_key:
					aLang = u""
				else:
					aLang = u"-" + android_locale_map.get(lang, lang)

				fk = (folder, aLang, file)
				if fk not in aF:
					aPath = os.path.join(sys.argv[2], u"android-strings/{0}values{1}/{2}.xml".format(folder, aLang, file).encode("utf-8"))
					d = os.path.dirname(aPath)
					if not os.path.exists(d):
						os.makedirs(d)
					aF[fk] = open(aPath, "w")
					aF[fk].write("<?xml version=\"1.0\" encoding=\"utf-8\"?>\n<resources>\n");

				aF[fk].write(u"\t<string name=\"{0}\">{1}</string>\n".format(aKey, aescape(u"".join(va))).encode("utf-8"))

			if iKey != "":
				va = split("%[^%]+%", value)
				for i in range(1, len(va), 2):
					ai = argMap[va[i]]
					if ai < len(iArg):
						arg = iArg[ai]
					else:
						print("Sheet \"{0}\": Undefined arg for iOS key: {1}[{2}]".format(sheet.name, iKey, va[i]))
						sys.exit()
					va[i] = u"%{0}${1}".format(ai+1, arg)

				for i in range(0, len(va), 2):
					va[i] = va[i].replace(u"%", u"%%")

				if ios_file_key_col < 0:
					file = ios_default_name
				else:
					file = sheet.cell(r, ios_file_key_col).value

				if file == u"":
					file = ios_default_name

				iLang = ios_locale_map.get(lang, lang)
				fk = (iLang, file)
				if fk not in iF:
					iPath = os.path.join(sys.argv[2], u"ios-strings/{0}.lproj/{1}.strings".format(iLang, file).encode("utf-8"))
					d = os.path.dirname(iPath)
					if not os.path.exists(d):
						os.makedirs(d)
					iF[fk] = open(iPath, "w")

				iF[fk].write(u"\"{0}\" = \"{1}\";\n".format(iKey, iescape(u"".join(va))).encode("utf-8"))

for fk in aF:
	aF[fk].write("</resources>\n");
	aF[fk].close()

for fk in iF:
	iF[fk].close()
