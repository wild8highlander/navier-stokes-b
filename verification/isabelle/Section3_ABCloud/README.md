# Isabelle-HOL · Section 3 — AB-Cloud

> **Navigation:** [`verification`](../../../verification/README.md) › **`Section3_ABCloud`**

![Isabelle-HOL](https://img.shields.io/badge/Isabelle--HOL-2024-1284BA?style=flat-square) ![Section](https://img.shields.io/badge/Section-3-9558B2?style=flat-square) ![License](https://img.shields.io/badge/License-IPL--RP--1.0-red?style=flat-square)

The **Isabelle-HOL port of Section 3** — AB-Cloud — the Non-Hermitian Hofstadter Hamiltonian. This folder is
an **independent Isabelle-HOL theory** over `Complex_Main`, written afresh in Isar. It is deliberately not a translation of the Lean file: agreement between the two is evidence about the mathematics, not tautology.

## 🔬 Section context — where this port sits

**Where it sits.** Section 3 of the framework covers **the structural core of the AB-Cloud Hamiltonian at reduced scale: the presuppositions of the heavy spectral statistics**. Its
central quantities are the Peierls phase e^{2πi/7}, the flux-quantisation lattice, and the GUE-class spacing statistics. The same assertions exist in every
peer language of the matrix, each in its own idiom: [Python](../../../verification/section3_ab_cloud/README.md) · [Lean 4](../../../verification/lean4/ResearchPapersVerification/Section3_ABCloud/README.md) · [Coq/Rocq](../../../verification/coq/section3_ab_cloud/README.md) · [Agda](../../../verification/agda/Section3_ABCloud/README.md) · [C++](../../../verification/cpp/section3_ab_cloud/README.md) · [Rust](../../../verification/rust/section3_ab_cloud/README.md) · [Haskell](../../../verification/haskell/Section3_ABCloud/README.md). Agreement
between all ports is enforced by the cross-language validator
([`tests/`](../../../verification/tests/README.md)) and fails CI on any
disagreement.

**What you will see.** Run this port and you get: a banner identifying the
section and language; the computed values at full precision; one
`[PASS]`/`[FAIL]` line per assertion; and a final
`JSON: {"section": 3, "language": "isabelle", "values": {…}, "all_passed": …}`
verdict line. Exit status is 0 only when every assertion passed.

## 📂 Contents

| File | Description |
|---|---|
| [`Hofstadter.thy`](Hofstadter.thy) | the section 3 port — AB-Cloud — the Non-Hermitian Hofstadter Hamiltonian |

## ▶️ How to run

```bash
cd verification/isabelle
isabelle build -D .                          # whole session
isabelle jedit -l HOL Section3_ABCloud/Hofstadter.thy     # interactive
```

## 📋 What is asserted

1. **Peierls phase** — |e^{2πi/7}| = 1 and the phase has exact order 7;
2. **flux quantisation** — the flux per plaquette is quantised in units of the flux quantum — the Hamiltonian is well defined on the lattice;
3. **Hermiticity and symmetry classes** — the reduced Hamiltonian has the declared symmetry class and the GUE spacing statistic is normalised.

## 🔍 Sample output

```text
$ cd verification/isabelle
=== Section 3 ===
|phase| = 1.0, order = 7
flux quantised
PASS
```

## 🧩 The port family

| Port | Where | Command | Time |
|---|---|---|---|
| Python (reference) | [`python/`](../../../verification/section3_ab_cloud/README.md) | `python3 verification/section3_ab_cloud/python/verify.py` | < 1 s |
| Lean 4 | [`lean4/`](../../../verification/lean4/ResearchPapersVerification/Section3_ABCloud/README.md) | `lake build && lake exe check` | min (cached s) |
| Coq | [`coq/`](../../../verification/coq/section3_ab_cloud/README.md) | `coqc verification/coq/section3_ab_cloud/CorrectionB.v` | s |
| Isabelle | [`isabelle/`](../../../verification/isabelle/Section3_ABCloud/README.md) | `isabelle build -D verification/isabelle` | min (first) |
| Agda | [`agda/`](../../../verification/agda/Section3_ABCloud/README.md) | `agda --safe verification/agda/Section3_ABCloud/CorrectionB.agda` | s |
| C++ | [`cpp/`](../../../verification/cpp/section3_ab_cloud/README.md) | `cmake -S verification/cpp -B build && ./build/section3_ab_cloud` | < 1 s |
| Rust | [`rust/`](../../../verification/rust/section3_ab_cloud/README.md) | `cargo run --release -p section3_ab_cloud` | < 1 s |
| Haskell | [`haskell/`](../../../verification/haskell/Section3_ABCloud/README.md) | `cabal run section3-ABCloud` | < 1 s |

Section 3 carries the structural skeleton of the AB-Cloud program: the identities that the heavy statistics elsewhere rely on, checked at a scale small enough to audit by eye. Its assertions are deliberately elementary — their value is that they are presuppositions, and a broken presupposition must be visible long before the statistics that consume it.

## 🔗 Cross-references

- [Section 3 reference port](../../../verification/section3_ab_cloud/README.md)
- [Framework hub](../../../verification/README.md)
- [Gap ledger (Lean 4)](../../../verification/lean4/TODO_sorry.md) — which
  formal lemmas are admitted gaps

---

---

Navigation: [repository root](../../../README.md) · [isabelle](../../../verification/isabelle/README.md) · [IPL-RP-1.0](../../../LICENSE.md)

*Part of [wild8highlander/navier-stokes-b](https://github.com/wild8highlander/navier-stokes-b) - (c) 2026 Isaev Iskhak Khamzatovich, all rights reserved.*

