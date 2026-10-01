# `section6_riemann_zeros/python/` — the reference port (Python)

> **Navigation:** [repository root](../../../README.md) › [verification](../../README.md) › [`section6_riemann_zeros`](../README.md) › **`python/`**

![Language](https://img.shields.io/badge/Python_3.11%2B-3776AB?style=flat-square) ![Deps](https://img.shields.io/badge/stdlib_·_mpmath_optional-2EA043?style=flat-square) ![Contract](https://img.shields.io/badge/PASS_%2B_JSON-FF8C00?style=flat-square) ![License](https://img.shields.io/badge/IPL--RP--1.0-red?style=flat-square)

---

This is the **reference implementation** of Section 6 — the executable
definition of the claims. It is deliberately boring: deterministic
(fixed-seed LCG where randomness is needed), self-contained (no imports
beyond the standard library; `mpmath` upgrades the 50-digit block when
present and is skipped cleanly when absent), and contract-exact (see
below). Every other port of Section 6 — C++, Rust, Haskell, Julia and
the four proof assistants — is required to agree with *this* file's
verdict, which is what makes it the reference.

## The assertions

| # | Assertion |
|---|---|
| C1 | `ζ(2) = π²/6` and `ζ(4) = π⁴/90` (tolerance 1e-12) |
| C2 | functional equation `ξ(s) = ξ(1−s)` off the line (measured 7.3×10⁻¹⁶) |
| C3 | `|ξ|` at the first zero < 1e-12 (measured 8.5×10⁻¹⁸) |
| C4 | `|ξ|` at a non-zero ordinate > 1e-2 (contrast) |
| C5 | `b` matches the framework value |

Pinned values: `xi_zero_residual` = 8.477×10⁻¹⁸

## Run

```bash
python3 verification/section6_riemann_zeros/python/verify.py
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
| `verify.py` | the verifier itself (5 assertions, one `main()`, ~120 lines) |
| `README.md` | this file |

## License

Part of **navier-stokes-b**, license IPL-RP-1.0 ([LICENSE.md](../../../LICENSE.md)).
