# `verification/python_levels/results/` — Fresh Outputs of the Chain

> **Navigation:** [`python_levels`](../README.md) › **`results`**

![Fresh](https://img.shields.io/badge/Role-Latest_run_outputs-FF8C00?style=flat-square) ![License](https://img.shields.io/badge/License-IPL--RP--1.0-red?style=flat-square)

The working outputs of the most recent
[`verify_all.py`](../README.md) run — overwritten in place each time the
chain executes. They are the *live* counterpart of the pinned baselines in
[`data/results/baseline/`](../../../data/results/baseline/README.md): diff
the two after a rerun, and "the chain still holds" becomes a mechanical
check instead of a claim.

## Files

| File | Level |
|---|---|
| `l1_exact_constants.json` | L1 — the exact constants (mpmath, 50 digits) + float64 cross-checks |
| `l2_rotation_algebra.json` | L2 — the rotation-algebra identities and residuals |
| `l3_kirchhoff_vortices.json` | L3 — the Kirchhoff chain: RK4 order, drift, isometry |
| `l4_nse_2d.json` | L4 — the 2D NSE identities: ω′ = cos θ_b·ω, energy, div, max principle |
| `l5_nse_3d_bkm.json` | L5 — the 3D Taylor–Green BKM verdict of the latest run |

## Contract

```bash
python3 ../verify_all.py        # regenerate (NSE3D_SKIP=1 to skip L5)
diff . ../../../data/results/baseline/    # compare against the pinned baselines
```

Only the pinned baselines are quoted by documentation and CI-pinned via
[`MANIFEST.json`](../../../MANIFEST.json); this directory is the bench,
not the archive.

---

---

Navigation: [python_levels](../README.md) · [pinned baselines](../../../data/results/baseline/README.md) · [IPL-RP-1.0](../../../LICENSE.md)

*Part of [wild8highlander/navier-stokes-b](https://github.com/wild8highlander/navier-stokes-b) - (c) 2026 Isaev Iskhak Khamzatovich, all rights reserved.*

