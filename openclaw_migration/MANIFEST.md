# Manifest
## Rule → Script mapping for the Montefiore PDF/UA Remediation Suite

This file is the authoritative map between rules and scripts. When you change
a rule, check the scripts listed under it. When you change a script, check
the rule that governs it. Changes to a rule and its governed scripts belong
in the same commit.

See CONTRIBUTING.md for commit conventions.

---

## Rules and their governed scripts

---

### ALT_TEXT_RULE.md
Governs the full alt text remediation pipeline triggered by veraPDF Figure
element failures. Covers auto-placeholder, vision model draft generation,
human review report, and approved text application.

**Primary scripts:**
- `tools/repair/fix_figure_alt_text.py` — auto placeholder + approved text application
- `tools/repair/generate_alt_text_drafts.py` — vision model draft generation
- `tools/repair/generate_alt_text_review_report.py` — interactive HTML review report

**Touches:**
- `tools/packaging/status_json_writer.py` — alt_text gate
- `tools/audit/parse_verapdf_summary.py` — surfaces Figure failures that trigger the path

---

### CONTRAST_REMEDIATION_REPORTING_RULE.md
Governs WCAG contrast audit and automated color correction. Covers the
`color-contrast` library usage, modulate() for auto-fixing, and disclosure
requirements for any color changes.

**Primary scripts:**
- `tools/audit/contrast_audit.py`
- `tools/repair/fix_contrast_color_runs.py`

**Touches:**
- `tools/packaging/status_json_writer.py` — contrast gate

---

### FONT_POLICY_EXPECTED_OPEN_FONTS_AND_GEOMETRY.md
Governs font substitution decisions, metric-compatible font selection,
and geometry matching. Defines the approved open font catalog.

**Primary scripts:**
- `tools/audit/font_inventory.py`
- `tools/audit/font_geometry_matcher.py`
- `tools/repair/fix_notdef_glyphs.py`
- `tools/repair/font_replacement_report.py`

---

### FONT_REPLACEMENT_REPORTING_RULE.md
Governs disclosure requirements when fonts are substituted. Works in
conjunction with FONT_POLICY.

**Primary scripts:**
- `tools/repair/font_replacement_report.py`

**Touches:**
- `tools/packaging/status_json_writer.py`

---

### METADATA_RULESET_RECAP.md / METADATA_XMP_PARITY_HARD_GATE.md
Governs PDF Info dictionary and XMP packet parity requirements.
Metadata parity is a hard gate — failure blocks packaging.

**Primary scripts:**
- `tools/audit/metadata_xmp_parity_audit.py`
- `tools/repair/fix_metadata_xmp_parity.py`
- `tools/repair/fix_pdfua_identifier.py`

**Touches:**
- `tools/packaging/status_json_writer.py` — metadata_parity gate

---

### NON_NEGOTIABLE_LOCAL_GATES.md
Defines the 13 gates that must pass before a document receives
PRODUCTION_FINAL_LOCAL_PREFLIGHT status. Governs the overall gate
sequence rather than any specific script.

**Touches (all gate scripts):**
- `tools/audit/run_qpdf_check.sh`
- `tools/audit/run_verapdf_profiles.sh`
- `tools/audit/metadata_xmp_parity_audit.py`
- `tools/qa/preservation_audit.py`
- `tools/qa/render_compare.py`
- `tools/qa/visual_qa.py`
- `tools/packaging/status_json_writer.py`

---

### OCR_REMEDIATION_RULE.md
Governs the OCR pre-flight gate for image-only and scanned pages.
OCR must run before any structural repair scripts.

**Primary scripts:**
- `tools/audit/detect_image_only_pages.py`

**Touches:**
- `tools/qa/preservation_audit.py` — REVIEW expected after OCR
- `tools/qa/render_compare.py` — hard stop if visual diff after OCR
- `tools/packaging/status_json_writer.py` — ocr_detection gate

---

### PDFPLUMBER_USAGE_RULE.md
Governs geometric table detection as the primary visual table presence
audit, complementing the struct tree analysis in table_semantics_audit.py.

**Primary scripts:**
- `tools/audit/table_semantics_audit.py` — pdfplumber pass integrated here

---

### PIKEPDF_USAGE_RULE.md
Governs low-level PDF object repair. Defines permitted use cases,
proportional change limit (10% of total objects), mandatory checkpoint
and verification sequence.

**Primary scripts:**
- `tools/repair/fix_parent_tree_mcids.py`

**Touches:**
- `tools/qa/preservation_audit.py` — mandatory after pikepdf write
- `tools/packaging/status_json_writer.py`

---

### PYPDF_FALLBACK_RULE.md
Governs pypdf use as a fallback when PyMuPDF fails to open a document.
Defines the 7-step fallback procedure.

**Touches (fallback logic inline in):**
- `tools/repair/fix_figure_alt_text.py`
- `tools/repair/fix_table_headers.py`
- `tools/packaging/status_json_writer.py`

---

### REFERENCE_SCOPE_RULE.md
Governs TH Scope attribute requirements for table header cells.

**Primary scripts:**
- `tools/audit/table_semantics_audit.py`
- `tools/repair/fix_table_headers.py`

---

### TABLE_SEMANTICS_RULE.md
Governs the full table semantics audit and repair pipeline, including
the pdfplumber/struct tree cross-reference.

**Primary scripts:**
- `tools/audit/table_semantics_audit.py`
- `tools/repair/fix_table_headers.py`

---

### V5_VERAPDF_PROFILE_SELECTION.md
Governs veraPDF profile selection: PDF/UA-1 + pinned WCAG-2-2-Machine.xml.

**Primary scripts:**
- `tools/audit/run_verapdf_profiles.sh`
- `tools/audit/parse_verapdf_summary.py`

---

### V5_HARD_MULTIPASS_GATE.md / V5_EXTERNAL_STATUS_RULE.md
Governs multi-pass repair sequencing and external validator status reporting.

**Touches:**
- `tools/packaging/status_json_writer.py`
- `tools/audit/run_verapdf_profiles.sh`

---

### V6_CONTROLLING_RULESET.md
Top-level governing document. References all other rules. No scripts
are solely governed by this rule — it coordinates the whole system.

---

### VISUAL_QA_RULE.md
Governs vision model usage for two purposes: (1) post-repair visual
page comparison as a final gate, and (2) alt text draft generation
via generate_alt_text_drafts.py. Defines when the vision model is
required, what it checks, and disclosure requirements.

**Primary scripts:**
- `tools/qa/visual_qa.py`
- `tools/qa/render_compare.py`
- `tools/repair/generate_alt_text_drafts.py`

**Touches:**
- `tools/packaging/status_json_writer.py` — visual_qa gate

---

## Cross-cutting scripts (no single governing rule)

These scripts are called by every job regardless of which repair path
was taken. Changes to them should be reviewed against all rules.

| Script | Purpose |
|--------|---------|
| `tools/packaging/package_scaffold.py` | Creates job directory structure |
| `tools/packaging/package_deliverables.py` | Promotes finished files to output/ |
| `tools/packaging/checksums.py` | SHA-256 verification |
| `tools/packaging/status_json_writer.py` | Assembles STATUS.json from all gate results |
| `tools/packaging/cleanup_job.py` | Operator tool — clears jobs/ after upload confirmed |
| `smoke_test.py` | Validates container setup on first run |

---

## New tool addition checklist

When adding a new tool to the pipeline:

- [ ] New rule file in `skills/montefiore-pdfua-unified-v6/rules/`
- [ ] Script added to `tools/audit/`, `tools/repair/`, `tools/qa/`, or `tools/packaging/`
- [ ] Gate added to `status_json_writer.py` gate_files dict
- [ ] TOOLS.md updated with script usage
- [ ] SKILL.md updated if the new rule changes agent decision logic
- [ ] This MANIFEST.md updated
- [ ] smoke_test.py updated if the tool requires a new binary or library
- [ ] requirements.txt updated if a new Python package is needed
