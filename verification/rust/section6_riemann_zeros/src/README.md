# Ⓜ️ Haskell · Section 6 · src — the Section Binary

> **Navigation:** [`verification`](../../../README.md) › [`rust`](../../README.md) › [`section6_riemann_zeros`](../README.md) › **`src`**

![Rust](https://img.shields.io/badge/Rust-1.75+-informational?style=flat-square&logo=rust&logoColor=white) ![License](https://img.shields.io/badge/License-IPL--RP--1.0-red?style=flat-square)

The **source folder of the Section 6 Haskell binary** — the executable module that prints the section banner, computes the section's quantities, asserts its properties with `[PASS]`/`[FAIL]` lines, and ends with the framework's `JSON:` verdict. Written in idiomatic, dependency-free Haskell (1.75+); the parent folder holds the build wiring.

## 🔬 Section Context — Where This Port Sits

**Where it sits.** Section 6 of the framework covers **the spectral correspondence between the AB-Cloud and the non-trivial zeros of the Riemann zeta function**. Its central quantities are the Hilbert–Pólya realisation, the Montgomery–Dyson GUE correspondence and the statistical identity of the two spectra; what this port asserts (or proves) is spectral-correspondence identities and the statistical machinery (⟨r⟩, KS, permutation tests) in constructive and classical form. The same assertions exist in every peer language of the matrix, each in its own idiom: [Python](../../../section6_riemann_zeros/python/README.md) · [Lean 4](../../../lean4/ResearchPapersVerification/Section6_RiemannZeros/README.md) · [Coq/Rocq](../../../coq/section6_riemann_zeros/README.md) · [Isabelle-HOL](../../../isabelle/Section6_RiemannZeros/README.md) · [Agda](../../../agda/Section6_RiemannZeros/README.md) · [C++](../../../cpp/section6_riemann_zeros/README.md) · [Haskell](../../../haskell/Section6_RiemannZeros/README.md). Agreement between all ports is enforced by the cross-language validator (`../../../tests/`) and the `ci-cross-language.yml` workflow.

**What you will see.** Run this port and you get: a banner identifying the section and language; the computed values printed at full precision; one `[PASS]`/`[FAIL]` line per assertion; and a final `JSON: {"section": 6, "language": "rust", "values": {…}, "all_passed": …}` verdict line. Exit status is 0 only when every assertion passed — CI treats anything else as a failure.

## 📂 Contents — What Lives Here

| File | Size | Description |
|---|---|---|
| [`main.rs`](main.rs) | 927 B | Section 6 Haskell source — the complete section verifier |

## ▶️ How to Run

```bash
cargo run --release --manifest-path verification/rust/Cargo.toml --bin <section>
```

## 🔗 Cross-References

- [Section folder](../README.md)
- [Haskell layer](../../README.md)

## 🇷🇺 Brief Summary (Russian Summary)

Source code of the Section 6 Haskell binary (main.rs); the PASS/JSON contract is the same as in all ports.

---

<div align="center">

**[⬆ Back to top](#-haskell--section-6--src--the-section-binary)** · 
**[Repository root](../../../README.md)**

*Part of [wild8highlander/navier-stokes-b](https://github.com/wild8highlander/navier-stokes-b) · Licensed under [IPL-RP-1.0](https://github.com/wild8highlander/navier-stokes-b/blob/main/LICENSE.md) — All Rights Reserved*

</div>
<!-- doc-enhancer:block v1 (auto-generated block; license files are not affected) -->

---

## 🧭 Navigation and Quick Links (auto)

- 🏠 [Repository root](../../../../../README.md)
- 📖 [How the claims are verified](../../../../../verification/README.md)
- 📄 [Papers (PDF)](../../../../../papers/README.md) · 📚 [Monographs](../../../../../docs/README.md) · 🧾 [LaTeX](../../../../../src/README.md)
- ⚖️ [IPL-RP-1.0 License](../../../../../LICENSE.md) — viewing, a single backup copy, and citation with attribution are permitted; everything else — only with the author's written consent.

*Block added automatically (`doc-enhancer v1`); it is unrelated to the license and does not modify it. Re-running the script does not duplicate the block.*

