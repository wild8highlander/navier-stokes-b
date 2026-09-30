# 🐍 Section 2 — Preprint NSE (Python Reference)

> **Navigation:** [`verification`](../README.md) › **`section2_preprint`**

![Python](https://img.shields.io/badge/Python-3.10--3.12-3776AB?style=flat-square&logo=python&logoColor=white) ![Section](https://img.shields.io/badge/Section-2-9558B2?style=flat-square) ![License](https://img.shields.io/badge/License-IPL--RP--1.0-red?style=flat-square)

This directory is the **Python reference implementation** of research
Section 2 — Preprint NSE — the Regularity Argument Chain. Within the framework it is the *numerical
reference tier*: the simplest, dependency-free port that every other
language port can be diffed against. The implementation is intentionally
minimal — pure standard library, a single `verify.py` entry point under
[`python/`](python/README.md), and the framework's uniform output contract:
the computed quantities are printed, each expected property is asserted
with a `[PASS]` line, and the run ends with the `JSON:` verdict.

## 🔬 What this section covers

**Coverage.** Section 2 covers **the NSE regularity argument chain of the preprint: the twist as a unitary rearrangement and the bound it produces**. Central quantities:
the twist operator on u, the identity ω′ = cos θ_b · ω, and the ordered estimates that close the regularity argument. The same assertions live in every peer language:
[Lean 4](../../verification/lean4/ResearchPapersVerification/Section2_PreprintNSE/README.md) · [Coq/Rocq](../../verification/coq/section2_preprint/README.md) · [Isabelle-HOL](../../verification/isabelle/Section2_PreprintNSE/README.md) · [Agda](../../verification/agda/Section2_PreprintNSE/README.md) · [C++](../../verification/cpp/section2_preprint/README.md) · [Rust](../../verification/rust/section2_preprint/README.md) · [Haskell](../../verification/haskell/Section2_PreprintNSE/README.md).

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

1. **twist unitarity** — the b-twist preserves the L2 norm of the velocity field (the Leray projection absorbs the gradient part);
2. **BKM bound under the twist** — the BKM integral decreases once the rotation is applied — no energy is injected;
3. **estimate ordering** — the chain of inequalities used by the regularity argument holds in the stated order.

## 🔍 Sample output

```text
$ python3 verification/section2_preprint/python/verify.py
=== Section 2 ===
||Twist(u)|| = ||u||
BKM factor = 0.96695
PASS
```

## 🧩 The port family

| Port | Where | Command | Time |
|---|---|---|---|
| Python (reference) | [`python/`](../../verification/section2_preprint/README.md) | `python3 verification/section2_preprint/python/verify.py` | < 1 s |
| Lean 4 | [`lean4/`](../../verification/lean4/ResearchPapersVerification/Section2_PreprintNSE/README.md) | `lake build && lake exe check` | min (cached s) |
| Coq | [`coq/`](../../verification/coq/section2_preprint/README.md) | `coqc verification/coq/section2_preprint/CorrectionB.v` | s |
| Isabelle | [`isabelle/`](../../verification/isabelle/Section2_PreprintNSE/README.md) | `isabelle build -D verification/isabelle` | min (first) |
| Agda | [`agda/`](../../verification/agda/Section2_PreprintNSE/README.md) | `agda --safe verification/agda/Section2_PreprintNSE/CorrectionB.agda` | s |
| C++ | [`cpp/`](../../verification/cpp/section2_preprint/README.md) | `cmake -S verification/cpp -B build && ./build/section2_preprint` | < 1 s |
| Rust | [`rust/`](../../verification/rust/section2_preprint/README.md) | `cargo run --release -p section2_preprint` | < 1 s |
| Haskell | [`haskell/`](../../verification/haskell/Section2_PreprintNSE/README.md) | `cabal run section2-PreprintNSE` | < 1 s |

Section 2 is the structural mirror of the preprint's argument: every analytic step of the regularity proof appears here as a checkable numeric assertion, and every formal kernel mirrors the same steps as lemmas. If any link of this section fails, the preprint's chain has a gap — which is precisely why it is asserted in eleven languages instead of one.

---

---

Navigation: [repository root](../../README.md) · [framework hub](../README.md) · [section 2 peers](../../verification/README.md) · [IPL-RP-1.0](../../LICENSE.md)

*Part of [wild8highlander/navier-stokes-b](https://github.com/wild8highlander/navier-stokes-b) - (c) 2026 Isaev Iskhak Khamzatovich, all rights reserved.*

