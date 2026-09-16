# Haskell · Section 1 — Correction b

> **Navigation:** [`verification`](../../../verification/README.md) › **`Section1_CorrectionB`**

![Haskell](https://img.shields.io/badge/Haskell-GHC_9.4-5E5086?style=flat-square&logo=haskell&logoColor=white) ![Section](https://img.shields.io/badge/Section-1-9558B2?style=flat-square) ![License](https://img.shields.io/badge/License-IPL--RP--1.0-red?style=flat-square)

The **Haskell port of Section 1** — Correction b — the Universal Polarization Constant. This folder is
a **pure Haskell (GHC 9.4) executable** in its own Cabal package. The section contract is expressed as types and pure functions — no `unsafe`, no FFI — making the port readable as an executable specification.

## 🔬 Section context — where this port sits

**Where it sits.** Section 1 of the framework covers **the universal polarization correction derived from the Kirchhoff point-vortex system**. Its
central quantities are b = 1/(4π + 2√3) = 0.062381194121028…, the rotation angle θ_b = arcsin(b) ≈ 3.5765°, and the stabilisation identity cos²θ_b + sin²θ_b = 1. The same assertions exist in every
peer language of the matrix, each in its own idiom: [Python](../../../verification/section1_correction_b/README.md) · [Lean 4](../../../verification/lean4/ResearchPapersVerification/Section1_CorrectionB/README.md) · [Coq/Rocq](../../../verification/coq/section1_correction_b/README.md) · [Isabelle-HOL](../../../verification/isabelle/Section1_CorrectionB/README.md) · [Agda](../../../verification/agda/Section1_CorrectionB/README.md) · [C++](../../../verification/cpp/section1_correction_b/README.md) · [Rust](../../../verification/rust/section1_correction_b/README.md). Agreement
between all ports is enforced by the cross-language validator
([`tests/`](../../../verification/tests/README.md)) and fails CI on any
disagreement.

**What you will see.** Run this port and you get: a banner identifying the
section and language; the computed values at full precision; one
`[PASS]`/`[FAIL]` line per assertion; and a final
`JSON: {"section": 1, "language": "haskell", "values": {…}, "all_passed": …}`
verdict line. Exit status is 0 only when every assertion passed.

## 📂 Contents

| File | Description |
|---|---|
| [`src/Main.hs`](src/Main.hs) | the section 1 port — Correction b — the Universal Polarization Constant |
| [`Section1_CorrectionB.cabal`](Section1_CorrectionB.cabal) | the crate/package manifest |

## ▶️ How to run

```bash
cd verification/haskell
cabal build                                  # all six packages
cabal run section1-correction-b               # this section
```

## 📋 What is asserted

1. **b well-defined and positive** — the closed form evaluates and satisfies 0 < b;
2. **b < 1** — the twist stays within the physical range;
3. **sin θ_b = b** — holds for θ_b = arcsin b (the trigonometric bridge);
4. **rotation sanity** — the associated Rodrigues rotation is orthogonal with det 1 (the numeric echo of the formal R_b_orthogonal / R_b_det_one).

## 🔍 Sample output

```text
$ cd verification/haskell
=== Section 1 ===
b = 0.062381194121028
PASS
```

## 🧩 The port family

| Port | Where | Command | Time |
|---|---|---|---|
| Python (reference) | [`python/`](../../../verification/section1_correction_b/README.md) | `python3 verification/section1_correction_b/python/verify.py` | < 1 s |
| Lean 4 | [`lean4/`](../../../verification/lean4/ResearchPapersVerification/Section1_CorrectionB/README.md) | `lake build && lake exe check` | min (cached s) |
| Coq | [`coq/`](../../../verification/coq/section1_correction_b/README.md) | `coqc verification/coq/section1_correction_b/CorrectionB.v` | s |
| Isabelle | [`isabelle/`](../../../verification/isabelle/Section1_CorrectionB/README.md) | `isabelle build -D verification/isabelle` | min (first) |
| Agda | [`agda/`](../../../verification/agda/Section1_CorrectionB/README.md) | `agda --safe verification/agda/Section1_CorrectionB/CorrectionB.agda` | s |
| C++ | [`cpp/`](../../../verification/cpp/section1_correction_b/README.md) | `cmake -S verification/cpp -B build && ./build/section1_correction_b` | < 1 s |
| Rust | [`rust/`](../../../verification/rust/section1_correction_b/README.md) | `cargo run --release -p section1_correction_b` | < 1 s |
| Haskell | [`haskell/`](../../../verification/haskell/Section1_CorrectionB/README.md) | `cabal run section1-CorrectionB` | < 1 s |

Section 1 is the framework's keystone: every other section references the constant it fixes. Its four assertions are the minimal complete characterisation of b for the framework's purposes — anything more belongs to the papers, anything less breaks the chain. When porting to a new language, Section 1 is the correct first target: fastest to write, easiest to diff, and it immediately joins the new language into the validator's matrix.

## 🔗 Cross-references

- [Section 1 reference port](../../../verification/section1_correction_b/README.md)
- [Framework hub](../../../verification/README.md)
- [Gap ledger (Lean 4)](../../../verification/lean4/TODO_sorry.md) — which
  formal lemmas are admitted gaps

---

---

Navigation: [repository root](../../../README.md) · [haskell](../../../verification/haskell/README.md) · [IPL-RP-1.0](../../../LICENSE.md)

*Part of [wild8highlander/navier-stokes-b](https://github.com/wild8highlander/navier-stokes-b) - (c) 2026 Isaev Iskhak Khamzatovich, all rights reserved.*

