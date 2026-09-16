# `papers/preprint/` — the Compact NSE Regularity Preprint

> **Navigation:** [`papers`](../README.md) › **`preprint`**

![Format](https://img.shields.io/badge/Format-PDF-D0021B?style=flat-square&logo=adobeacrobatreader&logoColor=white) ![License](https://img.shields.io/badge/License-IPL--RP--1.0-red?style=flat-square)

The shortest complete statement of the program's NSE result — the
recommended first read. `preprint_v2.pdf` (~120 KB, ~15 pages of plain
narrative) covers the correction b, the rotation angle θ_b, the
Leray-absorption argument, the regularity conclusion and the 3.5× BKM
reduction of the reference configuration. Fifteen minutes, and you are
current with the whole program.

## Files

| File | Size | Role |
|---|---|---|
| [`preprint_v1.pdf`](preprint_v1.pdf) | ~120 KB | the circulating copy under the `v1` name (byte-identical to `v2`) |
| [`preprint_v2.pdf`](preprint_v2.pdf) | ~120 KB | the revision-stamped name — quote and cite this one |

The two files are **byte-identical twins** under different names, kept for
citation convenience; the revision-stamped name is the one the LaTeX source
([`src/preprint/preprint.tex`](../../src/preprint/README.md)) tracks.

## Reading path

1. Read the PDF end-to-end (linear structure, no prerequisites beyond
   basic PDE vocabulary);
2. open [`data/results/summary_numbers.json`](../../data/results/summary_numbers.json)
   in a parallel tab — every number in the text appears there with the
   command that produced it;
3. continue to the full paper
   ([`correction-b/`](../correction-b/README.md)) for the Kirchhoff
   derivation and the stress tests.

## Verification mapping

The preprint's claims map onto Section 2 of the
[verification framework](../../verification/README.md) (the regularity
chain) and Section 1 (the constant itself); the computational echo of
both is pinned in
[`data/results/baseline/`](../../data/results/baseline/README.md).

---

---

Navigation: [repository root](../README.md) · [papers](../README.md) · [src/preprint](../../src/preprint/README.md) · [IPL-RP-1.0](../../../LICENSE.md)

*Part of [wild8highlander/navier-stokes-b](https://github.com/wild8highlander/navier-stokes-b) - (c) 2026 Isaev Iskhak Khamzatovich, all rights reserved.*

