# Ⓜ️ `rust/` — the Rust Numerical Verification Layer

> **Navigation:** [`verification`](../README.md) › **`rust`**

![Rust](https://img.shields.io/badge/Rust-1.75%2B-DEA584?style=flat-square&logo=rust&logoColor=white)
![Sections](https://img.shields.io/badge/Sections-6-9558B2?style=flat-square)
![Dependencies](https://img.shields.io/badge/Crates-zero_std_only-2EA043?style=flat-square&logo=rust&logoColor=white)
![License](https://img.shields.io/badge/License-IPL--RP--1.0-red?style=flat-square)

This directory carries the **Rust (1.75+) numerical-verification layer**:
one Cargo workspace, with a separate crate and binary per research
section, built with Cargo. The ports use **`std` only — no external
crates** — so the dependency graph is trivial and auditable, and the
memory-safety guarantees come for free.

Every section binary implements the framework's output contract: a
`check(name, expected, actual)` helper printing `[PASS]`/`[FAIL]` at
`{:15e}` precision, the final `JSON: {...}` verdict line, and `exit(1)`
semantics on any failure. Section 1 computes `b` from
`std::f64::consts::PI` via the closed form `b = π/(4π² + 2π√3)`
(algebraically identical to `1/(4π + 2√3)` = 0.06238119…), checks
positivity and bounds, and verifies the trigonometric identity chain via
`asin`/`cos`/`sin`.

## The six section ports

| Crate | Directory | Section | Binary |
|---|---|---|---|
| `section1_correction_b` | [`section1_correction_b/`](section1_correction_b/README.md) | 1 | prints b, asserts the four properties |
| `section2_preprint` | [`section2_preprint/`](section2_preprint/README.md) | 2 | twist unitarity chain |
| `section3_ab_cloud` | [`section3_ab_cloud/`](section3_ab_cloud/README.md) | 3 | Hofstadter structural checks |
| `section4_kdv` | [`section4_kdv/`](section4_kdv/README.md) | 4 | soliton conservation (std-only, FFT-free formulation) |
| `section5_klein_attractor` | [`section5_klein_attractor/`](section5_klein_attractor/README.md) | 5 | invariant statistics |
| `section6_riemann_zeros` | [`section6_riemann_zeros/`](section6_riemann_zeros/README.md) | 6 | gap-ratio diagnostics |

Each section folder carries its own `src/` with the binary's `main.rs`
(and a README), plus its own `Cargo.toml`.

## Contents

| File | Description |
|---|---|
| [`Cargo.toml`](Cargo.toml) | the workspace: resolver "2", the six member crates |

## How to run

```bash
cd verification/rust
cargo run --release                              # whole chain, all six sections
cargo run --release -p section1_correction_b     # one section
cargo test --release                             # unit tests alongside the contract checks
```

`--release` is the supported mode everywhere in the documentation; debug
builds are noticeably slower on the heavier sections and are only useful
when debugging the ports themselves. CI builds the workspace in the
extended-languages workflow and runs it under the cross-language
workflow; the pinned image lives at
[`docker/rust/`](../docker/README.md).

## 🎯 What Rust proves

The Rust ports prove that the sections do not need *anything* — no BLAS,
no NumPy, no standard scientific stack. Six crates, std-only, and the
contract still holds. That makes Rust the **supply-chain audit's favourite
witness**: with zero dependencies there is nothing to trust but the code
and the standard library, and `cargo vet`-style reviews reduce to reading
six small `main.rs` files. Combined with the memory guarantees, the Rust
tier also demonstrates that the framework's claims do not depend on
undefined behaviour anywhere in the arithmetic path.

## 🔗 See also

- [the framework hub](../README.md) — the two-tier picture and the
  contract;
- [`cpp/`](../cpp/README.md) — the BLAS-backed counterpart;
- [`haskell/`](../haskell/README.md) — the pure-functional witness;
- [`tests/`](../tests/README.md) — the validator that consumes these
  ports' JSON verdicts.


## The check() helper, annotated

```rust
fn check(name: &str, expected: f64, actual: f64, tol: f64) -> bool {
    let ok = (actual - expected).abs() <= tol;
    println!("[{}] {}: expected={:.15e}, actual={:.15e}",
             if ok { "PASS" } else { "FAIL" }, name, expected, actual);
    ok
}
```

Accumulate the booleans, print the `JSON:` verdict with `all_passed`, and
`std::process::exit(1)` on any failure — that is the whole harness, and
every port's `main` is a straight-line script of `check` calls. Reading a
Rust port end-to-end takes about the same time as running it.

## CI wiring

The extended-languages workflow builds the workspace (`cargo build
--release --locked`-equivalent semantics with zero deps to lock); the
cross-language workflow runs each binary and feeds the verdicts to the
[validator](../tests/README.md). Because there are no external crates,
neither workflow needs a registry cache — cold runners build the ring in
seconds.

## When to reach for the Rust port

- auditing the **supply chain** of a claim (zero deps is the answer);
- checking that a claim survives **memory-safety** discipline;
- diffing against C++ where performance differs but values must not.

---

Navigation: [verification](../README.md) · [repository root](../../README.md) · [IPL-RP-1.0](../../LICENSE.md)

*Part of [wild8highlander/navier-stokes-b](https://github.com/wild8highlander/navier-stokes-b) — © 2026 Isaev Iskhak Khamzatovich, all rights reserved.*
