# 🐍 Section 4 — KdV (Python Reference)

> **Navigation:** [`verification`](../README.md) › **`section4_kdv`**

![Python](https://img.shields.io/badge/Python-3.10--3.12-3776AB?style=flat-square&logo=python&logoColor=white) ![Section](https://img.shields.io/badge/Section-4-9558B2?style=flat-square) ![License](https://img.shields.io/badge/License-IPL--RP--1.0-red?style=flat-square)

This directory is the **Python reference implementation** of research
Section 4 — KdV — Soliton Interactions under the b-Correction. Within the framework it is the *numerical
reference tier*: the simplest, dependency-free port that every other
language port can be diffed against. The implementation is intentionally
minimal — pure standard library, a single `verify.py` entry point under
[`python/`](python/README.md), and the framework's uniform output contract:
the computed quantities are printed, each expected property is asserted
with a `[PASS]` line, and the run ends with the `JSON:` verdict.

## 🔬 What this section covers

**Coverage.** Section 4 covers **soliton interactions of the Korteweg–de Vries equation under the b-correction: the integrable continuation of the program**. Central quantities:
the conserved quantities (mass, momentum, energy) across the two-soliton interaction, and the closed-form sech² soliton profile. The same assertions live in every peer language:
[Lean 4](../../verification/lean4/ResearchPapersVerification/Section4_KdV/README.md) · [Coq/Rocq](../../verification/coq/section4_kdv/README.md) · [Isabelle-HOL](../../verification/isabelle/Section4_KdV/README.md) · [Agda](../../verification/agda/Section4_KdV/README.md) · [C++](../../verification/cpp/section4_kdv/README.md) · [Rust](../../verification/rust/section4_kdv/README.md) · [Haskell](../../verification/haskell/Section4_KdV/README.md).

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

1. **conservation across the interaction** — the conserved quantities measured before and after the two-soliton collision agree to tolerance;
2. **closed-form soliton** — the sech² profile substituted into KdV satisfies the equation (the formal counterpart is soliton_solves_KdV);
3. **phase shift bookkeeping** — the interaction's phase shifts are recorded and match the integrable theory.

## 🔍 Sample output

```text
$ python3 verification/section4_kdv/python/verify.py
=== Section 4 ===
mass conserved: |dM| = 3.1e-13
sech^2 residual = 2.4e-12
PASS
```

## 🧩 The port family

| Port | Where | Command | Time |
|---|---|---|---|
| Python (reference) | [`python/`](../../verification/section4_kdv/README.md) | `python3 verification/section4_kdv/python/verify.py` | < 1 s |
| Lean 4 | [`lean4/`](../../verification/lean4/ResearchPapersVerification/Section4_KdV/README.md) | `lake build && lake exe check` | min (cached s) |
| Coq | [`coq/`](../../verification/coq/section4_kdv/README.md) | `coqc verification/coq/section4_kdv/CorrectionB.v` | s |
| Isabelle | [`isabelle/`](../../verification/isabelle/Section4_KdV/README.md) | `isabelle build -D verification/isabelle` | min (first) |
| Agda | [`agda/`](../../verification/agda/Section4_KdV/README.md) | `agda --safe verification/agda/Section4_KdV/CorrectionB.agda` | s |
| C++ | [`cpp/`](../../verification/cpp/section4_kdv/README.md) | `cmake -S verification/cpp -B build && ./build/section4_kdv` | < 1 s |
| Rust | [`rust/`](../../verification/rust/section4_kdv/README.md) | `cargo run --release -p section4_kdv` | < 1 s |
| Haskell | [`haskell/`](../../verification/haskell/Section4_KdV/README.md) | `cabal run section4-KdV` | < 1 s |

Section 4 is the integrable-systems bridge of the program: the KdV chapter (papers/kdv) claims the same constant b governs soliton interactions, and this section is where that claim is executable. The C++ port is the computational workhorse here — the pseudospectral solver — while every other port checks the conservation bookkeeping on the closed-form solutions.

---

---

Navigation: [repository root](../../README.md) · [framework hub](../README.md) · [section 4 peers](../../verification/README.md) · [IPL-RP-1.0](../../LICENSE.md)

*Part of [wild8highlander/navier-stokes-b](https://github.com/wild8highlander/navier-stokes-b) - (c) 2026 Isaev Iskhak Khamzatovich, all rights reserved.*

