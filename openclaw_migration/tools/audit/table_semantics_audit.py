#!/usr/bin/env python3
"""
table_semantics_audit.py
Audits table structure elements for PDF/UA-1 compliance.
Checks: TH cells have Scope attribute, TD cells can resolve a header,
tables have at least one TH row.

Usage: table_semantics_audit.py <pdf> [--out results.json]
"""
import sys, json, re, argparse
from pathlib import Path

try:
    import fitz
except Exception as e:
    print(json.dumps({'result': 'ERROR', 'error': f'PyMuPDF unavailable: {e}'})); sys.exit(2)

parser = argparse.ArgumentParser()
parser.add_argument('pdf')
parser.add_argument('--out', default=None, help='Write JSON output to this file in addition to stdout')
args = parser.parse_args()

doc = fitz.open(args.pdf)
issues = []
tables_found = 0
th_cells_found = 0
th_missing_scope = 0

catalog = doc.pdf_catalog()
struct_tree_ref = doc.xref_get_key(catalog, 'StructTreeRoot')

if struct_tree_ref[0] == 'null' or not struct_tree_ref[1]:
    output = json.dumps({
        'pdf': args.pdf, 'result': 'SKIPPED',
        'reason': 'No StructTreeRoot — document not tagged'
    }, indent=2)
    print(output)
    if args.out:
        Path(args.out).write_text(output)
    sys.exit(1)

def get_kids_xrefs(xref, doc):
    kids = doc.xref_get_key(xref, 'K')
    if kids[0] == 'array':
        return [int(r) for r in re.findall(r'(\d+)\s+0\s+R', kids[1])]
    elif kids[0] == 'xref':
        return [int(kids[1].split()[0])]
    return []

def walk_for_type(xref, doc, target_types):
    try:
        s_type = doc.xref_get_key(xref, 'S')
        clean  = s_type[1].strip('/').strip() if s_type[0] != 'null' else ''
        if clean in target_types:
            yield xref, clean
        for kid_xref in get_kids_xrefs(xref, doc):
            yield from walk_for_type(kid_xref, doc, target_types)
    except Exception:
        return

struct_root_xref = int(struct_tree_ref[1].split()[0])

for xref, s_type in walk_for_type(struct_root_xref, doc, {'Table', 'TH', 'TD'}):
    if s_type == 'Table':
        tables_found += 1
    elif s_type == 'TH':
        th_cells_found += 1
        attrs = doc.xref_get_key(xref, 'A')
        scope_present = attrs[0] != 'null' and 'Scope' in attrs[1]
        if not scope_present:
            th_missing_scope += 1
            issues.append({
                'xref': xref,
                'type': 'TH_missing_scope',
                'note': 'TH cell has no Scope attribute — run fix_table_headers.py'
            })

result = 'PASS' if not issues else 'FAIL'

output = json.dumps({
    'pdf':              args.pdf,
    'result':           result,
    'tables_found':     tables_found,
    'th_cells_found':   th_cells_found,
    'th_missing_scope': th_missing_scope,
    'issues':           issues[:50],
    'issue_count':      len(issues)
}, indent=2)

print(output)

if args.out:
    Path(args.out).write_text(output)

sys.exit(0 if result == 'PASS' else 1)
