# 🦀 `rust/…/section5_*/src/` — the Binary Source

> **Navigation:** [`rust`](../../../verification/rust/README.md) › [section 5](../README.md) › **`src`**

![Rust](https://img.shields.io/badge/Rust-1.75%2B-DEA584?style=flat-square&logo=rust&logoColor=white) ![License](https://img.shields.io/badge/License-IPL--RP--1.0-red?style=flat-square)

The **`main.rs` of the Section 5 Rust port** — Klein Attractor — Ergodic Dynamics and the NSE Bridge. One std-only
module: it computes the section's quantities, asserts the properties
through the shared `check(name, expected, actual)` helper at `{:15e}`
precision, prints the `JSON:` verdict and exits non-zero on any failure.

| File | Description |
|---|---|
| [`main.rs`](main.rs) | the binary's single module — zero external crates |

## Run

```bash
cd verification/rust
cargo run --release -p section5_klein_attractor
```

Peers of this port: [Python](../../../../../verification/section5_klein_attractor/README.md) · [Lean 4](../../../../../verification/lean4/ResearchPapersVerification/Section5_KleinAttractor/README.md) · [Coq/Rocq](../../../../../verification/coq/section5_klein_attractor/README.md) · [Isabelle-HOL](../../../../../verification/isabelle/Section5_KleinAttractor/README.md) · [Agda](../../../../../verification/agda/Section5_KleinAttractor/README.md) · [C++](../../../../../verification/cpp/section5_klein_attractor/README.md) · [Haskell](../../../../../verification/haskell/Section5_KleinAttractor/README.md).

---

---

Navigation: [section 5](../README.md) · [rust layer](../../../verification/rust/README.md) · [IPL-RP-1.0](../../../../../LICENSE.md)

*Part of [wild8highlander/navier-stokes-b](https://github.com/wild8highlander/navier-stokes-b) - (c) 2026 Isaev Iskhak Khamzatovich, all rights reserved.*

