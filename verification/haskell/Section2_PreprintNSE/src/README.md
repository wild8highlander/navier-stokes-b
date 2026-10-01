# `Section2_PreprintNSE/src/` — the Haskell module of section 2

> **Navigation:** [repository root](../../../README.md) › [verification](../../../verification/README.md) › [haskell](../../README.md) › [`Section2_PreprintNSE`](../README.md) › **`src/`**

![Module](https://img.shields.io/badge/Main.hs-informational?style=flat-square) ![Purity](https://img.shields.io/badge/pure_·_total-5e5075?style=flat-square) ![License](https://img.shields.io/badge/IPL--RP--1.0-red?style=flat-square)

---

`Main.hs` is the complete port: pure numerical functions, an IO wrapper
that prints the contract output, and exact `Integer` arithmetic wherever
the claim demands it (Fibonacci, Cassini, the closed forms). The verdict
must agree with the Python reference
[`verification/section2_preprint/python/verify.py`](../../verification/section2_preprint/python/README.md).

## License

Part of **navier-stokes-b**, license IPL-RP-1.0. ([LICENSE.md](../../../LICENSE.md)).
