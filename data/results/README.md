# `data/results/` — JSON Run Protocols

Machine-readable verdicts of the executed program. Each JSON records the command,
parameters, tolerances and final numbers of one run, so any figure in the README can
be traced to its producing process.

## Files

| File | Run | Key fields |
|---|---|---|
| `p1_3d_microphysics.json` | P1 — 3D Wilson-chamber microphysics | growth error vs analytics, energy injection audit, Δσ_⊥ |
| `p2_grid_convergence.json` | P2 — grid & time-step convergence | RK4 `p_time`, factor `F` across N and Re |
| `p3_buoyancy.json` | P3 — buoyancy, Gr = 10⁶ | `Nu`, CFL margin, \|ΔNu(b)\|/Nu |
| `p4_ensemble_sigma_y.json` | P4 — ensemble spread, Re = 2000 | \|Δσ_y\|/σ_y vs 2s/σ threshold |
| `p5_droplet_feedback.json` | P5 — droplet feedback | `S_min` before/after, growth slowdown, vapor balance |
| `p6_b_universality.json` | P6 — universality of θ_b | worst angle residual per geometry (R², T², S², H², R³) |
| `summary_numbers.json` | all of the above | the single source for every quoted number |
| `p1_positions.npz`, `p3_theta_snapshot.npy` | binary snapshots | raw field/trajectory data backing P1 and P3 |
| [`baseline/`](baseline/README.md) | L1–L5 chain | pinned verification verdicts |

## Usage

```bash
# one-glance summary
python3 -c "import json;print(json.dumps(json.load(open('summary_numbers.json')),indent=2))"
```

Regenerate with `cd code && ./run_all.sh` — then update the README tables **in the
same change** and refresh [`MANIFEST.json`](../../MANIFEST.json).

---
Navigation: [data](../README.md) · [plots](../plots/README.md) · [code](../../code/README.md) · [IPL-RP-1.0](../../LICENSE.md)
