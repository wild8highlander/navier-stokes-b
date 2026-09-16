# 🦀 `rust/…/section2_*/src/` — the Binary Source

> **Navigation:** [`rust`](../../../verification/rust/README.md) › [section 2](../README.md) › **`src`**

![Rust](https://img.shields.io/badge/Rust-1.75%2B-DEA584?style=flat-square&logo=rust&logoColor=white) ![License](https://img.shields.io/badge/License-IPL--RP--1.0-red?style=flat-square)

The **`main.rs` of the Section 2 Rust port** — Preprint NSE — the Regularity Argument Chain. One std-only
module: it computes the section's quantities, asserts the properties
through the shared `check(name, expected, actual)` helper at `{:15e}`
precision, prints the `JSON:` verdict and exits non-zero on any failure.

| File | Description |
|---|---|
| [`main.rs`](main.rs) | the binary's single module — zero external crates |

## Run

```bash
cd verification/rust
cargo run --release -p section2_preprint
```

Peers of this port: [Python](../../../../../verification/section2_preprint/README.md) · [Lean 4](../../../../../verification/lean4/ResearchPapersVerification/Section2_PreprintNSE/README.md) · [Coq/Rocq](../../../../../verification/coq/section2_preprint/README.md) · [Isabelle-HOL](../../../../../verification/isabelle/Section2_PreprintNSE/README.md) · [Agda](../../../../../verification/agda/Section2_PreprintNSE/README.md) · [C++](../../../../../verification/cpp/section2_preprint/README.md) · [Haskell](../../../../../verification/haskell/Section2_PreprintNSE/README.md).

---

---

Navigation: [section 2](../README.md) · [rust layer](../../../verification/rust/README.md) · [IPL-RP-1.0](../../../../../LICENSE.md)

*Part of [wild8highlander/navier-stokes-b](https://github.com/wild8highlander/navier-stokes-b) - (c) 2026 Isaev Iskhak Khamzatovich, all rights reserved.*

