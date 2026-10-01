# `section6_riemann_zeros` — Riemann zeros — the Hilbert–Pólya programme (C++17)

> **Navigation:** [repository root](../../README.md) › [verification](../../verification/README.md) › [cpp](../README.md) › **section 6**

![Section](https://img.shields.io/badge/S6-2B579A?style=flat-square) ![Language](https://img.shields.io/badge/C%2B%2B17_·_CMake-red-informational?style=flat-square) ![Contract](https://img.shields.io/badge/PASS_%2B_JSON-FF8C00?style=flat-square) ![License](https://img.shields.io/badge/IPL--RP--1.0-red?style=flat-square)

---

**What this port recomputes:** ζ special values, the functional equation off the line, annihilation at the first zero vs the off-zero contrast.

The claims are *defined* by the Python reference port
([`verification/section6_riemann_zeros/python/verify.py`](../../verification/section6_riemann_zeros/python/README.md));
this C++17 binary must reproduce the same verdict — same
assertions, same tolerances, different arithmetic and toolchain. Any
disagreement is a CI failure by construction.

## How to build & run

```bash
cd verification/cpp && mkdir -p build && cd build && cmake .. && make -j$(nproc)

./build/verify_section6_riemann_zeros
```

## Files

| File | Role |
|---|---|
| `main.cpp` | the C++17 port of section 6 |

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
