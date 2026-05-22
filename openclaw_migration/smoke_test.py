#!/usr/bin/env python3
"""
smoke_test.py
Verifies the openclaw_migration workspace is correctly assembled and all
required tools and assets are in place before launching Docker.

Usage: smoke_test.py [<workspace-root>]
Default workspace root: current directory (expects openclaw_migration/ structure)
"""
import sys, json, shutil
from pathlib import Path

root = Path(sys.argv[1]) if len(sys.argv) > 1 else Path.cwd()
checks = []

def chk(name, cond, fix=''):
    checks.append({'check': name, 'pass': bool(cond), 'fix': fix})

# --- Directory structure ---
chk('tools/audit exists',     (root / 'tools/audit').exists(),
    'Run assemble_pipeline.py or create manually')
chk('tools/repair exists',    (root / 'tools/repair').exists(),
    'Copy repair helpers from openclaw_migration/tools/repair/')
chk('tools/packaging exists', (root / 'tools/packaging').exists(),
    'Copy packaging tools from openclaw_migration/tools/packaging/')
chk('tools/qa exists',        (root / 'tools/qa').exists(),
    'Copy QA tools from openclaw_migration/tools/qa/')
chk('workspace/skills exists', (root / 'workspace/skills').exists(),
    'Run assemble_pipeline.py')
chk('workspace/assets/validation_profiles exists',
    (root / 'workspace/assets/validation_profiles').exists(),
    'Copy veraPDF profiles from _05_assets/validation_profiles/')

# --- Critical files ---
chk('SKILL.md present',
    any((root / 'workspace/skills').rglob('SKILL.md')),
    'Copy SKILL.md from _03_skills/skills/montefiore-pdfua-unified-v6/')
chk('Dockerfile present',     (root / 'Dockerfile').exists(),
    'Run docker config step or copy from openclaw_migration/')
chk('docker-compose.yml present', (root / 'docker-compose.yml').exists(),
    'Run docker config step or copy from openclaw_migration/')
chk('.env.example present',   (root / '.env.example').exists(),
    'Copy .env.example from openclaw_migration/')
chk('requirements.txt present', (root / 'requirements.txt').exists(),
    'Copy from _02_scripts/requirements.txt')

# --- Pinned WCAG profile ---
wcag_profiles = list(root.rglob('WCAG-2-2-Machine.xml'))
chk('pinned WCAG-2-2-Machine.xml present', len(wcag_profiles) > 0,
    'Copy veraPDF profile repo into workspace/assets/validation_profiles/')

# --- System tools (inside Docker these will be present; outside they may not be) ---
chk('qpdf available',    shutil.which('qpdf') is not None,
    'Install via apt: apt-get install qpdf (or will be in Docker)')
chk('java available',    shutil.which('java') is not None,
    'Install JRE 17: apt-get install openjdk-17-jre-headless (or will be in Docker)')
chk('python3 available', shutil.which('python3') is not None,
    'Python 3 required')

# --- Python dependencies ---
try:
    import fitz
    chk('pymupdf importable', True)
except ImportError:
    chk('pymupdf importable', False, 'pip install pymupdf')

try:
    from fontTools.ttLib import TTFont
    chk('fonttools importable', True)
except ImportError:
    chk('fonttools importable', False, 'pip install fonttools')

# --- No stale OpenAI skill artifacts ---
openai_yamls = list(root.rglob('openai.yaml'))
chk('no stale openai.yaml artifacts', len(openai_yamls) == 0,
    f'Remove: {[str(p) for p in openai_yamls]}')

skill_zips = list(root.rglob('skill.zip'))
chk('no stale skill.zip artifacts', len(skill_zips) == 0,
    f'Remove: {[str(p) for p in skill_zips]}')

# --- Summary ---
passed  = sum(1 for c in checks if c['pass'])
failed  = sum(1 for c in checks if not c['pass'])
result  = 'PASS' if failed == 0 else 'FAIL'

print(json.dumps({
    'result':   result,
    'passed':   passed,
    'failed':   failed,
    'checks':   checks,
    'failures': [c for c in checks if not c['pass']]
}, indent=2))
sys.exit(0 if result == 'PASS' else 1)
