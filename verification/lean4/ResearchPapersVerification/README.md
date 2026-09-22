# Ⓜ️ `lean4/ResearchPapersVerification/` — the Lean Proof Library

> **Navigation:** [`lean4`](../../README.md) › **`ResearchPapersVerification`**

![Lean 4](https://img.shields.io/badge/Lean%204-v4.14-1284BA?style=flat-square&logo=leanpub&logoColor=white)
![Modules](https://img.shields.io/badge/Modules-9-9558B2?style=flat-square) ![License](https://img.shields.io/badge/License-IPL--RP--1.0-red?style=flat-square)

The **`ResearchPapersVerification` library** — the Lean package that holds
the entire formal development: the aggregator module, the common
foundation, and the six per-section modules. Everything under
[`verification/lean4/`](../../README.md) that is not build plumbing lives
here.

## Module map

| Module | Section | Contents |
|---|---|---|
| [`Common/`](Common/README.md) | — | `Foundation.lean`: the constant, the angle, the cross matrix, the shared lemmas |
| [`Section1_CorrectionB/`](Section1_CorrectionB/README.md) | 1 | the rotation algebra, the sine identity |
| [`Section2_PreprintNSE/`](Section2_PreprintNSE/README.md) | 2 | the regularity chain scaffolding |
| [`Section3_ABCloud/`](Section3_ABCloud/README.md) | 3 | the Hofstadter structure lemmas |
| [`Section4_KdV/`](Section4_KdV/README.md) | 4 | the soliton interaction identities |
| [`Section5_KleinAttractor/`](Section5_KleinAttractor/README.md) | 5 | the attractor structural facts |
| [`Section6_RiemannZeros/`](Section6_RiemannZeros/README.md) | 6 | the embedding compatibility |
| [`Basic.lean`](Basic.lean) | — | the aggregator — imports all sections |

## Build

```bash
cd verification/lean4 && lake build && lake exe check
```

Per-file status (closed lemmas vs `sorry` vs axiom) is tracked in
[`TODO_sorry.md`](../TODO_sorry.md) — the ledger is the module map's
second dimension.

---

---

Navigation: [lean4](../../README.md) · [gap ledger](../TODO_sorry.md) · [framework hub](../../../verification/README.md) · [IPL-RP-1.0](../../../LICENSE.md)

*Part of [wild8highlander/navier-stokes-b](https://github.com/wild8highlander/navier-stokes-b) - (c) 2026 Isaev Iskhak Khamzatovich, all rights reserved.*

