# Ⓜ️ `lean4/` — the Lean 4 Formal Verification Layer

> **Navigation:** [`verification`](../README.md) › **`lean4`**

![Lean 4](https://img.shields.io/badge/Lean%204-v4.14-1284BA?style=flat-square&logo=leanpub&logoColor=white)
![Mathlib](https://img.shields.io/badge/Mathlib4-pinned-1284BA?style=flat-square)
![Sections](https://img.shields.io/badge/Sections-6-9558B2?style=flat-square)
![License](https://img.shields.io/badge/License-IPL--RP--1.0-red?style=flat-square)

This directory carries the **Lean 4 (v4.14) formal-verification layer** of
the framework: machine-checked proofs built on the **Mathlib4** foundation,
with the research objects defined in a custom `ResearchPapersVerification`
library. It is the largest formal artifact in the repository — six research
sections of lemmas, an aggregator module, a numerical-bridge executable,
and an honest, itemised ledger of the admitted gaps.

The hybrid strategy is deliberate: Mathlib supplies the standard
mathematical infrastructure (real analysis, matrices, normed spaces), while
`Common/Foundation.lean` introduces the research-specific objects — the
polarization correction *b* as a closed-form real constant, the rotation
angle θ_b, the cross-product matrix construction, the Hofstadter-type
spectral scaffolding — so each section file states and proves exactly the
lemmas that matter, in exact arithmetic, with no floating point anywhere in
the formal statements.

**The checked core includes:** positivity and upper-boundedness of
`bCorrection` (`bCorrection_pos`, `bCorrection_lt_one`), the trigonometric
identity `sin θ_b = b` via `Real.sin_arcsin`, the unit-norm axis vector
`eZ`, the skew-symmetric cross matrix, and the per-section structures
listed in the development map below. **The admitted gaps** — every
remaining `sorry` — are enumerated with commentary in
[`TODO_sorry.md`](TODO_sorry.md); nothing is hidden behind unconditional
axioms.

## The six section ports

| Port | Module | Focus |
|---|---|---|
| [Section 1](ResearchPapersVerification/Section1_CorrectionB/README.md) | `Section1_CorrectionB/Basic.lean` | Correction b — the universal polarization constant: rotation algebra, sine identity |
| [Section 2](ResearchPapersVerification/Section2_PreprintNSE/README.md) | `Section2_PreprintNSE/ProofChain.lean` | Preprint NSE — the regularity argument chain |
| [Section 3](ResearchPapersVerification/Section3_ABCloud/README.md) | `Section3_ABCloud/HofstadterHamiltonian.lean` | AB-Cloud — the non-Hermitian Hofstadter Hamiltonian |
| [Section 4](ResearchPapersVerification/Section4_KdV/README.md) | `Section4_KdV/Soliton.lean` | KdV — soliton interactions under the b-correction |
| [Section 5](ResearchPapersVerification/Section5_KleinAttractor/README.md) | `Section5_KleinAttractor/KleinQuartic.lean` | Klein attractor — ergodic dynamics and the NSE bridge |
| [Section 6](ResearchPapersVerification/Section6_RiemannZeros/README.md) | `Section6_RiemannZeros/HilbertPolya.lean` | Riemann zeros — the Hilbert–Pólya programme |

## Contents

| File | Description |
|---|---|
| [`Main.lean`](Main.lean) | type-check entry point — imports and elaborates the whole library |
| [`Test.lean`](Test.lean) | numerical-bridge executable — prints the reference values |
| [`lakefile.lean`](lakefile.lean) | Lake package manifest — library/executable targets |
| [`lean-toolchain`](lean-toolchain) | the elan toolchain pin (byte-exact reproducibility) |
| [`TODO_sorry.md`](TODO_sorry.md) | the honest, itemised ledger of all admitted gaps |
| [`ResearchPapersVerification/`](ResearchPapersVerification/README.md) | the proof library — aggregator, common foundation, six section modules |

## How to run

```bash
cd verification/lean4
lake build && lake exe check     # whole library, machine-checked
lake exe test                    # the numerical bridge prints reference values
```

First build downloads Mathlib4 artifacts (several GB of cache); subsequent
builds are incremental and fast. If installing the toolchain is
inconvenient, use the pinned Docker image
([`docker/lean4/`](../docker/README.md)) or rely on CI: the
extended-languages workflow compiles the development on every push with
exactly the pinned toolchain.

## 🧱 The foundation file, annotated

[`ResearchPapersVerification/Common/Foundation.lean`](ResearchPapersVerification/README.md)
is the root of the development:

```lean
def bCorrection : ℝ := Real.pi / (4 * Real.pi^2 + 2 * Real.pi * Real.sqrt 3)
```

The constant is a **definition**, not a floating-point literal — every
theorem about it is a theorem about the exact closed form (algebraically
identical to `1/(4π + 2√3)`; note π/(4π² + 2π√3) = 1/(4π + 2√3)). The
bounds are closed by `nlinarith`/`linarith` from `Real.pi_pos`:

- `bCorrection_pos : 0 < bCorrection` — closed;
- `bCorrection_lt_one : bCorrection < 1` — closed except the auxiliary
  `Real.pi < 4` estimate (ledger item 1).

Section 1 then builds the geometry on this base: the unit axis `eZ`, the
`crossMatrix` constructor, the Rodrigues rotation, and the corrected
rotation `R_b` with `R_b_orthogonal` and `R_b_det_one` (generalised
orthogonality is a tracked `sorry` — the ledger records exactly which).
The trigonometric bridge `sin_θ_b_eq_b` is fully closed via
`Real.sin_arcsin`. The numeric interval estimates (`b_gt_007`, `b_lt_008`)
are planned as *strengthened* interval-arithmetic statements:
4π + 2√3 ∈ (15.8, 16.3) ⇒ b ∈ (0.0613, 0.0633) — stronger than the
current formulations and compatible with the recorded value
b = 0.06238119….

## 🧾 The gap ledger, precisely

[`TODO_sorry.md`](TODO_sorry.md) is the working contract of what remains.
At the current count it lists **13 `sorry`s** (proof obligations awaiting
discharge — mostly numerical estimates and general orthogonality/det
lemmas), **12 `axiom … : True` placeholders** (mechanical replacements:
`theorem … := trivial`, pending), and **4 genuine open-problem axioms**
(expected to remain open; explicitly annotated). Each entry carries a
difficulty estimate. The convention: as lemmas close, they are struck
from the ledger **in the same commit** — the ledger never lies about the
current state. The expected closure order: mechanical stubs first, then
the numeric estimates (`Real.pi < 4`; the b-interval via interval
tactics), then the general Rodrigues lemmas
(`rodrigues_orthogonal`, `rodrigues_det`).

## 🔁 Same lemmas, three other kernels

The Lean statements have deliberate mirrors: Coq's `CorrectionB.v` proves
`bCorrection_pos`/`b_lt_one` from `Reals` with `lra`; Isabelle's
`CorrectionB.thy` re-expresses them over `Complex_Main` in Isar; Agda's
`CorrectionB.agda` constructs them dependently over explicitly postulated
π and √3. When the four disagree about a statement's provability, that
disagreement is itself information — and the PASS/JSON contract makes the
computational echo of the same statements checkable in seven more
ecosystems (see the [framework hub](../README.md)).

## 🔗 See also

- [the framework hub](../README.md) — the two-tier picture and the
  contract;
- [`coq/`](../coq/README.md) · [`isabelle/`](../isabelle/README.md) ·
  [`agda/`](../agda/README.md) — the same statements in three other
  kernels;
- the [gap ledger](TODO_sorry.md) — the working list of admitted gaps;
- [`data/results/baseline/`](../../data/results/baseline/README.md) — the
  numeric baselines the computational echo must reproduce.


## Statement-fidelity checklist (for reviewers diffing against the papers)

1. the constant: the Lean definition is the exact closed form — confirm it
   matches the paper's formula symbol-by-symbol (both are
   `1/(4π + 2√3)`, whether written `π/(4π²+2π√3)` or divided out);
2. the bounds: `bCorrection_pos` and `bCorrection_lt_one` are the formal
   faces of the paper's 0 < b < 1; the strengthened interval form
   (b ∈ (0.0613, 0.0633)) is the planned replacement per the ledger;
3. the angle: `sin_θ_b_eq_b` is closed via `Real.sin_arcsin` — compare
   against the paper's definition θ_b := arcsin(b);
4. the rotation: `R_b_orthogonal` / `R_b_det_one` (partly ledger-tracked)
   mirror the paper's "the rotation is a rotation" lemma;
5. the audit trail: every closed lemma here must appear as `PASS` in the
   computational echo — cross-check with
   [`verification/section1_correction_b/`](../section1_correction_b/README.md).

## Environment tips

- **Mathlib cache:** `lake exe cache get` before the first build saves the
  multi-gigabyte Mathlib build; CI does this implicitly;
- **toolchain pinning:** `lean-toolchain` is byte-pinned; elan reads it and
  refuses drift — do not "temporarily" bump it in a PR that also changes
  proofs;
- **editor:** VS Code + the lean4 extension reads the same `lean-toolchain`
  pin; the `.lake/` directory is git-ignored build state.

## When a build fails

| Error shape | Meaning | First response |
|---|---|---|
| `unknown identifier 'bCorrection'` | import path changed | check `ResearchPapersVerification/Common/Foundation.lean` is imported |
| kernel error after a Mathlib bump | upstream rename | pin back or port; never `sorry` to green |
| `declaration uses 'sorry'` warning | expected for ledger items | confirm the item is in [`TODO_sorry.md`](TODO_sorry.md); a warning *not* in the ledger is a bug |

---

Navigation: [verification](../README.md) · [repository root](../../README.md) · [IPL-RP-1.0](../../LICENSE.md)

*Part of [wild8highlander/navier-stokes-b](https://github.com/wild8highlander/navier-stokes-b) — © 2026 Isaev Iskhak Khamzatovich, all rights reserved.*
