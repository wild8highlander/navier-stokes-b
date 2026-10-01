# `python_levels/` — the L1–L5 reference chain

> **Navigation:** [repository root](../README.md) › [verification](../README.md) › **`python_levels`**

![Python](https://img.shields.io/badge/Python_3.11%2B-3776AB?style=flat-square)
![Chain](https://img.shields.io/badge/Levels_L1%E2%80%93L5-2EA043?style=flat-square)
![mpmath](https://img.shields.io/badge/mpmath-50--digits-blueviolet?style=flat-square)
![License](https://img.shields.io/badge/License-IPL--RP--1.0-red?style=flat-square)

---

This is the **reference implementation of the verification chain** — the
executable definition of the five levels that re-derive the program's
analytical claims numerically. Everything else (Julia, the formal ports,
the NSB-96 laboratories) is required to agree with this directory.

## The five levels

| File | Level | Establishes | Recorded outcome |
|---|---|---|---|
| `l1_exact_constants.py` | **L1** | exact constants from the closed forms (mpmath, 50 digits) + float64 cross-check | all identities exact; `sin θ_b − b = 0` by construction |
| `l2_rotation_algebra.py` | **L2** | rotation algebra: `RᵀR = I`, `det R = 1`, `\|u′\| = \|u\|`, spectrum `{1, e^{±iθ_b}}` | residuals ≤ 4.5×10⁻¹⁶ over 10⁵ vectors |
| `l3_kirchhoff_vortices.py` | **L3** | Kirchhoff point-vortex system: Hamiltonicity, RK4 order, isometry | RK4 order measured **4.0008**; H-drift → 0 as dt⁴ |
| `l4_nse_2d.py` | **L4** | 2D NSE: `ω′ = cos θ_b·ω`, energy preservation, `div u′ = −b·ω`, max principle | residuals ≤ 7.1×10⁻¹⁴; energy error 2.2×10⁻¹⁶ |
| `l5_nse_3d_bkm.py` | **L5** | 3D Taylor–Green (N = 48, ν = 0.01, T = 6): BKM integral, true NSE vs continuous b-rotation | `I_BKM` = 9.3560 / 9.6758; `\|ΔE\|`/rotation 1.4×10⁻⁹ |
| `config.py` | — | shared tolerances and parameters | — |
| `verify_all.py` | — | the aggregate runner | `L1: PASS … L5: PASS` |

## Run

```bash
python3 verification/python_levels/verify_all.py               # full chain (~20 min)
NSE3D_SKIP=1 python3 verification/python_levels/verify_all.py  # fast mode (skip L5)
NSE3D_SMALL=1 python3 verification/python_levels/verify_all.py # L5 control mode
python3 verification/python_levels/l2_rotation_algebra.py      # one level
```

Wall-clock on two cores: L1–L4 about two minutes combined; L5 ten to
twenty minutes. Deterministic (fixed seeds), idempotent, safe to interrupt.

## Pinned verdicts

[`results/`](results/README.md) mirrors the verdict JSONs; the baseline
copies live in [`data/results/baseline/`](../../data/results/baseline/README.md).

## License

Part of **navier-stokes-b**, license IPL-RP-1.0 ([LICENSE.md](../LICENSE.md)).
