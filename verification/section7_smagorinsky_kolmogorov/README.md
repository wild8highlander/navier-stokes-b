# `section7_smagorinsky_kolmogorov/` — Smagorinsky–Kolmogorov — the master relation (new)

> **Navigation:** [repository root](../../README.md) › [verification](../README.md) › **`section7_smagorinsky_kolmogorov`**

![Section](https://img.shields.io/badge/Section_7-2B579A?style=flat-square) ![Reference](https://img.shields.io/badge/Python_stdlib-2EA043?style=flat-square) ![Contract](https://img.shields.io/badge/PASS_%2B_JSON-FF8C00?style=flat-square) ![License](https://img.shields.io/badge/IPL--RP--1.0-red?style=flat-square)

---

Section 7 is the verification bridge of the `research_col_smar` satellite. It verifies the master relation `C_s = 1/(π(3C_K/2)^{3/4})` at 50 digits, the agreement with Lilly's classical value (Δ = 6×10⁻⁶), the exact −3/4 exponent law, monotonicity, the literature band, the Cassini identity (exact integers, k = 0..40), the symmetry theorem of the φ-audit (the scale-similarity numerator is identically zero on x-mirror-symmetric circulations), and the reduced zero-drift condition (5′) coefficient algebra: a·b·b·c sign-definite (18/18 scans — no root at any scale), a·a·b·b degenerate (one-parameter family). This is the port-level confirmation of fixes I1–I2 of `PHI_FORMULA_FIXES.md`.

## The claims, verbatim

| # | Assertion | Recorded value / tolerance |
|---|---|---|
| C1 | parent constant `b` and `sin(θ_b) = b` (cross-link to Section 1) | |
| C2 | `C_s(1.5) = 0.17326595582970580175685956672739039132…` (float64 + mpmath 50 digits) | |
| C3 | `|C_s − Lilly 0.17326| < 1e-5` (measured 5.96×10⁻⁶) | |
| C4 | exponent law `C_s(a·C_K)/C_s(C_K) = a^(−3/4)` to 2.2×10⁻¹⁶ | |
| C5 | `C_s(1.8) < C_s(1.5) < C_s(1.2)` and `0 < C_s(C_K)` on (0, 10] | |
| C6 | literature band `0.16 < C_s(1.5) < 0.20` | |
| C7 | Cassini: `F(k+1)² − F(k)F(k+2) = (−1)ᵏ` for k = 0..40, exact | |
| C8 | symmetric quad: `|N| ≤ 1e-14` — `C_s` identifiably zero (parity theorem) | |
| C9 | (5′) coefficients: a·b·b·c sign-definite at 18/18 scans; a·a·b·b all-zero | |
| C10 | model spectrum slope = −5/3 to 1e-12 | |

Pinned values of the reference run: `C_s` = 0.1732659558297058, `no_root_scans` = 18/18, `slope` = −1.6666666666666667

## Layout

| Path | Role |
|---|---|
| [`python/verify.py`](python/verify.py) | the **reference port** — the executable definition of the claims above |
| [`python/README.md`](python/README.md) | how to run it, the contract, the exact expected output |



## How to run

```bash
# direct (the reference port is stdlib-only; mpmath upgrades the precision block)
python3 verification/section7_smagorinsky_kolmogorov/python/verify.py
python3 verification/section7_smagorinsky_kolmogorov/python/verify.py --preset default   # contract-compatible

# through the aggregate runner (same verdict, uniform harness)
python3 verification/common/python/main.py --section 7 --preset default

# over HTTP, through the REST API
#   GET /api/verify/7  →  the parsed verdict + full output
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
| Lean 4 (formal) | [`../lean4/ResearchPapersVerification/Section7_SmagorinskyKolmogorov/`](../lean4/ResearchPapersVerification/Section7_SmagorinskyKolmogorov/README.md) |
| Coq (formal) | [`../coq/`section7_smagorinsky/README.md](../coq/section7_smagorinsky/README.md) |
| Isabelle (formal) | [`../isabelle/Section7_SmagorinskyKolmogorov/README.md`](../isabelle/Section7_SmagorinskyKolmogorov/README.md) |
| Agda (formal) | [`../agda/Section7_SmagorinskyKolmogorov/README.md`](../agda/Section7_SmagorinskyKolmogorov/README.md) |
| C++17 | [`../cpp/section7_smagorinsky_kolmogorov/README.md`](../cpp/section7_smagorinsky_kolmogorov/README.md) |
| Rust | [`../rust/section7_smagorinsky_kolmogorov/README.md`](../rust/section7_smagorinsky_kolmogorov/README.md) |
| Haskell | [`../haskell/Section7_SmagorinskyKolmogorov/README.md`](../haskell/Section7_SmagorinskyKolmogorov/README.md) |
| Julia | `../julia_levels/` (`l7_…` for the chain sections) / the satellite `research_col_smar/code/julia` |

The same assertions are re-derived in every language of the matrix:
four proof assistants machine-check the structural statements, and five
computational toolchains recompute the numbers with five different
rounding regimes. A reviewer diffs *mathematical content* across systems,
not code style; any disagreement fails the cross-language validator in
[`verification/tests/`](../tests/README.md).

## License

Part of **navier-stokes-b**, license IPL-RP-1.0 ([LICENSE.md](../../LICENSE.md)).
