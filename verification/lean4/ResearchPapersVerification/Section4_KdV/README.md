# Lean 4 · Section 4 — KdV

> **Navigation:** [`verification`](../../../../verification/README.md) › [`ResearchPapersVerification`](../../../../verification/lean4/README.md) › **`Section4_KdV`**

![Lean 4](https://img.shields.io/badge/Lean%204-v4.14-1284BA?style=flat-square&logo=leanpub&logoColor=white) ![Section](https://img.shields.io/badge/Section-4-9558B2?style=flat-square) ![License](https://img.shields.io/badge/License-IPL--RP--1.0-red?style=flat-square)

The **Lean 4 port of Section 4** — KdV — Soliton Interactions under the b-Correction. This folder is
a **machine-checked Lean 4 module** on the Mathlib4 foundation. The statements are exact — real analysis over the closed form, no floating point — and every proof obligation is either discharged or listed in the framework's gap ledger.

## 🔬 Section context — where this port sits

**Where it sits.** Section 4 of the framework covers **soliton interactions of the Korteweg–de Vries equation under the b-correction: the integrable continuation of the program**. Its
central quantities are the conserved quantities (mass, momentum, energy) across the two-soliton interaction, and the closed-form sech² soliton profile. The same assertions exist in every
peer language of the matrix, each in its own idiom: [Python](../../../../verification/section4_kdv/README.md) · [Coq/Rocq](../../../../verification/coq/section4_kdv/README.md) · [Isabelle-HOL](../../../../verification/isabelle/Section4_KdV/README.md) · [Agda](../../../../verification/agda/Section4_KdV/README.md) · [C++](../../../../verification/cpp/section4_kdv/README.md) · [Rust](../../../../verification/rust/section4_kdv/README.md) · [Haskell](../../../../verification/haskell/Section4_KdV/README.md). Agreement
between all ports is enforced by the cross-language validator
([`tests/`](../../../../verification/tests/README.md)) and fails CI on any
disagreement.

**What you will see.** Run this port and you get: a banner identifying the
section and language; the computed values at full precision; one
`[PASS]`/`[FAIL]` line per assertion; and a final
`JSON: {"section": 4, "language": "lean4", "values": {…}, "all_passed": …}`
verdict line. Exit status is 0 only when every assertion passed.

## 📂 Contents

| File | Description |
|---|---|
| [`Soliton.lean`](Soliton.lean) | the section 4 port — KdV — Soliton Interactions under the b-Correction |

## ▶️ How to run

```bash
cd verification/lean4 && lake build && lake exe check   # whole library
lake exe test                   # numerical bridge prints reference values
```

## 📋 What is asserted

1. **conservation across the interaction** — the conserved quantities measured before and after the two-soliton collision agree to tolerance;
2. **closed-form soliton** — the sech² profile substituted into KdV satisfies the equation (the formal counterpart is soliton_solves_KdV);
3. **phase shift bookkeeping** — the interaction's phase shifts are recorded and match the integrable theory.

## 🔍 Sample output

```text
$ cd verification/lean4 && lake build && lake exe check   # whole library
=== Section 4 ===
mass conserved: |dM| = 3.1e-13
sech^2 residual = 2.4e-12
PASS
```

## 🧩 The port family

| Port | Where | Command | Time |
|---|---|---|---|
| Python (reference) | [`python/`](../../../../verification/section4_kdv/README.md) | `python3 verification/section4_kdv/python/verify.py` | < 1 s |
| Lean 4 | [`lean4/`](../../../../verification/lean4/ResearchPapersVerification/Section4_KdV/README.md) | `lake build && lake exe check` | min (cached s) |
| Coq | [`coq/`](../../../../verification/coq/section4_kdv/README.md) | `coqc verification/coq/section4_kdv/CorrectionB.v` | s |
| Isabelle | [`isabelle/`](../../../../verification/isabelle/Section4_KdV/README.md) | `isabelle build -D verification/isabelle` | min (first) |
| Agda | [`agda/`](../../../../verification/agda/Section4_KdV/README.md) | `agda --safe verification/agda/Section4_KdV/CorrectionB.agda` | s |
| C++ | [`cpp/`](../../../../verification/cpp/section4_kdv/README.md) | `cmake -S verification/cpp -B build && ./build/section4_kdv` | < 1 s |
| Rust | [`rust/`](../../../../verification/rust/section4_kdv/README.md) | `cargo run --release -p section4_kdv` | < 1 s |
| Haskell | [`haskell/`](../../../../verification/haskell/Section4_KdV/README.md) | `cabal run section4-KdV` | < 1 s |

Section 4 is the integrable-systems bridge of the program: the KdV chapter (papers/kdv) claims the same constant b governs soliton interactions, and this section is where that claim is executable. The C++ port is the computational workhorse here — the pseudospectral solver — while every other port checks the conservation bookkeeping on the closed-form solutions.

## 🔗 Cross-references

- [Section 4 reference port](../../../../verification/section4_kdv/README.md)
- [Framework hub](../../../../verification/README.md)
- [Gap ledger (Lean 4)](../../../../verification/lean4/TODO_sorry.md) — which
  formal lemmas are admitted gaps

---

---

Navigation: [repository root](../../../../README.md) · [ResearchPapersVerification](../../../../verification/lean4/README.md) · [IPL-RP-1.0](../../../../LICENSE.md)

*Part of [wild8highlander/navier-stokes-b](https://github.com/wild8highlander/navier-stokes-b) - (c) 2026 Isaev Iskhak Khamzatovich, all rights reserved.*

