# Ⓜ️ Rust · Section 3 — AB-Cloud

> **Navigation:** [`verification`](../../README.md) › [`rust`](../README.md) › **`section3_ab_cloud`**

![Rust](https://img.shields.io/badge/Rust-1.75+-informational?style=flat-square&logo=rust&logoColor=white) ![License](https://img.shields.io/badge/License-IPL--RP--1.0-red?style=flat-square) ![Section](https://img.shields.io/badge/Section-3-blue?style=flat-square)

The **Rust port of Section 3** — AB-Cloud — the Non-Hermitian Hofstadter Hamiltonian. This folder is the section's slot in the Rust layer of the framework: the file below states exactly the assertions the Python reference makes, in Rust idiom — memory-safe port using `std` only; the crate builds each section as its own binary.

The folder pairs the manifest with `src/` (see sibling folder) — Cargo expects the binary source under `src/main.rs`; the parent crate's `Cargo.toml` wires it as a section binary.

## 🔬 Section Context — Where This Port Sits

**Where it sits.** Section 3 of the framework covers **the 36³ non-Hermitian Hofstadter Hamiltonian with Aharonov–Bohm vortex fluxes**. Its central quantities are spectral construction with σ = 0.5 non-Hermiticity, α = 2.0 AB flux, disorder W = 1.0 and 5 000 embedded Riemann zeta zeros; what this port asserts (or proves) is GUE-consistency of the spectrum (⟨r⟩ gap statistics), gauge invariance of the vortex decoration, and spectral stability under perturbations. The same assertions exist in every peer language of the matrix, each in its own idiom: [Python](../../section3_ab_cloud/python/README.md) · [Lean 4](../../lean4/ResearchPapersVerification/Section3_ABCloud/README.md) · [Coq/Rocq](../../coq/section3_ab_cloud/README.md) · [Isabelle-HOL](../../isabelle/Section3_ABCloud/README.md) · [Agda](../../agda/Section3_ABCloud/README.md) · [C++](../../cpp/section3_ab_cloud/README.md) · [Haskell](../../haskell/Section3_ABCloud/README.md). Agreement between all ports is enforced by the cross-language validator (`../../tests/`) and the `ci-cross-language.yml` workflow.

**What you will see.** Run this port and you get: a banner identifying the section and language; the computed values printed at full precision; one `[PASS]`/`[FAIL]` line per assertion; and a final `JSON: {"section": 3, "language": "rust", "values": {…}, "all_passed": …}` verdict line. Exit status is 0 only when every assertion passed — CI treats anything else as a failure.

## 📂 Contents — What Lives Here

| File | Size | Description |
|---|---|---|
| [`Cargo.toml`](Cargo.toml) | 136 B | [package] name = "section3_ab_cloud" version = "2.0.0" edition = "2021" [[bin]] name = "verify_section3_ab_cloud" path = "src/main.rs" |
| [`src/`](src/) | — | subdirectory with 2 files (see its own README) |

## 🗂 Directory Layout

```
section3_ab_cloud/
├── src/   # 2 files
│   ├── main.rs
│   └── README.md  (this file)
├── Cargo.toml
└── README.md  (this file)
```

## ▶️ How to Run

```bash
cargo run --release --manifest-path verification/rust/Cargo.toml --bin <section>
```

## 🔗 Cross-References

- [Rust layer README](../README.md)
- [Python reference for this section](../../section3_ab_cloud/python/README.md)
- [Framework root](../../README.md)

## 🇷🇺 Brief Summary (Russian Summary)

Rust port of Section 3: one file with the theorems/checks of the "AB-Cloud" section; section context — in the identically named block; build and output — same as in the Rust layer README.

---

<div align="center">

**[⬆ Back to top](#-rust--section-3--ab-cloud)** · 
**[Repository root](../../README.md)**

*Part of [wild8highlander/navier-stokes-b](https://github.com/wild8highlander/navier-stokes-b) · Licensed under [IPL-RP-1.0](https://github.com/wild8highlander/navier-stokes-b/blob/main/LICENSE.md) — All Rights Reserved*

</div>
<!-- doc-enhancer:block v1 (auto-generated block; license files are not affected) -->

---

## 🧭 Navigation and Quick Links (auto)

- 🏠 [Repository root](../../../../README.md)
- 📖 [How the claims are verified](../../../../verification/README.md)
- 📄 [Papers (PDF)](../../../../papers/README.md) · 📚 [Monographs](../../../../docs/README.md) · 🧾 [LaTeX](../../../../src/README.md)
- ⚖️ [IPL-RP-1.0 License](../../../../LICENSE.md) — viewing, a single backup copy, and citation with attribution are permitted; everything else — only with the author's written consent.

*Block added automatically (`doc-enhancer v1`); it is unrelated to the license and does not modify it. Re-running the script does not duplicate the block.*

