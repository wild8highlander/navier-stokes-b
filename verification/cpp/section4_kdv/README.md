# `section4_kdv` — KdV — soliton interactions (C++17)

> **Navigation:** [repository root](../../README.md) › [verification](../../verification/README.md) › [cpp](../README.md) › **section 4**

![Section](https://img.shields.io/badge/S4-2B579A?style=flat-square) ![Language](https://img.shields.io/badge/C%2B%2B17_·_CMake-red-informational?style=flat-square) ![Contract](https://img.shields.io/badge/PASS_%2B_JSON-FF8C00?style=flat-square) ![License](https://img.shields.io/badge/IPL--RP--1.0-red?style=flat-square)

---

**What this port recomputes:** the soliton ODE residual at machine zero, the speed–amplitude law `u_max = c/2`, the width law `∝ 1/√c`.

The claims are *defined* by the Python reference port
([`verification/section4_kdv/python/verify.py`](../../verification/section4_kdv/python/README.md));
this C++17 binary must reproduce the same verdict — same
assertions, same tolerances, different arithmetic and toolchain. Any
disagreement is a CI failure by construction.

## How to build & run

```bash
cd verification/cpp && mkdir -p build && cd build && cmake .. && make -j$(nproc)

./build/verify_section4_kdv
```

## Files

| File | Role |
|---|---|
| `main.cpp` | the C++17 port of section 4 |

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
