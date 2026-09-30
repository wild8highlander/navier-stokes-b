# 🦀 `rust/…/section4_*/src/` — the Binary Source

> **Navigation:** [`rust`](../../README.md) › [section 4](../README.md) › **`src`**

![Rust](https://img.shields.io/badge/Rust-1.75%2B-DEA584?style=flat-square&logo=rust&logoColor=white) ![License](https://img.shields.io/badge/License-IPL--RP--1.0-red?style=flat-square)

The **`main.rs` of the Section 4 Rust port** — KdV — Soliton Interactions under the b-Correction. One std-only
module: it computes the section's quantities, asserts the properties
through the shared `check(name, expected, actual)` helper at `{:15e}`
precision, prints the `JSON:` verdict and exits non-zero on any failure.

| File | Description |
|---|---|
| [`main.rs`](main.rs) | the binary's single module — zero external crates |

## Run

```bash
cd verification/rust
cargo run --release -p section4_kdv
```

Peers of this port: [Python](../../../section4_kdv/README.md) · [Lean 4](../../../lean4/ResearchPapersVerification/Section4_KdV/README.md) · [Coq/Rocq](../../../coq/section4_kdv/README.md) · [Isabelle-HOL](../../../isabelle/Section4_KdV/README.md) · [Agda](../../../agda/Section4_KdV/README.md) · [C++](../../../cpp/section4_kdv/README.md) · [Haskell](../../../haskell/Section4_KdV/README.md).

---

---

Navigation: [section 4](../README.md) · [rust layer](../../README.md) · [IPL-RP-1.0](../../../../LICENSE.md)

*Part of [wild8highlander/navier-stokes-b](https://github.com/wild8highlander/navier-stokes-b) - (c) 2026 Isaev Iskhak Khamzatovich, all rights reserved.*

