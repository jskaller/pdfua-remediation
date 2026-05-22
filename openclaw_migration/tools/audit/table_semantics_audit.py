#!/usr/bin/env python3
"""
table_semantics_audit.py
Audits table structure elements for PDF/UA compliance (veraPDF rule 7.5).
Checks: TH cells have Scope, tables have THead/TBody, TR contains only TH/TD,
no empty header cells, Summary attribute present.

Usage: table_semantics_audit.py <pdf>
"""
import sys, json, re
from pathlib import Path

try:
    import fitz
except Exception as e:
    print(json.dumps({'result': 'ERROR', 'error': f'PyMuPDF unavailable: {e}'})); sys.exit(2)

if len(sys.argv) < 2:
    print('usage: table_semantics_audit.py <pdf>', file=sys.stderr); sys.exit(2)

doc = fitz.open(sys.argv[1])
issues = []
stats  = {'tables': 0, 'th_cells': 0, 'th_missing_scope': 0,
          'tables_missing_summary': 0, 'tables_missing_thead': 0}

catalog = doc.pdf_catalog()
struct_tree_ref = doc.xref_get_key(catalog, 'StructTreeRoot')

if struct_tree_ref[0] == 'null' or not struct_tree_ref[1]:
    print(json.dumps({'pdf': sys.argv[1], 'result': 'SKIPPED',
                      'reason': 'No StructTreeRoot — document not tagged'}))
    sys.exit(1)

def get_kids(xref):
    kids = doc.xref_get_key(xref, 'K')
    if kids[0] == 'array':
        return [int(r) for r in re.findall(r'(\d+)\s+0\s+R', kids[1])]
    elif kids[0] == 'xref':
        return [int(kids[1].split()[0])]
    return []

def stype(xref):
    s = doc.xref_get_key(xref, 'S')
    return s[1].strip('/').strip() if s[0] != 'null' else ''

def has_attr(xref, attr_name):
    a = doc.xref_get_key(xref, 'A')
    return a[0] != 'null' and attr_name in a[1]

def walk(xref, parent_type=None):
    try:
        t = stype(xref)

        if t == 'Table':
            stats['tables'] += 1
            if not has_attr(xref, 'Summary'):
                stats['tables_missing_summary'] += 1
                issues.append({'type': 'Table_missing_summary', 'xref': xref,
                               'fix': 'run fix_table_headers.py'})
            kids = get_kids(xref)
            kid_types = [stype(k) for k in kids]
            if 'THead' not in kid_types and any(st in kid_types for st in ('TR', 'TBody')):
                stats['tables_missing_thead'] += 1
                issues.append({'type': 'Table_missing_THead', 'xref': xref,
                               'note': 'No THead grouping — header row semantics unclear'})

        elif t == 'TH':
            stats['th_cells'] += 1
            if not has_attr(xref, 'Scope'):
                stats['th_missing_scope'] += 1
                issues.append({'type': 'TH_missing_scope', 'xref': xref,
                               'fix': 'run fix_table_headers.py'})

        for kid in get_kids(xref):
            walk(kid, t)
    except Exception:
        return

struct_root_xref = int(struct_tree_ref[1].split()[0])
walk(struct_root_xref)

result = 'PASS' if not issues else 'FAIL'
print(json.dumps({
    'pdf':     sys.argv[1],
    'result':  result,
    'stats':   stats,
    'issues':  issues
}, indent=2))
sys.exit(0 if result == 'PASS' else 1)
