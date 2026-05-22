#!/usr/bin/env bash
# run_verapdf_profiles.sh
# Runs all required veraPDF profiles against a PDF and writes XML reports.
# Profiles run: PDF/UA-1 (flavour), WCAG-2-2-Machine (pinned), ISO-32000-1-Tagged (if present)
#
# Usage: run_verapdf_profiles.sh <verapdf-bin> <profiles-root> <pdf> <out-dir>
# Exit: 0 = all profiles passed, 1 = one or more failures, 2 = usage error, 3 = missing profile

set -euo pipefail

if [ "$#" -lt 4 ]; then
    echo "usage: run_verapdf_profiles.sh <verapdf-bin> <profiles-root> <pdf> <out-dir>" >&2
    exit 2
fi

VERAPDF="${VERAPDF_BIN:-$1}"
PROFILES="$2"
PDF="$3"
OUT="$4"

mkdir -p "$OUT"

WCAG="$PROFILES/PDF_UA/WCAG-2-2-Machine.xml"
ISO="$PROFILES/PDF_UA/ISO-32000-1-Tagged.xml"
PDFUA2="$PROFILES/PDF_UA/PDFUA-2.xml"

if [ ! -f "$WCAG" ]; then
    echo "ERROR: missing pinned WCAG profile: $WCAG" >&2
    exit 3
fi

PASS=0
FAIL=0

run_profile() {
    local label="$1"
    local outfile="$2"
    shift 2
    echo "  running: $label"
    if "$VERAPDF" --format xml --verbose --maxfailuresdisplayed -1 "$@" "$PDF" > "$outfile" 2>&1; then
        echo "  result:  PASS -> $outfile"
        PASS=$((PASS + 1))
    else
        echo "  result:  FAIL -> $outfile"
        FAIL=$((FAIL + 1))
    fi
}

echo "=== veraPDF validation: $(basename "$PDF") ==="

run_profile "PDF/UA-1 (flavour)" \
    "$OUT/verapdf_pdfua_ua1.xml" \
    --flavour ua1

run_profile "WCAG-2-2-Machine (pinned)" \
    "$OUT/verapdf_wcag_2_2_machine.xml" \
    --profile "$WCAG"

if [ -f "$ISO" ]; then
    run_profile "ISO-32000-1-Tagged" \
        "$OUT/verapdf_iso_32000_1_tagged.xml" \
        --profile "$ISO"
fi

if [ -f "$PDFUA2" ]; then
    run_profile "PDF/UA-2" \
        "$OUT/verapdf_pdfua2.xml" \
        --profile "$PDFUA2"
fi

# Write summary JSON
RESULT="PASS"
[ "$FAIL" -gt 0 ] && RESULT="FAIL"

cat > "$OUT/verapdf_summary.json" <<EOF
{
  "pdf": "$PDF",
  "result": "$RESULT",
  "profiles_run": $((PASS + FAIL)),
  "profiles_passed": $PASS,
  "profiles_failed": $FAIL,
  "report_dir": "$OUT"
}
EOF

echo "=== Summary: $RESULT (passed: $PASS, failed: $FAIL) ==="
[ "$FAIL" -eq 0 ]
