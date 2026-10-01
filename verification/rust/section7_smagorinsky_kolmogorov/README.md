# `section7_smagorinsky_kolmogorov` — Smagorinsky–Kolmogorov — the master relation (Rust)

> **Navigation:** [repository root](../../README.md) › [verification](../../verification/README.md) › [rust](../README.md) › **section 7**

![Section](https://img.shields.io/badge/S7-2B579A?style=flat-square) ![Language](https://img.shields.io/badge/Rust_·_std--only-dea584-informational?style=flat-square) ![Contract](https://img.shields.io/badge/PASS_%2B_JSON-FF8C00?style=flat-square) ![License](https://img.shields.io/badge/IPL--RP--1.0-red?style=flat-square)

---

**What this port recomputes:** `C_s(1.5) = 0.17326595582970580…`, Lilly agreement to 6×10⁻⁶, the exact −3/4 exponent law, monotonicity, Cassini k = 0..40 exact, the (5′) coefficient algebra (a·b·b·c sign-definite, a·a·b·b degenerate), the K41 slope.

The claims are *defined* by the Python reference port
([`verification/section7_smagorinsky_kolmogorov/python/verify.py`](../../verification/section7_smagorinsky_kolmogorov/python/README.md));
this Rust binary must reproduce the same verdict — same
assertions, same tolerances, different arithmetic and toolchain. Any
disagreement is a CI failure by construction.

## How to build & run

```bash
cd verification/rust && cargo build --release

./target/release/verify_section7
```

## Files

| File | Role |
|---|---|
| `main.rs` | the Rust port of section 7 |
| `src/README.md` | notes on the source module |
| `Cargo.toml` / `.cabal` | the build manifest |

Every port follows the repository-wide output contract: banner → compute
from the closed forms (no data files) → one `[PASS]`/`[FAIL]` line per
assertion with the measured residual → exactly one `JSON: {"section": N,
"language": "...", "values": {...}, "all_passed": bool}` verdict line →
exit `0` only if everything passed. The cross-language validator in
[`verification/tests/`](../tests/README.md) (or
[`../..`](../tests/README.md) from nested directories) fails CI on any
disagreement between ports.

## License

Part of **navier-stokes-b**, license IPL-RP-1.0. ([LICENSE.md](../../LICENSE.md)).
