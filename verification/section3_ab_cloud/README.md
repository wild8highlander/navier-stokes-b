# `section3_ab_cloud/` — AB-Cloud — the Hofstadter Hamiltonian

> **Navigation:** [repository root](../../README.md) › [verification](../README.md) › **`section3_ab_cloud`**

![Section](https://img.shields.io/badge/Section_3-2B579A?style=flat-square) ![Reference](https://img.shields.io/badge/Python_stdlib-2EA043?style=flat-square) ![Contract](https://img.shields.io/badge/PASS_%2B_JSON-FF8C00?style=flat-square) ![License](https://img.shields.io/badge/IPL--RP--1.0-red?style=flat-square)

---

Section 3 verifies the AB-Cloud monograph's structural core: the Hofstadter Hamiltonian on the flux lattice is Hermitian with trace zero for every flux rational p/q, and the butterfly spectrum obeys the exact slice identities (`Σ E_j = −2`, `Σ E_j² = 2q − 4` for all p/q pairs) that the monograph's figure 4 depends on. The section also re-anchors the shared constant: `b matches framework value`.

## The claims, verbatim

| # | Assertion | Recorded value / tolerance |
|---|---|---|
| C1 | Hofstadter matrix Hermitian, trace 0 (checked for several p/q) | |
| C2 | butterfly slice identities: `Σ E_j = −2`, `Σ E_j² = 2q − 4` (all pairs) | |
| C3 | `b` matches the framework value | |

Pinned values of the reference run: hermiticity error 0.0, `|trace|` ≤ 6.7×10⁻¹⁶, slice identities to 5×10⁻¹⁵

## Layout

| Path | Role |
|---|---|
| [`python/verify.py`](python/verify.py) | the **reference port** — the executable definition of the claims above |
| [`python/README.md`](python/README.md) | how to run it, the contract, the exact expected output |



## How to run

```bash
# direct (the reference port is stdlib-only; mpmath upgrades the precision block)
python3 verification/section3_ab_cloud/python/verify.py
python3 verification/section3_ab_cloud/python/verify.py --preset default   # contract-compatible

# through the aggregate runner (same verdict, uniform harness)
python3 verification/common/python/main.py --section 3 --preset default

# over HTTP, through the REST API
#   GET /api/verify/3  →  the parsed verdict + full output
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
| Lean 4 (formal) | [`../lean4/ResearchPapersVerification/Section3_ABCloud/`](../lean4/ResearchPapersVerification/Section3_ABCloud/README.md) |
| Coq (formal) | [`../coq/`section3_ab_cloud/README.md](../coq/section3_ab_cloud/README.md) |
| Isabelle (formal) | [`../isabelle/Section3_ABCloud/README.md`](../isabelle/Section3_ABCloud/README.md) |
| Agda (formal) | [`../agda/Section3_ABCloud/README.md`](../agda/Section3_ABCloud/README.md) |
| C++17 | [`../cpp/section3_ab_cloud/README.md`](../cpp/section3_ab_cloud/README.md) |
| Rust | [`../rust/section3_ab_cloud/README.md`](../rust/section3_ab_cloud/README.md) |
| Haskell | [`../haskell/Section3_ABCloud/README.md`](../haskell/Section3_ABCloud/README.md) |
| Julia | `../julia_levels/` (`l3_…` for the chain sections) / the satellite `research_col_smar/code/julia` |

The same assertions are re-derived in every language of the matrix:
four proof assistants machine-check the structural statements, and five
computational toolchains recompute the numbers with five different
rounding regimes. A reviewer diffs *mathematical content* across systems,
not code style; any disagreement fails the cross-language validator in
[`verification/tests/`](../tests/README.md).

## License

Part of **navier-stokes-b**, license IPL-RP-1.0 ([LICENSE.md](../../LICENSE.md)).
