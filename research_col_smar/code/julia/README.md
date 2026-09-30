# `code/julia/` — Julia Verification Track

A deliberately dependency-free re-implementation of the analytical core
(the JSON writer is hand-rolled), so it runs on a bare Julia 1.10+
installation, including Termux.

| File | Content |
|---|---|
| `sk_core.jl` | module `sk_core`: constants, Lilly relation, closures |
| `p1_p2_julia.jl` | P1 + P2 verification, writes `results/p1_p2_julia.json` |
| `p5_regularity.jl` | P5 track: analytic core (Lanczos gamma), snapshot diagnostics, hand-written radix-2 FFT miniature 16^3 DNS |
| `p5c_stretch.jl` | P5-C track: recomputes the stretching statistics from the raw point-tensor artifacts — the file is POINT-major C-order `(n,n,n,9)`, so the column-major reader must reshape `(9, N, N, N)` (the `(N,N,N,9)` variant scrambles channels with spatial nodes) — plus GOE Monte-Carlo 2·10⁵ |

Run: `julia p1_p2_julia.jl ../../results`, `julia p5_regularity.jl ../..`
and `julia p5c_stretch.jl ../..`