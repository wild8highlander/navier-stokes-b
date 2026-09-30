# 🐍 Section 1 — Correction b (Python Reference)

> **Navigation:** [`verification`](../README.md) › **`section1_correction_b`**

![Python](https://img.shields.io/badge/Python-3.10--3.12-3776AB?style=flat-square&logo=python&logoColor=white) ![Section](https://img.shields.io/badge/Section-1-9558B2?style=flat-square) ![License](https://img.shields.io/badge/License-IPL--RP--1.0-red?style=flat-square)

This directory is the **Python reference implementation** of research
Section 1 — Correction b — the Universal Polarization Constant. Within the framework it is the *numerical
reference tier*: the simplest, dependency-free port that every other
language port can be diffed against. The implementation is intentionally
minimal — pure standard library, a single `verify.py` entry point under
[`python/`](python/README.md), and the framework's uniform output contract:
the computed quantities are printed, each expected property is asserted
with a `[PASS]` line, and the run ends with the `JSON:` verdict.

## 🔬 What this section covers

**Coverage.** Section 1 covers **the universal polarization correction derived from the Kirchhoff point-vortex system**. Central quantities:
b = 1/(4π + 2√3) = 0.062381194121028…, the rotation angle θ_b = arcsin(b) ≈ 3.5765°, and the stabilisation identity cos²θ_b + sin²θ_b = 1. The same assertions live in every peer language:
[Lean 4](../../verification/lean4/ResearchPapersVerification/Section1_CorrectionB/README.md) · [Coq/Rocq](../../verification/coq/section1_correction_b/README.md) · [Isabelle-HOL](../../verification/isabelle/Section1_CorrectionB/README.md) · [Agda](../../verification/agda/Section1_CorrectionB/README.md) · [C++](../../verification/cpp/section1_correction_b/README.md) · [Rust](../../verification/rust/section1_correction_b/README.md) · [Haskell](../../verification/haskell/Section1_CorrectionB/README.md).

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

1. **b well-defined and positive** — the closed form evaluates and satisfies 0 < b;
2. **b < 1** — the twist stays within the physical range;
3. **sin θ_b = b** — holds for θ_b = arcsin b (the trigonometric bridge);
4. **rotation sanity** — the associated Rodrigues rotation is orthogonal with det 1 (the numeric echo of the formal R_b_orthogonal / R_b_det_one).

## 🔍 Sample output

```text
$ python3 verification/section1_correction_b/python/verify.py
=== Section 1 ===
b = 0.062381194121028
PASS
```

## 🧩 The port family

| Port | Where | Command | Time |
|---|---|---|---|
| Python (reference) | [`python/`](../../verification/section1_correction_b/README.md) | `python3 verification/section1_correction_b/python/verify.py` | < 1 s |
| Lean 4 | [`lean4/`](../../verification/lean4/ResearchPapersVerification/Section1_CorrectionB/README.md) | `lake build && lake exe check` | min (cached s) |
| Coq | [`coq/`](../../verification/coq/section1_correction_b/README.md) | `coqc verification/coq/section1_correction_b/CorrectionB.v` | s |
| Isabelle | [`isabelle/`](../../verification/isabelle/Section1_CorrectionB/README.md) | `isabelle build -D verification/isabelle` | min (first) |
| Agda | [`agda/`](../../verification/agda/Section1_CorrectionB/README.md) | `agda --safe verification/agda/Section1_CorrectionB/CorrectionB.agda` | s |
| C++ | [`cpp/`](../../verification/cpp/section1_correction_b/README.md) | `cmake -S verification/cpp -B build && ./build/section1_correction_b` | < 1 s |
| Rust | [`rust/`](../../verification/rust/section1_correction_b/README.md) | `cargo run --release -p section1_correction_b` | < 1 s |
| Haskell | [`haskell/`](../../verification/haskell/Section1_CorrectionB/README.md) | `cabal run section1-CorrectionB` | < 1 s |

Section 1 is the framework's keystone: every other section references the constant it fixes. Its four assertions are the minimal complete characterisation of b for the framework's purposes — anything more belongs to the papers, anything less breaks the chain. When porting to a new language, Section 1 is the correct first target: fastest to write, easiest to diff, and it immediately joins the new language into the validator's matrix.

---

---

Navigation: [repository root](../../README.md) · [framework hub](../README.md) · [section 1 peers](../../verification/README.md) · [IPL-RP-1.0](../../LICENSE.md)

*Part of [wild8highlander/navier-stokes-b](https://github.com/wild8highlander/navier-stokes-b) - (c) 2026 Isaev Iskhak Khamzatovich, all rights reserved.*

