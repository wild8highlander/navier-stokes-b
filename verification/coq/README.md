# `coq/` — the Coq/Rocq formal tier

> **Navigation:** [repository root](../README.md) › [verification](../README.md) › **`coq`**

![Language](https://img.shields.io/badge/Coq_8.18_·_Reals-orange-informational?style=flat-square) ![Tier](https://img.shields.io/badge/1_·_Formal-blue?style=flat-square) ![Contract](https://img.shields.io/badge/lemmas_·_ledger-FF8C00?style=flat-square) ![License](https://img.shields.io/badge/IPL--RP--1.0-red?style=flat-square)

---

The Coq tree restates every section over classical `Reals`. Files deliberately `Compute` the constants during compilation so the reviewer sees the numbers in the build log. Each directory carries one self-contained `.v` file, listed in `_CoqProject` for `coq_makefile`. Section 7 (`section7_smagorinsky/MasterRelation.v`) fully proves the Fibonacci scaffolding, Cassini's identity (induction closed by `nia`) and the (5′) coefficient algebra; two rpow-technical analytic lemmas are admitted with a ledger note, consistent with the framework's honesty rule.

## Toolchain

Coq/Rocq 8.18, standard `Reals`, `lra`/`nia` automation

## Build

```bash
cd verification/coq
coq_makefile -f _CoqProject -o Makefile
make
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
