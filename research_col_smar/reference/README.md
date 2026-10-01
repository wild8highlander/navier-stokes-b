# `research_col_smar/reference/` — the pinned reference states and curves

> **Navigation:** [repository root](../../README.md) › [research_col_smar](../README.md) › **`reference`**

![Role](https://img.shields.io/badge/Role-pinned__references-2B579A?style=flat-square)
![Formats](https://img.shields.io/badge/Formats-NPZ_·_CSV_·_JSON_·_F64-2EA043?style=flat-square)
![License](https://img.shields.io/badge/License-IPL--RP--1.0-red?style=flat-square)

---

The **binary evidence layer** of the satellite program: the reference
fields, spectra, BKM curves and audit extracts that the reports quote and
the cross-checks compare against. These are not inputs the verifiers
*trust* — every analytic quantity is recomputed from closed forms — but
they are the *pinned states* a reproduction run can diff against, the
"same snapshot on your machine" guarantee.

## The files

| File | Size | Content |
|---|---|---|
| `ck96_state_t6.npz` | 21.7 MB | the full 96³ state at t = 6 of the A96 reference run (velocity, vorticity, spectra) — the reference state of the L11/L16 comparisons |
| `p5_snapshot_u.f64` | 2.7 MB | the raw float64 velocity snapshot (48³) of the P5 protocol — the L11 gradient-statistics input |
| `p5_snapshot_w.f64` | 2.7 MB | the raw float64 vorticity snapshot (48³), same time instant |
| `p5_spectra.npz` | 8.9 KB | the angle-averaged spectra of the P5 run (the `E(k)` curves of the monograph) |
| `p5_bkm.csv` | 43 KB | the BKM integral time series `I_BKM(t)` of the P5 protocol (true NSE vs b-rotation) |
| `p5_bkm_96.csv` | 25 KB | the same curve at 96³ (the `p5b` record) |
| `p5_certificate.csv` | 18 KB | the regularity-certificate columns of the P5 run (the LPS integrals, the exponential-tail fits) |
| `p5_bfamily.csv` | 742 B | the b-family summary (b ∈ {1, 1.25, 1.5, 2}: `k_max/η_b`, `k_d·η_b`, `x*(b)`, deviations) |
| `p5_regularity.json` | 4.2 KB | the regularity verdict record: per-b theory constants, measured cutoffs, relative deviations |
| `p5b_resolution_96.json` | 4.9 KB | the 96³ resolution record: the headline quantities of the doubled-resolution run |
| `phi_monograph_extract.txt` | 100 KB | the text extract of the φ-attractor monograph used by the L17 audit |
| `phi_monograph_structure.txt` | 4.9 KB | the structural map of the monograph (section → formulas → claims) used to plan the audit |

## How these are used

| Consumer | Uses |
|---|---|
| lab **L11** (gradient statistics) | `p5_snapshot_u.f64` (48³) vs the A96 state in `ck96_state_t6.npz` |
| lab **L12** (spectral flux) | the shell spectra inside `ck96_state_t6.npz` |
| lab **L16** (self-convergence) | `ck96_state_t6.npz` as the 96³ reference for the N and dt scans |
| lab **L17** (φ-audit) | the two `phi_monograph_*` extracts |
| the monograph's chapter 15 | `p5_bkm.csv` / `p5_bkm_96.csv` / `p5_certificate.csv` (figures 11–14) |
| [`verification/repo_integrity/`](../../verification/repo_integrity/README.md) | the presence and non-triviality of the JSON/CSV records (group E) |

## Provenance and integrity

Every file here was produced by a tool in
[`tools/`](../tools/README.md) with a fixed seed and is mirrored in the
results manifests of [`results/`](../results/README.md); the tree-level
sha256 ledger is [`MANIFEST.json`](../../MANIFEST.json), checked by CI on
every push. The raw per-run records (JSON verdicts, verdict CSVs) live in
[`results/results/`](results/results/README.md) — this directory holds
the heavier *states and curves*, that one the lighter *verdicts*.

## License

Part of **navier-stokes-b**, license IPL-RP-1.0 ([LICENSE.md](../../LICENSE.md)).
