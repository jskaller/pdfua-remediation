#!/usr/bin/env python3
"""
visual_qa.py
Generates a visual QA report: renders each page to PNG thumbnails,
extracts reading order summary, and flags pages with potential issues
(very sparse text, blank pages, extreme aspect ratios).

Usage: visual_qa.py <pdf> <out-dir> [--dpi 96]
Outputs: thumbnail PNGs + JSON report for human review.
"""
import sys, json, argparse
from pathlib import Path

try:
    import fitz
except Exception as e:
    print(json.dumps({'result': 'ERROR', 'error': f'PyMuPDF unavailable: {e}'})); sys.exit(2)

parser = argparse.ArgumentParser()
parser.add_argument('pdf')
parser.add_argument('out_dir')
parser.add_argument('--dpi', type=int, default=96)
args = parser.parse_args()

out_dir = Path(args.out_dir)
out_dir.mkdir(parents=True, exist_ok=True)

doc    = fitz.open(args.pdf)
matrix = fitz.Matrix(args.dpi / 72, args.dpi / 72)
pages  = []
flags  = []

for i, page in enumerate(doc):
    # Render thumbnail
    pix      = page.get_pixmap(matrix=matrix)
    thumb_path = out_dir / f'page_{i+1:03d}_thumb.png'
    pix.save(str(thumb_path))

    # Extract text summary
    text      = page.get_text('text').strip()
    word_count = len(text.split())
    rect      = page.rect

    # Flag conditions
    page_flags = []
    if word_count == 0:
        page_flags.append('BLANK_OR_IMAGE_ONLY')
    elif word_count < 5:
        page_flags.append('VERY_SPARSE_TEXT')
    if rect.width > 0 and (rect.height / rect.width > 4 or rect.width / rect.height > 4):
        page_flags.append('UNUSUAL_ASPECT_RATIO')

    # Check for images without alt text in struct tree
    imgs = page.get_images()
    if imgs and word_count == 0:
        page_flags.append('IMAGE_PAGE_NO_TEXT — verify alt text in structure')

    entry = {
        'page':       i + 1,
        'width_pt':   round(rect.width, 1),
        'height_pt':  round(rect.height, 1),
        'word_count': word_count,
        'image_count': len(imgs),
        'thumbnail':  str(thumb_path),
        'flags':      page_flags
    }
    pages.append(entry)
    if page_flags:
        flags.append({'page': i + 1, 'flags': page_flags})

result = 'REVIEW' if flags else 'PASS'
print(json.dumps({
    'pdf':          args.pdf,
    'result':       result,
    'total_pages':  len(doc),
    'pages_flagged': len(flags),
    'flagged':      flags,
    'pages':        pages,
    'thumbnails_dir': str(out_dir)
}, indent=2))
sys.exit(0 if result == 'PASS' else 1)
