# External Tools Required

This quickstart set intentionally does not include qpdf binaries/source trees or veraPDF installers/binaries.

## Required external binaries

- qpdf
  - Tested package in prior work: `qpdf-12.3.2-bin-linux-x86_64.zip`.
  - Required gate: `qpdf --check <pdf>` must pass.
- veraPDF
  - Tested package in prior work: `verapdf-greenfield-1.30.1-installer.zip`, veraPDF 1.30.1.
  - Required gates: PDF/UA target validation and pinned WCAG profile validation.

## Required bundled non-binary assets

- veraPDF validation profiles repository XML files are included in the assets package.
- For PDF/UA-1 local WCAG validation, use exactly `validation_profiles/veraPDF-validation-profiles-integration/PDF_UA/WCAG-2-2-Machine.xml`.

## Optional external confirmation tools

- axesCheck / axes4.
- PAC.

External axesCheck/PAC pass must never be claimed unless the tool is actually run and passes.

## Runtime libraries typically required

- Python 3.
- PyMuPDF (`fitz`).
- pikepdf.
- lxml.
- Pillow.
- FontTools, only when font geometry matching is needed.
- A PDF rendering backend available to PyMuPDF for visual QA.
