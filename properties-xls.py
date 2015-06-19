#!/usr/bin/env python

# properties-xls.py Localizable.strings Localizable.xls

import sys
import xlwt
from properties import Properties
from xml.sax.saxutils import escape, unescape

src = Properties(open(sys.argv[1]).read())
xls = xlwt.Workbook(encoding="utf-8")
sheet = xls.add_sheet("properties")

row = 0
for type, name, value in src.tokens():
	if type=="string":
		sheet.write(row, 0, name)
		sheet.write(row, 1, value.decode("string-escape"))
		row += 1

xls.save(sys.argv[2])
