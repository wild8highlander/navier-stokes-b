# Ⓜ️ Lean 4 · Section 4 — KdV

> **Navigation:** [`verification`](../../../README.md) › [`lean4`](../../README.md) › [`ResearchPapersVerification`](../README.md) › **`Section4_KdV`**

![Lean 4](https://img.shields.io/badge/Lean%204-v4.14-informational?style=flat-square&logo=leanpub&logoColor=white) ![License](https://img.shields.io/badge/License-IPL--RP--1.0-red?style=flat-square) ![Section](https://img.shields.io/badge/Section-4-blue?style=flat-square)

The **Lean 4 port of Section 4** — KdV — Soliton Interactions under the b-Correction. This folder is the section's slot in the Lean 4 layer of the framework: the file below states exactly the assertions the Python reference makes, in Lean 4 idiom — machine-checked proofs on the Mathlib4 foundation with custom definitions layered on top.

## 🔬 Section Context — Where This Port Sits

**Where it sits.** Section 4 of the framework covers **the Korteweg–de Vries equation and its soliton interactions**. Its central quantities are pseudospectral treatment of the KdV hierarchy and the manifestation of the polarization correction in soliton collision dynamics; what this port asserts (or proves) is conservation-law identities of the integrable KdV hierarchy and the numeric stability of the pseudospectral scheme. The same assertions exist in every peer language of the matrix, each in its own idiom: [Python](../../../section4_kdv/python/README.md) · [Coq/Rocq](../../../coq/section4_kdv/README.md) · [Isabelle-HOL](../../../isabelle/Section4_KdV/README.md) · [Agda](../../../agda/Section4_KdV/README.md) · [C++](../../../cpp/section4_kdv/README.md) · [Rust](../../../rust/section4_kdv/README.md) · [Haskell](../../../haskell/Section4_KdV/README.md). Agreement between all ports is enforced by the cross-language validator (`../../../tests/`) and the `ci-cross-language.yml` workflow.

**What you will see.** Run this port and you get: a banner identifying the section and language; the computed values printed at full precision; one `[PASS]`/`[FAIL]` line per assertion; and a final `JSON: {"section": 4, "language": "lean4", "values": {…}, "all_passed": …}` verdict line. Exit status is 0 only when every assertion passed — CI treats anything else as a failure.

## 📂 Contents — What Lives Here

| File | Size | Description |
|---|---|---|
| [`Soliton.lean`](Soliton.lean) | 579 B | Lean 4 module |

## ▶️ How to Run

```bash
cd verification/lean4 && lake build && lake exe check   # whole library
```

## 🔗 Cross-References

- [Lean 4 layer README](../README.md)
- [Python reference for this section](../../../section4_kdv/python/README.md)
- [Framework root](../../../README.md)

## 🇷🇺 Brief Summary (Russian Summary)

Lean 4 port of Section 4: one file with the theorems/checks of the "KdV" section; section context — in the identically named block; build and output — same as in the Lean 4 layer README.

---

<div align="center">

**[⬆ Back to top](#-lean-4--section-4--kdv)** · 
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

