# `lean4/` — the Lean 4 formal tier

> **Navigation:** [repository root](../README.md) › [verification](../README.md) › **`lean4`**

![Language](https://img.shields.io/badge/Lean_4_·_Mathlib4-blue-informational?style=flat-square) ![Tier](https://img.shields.io/badge/1_·_Formal-blue?style=flat-square) ![Contract](https://img.shields.io/badge/lemmas_·_ledger-FF8C00?style=flat-square) ![License](https://img.shields.io/badge/IPL--RP--1.0-red?style=flat-square)

---

Lean 4 is the largest formal artifact of the framework. The package `ResearchPapersVerification` is defined in `lakefile.lean` with Mathlib4 pinned to v4.14.0; `lake build` type-checks every module of every section, and `lake exe check` / `lake exe test` print the runtime bridge. The trust base is honest and enumerable — the gap ledger [`TODO_sorry.md`](TODO_sorry.md) itemises every `sorry`, every mechanical `axiom : True` stub and every open-problem axiom with a difficulty estimate and a closing plan. Section 7 adds the master-relation positivity, the Fibonacci scaffolding and the (5′) coefficient algebra (fully proved) with three ledger entries: S7-CASSINI, S7-EXPLAW, S7-ANTI.

## Toolchain

Lean 4 (v4.14.0-rc1) + Mathlib4 (v4.14.0)

## Build

```bash
cd verification/lean4
lake build        # type-check every module
lake exe check    # the numerical bridge banner
```

## Module map

| Directory | Section | Content |
|---|---|---|
| [`Section1_CorrectionB/`](Section1_CorrectionB/README.md) | S1 — Correction b | machine-checked: the closed form, the range 0 < b < 1, sin θ_b = b, the Rodrigues algebra, energy neutrality |
| [`Section2_PreprintNSE/`](Section2_PreprintNSE/README.md) | S2 — Preprint NSE | machine-checked: twist unitarity, the Leray premise (zero energy injection), the BKM bridge |
| [`Section3_ABCloud/`](Section3_ABCloud/README.md) | S3 — AB-Cloud | machine-checked: flux quantisation, Hermiticity and trace zero, butterfly slice identities |
| [`Section4_KdV/`](Section4_KdV/README.md) | S4 — KdV | machine-checked: the soliton ODE at machine zero, u_max = c/2, width ∝ 1/√c |
| [`Section5_KleinAttractor/`](Section5_KleinAttractor/README.md) | S5 — Klein attractor | machine-checked: orbit density, isometry at every iterate, the Niven-set irrationality |
| [`Section6_RiemannZeros/`](Section6_RiemannZeros/README.md) | S6 — Riemann zeros | machine-checked: ζ special values, ξ(s) = ξ(1−s), annihilation at the first zero |
| [`Section7_SmagorinskyKolmogorov/`](Section7_SmagorinskyKolmogorov/README.md) | S7 — Smagorinsky–Kolmogorov | machine-checked: C_s = 1/(π(3C_K/2)^{3/4}) at 50 digits, the −3/4 exponent law, Cassini, the (5′) coefficient algebra |
| [`Common/`](ResearchPapersVerification/Common/README.md) | shared foundation | the constant, its exact digits, the shared lemmas |


## The verification contract (formal mirror)

The formal tier mirrors the computational output contract with *lemma
names* instead of `[PASS]` lines: every claim of a section appears as a
named lemma, the numeric constants appear as `def`s or `Compute`d values,
and the admitted statements are public in the gap ledger. Nothing is
hidden behind unconditional assumptions — the trust base is enumerable.

## Cross-language matrix

![Lean_4](https://img.shields.io/badge/S1%E2%80%93S7-2B579A?style=flat-square) ![Coq](https://img.shields.io/badge/S1%E2%80%93S7-2B579A?style=flat-square) ![Isabelle](https://img.shields.io/badge/S1%E2%80%93S7-2B579A?style=flat-square) ![Agda](https://img.shields.io/badge/S1%E2%80%93S7-2B579A?style=flat-square)
The same assertions are proved in all four kernels; any structural
disagreement is a CI failure by construction.

## License

Part of **navier-stokes-b**, license IPL-RP-1.0. ([LICENSE.md](../LICENSE.md)).
