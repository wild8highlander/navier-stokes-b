# 🦀 `rust/…/section6_*/src/` — the Binary Source

> **Navigation:** [`rust`](../../README.md) › [section 6](../README.md) › **`src`**

![Rust](https://img.shields.io/badge/Rust-1.75%2B-DEA584?style=flat-square&logo=rust&logoColor=white) ![License](https://img.shields.io/badge/License-IPL--RP--1.0-red?style=flat-square)

The **`main.rs` of the Section 6 Rust port** — Riemann Zeros — the Hilbert–Pólya Programme. One std-only
module: it computes the section's quantities, asserts the properties
through the shared `check(name, expected, actual)` helper at `{:15e}`
precision, prints the `JSON:` verdict and exits non-zero on any failure.

| File | Description |
|---|---|
| [`main.rs`](main.rs) | the binary's single module — zero external crates |

## Run

```bash
cd verification/rust
cargo run --release -p section6_riemann_zeros
```

Peers of this port: [Python](../../../section6_riemann_zeros/README.md) · [Lean 4](../../../lean4/ResearchPapersVerification/Section6_RiemannZeros/README.md) · [Coq/Rocq](../../../coq/section6_riemann_zeros/README.md) · [Isabelle-HOL](../../../isabelle/Section6_RiemannZeros/README.md) · [Agda](../../../agda/Section6_RiemannZeros/README.md) · [C++](../../../cpp/section6_riemann_zeros/README.md) · [Haskell](../../../haskell/Section6_RiemannZeros/README.md).

---

---

Navigation: [section 6](../README.md) · [rust layer](../../README.md) · [IPL-RP-1.0](../../../../LICENSE.md)

*Part of [wild8highlander/navier-stokes-b](https://github.com/wild8highlander/navier-stokes-b) - (c) 2026 Isaev Iskhak Khamzatovich, all rights reserved.*

