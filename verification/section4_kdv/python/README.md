# 🐍 Section 4 · python — the Reference Port

> **Navigation:** [`verification`](../../README.md) › [`section4_kdv`](../README.md) › **`python`**

![Python](https://img.shields.io/badge/Python-3.10–3.12-informational?style=flat-square&logo=python&logoColor=white) ![License](https://img.shields.io/badge/License-IPL--RP--1.0-red?style=flat-square)

The **pure-Python port** of Section 4 — KdV — Soliton Interactions under the b-Correction. A single ~25-line `verify.py` using only the standard `math` module: it computes pseudospectral treatment of the KdV hierarchy and the manifestation of the polarization correction in soliton collision dynamics, asserts conservation-law identities of the integrable KdV hierarchy and the numeric stability of the pseudospectral scheme, and prints the framework's JSON verdict. This is the port CI runs first (job `ci-python.yml`) and the one new toolchain ports are compared against.

## 🔬 Section Context — Where This Port Sits

**Where it sits.** Section 4 of the framework covers **the Korteweg–de Vries equation and its soliton interactions**. Its central quantities are pseudospectral treatment of the KdV hierarchy and the manifestation of the polarization correction in soliton collision dynamics; what this port asserts (or proves) is conservation-law identities of the integrable KdV hierarchy and the numeric stability of the pseudospectral scheme. The same assertions exist in every peer language of the matrix, each in its own idiom: [Lean 4](../../lean4/ResearchPapersVerification/Section4_KdV/README.md) · [Coq/Rocq](../../coq/section4_kdv/README.md) · [Isabelle-HOL](../../isabelle/Section4_KdV/README.md) · [Agda](../../agda/Section4_KdV/README.md) · [C++](../../cpp/section4_kdv/README.md) · [Rust](../../rust/section4_kdv/README.md) · [Haskell](../../haskell/Section4_KdV/README.md). Agreement between all ports is enforced by the cross-language validator (`../../tests/`) and the `ci-cross-language.yml` workflow.

**What you will see.** Run this port and you get: a banner identifying the section and language; the computed values printed at full precision; one `[PASS]`/`[FAIL]` line per assertion; and a final `JSON: {"section": 4, "language": "python", "values": {…}, "all_passed": …}` verdict line. Exit status is 0 only when every assertion passed — CI treats anything else as a failure.

## 📂 Contents — What Lives Here

| File | Size | Description |
|---|---|---|
| [`verify.py`](verify.py) | 319 B | Section 4 reference verifier — prints values, asserts, JSON verdict (~25 lines) |

## ▶️ How to Run

```bash
python3 verify.py          # from this folder
# or from the repo root:
python3 verification/section4_kdv/python/verify.py
```

## 🔗 Cross-References

- [Section parent](../README.md)
- [Framework root](../../README.md)

## 🇷🇺 Brief Summary (Russian Summary)

The Python port of Section 4: one file, pure stdlib, PASS/JSON in a fraction of a second; result — pseudospectral treatment of the KdV hierarchy and the manifestation of the polarization correction in soliton collision dynamics.

---

<div align="center">

**[⬆ Back to top](#-section-4--python--the-reference-port)** · 
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

