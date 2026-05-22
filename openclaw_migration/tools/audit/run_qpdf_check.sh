#!/usr/bin/env bash
# run_qpdf_check.sh
# Runs qpdf --check on a PDF and writes a JSON summary.
# Also linearizes output if requested.
#
# Usage: run_qpdf_check.sh <pdf> <out-dir> [--linearize]
# Exit: 0 = pass, 1 = qpdf errors found, 2 = usage error

set -euo pipefail

if [ "$#" -lt 2 ]; then
    echo "usage: run_qpdf_check.sh <pdf> <out-dir> [--linearize]" >&2
    exit 2
fi

PDF="$1"
OUT="$2"
LINEARIZE="${3:-}"

mkdir -p "$OUT"
BASENAME=$(basename "$PDF" .pdf)
LOG="$OUT/qpdf_check_${BASENAME}.log"
RESULT_JSON="$OUT/qpdf_check_${BASENAME}.json"

echo "=== qpdf check: $PDF ==="

# Run check
set +e
qpdf --check "$PDF" > "$LOG" 2>&1
QPDF_EXIT=$?
set -e

# Parse result
if [ "$QPDF_EXIT" -eq 0 ]; then
    RESULT="PASS"
    ERRORS=0
elif [ "$QPDF_EXIT" -eq 3 ]; then
    RESULT="WARN"   # warnings only
    ERRORS=0
else
    RESULT="FAIL"
    ERRORS=1
fi

# Count warnings/errors in log
WARNINGS=$(grep -c "WARNING" "$LOG" 2>/dev/null || true)
ERROR_COUNT=$(grep -c "ERROR" "$LOG" 2>/dev/null || true)

# Linearize if requested
LINEARIZED_PATH=""
if [ "$LINEARIZE" = "--linearize" ] && [ "$RESULT" != "FAIL" ]; then
    LINEARIZED_PATH="$OUT/${BASENAME}_linearized.pdf"
    qpdf --linearize "$PDF" "$LINEARIZED_PATH"
    echo "  linearized -> $LINEARIZED_PATH"
fi

cat > "$RESULT_JSON" <<EOF
{
  "pdf": "$PDF",
  "result": "$RESULT",
  "qpdf_exit_code": $QPDF_EXIT,
  "warnings": $WARNINGS,
  "errors": $ERROR_COUNT,
  "log": "$LOG",
  "linearized": "$LINEARIZED_PATH"
}
EOF

echo "  result: $RESULT (warnings: $WARNINGS, errors: $ERROR_COUNT)"
cat "$LOG"

[ "$RESULT" != "FAIL" ]
