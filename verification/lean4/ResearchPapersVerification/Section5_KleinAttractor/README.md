# `Section5_KleinAttractor` — Klein attractor — ergodic dynamics and the NSE bridge (Lean 4)

> **Navigation:** [repository root](../../README.md) › [verification](../../verification/README.md) › [lean4](../README.md) › **section 5**

![Section](https://img.shields.io/badge/S5-2B579A?style=flat-square) ![Kernel](https://img.shields.io/badge/Lean_4_·_Mathlib4-blue-informational?style=flat-square) ![Status](https://img.shields.io/badge/machine--checked-2EA043?style=flat-square) ![License](https://img.shields.io/badge/IPL--RP--1.0-red?style=flat-square)

---

**What this module machine-checks:** orbit density, isometry at every iterate, the Niven-set irrationality.

The section belongs to the seven-section research map of the repository
(see the [verification hub](../../verification/README.md)); the Python
reference port that defines the claims is
[`verification/section5_klein_attractor/python/verify.py`](../../verification/section5_klein_attractor/python/README.md),
and this module is the Lean 4 mirror of the same assertions.

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
cd verification/lean4
lake build        # type-check every module
lake exe check    # the numerical bridge banner
```

## Files

| File | Role |
|---|---|
| `KleinQuartic.lean` | the Lean 4 module of section 5 |

## License

Part of **navier-stokes-b**, license IPL-RP-1.0. ([LICENSE.md](../../LICENSE.md)).
