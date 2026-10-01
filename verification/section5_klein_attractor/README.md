# `section5_klein_attractor/` — Klein attractor — ergodic dynamics and the NSE bridge

> **Navigation:** [repository root](../../README.md) › [verification](../README.md) › **`section5_klein_attractor`**

![Section](https://img.shields.io/badge/Section_5-2B579A?style=flat-square) ![Reference](https://img.shields.io/badge/Python_stdlib-2EA043?style=flat-square) ![Contract](https://img.shields.io/badge/PASS_%2B_JSON-FF8C00?style=flat-square) ![License](https://img.shields.io/badge/IPL--RP--1.0-red?style=flat-square)

---

Section 5 verifies the Klein-attractor facts: the rotation by `θ_b` is an isometry at every iterate, the orbit is dense (max angular gap < 10⁻³ rad after 10⁵ iterates), and the angle is irrational in π-turns because `sin θ_b = b` is not in the Niven set of rational values admitting rational arcsines. The NSE bridge statements (dissipation contraction) are mirrored by the formal ports.

## The claims, verbatim

| # | Assertion | Recorded value / tolerance |
|---|---|---|
| C1 | `b` and `θ_b` pinned; `θ_b/π = 0.019869451746021…` | |
| C2 | `sin(θ_b) = b ∉ Niven set` ⇒ `θ_b/π` irrational | |
| C3 | orbit dense: max angular gap < 1e-3 rad after 1e5 iterates (measured 9.0×10⁻⁵) | |
| C4 | rotation is an isometry at every iterate (`max |r² drift|` = 1.6×10⁻¹²) | |

Pinned values of the reference run: `max_gap` = 9.005×10⁻⁵ rad (uniform bound 6.28×10⁻⁵ × spacing)

## Layout

| Path | Role |
|---|---|
| [`python/verify.py`](python/verify.py) | the **reference port** — the executable definition of the claims above |
| [`python/README.md`](python/README.md) | how to run it, the contract, the exact expected output |



## How to run

```bash
# direct (the reference port is stdlib-only; mpmath upgrades the precision block)
python3 verification/section5_klein_attractor/python/verify.py
python3 verification/section5_klein_attractor/python/verify.py --preset default   # contract-compatible

# through the aggregate runner (same verdict, uniform harness)
python3 verification/common/python/main.py --section 5 --preset default

# over HTTP, through the REST API
#   GET /api/verify/5  →  the parsed verdict + full output
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
| Lean 4 (formal) | [`../lean4/ResearchPapersVerification/Section5_KleinAttractor/`](../lean4/ResearchPapersVerification/Section5_KleinAttractor/README.md) |
| Coq (formal) | [`../coq/`section5_klein_attractor/README.md](../coq/section5_klein_attractor/README.md) |
| Isabelle (formal) | [`../isabelle/Section5_KleinAttractor/README.md`](../isabelle/Section5_KleinAttractor/README.md) |
| Agda (formal) | [`../agda/Section5_KleinAttractor/README.md`](../agda/Section5_KleinAttractor/README.md) |
| C++17 | [`../cpp/section5_klein_attractor/README.md`](../cpp/section5_klein_attractor/README.md) |
| Rust | [`../rust/section5_klein_attractor/README.md`](../rust/section5_klein_attractor/README.md) |
| Haskell | [`../haskell/Section5_KleinAttractor/README.md`](../haskell/Section5_KleinAttractor/README.md) |
| Julia | `../julia_levels/` (`l5_…` for the chain sections) / the satellite `research_col_smar/code/julia` |

The same assertions are re-derived in every language of the matrix:
four proof assistants machine-check the structural statements, and five
computational toolchains recompute the numbers with five different
rounding regimes. A reviewer diffs *mathematical content* across systems,
not code style; any disagreement fails the cross-language validator in
[`verification/tests/`](../tests/README.md).

## License

Part of **navier-stokes-b**, license IPL-RP-1.0 ([LICENSE.md](../../LICENSE.md)).
