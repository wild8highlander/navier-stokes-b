# `code/julia/` — Julia Verification Track

A deliberately dependency-free re-implementation of the analytical core
(the JSON writer is hand-rolled), so it runs on a bare Julia 1.10+
installation, including Termux.

| File | Content |
|---|---|
| `sk_core.jl` | module `sk_core`: constants, Lilly relation, closures |
| `p1_p2_julia.jl` | P1 + P2 verification, writes `results/p1_p2_julia.json` |
| `p5_regularity.jl` | P5 track: analytic core (Lanczos gamma), snapshot diagnostics, hand-written radix-2 FFT miniature 16^3 DNS |

Run: `julia p1_p2_julia.jl ../../results` and `julia p5_regularity.jl ../..`
