# Ⓜ️ Lean 4 — Formal/Numerical Verification Layer

> **Navigation:** [`verification`](../README.md) › **`lean4`**

![Lean 4](https://img.shields.io/badge/Lean%204-v4.14-informational?style=flat-square&logo=leanpub&logoColor=white) ![License](https://img.shields.io/badge/License-IPL--RP--1.0-red?style=flat-square) ![Sections](https://img.shields.io/badge/Sections-6-blue?style=flat-square)

This directory carries the **Lean 4 (v4.14) formal-verification layer** of the framework: machine-checked proofs built on the **Mathlib4** foundation, with the research objects defined in a custom `ResearchPapersVerification` library. The development is the largest formal artifact in the repository — six research sections of lemmas, an aggregator module, a numerical-bridge executable and an honest, itemised list of the admitted gaps.

The hybrid strategy is deliberate: Mathlib supplies the standard mathematical infrastructure (real analysis, matrices, normed spaces), while `Common/Foundation.lean` introduces the research-specific objects — the polarization correction *b* as a closed-form real constant, the rotation angle θ_b, the cross-product matrix construction, the Hofstadter-type spectral scaffolding — so each section file can state and prove exactly the lemmas that matter.

**The checked core includes:** positivity and upper-boundedness of `bCorrection` (`bCorrection_pos`, `bCorrection_lt_one`), the trigonometric identity `sin θ_b = b` via `Real.sin_arcsin`, the unit-norm axis vector `eZ`, the skew-symmetric cross matrix, and the per-section structures listed in the module tree below. **The admitted gaps** — every remaining `sorry` — are enumerated with commentary in [`TODO_sorry.md`](TODO_sorry.md); nothing is hidden behind unconditional axioms.

Build with `lake build`; run the type-check executable with `lake exe check` and the numerical bridge with `lake exe test`. CI builds this directory in `ci-extended-languages.yml` with the toolchain pinned by `lean-toolchain`.

| [`ResearchPapersVerification/`](ResearchPapersVerification/README.md) | the proof library — aggregator, common foundation and the six section modules |
| [`Main.lean`](Main.lean) / [`Test.lean`](Test.lean) | type-check entry point and the numerical-bridge executable |
| [`TODO_sorry.md`](TODO_sorry.md) | the honest, itemised ledger of all admitted gaps |

## 🗂 The Six Section Ports

- [`ResearchPapersVerification/Section1_CorrectionB/`](ResearchPapersVerification/Section1_CorrectionB/README.md) — Correction b — the Universal Polarization Constant
- [`ResearchPapersVerification/Section2_PreprintNSE/`](ResearchPapersVerification/Section2_PreprintNSE/README.md) — Preprint NSE — the Regularity Argument Chain
- [`ResearchPapersVerification/Section3_ABCloud/`](ResearchPapersVerification/Section3_ABCloud/README.md) — AB-Cloud — the Non-Hermitian Hofstadter Hamiltonian
- [`ResearchPapersVerification/Section4_KdV/`](ResearchPapersVerification/Section4_KdV/README.md) — KdV — Soliton Interactions under the b-Correction
- [`ResearchPapersVerification/Section5_KleinAttractor/`](ResearchPapersVerification/Section5_KleinAttractor/README.md) — Klein Attractor — Ergodic Dynamics and the NSE Bridge
- [`ResearchPapersVerification/Section6_RiemannZeros/`](ResearchPapersVerification/Section6_RiemannZeros/README.md) — Riemann Zeros — the Hilbert–Pólya Programme

## 📂 Contents — What Lives Here

| File | Size | Description |
|---|---|---|
| [`Main.lean`](Main.lean) | 160 B | type-check entry point — imports and elaborates the whole library |
| [`ResearchPapersVerification/`](ResearchPapersVerification/) | — | subdirectory with 16 files (see its own README) |
| [`TODO_sorry.md`](TODO_sorry.md) | 6.5 KB | # Список незавершённых доказательств Lean 4 > Этот файл содержит полный перечень всех `sorry` (теорем с пропущенными > доказательствами) и `axiom` (аксиоматизированных утверждений)… |
| [`Test.lean`](Test.lean) | 169 B | numerical bridge executable — prints reference values |
| [`lakefile.lean`](lakefile.lean) | 508 B | Lake package manifest — library/executable targets |
| [`lean-toolchain`](lean-toolchain) | 25 B | Lean toolchain pin (elan reads this file) |

## 🗂 Directory Layout

```
lean4/
├── ResearchPapersVerification/   # 16 files
│   ├── Common/   # 2 files
│   │   ├── Foundation.lean
│   │   └── README.md  (this file)
│   ├── Section1_CorrectionB/   # 2 files
│   │   ├── Basic.lean
│   │   └── README.md  (this file)
│   ├── Section2_PreprintNSE/   # 2 files
│   │   ├── ProofChain.lean
│   │   └── README.md  (this file)
│   ├── Section3_ABCloud/   # 2 files
│   │   ├── HofstadterHamiltonian.lean
│   │   └── README.md  (this file)
│   ├── Section4_KdV/   # 2 files
│   │   ├── README.md  (this file)
│   │   └── Soliton.lean
│   ├── Section5_KleinAttractor/   # 2 files
│   │   ├── KleinQuartic.lean
│   │   └── README.md  (this file)
│   ├── Section6_RiemannZeros/   # 2 files
│   │   ├── HilbertPolya.lean
│   │   └── README.md  (this file)
│   ├── Basic.lean
│   └── README.md  (this file)
├── lakefile.lean
├── lean-toolchain
├── Main.lean
├── README.md  (this file)
├── Test.lean
└── TODO_sorry.md
```

## ▶️ How to Run

```bash
cd verification/lean4
lake build && lake exe check
```
Build step: `lake build`.

## 🇷🇺 Краткое резюме (Russian Summary)

**verification/lean4/** — слой верификации на Lean 4 (v4.14): машинно проверяемые доказательства на базе Mathlib4 с собственными определениями. Шесть портов по разделам (1: Correction b, 2: Preprint NSE, 3: AB-Cloud, 4: KdV, 5: Klein Attractor, 6: Riemann Zeros); единый контракт PASS/JSON; команды сборки — в разделе How to Run.

---

<div align="center">

**[⬆ Back to top](#-lean-4--formalnumerical-verification-layer)** · 
**[Repository root](../README.md)**

*Part of [wild8highlander/navier-stokes-b](https://github.com/wild8highlander/navier-stokes-b) · Licensed under [IPL-RP-1.0](https://github.com/wild8highlander/navier-stokes-b/blob/main/LICENSE.md) — All Rights Reserved*

</div>

---
## 🧱 The Foundation File, Annotated

[`ResearchPapersVerification/Common/Foundation.lean`](ResearchPapersVerification/Common/Foundation.lean) is the root of the Lean development. Its anatomy, worth understanding before reading anything else:

```lean
def bCorrection : ℝ := Real.pi / (4 * Real.pi^2 + 2 * Real.pi * Real.sqrt 3)
```

The constant is a **definition**, not a floating-point literal — every theorem about it is a theorem about the exact closed form. Positivity and the bound are closed by `nlinarith`/`linarith` from `Real.pi_pos`:

- `bCorrection_pos : 0 < bCorrection` — closed;
- `bCorrection_lt_one : bCorrection < 1` — closed except the auxiliary `Real.pi < 4` estimate (ledger item 1).

Section 1 then builds the geometry on this base: the unit axis `eZ`, the `crossMatrix` constructor, the Rodrigues rotation, and the corrected rotation `R_b` with `R_b_orthogonal` and `R_b_det_one` (the orthogonality generalises via a `sorry`-ed lemma — ledger items track exactly which). The trigonometric bridge `sin_θ_b_eq_b` is fully closed via `Real.sin_arcsin`.

## 🗺 Development Map

| File | Contents | Status |
|---|---|---|
| `Common/Foundation.lean` | the constant, its bounds | 1 admitted estimate |
| `Section1_CorrectionB/Basic.lean` | rotation algebra, sine identity | core closed, numeric bounds open |
| `Section2_PreprintNSE/` | the regularity chain scaffolding | per-lemma status in file |
| `Section3_ABCloud/HofstadterHamiltonian.lean` | Hofstadter structure lemmas | structural core |
| `Section4_KdV/Soliton.lean` | soliton interaction identities | structural core |
| `Section5_KleinAttractor/KleinQuartic.lean` | attractor structural facts | structural core |
| `Section6_RiemannZeros/HilbertPolya.lean` | embedding compatibility | structural core |

## 🧾 The Gap Ledger, Precisely

[`TODO_sorry.md`](TODO_sorry.md) is the working contract of what remains. At the current count it lists **13 `sorry`s** (proof obligations awaiting discharge — mostly numerical estimates like `b_gt_007`/`b_lt_008` and general orthogonality/determinant lemmas), **12 `axiom … : True` placeholders** (mechanical replacements, `theorem … := trivial`, pending), and **4 genuine open-problem axioms** that are expected to remain. Each entry carries a difficulty estimate. The convention: as lemmas close, they are struck from the ledger in the same commit — the ledger never lies about the current state.

## 🔁 Same Lemmas, Three Other Kernels

The Lean statements have deliberate mirrors: Coq's `CorrectionB.v` proves `bCorrection_pos`/`b_lt_one` from `Reals` with `lra`; Isabelle's `CorrectionB.thy` re-expresses them over `Complex_Main` in Isar; Agda's `CorrectionB.agda` constructs them dependently over an explicitly postulated π and √3. When the four disagree about a statement's provability, that disagreement is itself information — and the JSON/PASS contract makes the computational echo of the same statements checkable in seven more ecosystems.

## 🐳 Running Lean Without Installing It

If installing the toolchain locally is inconvenient, two pinned alternatives exist:

```bash
# the Docker image (see ../docker/lean4/Dockerfile)
docker build -t rp-lean4 verification/docker/lean4
docker run --rm -v "$PWD":/work rp-lean4 lake exe check

# or read-only: the CI job in ci-extended-languages.yml compiles the development on every push
```

---
## 🎯 What Lean Closes First

When working through the ledger, the expected closure order (by difficulty, per `TODO_sorry.md`): the `axiom … : True` stubs first (mechanical), then the auxiliary numeric estimates (`Real.pi < 4` inside `bCorrection_lt_one`; `b_gt_007`/`b_lt_008` via interval tactics), then the general Rodrigues lemmas (`rodrigues_orthogonal`, `rodrigues_det`). The four open-problem axioms are out of scope by definition. Contributing a closure: strike the ledger line in the same commit, per the ledger's own contract.

---
## 🔗 See Also

- the root README's [formal deep dive](../../README.md#-appendix-w--formal-verification-deep-dive) — the annotated Foundation file;
- [`coq/`](../coq/README.md) · [`isabelle/`](../isabelle/README.md) · [`agda/`](../agda/README.md) — the same statements in three other kernels;
- the [gap ledger](TODO_sorry.md) — the working list of admitted gaps.

<!-- doc-enhancer:block v1 (автоматический блок; файлы лицензии не затрагиваются) -->

---

## 🧭 Навигация и быстрые ссылки (auto)

- 🏠 [Корень репозитория](../../../README.md)
- 📖 [Как верифицируются утверждения](../../../verification/README.md)
- 📄 [Статьи (PDF)](../../../papers/README.md) · 📚 [Монографии](../../../docs/README.md) · 🧾 [LaTeX](../../../src/README.md)
- ⚖️ [Лицензия IPL-RP-1.0](../../../LICENSE.md) — просмотр, одна резервная копия и цитирование с атрибуцией разрешены; остальное — только с письменного согласия автора.

*Блок добавлен автоматически (`doc-enhancer v1`); к лицензии отношения не имеет и её не изменяет. Повторный запуск скрипта блок не дублирует.*

