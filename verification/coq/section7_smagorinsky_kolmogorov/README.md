# `Section7_SmagorinskyKolmogorov` — Smagorinsky–Kolmogorov — the master relation (Coq/Rocq)

> **Navigation:** [repository root](../../README.md) › [verification](../../verification/README.md) › [coq](../README.md) › **section 7**

![Section](https://img.shields.io/badge/S7-2B579A?style=flat-square) ![Kernel](https://img.shields.io/badge/Coq_8.18_·_Reals-orange-informational?style=flat-square) ![Status](https://img.shields.io/badge/machine--checked-2EA043?style=flat-square) ![License](https://img.shields.io/badge/IPL--RP--1.0-red?style=flat-square)

---

**What this module machine-checks:** C_s = 1/(π(3C_K/2)^{3/4}) at 50 digits, the −3/4 exponent law, Cassini, the (5′) coefficient algebra.

The section belongs to the seven-section research map of the repository
(see the [verification hub](../../verification/README.md)); the Python
reference port that defines the claims is
[`verification/section7_smagorinsky_kolmogorov/python/verify.py`](../../verification/section7_smagorinsky_kolmogorov/python/README.md),
and this module is the Coq/Rocq mirror of the same assertions.

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
cd verification/coq
coq_makefile -f _CoqProject -o Makefile
make
```

## Files

| File | Role |
|---|---|
| `Section7.v` | the Coq/Rocq module of section 7 |

## License

Part of **navier-stokes-b**, license IPL-RP-1.0. ([LICENSE.md](../../LICENSE.md)).
