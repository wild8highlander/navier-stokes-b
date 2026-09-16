# `src/main/` — Source of the Full Correction-b Paper

> **Navigation:** [`src`](../README.md) › **`main`**

![Format](https://img.shields.io/badge/Format-LaTeX-008080?style=flat-square&logo=latex&logoColor=white) ![License](https://img.shields.io/badge/License-IPL--RP--1.0-red?style=flat-square)

The compilable LaTeX source of the full paper: the Kirchhoff derivation of
the constant, the polarization twist, the regularity proof and the
numerical section — everything behind
[`papers/correction-b/main_v2.pdf`](../../papers/correction-b/README.md).

## Files

| File | Size | Role |
|---|---|---|
| [`main.tex`](main.tex) | ~55 KB | the primary document |
| [`main_v2.tex`](main_v2.tex) | ~55 KB | the revision-stamped copy matching the published `main_v2.pdf` |
| [`main_v3.tex`](main_v3.tex) | — | the working revision |

The preamble is self-contained: the accent colour for `titleformat`
sectioning and the `fancyhdr` running heads are defined inside the
document — no external style files to install.

## Compile

```bash
cd src/main
pdflatex main_v2.tex && pdflatex main_v2.tex    # two passes for refs/headers
```

## Versioning convention

`main.tex` and `main_v2.tex` are near-identical by design — the revision
stamp is the delta (`diff main.tex main_v2.tex`). Real content changes take
a *new* filename (v3, v4, …), never a silent edit of an existing pair:
published PDFs must remain traceable to the exact source that produced
them.

---

---

Navigation: [repository root](../README.md) · [src](../README.md) · [papers/correction-b](../../papers/correction-b/README.md) · [IPL-RP-1.0](../../../LICENSE.md)

*Part of [wild8highlander/navier-stokes-b](https://github.com/wild8highlander/navier-stokes-b) - (c) 2026 Isaev Iskhak Khamzatovich, all rights reserved.*

