# Tools and Conventions

## Binary paths (inside Docker container)

Paths use environment variable fallbacks so they can be overridden without
rebuilding the image. Docker defaults are shown.

| Tool | Env var | Default path |
|------|---------|--------------|
| veraPDF | `VERAPDF_BIN` | `/opt/verapdf/verapdf` |
| qpdf | `QPDF_BIN` | `/usr/bin/qpdf` |
| python3 | — | `/usr/bin/python3` |
| java | — | `/usr/bin/java` |
| bash | — | `/usr/bin/bash` |

Scripts that invoke veraPDF or qpdf respect these env vars automatically.
To override: `export VERAPDF_BIN=/custom/path/verapdf` before running.

## Script paths (relative to openclaw_migration/ root)

All scripts take `<input> <output>` arguments where applicable.
All scripts write JSON to stdout and exit 0 (pass), 1 (fail), 2 (error).
All audit scripts accept `--out <file>` to also write JSON to a file —
required when feeding results to status_json_writer.py.

### Audit (read-only)
```
tools/audit/run_verapdf_profiles.sh    <verapdf-bin> <profiles-root> <pdf> <out-dir>
tools/audit/run_qpdf_check.sh          <pdf> <out-dir> [--linearize] [--out file.json]
tools/audit/parse_verapdf_summary.py   <xml> [<xml2> ...]
tools/audit/metadata_xmp_parity_audit.py  <pdf> [--org "Org Name"] [--out file.json]
tools/audit/font_inventory.py          <pdf> [--out file.json]
tools/audit/font_geometry_matcher.py   <text-sample> <font1.ttf> [font2.ttf ...]
tools/audit/table_semantics_audit.py   <pdf> [--out file.json]
tools/audit/contrast_audit.py          <pdf> [--out file.json]
```

### Repair (modifies PDFs — always write to a new output path)
```
tools/repair/fix_pdfua_identifier.py              <in.pdf> <out.pdf>
tools/repair/fix_metadata_xmp_parity.py           <in.pdf> <out.pdf>
tools/repair/fix_figure_alt_text.py               <in.pdf> <out.pdf> [--alt-map map.json]
tools/repair/fix_table_headers.py                 <in.pdf> <out.pdf>
tools/repair/fix_link_annotation_descriptions.py  <in.pdf> <out.pdf>
tools/repair/fix_list_numbering.py                <in.pdf> <out.pdf>
tools/repair/fix_notdef_glyphs.py                 <pdf>          (audit only)
tools/repair/fix_parent_tree_mcids.py             <in.pdf> <out.pdf>
tools/repair/fix_contrast_color_runs.py           <pdf>          (audit only)
tools/repair/font_replacement_report.py           <pdf>          (audit only)
```

### QA
```
tools/qa/preservation_audit.py  <source.pdf> <output.pdf> [--out file.json]
tools/qa/render_compare.py      <source.pdf> <output.pdf> <out-dir> [--dpi 150] [--threshold 0.01] [--out file.json]
tools/qa/visual_qa.py           <pdf> <out-dir> [--dpi 96] [--out file.json]
```

### Packaging
```
tools/packaging/package_scaffold.py     <output-base-dir> <job-name>
tools/packaging/package_deliverables.py <job-dir> <remediated-pdf> [--source-pdf original.pdf]
tools/packaging/status_json_writer.py   <job-dir> [--pdf original.pdf] [--out STATUS.json]
tools/packaging/checksums.py            generate <dir> [--out SHA256SUMS.txt]
tools/packaging/checksums.py            verify   <dir> <SHA256SUMS.txt>
```

## Capturing audit output for status_json_writer

status_json_writer.py reads JSON files from the job directory by name.
Each audit script must be run with `--out` pointing into the job directory:

```bash
JOB=workspace/output/my_job_pdfua_2026-05-22

python3 tools/audit/metadata_xmp_parity_audit.py input.pdf \
    --out $JOB/metadata_xmp_parity_audit.json

python3 tools/audit/contrast_audit.py input.pdf \
    --out $JOB/contrast_audit.json

python3 tools/qa/preservation_audit.py source.pdf output.pdf \
    --out $JOB/preservation_audit.json

python3 tools/qa/visual_qa.py output.pdf $JOB/qa/ \
    --out $JOB/visual_qa.json

# veraPDF summary JSON is written automatically by run_verapdf_profiles.sh
bash tools/audit/run_verapdf_profiles.sh \
    ${VERAPDF_BIN:-/opt/verapdf/verapdf} \
    workspace/assets/validation_profiles/veraPDF-validation-profiles-integration \
    output.pdf $JOB/

# qpdf check JSON is written automatically by run_qpdf_check.sh
bash tools/audit/run_qpdf_check.sh output.pdf $JOB/
```

## veraPDF profiles root (inside Docker)

`/app/workspace/assets/validation_profiles/veraPDF-validation-profiles-integration`

Pinned WCAG profile: `PDF_UA/WCAG-2-2-Machine.xml` relative to profiles root.

## Naming conventions

- Job names: `<basename>_pdfua_<YYYY-MM-DD>` e.g. `annual_report_pdfua_2026-05-22`
- Intermediate repair passes: `<basename>_pass1.pdf`, `_pass2.pdf`, etc.
- Final output: `<basename>_pdfua_final.pdf`
- Never overwrite source PDFs — always write to a new path
