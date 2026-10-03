# NSB C++ Lab — the std::thread-parallel edition

**`nsb_lab.cpp`** — the Navier–Stokes b-Laboratory in ~2 200 lines of
modern C++17, single translation unit, standard library only. This
edition's signature feature is the **`std::thread`-parallel FFT**: the
axis passes of every 3-D transform are split across all hardware threads,
with `std::vector`/RAII replacing the C edition's manual memory
management. It passes the same self-test suite and reproduces the same
physics handshake numbers as every other edition.

* **Language**: C++17 (gcc ≥ 9, clang ≥ 10; MSVC 2019+ works with
  `/std:c++17`)
* **Dependencies**: standard library only (`<complex>`, `<thread>`,
  `<filesystem>`, `<random>`, …)
* **Build**: `g++ -O2 -std=c++17 -pthread nsb_lab.cpp -o nsb_lab`
  (or `make`, or CMake ≥ 3.10)

---

## Table of contents

1. [Quick start](#quick-start)
2. [What C++17 buys this edition](#what-cpp17-buys)
3. [The parallel FFT](#the-parallel-fft)
4. [RAII architecture](#raii-architecture)
5. [CLI reference](#cli-reference)
6. [The self-test](#the-self-test)
7. [Physics fidelity](#physics-fidelity)
8. [Build systems: Make and CMake](#build-systems)
9. [The PNG/GIF writers](#the-pnggif-writers)
10. [Performance](#performance)
11. [Termux notes](#termux-notes)
12. [Troubleshooting](#troubleshooting)

## Quick start

```bash
g++ -O2 -std=c++17 -pthread cpp/nsb_lab.cpp -o nsb_lab
./nsb_lab --selftest                       # 10 checks
./nsb_lab --quick --lang en
./nsb_lab --suite hard                     # full criterion set
./nsb_lab --flow katrina --gif 1
./nsb_lab --roadmap                        # benchmark, now multi-threaded
./nsb_lab                                  # interactive TUI
# or
make -C cpp && make -C cpp selftest
cmake -S cpp -B cpp/build && cmake --build cpp/build
```

## What C++17 buys this edition

* **`std::complex<double>`** with operator overloading — the solver reads
  like the equations (`du -= damp * uhat`), with the documented caveat
  that `int * complex` refuses to compile (it would deduce
  `complex<int>`); every integer wavenumber multiply is an explicit
  `cplx(k, 0) * …`. The two `operator*` overloads at the top of the file
  absorb this idiomatically.
* **`std::vector` everywhere** — no manual `malloc/free`, exception-safe
  sizing, and the work-buffers struct (`Work3D`) allocates its fourteen
  N³ fields once in the constructor.
* **`std::filesystem`** for the results tree, `<chrono>` for the monotonic
  clocks behind the progress bar, `<random>` (`mt19937_64`) for the ICs.
* **`std::thread::scope`-free parallelism**: this edition predates C++20
  scopes and uses explicit join vectors — see next section.

## The parallel FFT

The 3-D transform decomposes into three axis passes. The contiguous axis
(k) parallelises trivially: the flat buffer is split into `n²` lines and
`fft_lines_par` hands each worker thread a disjoint `split_at_mut`-style
range (implemented with `std::vector::data` + index windows and a join
list — no data races by construction, no mutexes needed because the
ranges are disjoint).

The two strided axes (j and i) use the **gather → parallel transform →
scatter** pattern: a serial permutation gathers each line into a
contiguous temp buffer, the same parallel line-transformer runs on it,
and a serial scatter writes the result back. This costs two extra
full-array passes per strided axis (≈10–15% at N ≥ 64) and buys a
completely data-race-free transform with no unsafe code and no locks on
the hot path. Worker count = `std::thread::hardware_concurrency()`.

The measured effect (verification machine, 8 cores): N=32 transform
≈ 1.4× serial, N=64 ≈ 3.1×, N=128 ≈ 5.6× — the gather/scatter share
grows with N, which is exactly why the Julia edition (FFTW) still wins
at the top end.

## RAII architecture

`NSE3D` (wavenumber arrays, mask, k²safe), `Work3D` (fourteen N³ buffers:
spectral state stages K1–K4, T1–T3, scratch `Field3`s, the physical u/w
triples, the projection scratch `kd`) and `Baro2D` are all
constructor-allocated and destructor-freed; nothing leaks, nothing is
copied on the hot path (fields are moved). The experiments are plain
functions that construct what they need and let scope do the cleanup —
the C edition's `free` ladder disappears entirely.

One architectural note for porters: `ifft_field3`/`fft_field3` use the
dedicated `scratch` field, *never* the RK4 stage arrays. The first draft
used `T1` as transform scratch and clobbered the RK4 intermediate state
(the self-test caught it as `p = 0.94` and `ΔE = 8e-3`); the rule and the
story are in `../docs/PORTING.md` §4.

## CLI reference

Shared grammar (root README §5): `--quick --suite normal|hard
--experiment tg|abc|houluo|baudit --flow <id|all|list> --roadmap
--selftest --list-flows --report --n --nu --nu4 --dt --t --cfl --gif
--lang --out --seed --no-color --ascii --help --version`. Checkpoints are
accepted and ignored (documented deviation — the C edition has the full
implementation). TUI as everywhere: items 1–8, 9 = language toggle,
0 = exit with uptime.

## The self-test

Ten checks, ≈ 6 s: FFT vs naive DFT (3e-15), 1-D round-trip (5e-16),
3-D round-trip (6e-16), RK4 order from the dt-ladder (`p = 4.125`),
Leray divergence on a random field (3.3e-16), energy non-increase,
b-rotation isometry (1e-15), full-symmetry relabeling (9e-16), PNG
signature, GIF signature. Exit code 0 only when all pass — the CI job
runs exactly this.

## Physics fidelity

Handshake numbers reproduce the reference to ≈1e-12:
`sup|ω|(T=0.6) = 1.7795`, `dλ/dt = −0.416 (R² = 1.00)` for
`N=16, ν=0.02, dt=0.01`. The full experiment set (TG with hard-mode
ladder, ABC Euler, Hou–Luo, b-audit), the 2-D barotropic flow runner
with b-kicks and GIF capture, the 20-flow table with DNS feasibility,
and the wave audits are ported. Deviations are documented in
`../docs/PORTING.md` §3 (checkpoints stubbed; plot writer reduced to
heat maps).

## Build systems

**Make** (`cpp/Makefile`): `all`, `run`, `selftest`, `clean` targets,
`CXX`/`CXXFLAGS` overridable.

**CMake** (`cpp/CMakeLists.txt`): minimum 3.10, C++17 required,
`Threads::Threads` linked (the only "find" needed), `-O2 -Wall`.
Both are CI-verified (gcc + clang matrix).

## The PNG/GIF writers

Same zero-dependency design as the C edition, in idiomatic C++: the
zlib stream is built from stored DEFLATE blocks with a hand-rolled
Adler-32; CRC32 uses the standard reflected table; chunk assembly is a
small helper over `std::ostream`. The GIF encoder carries the
uncompressed-LZW packer with the ≤255-byte sub-block rule (the rule whose
violation is the canonical GIF bug — see `../docs/PORTING.md` §4). The
C++ version's first draft computed the PNG CRC over the tag only —
IHDR/IDAT rejected by every decoder — and the fixed `png_chunk` computes
CRC over `tag + data`, exactly per the spec. Both bugs are documented
so porters check for them.

## Performance

Reference machine (8 cores): selftest ≈ 5 s; TG N=16 T=0.6 ≈ 3 s;
TG N=32 T=2 ≈ 55 s (parallel FFT already helping); flow run 64² ≈ 2 s.
The `--roadmap` benchmark reports the parallel GFLOP/s and the N→cost
table with the same verdict thresholds as every edition.

## Termux notes

`pkg install clang binutils` and the single build line work on
aarch64; `hardware_concurrency()` picks up the big.LITTLE topology and
the FFT workers spread across both clusters. For long runs,
`termux-wake-lock` as usual. If the linker complains about
`-pthread` on old Termux versions, drop the flag — modern Android libc
is threads-capable by default.

## Troubleshooting

* **`error: no match for 'operator*' (int, complex)`** — you added a new
  integer-scalar multiply; cast it (`cplx(k,0) * z`) or use the file-top
  overloads.
* **`p ≈ 0.94` in selftest RK4** — your transform helpers are clobbering
  a stage array; make sure they only touch `scratch`, never `T1/T2`.
* **PNG opens nowhere** — verify `png_chunk` CRCs over `tag + data`
  (parse the file with Python's `zlib.crc32` if in doubt).
* **Threads don't speed up N=32** — expected (per-thread work < join
  overhead); the crossover is ≈ N=64 on most machines.
