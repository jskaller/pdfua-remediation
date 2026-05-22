#!/usr/bin/env python3
"""
fix_pdfua_identifier.py
Ensures the PDF/UA-1 identifier is present in the XMP metadata.
Required: pdfuaid:part = 1 in the document XMP stream.
Rerun veraPDF PDF/UA after applying.
"""
import sys, json
from pathlib import Path

try:
    import fitz
except Exception as e:
    print(json.dumps({'result': 'ERROR', 'error': f'PyMuPDF unavailable: {e}'}))
    sys.exit(2)

if len(sys.argv) < 3:
    print('usage: fix_pdfua_identifier.py <input.pdf> <output.pdf>', file=sys.stderr)
    sys.exit(2)

src = sys.argv[1]
dst = sys.argv[2]

doc = fitz.open(src)
xmp = doc.get_xml_metadata() or ''

PDFUAID_NS   = 'xmlns:pdfuaid="http://www.aiim.org/pdfua/ns/id/"'
PDFUAID_PART = '<pdfuaid:part>1</pdfuaid:part>'
PDFUAID_AMDs = '<pdfuaid:amd>2005</pdfuaid:amd>'

changes = []

# Inject namespace declaration if missing
if 'pdfuaid' not in xmp:
    xmp = xmp.replace(
        '<rdf:Description',
        f'<rdf:Description {PDFUAID_NS}',
        1
    )
    changes.append('injected pdfuaid namespace')

# Inject pdfuaid:part if missing
if '<pdfuaid:part>' not in xmp:
    xmp = xmp.replace(
        '</rdf:Description>',
        f'  {PDFUAID_PART}\n  {PDFUAID_AMDs}\n</rdf:Description>',
        1
    )
    changes.append('injected pdfuaid:part=1 and pdfuaid:amd=2005')
else:
    # Correct value if wrong
    import re
    current = re.search(r'<pdfuaid:part>(\d+)</pdfuaid:part>', xmp)
    if current and current.group(1) != '1':
        xmp = re.sub(r'<pdfuaid:part>\d+</pdfuaid:part>', PDFUAID_PART, xmp)
        changes.append(f'corrected pdfuaid:part from {current.group(1)} to 1')

if changes:
    doc.set_xml_metadata(xmp)
    doc.save(dst, garbage=4, deflate=True)
    result = 'FIXED'
else:
    doc.save(dst, garbage=4, deflate=True)
    result = 'ALREADY_CORRECT'

print(json.dumps({
    'input': src,
    'output': dst,
    'result': result,
    'changes': changes
}, indent=2))
sys.exit(0)
