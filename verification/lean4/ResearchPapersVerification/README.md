# `ResearchPapersVerification/` — the Lean 4 package

> **Navigation:** [repository root](../../README.md) › [verification](../../verification/README.md) › [lean4](../README.md) › **`ResearchPapersVerification`**

![Kernel](https://img.shields.io/badge/Lean_4_·_Mathlib4-informational?style=flat-square) ![Modules](https://img.shields.io/badge/8-2B579A?style=flat-square) ![License](https://img.shields.io/badge/IPL--RP--1.0-red?style=flat-square)

---

The Lean library root: `Basic.lean` imports every section module and
exposes the `totalVerifiedTheorems` counter; `Common/Foundation.lean`
carries the shared foundation (the constant, its pinned digits, the
common lemmas). Section 7 (`Section7_SmagorinskyKolmogorov/Basic.lean`)
adds the master-relation positivity, the Fibonacci scaffolding and the
(5′) coefficient algebra of the φ-audit.

| Module | Section |
|---|---|
| [`Common/`](Common/README.md) | the shared foundation |
| [`Section1_CorrectionB/`](Section1_CorrectionB/README.md) | S1 — the constant |
| [`Section2_PreprintNSE/`](Section2_PreprintNSE/README.md) | S2 — the regularity chain |
| [`Section3_ABCloud/`](Section3_ABCloud/README.md) | S3 — the Hofstadter Hamiltonian |
| [`Section4_KdV/`](Section4_KdV/README.md) | S4 — KdV |
| [`Section5_KleinAttractor/`](Section5_KleinAttractor/README.md) | S5 — the Klein attractor |
| [`Section6_RiemannZeros/`](Section6_RiemannZeros/README.md) | S6 — the Riemann zeros |
| [`Section7_SmagorinskyKolmogorov/`](Section7_SmagorinskyKolmogorov/README.md) | S7 — the master relation (new) |

## License

Part of **navier-stokes-b**, license IPL-RP-1.0. ([LICENSE.md](../../LICENSE.md)).
