#!/usr/bin/env python3
"""
render_compare.py
Renders source and output PDFs to PNG at a given DPI and computes
a per-page pixel diff score. Flags pages with significant visual changes.

Usage: render_compare.py <source.pdf> <output.pdf> <out-dir> [--dpi 150] [--threshold 0.01]

threshold: fraction of pixels that may differ before flagging (default 1%)
Outputs: PNG crops of differing pages + JSON summary.
"""
import sys, json, argparse
from pathlib import Path

try:
    import fitz
except Exception as e:
    print(json.dumps({'result': 'ERROR', 'error': f'PyMuPDF unavailable: {e}'})); sys.exit(2)

parser = argparse.ArgumentParser()
parser.add_argument('source')
parser.add_argument('output')
parser.add_argument('out_dir')
parser.add_argument('--dpi',       type=int,   default=150)
parser.add_argument('--threshold', type=float, default=0.01)
args = parser.parse_args()

out_dir = Path(args.out_dir)
out_dir.mkdir(parents=True, exist_ok=True)

src_doc = fitz.open(args.source)
out_doc = fitz.open(args.output)

if len(src_doc) != len(out_doc):
    print(json.dumps({
        'result': 'FAIL',
        'reason': f'Page count mismatch: source={len(src_doc)}, output={len(out_doc)}'
    }))
    sys.exit(1)

matrix = fitz.Matrix(args.dpi / 72, args.dpi / 72)
page_results = []
flagged = []

for i, (src_page, out_page) in enumerate(zip(src_doc, out_doc)):
    src_pix = src_page.get_pixmap(matrix=matrix, colorspace=fitz.csGRAY)
    out_pix = out_page.get_pixmap(matrix=matrix, colorspace=fitz.csGRAY)

    if src_pix.width != out_pix.width or src_pix.height != out_pix.height:
        # Size mismatch — save both for review
        src_pix.save(str(out_dir / f'page_{i+1:03d}_source.png'))
        out_pix.save(str(out_dir / f'page_{i+1:03d}_output.png'))
        page_results.append({'page': i+1, 'diff_pct': 100.0, 'size_mismatch': True})
        flagged.append(i + 1)
        continue

    # Pixel-level diff
    total_pixels = src_pix.width * src_pix.height
    diff_count = 0
    src_samples = src_pix.samples
    out_samples = out_pix.samples

    for j in range(len(src_samples)):
        if abs(src_samples[j] - out_samples[j]) > 10:  # tolerance for compression artifacts
            diff_count += 1

    diff_pct = diff_count / total_pixels
    flagged_page = diff_pct > args.threshold

    if flagged_page:
        src_pix.save(str(out_dir / f'page_{i+1:03d}_source.png'))
        out_pix.save(str(out_dir / f'page_{i+1:03d}_output.png'))
        flagged.append(i + 1)

    page_results.append({
        'page':        i + 1,
        'diff_pct':    round(diff_pct * 100, 3),
        'flagged':     flagged_page
    })

result = 'PASS' if not flagged else 'REVIEW'
print(json.dumps({
    'source':         args.source,
    'output':         args.output,
    'result':         result,
    'dpi':            args.dpi,
    'threshold_pct':  args.threshold * 100,
    'pages_total':    len(src_doc),
    'pages_flagged':  len(flagged),
    'flagged_pages':  flagged,
    'page_results':   page_results,
    'crops_saved_to': str(out_dir) if flagged else ''
}, indent=2))
sys.exit(0 if result == 'PASS' else 1)
