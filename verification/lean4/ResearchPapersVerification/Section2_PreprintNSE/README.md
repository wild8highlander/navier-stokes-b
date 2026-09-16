# Lean 4 · Section 2 — Preprint NSE

> **Navigation:** [`verification`](../../../../verification/README.md) › [`ResearchPapersVerification`](../../../../verification/lean4/README.md) › **`Section2_PreprintNSE`**

![Lean 4](https://img.shields.io/badge/Lean%204-v4.14-1284BA?style=flat-square&logo=leanpub&logoColor=white) ![Section](https://img.shields.io/badge/Section-2-9558B2?style=flat-square) ![License](https://img.shields.io/badge/License-IPL--RP--1.0-red?style=flat-square)

The **Lean 4 port of Section 2** — Preprint NSE — the Regularity Argument Chain. This folder is
a **machine-checked Lean 4 module** on the Mathlib4 foundation. The statements are exact — real analysis over the closed form, no floating point — and every proof obligation is either discharged or listed in the framework's gap ledger.

## 🔬 Section context — where this port sits

**Where it sits.** Section 2 of the framework covers **the NSE regularity argument chain of the preprint: the twist as a unitary rearrangement and the bound it produces**. Its
central quantities are the twist operator on u, the identity ω′ = cos θ_b · ω, and the ordered estimates that close the regularity argument. The same assertions exist in every
peer language of the matrix, each in its own idiom: [Python](../../../../verification/section2_preprint/README.md) · [Coq/Rocq](../../../../verification/coq/section2_preprint/README.md) · [Isabelle-HOL](../../../../verification/isabelle/Section2_PreprintNSE/README.md) · [Agda](../../../../verification/agda/Section2_PreprintNSE/README.md) · [C++](../../../../verification/cpp/section2_preprint/README.md) · [Rust](../../../../verification/rust/section2_preprint/README.md) · [Haskell](../../../../verification/haskell/Section2_PreprintNSE/README.md). Agreement
between all ports is enforced by the cross-language validator
([`tests/`](../../../../verification/tests/README.md)) and fails CI on any
disagreement.

**What you will see.** Run this port and you get: a banner identifying the
section and language; the computed values at full precision; one
`[PASS]`/`[FAIL]` line per assertion; and a final
`JSON: {"section": 2, "language": "lean4", "values": {…}, "all_passed": …}`
verdict line. Exit status is 0 only when every assertion passed.

## 📂 Contents

| File | Description |
|---|---|
| [`ProofChain.lean`](ProofChain.lean) | the section 2 port — Preprint NSE — the Regularity Argument Chain |

## ▶️ How to run

```bash
cd verification/lean4 && lake build && lake exe check   # whole library
lake exe test                   # numerical bridge prints reference values
```

## 📋 What is asserted

1. **twist unitarity** — the b-twist preserves the L2 norm of the velocity field (the Leray projection absorbs the gradient part);
2. **BKM bound under the twist** — the BKM integral decreases once the rotation is applied — no energy is injected;
3. **estimate ordering** — the chain of inequalities used by the regularity argument holds in the stated order.

## 🔍 Sample output

```text
$ cd verification/lean4 && lake build && lake exe check   # whole library
=== Section 2 ===
||Twist(u)|| = ||u||
BKM factor = 0.96695
PASS
```

## 🧩 The port family

| Port | Where | Command | Time |
|---|---|---|---|
| Python (reference) | [`python/`](../../../../verification/section2_preprint/README.md) | `python3 verification/section2_preprint/python/verify.py` | < 1 s |
| Lean 4 | [`lean4/`](../../../../verification/lean4/ResearchPapersVerification/Section2_PreprintNSE/README.md) | `lake build && lake exe check` | min (cached s) |
| Coq | [`coq/`](../../../../verification/coq/section2_preprint/README.md) | `coqc verification/coq/section2_preprint/CorrectionB.v` | s |
| Isabelle | [`isabelle/`](../../../../verification/isabelle/Section2_PreprintNSE/README.md) | `isabelle build -D verification/isabelle` | min (first) |
| Agda | [`agda/`](../../../../verification/agda/Section2_PreprintNSE/README.md) | `agda --safe verification/agda/Section2_PreprintNSE/CorrectionB.agda` | s |
| C++ | [`cpp/`](../../../../verification/cpp/section2_preprint/README.md) | `cmake -S verification/cpp -B build && ./build/section2_preprint` | < 1 s |
| Rust | [`rust/`](../../../../verification/rust/section2_preprint/README.md) | `cargo run --release -p section2_preprint` | < 1 s |
| Haskell | [`haskell/`](../../../../verification/haskell/Section2_PreprintNSE/README.md) | `cabal run section2-PreprintNSE` | < 1 s |

Section 2 is the structural mirror of the preprint's argument: every analytic step of the regularity proof appears here as a checkable numeric assertion, and every formal kernel mirrors the same steps as lemmas. If any link of this section fails, the preprint's chain has a gap — which is precisely why it is asserted in eleven languages instead of one.

## 🔗 Cross-references

- [Section 2 reference port](../../../../verification/section2_preprint/README.md)
- [Framework hub](../../../../verification/README.md)
- [Gap ledger (Lean 4)](../../../../verification/lean4/TODO_sorry.md) — which
  formal lemmas are admitted gaps

---

---

Navigation: [repository root](../../../../README.md) · [ResearchPapersVerification](../../../../verification/lean4/README.md) · [IPL-RP-1.0](../../../../LICENSE.md)

*Part of [wild8highlander/navier-stokes-b](https://github.com/wild8highlander/navier-stokes-b) - (c) 2026 Isaev Iskhak Khamzatovich, all rights reserved.*

