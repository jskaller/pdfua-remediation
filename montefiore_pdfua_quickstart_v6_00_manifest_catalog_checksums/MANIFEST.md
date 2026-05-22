# Montefiore PDF/UA Quickstart V6 Manifest

Date: 2026-05-21

This consolidated set supersedes prior quickstart v4/v5 package layouts for active workflow use. It incorporates the strict V5/V5.1 corrections:

- veraPDF PDF/UA failure is stop-and-remediate, not a normal handoff state.
- Pinned WCAG profile for PDF/UA-1: `PDF_UA/WCAG-2-2-Machine.xml`.
- PDF20 WCAG profiles are forbidden for PDF/UA-1 output unless explicitly targeting PDF/UA-2/PDF 2.0.
- Metadata requires PDF Info + XMP parity after final save.
- Local and external status are reported separately.
- Examples are read-only calibration/reference material unless explicitly named as active source PDFs.
- Font replacement is last resort and requires geometry matching; font files are not bundled.
