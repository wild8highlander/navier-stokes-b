# `code/` — Three-Language Verification Tracks

The analytical core of the program (the master relation, the closures and
the spectral identities) is deliberately tiny, so it is implemented three
times and the outputs must agree:

| Directory | Language | Covers | Runtime |
|---|---|---|---|
| `python/` | Python 3.11+ | everything: P1-P5 + figures | ~25 min |
| `cpp/` | C++17 (no external libraries) | P1, P2, P3-sensitivity, P5 | ~1 min |
| `julia/` | Julia 1.10+ (no packages at all) | P1, P2, P5 | ~30 s |

Cross-language agreement at `C_K = 1.50`: `C_s` sharp = 0.17327 (Python) =
0.173266 (C++, long double) = 0.17327 (Julia). A relative divergence above
1e-5 in any shared quantity is a hard failure of the program. The P5
smoothness extension adds its own three-language verdict:
`results/p5_cross_language.json` (status PASS: analytic block ≤ 2.3·10⁻¹²,
snapshot diagnostics ≤ 3.3·10⁻¹², miniature DNS machine-precise at t = 0
and ≤ 8.1·10⁻⁶ at t = 1, the growth being the chaotic amplification of
floating-point noise).

Run instructions: see the parent README, section 8.
