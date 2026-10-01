# `section2_preprint/python/` — the reference port (Python)

> **Navigation:** [repository root](../../../README.md) › [verification](../../README.md) › [`section2_preprint`](../README.md) › **`python/`**

![Language](https://img.shields.io/badge/Python_3.11%2B-3776AB?style=flat-square) ![Deps](https://img.shields.io/badge/stdlib_·_mpmath_optional-2EA043?style=flat-square) ![Contract](https://img.shields.io/badge/PASS_%2B_JSON-FF8C00?style=flat-square) ![License](https://img.shields.io/badge/IPL--RP--1.0-red?style=flat-square)

---

This is the **reference implementation** of Section 2 — the executable
definition of the claims. It is deliberately boring: deterministic
(fixed-seed LCG where randomness is needed), self-contained (no imports
beyond the standard library; `mpmath` upgrades the 50-digit block when
present and is skipped cleanly when absent), and contract-exact (see
below). Every other port of Section 2 — C++, Rust, Haskell, Julia and
the four proof assistants — is required to agree with *this* file's
verdict, which is what makes it the reference.

## The assertions

| # | Assertion |
|---|---|
| C1 | `b ∈ (0,1)` and `sin(θ_b) = b` |
| C2 | `det R = 1` — the twist is volume-preserving |
| C3 | `max |ΔE|` per rotation ≤ 1e-12 (measured 6.7×10⁻¹⁶) — the Leray premise |
| C4 | signed energy injection zero to FP accumulation (`|ΣΔE|` ≤ 1e-12) |
| C5 | BKM enstrophy finite and positive on the reference TG field (`Ω` = 1.0) |

Pinned values: `max|ΔE|` = 6.66×10⁻¹⁶, `ΣΔE` = −2.53×10⁻¹³ (bound 2.2×10⁻¹²), `Ω` = 1.000000000000

## Run

```bash
python3 verification/section2_preprint/python/verify.py
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
