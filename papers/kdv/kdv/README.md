# `papers/kdv/kdv/` — `kdv_improved.py`, the §16.29 numerical implementation

> **Navigation:** [repository root](../../README.md) › [papers](../../papers/README.md) › [kdv](../README.md) › **`kdv/`**

![Solver](https://img.shields.io/badge/Solver-IFRK4_·_Fornberg--Whitham-2B579A?style=flat-square)
![Dealias](https://img.shields.io/badge/Dealiasing-2%2F3--rule-2EA043?style=flat-square)
![Benchmarks](https://img.shields.io/badge/Benchmark-Hirota__exact-FF8C00?style=flat-square)
![License](https://img.shields.io/badge/License-IPL--RP--1.0-red?style=flat-square)

---

This directory contains the **numerical workhorse of §16.29**:
`kdv_improved.py` (484 lines, documented, deterministic) — the improved
KdV complex of the NSB-96-UPGRADE package. It implements and improves the
numerical part of chapter 16: a pseudo-spectral integrating-factor RK4
solver with 2/3-spectrum dealiasing, full Lax-invariant tracking, the
exact N-soliton Hirota solutions as benchmarks, an extended equation
family, and WIN/DRAW/LOSS verdicts with JSON/CSV/MD reports.

## What it improves over the chapter-16 baseline

| # | Improvement | Why it matters |
|---|---|---|
| 1 | **2/3-dealiasing of the nonlinearity** | the baseline chapter numerics did not control aliasing; the rule zeroes the top third of the spectrum after every nonlinear evaluation, making the invariant drifts honest |
| 2 | **exact Lax combination for I₃** | `I₃ = ∫(u³ − ½u_x²)dx` is conserved by the *combination* `d/dt∫u³ = −3∫u_x³`, `d/dt∫u_x² = −6∫u_x³`; implementing the combination (not the terms separately) removes the discretization drift |
| 3 | **exact two-soliton benchmark (phase shifts)** | the collision is compared against the closed-form Hirota solution, not merely against itself; phase-shift agreement `4.9×10⁻⁸` |
| 4 | **extended family: KdV, mKdV, BBM, Kawahara** | one solver, four dispersive equations (§16.23), so the b-family is not tuned to one equation |
| 5 | **WIN/DRAW/LOSS verdicts with configurable thresholds** | the honesty rule of the parent program, imported verbatim |
| 6 | **reproducibility (seed) + JSON/CSV/MD reports + 600 dpi figures** | every run regenerates its own evidence |

## The solver in one table

| Component | Choice |
|---|---|
| discretization | Fourier pseudo-spectral on a periodic line |
| time stepping | integrating-factor RK4 (Fornberg–Whitham style) |
| anti-aliasing | 2/3 rule after every nonlinear evaluation |
| invariants | I₁ = ∫u dx, I₂ = ∫u² dx, I₃ = ∫(u³ − ½u_x²)dx (exact combination) |
| benchmarks | exact 1-soliton, exact N-soliton (Hirota `u = 2 ∂²ₓ ln F`) |
| equation family | `kdv`, `mkdv`, `bbm`, `kawahara` |
| outputs | `results/kdv_improved.json`, `results/kdv_improved_verdicts.csv`, figures at 600 dpi |

## Run

```bash
python3 papers/kdv/kdv/kdv_improved.py            # full battery
python3 papers/kdv/kdv/kdv_improved.py --quick    # smoke configuration
python3 papers/kdv/kdv/kdv_improved.py --dpi 600  # publication figures
```

Deterministic (fixed seed), idempotent; outputs land in the package's
`results/` and `figures/` directories and mirror the pinned records in
[`research_col_smar/results/results/`](../../../research_col_smar/reference/README.md).

## The recorded verdicts (lab L2 of the NSB-96 suite)

| Test | Value | Verdict |
|---|---|---|
| `E1` — `\|u_num − u_exact\|∞` at T = 20 | `9.813×10⁻⁸` | WIN |
| `M1` — Hilbert-form b-mechanism invariant drift | `2.932×10⁻⁹` | WIN |
| `M2` — Rodrigues-form b-mechanism invariant drift | `2.886×10⁻⁹` | WIN |
| `M3` — nonlinear mechanism trace | `5.223×10⁻⁶` | **DRAW** (honest) |
| `E5` — collision vs Hirota (phase shifts) | `4.895×10⁻⁸` | WIN |
| `E6` — θ-scan phase-space norm identity | `1.110×10⁻¹⁶` | WIN |
| `E7` — spectral convergence over the N ladder | `2.9 → 1.2×10⁻⁸` | WIN |

**Scoreboard: WIN 7 · DRAW 1 · LOSS 0** — one line of the NSB-96
aggregate (see [`research_col_smar/reports/NSB_LAB_REPORT.md`](../../../research_col_smar/reports/NSB_LAB_REPORT.md)).

## See it move

The repository ships the collision as an animation:
[`assets/animations/anim_kdv_collision.gif`](../../../assets/animations/README.md)
— the exact Hirota two-soliton interaction, rendered from the same
closed form this solver benchmarks against.

## License

Part of **navier-stokes-b**, license IPL-RP-1.0 ([LICENSE.md](../../LICENSE.md)).
