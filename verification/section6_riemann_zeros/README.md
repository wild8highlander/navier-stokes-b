# `section6_riemann_zeros/` — Riemann zeros — the Hilbert–Pólya programme

> **Navigation:** [repository root](../../README.md) › [verification](../README.md) › **`section6_riemann_zeros`**

![Section](https://img.shields.io/badge/Section_6-2B579A?style=flat-square) ![Reference](https://img.shields.io/badge/Python_stdlib-2EA043?style=flat-square) ![Contract](https://img.shields.io/badge/PASS_%2B_JSON-FF8C00?style=flat-square) ![License](https://img.shields.io/badge/IPL--RP--1.0-red?style=flat-square)

---

Section 6 verifies the frozen-data embedding facts of the AB-Cloud/Riemann correspondence: the zeta special values (`ζ(2) = π²/6`, `ζ(4) = π⁴/90`), the functional equation `ξ(s) = ξ(1−s)` off the critical line to 1e-10, the annihilation of ξ at the first non-trivial zero versus the contrast at a non-zero ordinate, and the framework constant cross-link.

## The claims, verbatim

| # | Assertion | Recorded value / tolerance |
|---|---|---|
| C1 | `ζ(2) = π²/6` and `ζ(4) = π⁴/90` (tolerance 1e-12) | |
| C2 | functional equation `ξ(s) = ξ(1−s)` off the line (measured 7.3×10⁻¹⁶) | |
| C3 | `|ξ|` at the first zero < 1e-12 (measured 8.5×10⁻¹⁸) | |
| C4 | `|ξ|` at a non-zero ordinate > 1e-2 (contrast) | |
| C5 | `b` matches the framework value | |

Pinned values of the reference run: `xi_zero_residual` = 8.477×10⁻¹⁸

## Layout

| Path | Role |
|---|---|
| [`python/verify.py`](python/verify.py) | the **reference port** — the executable definition of the claims above |
| [`python/README.md`](python/README.md) | how to run it, the contract, the exact expected output |



## How to run

```bash
# direct (the reference port is stdlib-only; mpmath upgrades the precision block)
python3 verification/section6_riemann_zeros/python/verify.py
python3 verification/section6_riemann_zeros/python/verify.py --preset default   # contract-compatible

# through the aggregate runner (same verdict, uniform harness)
python3 verification/common/python/main.py --section 6 --preset default

# over HTTP, through the REST API
#   GET /api/verify/6  →  the parsed verdict + full output
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
| Lean 4 (formal) | [`../lean4/ResearchPapersVerification/Section6_RiemannZeros/`](../lean4/ResearchPapersVerification/Section6_RiemannZeros/README.md) |
| Coq (formal) | [`../coq/`section6_riemann_zeros/README.md](../coq/section6_riemann_zeros/README.md) |
| Isabelle (formal) | [`../isabelle/Section6_RiemannZeros/README.md`](../isabelle/Section6_RiemannZeros/README.md) |
| Agda (formal) | [`../agda/Section6_RiemannZeros/README.md`](../agda/Section6_RiemannZeros/README.md) |
| C++17 | [`../cpp/section6_riemann_zeros/README.md`](../cpp/section6_riemann_zeros/README.md) |
| Rust | [`../rust/section6_riemann_zeros/README.md`](../rust/section6_riemann_zeros/README.md) |
| Haskell | [`../haskell/Section6_RiemannZeros/README.md`](../haskell/Section6_RiemannZeros/README.md) |
| Julia | `../julia_levels/` (`l6_…` for the chain sections) / the satellite `research_col_smar/code/julia` |

The same assertions are re-derived in every language of the matrix:
four proof assistants machine-check the structural statements, and five
computational toolchains recompute the numbers with five different
rounding regimes. A reviewer diffs *mathematical content* across systems,
not code style; any disagreement fails the cross-language validator in
[`verification/tests/`](../tests/README.md).

## License

Part of **navier-stokes-b**, license IPL-RP-1.0 ([LICENSE.md](../../LICENSE.md)).
