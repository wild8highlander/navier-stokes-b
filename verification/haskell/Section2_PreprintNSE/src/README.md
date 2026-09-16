# Ⓜ️ Haskell · Section 2 · src — the Section Binary

> **Navigation:** [`verification`](../../../README.md) › [`haskell`](../../README.md) › [`Section2_PreprintNSE`](../README.md) › **`src`**

![Haskell](https://img.shields.io/badge/Haskell-9.4-informational?style=flat-square&logo=haskell&logoColor=white) ![License](https://img.shields.io/badge/License-IPL--RP--1.0-red?style=flat-square)

The **source folder of the Section 2 Haskell binary** — the executable module that prints the section banner, computes the section's quantities, asserts its properties with `[PASS]`/`[FAIL]` lines, and ends with the framework's `JSON:` verdict. Written in idiomatic, dependency-free Haskell (9.4); the parent folder holds the build wiring.

## 🔬 Section Context — Where This Port Sits

**Where it sits.** Section 2 of the framework covers **the analytical chain behind global regularity of the 3D Navier–Stokes equations**. Its central quantities are the stabilisation mechanism induced by θ_b ≈ 7.07° and the 3.5× reduction of the BKM blow-up criterion integral; what this port asserts (or proves) is structural lemmas of the preprint: positivity and scale of the correction, unit-norm rotation axis, and the energy-estimate scaffolding. The same assertions exist in every peer language of the matrix, each in its own idiom: [Python](../../../section2_preprint/python/README.md) · [Lean 4](../../../lean4/ResearchPapersVerification/Section2_PreprintNSE/README.md) · [Coq/Rocq](../../../coq/section2_preprint/README.md) · [Isabelle-HOL](../../../isabelle/Section2_PreprintNSE/README.md) · [Agda](../../../agda/Section2_PreprintNSE/README.md) · [C++](../../../cpp/section2_preprint/README.md) · [Rust](../../../rust/section2_preprint/README.md). Agreement between all ports is enforced by the cross-language validator (`../../../tests/`) and the `ci-cross-language.yml` workflow.

**What you will see.** Run this port and you get: a banner identifying the section and language; the computed values printed at full precision; one `[PASS]`/`[FAIL]` line per assertion; and a final `JSON: {"section": 2, "language": "haskell", "values": {…}, "all_passed": …}` verdict line. Exit status is 0 only when every assertion passed — CI treats anything else as a failure.

## 📂 Contents — What Lives Here

| File | Size | Description |
|---|---|---|
| [`Main.hs`](Main.hs) | 235 B | Section 2 Haskell source — the complete section verifier |

## ▶️ How to Run

```bash
cd verification/haskell && cabal build && cabal run <section>
```

## 🔗 Cross-References

- [Section folder](../README.md)
- [Haskell layer](../../README.md)

## 📝 Summary

Source of the Section 2 Haskell binary (Main.hs); the PASS/JSON contract is the same as in all ports.

---

<div align="center">

**[⬆ Back to top](#-haskell--section-2--src--the-section-binary)** · 
**[Repository root](../../../README.md)**

*Part of [wild8highlander/navier-stokes-b](https://github.com/wild8highlander/navier-stokes-b) · Licensed under [IPL-RP-1.0](https://github.com/wild8highlander/navier-stokes-b/blob/main/LICENSE.md) — All Rights Reserved*

</div>
<!-- doc-enhancer:block v1 (auto-generated block; license files are not touched) -->

---

## 🧭 Navigation and Quick Links (auto)

- 🏠 [Repository root](../../../../../README.md)
- 📖 [How the claims are verified](../../../../../verification/README.md)
- 📄 [Papers (PDF)](../../../../../papers/README.md) · 📚 [Monographs](../../../../../docs/README.md) · 🧾 [LaTeX](../../../../../src/README.md)
- ⚖️ [IPL-RP-1.0 License](../../../../../LICENSE.md) — viewing, a single backup copy, and citation with attribution are permitted; everything else requires the author's written permission.

*Block added automatically (`doc-enhancer v1`); it is unrelated to the license and does not modify it. Re-running the script does not duplicate the block.*

