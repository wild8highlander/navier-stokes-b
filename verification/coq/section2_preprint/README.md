# Ⓜ️ Coq/Rocq · Section 2 — Preprint NSE

> **Navigation:** [`verification`](../../README.md) › [`coq`](../README.md) › **`section2_preprint`**

![Coq/Rocq](https://img.shields.io/badge/Coq/Rocq-8.18-informational?style=flat-square&logo=ocaml&logoColor=white) ![License](https://img.shields.io/badge/License-IPL--RP--1.0-red?style=flat-square) ![Section](https://img.shields.io/badge/Section-2-blue?style=flat-square)

The **Coq/Rocq port of Section 2** — Preprint NSE — the Regularity Argument Chain. This folder is the section's slot in the Coq/Rocq layer of the framework: the file below states exactly the assertions the Python reference makes, in Coq/Rocq idiom — proofs built on the standard `Reals` library with `lra`/`nra` automation.

## 🔬 Section Context — Where This Port Sits

**Where it sits.** Section 2 of the framework covers **the analytical chain behind global regularity of the 3D Navier–Stokes equations**. Its central quantities are the stabilisation mechanism induced by θ_b ≈ 7.07° and the 3.5× reduction of the BKM blow-up criterion integral; what this port asserts (or proves) is structural lemmas of the preprint: positivity and scale of the correction, unit-norm rotation axis, and the energy-estimate scaffolding. The same assertions exist in every peer language of the matrix, each in its own idiom: [Python](../../section2_preprint/python/README.md) · [Lean 4](../../lean4/ResearchPapersVerification/Section2_PreprintNSE/README.md) · [Isabelle-HOL](../../isabelle/Section2_PreprintNSE/README.md) · [Agda](../../agda/Section2_PreprintNSE/README.md) · [C++](../../cpp/section2_preprint/README.md) · [Rust](../../rust/section2_preprint/README.md) · [Haskell](../../haskell/Section2_PreprintNSE/README.md). Agreement between all ports is enforced by the cross-language validator (`../../tests/`) and the `ci-cross-language.yml` workflow.

**What you will see.** Run this port and you get: a banner identifying the section and language; the computed values printed at full precision; one `[PASS]`/`[FAIL]` line per assertion; and a final `JSON: {"section": 2, "language": "coq", "values": {…}, "all_passed": …}` verdict line. Exit status is 0 only when every assertion passed — CI treats anything else as a failure.

## 📂 Contents — What Lives Here

| File | Size | Description |
|---|---|---|
| [`ProofChain.v`](ProofChain.v) | 737 B | Coq proof development |

## ▶️ How to Run

```bash
cd verification/coq && coqc <section-file>.v         # per file
```

## 🔗 Cross-References

- [Coq/Rocq layer README](../README.md)
- [Python reference for this section](../../section2_preprint/python/README.md)
- [Framework root](../../README.md)

## 🇷🇺 Brief Summary (Russian Summary)

Coq/Rocq port of Section 2: a single file with the theorems/checks of the “Preprint NSE” section; the section context is given in the block of the same name; build and output follow the Coq/Rocq layer README.

---

<div align="center">

**[⬆ Back to top](#-coqrocq--section-2--preprint-nse)** · 
**[Repository root](../../README.md)**

*Part of [wild8highlander/navier-stokes-b](https://github.com/wild8highlander/navier-stokes-b) · Licensed under [IPL-RP-1.0](https://github.com/wild8highlander/navier-stokes-b/blob/main/LICENSE.md) — All Rights Reserved*

</div>
<!-- doc-enhancer:block v1 (automatic block; license files are not affected) -->

---

## 🧭 Navigation and Quick Links (auto)

- 🏠 [Repository root](../../../../README.md)
- 📖 [How the claims are verified](../../../../verification/README.md)
- 📄 [Papers (PDF)](../../../../papers/README.md) · 📚 [Monographs](../../../../docs/README.md) · 🧾 [LaTeX](../../../../src/README.md)
- ⚖️ [IPL-RP-1.0 License](../../../../LICENSE.md) — viewing, a single backup copy, and citation with attribution are permitted; anything else requires the author's written consent.

*This block was added automatically (`doc-enhancer v1`); it is unrelated to the license and does not modify it. Re-running the script does not duplicate the block.*

