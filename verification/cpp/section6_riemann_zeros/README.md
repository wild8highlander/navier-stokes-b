# Ⓜ️ C++ · Section 6 — Riemann Zeros

> **Navigation:** [`verification`](../../README.md) › [`cpp`](../README.md) › **`section6_riemann_zeros`**

![C++](https://img.shields.io/badge/C%2B%2B-C++17-informational?style=flat-square&logo=cplusplus&logoColor=white) ![License](https://img.shields.io/badge/License-IPL--RP--1.0-red?style=flat-square) ![Section](https://img.shields.io/badge/Section-6-blue?style=flat-square)

The **C++ port of Section 6** — Riemann Zeros — the Hilbert–Pólya Programme. This folder is the section's slot in the C++ layer of the framework: the file below states exactly the assertions the Python reference makes, in C++ idiom — header-light C++17 with a uniform check() harness printing PASS/FAIL per assertion and a JSON verdict.

## 🔬 Section Context — Where This Port Sits

**Where it sits.** Section 6 of the framework covers **the spectral correspondence between the AB-Cloud and the non-trivial zeros of the Riemann zeta function**. Its central quantities are the Hilbert–Pólya realisation, the Montgomery–Dyson GUE correspondence and the statistical identity of the two spectra; what this port asserts (or proves) is spectral-correspondence identities and the statistical machinery (⟨r⟩, KS, permutation tests) in constructive and classical form. The same assertions exist in every peer language of the matrix, each in its own idiom: [Python](../../section6_riemann_zeros/python/README.md) · [Lean 4](../../lean4/ResearchPapersVerification/Section6_RiemannZeros/README.md) · [Coq/Rocq](../../coq/section6_riemann_zeros/README.md) · [Isabelle-HOL](../../isabelle/Section6_RiemannZeros/README.md) · [Agda](../../agda/Section6_RiemannZeros/README.md) · [Rust](../../rust/section6_riemann_zeros/README.md) · [Haskell](../../haskell/Section6_RiemannZeros/README.md). Agreement between all ports is enforced by the cross-language validator (`../../tests/`) and the `ci-cross-language.yml` workflow.

**What you will see.** Run this port and you get: a banner identifying the section and language; the computed values printed at full precision; one `[PASS]`/`[FAIL]` line per assertion; and a final `JSON: {"section": 6, "language": "cpp", "values": {…}, "all_passed": …}` verdict line. Exit status is 0 only when every assertion passed — CI treats anything else as a failure.

## 📂 Contents — What Lives Here

| File | Size | Description |
|---|---|---|
| [`main.cpp`](main.cpp) | 744 B | include <cmath> include <iostream> |

## ▶️ How to Run

```bash
cmake -S verification/cpp -B build && cmake --build build && ./build/<section>  # per section
```

## 🔗 Cross-References

- [C++ layer README](../README.md)
- [Python reference for this section](../../section6_riemann_zeros/python/README.md)
- [Framework root](../../README.md)

## 🇷🇺 Brief Summary (Russian Summary)

C++ port of Section 6: a single file with the theorems/checks of the “Riemann Zeros” section; the section context is given in the block of the same name; build and output follow the C++ layer README.

---

<div align="center">

**[⬆ Back to top](#-c--section-6--riemann-zeros)** · 
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

