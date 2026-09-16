# 🐍 Section 3 — AB-Cloud (Python Reference)

> **Navigation:** [`verification`](../README.md) › **`section3_ab_cloud`**

![Python](https://img.shields.io/badge/Python-3.10--3.12-3776AB?style=flat-square&logo=python&logoColor=white) ![Section](https://img.shields.io/badge/Section-3-9558B2?style=flat-square) ![License](https://img.shields.io/badge/License-IPL--RP--1.0-red?style=flat-square)

This directory is the **Python reference implementation** of research
Section 3 — AB-Cloud — the Non-Hermitian Hofstadter Hamiltonian. Within the framework it is the *numerical
reference tier*: the simplest, dependency-free port that every other
language port can be diffed against. The implementation is intentionally
minimal — pure standard library, a single `verify.py` entry point under
[`python/`](python/README.md), and the framework's uniform output contract:
the computed quantities are printed, each expected property is asserted
with a `[PASS]` line, and the run ends with the `JSON:` verdict.

## 🔬 What this section covers

**Coverage.** Section 3 covers **the structural core of the AB-Cloud Hamiltonian at reduced scale: the presuppositions of the heavy spectral statistics**. Central quantities:
the Peierls phase e^{2πi/7}, the flux-quantisation lattice, and the GUE-class spacing statistics. The same assertions live in every peer language:
[Lean 4](../../verification/lean4/ResearchPapersVerification/Section3_ABCloud/README.md) · [Coq/Rocq](../../verification/coq/section3_ab_cloud/README.md) · [Isabelle-HOL](../../verification/isabelle/Section3_ABCloud/README.md) · [Agda](../../verification/agda/Section3_ABCloud/README.md) · [C++](../../verification/cpp/section3_ab_cloud/README.md) · [Rust](../../verification/rust/section3_ab_cloud/README.md) · [Haskell](../../verification/haskell/Section3_ABCloud/README.md).

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

1. **Peierls phase** — |e^{2πi/7}| = 1 and the phase has exact order 7;
2. **flux quantisation** — the flux per plaquette is quantised in units of the flux quantum — the Hamiltonian is well defined on the lattice;
3. **Hermiticity and symmetry classes** — the reduced Hamiltonian has the declared symmetry class and the GUE spacing statistic is normalised.

## 🔍 Sample output

```text
$ python3 verification/section3_ab_cloud/python/verify.py
=== Section 3 ===
|phase| = 1.0, order = 7
flux quantised
PASS
```

## 🧩 The port family

| Port | Where | Command | Time |
|---|---|---|---|
| Python (reference) | [`python/`](../../verification/section3_ab_cloud/README.md) | `python3 verification/section3_ab_cloud/python/verify.py` | < 1 s |
| Lean 4 | [`lean4/`](../../verification/lean4/ResearchPapersVerification/Section3_ABCloud/README.md) | `lake build && lake exe check` | min (cached s) |
| Coq | [`coq/`](../../verification/coq/section3_ab_cloud/README.md) | `coqc verification/coq/section3_ab_cloud/CorrectionB.v` | s |
| Isabelle | [`isabelle/`](../../verification/isabelle/Section3_ABCloud/README.md) | `isabelle build -D verification/isabelle` | min (first) |
| Agda | [`agda/`](../../verification/agda/Section3_ABCloud/README.md) | `agda --safe verification/agda/Section3_ABCloud/CorrectionB.agda` | s |
| C++ | [`cpp/`](../../verification/cpp/section3_ab_cloud/README.md) | `cmake -S verification/cpp -B build && ./build/section3_ab_cloud` | < 1 s |
| Rust | [`rust/`](../../verification/rust/section3_ab_cloud/README.md) | `cargo run --release -p section3_ab_cloud` | < 1 s |
| Haskell | [`haskell/`](../../verification/haskell/Section3_ABCloud/README.md) | `cabal run section3-ABCloud` | < 1 s |

Section 3 carries the structural skeleton of the AB-Cloud program: the identities that the heavy statistics elsewhere rely on, checked at a scale small enough to audit by eye. Its assertions are deliberately elementary — their value is that they are presuppositions, and a broken presupposition must be visible long before the statistics that consume it.

---

---

Navigation: [repository root](../../README.md) · [framework hub](../README.md) · [section 3 peers](../../verification/README.md) · [IPL-RP-1.0](../../LICENSE.md)

*Part of [wild8highlander/navier-stokes-b](https://github.com/wild8highlander/navier-stokes-b) - (c) 2026 Isaev Iskhak Khamzatovich, all rights reserved.*

