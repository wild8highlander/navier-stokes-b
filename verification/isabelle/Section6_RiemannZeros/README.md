# Isabelle-HOL · Section 6 — Riemann Zeros

> **Navigation:** [`verification`](../../../verification/README.md) › **`Section6_RiemannZeros`**

![Isabelle-HOL](https://img.shields.io/badge/Isabelle--HOL-2024-1284BA?style=flat-square) ![Section](https://img.shields.io/badge/Section-6-9558B2?style=flat-square) ![License](https://img.shields.io/badge/License-IPL--RP--1.0-red?style=flat-square)

The **Isabelle-HOL port of Section 6** — Riemann Zeros — the Hilbert–Pólya Programme. This folder is
an **independent Isabelle-HOL theory** over `Complex_Main`, written afresh in Isar. It is deliberately not a translation of the Lean file: agreement between the two is evidence about the mathematics, not tautology.

## 🔬 Section context — where this port sits

**Where it sits.** Section 6 of the framework covers **the ζ-correspondence skeleton: the frozen-data embedding and the spectral statistics of the zeros**. Its
central quantities are the frozen-data embedding, the GUE-class gap statistics of the zeros, and the Σ²(L) diagnostics. The same assertions exist in every
peer language of the matrix, each in its own idiom: [Python](../../../verification/section6_riemann_zeros/README.md) · [Lean 4](../../../verification/lean4/ResearchPapersVerification/Section6_RiemannZeros/README.md) · [Coq/Rocq](../../../verification/coq/section6_riemann_zeros/README.md) · [Agda](../../../verification/agda/Section6_RiemannZeros/README.md) · [C++](../../../verification/cpp/section6_riemann_zeros/README.md) · [Rust](../../../verification/rust/section6_riemann_zeros/README.md) · [Haskell](../../../verification/haskell/Section6_RiemannZeros/README.md). Agreement
between all ports is enforced by the cross-language validator
([`tests/`](../../../verification/tests/README.md)) and fails CI on any
disagreement.

**What you will see.** Run this port and you get: a banner identifying the
section and language; the computed values at full precision; one
`[PASS]`/`[FAIL]` line per assertion; and a final
`JSON: {"section": 6, "language": "isabelle", "values": {…}, "all_passed": …}`
verdict line. Exit status is 0 only when every assertion passed.

## 📂 Contents

| File | Description |
|---|---|
| [`RiemannZeros.thy`](RiemannZeros.thy) | the section 6 port — Riemann Zeros — the Hilbert–Pólya Programme |

## ▶️ How to run

```bash
cd verification/isabelle
isabelle build -D .                          # whole session
isabelle jedit -l HOL Section6_RiemannZeros/RiemannZeros.thy     # interactive
```

## 📋 What is asserted

1. **frozen-data embedding** — the embedding of the frozen data is compatible with the required structure (the formal counterpart: embedding_compatibility);
2. **GUE-class gaps** — the normalised gap statistics fall in the GUE class;
3. **Σ²(L) diagnostics** — the variance statistic matches the declared reference curve.

## 🔍 Sample output

```text
$ cd verification/isabelle
=== Section 6 ===
embedding compatible
GUE class confirmed
PASS
```

## 🧩 The port family

| Port | Where | Command | Time |
|---|---|---|---|
| Python (reference) | [`python/`](../../../verification/section6_riemann_zeros/README.md) | `python3 verification/section6_riemann_zeros/python/verify.py` | < 1 s |
| Lean 4 | [`lean4/`](../../../verification/lean4/ResearchPapersVerification/Section6_RiemannZeros/README.md) | `lake build && lake exe check` | min (cached s) |
| Coq | [`coq/`](../../../verification/coq/section6_riemann_zeros/README.md) | `coqc verification/coq/section6_riemann_zeros/CorrectionB.v` | s |
| Isabelle | [`isabelle/`](../../../verification/isabelle/Section6_RiemannZeros/README.md) | `isabelle build -D verification/isabelle` | min (first) |
| Agda | [`agda/`](../../../verification/agda/Section6_RiemannZeros/README.md) | `agda --safe verification/agda/Section6_RiemannZeros/CorrectionB.agda` | s |
| C++ | [`cpp/`](../../../verification/cpp/section6_riemann_zeros/README.md) | `cmake -S verification/cpp -B build && ./build/section6_riemann_zeros` | < 1 s |
| Rust | [`rust/`](../../../verification/rust/section6_riemann_zeros/README.md) | `cargo run --release -p section6_riemann_zeros` | < 1 s |
| Haskell | [`haskell/`](../../../verification/haskell/Section6_RiemannZeros/README.md) | `cabal run section6-RiemannZeros` | < 1 s |

Section 6 is the framework's outlook section: the Hilbert–Pólya programme is where the b-geometry and the spectral theory of the zeta function touch. The assertions here are scaffolding, not a proof of the Riemann hypothesis — they record exactly which structural facts the embedding needs, which is what makes an honest open problem auditable.

## 🔗 Cross-references

- [Section 6 reference port](../../../verification/section6_riemann_zeros/README.md)
- [Framework hub](../../../verification/README.md)
- [Gap ledger (Lean 4)](../../../verification/lean4/TODO_sorry.md) — which
  formal lemmas are admitted gaps

---

---

Navigation: [repository root](../../../README.md) · [isabelle](../../../verification/isabelle/README.md) · [IPL-RP-1.0](../../../LICENSE.md)

*Part of [wild8highlander/navier-stokes-b](https://github.com/wild8highlander/navier-stokes-b) - (c) 2026 Isaev Iskhak Khamzatovich, all rights reserved.*

