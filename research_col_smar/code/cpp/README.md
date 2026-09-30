# `code/cpp/` — C++17 Verification Track

Long-double re-implementation of the analytical core with a `Makefile`:

| File | Content |
|---|---|
| `sk_core.hpp` | shared constants and closures (header-only) |
| `p1_lilly.cpp` | master relation in `long double` + quadrature checks |
| `p2_closures.cpp` | Heisenberg/Pao closures, log-grid dissipation integrals |
| `p3_apriori_cpp.cpp` | `C_s(Delta/eta)` convergence curves for both filters |
| `p5_regularity.cpp` | P5 track: long-double analytic core (beta_b, x*(b), LPS), raw-snapshot diagnostics, hand-written radix-2 FFT miniature 16^3 DNS |
| `Makefile` | `make` (build), `make run` (build + execute into ../../results) |

No external libraries are required; a C++17 compiler (`g++`, `clang++`)
is enough. On Termux: `make CXX=clang++`.
