# `section4_kdv/` — KdV — soliton interactions under the b-correction

> **Navigation:** [repository root](../../README.md) › [verification](../README.md) › **`section4_kdv`**

![Section](https://img.shields.io/badge/Section_4-2B579A?style=flat-square) ![Reference](https://img.shields.io/badge/Python_stdlib-2EA043?style=flat-square) ![Contract](https://img.shields.io/badge/PASS_%2B_JSON-FF8C00?style=flat-square) ![License](https://img.shields.io/badge/IPL--RP--1.0-red?style=flat-square)

---

Section 4 pins the KdV facts used by chapter 16 and by §16.29: the soliton ODE residual is machine zero, the speed–amplitude law `u_max = c/2` holds, the profile width scales as `1/√c`, and the section constant is the framework constant. The heavier interaction benchmarks (Hirota collision, invariants, exact Lax combination) live in the kdv_improved protocol of `papers/kdv/kdv/` and lab L2 of the NSB-96 suite.

## The claims, verbatim

| # | Assertion | Recorded value / tolerance |
|---|---|---|
| C1 | soliton ODE `u''' − c u' + 6 u u' = 0` at machine zero (1.8×10⁻¹⁵) | |
| C2 | `u_max = c/2` (speed–amplitude law) | |
| C3 | profile width ∝ `1/√c` | |
| C4 | `b` and `θ_b` pinned | |

Pinned values of the reference run: `ode_max_residual` = 1.78×10⁻¹⁵

## Layout

| Path | Role |
|---|---|
| [`python/verify.py`](python/verify.py) | the **reference port** — the executable definition of the claims above |
| [`python/README.md`](python/README.md) | how to run it, the contract, the exact expected output |



## How to run

```bash
# direct (the reference port is stdlib-only; mpmath upgrades the precision block)
python3 verification/section4_kdv/python/verify.py
python3 verification/section4_kdv/python/verify.py --preset default   # contract-compatible

# through the aggregate runner (same verdict, uniform harness)
python3 verification/common/python/main.py --section 4 --preset default

# over HTTP, through the REST API
#   GET /api/verify/4  →  the parsed verdict + full output
```

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

## Where this section lives across the matrix

| Port | Location |
|---|---|
| Python reference | [`python/verify.py`](python/verify.py) (this directory) |
| Lean 4 (formal) | [`../lean4/ResearchPapersVerification/Section4_KdV/`](../lean4/ResearchPapersVerification/Section4_KdV/README.md) |
| Coq (formal) | [`../coq/`section4_kdv/README.md](../coq/section4_kdv/README.md) |
| Isabelle (formal) | [`../isabelle/Section4_KdV/README.md`](../isabelle/Section4_KdV/README.md) |
| Agda (formal) | [`../agda/Section4_KdV/README.md`](../agda/Section4_KdV/README.md) |
| C++17 | [`../cpp/section4_kdv/README.md`](../cpp/section4_kdv/README.md) |
| Rust | [`../rust/section4_kdv/README.md`](../rust/section4_kdv/README.md) |
| Haskell | [`../haskell/Section4_KdV/README.md`](../haskell/Section4_KdV/README.md) |
| Julia | `../julia_levels/` (`l4_…` for the chain sections) / the satellite `research_col_smar/code/julia` |

The same assertions are re-derived in every language of the matrix:
four proof assistants machine-check the structural statements, and five
computational toolchains recompute the numbers with five different
rounding regimes. A reviewer diffs *mathematical content* across systems,
not code style; any disagreement fails the cross-language validator in
[`verification/tests/`](../tests/README.md).

## License

Part of **navier-stokes-b**, license IPL-RP-1.0 ([LICENSE.md](../../LICENSE.md)).
