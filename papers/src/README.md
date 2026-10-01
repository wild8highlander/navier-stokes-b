# `src/` — Compilable LaTeX Sources of the Papers

> **Navigation:** [repository root](../README.md) › **`src`**

![Format](https://img.shields.io/badge/Format-LaTeX-008080?style=flat-square&logo=latex&logoColor=white)
![Engine](https://img.shields.io/badge/Engine-pdflatex-008080?style=flat-square)
![License](https://img.shields.io/badge/License-IPL--RP--1.0-red?style=flat-square)

This directory holds the **compilable LaTeX sources** behind the PDFs
published in [`papers/`](../papers/README.md). The sources are the
authoritative textual record of the program: any wording in a typeset PDF
can be traced, diffed and quoted against them. For citation disputes,
translation work and precision quoting, the source is the ground truth —
the PDF is its projection.

Two groups live here:

- **[`main/`](main/README.md)** — the source of the full correction-b
  paper: `main.tex` (~55 KB, the primary document), `main_v2.tex` (the
  revision-stamped copy matching `papers/correction-b/main_v2.pdf`) and
  `main_v3.tex` (the working revision), complete with a custom
  accent-coloured sectioning setup and running headers;
- **[`preprint/`](preprint/README.md)** — `preprint.tex` and
  `preprint_v3.tex`, the sources of the compact NSE regularity preprint
  whose title page reads *"Correction b as Polarization Twisting:
  Analytical Proof of 3D Navier–Stokes Regularity without Dissipation"*.

The sources are intentionally plain LaTeX — standard article class plus
common formatting packages, no exotic dependencies — so any modern TeX
distribution compiles them without surprises. The monograph figures
referenced by the manuscripts are preserved with the Word editions in
[`docs/`](../docs/README.md); the two-language monograph of the runs
package lives in [`monograph/`](../monograph/README.md).

## Compilation

```bash
# full paper (correction-b) — two passes for references and headers
cd src/main
pdflatex main.tex && pdflatex main.tex

# preprint
cd src/preprint
pdflatex preprint.tex && pdflatex preprint.tex
```

TeX Live, MiKTeX, MacTeX and Overleaf all work as-is. Two passes are
needed for cross-references and running heads (the preamble defines an
accent colour for `titleformat` sectioning and `fancyhdr` headers inside
the document itself — no external style files to install).

## Versioning convention

`main.tex` and `main_v2.tex` are intentionally near-identical — the
revision stamp is the meaningful delta (`diff src/main/main.tex
src/main/main_v2.tex` shows exactly that). The convention going forward:
real content changes take a *new* filename (v3, v4, …), never a silent
edit of an existing pair, because the published PDFs must remain traceable
to the exact source that produced them. The PDFs in
[`papers/`](../papers/README.md) are pinned by
[`MANIFEST.json`](../MANIFEST.json); a source edit without a matching
re-typeset PDF is visible at a glance.

## Relationship map

| Layer | Directory | Format | Role |
|---|---|---|---|
| Final papers | [`papers/`](../papers/README.md) | PDF | what to cite |
| **Compilable sources** | **`src/` (this directory)** | `.tex` | what to diff and quote |
| Manuscripts | [`docs/`](../docs/README.md) | `.docx` | what circulated editorially |
| Monograph | [`monograph/`](../monograph/README.md) | PDF + DOCX | the book-length treatment |
| Verification | [`verification/`](../verification/README.md) | code | what backs the numbers |

## From source to claim to verification

A worked example of the traceability chain: the derivation section of
`main.tex` contains the closed form of the constant; the same closed form
is `bCorrection` in
[`verification/lean4/ResearchPapersVerification/Common/Foundation.lean`](../verification/lean4/README.md)
— compiled with `bCorrection_pos` and `bCorrection_lt_one`; the same
number is printed by every Section 1 port
(`python3 verification/section1_correction_b/python/verify.py` and its
ten siblings); and the value anchors the results table of the root README.
Four representations — prose, theorem, computation, table — of one
mathematical object, all inside one repository. That is the standard every
claim here is held to.


## Package inventory

| File | Size | Document it produces |
|---|---|---|
| [`main/main.tex`](main/README.md) | ~55 KB | the full paper (primary source) |
| [`main/main_v2.tex`](main/README.md) | ~55 KB | the revision stamp behind `papers/correction-b/main_v2.pdf` |
| [`main/main_v3.tex`](main/README.md) | — | the working revision |
| [`preprint/preprint.tex`](preprint/README.md) | — | the compact preprint behind `papers/preprint/preprint_v2.pdf` |
| [`preprint/preprint_v3.tex`](preprint/README.md) | — | the working revision |

## House typography, for future revisions

Both documents share conventions a revision should preserve so the corpus
stays visually and mechanically coherent:

- the **accent colour** for `titleformat` sectioning is defined in each
  preamble — keep the definition local (no shared .sty), because each PDF
  must remain buildable from its own folder alone;
- **running heads** via `fancyhdr`: title on even pages, section on odd;
- **standard math environments** only — no custom theorem classes beyond
  basics, keeping the sources portable across engines and editors;
- **two-pass compilation** always; a single pass produces unresolved
  references and stale headers, which is a documentation bug, not a
  feature.

## Diffing discipline

The published PDFs are pinned by [`MANIFEST.json`](../MANIFEST.json), so a
source edit without a re-typeset PDF is visible immediately. The intended
cycle is: edit `*_v3.tex` → re-typeset → promote to a new stamped name
(`_v3` → `_v4`) *only* when the change is meant to become citable → commit
source, PDF and manifest in one change. `diff main.tex main_v2.tex`
demonstrates the expected shape of a stamp-only delta: the banner and
metadata differ, the mathematics does not.

---

Navigation: [repository root](../README.md) · [papers](../papers/README.md) · [docs](../docs/README.md) · [monograph](../monograph/README.md) · [IPL-RP-1.0](../LICENSE.md)

*Part of [wild8highlander/navier-stokes-b](https://github.com/wild8highlander/navier-stokes-b) — © 2026 Isaev Iskhak Khamzatovich, all rights reserved.*
