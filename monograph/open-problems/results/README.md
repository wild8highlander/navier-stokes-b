# `monograph/open-problems/results/` — JSON Protocols of P1–P7

Machine-readable verdicts of the executable open-problems program
([`../code/`](../code/README.md)). One file per problem, one line of headline in each —
these are the exact numbers printed in the open-problems appendix of the monograph.

| File | Problem | Headline |
|---|---|---|
| `core_b.json` | core | pinned values of b, θ_b and the rotation map |
| `p1b_droplet_feedback.json` | P1b | feedback on supersaturation S(t) |
| `p2_track_momentum.json` | P2 | momentum conservation through the b-rotation |
| `p3_surface_universality.json` | P3 | worst θ_b residual across geometries |
| `p4_ensemble.json` | P4 | ensemble spread vs threshold |
| `p5_bprotocol.json` | P5 | b-protocol growth control |
| `p6_taylor_green_bkm.json` | P6 | BKM integral: NSE vs b-rotation |
| `p7_collider_scale.json` | P7 | collider-scale scaling of the effect |

All files are pinned by sha256 in [`MANIFEST.json`](../../../MANIFEST.json); regenerate
with `python3 ../code/run_all.py` and refresh the manifest in the same change.

---
Navigation: [open-problems](../README.md) · [code](../code/README.md) · [figures](../figures/README.md) · [IPL-RP-1.0](../../../LICENSE.md)
