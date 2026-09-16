# `src/preprint/` — Source of the Compact Preprint

> **Navigation:** [`src`](../README.md) › **`preprint`**

![Format](https://img.shields.io/badge/Format-LaTeX-008080?style=flat-square&logo=latex&logoColor=white) ![License](https://img.shields.io/badge/License-IPL--RP--1.0-red?style=flat-square)

The compilable LaTeX source of the compact NSE regularity preprint whose
title page reads *"Correction b as Polarization Twisting: Analytical Proof
of 3D Navier–Stokes Regularity without Dissipation"* — behind
[`papers/preprint/preprint_v2.pdf`](../../papers/preprint/README.md).

## Files

| File | Role |
|---|---|
| [`preprint.tex`](preprint.tex) | the source of the circulating preprint |
| [`preprint_v3.tex`](preprint_v3.tex) | the working revision |

## Compile

```bash
cd src/preprint
pdflatex preprint.tex && pdflatex preprint.tex
```

Same house typography as the full paper (accent-coloured sectioning,
running headers), standard article class, two-pass compilation.

---

---

Navigation: [repository root](../README.md) · [src](../README.md) · [papers/preprint](../../papers/preprint/README.md) · [IPL-RP-1.0](../../../LICENSE.md)

*Part of [wild8highlander/navier-stokes-b](https://github.com/wild8highlander/navier-stokes-b) - (c) 2026 Isaev Iskhak Khamzatovich, all rights reserved.*

