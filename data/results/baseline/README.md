# `data/results/baseline/` — Pinned Verdicts of the L1–L5 Chain

Reference outputs of the five-level verification chain, recorded from the executed run
of [`verification/python_levels/verify_all.py`](../../../verification/python_levels/README.md)
on 2026-09-16. They serve two purposes: (1) the headline numbers in the README, and
(2) regression baselines — rerunning the chain must land on these values.

## Files

| File | Level | What is pinned |
|---|---|---|
| `l1_exact_constants.json` | L1 | exact values of b, θ_b, cos θ_b (50 digits) |
| `l2_rotation_algebra.json` | L2 | Rodrigues rotation shape coefficients and identities |
| `l3_kirchhoff_vortices.json` | L3 | Kirchhoff point-vortex system: b emerges from the equilibrium |
| `l4_nse_2d.json` | L4 | 2D NSE checks: residual margins, RK4 order 4.0008 |
| `l5_nse_3d_bkm.json` | L5 | 3D NSE: I_BKM = 9.3560 (NSE) / 9.6758 (b-rotation), \|ΔE\| per rotation 1.4×10⁻⁹ |

## Reproduce

```bash
python3 verification/python_levels/verify_all.py   # ~20 min on 2 cores
# then diff your outputs against these files
```

File integrity is pinned in [`MANIFEST.json`](../../../MANIFEST.json) and re-checked by CI.

---
Navigation: [results](../README.md) · [verification chain](../../../verification/README.md) · [IPL-RP-1.0](../../../LICENSE.md)
