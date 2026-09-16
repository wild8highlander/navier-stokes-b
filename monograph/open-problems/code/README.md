# `monograph/open-problems/code/` — Executable P1–P7 Program

Python implementation of the seven-open-problem program described in
[`OPEN_PROBLEMS_7.md`](../OPEN_PROBLEMS_7.md). Each script solves one problem and
writes its JSON protocol to [`../results/`](../results/README.md); the figures land in
[`../figures/`](../figures/README.md).

| Script | Problem | Output protocol |
|---|---|---|
| `core_b.py` | shared core: the constant b, the rotation map | `core_b.json` |
| `p1b_droplet_feedback.py` | P1b — droplet feedback on supersaturation | `p1b_droplet_feedback.json` |
| `p2_track_momentum.py` | P2 — momentum tracking of the b-rotation | `p2_track_momentum.json` |
| `p3_surface_universality.py` | P3 — universality of θ_b across geometries | `p3_surface_universality.json` |
| `p4_ensemble.py` | P4 — ensemble statistics at Re = 2000 | `p4_ensemble.json` |
| `p5_bprotocol.py` | P5 — the b-protocol for growth control | `p5_bprotocol.json` |
| `p6_taylor_green_bkm.py` | P6 — Taylor–Green BKM integral reduction | `p6_taylor_green_bkm.json` |
| `p7_collider_scale.py` | P7 — collider-scale implications | `p7_collider_scale.json` |
| `make_figures.py` | regenerates all figures from the protocols | `../figures/*.png` |
| `run_all.py` | runs the whole program in order | — |

## Usage

```bash
python3 run_all.py                    # full program
python3 p6_taylor_green_bkm.py        # a single problem
python3 make_figures.py               # figures only
```

The same problems are mirrored by the formal/verification layer — see
[`verification/section1_correction_b/`](../../../verification/section1_correction_b/README.md)
and the P7 Lean 4 registry at the repository root.

---
Navigation: [open-problems](../README.md) · [results](../results/README.md) · [figures](../figures/README.md) · [IPL-RP-1.0](../../../LICENSE.md)
