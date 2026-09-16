# `papers/` — Typeset Articles of the b-Correction Program (PDF)

> **Navigation:** [repository root](../README.md) › **`papers`**

![Papers](https://img.shields.io/badge/Content-Research_papers-1284BA?style=flat-square)
![Format](https://img.shields.io/badge/Format-PDF-D0021B?style=flat-square&logo=adobeacrobatreader&logoColor=white)
![License](https://img.shields.io/badge/License-IPL--RP--1.0-red?style=flat-square)

The **final typeset PDF articles** of the b-correction program, kept exactly
in the form in which they circulate. Each subfolder is one article (or one
article in two language editions). The LaTeX sources behind every PDF live
in [`src/`](../src/README.md); the full book-length monographs live in
[`monograph/`](../monograph/README.md) and, as circulating Word editions,
in [`docs/`](../docs/README.md); the numerical protocols behind every
quantitative claim live in [`data/results/`](../data/results/README.md).

## Collections

| Collection | Editions | Program |
|---|---|---|
| [`preprint/`](preprint/README.md) | `preprint_v1.pdf`, `preprint_v2.pdf` (~120 KB, byte-identical twins) | the compact statement of the NSE regularity result — **the best first read** |
| [`correction-b/`](correction-b/README.md) | `main.pdf`, `main_v2.pdf` (~2.3 MB, byte-identical twins) | the full paper: regularity of 3D NSE through the polarization correction b |
| [`kdv/`](kdv/README.md) | `KdV_b_correction_Chapter16_RU.pdf`, `..._EN.pdf` (two genuinely independent language editions) | the continuation: the same constant b in Korteweg–de Vries soliton interactions |

The twin-naming convention (`main` / `main_v2`, `v1` / `v2`) inside
`correction-b/` and `preprint/` exists for citation convenience: both names
resolve to the same bytes, so either may be quoted, and the
revision-stamped name is the one the LaTeX sources track. The KdV chapter,
by contrast, is *not* a twin pair — the RU and EN editions were typeset
independently and carry their own pagination.

## Reading order

1. **`preprint/preprint_v2.pdf`** — ~120 KB, the shortest complete
   exposition of the NSE result: the correction b, the rotation angle, the
   Leray-absorption argument, the regularity conclusion, the 3.5× BKM
   reduction. Fifteen minutes and you are current.
2. **`correction-b/main_v2.pdf`** — the full article: derivation of b from
   the Kirchhoff point-vortex system, the regularity proof, and the
   numerical stress tests cross-referenced against the pinned protocols.
3. **`kdv/KdV_b_correction_Chapter16_RU.pdf`** (or `_EN.pdf`) — the
   integrable continuation: the same constant surfacing in soliton
   interactions of the Korteweg–de Vries equation.

## Verification support

Every quantitative claim in these articles maps onto a section of the
eleven-language framework in [`verification/`](../verification/README.md):
section 1 — the value and the bounds of b; section 2 — the regularity
argument chain; section 4 — the KdV solitons (with the C++ pseudospectral
port as the computational workhorse). The papers deliberately do not carry
their own numbers as authority — [`data/results/`](../data/results/README.md)
does — so a dispute about any figure is settled by rerunning a script, not
by re-reading prose.

## Provenance

All PDFs are pinned by [`MANIFEST.json`](../MANIFEST.json) (sha256 + byte
size) and are covered by the Zenodo DOI
[10.5281/zenodo.21825394](https://doi.org/10.5281/zenodo.21825394); cite
the repository per [`CITATION.cff`](../CITATION.cff). The license
([IPL-RP-1.0](../LICENSE.md)) permits reading, one personal unmodified
backup, and quoting with full attribution.


## The document graph, at a glance

```text
monograph (RU/EN × PDF/DOCX)          the book-length treatment
      │
      ├── papers/preprint             the 15-minute statement
      ├── papers/correction-b         the full paper (cite this)
      └── papers/kdv                  the integrable continuation
              ▲
              └── verification/section4_kdv      the executable claim
```

Every arrow is bidirectional in practice: the papers quote the protocols in
[`data/results/`](../data/results/README.md), and the verification
framework asserts every quantitative statement the papers make. The papers
deliberately carry no authority of their own over numbers — which is why a
dispute about any figure is settled by rerunning a script rather than
re-reading prose.

## Which file to cite

| Purpose | File |
|---|---|
| citing the regularity result | `correction-b/main_v2.pdf` (or the Zenodo DOI) |
| citing the compact statement | `preprint/preprint_v2.pdf` |
| citing the KdV continuation | `kdv/KdV_b_correction_Chapter16_EN.pdf` (or `_RU`) |

The byte-identical twins are a convenience, not two documents: either name
resolves to the same bytes, and
[`MANIFEST.json`](../MANIFEST.json) proves it. The KdV editions are
independent typesettings — cite the language you read.

## Accessibility notes

All PDFs are text-based (selectable, searchable) and the figures inside
them are the same 300-dpi renders shipped in
[`data/plots/`](../data/plots/README.md). If you need the content in
another form — the Word editions in [`docs/`](../docs/README.md) open in
screen readers and editors; the LaTeX sources in [`src/`](../src/README.md)
rebuild the text in any TeX environment; and reasonable alternative-format
requests are welcome via
[issues](https://github.com/wild8highlander/navier-stokes-b/issues/new?template=feature_request.yml).

---

Navigation: [repository root](../README.md) · [src (LaTeX)](../src/README.md) · [monograph](../monograph/README.md) · [docs (Word)](../docs/README.md) · [IPL-RP-1.0](../LICENSE.md)

*Part of [wild8highlander/navier-stokes-b](https://github.com/wild8highlander/navier-stokes-b) — © 2026 Isaev Iskhak Khamzatovich, all rights reserved.*
