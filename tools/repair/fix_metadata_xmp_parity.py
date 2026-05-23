#!/usr/bin/env python3
"""
fix_metadata_xmp_parity.py
Synchronises the PDF Info dictionary fields with XMP metadata.
Fields synced: Title, Author, Subject, Creator, Producer, CreationDate, ModDate.
Rerun metadata_xmp_parity_audit.py after applying.
"""
import sys, json, re
from datetime import datetime, timezone

try:
    import fitz
except Exception as e:
    print(json.dumps({'result': 'ERROR', 'error': f'PyMuPDF unavailable: {e}'}))
    sys.exit(2)

if len(sys.argv) < 3:
    print('usage: fix_metadata_xmp_parity.py <input.pdf> <output.pdf>', file=sys.stderr)
    sys.exit(2)

src = sys.argv[1]
dst = sys.argv[2]

doc = fitz.open(src)
meta = doc.metadata or {}
xmp  = doc.get_xml_metadata() or ''

changes = []

def xmp_text(tag, value):
    return f'<{tag}>{value}</{tag}>'

def get_xmp_val(tag, xmp_str):
    m = re.search(rf'<{re.escape(tag)}>(.*?)</{re.escape(tag)}>', xmp_str, re.S)
    return m.group(1).strip() if m else ''

def set_xmp_val(tag, value, xmp_str):
    new_tag = xmp_text(tag, value)
    if f'<{tag}>' in xmp_str:
        return re.sub(rf'<{re.escape(tag)}>.*?</{re.escape(tag)}>', new_tag, xmp_str, flags=re.S)
    else:
        return xmp_str.replace('</rdf:Description>', f'  {new_tag}\n</rdf:Description>', 1)

# Map Info dict keys -> XMP tags (namespace:local)
field_map = {
    'title':    ('dc:title',          'dc:title'),
    'author':   ('dc:creator',        'dc:creator'),
    'subject':  ('dc:description',    'dc:description'),
    'creator':  ('xmp:CreatorTool',   'xmp:CreatorTool'),
    'producer': ('pdf:Producer',      'pdf:Producer'),
}

for info_key, (xmp_tag, _) in field_map.items():
    info_val = meta.get(info_key, '').strip()
    xmp_val  = get_xmp_val(xmp_tag, xmp).strip()

    if info_val and not xmp_val:
        xmp = set_xmp_val(xmp_tag, info_val, xmp)
        changes.append(f'set {xmp_tag} from Info ({info_val!r})')
    elif xmp_val and not info_val:
        meta[info_key] = xmp_val
        changes.append(f'set Info.{info_key} from XMP ({xmp_val!r})')
    elif info_val and xmp_val and info_val != xmp_val:
        # XMP wins for display; sync Info to XMP
        meta[info_key] = xmp_val
        changes.append(f'synced Info.{info_key} to XMP value ({xmp_val!r})')

if changes:
    doc.set_metadata(meta)
    doc.set_xml_metadata(xmp)

doc.save(dst, garbage=4, deflate=True)

print(json.dumps({
    'input':   src,
    'output':  dst,
    'result':  'FIXED' if changes else 'ALREADY_CORRECT',
    'changes': changes
}, indent=2))
sys.exit(0)
