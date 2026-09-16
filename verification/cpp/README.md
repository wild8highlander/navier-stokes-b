# Ⓜ️ `cpp/` — the C++17 Numerical Verification Layer

> **Navigation:** [`verification`](../README.md) › **`cpp`**

![C++](https://img.shields.io/badge/C%2B%2B-17-00599C?style=flat-square&logo=cplusplus&logoColor=white)
![Build](https://img.shields.io/badge/Build-CMake_3.18%2B-064F8C?style=flat-square&logo=cmake&logoColor=white)
![Sections](https://img.shields.io/badge/Sections-6-9558B2?style=flat-square)
![License](https://img.shields.io/badge/License-IPL--RP--1.0-red?style=flat-square)

This directory carries the **C++17 numerical-verification layer**: one
self-contained section program per research topic, orchestrated by a
shared [`CMakeLists.txt`](CMakeLists.txt). The ports use a uniform
`check()` harness — every assertion prints `[PASS]`/`[FAIL]` with expected
vs actual at 15-digit precision, and `main` ends with the framework's
`JSON: {...}` verdict line and a non-zero exit on any failure.

The implementations are deliberately header-light: `std::cmath` arithmetic
for Section 1 (computing `b = π/(4π² + 2π√3)` to `double` precision —
algebraically identical to `1/(4π + 2√3)` = 0.06238119… — and verifying
`sin θ = b`, `cos²θ + sin²θ = 1`), and progressively deeper numerical
machinery for the later sections (pseudospectral KdV in Section 4,
BLAS/LAPACK-style spectral work in Section 3), matching the roles the
root README's language table assigns to C++.

## The six section ports

| Target | Directory | Section | Notes |
|---|---|---|---|
| `section1_correction_b` | [`section1_correction_b/`](section1_correction_b/README.md) | 1 | std::cmath closed-form evaluation |
| `section2_preprint` | [`section2_preprint/`](section2_preprint/README.md) | 2 | the regularity chain, array-based |
| `section3_ab_cloud` | [`section3_ab_cloud/`](section3_ab_cloud/README.md) | 3 | the heaviest: BLAS/LAPACK eigen-routines |
| `section4_kdv` | [`section4_kdv/`](section4_kdv/README.md) | 4 | the pseudospectral workhorse (FFT-dominated) |
| `section5_klein_attractor` | [`section5_klein_attractor/`](section5_klein_attractor/README.md) | 5 | invariant statistics |
| `section6_riemann_zeros` | [`section6_riemann_zeros/`](section6_riemann_zeros/README.md) | 6 | spacing diagnostics |

## Contents

| File | Description |
|---|---|
| [`CMakeLists.txt`](CMakeLists.txt) | one CMake project building all six section targets |

## How to run

```bash
cd verification/cpp
cmake -S . -B build && cmake --build build -j     # configure + parallel build
./build/section1_correction_b                     # run any target directly
```

What CMake resolves, in order: a C++17 compiler (GCC ≥ 9, Clang ≥ 10,
MSVC 2019+); a BLAS/LAPACK provider (OpenBLAS preferred, then reference
LAPACK — the chosen provider is printed during configuration); the six
per-section executables. Typical first build: 1–3 minutes, with BLAS
detection dominating configuration rather than compilation. If
configuration reports "no BLAS found", install the development packages
(`libopenblas-dev` / `liblapack-dev` on Debian–Ubuntu) and clear the
`build/` cache — CMake caches failed detections aggressively. CI compiles
the suite in the extended-languages workflow and runs the binaries under
the cross-language workflow.

## 🧮 The uniform check() harness

Every C++ port shares the same harness shape: a
`check(name, expected, actual, tol)` helper that prints `[PASS]`/`[FAIL]`
lines, accumulates failures, and emits the JSON verdict at the end. The
harness is the C++ face of the framework's output contract — the
validator in [`tests/`](../tests/README.md) consumes its output exactly
like every other language's, so performance engineering never buys
contract drift.

## 🎯 What C++ is for here

The C++ tier is the **performance witness and the KdV workhorse**:
BLAS/LAPACK-backed eigen-routines and the FFT pseudospectral solver live
here. Its check() harness keeps it inside the same contract as the
std-only languages — performance without divergence. When diffing against
Rust, the *values* agree to tolerance; the *runtime* is where C++
distinguishes itself.

## 🔗 See also

- [the framework hub](../README.md) — the two-tier picture and the
  contract;
- [`rust/`](../rust/README.md) — the std-only comparison point;
- [`docker/cpp/`](../docker/README.md) — the pinned toolchain image;
- [`section4_kdv/`](section4_kdv/README.md) — the pseudospectral port the
  KdV chapter relies on.


## BLAS provider matrix

| Environment | Provider CMake finds | Note |
|---|---|---|
| Debian/Ubuntu with `libopenblas-dev` | OpenBLAS | the reference configuration |
| Debian/Ubuntu with `liblapack-dev` only | reference LAPACK | slower, values identical |
| macOS with brew LAPACK | Accelerate/OpenBLAS | framework path printed at configure time |
| no BLAS | configuration fails | install a provider; clear `build/` (failed detections are cached) |

## Performance character

Section 3 (AB-Cloud eigen-work) and Section 4 (pseudospectral KdV) are the
heave ports: expect the build's `-O2` defaults to be adequate, and expect
the runtime to be dominated by BLAS-3 and FFT kernels respectively. The
other four sections run in milliseconds. If a port's runtime jumps by an
order of magnitude on identical hardware, suspect a BLAS provider switch —
the configure line prints which one was chosen.

## Contract discipline under performance pressure

The temptation in a performance tier is to fudge the harness: fewer
digits, looser tolerances, fewer assertions. The C++ ports resist it
structurally — the same `check()` helper, the same 15-digit printing, the
same JSON verdict as the std-only tiers, and the
[validator](../tests/README.md) diffs them all against the same reference.
Performance may vary between ports; the *claims* may not.

---

Navigation: [verification](../README.md) · [repository root](../../README.md) · [IPL-RP-1.0](../../LICENSE.md)

*Part of [wild8highlander/navier-stokes-b](https://github.com/wild8highlander/navier-stokes-b) — © 2026 Isaev Iskhak Khamzatovich, all rights reserved.*
