#!/usr/bin/env python3
"""
smoke_test.py
Verifies the openclaw_migration workspace is correctly assembled and all
required tools and assets are in place before or after Docker launch.

Inside Docker: run as  python3 /app/smoke_test.py /app
Outside Docker: run as python3 smoke_test.py  (from inside openclaw_migration/)

Usage: smoke_test.py [<workspace-root>]
Default: current directory
"""
import sys, json, shutil
from pathlib import Path

# Accept explicit root, otherwise use cwd.
# Inside Docker the Dockerfile sets WORKDIR /app/openclaw_migration so
# Path.cwd() resolves correctly without needing an explicit argument.
root = Path(sys.argv[1]) if len(sys.argv) > 1 else Path.cwd()
checks = []

def chk(name, cond, fix=''):
    checks.append({'check': name, 'pass': bool(cond), 'fix': fix})

# --- Directory structure ---
chk('tools/audit exists',
    (root / 'tools/audit').exists(),
    'Missing tools/audit/ — check openclaw_migration structure')
chk('tools/repair exists',
    (root / 'tools/repair').exists(),
    'Missing tools/repair/')
chk('tools/packaging exists',
    (root / 'tools/packaging').exists(),
    'Missing tools/packaging/')
chk('tools/qa exists',
    (root / 'tools/qa').exists(),
    'Missing tools/qa/')
chk('workspace/skills exists',
    (root / 'workspace/skills').exists(),
    'Missing workspace/skills/')
chk('workspace/assets/validation_profiles exists',
    (root / 'workspace/assets/validation_profiles').exists(),
    'Create workspace/assets/validation_profiles/ and copy veraPDF profiles into it')

# --- Critical workspace files ---
chk('AGENTS.md present',
    (root / 'workspace/AGENTS.md').exists(),
    'Missing workspace/AGENTS.md')
chk('TOOLS.md present',
    (root / 'workspace/TOOLS.md').exists(),
    'Missing workspace/TOOLS.md')
chk('SOUL.md present',
    (root / 'workspace/SOUL.md').exists(),
    'Missing workspace/SOUL.md')

# --- Skill ---
skill_mds = list((root / 'workspace/skills').rglob('SKILL.md'))
chk('SKILL.md present',
    len(skill_mds) > 0,
    'Missing workspace/skills/montefiore-pdfua-unified-v6/SKILL.md')

# --- Docker files (expected after docker config step) ---
chk('Dockerfile present',
    (root / 'Dockerfile').exists(),
    'Dockerfile not yet created — run docker config step')
chk('docker-compose.yml present',
    (root / 'docker-compose.yml').exists(),
    'docker-compose.yml not yet created — run docker config step')
chk('.env.example present',
    (root / '.env.example').exists(),
    '.env.example not yet created — run docker config step')

# --- Python requirements ---
chk('requirements.txt present',
    (root / 'requirements.txt').exists(),
    'Missing requirements.txt')

# --- Pinned WCAG profile ---
wcag_profiles = list(root.rglob('WCAG-2-2-Machine.xml'))
chk('pinned WCAG-2-2-Machine.xml present',
    len(wcag_profiles) > 0,
    'Copy veraPDF profile repo into workspace/assets/validation_profiles/')

# --- System tools ---
chk('qpdf available',
    shutil.which('qpdf') is not None,
    'Install via apt: apt-get install qpdf  (present inside Docker)')
chk('java available',
    shutil.which('java') is not None,
    'Install JRE: apt-get install openjdk-17-jre-headless  (present inside Docker)')
chk('python3 available',
    shutil.which('python3') is not None,
    'Python 3.9+ required')

# --- Python dependencies ---
try:
    import fitz
    chk('pymupdf importable', True)
except ImportError:
    chk('pymupdf importable', False, 'pip install pymupdf>=1.23.0')

try:
    from fontTools.ttLib import TTFont
    chk('fonttools importable', True)
except ImportError:
    chk('fonttools importable', False, 'pip install fonttools>=4.47.0')

try:
    from PIL import Image
    chk('pillow importable', True)
except ImportError:
    chk('pillow importable', False, 'pip install Pillow>=10.0.0')

# --- No stale ChatGPT/OpenAI artifacts ---
openai_yamls = list(root.rglob('openai.yaml'))
chk('no stale openai.yaml artifacts',
    len(openai_yamls) == 0,
    f'Remove: {[str(p) for p in openai_yamls]}')

skill_zips = list(root.rglob('skill.zip'))
chk('no stale skill.zip artifacts',
    len(skill_zips) == 0,
    f'Remove: {[str(p) for p in skill_zips]}')

# --- Summary ---
passed = sum(1 for c in checks if c['pass'])
failed = sum(1 for c in checks if not c['pass'])
result = 'PASS' if failed == 0 else 'FAIL'

print(json.dumps({
    'result':   result,
    'root':     str(root),
    'passed':   passed,
    'failed':   failed,
    'checks':   checks,
    'failures': [c for c in checks if not c['pass']]
}, indent=2))
sys.exit(0 if result == 'PASS' else 1)
