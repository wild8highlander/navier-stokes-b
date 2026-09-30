# 🐍 Section 6 — Riemann Zeros (Python Reference)

> **Navigation:** [`verification`](../README.md) › **`section6_riemann_zeros`**

![Python](https://img.shields.io/badge/Python-3.10--3.12-3776AB?style=flat-square&logo=python&logoColor=white) ![Section](https://img.shields.io/badge/Section-6-9558B2?style=flat-square) ![License](https://img.shields.io/badge/License-IPL--RP--1.0-red?style=flat-square)

This directory is the **Python reference implementation** of research
Section 6 — Riemann Zeros — the Hilbert–Pólya Programme. Within the framework it is the *numerical
reference tier*: the simplest, dependency-free port that every other
language port can be diffed against. The implementation is intentionally
minimal — pure standard library, a single `verify.py` entry point under
[`python/`](python/README.md), and the framework's uniform output contract:
the computed quantities are printed, each expected property is asserted
with a `[PASS]` line, and the run ends with the `JSON:` verdict.

## 🔬 What this section covers

**Coverage.** Section 6 covers **the ζ-correspondence skeleton: the frozen-data embedding and the spectral statistics of the zeros**. Central quantities:
the frozen-data embedding, the GUE-class gap statistics of the zeros, and the Σ²(L) diagnostics. The same assertions live in every peer language:
[Lean 4](../../verification/lean4/ResearchPapersVerification/Section6_RiemannZeros/README.md) · [Coq/Rocq](../../verification/coq/section6_riemann_zeros/README.md) · [Isabelle-HOL](../../verification/isabelle/Section6_RiemannZeros/README.md) · [Agda](../../verification/agda/Section6_RiemannZeros/README.md) · [C++](../../verification/cpp/section6_riemann_zeros/README.md) · [Rust](../../verification/rust/section6_riemann_zeros/README.md) · [Haskell](../../verification/haskell/Section6_RiemannZeros/README.md).

## 📂 Contents

| Item | Description |
|---|---|
| [`python/`](python/README.md) | the runnable reference port — a single `verify.py` |

## ▶️ How to run

```bash
python3 python/verify.py
# runtime: well under a second, no dependencies, no configuration
```

## 📋 What is asserted

1. **frozen-data embedding** — the embedding of the frozen data is compatible with the required structure (the formal counterpart: embedding_compatibility);
2. **GUE-class gaps** — the normalised gap statistics fall in the GUE class;
3. **Σ²(L) diagnostics** — the variance statistic matches the declared reference curve.

## 🔍 Sample output

```text
$ python3 verification/section6_riemann_zeros/python/verify.py
=== Section 6 ===
embedding compatible
GUE class confirmed
PASS
```

## 🧩 The port family

| Port | Where | Command | Time |
|---|---|---|---|
| Python (reference) | [`python/`](../../verification/section6_riemann_zeros/README.md) | `python3 verification/section6_riemann_zeros/python/verify.py` | < 1 s |
| Lean 4 | [`lean4/`](../../verification/lean4/ResearchPapersVerification/Section6_RiemannZeros/README.md) | `lake build && lake exe check` | min (cached s) |
| Coq | [`coq/`](../../verification/coq/section6_riemann_zeros/README.md) | `coqc verification/coq/section6_riemann_zeros/CorrectionB.v` | s |
| Isabelle | [`isabelle/`](../../verification/isabelle/Section6_RiemannZeros/README.md) | `isabelle build -D verification/isabelle` | min (first) |
| Agda | [`agda/`](../../verification/agda/Section6_RiemannZeros/README.md) | `agda --safe verification/agda/Section6_RiemannZeros/CorrectionB.agda` | s |
| C++ | [`cpp/`](../../verification/cpp/section6_riemann_zeros/README.md) | `cmake -S verification/cpp -B build && ./build/section6_riemann_zeros` | < 1 s |
| Rust | [`rust/`](../../verification/rust/section6_riemann_zeros/README.md) | `cargo run --release -p section6_riemann_zeros` | < 1 s |
| Haskell | [`haskell/`](../../verification/haskell/Section6_RiemannZeros/README.md) | `cabal run section6-RiemannZeros` | < 1 s |

Section 6 is the framework's outlook section: the Hilbert–Pólya programme is where the b-geometry and the spectral theory of the zeta function touch. The assertions here are scaffolding, not a proof of the Riemann hypothesis — they record exactly which structural facts the embedding needs, which is what makes an honest open problem auditable.

---

---

Navigation: [repository root](../../README.md) · [framework hub](../README.md) · [section 6 peers](../../verification/README.md) · [IPL-RP-1.0](../../LICENSE.md)

*Part of [wild8highlander/navier-stokes-b](https://github.com/wild8highlander/navier-stokes-b) - (c) 2026 Isaev Iskhak Khamzatovich, all rights reserved.*

