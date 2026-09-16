# 📄 Papers — Final Typeset PDF Papers

> **Navigation:** **`papers`**

![Papers](https://img.shields.io/badge/Content-Research%20Papers-blue?style=flat-square) ![License](https://img.shields.io/badge/License-IPL--RP--1.0-red?style=flat-square)

This is where the **final typeset PDF papers** of the b-correction program are collected.
Each subfolder is one paper (or one paper in two language editions),
stored exactly as it circulated. LaTeX sources are in [`src/`](../src/README.md),
Word monographs in [`docs/`](../docs/README.md), numerical protocols in [`data/results/`](../data/results/).

## 📑 Collections

| Collection | Editions | Program |
|---|---|---|
| **correction-b** | `main.pdf`, `main_v2.pdf` (~2.3 MB, identical) | 3D NSE regularity via the polarization correction b |
| **preprint** | `preprint_v1.pdf`, `preprint_v2.pdf` (~120 KB, identical) | Compact exposition of the regularity result — the best first read |
| **kdv** | `KdV_b_correction_Chapter16_EN.pdf`, `..._RU.pdf` | Continuation of the program: Korteweg–de Vries solitons under the b-correction |

The PDF pairs inside `correction-b/` and `preprint/` are byte-identical twins under
different names (`main` / `main_v2`, `v1` / `v2`) for citation convenience;
the KdV chapter ships in two genuinely independent language editions.

## 🧭 Reading Order

1. **`preprint/preprint_v2.pdf`** — ~120 KB, the shortest complete exposition
   of the NS result: the b-correction, the rotation angle, the 3.5× reduction of the BKM criterion.
2. **`correction-b/main_v2.pdf`** — the full paper: the derivation of b from the
   Kirchhoff system, the regularity proof, numerical stress-tests.
3. **`kdv/KdV_b_correction_Chapter16_RU.pdf`** (or `_EN.pdf`) — the integrable
   continuation: the same constant in soliton interactions.

## 🔬 Verification Support

Every quantitative claim of the papers maps onto a section of the
11-language framework [`verification/`](../verification/README.md):
Section 1 — the value and bounds of b; Section 2 — the chain of the regularity argument;
Section 4 — KdV solitons (the C++ pseudospectral port).

*Part of [wild8highlander/navier-stokes-b](https://github.com/wild8highlander/navier-stokes-b) · License [IPL-RP-1.0](../LICENSE.md) — All Rights Reserved*
