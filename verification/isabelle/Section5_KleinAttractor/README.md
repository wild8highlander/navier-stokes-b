# Isabelle-HOL · Section 5 — Klein Attractor

> **Navigation:** [`verification`](../../../verification/README.md) › **`Section5_KleinAttractor`**

![Isabelle-HOL](https://img.shields.io/badge/Isabelle--HOL-2024-1284BA?style=flat-square) ![Section](https://img.shields.io/badge/Section-5-9558B2?style=flat-square) ![License](https://img.shields.io/badge/License-IPL--RP--1.0-red?style=flat-square)

The **Isabelle-HOL port of Section 5** — Klein Attractor — Ergodic Dynamics and the NSE Bridge. This folder is
an **independent Isabelle-HOL theory** over `Complex_Main`, written afresh in Isar. It is deliberately not a translation of the Lean file: agreement between the two is evidence about the mathematics, not tautology.

## 🔬 Section context — where this port sits

**Where it sits.** Section 5 of the framework covers **the Klein attractor: ergodic statistics over the reference ensemble and the bridge back to the NSE program**. Its
central quantities are the Klein closure Z = exp(b·β_K·L_min) = 1.351637344385124…, the invariant statistics of the reference ensemble, and the contraction statements. The same assertions exist in every
peer language of the matrix, each in its own idiom: [Python](../../../verification/section5_klein_attractor/README.md) · [Lean 4](../../../verification/lean4/ResearchPapersVerification/Section5_KleinAttractor/README.md) · [Coq/Rocq](../../../verification/coq/section5_klein_attractor/README.md) · [Agda](../../../verification/agda/Section5_KleinAttractor/README.md) · [C++](../../../verification/cpp/section5_klein_attractor/README.md) · [Rust](../../../verification/rust/section5_klein_attractor/README.md) · [Haskell](../../../verification/haskell/Section5_KleinAttractor/README.md). Agreement
between all ports is enforced by the cross-language validator
([`tests/`](../../../verification/tests/README.md)) and fails CI on any
disagreement.

**What you will see.** Run this port and you get: a banner identifying the
section and language; the computed values at full precision; one
`[PASS]`/`[FAIL]` line per assertion; and a final
`JSON: {"section": 5, "language": "isabelle", "values": {…}, "all_passed": …}`
verdict line. Exit status is 0 only when every assertion passed.

## 📂 Contents

| File | Description |
|---|---|
| [`Klein.thy`](Klein.thy) | the section 5 port — Klein Attractor — Ergodic Dynamics and the NSE Bridge |

## ▶️ How to run

```bash
cd verification/isabelle
isabelle build -D .                          # whole session
isabelle jedit -l HOL Section5_KleinAttractor/Klein.thy     # interactive
```

## 📋 What is asserted

1. **invariant statistics** — the reference ensemble's statistics are invariant under the dynamics;
2. **contraction** — the declared contraction statements hold — the attractor absorbs the transients;
3. **the NSE bridge** — the closure Z enters the NSE-side estimates in the role the monograph assigns it.

## 🔍 Sample output

```text
$ cd verification/isabelle
=== Section 5 ===
Z = 1.351637344385124
contraction holds
PASS
```

## 🧩 The port family

| Port | Where | Command | Time |
|---|---|---|---|
| Python (reference) | [`python/`](../../../verification/section5_klein_attractor/README.md) | `python3 verification/section5_klein_attractor/python/verify.py` | < 1 s |
| Lean 4 | [`lean4/`](../../../verification/lean4/ResearchPapersVerification/Section5_KleinAttractor/README.md) | `lake build && lake exe check` | min (cached s) |
| Coq | [`coq/`](../../../verification/coq/section5_klein_attractor/README.md) | `coqc verification/coq/section5_klein_attractor/CorrectionB.v` | s |
| Isabelle | [`isabelle/`](../../../verification/isabelle/Section5_KleinAttractor/README.md) | `isabelle build -D verification/isabelle` | min (first) |
| Agda | [`agda/`](../../../verification/agda/Section5_KleinAttractor/README.md) | `agda --safe verification/agda/Section5_KleinAttractor/CorrectionB.agda` | s |
| C++ | [`cpp/`](../../../verification/cpp/section5_klein_attractor/README.md) | `cmake -S verification/cpp -B build && ./build/section5_klein_attractor` | < 1 s |
| Rust | [`rust/`](../../../verification/rust/section5_klein_attractor/README.md) | `cargo run --release -p section5_klein_attractor` | < 1 s |
| Haskell | [`haskell/`](../../../verification/haskell/Section5_KleinAttractor/README.md) | `cabal run section5-KleinAttractor` | < 1 s |

Section 5 documents the attractor side of the program: the place where the geometric mechanism and the statistical mechanics meet. Its contraction statements are what make the ensemble averages of the monograph legitimate, and its closure constant Z is one of the few quantities the framework pins at 50 digits (see L1 of the verification chain).

## 🔗 Cross-references

- [Section 5 reference port](../../../verification/section5_klein_attractor/README.md)
- [Framework hub](../../../verification/README.md)
- [Gap ledger (Lean 4)](../../../verification/lean4/TODO_sorry.md) — which
  formal lemmas are admitted gaps

---

---

Navigation: [repository root](../../../README.md) · [isabelle](../../../verification/isabelle/README.md) · [IPL-RP-1.0](../../../LICENSE.md)

*Part of [wild8highlander/navier-stokes-b](https://github.com/wild8highlander/navier-stokes-b) - (c) 2026 Isaev Iskhak Khamzatovich, all rights reserved.*

