# Ⓜ️ `isabelle/` — the Isabelle-HOL Formal Verification Layer

> **Navigation:** [`verification`](../README.md) › **`isabelle`**

![Isabelle-HOL](https://img.shields.io/badge/Isabelle--HOL-2024-1284BA?style=flat-square)
![Sections](https://img.shields.io/badge/Sections-6-9558B2?style=flat-square)
![License](https://img.shields.io/badge/License-IPL--RP--1.0-red?style=flat-square)

This directory carries the **Isabelle-HOL (2024) formal-verification
layer**: one theory file per research section, each stated over
`Complex_Main` and registered in the session [`ROOT`](ROOT). Isabelle's
role in the framework is **independence** — the statements are written
afresh in Isar style, not translated from the Coq or Lean sources, so
agreement between systems is evidence, not tautology.

The theories define `b_correction` as a real constant
(`pi / (4 * pi^2 + 2 * pi * sqrt 3)`, algebraically the same closed form as
`1/(4π + 2√3)`), prove `b_pos` from `pi_gt_zero` with `divide_pos_pos`,
exercise `value "b_correction"` so the numeric value prints during session
build, and chain the trigonometric identities (`sin_theta_eq_b` via
`theta_b = arcsin b_correction`). Admitted branches use explicit `sorry`
and are itemised in the framework's gap ledger.

Build the session with `isabelle build -D .`, or open any theory with
`isabelle jedit -l HOL`. CI builds the session in the
extended-languages workflow.

## The six section ports

| Port | Theory | Basis |
|---|---|---|
| [Section 1](Section1_CorrectionB/README.md) | `Section1_CorrectionB/CorrectionB.thy` | `Complex_Main` |
| [Section 2](Section2_PreprintNSE/README.md) | `Section2_PreprintNSE/ProofChain.thy` | `Complex_Main` |
| [Section 3](Section3_ABCloud/README.md) | `Section3_ABCloud/Hofstadter.thy` | `Complex_Main` |
| [Section 4](Section4_KdV/README.md) | `Section4_KdV/KdV.thy` | `Complex_Main` |
| [Section 5](Section5_KleinAttractor/README.md) | `Section5_KleinAttractor/Klein.thy` | `Complex_Main` |
| [Section 6](Section6_RiemannZeros/README.md) | `Section6_RiemannZeros/RiemannZeros.thy` | `Complex_Main` |

## Contents

| File | Description |
|---|---|
| [`ROOT`](ROOT) | the Isabelle session ROOT — registers all theories for `isabelle build` |
| `Section1_CorrectionB/` … `Section6_RiemannZeros/` | the six theory folders, each with its `.thy` file and README |

## How to run

```bash
cd verification/isabelle
isabelle build -D .                 # the whole session — the integration check
isabelle jedit -l HOL Section1_CorrectionB/CorrectionB.thy   # interactive reading
```

Budget for a long first build (heap images); subsequent builds are
incremental and fast. Without installing Isabelle, use the pinned image
([`docker/isabelle/`](../docker/README.md)) or read the CI job — the
session build doubles as the integration check that all six theories load
together under `Complex_Main`, the formal analogue of the validator's
cross-language pass.

## 🔎 Why an independent restatement matters

The value of the Isabelle development is precisely that it is **not** a
translation of the Lean files — it is an independent restatement from the
papers' statements. Where Lean and Isabelle agree, the agreement is
evidence about the mathematics; where they would disagree, the
disagreement is a finding. The same logic applies to the Coq and Agda
mirrors, and it is why the repository keeps four formal developments of
the same six sections rather than formalising "once, properly".

The Isar style is deliberate: structured proof blocks with explicit
statement/proof separation, so a reviewer reads the mathematical content
rather than tactic traces. Automation (`simp`, `auto`, `linarith`) is used
where the step is genuinely routine — and marked as such. This makes the
Isabelle development the **best entry point for a reviewer who wants to
check statement fidelity against the papers**: the Isar blocks read like
the papers' own lemma structure.

## 🔗 See also

- [the framework hub](../README.md) — the two-tier picture and the
  contract;
- [`lean4/`](../lean4/README.md) — the statement-fidelity diffing partner;
- [`coq/`](../coq/README.md) · [`agda/`](../agda/README.md) — the other
  kernels;
- [`docker/isabelle/`](../docker/README.md) — the pinned toolchain image.


## Reading order for a statement-fidelity audit

1. open [`ROOT`](ROOT) — one session, six theories, `Complex_Main`
   throughout; the session file is the integration contract;
2. read `Section1_CorrectionB/CorrectionB.thy` top to bottom — the
   definition, the `value` call that prints the number, the positivity
   proof, the angle chain; this file calibrates how the other five read;
3. for the section you care about, diff the Isar statements against the
   corresponding section README's claim list — the Isabelle development is
   the one written to be *read*;
4. finish in [`lean4/TODO_sorry.md`](../lean4/TODO_sorry.md) to see which
   statements are admitted rather than closed.

## Session build economics

The first `isabelle build -D .` builds heap images and can take tens of
minutes; this is a one-time cost per environment. Subsequent builds are
incremental — touching one `.thy` rebuilds that theory and the session
link, in seconds-to-minutes. CI pays the cold cost on cached runners; the
[Docker image](../docker/README.md) bakes the heaps so container runs start
warm.

## What Isabelle adds beyond redundancy

Because Isar proofs read like structured mathematics, the Isabelle
development is the framework's **executable documentation of the
statements**: when the papers' wording and the Lean statement's syntax
disagree about emphasis, the Isar file is the tie-breaker a human can
read. It also catches a class of errors the tactic-heavy kernels absorb
silently — a statement that cannot be *structured* cleanly is usually a
statement that was modelled wrong.

---

Navigation: [verification](../README.md) · [repository root](../../README.md) · [IPL-RP-1.0](../../LICENSE.md)

*Part of [wild8highlander/navier-stokes-b](https://github.com/wild8highlander/navier-stokes-b) — © 2026 Isaev Iskhak Khamzatovich, all rights reserved.*
