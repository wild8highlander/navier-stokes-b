# 🧩 Lean 4 · ResearchPapersVerification — the Proof Library

> **Navigation:** [`verification`](../../README.md) › [`lean4`](../README.md) › **`ResearchPapersVerification`**

![Lean 4](https://img.shields.io/badge/Lean%204-v4.14-informational?style=flat-square&logo=leanpub&logoColor=white) ![License](https://img.shields.io/badge/License-IPL--RP--1.0-red?style=flat-square)

The **proof library** of the Lean 4 layer: this is the module tree that `Main.lean` imports and type-checks. `Basic.lean` (the aggregator at this level) re-exports the six section modules; [`Common/Foundation.lean`](Common/README.md) defines the shared research objects once — the correction `bCorrection` with its closed form and proved bounds — so every section builds on the same foundation rather than restating it.

Each `SectionN_*` module below states the lemmas of its research section in Lean 4 + Mathlib4 style: definitional equalities, explicit numeric bridges (`bReference = 0.0785`), and the theorems that connect them (`sin_θ_b_eq_b` via `Real.sin_arcsin`, cross-matrix constructions, spectral scaffolding). Every `sorry` that remains in these files is recorded in [`../TODO_sorry.md`](../TODO_sorry.md) with context and a closure plan.

## 📂 Contents — What Lives Here

| File | Size | Description |
|---|---|---|
| [`Basic.lean`](Basic.lean) | 511 B | aggregator module — re-exports the section modules |
| [`Common/`](Common/) | — | shared foundation — bCorrection, constants, base lemmas |
| [`Section1_CorrectionB/`](Section1_CorrectionB/) | — | Section 1 module — correction-b lemmas |
| [`Section2_PreprintNSE/`](Section2_PreprintNSE/) | — | Section 2 module — NSE regularity chain |
| [`Section3_ABCloud/`](Section3_ABCloud/) | — | Section 3 module — AB-Cloud structures |
| [`Section4_KdV/`](Section4_KdV/) | — | Section 4 module — KdV soliton scaffolding |
| [`Section5_KleinAttractor/`](Section5_KleinAttractor/) | — | Section 5 module — Klein attractor dynamics |
| [`Section6_RiemannZeros/`](Section6_RiemannZeros/) | — | Section 6 module — Riemann-zeros correspondence |

## 🗂 Directory Layout

```
ResearchPapersVerification/
├── Common/   # 2 files
│   ├── Foundation.lean
│   └── README.md  (this file)
├── Section1_CorrectionB/   # 2 files
│   ├── Basic.lean
│   └── README.md  (this file)
├── Section2_PreprintNSE/   # 2 files
│   ├── ProofChain.lean
│   └── README.md  (this file)
├── Section3_ABCloud/   # 2 files
│   ├── HofstadterHamiltonian.lean
│   └── README.md  (this file)
├── Section4_KdV/   # 2 files
│   ├── README.md  (this file)
│   └── Soliton.lean
├── Section5_KleinAttractor/   # 2 files
│   ├── KleinQuartic.lean
│   └── README.md  (this file)
├── Section6_RiemannZeros/   # 2 files
│   ├── HilbertPolya.lean
│   └── README.md  (this file)
├── Basic.lean
└── README.md  (this file)
```

## 🔗 Cross-References

- [Lean 4 layer README](../README.md)
- [Gap ledger — TODO_sorry.md](../TODO_sorry.md)

## 🇷🇺 Краткое резюме (Russian Summary)

Библиотека доказательств Lean 4: агрегатор Basic.lean, общая база Common/Foundation.lean и шесть модулей-разделов; все sorry задокументированы в TODO_sorry.md.

---

<div align="center">

**[⬆ Back to top](#-lean-4--researchpapersverification--the-proof-library)** · 
**[Repository root](../../README.md)**

*Part of [wild8highlander/navier-stokes-b](https://github.com/wild8highlander/navier-stokes-b) · Licensed under [IPL-RP-1.0](https://github.com/wild8highlander/navier-stokes-b/blob/main/LICENSE.md) — All Rights Reserved*

</div>
<!-- doc-enhancer:block v1 (автоматический блок; файлы лицензии не затрагиваются) -->

---

## 🧭 Навигация и быстрые ссылки (auto)

- 🏠 [Корень репозитория](../../../../README.md)
- 📖 [Как верифицируются утверждения](../../../../verification/README.md)
- 📄 [Статьи (PDF)](../../../../papers/README.md) · 📚 [Монографии](../../../../docs/README.md) · 🧾 [LaTeX](../../../../src/README.md)
- ⚖️ [Лицензия IPL-RP-1.0](../../../../LICENSE.md) — просмотр, одна резервная копия и цитирование с атрибуцией разрешены; остальное — только с письменного согласия автора.

*Блок добавлен автоматически (`doc-enhancer v1`); к лицензии отношения не имеет и её не изменяет. Повторный запуск скрипта блок не дублирует.*

