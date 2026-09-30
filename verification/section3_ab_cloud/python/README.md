# 🐍 Section 3 · python — the Reference Port

> **Navigation:** [`verification`](../../README.md) › [`section3_ab_cloud`](../README.md) › **`python`**

![Python](https://img.shields.io/badge/Python-3.10--3.12-3776AB?style=flat-square&logo=python&logoColor=white) ![License](https://img.shields.io/badge/License-IPL--RP--1.0-red?style=flat-square)

The **pure-Python port** of Section 3 — AB-Cloud — the Non-Hermitian Hofstadter Hamiltonian. A single
`verify.py` using only the standard library: it computes the section's
quantities from closed-form inputs, asserts the section's properties, and
prints the framework's JSON verdict. This is the port CI runs first and the
one new toolchain ports are compared against.

## 🔬 Section context

Section 3 covers **the structural core of the AB-Cloud Hamiltonian at reduced scale: the presuppositions of the heavy spectral statistics**; central quantities: the Peierls phase e^{2πi/7}, the flux-quantisation lattice, and the GUE-class spacing statistics.
Peers: [Lean 4](../../../verification/lean4/ResearchPapersVerification/Section3_ABCloud/README.md) · [Coq/Rocq](../../../verification/coq/section3_ab_cloud/README.md) · [Isabelle-HOL](../../../verification/isabelle/Section3_ABCloud/README.md) · [Agda](../../../verification/agda/Section3_ABCloud/README.md) · [C++](../../../verification/cpp/section3_ab_cloud/README.md) · [Rust](../../../verification/rust/section3_ab_cloud/README.md) · [Haskell](../../../verification/haskell/Section3_ABCloud/README.md).

| File | Description |
|---|---|
| [`verify.py`](verify.py) | the Section 3 reference verifier — prints values, asserts, JSON verdict |

## ▶️ How to run

```bash
python3 verify.py          # from this folder
python3 verification/section3_ab_cloud/python/verify.py   # from the repo root
```

## 🔍 Sample output

```text
=== Section 3 ===
|phase| = 1.0, order = 7
flux quantised
PASS
```

Exit code 0 = all assertions passed; anything else fails CI.

## 📋 What is asserted

1. **Peierls phase** — |e^{2πi/7}| = 1 and the phase has exact order 7;
2. **flux quantisation** — the flux per plaquette is quantised in units of the flux quantum — the Hamiltonian is well defined on the lattice;
3. **Hermiticity and symmetry classes** — the reduced Hamiltonian has the declared symmetry class and the GUE spacing statistic is normalised.

---

---

Navigation: [section parent](../README.md) · [framework hub](../../README.md) · [IPL-RP-1.0](../../../LICENSE.md)

*Part of [wild8highlander/navier-stokes-b](https://github.com/wild8highlander/navier-stokes-b) - (c) 2026 Isaev Iskhak Khamzatovich, all rights reserved.*

