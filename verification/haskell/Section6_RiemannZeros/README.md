# `Section6_RiemannZeros` — Riemann zeros — the Hilbert–Pólya programme (Haskell)

> **Navigation:** [repository root](../../README.md) › [verification](../../verification/README.md) › [haskell](../README.md) › **section 6**

![Section](https://img.shields.io/badge/S6-2B579A?style=flat-square) ![Language](https://img.shields.io/badge/Haskell_·_GHC_9.4-5e5075-informational?style=flat-square) ![Contract](https://img.shields.io/badge/PASS_%2B_JSON-FF8C00?style=flat-square) ![License](https://img.shields.io/badge/IPL--RP--1.0-red?style=flat-square)

---

**What this port recomputes:** ζ special values, the functional equation off the line, annihilation at the first zero vs the off-zero contrast.

The claims are *defined* by the Python reference port
([`verification/section6_riemann_zeros/python/verify.py`](../../verification/section6_riemann_zeros/python/README.md));
this Haskell binary must reproduce the same verdict — same
assertions, same tolerances, different arithmetic and toolchain. Any
disagreement is a CI failure by construction.

## How to build & run

```bash
cd verification/haskell && cabal build all

cabal run verify_section6_riemann_zeros
```

## Files

| File | Role |
|---|---|
| `Main.hs` | the Haskell port of section 6 |
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
