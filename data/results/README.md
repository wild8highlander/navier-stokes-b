# `data/results/` — JSON Run Protocols of the Executed Program

> **Navigation:** [repository root](../../README.md) › [`data`](../README.md) › **`results`**

![Protocols](https://img.shields.io/badge/Files-JSON_pinned-1284BA?style=flat-square)
![Runs](https://img.shields.io/badge/Runs-P1%E2%80%93P6_%2B_L1%E2%80%93L5-2EA043?style=flat-square)
![License](https://img.shields.io/badge/License-IPL--RP--1.0-red?style=flat-square)

Machine-readable verdicts of the executed program. Each JSON records the
command, the full parameter set, the pre-registered success criteria, the
tolerances and the final numbers of one run — so any figure in any document
of this repository can be traced to its producing process, rerun and diffed.
The aggregate [`summary_numbers.json`](summary_numbers.json) collects every
headline value into one file, which is the intended first stop for a reader
checking a claim.

## Files

| File | Run | Key fields |
|---|---|---|
| `p1_3d_microphysics.json` | **P1** — 3D Wilson-chamber microphysics | growth error vs analytics (1.5×10⁻¹⁶), signed energy-injection audit (exactly 0), Δσ_⊥ = 1.17×10⁻⁷ m |
| `p1_positions.npz` | P1 binary snapshot | raw droplet trajectories backing the P1 figure |
| `p2_grid_convergence.json` | **P2** — grid & time-step convergence | RK4 `p_time` = 3.743, factor `F` across N = 64/128 and Re = 400/800/1600 |
| `p3_buoyancy.json` | **P3** — buoyancy at Gr = 10⁶ | `Nu` = 19.64, CFL margin 0.246, \|ΔNu(b)\|/Nu ≤ 2.1×10⁻¹¹ |
| `p3_theta_snapshot.npy` | P3 binary snapshot | temperature field snapshot θ(z) backing the P3 figure |
| `p4_ensemble_sigma_y.json` | **P4** — ensemble spread at Re = 2000 | \|Δσ_y\|/σ_y = 9.3×10⁻⁷ against the 2s/σ threshold 4.8 % |
| `p5_droplet_feedback.json` | **P5** — two-way droplet feedback | `S_min` = 3.8746, growth slowdown 1.16 %, vapor balance 0.75 % |
| `p6_b_universality.json` | **P6** — universality of θ_b | worst angle residual per geometry (R², T², S², H², R³): 9.5×10⁻¹⁵ |
| `summary_numbers.json` | **all of the above** | the single source for every quoted number of the program |
| [`baseline/`](baseline/README.md) | the L1–L5 chain | pinned verdicts of the five-level verification chain |

## Usage

```bash
# one-glance summary of every headline number
python3 -c "import json; print(json.dumps(json.load(open('summary_numbers.json')), indent=2))"

# compare a fresh rerun against the pinned baseline (after running code/run_all.sh)
python3 - <<'PY'
import json
pinned = json.load(open('p2_grid_convergence.json'))
print(json.dumps(pinned, indent=2)[:800], '...')
PY
```

## Regeneration and the immutability contract

Regenerate with `cd code && ./run_all.sh` — then update the README tables
**in the same change** and refresh [`MANIFEST.json`](../../MANIFEST.json)
(`make manifest`). These files are immutable evidence: documentation quotes
them, the manifest pins their sha256, and CI fails on any drift. The binary
snapshots (`.npz`, `.npy`) are raw field/trajectory data backing the plots —
they are the "make the figure from data, not from memory" guarantee of
[`data/plots/`](../plots/README.md).


## The envelope schema, in one table

| Field | Type | Meaning |
|---|---|---|
| `command` | string | the exact producing command |
| `parameters` | object | grid, seeds, ν, dt, windows — everything needed to rerun |
| `criteria` | list | the pre-registered success criteria with thresholds and marks |
| `values` | object | the recorded numbers (the documentation quotes these) |
| `tolerances` | object | the rerun agreement windows per value |
| `wall_time_s` | number | wall-clock cost of the recorded run |
| `timestamp` | string | when the run executed |

## Checking a specific claim

```bash
# every headline number of the program, pretty-printed:
python3 -c "import json; print(json.dumps(json.load(open('summary_numbers.json')), indent=2))" | less

# just the P3 Nusselt number:
python3 -c "import json; print(json.load(open('p3_buoyancy.json'))['values'])"
```

## Cross-references into the framework

| Protocol | Verifying framework layer |
|---|---|
| `p1_3d_microphysics.json` | [`code/p1_3d_microphysics.py`](../../code/README.md); framework section 1 (the constant) and the L4 identity |
| `p2_grid_convergence.json` | [`code/p2_grid_convergence.py`](../../code/README.md); L3's RK4-order measurement is the same diagnostic family |
| `p3_buoyancy.json` | [`code/p3_buoyancy.py`](../../code/README.md); the b-mode applies the L4 identity per step |
| `p4_ensemble_sigma_y.json` | [`code/p4_ensemble_sigma_y.py`](../../code/README.md); section 5's contraction statements |
| `p5_droplet_feedback.json` | [`code/p5_droplet_feedback.py`](../../code/README.md) |
| `p6_b_universality.json` | [`code/p6_b_universality.py`](../../code/README.md); mirrors the monograph's universality claim |

---

Navigation: [data](../README.md) · [plots](../plots/README.md) · [baseline](baseline/README.md) · [code](../../code/README.md) · [IPL-RP-1.0](../../LICENSE.md)

*Part of [wild8highlander/navier-stokes-b](https://github.com/wild8highlander/navier-stokes-b) — © 2026 Isaev Iskhak Khamzatovich, all rights reserved.*
