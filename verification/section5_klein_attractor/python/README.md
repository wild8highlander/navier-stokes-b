# 🐍 Section 5 · python — the Reference Port

> **Navigation:** [`verification`](../../README.md) › [`section5_klein_attractor`](../README.md) › **`python`**

![Python](https://img.shields.io/badge/Python-3.10--3.12-3776AB?style=flat-square&logo=python&logoColor=white) ![License](https://img.shields.io/badge/License-IPL--RP--1.0-red?style=flat-square)

The **pure-Python port** of Section 5 — Klein Attractor — Ergodic Dynamics and the NSE Bridge. A single
`verify.py` using only the standard library: it computes the section's
quantities from closed-form inputs, asserts the section's properties, and
prints the framework's JSON verdict. This is the port CI runs first and the
one new toolchain ports are compared against.

## 🔬 Section context

Section 5 covers **the Klein attractor: ergodic statistics over the reference ensemble and the bridge back to the NSE program**; central quantities: the Klein closure Z = exp(b·β_K·L_min) = 1.351637344385124…, the invariant statistics of the reference ensemble, and the contraction statements.
Peers: [Lean 4](../../../verification/lean4/ResearchPapersVerification/Section5_KleinAttractor/README.md) · [Coq/Rocq](../../../verification/coq/section5_klein_attractor/README.md) · [Isabelle-HOL](../../../verification/isabelle/Section5_KleinAttractor/README.md) · [Agda](../../../verification/agda/Section5_KleinAttractor/README.md) · [C++](../../../verification/cpp/section5_klein_attractor/README.md) · [Rust](../../../verification/rust/section5_klein_attractor/README.md) · [Haskell](../../../verification/haskell/Section5_KleinAttractor/README.md).

| File | Description |
|---|---|
| [`verify.py`](verify.py) | the Section 5 reference verifier — prints values, asserts, JSON verdict |

## ▶️ How to run

```bash
python3 verify.py          # from this folder
python3 verification/section5_klein_attractor/python/verify.py   # from the repo root
```

## 🔍 Sample output

```text
=== Section 5 ===
Z = 1.351637344385124
contraction holds
PASS
```

Exit code 0 = all assertions passed; anything else fails CI.

## 📋 What is asserted

1. **invariant statistics** — the reference ensemble's statistics are invariant under the dynamics;
2. **contraction** — the declared contraction statements hold — the attractor absorbs the transients;
3. **the NSE bridge** — the closure Z enters the NSE-side estimates in the role the monograph assigns it.

---

---

Navigation: [section parent](../README.md) · [framework hub](../../README.md) · [IPL-RP-1.0](../../../LICENSE.md)

*Part of [wild8highlander/navier-stokes-b](https://github.com/wild8highlander/navier-stokes-b) - (c) 2026 Isaev Iskhak Khamzatovich, all rights reserved.*

