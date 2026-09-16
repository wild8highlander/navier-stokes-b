# Ⓜ️ Isabelle-HOL · Section 1 — Correction b

> **Navigation:** [`verification`](../../README.md) › [`isabelle`](../README.md) › **`Section1_CorrectionB`**

![Isabelle-HOL](https://img.shields.io/badge/Isabelle-HOL-2024-informational?style=flat-square&logo=isamars&logoColor=white) ![License](https://img.shields.io/badge/License-IPL--RP--1.0-red?style=flat-square) ![Section](https://img.shields.io/badge/Section-1-blue?style=flat-square)

The **Isabelle-HOL port of Section 1** — Correction b — the Universal Polarization Constant. This folder is the section's slot in the Isabelle-HOL layer of the framework: the file below states exactly the assertions the Python reference makes, in Isabelle-HOL idiom — proofs stated over `Complex_Main`; each section is a standalone theory.

## 🔬 Section Context — Where This Port Sits

**Where it sits.** Section 1 of the framework covers **the universal polarization correction derived from the Kirchhoff point-vortex system**. Its central quantities are b = π / (4·π² + 2·π·√3) ≈ 0.0785, the rotation angle θ_b = arcsin(b) ≈ 7.07°, and the stabilisation identity cos²θ_b + sin²θ_b = 1; what this port asserts (or proves) is 0 < b < 1 (both bounds), sin θ_b = b, cos²θ_b + sin²θ_b = 1, and the reference interval 0.07 < b < 0.08 against the published value 0.0785. The same assertions exist in every peer language of the matrix, each in its own idiom: [Python](../../section1_correction_b/python/README.md) · [Lean 4](../../lean4/ResearchPapersVerification/Section1_CorrectionB/README.md) · [Coq/Rocq](../../coq/section1_correction_b/README.md) · [Agda](../../agda/Section1_CorrectionB/README.md) · [C++](../../cpp/section1_correction_b/README.md) · [Rust](../../rust/section1_correction_b/README.md) · [Haskell](../../haskell/Section1_CorrectionB/README.md). Agreement between all ports is enforced by the cross-language validator (`../../tests/`) and the `ci-cross-language.yml` workflow.

**What you will see.** Run this port and you get: a banner identifying the section and language; the computed values printed at full precision; one `[PASS]`/`[FAIL]` line per assertion; and a final `JSON: {"section": 1, "language": "isabelle", "values": {…}, "all_passed": …}` verdict line. Exit status is 0 only when every assertion passed — CI treats anything else as a failure.

## 📂 Contents — What Lives Here

| File | Size | Description |
|---|---|---|
| [`CorrectionB.thy`](CorrectionB.thy) | 496 B | Section 1 Isabelle theory — Correction b — the Universal Polarization Constant (Complex_Main, Isar proofs) |

## ▶️ How to Run

```bash
cd verification/isabelle && isabelle build -D .      # whole session
```

## 🔗 Cross-References

- [Isabelle-HOL layer README](../README.md)
- [Python reference for this section](../../section1_correction_b/python/README.md)
- [Framework root](../../README.md)

## 📝 Summary

Isabelle-HOL port of Section 1: a single file with the theorems/checks of the "Correction b" section; the section context is given in the Section Context block above; build and output follow the Isabelle-HOL layer README.

---

<div align="center">

**[⬆ Back to top](#-isabelle-hol--section-1--correction-b)** · 
**[Repository root](../../README.md)**

*Part of [wild8highlander/navier-stokes-b](https://github.com/wild8highlander/navier-stokes-b) · Licensed under [IPL-RP-1.0](https://github.com/wild8highlander/navier-stokes-b/blob/main/LICENSE.md) — All Rights Reserved*

</div>
<!-- doc-enhancer:block v1 (auto-generated block; license files are not touched) -->

---

## 🧭 Navigation and Quick Links (auto)

- 🏠 [Repository root](../../../../README.md)
- 📖 [How the claims are verified](../../../../verification/README.md)
- 📄 [Papers (PDF)](../../../../papers/README.md) · 📚 [Monographs](../../../../docs/README.md) · 🧾 [LaTeX](../../../../src/README.md)
- ⚖️ [IPL-RP-1.0 License](../../../../LICENSE.md) — viewing, a single backup copy, and citation with attribution are permitted; everything else requires the author's written permission.

*Block added automatically (`doc-enhancer v1`); it is unrelated to the license and does not modify it. Re-running the script does not duplicate the block.*

