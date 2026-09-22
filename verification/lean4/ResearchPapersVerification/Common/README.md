# Ⓜ️ `lean4/…/Common/` — the Foundation Module

> **Navigation:** [`lean4`](../../../README.md) › [`ResearchPapersVerification`](../README.md) › **`Common`**

![Lean 4](https://img.shields.io/badge/Lean%204-v4.14-1284BA?style=flat-square&logo=leanpub&logoColor=white) ![License](https://img.shields.io/badge/License-IPL--RP--1.0-red?style=flat-square)

The **root of the Lean development**: `Foundation.lean` defines the
research objects every section module imports.

## The file, annotated

```lean
def bCorrection : ℝ := Real.pi / (4 * Real.pi^2 + 2 * Real.pi * Real.sqrt 3)
```

The constant is a **definition**, not a floating-point literal —
algebraically identical to `1/(4π + 2√3)` — so every theorem about it is a
theorem about the exact closed form. The core lemmas:

- `bCorrection_pos : 0 < bCorrection` — closed (`nlinarith` from `Real.pi_pos`);
- `bCorrection_lt_one : bCorrection < 1` — closed except the auxiliary
  `Real.pi < 4` estimate (ledger item 1 of
  [`TODO_sorry.md`](../../TODO_sorry.md));
- the unit-norm axis `eZ`, the skew-symmetric `crossMatrix`, the Rodrigues
  rotation, and the corrected rotation `R_b` with its orthogonality and
  determinant lemmas.

## Read next

[`Section1_CorrectionB/`](../Section1_CorrectionB/README.md) builds the
geometry on this base; the
[gap ledger](../../TODO_sorry.md) records exactly which auxiliary
estimates remain admitted.

---

---

Navigation: [library](../README.md) · [lean4](../../../README.md) · [ledger](../../TODO_sorry.md) · [IPL-RP-1.0](../../../../LICENSE.md)

*Part of [wild8highlander/navier-stokes-b](https://github.com/wild8highlander/navier-stokes-b) - (c) 2026 Isaev Iskhak Khamzatovich, all rights reserved.*

