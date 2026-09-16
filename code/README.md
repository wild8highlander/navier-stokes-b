# `code/` — Physics Runs P1–P6 and the Core Libraries

Executable Python programs of the b-correction program. Every run writes a JSON
protocol to [`data/results/`](../data/results/) and the final figures to
[`data/plots/`](../data/plots/). The numbers quoted in the root README come from
these programs — nothing is hand-written.

## Contents

| File | Purpose | Key output |
|---|---|---|
| `tg2d_core.py` | shared 2D thermogasdynamics core (grid, CFL, buoyancy) | — |
| `chamber3d.py` | 3D Wilson-chamber geometry used by P1/P5 | — |
| `p1_3d_microphysics.py` | **P1** droplet microphysics vs analytics; energy-injection audit | `data/results/p1_3d_microphysics.json` |
| `p2_grid_convergence.py` | **P2** grid/time-step convergence; RK4 order measurement | `data/results/p2_grid_convergence.json` |
| `p3_buoyancy.py` | **P3** buoyancy at Gr = 10⁶ (free-slip, 72×144) | `data/results/p3_buoyancy.json` |
| `p4_ensemble_sigma_y.py` | **P4** ensemble spread at Re = 2000 (4 realizations) | `data/results/p4_ensemble_sigma_y.json` |
| `p5_droplet_feedback.py` | **P5** droplet feedback on supersaturation | `data/results/p5_droplet_feedback.json` |
| `p6_b_universality.py` | **P6** universality of θ_b on R², T², S², H², R³ | `data/results/p6_b_universality.json` |
| `make_plots.py` | regenerates the 300-dpi plots from the JSON protocols | `data/plots/*.png` |
| `run_all.sh` | runs the full chain P1 → P6 + plots, sequentially | — |

## Usage

```bash
# full chain (sequential; P3 takes ~15 min on 2 cores)
./run_all.sh

# a single run
python3 p2_grid_convergence.py

# regenerate plots only (requires data/results/*.json)
python3 make_plots.py
```

## Requirements

Python 3.11+ (reference: 3.12) with numpy, scipy, matplotlib, mpmath —
see [`environment.yml`](../environment.yml) or `make install` at the repository root.

## Verification contract

Each program is idempotent and deterministic on a fixed platform: rerunning it must
reproduce the pinned values in `data/results/` up to the stated tolerances. If a value
differs, treat it as a bug and file a
[verification request](https://github.com/wild8highlander/navier-stokes-b/issues/new?template=verification_request.yml).

---
Navigation: [repository root](../README.md) · [results](../data/results/README.md) · [plots](../data/plots/README.md) · [IPL-RP-1.0](../LICENSE.md)
