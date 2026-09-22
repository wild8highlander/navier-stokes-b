# `papers/correction-b/` — the Full NSE Regularity Paper

> **Navigation:** [`papers`](../README.md) › **`correction-b`**

![Format](https://img.shields.io/badge/Format-PDF-D0021B?style=flat-square&logo=adobeacrobatreader&logoColor=white) ![License](https://img.shields.io/badge/License-IPL--RP--1.0-red?style=flat-square)

The full journal-style article of the program: the derivation of
`b = 1/(4π + 2√3)` from the Kirchhoff point-vortex system, the polarization
twist and its Rodrigues form, the analytical proof of global regularity of
the 3D Navier–Stokes equations without artificial dissipation, and the
numerical stress tests that cross-reference the pinned protocols.

## Files

| File | Size | Role |
|---|---|---|
| [`main.pdf`](main.pdf) | ~2.3 MB | the circulating copy under the plain name (byte-identical to `main_v2`) |
| [`main_v2.pdf`](main_v2.pdf) | ~2.3 MB | the revision-stamped name — quote and cite this one |

## Reading path

1. Skim the introduction and the statement of the main theorem;
2. read the Kirchhoff derivation — where the constant comes from and why
   it is what it is;
3. read the regularity argument with
   [`verification/section2_preprint/`](../../verification/section2_preprint/README.md)
   open beside it — every estimate in the text is an assertion there;
4. finish with the numerical section and
   [`data/results/`](../../data/results/README.md).

## Source and traceability

The compilable LaTeX source is [`src/main/main_v2.tex`](../../src/main/README.md)
(the twin `main.pdf`/`main_v2.pdf` names resolve to the same bytes; the
source tracks the stamped name). Any wording can be diffed against the
source, and any number against the JSON protocols — the PDF is a
projection, not an authority.

---

---

Navigation: [repository root](../../README.md) · [papers](../README.md) · [src/main](../../src/main/README.md) · [IPL-RP-1.0](../../LICENSE.md)

*Part of [wild8highlander/navier-stokes-b](https://github.com/wild8highlander/navier-stokes-b) - (c) 2026 Isaev Iskhak Khamzatovich, all rights reserved.*

