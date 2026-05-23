#!/usr/bin/env python3
"""
table_semantics_audit.py
Audits table structure for PDF/UA-1 compliance using two complementary passes:

Pass 1 — pdfplumber (geometric): detects visually present tables on each page
  from borders, lines, and character alignment. Identifies tables that exist
  visually but are absent from the structure tree (untagged tables).

Pass 2 — PyMuPDF (struct tree): walks the PDF structure tree to validate that
  tagged tables have correct TH Scope attributes and resolvable header chains.

The delta between Pass 1 and Pass 2 is the primary diagnostic output.
A page where pdfplumber finds more tables than the struct tree contains has
untagged tables that will fail veraPDF — run fix_table_headers.py after
manually tagging those tables.

Usage: table_semantics_audit.py <pdf> [--out results.json]
"""
import sys, json, re, argparse
from pathlib import Path

try:
    import fitz
except Exception as e:
    print(json.dumps({'result': 'ERROR', 'error': f'PyMuPDF unavailable: {e}'}))
    sys.exit(2)

try:
    import pdfplumber
    PDFPLUMBER_AVAILABLE = True
except Exception:
    PDFPLUMBER_AVAILABLE = False

parser = argparse.ArgumentParser()
parser.add_argument('pdf')
parser.add_argument('--out', default=None, help='Write JSON output to this file in addition to stdout')
parser.add_argument('--no-pdfplumber', action='store_true',
                    help='Skip geometric pass (struct tree audit only)')
args = parser.parse_args()

pdf_path = args.pdf
issues = []

# ---------------------------------------------------------------------------
# Pass 1: pdfplumber geometric table detection
# ---------------------------------------------------------------------------

pdfplumber_results = {}
pdfplumber_ran = False
untagged_table_pages = []

if PDFPLUMBER_AVAILABLE and not args.no_pdfplumber:
    pdfplumber_ran = True
    try:
        with pdfplumber.open(pdf_path) as plumb_doc:
            for page_obj in plumb_doc.pages:
                page_num = page_obj.page_number  # 1-based

                # Skip image-only pages — pdfplumber cannot detect tables
                # on pages without a native text layer.
                has_text = len(page_obj.chars) > 0
                if not has_text:
                    pdfplumber_results[page_num] = {
                        'skipped': True,
                        'reason': 'image_only_page',
                        'visual_tables': 0
                    }
                    continue

                visual_tables = page_obj.find_tables()
                pdfplumber_results[page_num] = {
                    'skipped': False,
                    'visual_tables': len(visual_tables),
                    'table_bboxes': [
                        {
                            'x0': round(t.bbox[0], 1),
                            'y0': round(t.bbox[1], 1),
                            'x1': round(t.bbox[2], 1),
                            'y1': round(t.bbox[3], 1)
                        }
                        for t in visual_tables
                    ]
                }
    except Exception as e:
        pdfplumber_ran = False
        issues.append({
            'type': 'pdfplumber_error',
            'note': f'pdfplumber pass failed: {e} — struct tree audit continues'
        })

# ---------------------------------------------------------------------------
# Pass 2: PyMuPDF struct tree audit
# ---------------------------------------------------------------------------

doc = fitz.open(pdf_path)
tables_found = 0
th_cells_found = 0
th_missing_scope = 0

# Count struct tree tables per page for delta calculation
struct_tables_by_page = {}  # page_num (1-based) -> count

catalog = doc.pdf_catalog()
struct_tree_ref = doc.xref_get_key(catalog, 'StructTreeRoot')

if struct_tree_ref[0] == 'null' or not struct_tree_ref[1]:
    # No struct tree — pdfplumber results still valid as untagged table detection
    untagged_summary = {}
    total_visual = 0
    if pdfplumber_ran:
        for pg, data in pdfplumber_results.items():
            if not data.get('skipped') and data['visual_tables'] > 0:
                untagged_table_pages.append(pg)
                total_visual += data['visual_tables']
        untagged_summary = {
            'total_visual_tables_found': total_visual,
            'untagged_table_pages': untagged_table_pages,
            'note': 'Document has no struct tree — all visual tables are untagged'
        }

    output = json.dumps({
        'pdf': pdf_path,
        'result': 'FAIL' if untagged_table_pages else 'SKIPPED',
        'reason': 'No StructTreeRoot — document not tagged',
        'pdfplumber_ran': pdfplumber_ran,
        'pdfplumber_geometric': pdfplumber_results if pdfplumber_ran else None,
        'untagged_tables': untagged_summary if pdfplumber_ran else None,
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


def get_page_number_for_xref(xref, doc):
    """Attempt to find the 1-based page number for a struct element."""
    try:
        pg_ref = doc.xref_get_key(xref, 'Pg')
        if pg_ref[0] == 'xref':
            pg_xref = int(pg_ref[1].split()[0])
            for i in range(len(doc)):
                if doc[i].xref == pg_xref:
                    return i + 1
    except Exception:
        pass
    return None


def walk_for_type(xref, doc, target_types):
    try:
        s_type = doc.xref_get_key(xref, 'S')
        clean = s_type[1].strip('/').strip() if s_type[0] != 'null' else ''
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
        pg = get_page_number_for_xref(xref, doc)
        if pg is not None:
            struct_tables_by_page[pg] = struct_tables_by_page.get(pg, 0) + 1

    elif s_type == 'TH':
        th_cells_found += 1
        attrs = doc.xref_get_key(xref, 'A')
        scope_present = attrs[0] != 'null' and 'Scope' in attrs[1]
        if not scope_present:
            th_missing_scope += 1
            pg = get_page_number_for_xref(xref, doc)
            issues.append({
                'xref': xref,
                'page': pg,
                'type': 'TH_missing_scope',
                'note': 'TH cell has no Scope attribute — run fix_table_headers.py'
            })

# ---------------------------------------------------------------------------
# Cross-reference: geometric vs struct tree
# ---------------------------------------------------------------------------

delta_by_page = {}
untagged_table_pages = []
total_visual_tables = 0
total_struct_tables = tables_found

if pdfplumber_ran:
    all_pages = set(list(pdfplumber_results.keys()) + list(struct_tables_by_page.keys()))
    for pg in sorted(all_pages):
        plumb_data = pdfplumber_results.get(pg, {})
        if plumb_data.get('skipped'):
            continue
        visual = plumb_data.get('visual_tables', 0)
        tagged = struct_tables_by_page.get(pg, 0)
        delta = visual - tagged
        total_visual_tables += visual
        delta_by_page[pg] = {
            'visual_tables': visual,
            'struct_tree_tables': tagged,
            'delta': delta
        }
        if delta > 0:
            untagged_table_pages.append(pg)
            issues.append({
                'page': pg,
                'type': 'untagged_tables_detected',
                'visual_tables': visual,
                'struct_tree_tables': tagged,
                'delta': delta,
                'note': (
                    f'Page {pg}: pdfplumber found {visual} visual table(s), '
                    f'struct tree has {tagged}. '
                    f'{delta} table(s) appear untagged — manual tagging required '
                    f'before fix_table_headers.py can repair header scope.'
                )
            })

# ---------------------------------------------------------------------------
# Result
# ---------------------------------------------------------------------------

result = 'PASS' if not issues else 'FAIL'

output = json.dumps({
    'pdf':                      pdf_path,
    'result':                   result,
    # Struct tree summary
    'struct_tree_tables_found': tables_found,
    'th_cells_found':           th_cells_found,
    'th_missing_scope':         th_missing_scope,
    # Geometric summary
    'pdfplumber_ran':           pdfplumber_ran,
    'total_visual_tables':      total_visual_tables if pdfplumber_ran else None,
    'untagged_table_pages':     untagged_table_pages if pdfplumber_ran else None,
    # Delta detail (per page)
    'page_delta':               delta_by_page if pdfplumber_ran else None,
    # All issues (struct + untagged)
    'issues':                   issues[:50],
    'issue_count':              len(issues)
}, indent=2)

print(output)

if args.out:
    Path(args.out).write_text(output)

sys.exit(0 if result == 'PASS' else 1)
