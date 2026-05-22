#!/usr/bin/env python3
"""
font_inventory.py
Lists all fonts used in a PDF with embedding status, type, and page coverage.
Quick triage before running font_geometry_matcher.py or font_replacement_report.py.

Usage: font_inventory.py <pdf>
"""
import sys, json
from pathlib import Path

try:
    import fitz
except Exception as e:
    print(json.dumps({'result': 'ERROR', 'error': f'PyMuPDF unavailable: {e}'})); sys.exit(2)

if len(sys.argv) < 2:
    print('usage: font_inventory.py <pdf>', file=sys.stderr); sys.exit(2)

doc = fitz.open(sys.argv[1])
fonts = {}

for page_num, page in enumerate(doc):
    for font in page.get_fonts(full=True):
        xref, ext, font_type, basename, name, enc = font[:6]
        key = name or basename or f'unnamed_{xref}'
        if key not in fonts:
            fonts[key] = {
                'name':      name,
                'basename':  basename,
                'type':      font_type,
                'ext':       ext,
                'encoding':  enc,
                'embedded':  xref > 0,
                'xref':      xref,
                'pages':     []
            }
        if page_num + 1 not in fonts[key]['pages']:
            fonts[key]['pages'].append(page_num + 1)

font_list = sorted(fonts.values(), key=lambda f: f['name'] or '')
not_embedded = [f for f in font_list if not f['embedded']]

print(json.dumps({
    'pdf':           sys.argv[1],
    'result':        'FAIL' if not_embedded else 'PASS',
    'total_fonts':   len(font_list),
    'not_embedded':  len(not_embedded),
    'fonts':         font_list
}, indent=2))
sys.exit(0 if not not_embedded else 1)
