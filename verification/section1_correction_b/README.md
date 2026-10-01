# `section1_correction_b/` — Correction b — the universal polarization constant

> **Navigation:** [repository root](../../README.md) › [verification](../README.md) › **`section1_correction_b`**

![Section](https://img.shields.io/badge/Section_1-2B579A?style=flat-square) ![Reference](https://img.shields.io/badge/Python_stdlib-2EA043?style=flat-square) ![Contract](https://img.shields.io/badge/PASS_%2B_JSON-FF8C00?style=flat-square) ![License](https://img.shields.io/badge/IPL--RP--1.0-red?style=flat-square)

---

Section 1 is the executable definition of the constant itself: the closed form `b = 1/(4π + 2√3)`, the range `0 < b < 1`, the arcsine identity `sin θ_b = b` at machine precision, and the sanity algebra of the Rodrigues rotation about a non-trivial axis (orthogonality, `det R = 1`, `trace R = 1 + 2 cos θ_b`, and energy neutrality of the rotation over 10⁴ deterministic pseudo-random vectors). Every other section re-anchors to this one: `b matches framework value` is a standing assertion of sections 3, 6 and 7.

## The claims, verbatim

| # | Assertion | Recorded value / tolerance |
|---|---|---|
| C1 | `b` matches the pinned value `0.06238119412102822…` to 15+ digits | |
| C2 | `0 < b < 1` | |
| C3 | `sin(θ_b) = b` to machine precision (θ_b = arcsin b by construction) | |
| C4 | `cos²θ_b + b² = 1` | |
| C5 | `det R = 1` and `trace R = 1 + 2 cos θ_b` for the θ_b-rotation | |
| C6 | `RᵀR = I` (orthogonality, max residual < 1e-12) | |
| C7 | energy neutrality: `max |ΔE|` over 10⁴ vectors ≤ 1e-12 | |

Pinned values of the reference run: `b` = 0.06238119412102824, `θ_b` = 0.06242172363615545 rad = 3.5765013142837°

## Layout

| Path | Role |
|---|---|
| [`python/verify.py`](python/verify.py) | the **reference port** — the executable definition of the claims above |
| [`python/README.md`](python/README.md) | how to run it, the contract, the exact expected output |



## How to run

```bash
# direct (the reference port is stdlib-only; mpmath upgrades the precision block)
python3 verification/section1_correction_b/python/verify.py
python3 verification/section1_correction_b/python/verify.py --preset default   # contract-compatible

# through the aggregate runner (same verdict, uniform harness)
python3 verification/common/python/main.py --section 1 --preset default

# over HTTP, through the REST API
#   GET /api/verify/1  →  the parsed verdict + full output
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
| Lean 4 (formal) | [`../lean4/ResearchPapersVerification/Section1_CorrectionB/`](../lean4/ResearchPapersVerification/Section1_CorrectionB/README.md) |
| Coq (formal) | [`../coq/`section1_correction_b/README.md](../coq/section1_correction_b/README.md) |
| Isabelle (formal) | [`../isabelle/Section1_CorrectionB/README.md`](../isabelle/Section1_CorrectionB/README.md) |
| Agda (formal) | [`../agda/Section1_CorrectionB/README.md`](../agda/Section1_CorrectionB/README.md) |
| C++17 | [`../cpp/section1_correction_b/README.md`](../cpp/section1_correction_b/README.md) |
| Rust | [`../rust/section1_correction_b/README.md`](../rust/section1_correction_b/README.md) |
| Haskell | [`../haskell/Section1_CorrectionB/README.md`](../haskell/Section1_CorrectionB/README.md) |
| Julia | `../julia_levels/` (`l1_…` for the chain sections) / the satellite `research_col_smar/code/julia` |

The same assertions are re-derived in every language of the matrix:
four proof assistants machine-check the structural statements, and five
computational toolchains recompute the numbers with five different
rounding regimes. A reviewer diffs *mathematical content* across systems,
not code style; any disagreement fails the cross-language validator in
[`verification/tests/`](../tests/README.md).

## License

Part of **navier-stokes-b**, license IPL-RP-1.0 ([LICENSE.md](../../LICENSE.md)).
