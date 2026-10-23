# `assets/charts/` — The Dark-Theme Chart Set

> **Navigation:** [repository root](../../README.md) › [assets](../README.md) › **`charts`**

![Role](https://img.shields.io/badge/Role-Chart_set-00E5FF?style=flat-square)
![Format](https://img.shields.io/badge/Format-PNG_·_200_dpi-1284BA?style=flat-square)
![License](https://img.shields.io/badge/License-IPL--RP--1.0-red?style=flat-square)

Fourteen publication-grade summary charts drawn in the repository's visual
language (deep navy `#0A0E1A`, cyan `#00E5FF`, amber `#F59E0B`, violet
`#A855F7`). Every number plotted here is quoted verbatim from the pinned
protocols — `data/results/`, the NSB-96 lab records and the section
verifiers — so the charts are a visual index of the evidence layer, not a
separate source of truth. Where a curve is schematic (the spectral slope
guides, the L16 fit line), the caption says so explicitly.

## Contents

| Chart | Shows |
|---|---|
| `chart_scoreboard.png` | the NSB-96 scoreboard: per-lab stacked verdicts + the 67 / 7 / 2 aggregate donut |
| `chart_verification_matrix.png` | 11 languages × 7 sections coverage with the tier colour code |
| `chart_residuals.png` | headline residuals of the executed program, log scale |
| `chart_b_digits.png` | the constant `b` at full printed precision, digit by digit |
| `chart_spectrum.png` | the energy cascade with k⁻⁵/³ and k⁻³ slope guides |
| `chart_master_relation.png` | the Smagorinsky–Kolmogorov master relation and the Lilly point |
| `chart_convergence.png` | L4 48³→96³ convergence + the L16 exponential fit |
| `chart_kdv_family.png` | the hyperdissipative KdV family: cutoff law + mass conservation |
| `chart_open_problems.png` | P1–P7 outcomes: strict bounds vs measured effects vs ledger |
| `chart_timeline.png` | the three program milestones |
| `chart_energy_neutrality.png` | energy non-conservation per event across all protocols |
| `chart_universality.png` | P6: θ_b universality across five geometries |
| `chart_ci_pipeline.png` | the CI gates and their typical wall-clock |
| `chart_social_preview.png` | the abstract chaos→order social card (also used as `assets/social-preview.png`) |

## Regeneration

The charts are deterministic matplotlib renders (fixed data quoted from the
pinned JSON protocols). To regenerate or restyle them, re-run the rendering
script with any matplotlib ≥ 3.8 — no network access, no datasets beyond the
quoted constants are needed.
