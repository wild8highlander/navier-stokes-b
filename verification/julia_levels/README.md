# `julia_levels/` — the independent Julia chain (L1–L5 + L7)

> **Navigation:** [repository root](../README.md) › [verification](../README.md) › **`julia_levels`**

![Julia](https://img.shields.io/badge/Julia_stdlib--only-9558B2?style=flat-square)
![Chain](https://img.shields.io/badge/Levels_L1%E2%80%93L5_%2B_L7-2EA043?style=flat-square)
![License](https://img.shields.io/badge/License-IPL--RP--1.0-red?style=flat-square)

---

The Julia tree is a **fully independent re-implementation of the L1–L5
chain** (and, since the Section-7 extension, of the Smagorinsky–Kolmogorov
master relation as `L7`): standard library only, its own radix-2 FFT, its
own linear algebra where needed. Julia's `Float64` and LLVM codegen give a
genuinely independent arithmetic path; agreement with the Python reference
to the stated tolerances is the cross-language statement.

## Levels

| File | Level | What it re-derives | Pinned outcome |
|---|---|---|---|
| `l1_exact_constants.jl` | **L1** | the constants from the closed forms (`BigFloat`, 50 digits) + float64 cross-check | all identities exact |
| `l2_rotation_algebra.jl` | **L2** | `RᵀR = I`, `det R = 1`, `\|u′\| = \|u\|`, spectrum `{1, e^{±iθ_b}}` | residuals ≤ 4.5×10⁻¹⁶ |
| `l3_kirchhoff_vortices.jl` | **L3** | Kirchhoff Hamiltonicity, RK4 order, isometry | RK4 order ≈ 4.0008 |
| `l4_nse_2d.jl` | **L4** | `ω′ = cos θ_b · ω`, energy preservation, `div u′ = −b·ω` | residuals ≤ 7.1×10⁻¹⁴ |
| `l5_nse_3d_bkm.jl` | **L5** | 3D Taylor–Green BKM protocol, true NSE vs continuous b-rotation | `\|ΔE\|`/rotation ≈ 1.4×10⁻⁹ |
| `l7_smagorinsky_kolmogorov.jl` | **L7** | the master relation (BigFloat), Cassini (BigInt), the (5′) coefficient algebra, K41 slope | `C_s` = 0.1732659558297058 |
| `config.jl` | — | shared configuration and tolerances | — |
| `common.jl` | — | shared helpers (FFT, banners, checks) | — |

## Run

```bash
julia verify_all.jl                  # everything; L5 (N=32) ≈ 5–15 min
NSE3D_SKIP=1 julia verify_all.jl     # without L5
NSE3D_SMALL=1 julia verify_all.jl    # L5 in a control mode
julia l7_smagorinsky_kolmogorov.jl   # section 7 standalone
```

Pinned verdicts of the chain are mirrored in
[`data/results/baseline/`](../../data/results/baseline/README.md) and in
[`results/`](results/README.md).

## Output contract

Banner → compute from the closed forms → per-assertion `[PASS]`/`[FAIL]`
→ `JSON:` verdict per port → the aggregate `L1…L7: PASS/FAIL` table.

## License

Part of **navier-stokes-b**, license IPL-RP-1.0 ([LICENSE.md](../LICENSE.md)).
