# Ⓜ️ `agda/` — the Agda Formal Verification Layer

> **Navigation:** [`verification`](../README.md) › **`agda`**

![Agda](https://img.shields.io/badge/Agda-2.6-CB6BA7?style=flat-square&logo=agda&logoColor=white)
![Sections](https://img.shields.io/badge/Sections-6-9558B2?style=flat-square)
![Safe](https://img.shields.io/badge/Flags---safe-2EA043?style=flat-square)
![License](https://img.shields.io/badge/License-IPL--RP--1.0-red?style=flat-square)

This directory carries the **Agda (2.6) formal-verification layer**: a
dependently-typed, constructive development with one module per research
section, compiled with `--safe`. Agda's contribution to the framework is
the **minimal trust base** made literal: π and √3 are explicit
`postulate`s rather than library imports, so the axioms a reader must
accept are visible in the first lines of each file — an honest, two-line
trust base beats an implicit one.

The modules define `b-correction` as a rational-expression division over
`Data.Rational`, carry the postulated positivity/bound lemmas (`b-pos`,
`b-lt-one`), and develop the per-section constructions (the PSL(2,7) proof
chain in Section 2, Hofstadter scaffolding in Section 3, and so on). The
[`agda.agda-lib`](agda.agda-lib) file registers the include roots so
`agda` resolves the `SectionN_*` modules from anywhere.

Check any module with `agda Section1_CorrectionB/CorrectionB.agda` (with
`--safe` for the CI configuration). CI type-checks the modules in the
extended-languages workflow.

## The six section ports

| Port | Module | Notes |
|---|---|---|
| [Section 1](Section1_CorrectionB/README.md) | `Section1_CorrectionB/CorrectionB.agda` | π and √3 postulated explicitly |
| [Section 2](Section2_PreprintNSE/README.md) | `Section2_PreprintNSE/ProofChain.agda` | the chain as an indexed structure |
| [Section 3](Section3_ABCloud/README.md) | `Section3_ABCloud/Hofstadter.agda` | flux structure as inductive data |
| [Section 4](Section4_KdV/README.md) | `Section4_KdV/KdV.agda` | conservation as type-level identity |
| [Section 5](Section5_KleinAttractor/README.md) | `Section5_KleinAttractor/Klein.agda` | contraction statements |
| [Section 6](Section6_RiemannZeros/README.md) | `Section6_RiemannZeros/RiemannZeros.agda` | embedding compatibility |

## Contents

| File | Description |
|---|---|
| [`agda.agda-lib`](agda.agda-lib) | library file — include roots and module list |
| `Section1_CorrectionB/` … `Section6_RiemannZeros/` | the six modules, each with its `.agda` file and README |

## How to run

```bash
cd verification/agda
agda --safe Section1_CorrectionB/CorrectionB.agda     # one module
# or, all modules in dependency order:
agda --safe Section6_RiemannZeros/RiemannZeros.agda
```

Run from the repository root or set the include path per
`agda.agda-lib`. Without installing Agda, use the pinned image
([`docker/agda/`](../docker/README.md)) or the CI job, which compiles
every module with `--safe` on each push.

## 🔬 What Agda proves about the trust base

Because π and √3 are the **only** postulates, everything else in the Agda
development is *constructed* — including the order relations and the
algebraic identities the other systems take from their standard libraries.
Reading the Agda files is therefore the fastest way to see exactly which
properties of π and √3 the whole framework's formal layer actually needs:
read the postulate block, and you have enumerated the formal trust base.
This is the same honesty policy that keeps the Lean gap ledger public —
the framework's contract with its reader is that trust is always
enumerable, never ambient.

The constructive idiom also has a practical consequence: where a classical
development might prove a disjunction by excluded middle, the Agda modules
carry the constructive content (witnesses, not just existence), which
occasionally sharpens the statements themselves.

## 🔗 See also

- [the framework hub](../README.md) — the two-tier picture and the
  contract;
- [`lean4/`](../lean4/README.md) — the primary formal development;
- [`coq/`](../coq/README.md) · [`isabelle/`](../isabelle/README.md) — the
  other kernels;
- [`docker/agda/`](../docker/README.md) — the pinned toolchain image.


## The postulate block, precisely

Every section module opens with the same two-line trust base:

- `postulate π : ℝ` with the positivity/order properties the development
  actually uses;
- `postulate √3 : ℝ` likewise.

That is the entire axiom set. Everything else — the rational arithmetic,
the order relations, the algebraic identities — is constructed. This is
why the Agda folder is the fastest read in the formal tier: the postulate
block *is* the framework's formal trust base, enumerated.

## Compilation flags and what they buy

`--safe` disables unsafe pragmas — a module that compiled with `--safe`
cannot have switched off the termination or positivity checkers. CI
compiles with `--safe` for exactly this reason; a local build without the
flag is fine for exploration but proves nothing.

## Where Agda is the right witness

| Question | Best answered by | Why |
|---|---|---|
| what does the formal layer assume? | Agda | the postulate block enumerates it |
| is the statement constructive? | Agda | witnesses are extracted by construction |
| is the proof classical-routine? | Coq | `lra` closes it — routine is signal too |
| is the statement faithful to the paper? | Isabelle | Isar blocks read like the paper |
| is everything integrated? | Lean | the aggregator + the gap ledger |

---

Navigation: [verification](../README.md) · [repository root](../../README.md) · [IPL-RP-1.0](../../LICENSE.md)

*Part of [wild8highlander/navier-stokes-b](https://github.com/wild8highlander/navier-stokes-b) — © 2026 Isaev Iskhak Khamzatovich, all rights reserved.*
