# `monograph/` — The Two-Language Monograph and the Open-Problems Appendices

> **Navigation:** [repository root](../README.md) › **`monograph`**

![Monograph](https://img.shields.io/badge/Formats-PDF_%2B_DOCX-2B579A?style=flat-square)
![Languages](https://img.shields.io/badge/Editions-RU_%2B_EN-1284BA?style=flat-square)
![License](https://img.shields.io/badge/License-IPL--RP--1.0-red?style=flat-square)

The book-length treatment of the b-correction program, in two languages
(RU/EN) and two formats (PDF/DOCX), plus the standalone appendices that
define and execute the **seven-open-problem program (P1–P7)**. Where the
articles in [`papers/`](../papers/README.md) state the result, the
monograph *documents the program*: every run with its parameter table,
every registered success criterion, every figure, and the chapters that
connect the constant to neighbouring systems — including the
hadron-collider scale discussion.

## Contents

| File / directory | Description |
|---|---|
| `MONOGRAPH_EN.pdf` / `MONOGRAPH_EN.docx` | English monograph — full derivation, all runs, tables and plots |
| `MONOGRAPH_RU.pdf` / `MONOGRAPH_RU.docx` | Russian monograph — same content, including the hadron-collider chapter |
| `cover_en.html` / `cover_ru.html` | print-ready cover layouts used to typeset the editions |
| [`open-problems/`](open-problems/README.md) | appendix: the seven-open-problem program — master document, runnable code, JSON results, figures |
| [`open-problems-b/`](open-problems-b/README.md) | appendix extension: the P4b ensemble (T = 8) and the P5b full-duplex b-protocol |

The PDF is the citable edition; the DOCX is the editorial source edition
(kept in sync with the circulating form); the cover HTML files are the
print layout used for both languages. All four documents are pinned by
[`MANIFEST.json`](../MANIFEST.json).

## Reading order

The monograph is self-contained. Start with the introduction and the
chapter on the constant b; the middle chapters walk the verification chain
L1–L5 and the physics runs P1–P6 exactly as registered in
[`data/results/`](../data/results/README.md); the open-problems appendices
then show the *executable* form of the program — every problem P1–P7 has
code, a JSON protocol and a figure, and re-running
`python3 open-problems/code/run_all.py` (~10 min) regenerates them all.
The monograph quotes the protocols; the protocols never quote the
monograph.

## Related material

- Papers (preprint → full paper → KdV chapter): [`papers/`](../papers/README.md)
- LaTeX sources of the articles: [`src/`](../src/README.md)
- Data and plots of the runs: [`data/`](../data/README.md)
- The P7 registry at the repository root: [`OPEN_PROBLEMS_7.md`](../OPEN_PROBLEMS_7.md)
- The verification framework backing every number: [`verification/`](../verification/README.md)


## Chapter map

The monograph is organised so that each claim has exactly one home chapter,
and each chapter has a corresponding evidence pointer in the repository:

| Part | Chapters | Evidence pointer |
|---|---|---|
| The constant | derivation from the Kirchhoff system; the Rodrigues form; the Leray absorption | [`data/results/baseline/l1–l3`](../data/results/baseline/README.md); [verification section 1](../verification/README.md) |
| The chain | L1–L5 with full parameter tables | [`data/results/baseline/`](../data/results/baseline/README.md) |
| The runs | P1–P6, each with its registered criteria and outcomes | [`data/results/p*.json`](../data/results/README.md); [`code/`](../code/README.md) |
| Applications | the hadron-collider chapter and the communication protocol | [`monograph/open-problems/`](open-problems/README.md) (P7) |
| Open problems | the program itself: statements, plans, criteria, outcomes | [`OPEN_PROBLEMS_7.md`](../OPEN_PROBLEMS_7.md); [`open-problems/`](open-problems/README.md) |

## Which edition for which purpose

| Purpose | Edition |
|---|---|
| citing the program-level argument | `MONOGRAPH_EN.pdf` or `MONOGRAPH_RU.pdf` (the DOI resolves to the archived set) |
| annotating in a word processor | the `.docx` editions |
| print reproduction | the PDFs + the `cover_{ru,en}.html` print layouts |
| verifying a specific number | never the monograph — [`data/results/summary_numbers.json`](../data/results/summary_numbers.json) |

## Why both formats are kept

The PDF is the citable, immutable projection; the DOCX is the editorial
form the text actually lives in. Keeping both — pinned by
[`MANIFEST.json`](../MANIFEST.json) — means the citable artefact and the
editable artefact are always both present and both checksummed, so a
future revision cannot silently diverge from what was cited.

---

Navigation: [repository root](../README.md) · [papers](../papers/README.md) · [data](../data/README.md) · [verification](../verification/README.md) · [IPL-RP-1.0](../LICENSE.md)

*Part of [wild8highlander/navier-stokes-b](https://github.com/wild8highlander/navier-stokes-b) — © 2026 Isaev Iskhak Khamzatovich, all rights reserved.*
