# `rust/` — the Rust recomputation tier

> **Navigation:** [repository root](../README.md) › [verification](../README.md) › **`rust`**

![Language](https://img.shields.io/badge/Rust_·_std--only-dea584-informational?style=flat-square) ![Tier](https://img.shields.io/badge/2_·_computational-2EA043?style=flat-square) ![Contract](https://img.shields.io/badge/PASS_%2B_JSON-FF8C00?style=flat-square) ![License](https://img.shields.io/badge/IPL--RP--1.0-red?style=flat-square)

---

The Rust tree is the memory-safety recomputation tier: a std-only Cargo workspace with one binary crate per section (`verify_section1` … `verify_section7`). No external crates are permitted — the ports deliberately re-implement the small linear algebra they need, so the build is reproducible from `rustc` alone. Exact integer work (Fibonacci, Cassini) uses `i128`/`u128`, which is a genuinely different arithmetic path than the other ports.

## Toolchain

Rust edition 2021, std-only Cargo workspace — zero external crates

## Build & run

```bash
cd verification/rust
cargo build --release

# run one section
./target/release/verify_section7
```

## Section map

| Directory | Section | What the port recomputes |
|---|---|---|
| [`section1_correction_b/`](section1_correction_b/README.md) | S1 — Correction b | the closed form `b = 1/(4π+2√3)` in the language's own arithmetic, `sin(θ_b) = b`, the Rodrigues algebra (`RᵀR = I`, `det R = 1`, `trace R = 1 + 2 cos θ_b`) and energy neutrality over 10⁴ vectors |
| [`section2_preprint/`](section2_preprint/README.md) | S2 — Preprint NSE | twist unitarity, the Leray premise (per-rotation energy change at machine-accumulation level, signed injection zero in the mean), the BKM bridge on the reference Taylor–Green field |
| [`section3_ab_cloud/`](section3_ab_cloud/README.md) | S3 — AB-Cloud | Hermiticity and trace zero of the flux-lattice Hamiltonian, the butterfly slice identities `Σ E_j = −2`, `Σ E_j² = 2q − 4`, and the framework-constant cross-link |
| [`section4_kdv/`](section4_kdv/README.md) | S4 — KdV | the soliton ODE residual at machine zero, the speed–amplitude law `u_max = c/2`, the width law `∝ 1/√c` |
| [`section5_klein_attractor/`](section5_klein_attractor/README.md) | S5 — Klein attractor | orbit density (max angular gap), isometry at every iterate, the Niven-set irrationality argument |
| [`section6_riemann_zeros/`](section6_riemann_zeros/README.md) | S6 — Riemann zeros | ζ special values, the functional equation off the line, annihilation at the first zero vs the off-zero contrast |
| [`section7_smagorinsky_kolmogorov/`](section7_smagorinsky_kolmogorov/README.md) | S7 — Smagorinsky–Kolmogorov | `C_s(1.5) = 0.17326595582970580…`, Lilly agreement to 6×10⁻⁶, the exact −3/4 exponent law, monotonicity, Cassini k = 0..40 exact, the (5′) coefficient algebra (a·b·b·c sign-definite, a·a·b·b degenerate), the K41 slope |

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
