# 🦀 `rust/…/section3_*/src/` — the Binary Source

> **Navigation:** [`rust`](../../../verification/rust/README.md) › [section 3](../README.md) › **`src`**

![Rust](https://img.shields.io/badge/Rust-1.75%2B-DEA584?style=flat-square&logo=rust&logoColor=white) ![License](https://img.shields.io/badge/License-IPL--RP--1.0-red?style=flat-square)

The **`main.rs` of the Section 3 Rust port** — AB-Cloud — the Non-Hermitian Hofstadter Hamiltonian. One std-only
module: it computes the section's quantities, asserts the properties
through the shared `check(name, expected, actual)` helper at `{:15e}`
precision, prints the `JSON:` verdict and exits non-zero on any failure.

| File | Description |
|---|---|
| [`main.rs`](main.rs) | the binary's single module — zero external crates |

## Run

```bash
cd verification/rust
cargo run --release -p section3_ab_cloud
```

Peers of this port: [Python](../../../../../verification/section3_ab_cloud/README.md) · [Lean 4](../../../../../verification/lean4/ResearchPapersVerification/Section3_ABCloud/README.md) · [Coq/Rocq](../../../../../verification/coq/section3_ab_cloud/README.md) · [Isabelle-HOL](../../../../../verification/isabelle/Section3_ABCloud/README.md) · [Agda](../../../../../verification/agda/Section3_ABCloud/README.md) · [C++](../../../../../verification/cpp/section3_ab_cloud/README.md) · [Haskell](../../../../../verification/haskell/Section3_ABCloud/README.md).

---

---

Navigation: [section 3](../README.md) · [rust layer](../../../verification/rust/README.md) · [IPL-RP-1.0](../../../../../LICENSE.md)

*Part of [wild8highlander/navier-stokes-b](https://github.com/wild8highlander/navier-stokes-b) - (c) 2026 Isaev Iskhak Khamzatovich, all rights reserved.*

