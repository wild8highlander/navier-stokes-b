# `data/results/baseline/` — Pinned Verdicts of the L1–L5 Verification Chain

> **Navigation:** [repository root](../../../README.md) › [`data`](../../README.md) › [`results`](../README.md) › **`baseline`**

![Chain](https://img.shields.io/badge/Chain-L1%E2%80%93L5-2EA043?style=flat-square)
![Pinned](https://img.shields.io/badge/Status-Regression_baseline-1284BA?style=flat-square)
![License](https://img.shields.io/badge/License-IPL--RP--1.0-red?style=flat-square)

Reference outputs of the five-level verification chain, recorded from the
executed run of
[`verification/python_levels/verify_all.py`](../../../verification/python_levels/README.md)
on **2026-09-16**. They serve two distinct purposes. First, they are the
source of the headline numbers quoted in the root README's results table —
L1–L4 residuals in the 10⁻¹⁶–10⁻¹⁴ range and the RK4 order 4.0008 of L3,
the 3D BKM integral of L5. Second, they are **regression baselines**: any
rerun of the chain on a fixed platform must land on these values to the
stated tolerances, which turns "the chain still holds" from an assertion
into a diff.

## The five levels, precisely

| File | Level | What is pinned | Expected rerun agreement |
|---|---|---|---|
| `l1_exact_constants.json` | **L1** | exact values of b, θ_b, cos θ_b, ln(1+b), the Klein closure Z = exp(b·β_K·L_min), C_s, φ, e — mpmath at 50 digits, plus float64 cross-checks of each | exact to string comparison at 50 digits; float64 errors ≤ 1.2×10⁻¹⁶ |
| `l2_rotation_algebra.json` | **L2** | the Rodrigues form `u′ = u∥ + √(1−b²)·u⊥ + b·(ω̂×u⊥)` against the rotation matrix: RᵀR = I, det R = 1, \|u′\| = \|u\|, spectrum {1, e^{±iθ_b}}, trace-angle identity | residuals ≤ 4.5×10⁻¹⁶ over 10⁵ vectors |
| `l3_kirchhoff_vortices.json` | **L3** | Kirchhoff point-vortex system: Hamiltonian drift → 0 as dt⁴, measured RK4 order 4.0008, isometry of the phase flow in the harmonic case, area preservation in the nonlinear case | order within [3.8, 4.2]; drifts as recorded per dt |
| `l4_nse_2d.json` | **L4** | 2D NSE: the exact identity ω′ = cos θ_b·ω, energy preservation under rotation, div u′ = −b·ω, the energy identity, the vorticity max principle, continuous rotation without injection | residuals ≤ 7.1×10⁻¹⁴; energy error 2.2×10⁻¹⁶; excess 0.0 |
| `l5_nse_3d_bkm.json` | **L5** | 3D Taylor–Green (N = 48, ν = 0.01, T = 6): BKM integral I_BKM = 9.3560 (true NSE) vs 9.6758 (continuous b-rotation), factor 0.96695, \|ΔE\| per rotation 1.4×10⁻⁹ | statistical identity of the protocol; large-run reproducibility |

## Reproduce

```bash
python3 verification/python_levels/verify_all.py        # ~20 min on 2 cores
NSE3D_SKIP=1  python3 verification/python_levels/verify_all.py   # L1–L4 only, ~1 min
NSE3D_SMALL=1 python3 verification/python_levels/verify_all.py   # L5 in control mode N=24, T=1
# then diff your outputs against the files in this directory
```

## Notes on honest interpretation

The historical "3.5× BKM reduction" headline refers to the under-resolved
N = 24 configuration of monograph chapter 11 and is *not* what the fixed
L5 protocol reproduces — the pinned run gives its own factors (1.032× on
the BKM integral, 1.014× on max‖ω‖∞ at N = 48), and
[`verification/python_levels/README.md`](../../../verification/python_levels/README.md)
documents this distinction openly. The chain's job is to make every
number's provenance unambiguous, including the ones that changed.

File integrity is pinned in [`MANIFEST.json`](../../../MANIFEST.json) and
re-checked by CI on every push.


## How the baselines are used by CI and the framework

The baselines are not decorative: they are the concrete values that the
[verification framework](../../../verification/README.md) must reproduce.
The Python chain writes fresh outputs to
[`verification/python_levels/results/`](../../../verification/python_levels/results/README.md)
on every run; diffing those against these pinned files is the regression
test. The Julia twin in
[`verification/julia_levels/`](../../../verification/julia_levels/README.md)
reproduces the same *qualitative* verdicts through an entirely independent
code path (own FFT, different L5 grid) — the independence claim is
deliberately not a bit-for-bit claim, and both chains' JSONs record enough
parameters to keep the distinction auditable.

## Tolerance policy

L1 is exact: the 50-digit strings must match character for character, and
the float64 cross-checks carry explicit per-value tolerances (of order
`10⁻¹⁶`). L2–L4 carry residual tolerances in the `10⁻¹⁶`–`10⁻¹⁴` band as
recorded inside each file. L5 is a fixed-protocol run: its verdict line
(factors, BKM integrals) must match; intermediate field statistics may
differ within the stored windows. If a rerun lands outside any window, the
[dispute protocol](../../../VERIFICATION.md) applies — reproduce, capture,
report.

---

Navigation: [results](../README.md) · [verification chain](../../../verification/README.md) · [summary numbers](../summary_numbers.json) · [IPL-RP-1.0](../../../LICENSE.md)

*Part of [wild8highlander/navier-stokes-b](https://github.com/wild8highlander/navier-stokes-b) — © 2026 Isaev Iskhak Khamzatovich, all rights reserved.*
