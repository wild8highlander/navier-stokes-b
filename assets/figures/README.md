# `assets/figures/` — the academic figure set

> **Navigation:** [repository root](../README.md) › [assets](../README.md) › **`figures`**

![Count](https://img.shields.io/badge/Figures-11_%40_300dpi-2EA043?style=flat-square)
![Source](https://img.shields.io/badge/Source-pinned__protocols-2B579A?style=flat-square)
![License](https://img.shields.io/badge/License-IPL--RP--1.0-red?style=flat-square)

---

This directory is the **referenced figure set** of the repository's
documentation layer: every figure below is embedded in a README
(`README.md`, the verification hub, the satellite READMEs) and every
number it displays is taken verbatim from a pinned protocol —
`data/results/*.json`, `data/results/summary_numbers.json`, or the
NSB-96 reports in `research_col_smar/reports/`. Nothing here is an
artist's impression.

| Figure | Shows | Numbers come from |
|---|---|---|
| [`fig_b_anatomy.png`](fig_b_anatomy.png) | the anatomy of `b = 1/(4π + 2√3)` — the two geometric readings of the denominator — and the angle `θ_b = 3.5765013°` on the unit circle | `summary_numbers.json` |
| [`fig_rodrigues_rotation.png`](fig_rodrigues_rotation.png) | the Rodrigues decomposition (`u∥`, `√(1−b²)·u⊥`, `b·(ω̂×u⊥)`), the rotation plane, the Leray absorption of the gradient part, and the energy-neutrality box | L2/L4/L5 |
| [`fig_headline_results.png`](fig_headline_results.png) | the headline residuals of the executed program at log scale — from machine-zero identities to strict bounds | P1–P6, L2, L4 |
| [`fig_labs_scoreboard.png`](fig_labs_scoreboard.png) | the NSB-96 scoreboard: thirteen laboratories, stacked WIN/DRAW/LOSS bars, aggregate **67 · 7 · 2** | `NSB_LAB_REPORT.md`, `EXTRA_RESEARCH_REPORT.md` |
| [`fig_master_relation.png`](fig_master_relation.png) | the master relation `C_s = 1/(π(3C_K/2)^{3/4})` over `C_K ∈ [1.2, 1.8]` with the program point and the Lilly point; the exact −3/4 log-derivative panel | `research_col_smar` P1–P4 |
| [`fig_verification_matrix.png`](fig_verification_matrix.png) | the language × section coverage matrix of the eleven-language framework, including the new Section 7 | `verification/` |
| [`fig_program_timeline.png`](fig_program_timeline.png) | the four milestones: v1.0.0 import → modernization → NSB-96 → the KdV exact edition | git history |
| [`fig_kdv_bfamily.png`](fig_kdv_bfamily.png) | the hyperdissipative KdV family (L13): theory cutoff `k_ν(b) = (1/νT)^{1/2b}` vs measured `k_e`; exact mass conservation for every b | extra13 records |
| [`fig_convergence_l16.png`](fig_convergence_l16.png) | the L16 self-convergence scans (N = 24…72 vs the 96³ reference) with the exponential fit `err ∝ e^{−0.183·N}` | extra16 records |
| [`fig_p6_universality.png`](fig_p6_universality.png) | the P6 universality of `θ_b` across five geometries (200 000 vectors each, seed 11) — worst residual `9.5×10⁻¹⁵` | `p6_b_universality.json` |
| [`fig_bkm_protocol.png`](fig_bkm_protocol.png) | the L5 BKM protocol (`I_BKM` 9.3560 vs 9.6758), the three energy-neutrality protocols, and the 48³↔96³ agreement of the headline quantities | `l5` baseline, `main96` record |

## Usage notes

- All figures are 300 dpi PNG on a white background — print-ready and
  dark-mode-safe (GitHub shows them on a white card).
- The set is referenced from the root README's gallery (§13) and from the
  topical sections; the canonical alt-text lives there.
- The animations (GIF) live next door in
  [`assets/animations/`](../animations/README.md).
- Related (older) publication plots of the P1–P6 physics chain are in
  [`data/plots/`](../../data/plots/README.md); the satellite's own
  figure families (RU/EN editions) are in
  [`research_col_smar/figures/`](../../research_col_smar/figures/README.md).

## License

Part of **navier-stokes-b**, license IPL-RP-1.0 ([LICENSE.md](../../LICENSE.md)).
