#!/usr/bin/env python

# aresource-xls.py strings.xml strings.xls

import sys
import xlwt
from translate.storage.aresource import AndroidResourceUnit
from aresource import Resource
import HTMLParser
import re

htmlParse = HTMLParser.HTMLParser()

def unescape(s):
	s = AndroidResourceUnit.unescape(s)
	s = htmlParse.unescape(s)
	return s

src = Resource(open(sys.argv[1]).read())
xls = xlwt.Workbook(encoding="utf-8")
sheet = xls.add_sheet("aresource")

row = 0
for type, name, attr, value, format_hint in src.tokens():
	if type=="string":
		sheet.write(row, 0, name)
		sheet.write(row, 1, unescape(value))
		row += 1
		continue
	if type=="string-array":
		for i in range(len(value)):
			sheet.write(row, 0, "{0}[{1}]".format(name, i))
			sheet.write(row, 1, unescape(value[i]))
			row += 1
		continue
	if type=="plurals":
		for k in value:
			sheet.write(row, 0, "{0}{{{1}}}".format(name, k))
			sheet.write(row, 1, unescape(value[k]))
			row += 1
		continue

xls.save(sys.argv[2])
