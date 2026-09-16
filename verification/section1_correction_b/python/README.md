# 🐍 Section 1 · python — the Reference Port

> **Navigation:** [`verification`](../../README.md) › [`section1_correction_b`](../README.md) › **`python`**

![Python](https://img.shields.io/badge/Python-3.10--3.12-3776AB?style=flat-square&logo=python&logoColor=white) ![License](https://img.shields.io/badge/License-IPL--RP--1.0-red?style=flat-square)

The **pure-Python port** of Section 1 — Correction b — the Universal Polarization Constant. A single
`verify.py` using only the standard library: it computes the section's
quantities from closed-form inputs, asserts the section's properties, and
prints the framework's JSON verdict. This is the port CI runs first and the
one new toolchain ports are compared against.

## 🔬 Section context

Section 1 covers **the universal polarization correction derived from the Kirchhoff point-vortex system**; central quantities: b = 1/(4π + 2√3) = 0.062381194121028…, the rotation angle θ_b = arcsin(b) ≈ 3.5765°, and the stabilisation identity cos²θ_b + sin²θ_b = 1.
Peers: [Lean 4](../../../verification/lean4/ResearchPapersVerification/Section1_CorrectionB/README.md) · [Coq/Rocq](../../../verification/coq/section1_correction_b/README.md) · [Isabelle-HOL](../../../verification/isabelle/Section1_CorrectionB/README.md) · [Agda](../../../verification/agda/Section1_CorrectionB/README.md) · [C++](../../../verification/cpp/section1_correction_b/README.md) · [Rust](../../../verification/rust/section1_correction_b/README.md) · [Haskell](../../../verification/haskell/Section1_CorrectionB/README.md).

| File | Description |
|---|---|
| [`verify.py`](verify.py) | the Section 1 reference verifier — prints values, asserts, JSON verdict |

## ▶️ How to run

```bash
python3 verify.py          # from this folder
python3 verification/section1_correction_b/python/verify.py   # from the repo root
```

## 🔍 Sample output

```text
=== Section 1 ===
b = 0.062381194121028
PASS
```

Exit code 0 = all assertions passed; anything else fails CI.

## 📋 What is asserted

1. **b well-defined and positive** — the closed form evaluates and satisfies 0 < b;
2. **b < 1** — the twist stays within the physical range;
3. **sin θ_b = b** — holds for θ_b = arcsin b (the trigonometric bridge);
4. **rotation sanity** — the associated Rodrigues rotation is orthogonal with det 1 (the numeric echo of the formal R_b_orthogonal / R_b_det_one).

---

---

Navigation: [section parent](../README.md) · [framework hub](../../README.md) · [IPL-RP-1.0](../../../LICENSE.md)

*Part of [wild8highlander/navier-stokes-b](https://github.com/wild8highlander/navier-stokes-b) - (c) 2026 Isaev Iskhak Khamzatovich, all rights reserved.*

