# Ⓜ️ Coq/Rocq · Section 1 — Correction b

> **Navigation:** [`verification`](../../README.md) › [`coq`](../README.md) › **`section1_correction_b`**

![Coq/Rocq](https://img.shields.io/badge/Coq/Rocq-8.18-informational?style=flat-square&logo=ocaml&logoColor=white) ![License](https://img.shields.io/badge/License-IPL--RP--1.0-red?style=flat-square) ![Section](https://img.shields.io/badge/Section-1-blue?style=flat-square)

The **Coq/Rocq port of Section 1** — Correction b — the Universal Polarization Constant. This folder is the section's slot in the Coq/Rocq layer of the framework: the file below states exactly the assertions the Python reference makes, in Coq/Rocq idiom — proofs built on the standard `Reals` library with `lra`/`nra` automation.

## 🔬 Section Context — Where This Port Sits

**Where it sits.** Section 1 of the framework covers **the universal polarization correction derived from the Kirchhoff point-vortex system**. Its central quantities are b = π / (4·π² + 2·π·√3) ≈ 0.0785, the rotation angle θ_b = arcsin(b) ≈ 7.07°, and the stabilisation identity cos²θ_b + sin²θ_b = 1; what this port asserts (or proves) is 0 < b < 1 (both bounds), sin θ_b = b, cos²θ_b + sin²θ_b = 1, and the reference interval 0.07 < b < 0.08 against the published value 0.0785. The same assertions exist in every peer language of the matrix, each in its own idiom: [Python](../../section1_correction_b/python/README.md) · [Lean 4](../../lean4/ResearchPapersVerification/Section1_CorrectionB/README.md) · [Isabelle-HOL](../../isabelle/Section1_CorrectionB/README.md) · [Agda](../../agda/Section1_CorrectionB/README.md) · [C++](../../cpp/section1_correction_b/README.md) · [Rust](../../rust/section1_correction_b/README.md) · [Haskell](../../haskell/Section1_CorrectionB/README.md). Agreement between all ports is enforced by the cross-language validator (`../../tests/`) and the `ci-cross-language.yml` workflow.

**What you will see.** Run this port and you get: a banner identifying the section and language; the computed values printed at full precision; one `[PASS]`/`[FAIL]` line per assertion; and a final `JSON: {"section": 1, "language": "coq", "values": {…}, "all_passed": …}` verdict line. Exit status is 0 only when every assertion passed — CI treats anything else as a failure.

## 📂 Contents — What Lives Here

| File | Size | Description |
|---|---|---|
| [`CorrectionB.v`](CorrectionB.v) | 802 B | Section 1 Coq file — Correction b — the Universal Polarization Constant (Reals + lra; Compute prints the constants) |

## ▶️ How to Run

```bash
cd verification/coq && coqc <section-file>.v         # per file
```

## 🔗 Cross-References

- [Coq/Rocq layer README](../README.md)
- [Python reference for this section](../../section1_correction_b/python/README.md)
- [Framework root](../../README.md)

## 🇷🇺 Brief Summary (Russian Summary)

Coq/Rocq port of Section 1: a single file with the theorems/checks of the “Correction b” section; the section context is given in the block of the same name; build and output follow the Coq/Rocq layer README.

---

<div align="center">

**[⬆ Back to top](#-coqrocq--section-1--correction-b)** · 
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

