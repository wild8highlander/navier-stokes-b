# `section2_preprint/src/` — the Rust module of section 2

> **Navigation:** [repository root](../../../README.md) › [verification](../../../verification/README.md) › [rust](../../README.md) › [`section2_preprint`](../README.md) › **`src/`**

![Module](https://img.shields.io/badge/main.rs-informational?style=flat-square) ![Safety](https://img.shields.io/badge/std--only_·_no--unsafe-2EA043?style=flat-square) ![License](https://img.shields.io/badge/IPL--RP--1.0-red?style=flat-square)

---

`main.rs` is the complete port: a single `fn main()` behind the uniform
`check()` harness. The module contains no `unsafe`, no external crates,
and no floating-point state beyond the deterministic computation itself —
which is the point: the Rust toolchain re-derives the numbers with its own
arithmetic, and the verdict must agree with the Python reference
[`verification/section2_preprint/python/verify.py`](../../verification/section2_preprint/python/README.md)
to the stated tolerances.

## License

Part of **navier-stokes-b**, license IPL-RP-1.0. ([LICENSE.md](../../../LICENSE.md)).
