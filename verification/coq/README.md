# Ⓜ️ `coq/` — the Coq/Rocq Formal Verification Layer

> **Navigation:** [`verification`](../README.md) › **`coq`**

![Coq/Rocq](https://img.shields.io/badge/Coq%2FRocq-8.18-DC8447?style=flat-square&logo=ocaml&logoColor=white)
![Sections](https://img.shields.io/badge/Sections-6-9558B2?style=flat-square)
![License](https://img.shields.io/badge/License-IPL--RP--1.0-red?style=flat-square)

This directory carries the **Coq/Rocq (8.18) formal-verification layer**:
one proof file per research section, built on the standard library's
`Reals` with `lra`/`nra` automation. The development favours classical
real analysis — `b_correction` is a first-class `R`, its positivity proved
via `Rdiv_lt_0_compat` with `PI_pos`, and the trigonometric identity chain
exercised through `sqrt_def` and `lra`.

Each section file is self-contained: open it, `Require` it, or `Compute`
the constants directly — the files intentionally call
`Compute b_correction`, so the numeric value prints *during compilation*
and a reviewer watches the number appear as the proof builds. Admitted
branches are marked with explicit `Admitted` and are documented in the
per-section READMEs and the framework's gap ledger, keeping the
checked/unchecked boundary visible at all times.

Build per file with `coqc` (the file list lives in
[`_CoqProject`](_CoqProject)), or drop the folder into CoqIDE/Proof
Everything. CI compiles every file in the extended-languages workflow.

## The six section ports

| Port | File | Notable lemmas | Automation |
|---|---|---|---|
| [Section 1](section1_correction_b/README.md) | `section1_correction_b/CorrectionB.v` | `bCorrection_pos`, `bCorrection_lt_one` | `lra` over `Reals` |
| [Section 2](section2_preprint/README.md) | `section2_preprint/ProofChain.v` | chain ordering lemmas | `lra` |
| [Section 3](section3_ab_cloud/README.md) | `section3_ab_cloud/Hofstadter.v` | flux quantisation, Hermiticity | `lia` + field simplifications |
| [Section 4](section4_kdv/README.md) | `section4_kdv/KdV.v` | conservation identities | `lra` |
| [Section 5](section5_klein_attractor/README.md) | `section5_klein_attractor/Klein.v` | contraction statements | `lra` |
| [Section 6](section6_riemann_zeros/README.md) | `section6_riemann_zeros/RiemannZeros.v` | embedding compatibility | `lra` |

## Contents

| File | Description |
|---|---|
| [`_CoqProject`](_CoqProject) | lists the `.v` sources for `coq_makefile`; also the canonical build order |
| `section1_correction_b/` … `section6_riemann_zeros/` | the six ports, each with its proof file and README |

## How to run

```bash
cd verification/coq
coq_makefile -f _CoqProject -o Makefile && make        # all six files
coqc coq/section1_correction_b/CorrectionB.v           # one file (prints Compute output)
```

The build order is exactly the order in `_CoqProject`; each file is
self-contained modulo the standard library — no cross-file imports — which
keeps per-file compilation independent and CI parallelisable. Without
installing Coq, use the pinned image: `docker build -t rp-coq
../docker/coq && docker run --rm -v "$PWD":/work rp-coq coqc
verification/coq/section1_correction_b/CorrectionB.v`.

## 🎯 What Coq covers uniquely

The Coq development is the **classical-logic witness** of the matrix:
where Agda constructs and Isabelle structures, Coq compresses — the
`lra`-automated `Reals` proofs show that the statements' content is
routine classical mathematics, which is itself a useful signal (the hard
part of the program is the modelling, not the arithmetic). When diffing
against Lean, expect the same lemma names modulo naming conventions and
the same proof obligations modulo automation. Where a statement is
`Admitted` here, the framework's ledger records it; the count matches the
[Lean ledger](../lean4/TODO_sorry.md) classes so the two kernels can be
reconciled line by line.

## 🔗 See also

- [the framework hub](../README.md) — the two-tier picture and the
  contract;
- [`lean4/`](../lean4/README.md) — the primary formal development this
  mirrors;
- [`isabelle/`](../isabelle/README.md) · [`agda/`](../agda/README.md) —
  the other two kernels;
- [`docker/coq/`](../docker/README.md) — the pinned toolchain image.


## Reading the files as a reviewer

Each `.v` file is a self-contained argument in three movements: the
**definitions** (the closed form as a `R` expression), the **statements**
(the section's claims as `Lemma`s), and the **proofs** (`lra`-automated
where the step is classical routine, hand-written where it is not). The
`Compute` calls are placed so that compiling the file prints the numeric
values into the build log — a reviewer of the CI log sees the constants
without opening a single file.

## The `_CoqProject` as the build contract

The file lists the six `.v` sources in the canonical compile order. Two
rules keep it boring: no cross-file imports (each file compiles
independently, so CI parallelises trivially), and no `Require`d external
packages beyond the standard library (the supply chain is Coq itself).

## Reconciling with the other kernels

| Question | Coq answer | Where to cross-check |
|---|---|---|
| is b positive? | `bCorrection_pos` | Lean: `bCorrection_pos`; Isabelle: `b_pos`; Agda: `b-pos` |
| is the interval known? | via `lra` on the closed form | the ledger's interval plan (b ∈ (0.0613, 0.0633)) |
| is sin θ_b = b? | through `sqrt_def` + `lra` | Lean: `sin_θ_b_eq_b` (closed) |
| what is admitted? | explicit `Admitted` | [`lean4/TODO_sorry.md`](../lean4/TODO_sorry.md) reconciles the counts |

---

Navigation: [verification](../README.md) · [repository root](../../README.md) · [IPL-RP-1.0](../../LICENSE.md)

*Part of [wild8highlander/navier-stokes-b](https://github.com/wild8highlander/navier-stokes-b) — © 2026 Isaev Iskhak Khamzatovich, all rights reserved.*
