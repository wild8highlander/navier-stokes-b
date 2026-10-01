# `section1_correction_b` — Correction b — the universal polarization constant (C++17)

> **Navigation:** [repository root](../../README.md) › [verification](../../verification/README.md) › [cpp](../README.md) › **section 1**

![Section](https://img.shields.io/badge/S1-2B579A?style=flat-square) ![Language](https://img.shields.io/badge/C%2B%2B17_·_CMake-red-informational?style=flat-square) ![Contract](https://img.shields.io/badge/PASS_%2B_JSON-FF8C00?style=flat-square) ![License](https://img.shields.io/badge/IPL--RP--1.0-red?style=flat-square)

---

**What this port recomputes:** the closed form `b = 1/(4π+2√3)` in the language's own arithmetic, `sin(θ_b) = b`, the Rodrigues algebra (`RᵀR = I`, `det R = 1`, `trace R = 1 + 2 cos θ_b`) and energy neutrality over 10⁴ vectors.

The claims are *defined* by the Python reference port
([`verification/section1_correction_b/python/verify.py`](../../verification/section1_correction_b/python/README.md));
this C++17 binary must reproduce the same verdict — same
assertions, same tolerances, different arithmetic and toolchain. Any
disagreement is a CI failure by construction.

## How to build & run

```bash
cd verification/cpp && mkdir -p build && cd build && cmake .. && make -j$(nproc)

./build/verify_section1_correction_b
```

## Files

| File | Role |
|---|---|
| `main.cpp` | the C++17 port of section 1 |

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
