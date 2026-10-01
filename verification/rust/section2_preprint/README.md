# `section2_preprint` — Preprint NSE — the regularity chain (Rust)

> **Navigation:** [repository root](../../README.md) › [verification](../../verification/README.md) › [rust](../README.md) › **section 2**

![Section](https://img.shields.io/badge/S2-2B579A?style=flat-square) ![Language](https://img.shields.io/badge/Rust_·_std--only-dea584-informational?style=flat-square) ![Contract](https://img.shields.io/badge/PASS_%2B_JSON-FF8C00?style=flat-square) ![License](https://img.shields.io/badge/IPL--RP--1.0-red?style=flat-square)

---

**What this port recomputes:** twist unitarity, the Leray premise (per-rotation energy change at machine-accumulation level, signed injection zero in the mean), the BKM bridge on the reference Taylor–Green field.

The claims are *defined* by the Python reference port
([`verification/section2_preprint/python/verify.py`](../../verification/section2_preprint/python/README.md));
this Rust binary must reproduce the same verdict — same
assertions, same tolerances, different arithmetic and toolchain. Any
disagreement is a CI failure by construction.

## How to build & run

```bash
cd verification/rust && cargo build --release

./target/release/verify_section2
```

## Files

| File | Role |
|---|---|
| `main.rs` | the Rust port of section 2 |
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
