# Workflow Guide
## Montefiore PDF/UA Remediation Suite

This document describes the complete operational workflow from receiving a
Jira ticket to uploading the remediated output. It is written for team
members running the remediation pipeline day-to-day.

---

## How the workspace works

**All PDFs and job data live on your host machine — nothing is stored inside
the Docker container.** The container holds only code and tools. Your workspace
directory is mounted into the container at runtime, so a container rebuild
never loses any work.

Set your workspace location in `.env`:
```bash
WORKSPACE_PATH=/Users/yourname/montefiore-workspace
```

Use an absolute path. The directory will be created automatically on first run.

---

## Workspace structure

```
~/montefiore-workspace/
  input/
    MM-17893/                        ← one folder per Jira ticket
      consent_form.pdf               ← source PDFs, never modified
      patient_intake.pdf
      annual_report_v2.pdf           ← rework version (see Rework below)

  jobs/                              ← active work — temporary, clear when done
    MM-17893_consent_form/
      STATUS.json                    ← live job status
      audit/                         ← veraPDF, qpdf, pdfplumber outputs
      repair/                        ← intermediate repair checkpoints
      qa/                            ← visual QA renders and reports

  output/
    MM-17893_remediated/             ← finished files only
      consent_form_remediated.pdf    ← PASS → upload to Jira
      consent_form_AUDIT_REPORT.md   ← always included
      patient_intake_remediated.pdf
      patient_intake_AUDIT_REPORT.md
      review/                        ← needs human sign-off before upload
        annual_report_review.pdf
        annual_report_AUDIT_REPORT.md
      failed/                        ← could not be remediated automatically
        lab_results_failed.pdf
        lab_results_AUDIT_REPORT.md

  assets/                            ← veraPDF profiles (auto-populated at build)
  skills/                            ← agent rules and SKILL.md
  templates/                         ← report templates
```

---

## Standard workflow

### Step 1 — Receive ticket

A Jira ticket arrives with one or more PDF attachments. Download the PDFs.

### Step 2 — Set up input

Create a folder named after the Jira ticket and drop the PDFs in:

```bash
mkdir -p ~/montefiore-workspace/input/MM-17893
cp ~/Downloads/consent_form.pdf ~/montefiore-workspace/input/MM-17893/
cp ~/Downloads/patient_intake.pdf ~/montefiore-workspace/input/MM-17893/
```

The ticket folder name IS the job identifier. Use it exactly as it appears
in Jira — `MM-17893`, `PDFUA-4421`, etc.

### Step 3 — Start the container

```bash
cd /path/to/pdfua-remediation/openclaw_migration
docker compose up -d
```

### Step 4 — Run remediation

Tell the agent which ticket to process:

```
Process all PDFs in input/MM-17893
```

The agent will:
1. Detect image-only pages → run OCR if needed
2. Run qpdf structural check
3. Run veraPDF PDF/UA + WCAG audit
4. Apply all applicable repair scripts
5. Re-run audit gates to confirm fixes
6. Run visual QA on any visually modified pages
7. Run preservation audit
8. Write STATUS.json
9. Promote finished files to `output/MM-17893_remediated/`

You can also process a single file:
```
Process input/MM-17893/consent_form.pdf
```

### Step 5 — Check results

Open `output/MM-17893_remediated/` on your host machine.

| What you see | Means | Action |
|-------------|-------|--------|
| `consent_form_remediated.pdf` | PASS | Upload to Jira |
| `review/annual_report_review.pdf` | REVIEW_REQUIRED | Inspect before uploading |
| `failed/lab_results_failed.pdf` | FAIL | Read AUDIT_REPORT, escalate |

### Step 6 — Upload to Jira

**For PASS files:** Upload both files to the Jira ticket:
- `consent_form_remediated.pdf`
- `consent_form_AUDIT_REPORT.md`

**For REVIEW files:** Read `annual_report_AUDIT_REPORT.md` first.
If you approve the result, promote it:
```bash
# Rename and move to the main output folder
mv output/MM-17893_remediated/review/annual_report_review.pdf \
   output/MM-17893_remediated/annual_report_remediated.pdf
mv output/MM-17893_remediated/review/annual_report_AUDIT_REPORT.md \
   output/MM-17893_remediated/annual_report_AUDIT_REPORT.md
```
Then upload as normal. If you reject it, see Rework below.

**For FAIL files:** Upload only `lab_results_AUDIT_REPORT.md` to the ticket
with a comment explaining manual remediation is required. Do not upload the
`_failed.pdf` unless the client specifically requests the best attempt.

### Step 7 — Clean up jobs/

After confirming the Jira upload, clear the active job directory:

```bash
python3 tools/packaging/cleanup_job.py MM-17893_consent_form
```

This removes the `jobs/MM-17893_consent_form/` working directory.
`output/MM-17893_remediated/` is preserved — it is the permanent record.

To clean all completed jobs for a ticket at once:
```bash
python3 tools/packaging/cleanup_job.py --ticket MM-17893
```

---

## Rework workflow

A rework occurs when a REVIEW file is rejected, or when Montefiore returns
a previously delivered PDF requesting further remediation.

### File naming for rework

Add a version suffix to the filename before dropping into input:

```
annual_report.pdf       ← original
annual_report_v2.pdf    ← first rework
annual_report_v3.pdf    ← second rework
```

The pipeline treats each version as an independent job. Output follows the
same suffix:

```
output/MM-17893_remediated/
  annual_report_v2_remediated.pdf
  annual_report_v2_AUDIT_REPORT.md
```

### Rework from a REVIEW result

1. Note what the AUDIT_REPORT says needs attention
2. If it can be addressed automatically, tell the agent specifically:
   ```
   Process input/MM-17893/annual_report_v2.pdf
   Focus on: [issue from audit report]
   ```
3. If it requires manual intervention first (Acrobat Pro, CommonLook),
   remediate manually, save as `annual_report_v2.pdf`, drop in input/,
   then run through the pipeline for a verification pass

### Rework from a FAIL result

1. Read `failed/lab_results_AUDIT_REPORT.md` for recommended manual actions
2. Attempt manual remediation in Acrobat Pro or CommonLook
3. Save as `lab_results_v2.pdf`, drop in `input/MM-17893/`
4. Run through pipeline — the agent will re-audit and attempt any remaining fixes

---

## What the AUDIT_REPORT contains

Every output PDF is accompanied by an `_AUDIT_REPORT.md`. This is the
permanent record of what was done and the evidence of compliance.

**PASS report includes:**
- veraPDF result before and after (failure count: N → 0)
- qpdf result
- Repairs applied with counts (e.g. "14 TH scope attributes added")
- OCR: applied or not, pages, language, confidence
- Visual QA: result, pages checked, model used
- Preservation audit: result
- Checksums: source and output SHA-256

**REVIEW report adds:**
- Review reason: which gate flagged and why
- Reviewer action required: specific things to check

**FAIL report adds:**
- Fail reason: which hard gate failed
- Gates passed before failure: what did succeed
- Recommended manual action: what to try in Acrobat/CommonLook
- Escalation: note that manual remediation is required

---

## Output naming reference

| File | When present |
|------|-------------|
| `{name}_remediated.pdf` | PASS — upload to Jira |
| `{name}_AUDIT_REPORT.md` | Always — upload alongside PDF |
| `review/{name}_review.pdf` | REVIEW_REQUIRED — inspect first |
| `review/{name}_AUDIT_REPORT.md` | Always with review PDF |
| `failed/{name}_failed.pdf` | FAIL — do not upload unless asked |
| `failed/{name}_AUDIT_REPORT.md` | Always with failed PDF — upload this |

---

## Source files are never modified

The pipeline never writes to `input/`. Source PDFs are read-only by
convention. You can safely leave them in `input/` indefinitely — they
are not consuming significant space relative to the job artifacts.

Clear `input/MM-17893/` manually once you are confident the ticket is
fully resolved and no further rework is expected.

---

## Disk space

The `jobs/` directory contains intermediate artifacts that can be
3-5x the size of the source PDFs (rendered page images, repair
checkpoints, veraPDF XML reports, pdfplumber maps). Clear job
directories promptly after confirming uploads.

`output/` contains only the final PDFs and Markdown reports — small.
`input/` contains only the source PDFs — size of what you downloaded.

The Docker container image itself contains no PDF data and stays lean.
