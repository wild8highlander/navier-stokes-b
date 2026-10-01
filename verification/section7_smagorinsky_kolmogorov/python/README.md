# `section7_smagorinsky_kolmogorov/python/` — the reference port (Python)

> **Navigation:** [repository root](../../../README.md) › [verification](../../README.md) › [`section7_smagorinsky_kolmogorov`](../README.md) › **`python/`**

![Language](https://img.shields.io/badge/Python_3.11%2B-3776AB?style=flat-square) ![Deps](https://img.shields.io/badge/stdlib_·_mpmath_optional-2EA043?style=flat-square) ![Contract](https://img.shields.io/badge/PASS_%2B_JSON-FF8C00?style=flat-square) ![License](https://img.shields.io/badge/IPL--RP--1.0-red?style=flat-square)

---

This is the **reference implementation** of Section 7 — the executable
definition of the claims. It is deliberately boring: deterministic
(fixed-seed LCG where randomness is needed), self-contained (no imports
beyond the standard library; `mpmath` upgrades the 50-digit block when
present and is skipped cleanly when absent), and contract-exact (see
below). Every other port of Section 7 — C++, Rust, Haskell, Julia and
the four proof assistants — is required to agree with *this* file's
verdict, which is what makes it the reference.

## The assertions

| # | Assertion |
|---|---|
| C1 | parent constant `b` and `sin(θ_b) = b` (cross-link to Section 1) |
| C2 | `C_s(1.5) = 0.17326595582970580175685956672739039132…` (float64 + mpmath 50 digits) |
| C3 | `|C_s − Lilly 0.17326| < 1e-5` (measured 5.96×10⁻⁶) |
| C4 | exponent law `C_s(a·C_K)/C_s(C_K) = a^(−3/4)` to 2.2×10⁻¹⁶ |
| C5 | `C_s(1.8) < C_s(1.5) < C_s(1.2)` and `0 < C_s(C_K)` on (0, 10] |
| C6 | literature band `0.16 < C_s(1.5) < 0.20` |
| C7 | Cassini: `F(k+1)² − F(k)F(k+2) = (−1)ᵏ` for k = 0..40, exact |
| C8 | symmetric quad: `|N| ≤ 1e-14` — `C_s` identifiably zero (parity theorem) |
| C9 | (5′) coefficients: a·b·b·c sign-definite at 18/18 scans; a·a·b·b all-zero |
| C10 | model spectrum slope = −5/3 to 1e-12 |

Pinned values: `C_s` = 0.1732659558297058, `no_root_scans` = 18/18, `slope` = −1.6666666666666667

## Run

```bash
python3 verification/section7_smagorinsky_kolmogorov/python/verify.py
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
| `verify.py` | the verifier itself (10 assertions, one `main()`, ~120 lines) |
| `README.md` | this file |

## License

Part of **navier-stokes-b**, license IPL-RP-1.0 ([LICENSE.md](../../../LICENSE.md)).
