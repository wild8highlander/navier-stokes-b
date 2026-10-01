# `section4_kdv/python/` — the reference port (Python)

> **Navigation:** [repository root](../../../README.md) › [verification](../../README.md) › [`section4_kdv`](../README.md) › **`python/`**

![Language](https://img.shields.io/badge/Python_3.11%2B-3776AB?style=flat-square) ![Deps](https://img.shields.io/badge/stdlib_·_mpmath_optional-2EA043?style=flat-square) ![Contract](https://img.shields.io/badge/PASS_%2B_JSON-FF8C00?style=flat-square) ![License](https://img.shields.io/badge/IPL--RP--1.0-red?style=flat-square)

---

This is the **reference implementation** of Section 4 — the executable
definition of the claims. It is deliberately boring: deterministic
(fixed-seed LCG where randomness is needed), self-contained (no imports
beyond the standard library; `mpmath` upgrades the 50-digit block when
present and is skipped cleanly when absent), and contract-exact (see
below). Every other port of Section 4 — C++, Rust, Haskell, Julia and
the four proof assistants — is required to agree with *this* file's
verdict, which is what makes it the reference.

## The assertions

| # | Assertion |
|---|---|
| C1 | soliton ODE `u''' − c u' + 6 u u' = 0` at machine zero (1.8×10⁻¹⁵) |
| C2 | `u_max = c/2` (speed–amplitude law) |
| C3 | profile width ∝ `1/√c` |
| C4 | `b` and `θ_b` pinned |

Pinned values: `ode_max_residual` = 1.78×10⁻¹⁵

## Run

```bash
python3 verification/section4_kdv/python/verify.py
```

Wall-clock: well under one second on any modern machine.

## Output contract

Every port follows the repository-wide output contract, which is what
makes cross-language comparison mechanical:

1. print a banner line identifying section and language;
2. compute the section's quantities **from the closed forms** (no data
   files are read at this tier);
3. print one `[PASS]`/`[FAIL]` line per assertion with the measured
   residual;
4. print exactly one machine-readable verdict line `JSON: {"section": N,
   "language": "...", "values": {...}, "all_passed": true|false}`;
5. exit `0` only if every assertion passed — CI fails otherwise.

## Files

| File | Purpose |
|---|---|
| `verify.py` | the verifier itself (4 assertions, one `main()`, ~120 lines) |
| `README.md` | this file |

## License

Part of **navier-stokes-b**, license IPL-RP-1.0 ([LICENSE.md](../../../LICENSE.md)).
