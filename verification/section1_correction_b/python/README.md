# `section1_correction_b/python/` — the reference port (Python)

> **Navigation:** [repository root](../../../README.md) › [verification](../../README.md) › [`section1_correction_b`](../README.md) › **`python/`**

![Language](https://img.shields.io/badge/Python_3.11%2B-3776AB?style=flat-square) ![Deps](https://img.shields.io/badge/stdlib_·_mpmath_optional-2EA043?style=flat-square) ![Contract](https://img.shields.io/badge/PASS_%2B_JSON-FF8C00?style=flat-square) ![License](https://img.shields.io/badge/IPL--RP--1.0-red?style=flat-square)

---

This is the **reference implementation** of Section 1 — the executable
definition of the claims. It is deliberately boring: deterministic
(fixed-seed LCG where randomness is needed), self-contained (no imports
beyond the standard library; `mpmath` upgrades the 50-digit block when
present and is skipped cleanly when absent), and contract-exact (see
below). Every other port of Section 1 — C++, Rust, Haskell, Julia and
the four proof assistants — is required to agree with *this* file's
verdict, which is what makes it the reference.

## The assertions

| # | Assertion |
|---|---|
| C1 | `b` matches the pinned value `0.06238119412102822…` to 15+ digits |
| C2 | `0 < b < 1` |
| C3 | `sin(θ_b) = b` to machine precision (θ_b = arcsin b by construction) |
| C4 | `cos²θ_b + b² = 1` |
| C5 | `det R = 1` and `trace R = 1 + 2 cos θ_b` for the θ_b-rotation |
| C6 | `RᵀR = I` (orthogonality, max residual < 1e-12) |
| C7 | energy neutrality: `max |ΔE|` over 10⁴ vectors ≤ 1e-12 |

Pinned values: `b` = 0.06238119412102824, `θ_b` = 0.06242172363615545 rad = 3.5765013142837°

## Run

```bash
python3 verification/section1_correction_b/python/verify.py
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
| `verify.py` | the verifier itself (7 assertions, one `main()`, ~120 lines) |
| `README.md` | this file |

## License

Part of **navier-stokes-b**, license IPL-RP-1.0 ([LICENSE.md](../../../LICENSE.md)).
