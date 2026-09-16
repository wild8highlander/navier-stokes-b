# 🐍 Section 5 — Klein Attractor (Python Reference)

> **Navigation:** [`verification`](../README.md) › **`section5_klein_attractor`**

![Python](https://img.shields.io/badge/Python-3.10--3.12-3776AB?style=flat-square&logo=python&logoColor=white) ![Section](https://img.shields.io/badge/Section-5-9558B2?style=flat-square) ![License](https://img.shields.io/badge/License-IPL--RP--1.0-red?style=flat-square)

This directory is the **Python reference implementation** of research
Section 5 — Klein Attractor — Ergodic Dynamics and the NSE Bridge. Within the framework it is the *numerical
reference tier*: the simplest, dependency-free port that every other
language port can be diffed against. The implementation is intentionally
minimal — pure standard library, a single `verify.py` entry point under
[`python/`](python/README.md), and the framework's uniform output contract:
the computed quantities are printed, each expected property is asserted
with a `[PASS]` line, and the run ends with the `JSON:` verdict.

## 🔬 What this section covers

**Coverage.** Section 5 covers **the Klein attractor: ergodic statistics over the reference ensemble and the bridge back to the NSE program**. Central quantities:
the Klein closure Z = exp(b·β_K·L_min) = 1.351637344385124…, the invariant statistics of the reference ensemble, and the contraction statements. The same assertions live in every peer language:
[Lean 4](../../verification/lean4/ResearchPapersVerification/Section5_KleinAttractor/README.md) · [Coq/Rocq](../../verification/coq/section5_klein_attractor/README.md) · [Isabelle-HOL](../../verification/isabelle/Section5_KleinAttractor/README.md) · [Agda](../../verification/agda/Section5_KleinAttractor/README.md) · [C++](../../verification/cpp/section5_klein_attractor/README.md) · [Rust](../../verification/rust/section5_klein_attractor/README.md) · [Haskell](../../verification/haskell/Section5_KleinAttractor/README.md).

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

1. **invariant statistics** — the reference ensemble's statistics are invariant under the dynamics;
2. **contraction** — the declared contraction statements hold — the attractor absorbs the transients;
3. **the NSE bridge** — the closure Z enters the NSE-side estimates in the role the monograph assigns it.

## 🔍 Sample output

```text
$ python3 verification/section5_klein_attractor/python/verify.py
=== Section 5 ===
Z = 1.351637344385124
contraction holds
PASS
```

## 🧩 The port family

| Port | Where | Command | Time |
|---|---|---|---|
| Python (reference) | [`python/`](../../verification/section5_klein_attractor/README.md) | `python3 verification/section5_klein_attractor/python/verify.py` | < 1 s |
| Lean 4 | [`lean4/`](../../verification/lean4/ResearchPapersVerification/Section5_KleinAttractor/README.md) | `lake build && lake exe check` | min (cached s) |
| Coq | [`coq/`](../../verification/coq/section5_klein_attractor/README.md) | `coqc verification/coq/section5_klein_attractor/CorrectionB.v` | s |
| Isabelle | [`isabelle/`](../../verification/isabelle/Section5_KleinAttractor/README.md) | `isabelle build -D verification/isabelle` | min (first) |
| Agda | [`agda/`](../../verification/agda/Section5_KleinAttractor/README.md) | `agda --safe verification/agda/Section5_KleinAttractor/CorrectionB.agda` | s |
| C++ | [`cpp/`](../../verification/cpp/section5_klein_attractor/README.md) | `cmake -S verification/cpp -B build && ./build/section5_klein_attractor` | < 1 s |
| Rust | [`rust/`](../../verification/rust/section5_klein_attractor/README.md) | `cargo run --release -p section5_klein_attractor` | < 1 s |
| Haskell | [`haskell/`](../../verification/haskell/Section5_KleinAttractor/README.md) | `cabal run section5-KleinAttractor` | < 1 s |

Section 5 documents the attractor side of the program: the place where the geometric mechanism and the statistical mechanics meet. Its contraction statements are what make the ensemble averages of the monograph legitimate, and its closure constant Z is one of the few quantities the framework pins at 50 digits (see L1 of the verification chain).

---

---

Navigation: [repository root](../../README.md) · [framework hub](../README.md) · [section 5 peers](../../verification/README.md) · [IPL-RP-1.0](../../LICENSE.md)

*Part of [wild8highlander/navier-stokes-b](https://github.com/wild8highlander/navier-stokes-b) - (c) 2026 Isaev Iskhak Khamzatovich, all rights reserved.*

