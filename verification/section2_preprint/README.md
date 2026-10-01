# `section2_preprint/` — Preprint NSE — the analytical regularity chain

> **Navigation:** [repository root](../../README.md) › [verification](../README.md) › **`section2_preprint`**

![Section](https://img.shields.io/badge/Section_2-2B579A?style=flat-square) ![Reference](https://img.shields.io/badge/Python_stdlib-2EA043?style=flat-square) ![Contract](https://img.shields.io/badge/PASS_%2B_JSON-FF8C00?style=flat-square) ![License](https://img.shields.io/badge/IPL--RP--1.0-red?style=flat-square)

---

Section 2 encodes the preprint's proof chain as executable assertions: the twist unitarity (the rotation preserves norms and volumes), the Leray premise (per-rotation energy change bounded by machine accumulation, signed injection exactly zero in the mean), and the BKM bridge — the enstrophy of the reference Taylor–Green field is finite and positive, so the blow-up criterion is well-defined on the test case. The formal ports mirror the chain as a lemma sequence from the constant to the stability statement.

## The claims, verbatim

| # | Assertion | Recorded value / tolerance |
|---|---|---|
| C1 | `b ∈ (0,1)` and `sin(θ_b) = b` | |
| C2 | `det R = 1` — the twist is volume-preserving | |
| C3 | `max |ΔE|` per rotation ≤ 1e-12 (measured 6.7×10⁻¹⁶) — the Leray premise | |
| C4 | signed energy injection zero to FP accumulation (`|ΣΔE|` ≤ 1e-12) | |
| C5 | BKM enstrophy finite and positive on the reference TG field (`Ω` = 1.0) | |

Pinned values of the reference run: `max|ΔE|` = 6.66×10⁻¹⁶, `ΣΔE` = −2.53×10⁻¹³ (bound 2.2×10⁻¹²), `Ω` = 1.000000000000

## Layout

| Path | Role |
|---|---|
| [`python/verify.py`](python/verify.py) | the **reference port** — the executable definition of the claims above |
| [`python/README.md`](python/README.md) | how to run it, the contract, the exact expected output |



## How to run

```bash
# direct (the reference port is stdlib-only; mpmath upgrades the precision block)
python3 verification/section2_preprint/python/verify.py
python3 verification/section2_preprint/python/verify.py --preset default   # contract-compatible

# through the aggregate runner (same verdict, uniform harness)
python3 verification/common/python/main.py --section 2 --preset default

# over HTTP, through the REST API
#   GET /api/verify/2  →  the parsed verdict + full output
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
| Lean 4 (formal) | [`../lean4/ResearchPapersVerification/Section2_PreprintNSE/`](../lean4/ResearchPapersVerification/Section2_PreprintNSE/README.md) |
| Coq (formal) | [`../coq/`section2_preprint/README.md](../coq/section2_preprint/README.md) |
| Isabelle (formal) | [`../isabelle/Section2_PreprintNSE/README.md`](../isabelle/Section2_PreprintNSE/README.md) |
| Agda (formal) | [`../agda/Section2_PreprintNSE/README.md`](../agda/Section2_PreprintNSE/README.md) |
| C++17 | [`../cpp/section2_preprint/README.md`](../cpp/section2_preprint/README.md) |
| Rust | [`../rust/section2_preprint/README.md`](../rust/section2_preprint/README.md) |
| Haskell | [`../haskell/Section2_PreprintNSE/README.md`](../haskell/Section2_PreprintNSE/README.md) |
| Julia | `../julia_levels/` (`l2_…` for the chain sections) / the satellite `research_col_smar/code/julia` |

The same assertions are re-derived in every language of the matrix:
four proof assistants machine-check the structural statements, and five
computational toolchains recompute the numbers with five different
rounding regimes. A reviewer diffs *mathematical content* across systems,
not code style; any disagreement fails the cross-language validator in
[`verification/tests/`](../tests/README.md).

## License

Part of **navier-stokes-b**, license IPL-RP-1.0 ([LICENSE.md](../../LICENSE.md)).
