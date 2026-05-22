---
name: montefiore-pdfua-unified-v6
description: PDF/UA remediation workflow. Use when asked to remediate, validate, preflight, fix, or package a PDF for accessibility. Runs veraPDF PDF/UA-1 and WCAG-2-2-Machine validation, metadata/XMP parity, contrast audit, table semantics, native text preservation, visual QA, and produces a signed deliverable package.
user-invocable: true
metadata: {"openclaw":{"requires":{"bins":["qpdf","java"],"env":["LLM_API_KEY"]},"emoji":"♿"}}
---

# PDF/UA Remediation — V6

Use this skill for end-to-end PDF accessibility remediation.

## Workflow

### 1. Intake
- Confirm the source PDF is in `input/` and explicitly named by the user
- Create job scaffold: `python3 tools/packaging/package_scaffold.py output <job-name>`
- Copy source PDF to `output/<job-name>/pdf/` for reference

### 2. Structural check
```bash
tools/audit/run_qpdf_check.sh <pdf> output/<job-name>/reports/
```
Hard stop on FAIL. Fix with `qpdf --repair` if minor; escalate if severe.

### 3. Initial veraPDF validation
```bash
tools/audit/run_verapdf_profiles.sh \
  /opt/verapdf/verapdf \
  workspace/assets/validation_profiles/veraPDF-validation-profiles-integration \
  <pdf> \
  output/<job-name>/reports/
```
Parse results: `python3 tools/audit/parse_verapdf_summary.py output/<job-name>/reports/*.xml`

### 4. Repair pass (based on veraPDF failures)

Run applicable repair scripts. Always write to a new output path, never overwrite source.

Read `{baseDir}/rules/V6_CONTROLLING_RULESET.md` before any repair.
Read `{baseDir}/rules/METADATA_XMP_PARITY_HARD_GATE.md` before handoff.
Read `{baseDir}/rules/FONT_POLICY_EXPECTED_OPEN_FONTS_AND_GEOMETRY.md` before any font work.
Read `{baseDir}/checklists/PRE_HANDOFF_CHECKLIST.md` before packaging.

Common repair sequence:
```
fix_pdfua_identifier.py          <- almost always needed on unremediated PDFs
fix_metadata_xmp_parity.py       <- run after any metadata change
fix_figure_alt_text.py           <- required if figures missing Alt
fix_table_headers.py             <- required if TH missing Scope
fix_link_annotation_descriptions.py  <- required if links missing Contents
fix_list_numbering.py            <- required if L missing ListNumbering
```

### 5. Re-validate
Re-run veraPDF after each repair pass. Repeat until PDF/UA-1 passes.

### 6. Post-repair gates
```bash
python3 tools/audit/metadata_xmp_parity_audit.py <final.pdf>
python3 tools/qa/preservation_audit.py <source.pdf> <final.pdf>
python3 tools/audit/contrast_audit.py <final.pdf>
python3 tools/audit/table_semantics_audit.py <final.pdf>
python3 tools/qa/visual_qa.py <final.pdf> output/<job-name>/qa/
python3 tools/qa/render_compare.py <source.pdf> <final.pdf> output/<job-name>/qa/
```

### 7. Package and deliver
```bash
python3 tools/packaging/package_deliverables.py \
  output/<job-name> <final.pdf> --source-pdf <source.pdf>

python3 tools/packaging/status_json_writer.py output/<job-name>
python3 tools/packaging/checksums.py generate output/<job-name>
```

## Hard gates

- veraPDF PDF/UA-1: MUST PASS before handoff
- veraPDF WCAG-2-2-Machine: MUST PASS before handoff
- preservation_audit: MUST PASS (REVIEW requires human sign-off)
- metadata_xmp_parity: MUST PASS before handoff
- contrast_audit FAIL: flag for human review, document in STATUS.json
- axesCheck/PAC: NOT RUN in this environment — mark as EXTERNAL in STATUS.json

## Rules reference

All controlling rules are in `{baseDir}/rules/`. The V6 controlling ruleset
takes precedence over all V5 rules. V5 rules remain valid where not superseded.
