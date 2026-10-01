# `python_levels/results/` — chain verdict mirror

> **Navigation:** [repository root](../../../README.md) › [verification](../../README.md) › [python_levels](../README.md) › **`results/`**

![Mirror](https://img.shields.io/badge/Role-verdict--mirror-2EA043?style=flat-square)
![License](https://img.shields.io/badge/License-IPL--RP--1.0-red?style=flat-square)

---

The pinned verdict JSONs of the L1–L5 chain runs. These files are the
*mirror* of the authoritative baseline copies in
[`data/results/baseline/`](../../../data/results/baseline/README.md); the
repository auditor
([`verification/repo_integrity/`](../../repo_integrity/README.md)) checks
the baseline copies on every run.

| File | Level | Content |
|---|---|---|
| `l1_exact_constants.json` | L1 | the 50-digit constants and the float64 cross-check residuals |
| `l2_rotation_algebra.json` | L2 | the rotation-algebra residuals (orthogonality, determinant, spectrum) |
| `l3_kirchhoff_vortices.json` | L3 | the RK4 order measurement and the Hamiltonian drift table |
| `l4_nse_2d.json` | L4 | the vorticity identity, energy preservation and balance residuals |
| `l5_nse_3d_bkm.json` | L5 | the BKM protocol record: parameters, integrals, per-rotation energy |

**Authoritative copies:** [`data/results/baseline/`](../../../data/results/baseline/README.md)
(verified by `make verify-repo` and the CI manifest job).

## License

Part of **navier-stokes-b**, license IPL-RP-1.0 ([LICENSE.md](../../../LICENSE.md)).
