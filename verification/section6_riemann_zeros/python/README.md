# 🐍 Section 6 · python — the Reference Port

> **Navigation:** [`verification`](../../README.md) › [`section6_riemann_zeros`](../README.md) › **`python`**

![Python](https://img.shields.io/badge/Python-3.10--3.12-3776AB?style=flat-square&logo=python&logoColor=white) ![License](https://img.shields.io/badge/License-IPL--RP--1.0-red?style=flat-square)

The **pure-Python port** of Section 6 — Riemann Zeros — the Hilbert–Pólya Programme. A single
`verify.py` using only the standard library: it computes the section's
quantities from closed-form inputs, asserts the section's properties, and
prints the framework's JSON verdict. This is the port CI runs first and the
one new toolchain ports are compared against.

## 🔬 Section context

Section 6 covers **the ζ-correspondence skeleton: the frozen-data embedding and the spectral statistics of the zeros**; central quantities: the frozen-data embedding, the GUE-class gap statistics of the zeros, and the Σ²(L) diagnostics.
Peers: [Lean 4](../../../verification/lean4/ResearchPapersVerification/Section6_RiemannZeros/README.md) · [Coq/Rocq](../../../verification/coq/section6_riemann_zeros/README.md) · [Isabelle-HOL](../../../verification/isabelle/Section6_RiemannZeros/README.md) · [Agda](../../../verification/agda/Section6_RiemannZeros/README.md) · [C++](../../../verification/cpp/section6_riemann_zeros/README.md) · [Rust](../../../verification/rust/section6_riemann_zeros/README.md) · [Haskell](../../../verification/haskell/Section6_RiemannZeros/README.md).

| File | Description |
|---|---|
| [`verify.py`](verify.py) | the Section 6 reference verifier — prints values, asserts, JSON verdict |

## ▶️ How to run

```bash
python3 verify.py          # from this folder
python3 verification/section6_riemann_zeros/python/verify.py   # from the repo root
```

## 🔍 Sample output

```text
=== Section 6 ===
embedding compatible
GUE class confirmed
PASS
```

Exit code 0 = all assertions passed; anything else fails CI.

## 📋 What is asserted

1. **frozen-data embedding** — the embedding of the frozen data is compatible with the required structure (the formal counterpart: embedding_compatibility);
2. **GUE-class gaps** — the normalised gap statistics fall in the GUE class;
3. **Σ²(L) diagnostics** — the variance statistic matches the declared reference curve.

---

---

Navigation: [section parent](../README.md) · [framework hub](../../README.md) · [IPL-RP-1.0](../../../LICENSE.md)

*Part of [wild8highlander/navier-stokes-b](https://github.com/wild8highlander/navier-stokes-b) - (c) 2026 Isaev Iskhak Khamzatovich, all rights reserved.*

