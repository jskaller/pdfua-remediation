#!/usr/bin/env python3
"""
fix_figure_alt_text.py
Adds or repairs Alt text on Figure structure elements that are missing it.
Two modes:
  - auto: sets a placeholder alt text so veraPDF passes; flag for human review
  - manual: reads a JSON map of {figure_index: alt_text} and applies exactly those

Usage:
  fix_figure_alt_text.py <input.pdf> <output.pdf> [--alt-map alt_map.json]

Without --alt-map, runs in auto mode (placeholder text).
fig_index keys in the alt-map are zero-based and count ALL Figure elements
encountered in struct tree order, including those that already have alt text.
Rerun veraPDF PDF/UA and visual QA after applying.
"""
import sys, json, argparse
from pathlib import Path

try:
    import fitz
except Exception as e:
    print(json.dumps({'result': 'ERROR', 'error': f'PyMuPDF unavailable: {e}'}))
    sys.exit(2)

parser = argparse.ArgumentParser()
parser.add_argument('input')
parser.add_argument('output')
parser.add_argument('--alt-map', help='JSON file mapping figure index to alt text')
args = parser.parse_args()

alt_map = {}
if args.alt_map:
    try:
        alt_map = json.loads(Path(args.alt_map).read_text())
    except Exception as e:
        print(json.dumps({'result': 'ERROR', 'error': f'Could not read alt-map: {e}'}))
        sys.exit(2)

doc = fitz.open(args.input)
changes = []
needs_review = []

catalog = doc.pdf_catalog()
struct_tree_ref = doc.xref_get_key(catalog, 'StructTreeRoot')

if struct_tree_ref[0] == 'null' or not struct_tree_ref[1]:
    print(json.dumps({
        'input': args.input,
        'result': 'SKIPPED',
        'reason': 'No StructTreeRoot found — document is not tagged'
    }, indent=2))
    sys.exit(1)

def walk_struct(xref, doc, depth=0):
    """Recursively walk structure tree, yield (xref, type, alt) for all nodes."""
    try:
        import re
        s_type = doc.xref_get_key(xref, 'S')
        alt    = doc.xref_get_key(xref, 'Alt')
        kids   = doc.xref_get_key(xref, 'K')
        yield (xref,
               s_type[1] if s_type[0] != 'null' else '',
               alt[1] if alt[0] != 'null' else None)
        if kids[0] == 'array':
            refs = re.findall(r'(\d+)\s+0\s+R', kids[1])
            for ref in refs:
                yield from walk_struct(int(ref), doc, depth + 1)
        elif kids[0] == 'xref':
            yield from walk_struct(int(kids[1].split()[0]), doc, depth + 1)
    except Exception:
        return

struct_root_xref = int(struct_tree_ref[1].split()[0])

# fig_index counts ALL Figure elements encountered, whether or not they
# need fixing — so alt-map keys reliably address the correct element.
fig_index = 0

for xref, s_type, alt in walk_struct(struct_root_xref, doc):
    clean_type = s_type.strip('/').strip()
    if clean_type == 'Figure':
        if alt is None or alt.strip('()').strip() == '':
            # Missing or empty alt text — apply fix
            if str(fig_index) in alt_map:
                new_alt = alt_map[str(fig_index)]
                mode = 'manual'
            else:
                new_alt = f'[Figure {fig_index + 1} — alt text required]'
                mode = 'auto-placeholder'
                needs_review.append({'xref': xref, 'figure_index': fig_index})

            doc.xref_set_key(xref, 'Alt', fitz.get_pdf_str(new_alt))
            changes.append({
                'xref': xref,
                'figure_index': fig_index,
                'mode': mode,
                'alt_set': new_alt
            })
        # Always increment — counts all Figures, not just missing ones
        fig_index += 1

doc.save(args.output, garbage=4, deflate=True)
result = 'FIXED' if changes else 'ALREADY_CORRECT'

print(json.dumps({
    'input':          args.input,
    'output':         args.output,
    'result':         result,
    'figures_total':  fig_index,
    'changes':        changes,
    'needs_review':   needs_review,
    'note': 'Auto-placeholder alt texts must be replaced with meaningful descriptions before final handoff.'
            if needs_review else ''
}, indent=2))
sys.exit(0 if result in ('FIXED', 'ALREADY_CORRECT') else 1)
