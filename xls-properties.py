#!/usr/bin/env python

# properties-xls.py Localizable.xls

import sys
import xlrd
from xml.sax.saxutils import escape, unescape

for path in sys.argv[1:]:
	print(u"Processing {0}".format(path))
	xls = xlrd.open_workbook(path)
	sheet = xls.sheet_by_index(0)

	for c in range(1, sheet.ncols):
		code = sheet.cell(0, c).value
		print(u"Translating {0}".format(code))
		f = open(u"Localizable-{0}.strings".format(code).encode("utf-8"), "w")
		for r in range(1, sheet.nrows):
			key = sheet.cell(r, 0).value
			value = sheet.cell(r, c).value
			if key.strip()=="":
				continue
			f.write(u"\"{0}\" = \"{1}\";\n".format(key, value).encode("utf-8"))

		f.close()
