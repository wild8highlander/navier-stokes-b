# `code/` — The Physics Runs P1–P6 and the Core Libraries

> **Navigation:** [repository root](../README.md) › **`code`**

![Runs](https://img.shields.io/badge/Runs-P1%E2%80%93P6-2EA043?style=flat-square)
![Python](https://img.shields.io/badge/Python-3.11%2B-3776AB?style=flat-square&logo=python&logoColor=white)
![License](https://img.shields.io/badge/License-IPL--RP--1.0-red?style=flat-square)

Executable Python programs of the b-correction program. Every run writes a
JSON protocol to [`data/results/`](../data/results/README.md) and its final
figures to [`data/plots/`](../data/plots/README.md). **Every number quoted in
the root README comes from these programs** — nothing in the documentation is
hand-written, and every protocol JSON stores the command, parameters,
tolerances and wall-clock time of its run, so any figure can be traced back to
the exact process that produced it.

The programs share a deliberate design philosophy. Each one is
**deterministic** (fixed seeds — P1 uses `seed = 42`, P4 uses seeds 1–4 for
its ensemble members), **idempotent** (rerunning overwrites its own protocol
in place, never accumulating state), and **self-auditing** (each script
prints its pre-registered success criteria and marks each one
achieved/failed before writing the JSON). A run that cannot reproduce its
pinned values on a fixed platform is treated as a bug, not as physics.

## Contents

| File | Role | Key output |
|---|---|---|
| [`tg2d_core.py`](tg2d_core.py) | shared 2D thermogasdynamics core: Fourier×Chebyshev grid, CFL guard, AB2 advection, hyperviscosity, b-rotation operator (Rodrigues + Leray projection) | — |
| [`chamber3d.py`](chamber3d.py) | 3D Wilson-chamber geometry used by P1/P5: adiabatic expansion, Magnus supersaturation, 64³ grid, ion-track seeding, trilinear advection | — |
| [`p1_3d_microphysics.py`](p1_3d_microphysics.py) | **P1** — droplet microphysics vs analytics; energy-injection audit of the b-rotation | `data/results/p1_3d_microphysics.json`, `p1_positions.npz` |
| [`p2_grid_convergence.py`](p2_grid_convergence.py) | **P2** — grid & time-step convergence; RK4 order measurement; factor-F stability across N and Re | `data/results/p2_grid_convergence.json` |
| [`p3_buoyancy.py`](p3_buoyancy.py) | **P3** — Rayleigh–Bénard buoyancy at Gr = 10⁶ (ψ–ω formulation, free-slip, 72×144, AB2+Euler, 4th-order hyperviscosity) | `data/results/p3_buoyancy.json`, `p3_theta_snapshot.npy` |
| [`p4_ensemble_sigma_y.py`](p4_ensemble_sigma_y.py) | **P4** — ensemble spread σ_y at Re = 2000 (T = 4 realizations, 2000 RK2 tracers each) | `data/results/p4_ensemble_sigma_y.json` |
| [`p5_droplet_feedback.py`](p5_droplet_feedback.py) | **P5** — two-way droplet–flow feedback: vapor sink ṁ = 4πR·D_v·ρ_vs·(S−1) with conservative spectral diffusion + Stokes reaction on the gas | `data/results/p5_droplet_feedback.json` |
| [`p6_b_universality.py`](p6_b_universality.py) | **P6** — universality of θ_b on R², T², S², H², R³ (200 000 random points/fields per geometry) | `data/results/p6_b_universality.json` |
| [`make_plots.py`](make_plots.py) | regenerates the five 300-dpi plots **from the JSON protocols** (never from memory) | `data/plots/*.png` |
| [`run_all.sh`](run_all.sh) | runs the full chain P1 → P6 + plots, sequentially, with per-stage timing | — |

## Usage

```bash
# full chain (sequential; P3 takes ~15 min on 2 cores, whole chain ~40 min)
./run_all.sh

# a single run
python3 p2_grid_convergence.py

# regenerate plots only (requires data/results/*.json to exist)
python3 make_plots.py
```

Every script is runnable standalone with no arguments; parameters are fixed
constants in the file header (deliberately — the values are *the registered
protocol*, not knobs). To vary a parameter you are expected to copy the
script and register a new protocol, not to edit the pinned one.

## Requirements

Python **3.11+** (reference environment: 3.12) with `numpy`, `scipy`,
`matplotlib`, `mpmath` — see [`environment.yml`](../environment.yml) or run
`make install` at the repository root. All heavy loops are vectorized with
numpy; a modern laptop runs the full chain in tens of minutes and the P6
universality sweep (a million Rodrigues rotations) in under a minute.

## The runs at a glance

| Run | Physical setting | Registered headline criterion | Recorded outcome |
|---|---|---|---|
| **P1** | Wilson chamber in native 3D: adiabatic expansion (γ = 1.4, V₁/V₀ = 1.25) → supersaturation S₀ = 4.2135 → ion track (56 nodes) → droplet growth → Stokes sedimentation | growth error ≤ 1 %; signed energy injection ≤ 10⁻¹² | **1.5×10⁻¹⁶**; **exactly 0.00e+00** |
| **P2** | Taylor–Green 2D, N ∈ {32, 64, 128}, Re = 400/800/1600 | RK4 order ∈ [3.8, 4.2]; \|F(128) − F(64)\| < 0.01 | **3.743** (truncation regime); **3.3×10⁻¹⁶** |
| **P3** | Rayleigh–Bénard at Gr = Ra/Pr = 10⁶, free-slip, 72×144 | Nu > 1.5; CFL < 0.45 | **Nu = 19.64**; **CFL = 0.246** |
| **P4** | decaying 2D turbulence, E(k) ∝ k³·exp(−(k/k_p)²), T = 4 ensemble | visibility \|Δσ_y\| > 2s, else a bound | **9.3×10⁻⁷** ≪ 2s/σ_y = 4.8 % → strict bound |
| **P5** | P1 + active droplets (vapor sink + sedimentation reaction) | S_min < 3.893; vapor balance ≤ 5 % | **S_min = 3.8746**; **0.75 %** |
| **P6** | Rodrigues rotation at θ_b on five geometries, 200 000 samples each | max\|angle − θ_b\| ≤ 10⁻¹² | **9.5×10⁻¹⁵** |

## Verification contract

Each program is idempotent and deterministic on a fixed platform: rerunning
it must reproduce the pinned values in
[`data/results/`](../data/results/README.md) up to the stated tolerances.
If a value differs, treat it as a bug and file a
[verification request](https://github.com/wild8highlander/navier-stokes-b/issues/new?template=verification_request.yml)
— reproduction failures are triaged as high-priority. The JSON protocols are
**immutable evidence**: their sha256 is pinned in
[`MANIFEST.json`](../MANIFEST.json) and re-checked by CI, and regenerating
them is allowed only together with a re-run and a matching documentation
update in the same change.

## Relationship to the rest of the repository

The physics runs consume the closed-form constant and the rotation operator
that the verification framework asserts independently:
[`verification/python_levels/`](../verification/python_levels/README.md)
re-derives the L1–L5 chain these runs rest on; the L4 identity
`ω′ = cos(dt·θ_b)·ω` is exactly what P2 and P3 exercise through the
`b_rotation` mode; and the open-problems appendices in
[`monograph/open-problems/`](../monograph/README.md) quote these protocols
as their evidence base. When you change anything here, the intended workflow
is: rerun, let the JSONs and plots regenerate, then update the documentation
tables **in the same commit** and refresh the manifest (`make manifest`).

## Numerical methods, per run

The runs share a small, deliberately boring numerical toolkit — the
interesting part is the physics protocol, not solver exotica. All spatial
discretisations are spectral or finite-difference on uniform grids; time
stepping is explicit; the rotation operator is applied per step through
the same Rodrigues + Leray path that the verification framework proves
properties of.

**`tg2d_core.py`** — the 2D thermogasdynamics core used by P2/P3/P4.
Fourier in x, Chebyshev (or finite-difference) in z; 2/3 dealiasing;
AB2 for advection and buoyancy, Euler for diffusion (AB2 weights are
unstable on stiff diffusion when `ν·k²_max·dt·1.5 > 1` — a lesson recorded
in the P3 protocol); fourth-order hyperviscosity against aliasing; Thomas
tridiagonal solves for the stream function; the CFL guard aborts the run
rather than silently exceeding the threshold.

**`chamber3d.py`** — the Wilson-chamber geometry for P1/P5. Adiabatic
expansion with γ = 1.4 and expansion ratio V₁/V₀ = 1.25; supersaturation
from the Magnus formula (S₀ = 4.2135 in the registered protocol); a 64³
grid over a 10 cm domain with a 56-node ion track; droplet growth by the
exact analytic form `d(R²)/dt = 2α_g(S−1)`; Stokes sedimentation;
trilinearly interpolated field advection; a neutral condensation threshold
that stays unreached so the background remains clean.

**The rotation operator** (shared): at every step the velocity field is
rotated by `φ = dt·θ_b` about the local vorticity axis — Rodrigues form,
Leray projection absorbing the gradient part, vorticity recomputed from
the rotated velocity. The signed energy-injection audit runs on every
step of every run; the recorded value is exactly zero (the |ΔE| values
in the protocols are the *symmetric* rotation cost, not injection).

## Output schema

Every `data/results/p*.json` protocol carries the same envelope, which is
what makes the layer machine-checkable:

| Field | Meaning |
|---|---|
| `command` | the exact producing command line |
| `parameters` | the full parameter set of the run (grid, seeds, ν, dt, …) |
| `criteria` | the pre-registered success criteria with thresholds and achieved/failed marks |
| `values` | the recorded numbers quoted by the documentation |
| `tolerances` | the agreement windows a rerun must satisfy |
| `wall_time_s` | the wall-clock time of the recorded run |
| `timestamp` | when the run was executed |

`summary_numbers.json` mirrors every `values` block into one file with the
50-digit constants of the L-chain — it is the single file to open when
checking any quoted number.

## Troubleshooting

| Symptom | Cause | Fix |
|---|---|---|
| `CFL guard triggered` in P3 | dt too large for the resolution | keep the registered dt = 0.05-window; the protocol value CFL = 0.246 has margin |
| P4 ensemble spread looks seeded-wrong | seeds overridden by environment | the ensemble uses seeds 1–4; do not set numpy global seeds before the run |
| P6 slow (> 5 min) | BLAS threading oversubscribed | `OMP_NUM_THREADS=2 python3 p6_b_universality.py` |
| plots differ from the repo PNGs | matplotlib version drift | regenerate with the pinned environment (`environment.yml`); the JSONs, not the PNGs, are authoritative |
| P1 returns instantly with old JSON | reading the protocol instead of running | the script *overwrites* its JSON; check the `timestamp` field |

## Reproduction workflow, end to end

1. `python3 code/p2_grid_convergence.py` — the fastest full-fidelity run
   (minutes); diff your `data/results/p2_grid_convergence.json` against
   the pinned one (they should match to the stored tolerances);
2. `NSE3D_SKIP=1 python3 verification/python_levels/verify_all.py` — the
   L1–L4 chain in about a minute;
3. `cd code && ./run_all.sh` — the whole program (~40 min);
4. `python3 code/make_plots.py` — regenerate the figures from your JSONs;
5. `make verify-manifest` — confirm the tree (your regenerated evidence
   will legitimately differ; that is the moment to run `make manifest` and
   commit everything atomically, per the data-layer contract).

If any step disagrees beyond the stored tolerances, do not debug the
documentation — file a
[verification request](https://github.com/wild8highlander/navier-stokes-b/issues/new?template=verification_request.yml)
with your stdout, commit hash and platform. Reproduction failures are the
highest-priority bugs this repository knows.

---

Navigation: [repository root](../README.md) · [results](../data/results/README.md) · [plots](../data/plots/README.md) · [verification](../verification/README.md) · [IPL-RP-1.0](../LICENSE.md)

*Part of [wild8highlander/navier-stokes-b](https://github.com/wild8highlander/navier-stokes-b) — © 2026 Isaev Iskhak Khamzatovich, all rights reserved.*
