# `python_levels/` — the L1–L5 Verification Chain (Python Reference)

> **Navigation:** [`verification`](../README.md) › **`python_levels`**

![Chain](https://img.shields.io/badge/Chain-L1%E2%80%93L5-2EA043?style=flat-square)
![Python](https://img.shields.io/badge/Python-3.11%2B-3776AB?style=flat-square&logo=python&logoColor=white)
![Precision](https://img.shields.io/badge/mpmath-50_digits-1284BA?style=flat-square)
![License](https://img.shields.io/badge/License-IPL--RP--1.0-red?style=flat-square)

The independent multi-level verification chain of the b-correction program,
in Python. Every check recomputes everything from scratch on every run;
results are written to [`results/`](results/README.md) as honest JSON —
no hand-edited numbers. This is the reference implementation of the
L1–L5 chain that the Julia twin in
[`julia_levels/`](../julia_levels/README.md) independently re-derives and
that the pinned baselines in
[`data/results/baseline/`](../../data/results/baseline/README.md)
freeze for regression testing.

## The five levels

| Level | What it verifies | Time |
|---|---|---|
| **L1** | constants from closed formulas (mpmath, 50 digits): b in two forms, `sin θ_b = b` exactly, cos θ_b, ln(1+b), the Klein closure Z = exp(b·β_K·L_min), C_s (Lilly), φ, e — plus a float64 cross-check of every quantity | ~1 s |
| **L2** | rotation algebra: the exact form `u′ = u∥ + √(1−b²)·u⊥ + b·(ω̂×u⊥)` equals the Rodrigues rotation at θ_b; RᵀR = I over 10⁵ vectors; det R = 1; \|u′\| = \|u\|; spectrum {1, e^{±iθ_b}} | ~10 s |
| **L3** | Kirchhoff point vortices: Hamiltonicity (H-drift → 0 as dt⁴), measured RK4 order 4.0008, isometry of the phase flow, area preservation | ~30 s |
| **L4** | 2D NSE: the identity `ω′ = cos θ_b·ω` exactly; energy preserved under rotation; `div u′ = −b·ω`; the energy identity; the vorticity max principle; continuous rotation without energy injection | 2–5 min |
| **L5** | 3D Taylor–Green N = 48, ν = 0.01, T = 6: the BKM integral and max‖ω‖∞ for true NSE vs the continuous b-rotation; \|ΔE\| per rotation | 10–20 min |

## How to run

```bash
python3 verify_all.py                 # everything
NSE3D_SKIP=1  python3 verify_all.py   # without L5 (~1 minute)
NSE3D_SMALL=1 python3 verify_all.py   # L5 in control mode N=24, T=1
```

Dependencies: `numpy` and `mpmath` (required); `sympy` optional (the
symbolic proof that the two closed forms of b are identical). Each run
overwrites its own JSON in [`results/`](results/README.md) — the pinned
copies in [`data/results/baseline/`](../../data/results/baseline/README.md)
are the regression baselines to diff against.

## The L5 protocol, precisely

Taylor–Green in T³, 2/3-dealiasing, RK4, dt = 0.004, T = 6. Continuous
rotation: angle per step φ = dt·θ_b (cumulative θ_b·T ≈ 21.459°), axis
ω̂ = ω/‖ω‖, vorticity recomputed from the rotated velocity, Leray
projection. Recorded verdict: `I_BKM` = 9.3560 (NSE) vs 9.6758 (b-rotation),
factor 0.96695, \|ΔE\| per rotation 1.4×10⁻⁹.

**On the historical 3.5× figure — an honesty note.** The 3.5× headline
belongs to the under-resolved N = 24 configuration of monograph chapter 11
and is deliberately *not* reproduced by this fixed protocol: the pinned
N = 48 run gives its own factors (1.032× on the BKM integral, 1.014× on
max‖ω‖∞, \|ΔE\| ≤ 5.1×10⁻⁵). The chain's contract is that every number's
provenance is unambiguous — including the numbers that changed between
configurations. Both configurations' parameters are recorded in the JSONs.

## Relationship to the rest of the framework

L1–L4 feed the physics runs in [`code/`](../../code/README.md) (the P2/P3
b-rotation mode *is* the L4 identity applied per time step); L5 is the 3D
bridge the open-problems program builds on (P1's residual-motion band is
k ≤ N/6 of this protocol). The six per-section Python ports in
[`section1_correction_b/ … section6_riemann_zeros/`](../README.md) are a
different, contract-based decomposition of the same mathematics — the L
chain is the physics-first view, the sections are the claim-first view;
the validator in [`tests/`](../tests/README.md) keeps both honest.


## The L-chain's parameter tables, condensed

| Level | Key parameters | Sensitivity notes |
|---|---|---|
| L1 | none (closed forms) | exact at 50 digits; float64 echoes carry `10⁻¹⁶`-class tolerances |
| L2 | 10⁵ random vectors, fixed seed | residuals scale with vector count; seed is part of the protocol |
| L3 | dt ∈ {0.1, 0.05, 0.025}, harmonic + nonlinear cases | RK4 order measured in the truncation regime; H-drift must fall as dt⁴ |
| L4 | 200 velocity fields, 2/3-dealiased N-grid | identity residuals `10⁻¹⁴`-class; energy check is exactness-level |
| L5 | N = 48, ν = 0.01, dt = 0.004, T = 6 | the expensive level; NSE3D_SMALL runs a control-mode N = 24, T = 1 |

## Reading the JSON outputs

Each level writes its own JSON with the same envelope as the physics runs
(command, parameters, values, tolerances, timestamp). The float64
cross-check block in L1 records both the 50-digit string and the double
echo, which is the cheapest possible demonstration of where double
precision stops being enough — one of the reasons the formal tier works
over exact reals instead.

## When to run which chain

| You want… | Run |
|---|---|
| the fastest honest smoke | `NSE3D_SKIP=1 python3 verify_all.py` (~1 min) |
| the full reference chain | `python3 verify_all.py` (~20 min) |
| an independent-implementation check | [`julia_levels/verify_all.jl`](../julia_levels/README.md) |
| the per-claim contract matrix | `make verify-all` (the six sections) |

---

Navigation: [verification](../README.md) · [results](results/README.md) · [julia twin](../julia_levels/README.md) · [baselines](../../data/results/baseline/README.md) · [IPL-RP-1.0](../../LICENSE.md)

*Part of [wild8highlander/navier-stokes-b](https://github.com/wild8highlander/navier-stokes-b) — © 2026 Isaev Iskhak Khamzatovich, all rights reserved.*
