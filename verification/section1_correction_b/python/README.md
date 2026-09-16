# 🐍 Section 1 · python — the Reference Port

> **Navigation:** [`verification`](../../README.md) › [`section1_correction_b`](../README.md) › **`python`**

![Python](https://img.shields.io/badge/Python-3.10–3.12-informational?style=flat-square&logo=python&logoColor=white) ![License](https://img.shields.io/badge/License-IPL--RP--1.0-red?style=flat-square)

The **pure-Python port** of Section 1 — Correction b — the Universal Polarization Constant. A single ~25-line `verify.py` using only the standard `math` module: it computes b = π / (4·π² + 2·π·√3) ≈ 0.0785, the rotation angle θ_b = arcsin(b) ≈ 7.07°, and the stabilisation identity cos²θ_b + sin²θ_b = 1, asserts 0 < b < 1 (both bounds), sin θ_b = b, cos²θ_b + sin²θ_b = 1, and the reference interval 0.07 < b < 0.08 against the published value 0.0785, and prints the framework's JSON verdict. This is the port CI runs first (job `ci-python.yml`) and the one new toolchain ports are compared against.

## 🔬 Section Context — Where This Port Sits

**Where it sits.** Section 1 of the framework covers **the universal polarization correction derived from the Kirchhoff point-vortex system**. Its central quantities are b = π / (4·π² + 2·π·√3) ≈ 0.0785, the rotation angle θ_b = arcsin(b) ≈ 7.07°, and the stabilisation identity cos²θ_b + sin²θ_b = 1; what this port asserts (or proves) is 0 < b < 1 (both bounds), sin θ_b = b, cos²θ_b + sin²θ_b = 1, and the reference interval 0.07 < b < 0.08 against the published value 0.0785. The same assertions exist in every peer language of the matrix, each in its own idiom: [Lean 4](../../lean4/ResearchPapersVerification/Section1_CorrectionB/README.md) · [Coq/Rocq](../../coq/section1_correction_b/README.md) · [Isabelle-HOL](../../isabelle/Section1_CorrectionB/README.md) · [Agda](../../agda/Section1_CorrectionB/README.md) · [C++](../../cpp/section1_correction_b/README.md) · [Rust](../../rust/section1_correction_b/README.md) · [Haskell](../../haskell/Section1_CorrectionB/README.md). Agreement between all ports is enforced by the cross-language validator (`../../tests/`) and the `ci-cross-language.yml` workflow.

**What you will see.** Run this port and you get: a banner identifying the section and language; the computed values printed at full precision; one `[PASS]`/`[FAIL]` line per assertion; and a final `JSON: {"section": 1, "language": "python", "values": {…}, "all_passed": …}` verdict line. Exit status is 0 only when every assertion passed — CI treats anything else as a failure.

## 📂 Contents — What Lives Here

| File | Size | Description |
|---|---|---|
| [`verify.py`](verify.py) | 319 B | Section 1 reference verifier — prints values, asserts, JSON verdict (~25 lines) |

## ▶️ How to Run

```bash
python3 verify.py          # from this folder
# or from the repo root:
python3 verification/section1_correction_b/python/verify.py
```

## 🔗 Cross-References

- [Section parent](../README.md)
- [Framework root](../../README.md)

## 🇷🇺 Brief Summary (Russian Summary)

The Python port of Section 1: one file, pure stdlib, PASS/JSON in a fraction of a second; result — b = π / (4·π² + 2·π·√3) ≈ 0.0785, the rotation angle θ_b = arcsin(b) ≈ 7.07°, and the stabilisation identity cos²θ_b + sin²θ_b = 1.

---

<div align="center">

**[⬆ Back to top](#-section-1--python--the-reference-port)** · 
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

