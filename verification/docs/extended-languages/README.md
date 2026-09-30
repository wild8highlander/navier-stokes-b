# 📚 `verification/docs/extended-languages/` — the Extended Toolchain Ring

> **Navigation:** [`docs`](../README.md) › **`extended-languages`**

![Scope](https://img.shields.io/badge/Scope-Extended_languages-9558B2?style=flat-square) ![License](https://img.shields.io/badge/License-IPL--RP--1.0-red?style=flat-square)

Notes on the **extended ring** — the languages beyond the stdlib-Python
reference: C++17, Rust, Haskell and Julia on the computational side, plus
the four formal kernels (Lean 4, Coq, Isabelle, Agda). What "extended"
means operationally: toolchain-pinned, Docker-imaged, CI-built, and
toolchain-locked in the test suite (auto-skip when absent locally).

## The ring at a glance

| Language | Build entry | Pinned by | Docker image |
|---|---|---|---|
| C++17 | `cmake -S verification/cpp -B build` | CMake ≥ 3.18 | [`docker/cpp/`](../../docker/README.md) |
| Rust | `cargo run --release` | rust 1.75+ | [`docker/rust/`](../../docker/README.md) |
| Haskell | `cabal build` | GHC 9.4 | [`docker/haskell/`](../../docker/README.md) |
| Julia | `julia verify_all.jl` | stdlib-only | (no image needed) |
| Lean 4 | `lake build` | `lean-toolchain` pin | [`docker/lean4/`](../../docker/README.md) |
| Coq | `coq_makefile && make` | 8.18 | [`docker/coq/`](../../docker/README.md) |
| Isabelle | `isabelle build -D .` | 2024 | [`docker/isabelle/`](../../docker/README.md) |
| Agda | `agda --safe` | 2.6 | [`docker/agda/`](../../docker/README.md) |

CI compiles the ring where runners allow and always runs the stdlib
subset; the [validator](../../tests/README.md) consumes whatever verdicts
exist and reports the covered matrix.

---

---

Navigation: [docs](../README.md) · [docker](../../docker/README.md) · [tests](../../tests/README.md) · [IPL-RP-1.0](../../../LICENSE.md)

*Part of [wild8highlander/navier-stokes-b](https://github.com/wild8highlander/navier-stokes-b) - (c) 2026 Isaev Iskhak Khamzatovich, all rights reserved.*

