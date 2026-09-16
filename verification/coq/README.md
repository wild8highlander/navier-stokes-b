# Ⓜ️ Coq/Rocq — Formal/Numerical Verification Layer

> **Navigation:** [`verification`](../README.md) › **`coq`**

![Coq/Rocq](https://img.shields.io/badge/Coq/Rocq-8.18-informational?style=flat-square&logo=ocaml&logoColor=white) ![License](https://img.shields.io/badge/License-IPL--RP--1.0-red?style=flat-square) ![Sections](https://img.shields.io/badge/Sections-6-blue?style=flat-square)

This directory carries the **Coq/Rocq (8.18) formal-verification layer**: one proof file per research section, built on the standard library's `Reals` with `lra`/`nra` automation. The development favours classical real analysis — `b_correction` is a first-class `R`, its positivity proved via `Rdiv_lt_0_compat` with `PI_pos`, and the trigonometric identity chain exercised through `sqrt_def` and `lra`.

Each section file is self-contained: open it, `Require` it, or `Compute` the constants directly (the files intentionally call `Compute b_correction` so the value is printed during compilation — a reviewer sees the number as the proof compiles). Admitted branches are marked with explicit `admit`/`Admitted` and are documented in the per-section READMEs and in the framework's gap ledger, keeping the checked/unchecked boundary visible.

Build per file with `coqc` (see `_CoqProject` for the file list), or drop the folder into CoqIDE/Proof Everything. CI compiles every file in `ci-extended-languages.yml`.

## 🗂 The Six Section Ports

- [`section1_correction_b/`](section1_correction_b/README.md) — Correction b — the Universal Polarization Constant
- [`section2_preprint/`](section2_preprint/README.md) — Preprint NSE — the Regularity Argument Chain
- [`section3_ab_cloud/`](section3_ab_cloud/README.md) — AB-Cloud — the Non-Hermitian Hofstadter Hamiltonian
- [`section4_kdv/`](section4_kdv/README.md) — KdV — Soliton Interactions under the b-Correction
- [`section5_klein_attractor/`](section5_klein_attractor/README.md) — Klein Attractor — Ergodic Dynamics and the NSE Bridge
- [`section6_riemann_zeros/`](section6_riemann_zeros/README.md) — Riemann Zeros — the Hilbert–Pólya Programme

## 📂 Contents — What Lives Here

| File | Size | Description |
|---|---|---|
| [`_CoqProject`](_CoqProject) | 221 B | Coq project file — lists the .v sources for coq_makefile |
| [`section1_correction_b/`](section1_correction_b/) | — | Section 1 port — Correction b — the Universal Polarization Constant |
| [`section2_preprint/`](section2_preprint/) | — | Section 2 port — Preprint NSE — the Regularity Argument Chain |
| [`section3_ab_cloud/`](section3_ab_cloud/) | — | Section 3 port — AB-Cloud — the Non-Hermitian Hofstadter Hamiltonian |
| [`section4_kdv/`](section4_kdv/) | — | Section 4 port — KdV — Soliton Interactions under the b-Correction |
| [`section5_klein_attractor/`](section5_klein_attractor/) | — | Section 5 port — Klein Attractor — Ergodic Dynamics and the NSE Bridge |
| [`section6_riemann_zeros/`](section6_riemann_zeros/) | — | Section 6 port — Riemann Zeros — the Hilbert–Pólya Programme |

## 🗂 Directory Layout

```
coq/
├── section1_correction_b/   # 2 files
│   ├── CorrectionB.v
│   └── README.md  (this file)
├── section2_preprint/   # 2 files
│   ├── ProofChain.v
│   └── README.md  (this file)
├── section3_ab_cloud/   # 2 files
│   ├── Hofstadter.v
│   └── README.md  (this file)
├── section4_kdv/   # 2 files
│   ├── KdV.v
│   └── README.md  (this file)
├── section5_klein_attractor/   # 2 files
│   ├── Klein.v
│   └── README.md  (this file)
├── section6_riemann_zeros/   # 2 files
│   ├── README.md  (this file)
│   └── RiemannZeros.v
├── _CoqProject
└── README.md  (this file)
```

## ▶️ How to Run

```bash
cd verification/coq
coqc <file>.v (per section file)
```
Build step: `coq_makefile or per-file coqc`.

## 🇷🇺 Краткое резюме (Russian Summary)

**verification/coq/** — слой верификации на Coq/Rocq (8.18): доказательства на стандартной библиотеке Reals с автоматизацией lra/nra. Шесть портов по разделам (1: Correction b, 2: Preprint NSE, 3: AB-Cloud, 4: KdV, 5: Klein Attractor, 6: Riemann Zeros); единый контракт PASS/JSON; команды сборки — в разделе How to Run.

---

<div align="center">

**[⬆ Back to top](#-coqrocq--formalnumerical-verification-layer)** · 
**[Repository root](../README.md)**

*Part of [wild8highlander/navier-stokes-b](https://github.com/wild8highlander/navier-stokes-b) · Licensed under [IPL-RP-1.0](https://github.com/wild8highlander/navier-stokes-b/blob/main/LICENSE.md) — All Rights Reserved*

</div>

---
## 🧱 Development Anatomy

Six independent developments, one per section, classical-logic style:

| File | Section | Notable lemmas | Automation |
|---|---|---|---|
| `section1_correction_b/CorrectionB.v` | 1 | `bCorrection_pos`, `bCorrection_lt_one` | `lra` over `Reals` |
| `section2_preprint/ProofChain.v` | 2 | chain ordering lemmas | `lra` |
| `section3_ab_cloud/Hofstadter.v` | 3 | flux quantisation, Hermiticity | `lia` + field_simps |
| `section4_kdv/KdV.v` | 4 | conservation identities | `lra` |
| `section5_klein_attractor/Klein.v` | 5 | contraction statements | `lra` |
| `section6_riemann_zeros/RiemannZeros.v` | 6 | embedding compatibility | `lra` |

The build order is exactly the order in [`_CoqProject`](_CoqProject); each file is self-contained modulo the standard library — no cross-file imports — which keeps per-file compilation independent and CI parallelisable.

## 🐳 Running Coq Without Installing It

```bash
docker build -t rp-coq verification/docker/coq
docker run --rm -v "$PWD":/work rp-coq coqc verification/coq/section1_correction_b/CorrectionB.v
```

Or read the CI job: `ci-extended-languages.yml` compiles all six files on every push, so a regression in any of them surfaces in the cheapest possible gate.

---
## 🎯 What Coq Covers Uniquely

The Coq development is the classical-logic witness: where Agda constructs and Isabelle structures, Coq compresses — the `lra`-automated `Reals` proofs show the statements' content is *routine classical mathematics*, which is itself a useful signal (the hard part is the modelling, not the arithmetic). When diffing against Lean, expect the same lemma names modulo naming conventions and the same proof obligations modulo automation.

---
## 🔗 See Also

- [`lean4/`](../lean4/README.md) — the primary formal development this mirrors;
- the `_CoqProject` build order — the canonical compile sequence;
- Section × Language [matrix](../../README.md#-верификация-на-11-языках) — where each `v` file sits.

<!-- doc-enhancer:block v1 (автоматический блок; файлы лицензии не затрагиваются) -->

---

## 🧭 Навигация и быстрые ссылки (auto)

- 🏠 [Корень репозитория](../../../README.md)
- 📖 [Как верифицируются утверждения](../../../verification/README.md)
- 📄 [Статьи (PDF)](../../../papers/README.md) · 📚 [Монографии](../../../docs/README.md) · 🧾 [LaTeX](../../../src/README.md)
- ⚖️ [Лицензия IPL-RP-1.0](../../../LICENSE.md) — просмотр, одна резервная копия и цитирование с атрибуцией разрешены; остальное — только с письменного согласия автора.

*Блок добавлен автоматически (`doc-enhancer v1`); к лицензии отношения не имеет и её не изменяет. Повторный запуск скрипта блок не дублирует.*

