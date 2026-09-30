# `code/cpp/` — C++17 Verification Track

Long-double re-implementation of the analytical core with a `Makefile`:

| File | Content |
|---|---|
| `sk_core.hpp` | shared constants and closures (header-only) |
| `p1_lilly.cpp` | master relation in `long double` + quadrature checks |
| `p2_closures.cpp` | Heisenberg/Pao closures, log-grid dissipation integrals |
| `p3_apriori_cpp.cpp` | `C_s(Delta/eta)` convergence curves for both filters |
| `p5_regularity.cpp` | P5 track: long-double analytic core (beta_b, x*(b), LPS), raw-snapshot diagnostics, hand-written radix-2 FFT miniature 16^3 DNS |
| `p5c_stretch.cpp` | P5-C track: recomputes the stretching statistics (eigen, beta_S, cos²θ_i, α) from the raw point-tensor artifacts (row-major `(n,n,n,9)` reader) + GOE Monte-Carlo 2·10⁵ |
| `p5d_qr.cpp` | P5-D | Q-R invariants + strain block of the P5-D tensor dump (64^3) in long double; writes `p5d_cpp.json` |
| `Makefile` | `make` (build), `make run` (build + execute into ../../results) |

No external libraries are required; a C++17 compiler (`g++`, `clang++`)
is enough. On Termux: `make CXX=clang++`.