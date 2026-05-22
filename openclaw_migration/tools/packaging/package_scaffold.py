#!/usr/bin/env python3
"""
package_scaffold.py
Creates the standard output package directory structure for a remediation job.

Usage: package_scaffold.py <output-base-dir> <job-name>
Creates: <output-base-dir>/<job-name>/{pdf/, reports/, qa/, logs/}
"""
import sys, json
from pathlib import Path
from datetime import datetime, timezone

if len(sys.argv) < 3:
    print('usage: package_scaffold.py <output-base-dir> <job-name>', file=sys.stderr)
    sys.exit(2)

base    = Path(sys.argv[1])
name    = sys.argv[2]
job_dir = base / name

subdirs = ['pdf', 'reports', 'qa', 'logs']
created = []

for sub in subdirs:
    p = job_dir / sub
    p.mkdir(parents=True, exist_ok=True)
    created.append(str(p))

# Write a minimal package manifest
manifest = {
    'job_name':    name,
    'created_at':  datetime.now(timezone.utc).isoformat(),
    'structure':   subdirs,
    'status':      'IN_PROGRESS'
}
manifest_path = job_dir / 'PACKAGE_MANIFEST.json'
manifest_path.write_text(json.dumps(manifest, indent=2))

print(json.dumps({
    'result':    'OK',
    'job_dir':   str(job_dir),
    'created':   created,
    'manifest':  str(manifest_path)
}, indent=2))
sys.exit(0)
