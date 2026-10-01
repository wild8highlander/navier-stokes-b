# `Section6_RiemannZeros` — Riemann zeros — the Hilbert–Pólya programme (Isabelle/HOL)

> **Navigation:** [repository root](../../README.md) › [verification](../../verification/README.md) › [isabelle](../README.md) › **section 6**

![Section](https://img.shields.io/badge/S6-2B579A?style=flat-square) ![Kernel](https://img.shields.io/badge/Isabelle_2024-blueviolet-informational?style=flat-square) ![Status](https://img.shields.io/badge/machine--checked-2EA043?style=flat-square) ![License](https://img.shields.io/badge/IPL--RP--1.0-red?style=flat-square)

---

**What this module machine-checks:** ζ special values, ξ(s) = ξ(1−s), annihilation at the first zero.

The section belongs to the seven-section research map of the repository
(see the [verification hub](../../verification/README.md)); the Python
reference port that defines the claims is
[`verification/section6_riemann_zeros/python/verify.py`](../../verification/section6_riemann_zeros/python/README.md),
and this module is the Isabelle/HOL mirror of the same assertions.

## Assertion → lemma map

| Claim (reference port) | Formal counterpart |
|---|---|
| C1 | the constant block (`b_pos`, `b_lt_one`, the pinned digits) |
| C2 | the identity block (arcsine / parity / spectrum) |
| C3 | the structural block (algebra / Hermiticity / isometry) |
| C4 | the analytic block (bounds / monotonicity / density) |
| C5 | the bridge block (NSE / BKM / cross-links) |

The exact lemma names are in the source file; the admitted statements
(such as the rotation orthogonality in Section 1, or the Cassini
induction in Section 7 where a kernel defers it) are itemised in the
relevant ledger — for Lean 4, [`TODO_sorry.md`](../../lean4/TODO_sorry.md).

## Build

```bash
cd verification/isabelle
isabelle build -D .
```

## Files

| File | Role |
|---|---|
| `RiemannZeros.thy` | the Isabelle/HOL module of section 6 |

## License

Part of **navier-stokes-b**, license IPL-RP-1.0. ([LICENSE.md](../../LICENSE.md)).
