# Ⓜ️ Rust — Formal/Numerical Verification Layer

> **Navigation:** [`verification`](../README.md) › **`rust`**

![Rust](https://img.shields.io/badge/Rust-1.75+-informational?style=flat-square&logo=rust&logoColor=white) ![License](https://img.shields.io/badge/License-IPL--RP--1.0-red?style=flat-square) ![Sections](https://img.shields.io/badge/Sections-6-blue?style=flat-square)

This directory carries the **Rust (1.75+) numerical-verification layer**: one crate for the whole framework, with a separate binary per research section (`src/bin`-style section folders), built with Cargo. The ports use `std` only — no external crates — so the dependency graph is trivial and auditable, and the memory-safety guarantees come for free.

Every section binary implements the framework's output contract: a `check(name, expected, actual)` helper printing `[PASS]`/`[FAIL]` at `{:15e}` precision, the `JSON:` verdict line, and `exit(1)` semantics on failure. Section 1 computes `b` from `std::f64::consts::PI`, checks positivity/bounds, and verifies the trigonometric identity chain via `asin`/`cos`/`sin`.

Run a section with `cargo run --release --bin <section>` (or `cargo run --release` for the default); `Cargo.toml` wires the release profile for speed. CI builds the crate in `ci-extended-languages.yml` and runs it under `ci-cross-language.yml`.

Each section folder carries its own `src/` with the binary's `main.rs`.

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
| [`Cargo.toml`](Cargo.toml) | 240 B | [workspace] resolver = "2" members = [ "section1_correction_b", "section2_preprint", "section3_ab_cloud", "section4_kdv", "section5_klein_attractor", "section6_riemann_zeros", ] [w… |
| [`section1_correction_b/`](section1_correction_b/) | — | Section 1 port — Correction b — the Universal Polarization Constant |
| [`section2_preprint/`](section2_preprint/) | — | Section 2 port — Preprint NSE — the Regularity Argument Chain |
| [`section3_ab_cloud/`](section3_ab_cloud/) | — | Section 3 port — AB-Cloud — the Non-Hermitian Hofstadter Hamiltonian |
| [`section4_kdv/`](section4_kdv/) | — | Section 4 port — KdV — Soliton Interactions under the b-Correction |
| [`section5_klein_attractor/`](section5_klein_attractor/) | — | Section 5 port — Klein Attractor — Ergodic Dynamics and the NSE Bridge |
| [`section6_riemann_zeros/`](section6_riemann_zeros/) | — | Section 6 port — Riemann Zeros — the Hilbert–Pólya Programme |

## 🗂 Directory Layout

```
rust/
├── section1_correction_b/   # 4 files
│   ├── src/   # 2 files
│   │   ├── main.rs
│   │   └── README.md  (this file)
│   ├── Cargo.toml
│   └── README.md  (this file)
├── section2_preprint/   # 4 files
│   ├── src/   # 2 files
│   │   ├── main.rs
│   │   └── README.md  (this file)
│   ├── Cargo.toml
│   └── README.md  (this file)
├── section3_ab_cloud/   # 4 files
│   ├── src/   # 2 files
│   │   ├── main.rs
│   │   └── README.md  (this file)
│   ├── Cargo.toml
│   └── README.md  (this file)
├── section4_kdv/   # 4 files
│   ├── src/   # 2 files
│   │   ├── main.rs
│   │   └── README.md  (this file)
│   ├── Cargo.toml
│   └── README.md  (this file)
├── section5_klein_attractor/   # 4 files
│   ├── src/   # 2 files
│   │   ├── main.rs
│   │   └── README.md  (this file)
│   ├── Cargo.toml
│   └── README.md  (this file)
├── section6_riemann_zeros/   # 4 files
│   ├── src/   # 2 files
│   │   ├── main.rs
│   │   └── README.md  (this file)
│   ├── Cargo.toml
│   └── README.md  (this file)
├── Cargo.toml
└── README.md  (this file)
```

## ▶️ How to Run

```bash
cd verification/rust
cargo run --release
```
Build step: `cargo build --release`.

## 📝 Summary

**verification/rust/** — the Rust (1.75+) verification layer: a memory-safe std-only port; each section is a separate binary. Six per-section ports (1: Correction b, 2: Preprint NSE, 3: AB-Cloud, 4: KdV, 5: Klein Attractor, 6: Riemann Zeros); the uniform PASS/JSON contract; build commands — see the How to Run section.

---

<div align="center">

**[⬆ Back to top](#-rust--formalnumerical-verification-layer)** · 
**[Repository root](../README.md)**

*Part of [wild8highlander/navier-stokes-b](https://github.com/wild8highlander/navier-stokes-b) · Licensed under [IPL-RP-1.0](https://github.com/wild8highlander/navier-stokes-b/blob/main/LICENSE.md) — All Rights Reserved*

</div>

---
## 🦀 Workspace Anatomy

One workspace ([`Cargo.toml`](Cargo.toml)), six packages, zero external crates:

| Package | Section | Binary |
|---|---|---|
| `section1_correction_b` | 1 | prints b, asserts the four properties |
| `section2_preprint` | 2 | twist unitarity chain |
| `section3_ab_cloud` | 3 | Hofstadter structural checks |
| `section4_kdv` | 4 | soliton conservation (std-only FFT-free formulation) |
| `section5_klein_attractor` | 5 | invariant statistics |
| `section6_riemann_zeros` | 6 | gap-ratio diagnostics |

The std-only policy is the Rust face of the framework's hermeticity: no `ndarray`, no `num_cpus`, nothing — the ports are auditable by reading them, and supply-chain risk is zero by construction.

## 🔁 Running Patterns

```bash
cargo run --release                              # whole chain, all six sections
cargo run --release -p section1_correction_b     # one section
cargo test --release                             # unit tests alongside the contract checks
```

`--release` is the supported mode everywhere in the documentation; debug builds are noticeably slower on the heavier sections and are only useful when debugging the ports themselves.

---
## 🎯 What Rust Proves

The Rust ports prove the sections do not need *anything* — no BLAS, no NumPy, no standard scientific stack. Six packages, std-only, and the contract still holds. That makes Rust the supply-chain audit's favourite witness: with zero dependencies, there is nothing to trust but the code and the standard library.

---
## 🔗 See Also

- the workspace [`Cargo.toml`](Cargo.toml) — package registry;
- [`cpp/`](../cpp/README.md) — the BLAS-backed counterpart;
- [`tests/`](../tests/README.md) — the validator that consumes these ports' JSON.

<!-- doc-enhancer:block v1 (auto-inserted block; license files are not touched) -->

---

## 🧭 Navigation and Quick Links (auto)

- 🏠 [Repository root](../../../README.md)
- 📖 [How the claims are verified](../../../verification/README.md)
- 📄 [Papers (PDF)](../../../papers/README.md) · 📚 [Monographs](../../../docs/README.md) · 🧾 [LaTeX](../../../src/README.md)
- ⚖️ [IPL-RP-1.0 License](../../../LICENSE.md) — viewing, one backup copy and citation with attribution are allowed; everything else only with the Author's written consent.

*Block inserted automatically (`doc-enhancer v1`); it is not part of the license and does not modify it. Re-running the script does not duplicate the block.*

