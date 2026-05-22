#!/usr/bin/env python3
"""
metadata_xmp_parity_audit.py
Audits PDF Info dictionary vs XMP metadata for parity.
Checks: author, creator, producer fields match between Info and XMP,
pdfuaid:part=1 present, and document language set.

Org-specific metadata values are configurable via --org env var or
ORG_NAME environment variable. Defaults to generic checks if not set.

Usage: metadata_xmp_parity_audit.py <pdf> [--org "Org Name"]
"""
import sys, json, re, os, argparse
from pathlib import Path

try:
    import fitz
except Exception as e:
    print(json.dumps({'result': 'ERROR', 'error': f'PyMuPDF unavailable: {e}'})); sys.exit(2)

parser = argparse.ArgumentParser()
parser.add_argument('pdf')
parser.add_argument('--org', default=os.environ.get('ORG_NAME', ''),
                    help='Expected org name in metadata fields (optional)')
args = parser.parse_args()

doc  = fitz.open(args.pdf)
meta = doc.metadata or {}
xmp  = doc.get_xml_metadata() or ''

checks = []

def xmp_val(tag):
    m = re.search(rf'<{re.escape(tag)}>(.*?)</{re.escape(tag)}>', xmp, re.S)
    return m.group(1).strip() if m else ''

# Check Info/XMP parity for key fields
field_map = {
    'title':    'dc:title',
    'author':   'dc:creator',
    'subject':  'dc:description',
    'creator':  'xmp:CreatorTool',
    'producer': 'pdf:Producer',
}

for info_key, xmp_tag in field_map.items():
    info_val = meta.get(info_key, '').strip()
    xmp_v    = xmp_val(xmp_tag).strip()
    match    = info_val == xmp_v
    checks.append({
        'field':       info_key,
        'info_value':  info_val,
        'xmp_value':   xmp_v,
        'pass':        match,
        'note':        '' if match else 'Info/XMP mismatch — run fix_metadata_xmp_parity.py'
    })

# If org name provided, validate it appears in key fields
if args.org:
    for field in ['author', 'creator', 'producer']:
        val = meta.get(field, '')
        checks.append({
            'field': f'{field}_org_check',
            'value': val,
            'pass':  args.org in val,
            'note':  f'Expected org "{args.org}" not found in {field}' if args.org not in val else ''
        })

# PDF/UA identifier
checks.append({
    'field': 'pdfuaid_part',
    'pass':  'pdfuaid:part' in xmp and '>1<' in xmp,
    'note':  'pdfuaid:part=1 missing — run fix_pdfua_identifier.py'
             if not ('pdfuaid:part' in xmp and '>1<' in xmp) else ''
})

# Document language
catalog     = doc.pdf_catalog()
lang_ref    = doc.xref_get_key(catalog, 'Lang')
has_lang    = lang_ref[0] != 'null' and bool(lang_ref[1].strip().strip('()'))
checks.append({
    'field': 'catalog_lang',
    'value': lang_ref[1].strip('()') if has_lang else '',
    'pass':  has_lang,
    'note':  'No /Lang in catalog — set document language' if not has_lang else ''
})

# Title present
has_title = bool(meta.get('title', '').strip())
checks.append({
    'field': 'title_present',
    'value': meta.get('title', ''),
    'pass':  has_title,
    'note':  'No document title set' if not has_title else ''
})

result = 'PASS' if all(c['pass'] for c in checks) else 'FAIL'
failures = [c for c in checks if not c['pass']]

print(json.dumps({
    'pdf':      args.pdf,
    'result':   result,
    'checks':   checks,
    'failures': failures,
    'info':     meta
}, indent=2))
sys.exit(0 if result == 'PASS' else 1)
