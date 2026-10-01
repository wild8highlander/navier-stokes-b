# `papers/kdv/` — the KdV continuation: chapter 16 with the exact §16.29 edition

> **Navigation:** [repository root](../README.md) › [papers](../README.md) › **`kdv`**

![Chapter](https://img.shields.io/badge/Chapter-16_·_KdV--b-2B579A?style=flat-square)
![Languages](https://img.shields.io/badge/Editions-RU_·_EN-1284BA?style=flat-square)
![Formats](https://img.shields.io/badge/Formats-PDF_·_DOCX-2EA043?style=flat-square)
![Protocol](https://img.shields.io/badge/§16.29-11_WIN_·_1_DRAW_·_0_LOSS-2EA043?style=flat-square)
![License](https://img.shields.io/badge/License-IPL--RP--1.0-red?style=flat-square)

---

The second life of the constant: **the same polarization geometry that
regularizes the 3D Navier–Stokes equations reappears, verifiably, in the
Korteweg–de Vries equation.** Chapter 16 carries the b-correction over to
KdV soliton dynamics — the correction term, its conservation laws, the
soliton interactions, and the honest verdicts where the effect is below
the visibility threshold. If the b-geometry were an artifact of one
system, this chapter could not exist; the fact that the same angle
surfaces in an integrable system with exact solutions is the strongest
independent hint that it is a real geometric object.

## The editions (RU + EN, PDF + DOCX)

| File | Language | Format | Content |
|---|---|---|---|
| [`KdV_b_correction_Chapter16_RU.pdf`](KdV_b_correction_Chapter16_RU.pdf) | Russian | PDF | the full chapter 16, including **§16.29** (103 pages) |
| [`KdV_b_correction_Chapter16_RU.docx`](KdV_b_correction_Chapter16_RU.docx) | Russian | DOCX | identical content, editable |
| [`KdV_b_correction_Chapter16_EN.pdf`](KdV_b_correction_Chapter16_EN.pdf) | English | PDF | the English edition (92 pages) |
| [`KdV_b_correction_Chapter16_EN.docx`](KdV_b_correction_Chapter16_EN.docx) | English | DOCX | identical content, editable |

Backup copies of the previous editions are kept alongside in
[`docs/kdv/ru/`](../../docs/kdv/ru/README.md) and
[`docs/kdv/en/`](../../docs/kdv/en/README.md)
(`*_backup_before_exact_edition.docx`).

## What §16.29 adds — the exact-solver protocol

The 2026-10-01 edition appends section **16.29 — "Improved numerical
implementation: the exact Lax combination, the Hirota benchmark and
cross-language reproduction"**, driven by
[`kdv/kdv_improved.py`](kdv/README.md):

- the **exact Lax combination** for the I₃ invariant:
  `d/dt ∫u³ = −3∫u_x³`, `d/dt ∫u_x² = −6∫u_x³` — no more drift by
  discretization accident;
- the **exact N-soliton solutions of Hirota as benchmarks** — the
  two-soliton collision reproduced to `|u_num − u_Hirota|∞ = 4.9×10⁻⁸`;
- **2/3-spectrum dealiasing** of the nonlinearity (absent in the earlier
  chapter-16 numerics), controlling the aliasing error;
- an honest **DRAW** where the b-mechanism's nonlinear trace is at the
  `1 − cos θ_b ≈ 1.9×10⁻³` level — recorded as a draw, not spun as a win;
- the protocol verdict: **11 WIN · 1 DRAW · 0 LOSS** (table 16.13,
  figures 16.77–16.78 of the RU edition).

## The numbers, pinned

| Quantity | Value | Record |
|---|---|---|
| `E1` — solver vs exact one-soliton (T = 20) | `9.813×10⁻⁸` | lab L2 of the NSB-96 suite |
| `M1` (Hilbert) invariant drift under the b-mechanism | `2.932×10⁻⁹` | lab L2 |
| `M2` (Rodrigues) invariant drift | `2.886×10⁻⁹` | lab L2 |
| `M3` — nonlinear mechanism trace (honest draw) | `5.223×10⁻⁶` | lab L2 |
| `E5` — collision vs Hirota, phase shifts | `4.895×10⁻⁸` | lab L2 |
| `E6` — θ-scan phase-space norm identity | `1.110×10⁻¹⁶` | lab L2 |
| `E7` — spectral convergence (N ladder) | `2.9 → 1.2×10⁻⁸` | lab L2 |

The same battery re-runs inside the NSB-96 suite (lab **L2**, scoreboard
WIN 7 · DRAW 1 · LOSS 0) — see
[`research_col_smar/reports/NSB_LAB_REPORT.md`](../../research_col_smar/reports/NSB_LAB_REPORT.md).

## Layout of this directory

| Path | Role |
|---|---|
| `KdV_b_correction_Chapter16_{RU,EN}.pdf` | the typeset chapter (PDF) |
| `KdV_b_correction_Chapter16_{RU,EN}.docx` | the editable editions (DOCX) |
| [`kdv/`](kdv/README.md) | `kdv_improved.py` — the §16.29 numerical implementation (IFRK4 + dealiasing + Hirota benchmarks) |
| `README.md` | this document |

The DOCX masters with figures live in [`docs/kdv/ru/`](../../docs/kdv/ru/README.md)
and [`docs/kdv/en/`](../../docs/kdv/en/README.md); the LaTeX-level sources
of the main paper and preprint are under [`src/`](../../src/README.md).

## Reading path

1. The one-soliton facts (section 4 of the
   [verification framework](../../verification/section4_kdv/README.md)):
   `u''' − c u' + 6 u u' = 0`, `u_max = c/2`, width `∝ 1/√c`.
2. The b-correction in KdV: chapter 16, §§16.1–16.10.
3. The exact-solver protocol: §16.29 + [`kdv/`](kdv/README.md).
4. The independent re-check: lab L2 in the
   [NSB-96 report](../../research_col_smar/reports/NSB_LAB_REPORT.md).

## License

Part of **navier-stokes-b**, license IPL-RP-1.0 ([LICENSE.md](../LICENSE.md)).
