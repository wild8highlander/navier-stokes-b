# 🐍 Section 4 · python — the Reference Port

> **Navigation:** [`verification`](../../README.md) › [`section4_kdv`](../README.md) › **`python`**

![Python](https://img.shields.io/badge/Python-3.10--3.12-3776AB?style=flat-square&logo=python&logoColor=white) ![License](https://img.shields.io/badge/License-IPL--RP--1.0-red?style=flat-square)

The **pure-Python port** of Section 4 — KdV — Soliton Interactions under the b-Correction. A single
`verify.py` using only the standard library: it computes the section's
quantities from closed-form inputs, asserts the section's properties, and
prints the framework's JSON verdict. This is the port CI runs first and the
one new toolchain ports are compared against.

## 🔬 Section context

Section 4 covers **soliton interactions of the Korteweg–de Vries equation under the b-correction: the integrable continuation of the program**; central quantities: the conserved quantities (mass, momentum, energy) across the two-soliton interaction, and the closed-form sech² soliton profile.
Peers: [Lean 4](../../../verification/lean4/ResearchPapersVerification/Section4_KdV/README.md) · [Coq/Rocq](../../../verification/coq/section4_kdv/README.md) · [Isabelle-HOL](../../../verification/isabelle/Section4_KdV/README.md) · [Agda](../../../verification/agda/Section4_KdV/README.md) · [C++](../../../verification/cpp/section4_kdv/README.md) · [Rust](../../../verification/rust/section4_kdv/README.md) · [Haskell](../../../verification/haskell/Section4_KdV/README.md).

| File | Description |
|---|---|
| [`verify.py`](verify.py) | the Section 4 reference verifier — prints values, asserts, JSON verdict |

## ▶️ How to run

```bash
python3 verify.py          # from this folder
python3 verification/section4_kdv/python/verify.py   # from the repo root
```

## 🔍 Sample output

```text
=== Section 4 ===
mass conserved: |dM| = 3.1e-13
sech^2 residual = 2.4e-12
PASS
```

Exit code 0 = all assertions passed; anything else fails CI.

## 📋 What is asserted

1. **conservation across the interaction** — the conserved quantities measured before and after the two-soliton collision agree to tolerance;
2. **closed-form soliton** — the sech² profile substituted into KdV satisfies the equation (the formal counterpart is soliton_solves_KdV);
3. **phase shift bookkeeping** — the interaction's phase shifts are recorded and match the integrable theory.

---

---

Navigation: [section parent](../README.md) · [framework hub](../../README.md) · [IPL-RP-1.0](../../../LICENSE.md)

*Part of [wild8highlander/navier-stokes-b](https://github.com/wild8highlander/navier-stokes-b) - (c) 2026 Isaev Iskhak Khamzatovich, all rights reserved.*

