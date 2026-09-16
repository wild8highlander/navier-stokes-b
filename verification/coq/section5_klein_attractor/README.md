# Ⓜ️ Coq/Rocq · Section 5 — Klein Attractor

> **Navigation:** [`verification`](../../README.md) › [`coq`](../README.md) › **`section5_klein_attractor`**

![Coq/Rocq](https://img.shields.io/badge/Coq/Rocq-8.18-informational?style=flat-square&logo=ocaml&logoColor=white) ![License](https://img.shields.io/badge/License-IPL--RP--1.0-red?style=flat-square) ![Section](https://img.shields.io/badge/Section-5-blue?style=flat-square)

The **Coq/Rocq port of Section 5** — Klein Attractor — Ergodic Dynamics and the NSE Bridge. This folder is the section's slot in the Coq/Rocq layer of the framework: the file below states exactly the assertions the Python reference makes, in Coq/Rocq idiom — proofs built on the standard `Reals` library with `lra`/`nra` automation.

## 🔬 Section Context — Where This Port Sits

**Where it sits.** Section 5 of the framework covers **the Klein attractor dynamical system with ergodic-theoretic structure**. Its central quantities are the attractor's invariant-measure behaviour and the bridge connecting its dynamics back to the Navier–Stokes setting; what this port asserts (or proves) is ergodicity scaffolding, invariant-measure identities and the structural lemmas of the Klein–NS bridge. The same assertions exist in every peer language of the matrix, each in its own idiom: [Python](../../section5_klein_attractor/python/README.md) · [Lean 4](../../lean4/ResearchPapersVerification/Section5_KleinAttractor/README.md) · [Isabelle-HOL](../../isabelle/Section5_KleinAttractor/README.md) · [Agda](../../agda/Section5_KleinAttractor/README.md) · [C++](../../cpp/section5_klein_attractor/README.md) · [Rust](../../rust/section5_klein_attractor/README.md) · [Haskell](../../haskell/Section5_KleinAttractor/README.md). Agreement between all ports is enforced by the cross-language validator (`../../tests/`) and the `ci-cross-language.yml` workflow.

**What you will see.** Run this port and you get: a banner identifying the section and language; the computed values printed at full precision; one `[PASS]`/`[FAIL]` line per assertion; and a final `JSON: {"section": 5, "language": "coq", "values": {…}, "all_passed": …}` verdict line. Exit status is 0 only when every assertion passed — CI treats anything else as a failure.

## 📂 Contents — What Lives Here

| File | Size | Description |
|---|---|---|
| [`Klein.v`](Klein.v) | 431 B | Coq proof development |

## ▶️ How to Run

```bash
cd verification/coq && coqc <section-file>.v         # per file
```

## 🔗 Cross-References

- [Coq/Rocq layer README](../README.md)
- [Python reference for this section](../../section5_klein_attractor/python/README.md)
- [Framework root](../../README.md)

## 🇷🇺 Brief Summary (Russian Summary)

Coq/Rocq port of Section 5: a single file with the theorems/checks of the “Klein Attractor” section; the section context is given in the block of the same name; build and output follow the Coq/Rocq layer README.

---

<div align="center">

**[⬆ Back to top](#-coqrocq--section-5--klein-attractor)** · 
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

