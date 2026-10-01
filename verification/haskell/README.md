# `haskell/` — the Haskell recomputation tier

> **Navigation:** [repository root](../README.md) › [verification](../README.md) › **`haskell`**

![Language](https://img.shields.io/badge/Haskell_·_GHC_9.4-5e5075-informational?style=flat-square) ![Tier](https://img.shields.io/badge/2_·_computational-2EA043?style=flat-square) ![Contract](https://img.shields.io/badge/PASS_%2B_JSON-FF8C00?style=flat-square) ![License](https://img.shields.io/badge/IPL--RP--1.0-red?style=flat-square)

---

The Haskell tree is the lazy, pure recomputation tier: one Cabal project per section (see `cabal.project`), each with a pure `Main` module and an IO wrapper that formats the contract output. Lazy evaluation and arbitrary-precision `Integer` make the exact identities (Cassini, the closed forms) structurally natural — the port checks them without any approximation, then repeats them in `Double` for the floating-point comparison.

## Toolchain

GHC 9.4 via Cabal, pure functional idioms, `Integer` where exactness matters

## Build & run

```bash
cd verification/haskell
cabal build all

# run one section
cabal run verify_section7_smagorinsky_kolmogorov
```

## Section map

| Directory | Section | What the port recomputes |
|---|---|---|
| [`Section1_CorrectionB/`](Section1_CorrectionB/README.md) | S1 — Correction b | the closed form `b = 1/(4π+2√3)` in the language's own arithmetic, `sin(θ_b) = b`, the Rodrigues algebra (`RᵀR = I`, `det R = 1`, `trace R = 1 + 2 cos θ_b`) and energy neutrality over 10⁴ vectors |
| [`Section2_PreprintNSE/`](Section2_PreprintNSE/README.md) | S2 — Preprint NSE | twist unitarity, the Leray premise (per-rotation energy change at machine-accumulation level, signed injection zero in the mean), the BKM bridge on the reference Taylor–Green field |
| [`Section3_ABCloud/`](Section3_ABCloud/README.md) | S3 — AB-Cloud | Hermiticity and trace zero of the flux-lattice Hamiltonian, the butterfly slice identities `Σ E_j = −2`, `Σ E_j² = 2q − 4`, and the framework-constant cross-link |
| [`Section4_KdV/`](Section4_KdV/README.md) | S4 — KdV | the soliton ODE residual at machine zero, the speed–amplitude law `u_max = c/2`, the width law `∝ 1/√c` |
| [`Section5_KleinAttractor/`](Section5_KleinAttractor/README.md) | S5 — Klein attractor | orbit density (max angular gap), isometry at every iterate, the Niven-set irrationality argument |
| [`Section6_RiemannZeros/`](Section6_RiemannZeros/README.md) | S6 — Riemann zeros | ζ special values, the functional equation off the line, annihilation at the first zero vs the off-zero contrast |
| [`Section7_SmagorinskyKolmogorov/`](Section7_SmagorinskyKolmogorov/README.md) | S7 — Smagorinsky–Kolmogorov | `C_s(1.5) = 0.17326595582970580…`, Lilly agreement to 6×10⁻⁶, the exact −3/4 exponent law, monotonicity, Cassini k = 0..40 exact, the (5′) coefficient algebra (a·b·b·c sign-definite, a·a·b·b degenerate), the K41 slope |

Every port follows the repository-wide output contract: banner → compute
from the closed forms (no data files) → one `[PASS]`/`[FAIL]` line per
assertion with the measured residual → exactly one `JSON: {"section": N,
"language": "...", "values": {...}, "all_passed": bool}` verdict line →
exit `0` only if everything passed. The cross-language validator in
[`verification/tests/`](../tests/README.md) (or
[`../..`](../tests/README.md) from nested directories) fails CI on any
disagreement between ports.

## License

Part of **navier-stokes-b**, license IPL-RP-1.0. ([LICENSE.md](../LICENSE.md)).
