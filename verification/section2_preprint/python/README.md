# 🐍 Section 2 · python — the Reference Port

> **Navigation:** [`verification`](../../README.md) › [`section2_preprint`](../README.md) › **`python`**

![Python](https://img.shields.io/badge/Python-3.10--3.12-3776AB?style=flat-square&logo=python&logoColor=white) ![License](https://img.shields.io/badge/License-IPL--RP--1.0-red?style=flat-square)

The **pure-Python port** of Section 2 — Preprint NSE — the Regularity Argument Chain. A single
`verify.py` using only the standard library: it computes the section's
quantities from closed-form inputs, asserts the section's properties, and
prints the framework's JSON verdict. This is the port CI runs first and the
one new toolchain ports are compared against.

## 🔬 Section context

Section 2 covers **the NSE regularity argument chain of the preprint: the twist as a unitary rearrangement and the bound it produces**; central quantities: the twist operator on u, the identity ω′ = cos θ_b · ω, and the ordered estimates that close the regularity argument.
Peers: [Lean 4](../../../verification/lean4/ResearchPapersVerification/Section2_PreprintNSE/README.md) · [Coq/Rocq](../../../verification/coq/section2_preprint/README.md) · [Isabelle-HOL](../../../verification/isabelle/Section2_PreprintNSE/README.md) · [Agda](../../../verification/agda/Section2_PreprintNSE/README.md) · [C++](../../../verification/cpp/section2_preprint/README.md) · [Rust](../../../verification/rust/section2_preprint/README.md) · [Haskell](../../../verification/haskell/Section2_PreprintNSE/README.md).

| File | Description |
|---|---|
| [`verify.py`](verify.py) | the Section 2 reference verifier — prints values, asserts, JSON verdict |

## ▶️ How to run

```bash
python3 verify.py          # from this folder
python3 verification/section2_preprint/python/verify.py   # from the repo root
```

## 🔍 Sample output

```text
=== Section 2 ===
||Twist(u)|| = ||u||
BKM factor = 0.96695
PASS
```

Exit code 0 = all assertions passed; anything else fails CI.

## 📋 What is asserted

1. **twist unitarity** — the b-twist preserves the L2 norm of the velocity field (the Leray projection absorbs the gradient part);
2. **BKM bound under the twist** — the BKM integral decreases once the rotation is applied — no energy is injected;
3. **estimate ordering** — the chain of inequalities used by the regularity argument holds in the stated order.

---

---

Navigation: [section parent](../README.md) · [framework hub](../../README.md) · [IPL-RP-1.0](../../../LICENSE.md)

*Part of [wild8highlander/navier-stokes-b](https://github.com/wild8highlander/navier-stokes-b) - (c) 2026 Isaev Iskhak Khamzatovich, all rights reserved.*

