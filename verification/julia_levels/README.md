# `julia_levels/` — the L1–L5 Verification Chain (Independent Julia Twin)

> **Navigation:** [`verification`](../README.md) › **`julia_levels`**

![Julia](https://img.shields.io/badge/Julia-stdlib_only-9558B2?style=flat-square&logo=julia&logoColor=white)
![Chain](https://img.shields.io/badge/Chain-L1%E2%80%93L5-2EA043?style=flat-square)
![Independence](https://img.shields.io/badge/Implementation-fully_independent-FF8C00?style=flat-square)
![License](https://img.shields.io/badge/License-IPL--RP--1.0-red?style=flat-square)

A **completely independent implementation** of the L1–L5 verification
chain in pure stdlib Julia — nothing to install: no FFTW, no JSON package,
no external dependencies of any kind. Where the Python chain in
[`python_levels/`](../python_levels/README.md) is the reference, this is
the independence check: a second implementation in a second language, a
second numeric stack and (deliberately) a slightly different L5 grid.

## What each level does here

| Level | Implementation notes |
|---|---|
| **L1** | BigFloat (120-bit) evaluation of the closed forms against the 50-digit string references: b, θ_b, cos θ_b, ln(1+b), the Klein closure, C_s, φ, e |
| **L2** | rotation algebra over 1000 vectors × 200 axes with its **own** Rodrigues matrix construction |
| **L3** | Kirchhoff point vortices: RK4 order, isometry, area preservation |
| **L4** | 2D NSE with an **own radix-2 FFT self-tested against a direct DFT**, 2/3 rule with 2N padding, the identity ω′ = cos θ_b·ω, energy accounting |
| **L5** | 3D Taylor–Green at **N = 32**: BKM integral, continuous b-rotation (smoothed axis band k ≤ N/6, quadratic weight), 2N padding |

## How to run

```bash
julia verify_all.jl                 # everything; L5 ≈ 5–15 min
NSE3D_SKIP=1  julia verify_all.jl   # without L5 (~1 minute)
NSE3D_SMALL=1 julia verify_all.jl   # L5 in control mode
```

Each run writes its results to `results/*.json` (per-run protocols,
overwritten in place — same contract as the Python chain).

## Why the different N — and why that is the point

The Julia L5 uses **N = 32** (its own radix-2 FFT requires powers of two)
while the Python L5 uses **N = 48**. This is documented honestly and
deliberately: the two chains are **two independent benchmarks, not one
task on two languages**. Cross-language equality claims are reserved for
the six contract sections (where the
[`validator`](../tests/README.md) diffs JSON verdicts to tolerance);
the L chains instead make an independence claim — same mathematics,
same qualitative verdicts (the b-rotation reduces the BKM integral and
injects no energy), computed through entirely different code paths. The
constants of L1–L4, which *are* directly comparable, are reconciled
bit-for-bit by the comparison script (`scripts/compare_python_julia.py`
in the author's toolchain) against the string references.

## Relationship to the rest of the framework

The Julia chain is the strongest answer to "what if numpy is wrong?":
every numerical primitive used by the Python chain (FFT, interpolation,
special functions) is re-implemented here from the standard library, and
the qualitative conclusions reproduce. For the per-claim, per-language
matrix — including formal proofs — see the
[framework hub](../README.md); for the pinned regression baselines, see
[`data/results/baseline/`](../../data/results/baseline/README.md).


## The self-tested FFT, precisely

L4 and L5 need spectra; instead of importing FFTW, the Julia chain ships a
radix-2 FFT whose first act is to **test itself against a direct DFT** on
the run's grid — the test runs every time, before the physics, and aborts
on disagreement. This is the microcosm of the whole framework's
philosophy: the dependency is not trusted, it is *checked*, every run.

## 2N padding and the dealiasing contract

Both chains use 2/3-rule dealiasing; the Julia chain pads to 2N (its FFT
requires powers of two) while the Python chain truncates to 2/3. The two
routes are spectrally equivalent for the recorded diagnostics, and the
JSONs record which route was taken — an honest difference, not a hidden
one.

## Reconciling the two chains

| Quantity | Comparable across chains? | How |
|---|---|---|
| L1 constants | yes, exactly | the 50-digit string references |
| L2–L4 residuals | yes, qualitatively | same identities, same tolerance bands |
| L5 verdicts | qualitatively | different grids (N = 32 vs N = 48): factors differ, the direction and energy-neutrality must agree |
| timing | no | different runtimes by design — not a benchmark pair |

If a rerun of either chain disagrees with its own pinned baselines in
[`data/results/baseline/`](../../data/results/baseline/README.md) beyond
the recorded tolerances, the dispute protocol in
[`VERIFICATION.md`](../../VERIFICATION.md) applies.

---

Navigation: [verification](../README.md) · [python reference](../python_levels/README.md) · [baselines](../../data/results/baseline/README.md) · [IPL-RP-1.0](../../LICENSE.md)

*Part of [wild8highlander/navier-stokes-b](https://github.com/wild8highlander/navier-stokes-b) — © 2026 Isaev Iskhak Khamzatovich, all rights reserved.*
