# Ⓜ️ C++ — Formal/Numerical Verification Layer

> **Navigation:** [`verification`](../README.md) › **`cpp`**

![C++](https://img.shields.io/badge/C%2B%2B-C++17-informational?style=flat-square&logo=cplusplus&logoColor=white) ![License](https://img.shields.io/badge/License-IPL--RP--1.0-red?style=flat-square) ![Sections](https://img.shields.io/badge/Sections-6-blue?style=flat-square)

This directory carries the **C++17 numerical-verification layer**: one self-contained section program per research topic, orchestrated by a shared `CMakeLists.txt`. The ports use a uniform `check()` harness — every assertion prints `[PASS]`/`[FAIL]` with expected vs actual at 15-digit precision, and `main` ends with the framework's `JSON: {...}` verdict line and a non-zero exit on any failure.

The implementations are deliberately header-light: `std::cmath` arithmetic for Section 1 (computing `b = π/(4π² + 2π√3)` to `double` precision, verifying `sin θ = b`, `cos²θ + sin²θ = 1`), and progressively deeper numerical machinery for the later sections (pseudospectral KdV in Section 4, BLAS/LAPACK-style spectral work in Section 3), matching the roles the root README's language table assigns to C++.

Build everything through CMake (≥ 3.28): `cmake -S . -B build && cmake --build build`, then run each section binary. CI compiles the suite in `ci-extended-languages.yml` and runs the binaries under `ci-cross-language.yml`.

## 🗂 The Six Section Ports

- [`section1_correction_b/`](section1_correction_b/README.md) — Correction b — the Universal Polarization Constant
- [`section2_preprint/`](section2_preprint/README.md) — Preprint NSE — the Regularity Argument Chain
- [`section3_ab_cloud/`](section3_ab_cloud/README.md) — AB-Cloud — the Non-Hermitian Hofstadter Hamiltonian
- [`section4_kdv/`](section4_kdv/README.md) — KdV — Soliton Interactions under the b-Correction
- [`section5_klein_attractor/`](section5_klein_attractor/README.md) — Klein Attractor — Ergodic Dynamics and the NSE Bridge
- [`section6_riemann_zeros/`](section6_riemann_zeros/README.md) — Riemann Zeros — the Hilbert–Pólya Programme

## 📂 Contents — What Lives Here

| File | Size | Description |
|---|---|---|
| [`CMakeLists.txt`](CMakeLists.txt) | 388 B | cmake_minimum_required(VERSION 3.18) project(research_papers_verification_cpp CXX) set(CMAKE_CXX_STANDARD 17) set(CMAKE_CXX_STANDARD_REQUIRED ON) add_compile_options(-Wall -Wextra)… |
| [`section1_correction_b/`](section1_correction_b/) | — | Section 1 port — Correction b — the Universal Polarization Constant |
| [`section2_preprint/`](section2_preprint/) | — | Section 2 port — Preprint NSE — the Regularity Argument Chain |
| [`section3_ab_cloud/`](section3_ab_cloud/) | — | Section 3 port — AB-Cloud — the Non-Hermitian Hofstadter Hamiltonian |
| [`section4_kdv/`](section4_kdv/) | — | Section 4 port — KdV — Soliton Interactions under the b-Correction |
| [`section5_klein_attractor/`](section5_klein_attractor/) | — | Section 5 port — Klein Attractor — Ergodic Dynamics and the NSE Bridge |
| [`section6_riemann_zeros/`](section6_riemann_zeros/) | — | Section 6 port — Riemann Zeros — the Hilbert–Pólya Programme |

## 🗂 Directory Layout

```
cpp/
├── section1_correction_b/   # 2 files
│   ├── main.cpp
│   └── README.md  (this file)
├── section2_preprint/   # 2 files
│   ├── main.cpp
│   └── README.md  (this file)
├── section3_ab_cloud/   # 2 files
│   ├── main.cpp
│   └── README.md  (this file)
├── section4_kdv/   # 2 files
│   ├── main.cpp
│   └── README.md  (this file)
├── section5_klein_attractor/   # 2 files
│   ├── main.cpp
│   └── README.md  (this file)
├── section6_riemann_zeros/   # 2 files
│   ├── main.cpp
│   └── README.md  (this file)
├── CMakeLists.txt
└── README.md  (this file)
```

## ▶️ How to Run

```bash
cd verification/cpp
cmake -S . -B build && cmake --build build && ./build/<target>
```
Build step: `cmake -S . -B build && cmake --build build`.

## 🇷🇺 Краткое резюме (Russian Summary)

**verification/cpp/** — слой верификации на C++ (C++17): лёгкий C++17 с единым харнессом check() и JSON-вердиктом. Шесть портов по разделам (1: Correction b, 2: Preprint NSE, 3: AB-Cloud, 4: KdV, 5: Klein Attractor, 6: Riemann Zeros); единый контракт PASS/JSON; команды сборки — в разделе How to Run.

---

<div align="center">

**[⬆ Back to top](#-c--formalnumerical-verification-layer)** · 
**[Repository root](../README.md)**

*Part of [wild8highlander/navier-stokes-b](https://github.com/wild8highlander/navier-stokes-b) · Licensed under [IPL-RP-1.0](https://github.com/wild8highlander/navier-stokes-b/blob/main/LICENSE.md) — All Rights Reserved*

</div>

---
## 🏗 Build System Details

One CMake project ([`CMakeLists.txt`](CMakeLists.txt)) builds all six section targets. What CMake resolves, in order:

1. a C++17 compiler (GCC ≥ 9, Clang ≥ 10, MSVC 2019+);
2. a BLAS/LAPACK provider — OpenBLAS preferred, then reference LAPACK; the chosen provider is printed during configuration;
3. per-target executables `section1_correction_b` … `section6_riemann_zeros`.

```bash
cmake -S verification/cpp -B build          # read the provider line in the output
cmake --build build -j                      # parallel build
./build/section1_correction_b               # run any target directly
```

## 🧮 The Uniform check() Harness

Every C++ port shares the same harness shape: a `check(name, expected, actual, tol)` helper that prints `[PASS]/[FAIL]` lines, accumulates failures, and emits the JSON verdict at the end. The harness is the C++ face of the framework's output contract — the validator in [`tests/`](../tests/README.md) consumes its output exactly like every other language's.

## ⚡ Performance Notes

The AB-Cloud eigenvalue work (Section 3) is the heaviest of the six; the KdV pseudospectral solver (Section 4) is FFT-dominated. Typical first-build times: 1–3 minutes (BLAS detection dominates configuration, not compilation). If configuration reports "no BLAS found", install the development packages (`libopenblas-dev`/`liblapack-dev` on Debian–Ubuntu) and clear the `build/` cache — CMake caches failed detections aggressively.

---
## 🎯 What C++ Is For Here

The C++ tier is the performance witness and the KdV workhorse: BLAS/LAPACK-backed eigen-routines and the FFT pseudospectral solver live here. Its check() harness keeps it inside the same contract as the std-only languages — performance without contract drift. When diffing against Rust, the values agree to tolerance; the *runtime* is where C++ distinguishes itself.

---
## 🔗 See Also

- [`CMakeLists.txt`](CMakeLists.txt) — the single build entry;
- [`rust/`](../rust/README.md) — the std-only comparison point;
- performance notes in the root README's [Appendix E](../../README.md#-appendix-e--performance-notes).

<!-- doc-enhancer:block v1 (автоматический блок; файлы лицензии не затрагиваются) -->

---

## 🧭 Навигация и быстрые ссылки (auto)

- 🏠 [Корень репозитория](../../../README.md)
- 📖 [Как верифицируются утверждения](../../../verification/README.md)
- 📄 [Статьи (PDF)](../../../papers/README.md) · 📚 [Монографии](../../../docs/README.md) · 🧾 [LaTeX](../../../src/README.md)
- ⚖️ [Лицензия IPL-RP-1.0](../../../LICENSE.md) — просмотр, одна резервная копия и цитирование с атрибуцией разрешены; остальное — только с письменного согласия автора.

*Блок добавлен автоматически (`doc-enhancer v1`); к лицензии отношения не имеет и её не изменяет. Повторный запуск скрипта блок не дублирует.*

