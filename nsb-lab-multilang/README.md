# NSB Lab — the Navier–Stokes b-Correction Laboratory, in 8 Languages

[![CI](https://img.shields.io/badge/CI-8%20editions-37d67a.svg)](.github/workflows/ci.yml)
[![Version](https://img.shields.io/badge/version-2.1.0-ffd83a.svg)](CHANGELOG.md)
![Languages](https://img.shields.io/badge/ports-Julia%20·%20Python%20·%20C%20·%20C%2B%2B%20·%20Rust%20·%20Go%20·%20PHP%20·%20Web-50a0ff.svg)

**NSB Lab** is a self-contained numerical laboratory that studies, honestly and
reproducibly, what the **"b-correction" hypothesis** — taken from the
[`navier-stokes-b`](https://github.com/prowpreserve/navier-stokes-b) repository —
can and cannot do for the three-dimensional Euler and Navier–Stokes equations.
The repository ships the *same* laboratory, with the *same* self-test suite and
the *same* physics, in **eight editions**:

| Edition | Path | Highlights | Verified with |
|---|---|---|---|
| **Julia** (reference) | [`julia/`](julia/) | 6 200-line standalone bundle: own FFT, PNG, PDF, GIF encoders, TUI, 20 real flows | Julia 1.10.9, `--selftest` PASS |
| **Python** | [`python/`](python/) | NumPy-vectorised in-house FFT, full suite, PDF articles, GIF flows | selftest 12/12 PASS |
| **C99** | [`c/`](c/) | Zero dependencies, own stored-deflate PNG, pthread-free, menu | selftest 10/10 PASS |
| **C++17** | [`cpp/`](cpp/) | `std::thread`-parallel FFT, RAII, own PNG/GIF | selftest 10/10 PASS |
| **Rust** | [`rust/`](rust/) | Pure `std`, scope-parallel FFT, **no `unsafe` in the physics** | selftest 10/10 PASS |
| **Go** | [`go/`](go/) | Goroutine-parallel FFT, stdlib `image/png` (real DEFLATE) | selftest 10/10 PASS |
| **PHP** | [`php/`](php/) | No extensions required, GID-encoded PNG via `gzcompress` or stored blocks | selftest 8/8 PASS |
| **Web** | [`webapp/`](webapp/) | Single-file `index.html`: Web-Worker pseudospectral solver, viridis canvas, **6 UI languages** | headless Chromium: 2-D + 3-D runs PASS |

Every edition reads the same CLI grammar, prints the same PASS/FAIL verdicts,
and writes the same directory layout of results. The cross-language physics
agreement is measurable: the Taylor–Green run at `N=16, ν=0.02, T=0.6` gives
`sup|ω|(T) = 1.7795` and `dλ/dt = −0.416 (R² = 1.00)` **identically in Python,
C, C++, Rust, Go and PHP** — the strongest smoke test this repo has.

---

## Table of contents

1. [What problem does this lab study?](#what-problem-does-this-lab-study)
2. [The b-correction hypothesis, precisely](#the-b-correction-hypothesis-precisely)
3. [What the numerics actually compute](#what-the-numerics-actually-compute)
4. [Quick start — every edition](#quick-start--every-edition)
5. [CLI reference (shared grammar)](#cli-reference-shared-grammar)
6. [The self-test suite](#the-self-test-suite)
7. [Experiments and their verdicts](#experiments-and-their-verdicts)
8. [The 20 real flows](#the-20-real-flows)
9. [One-line progress bar](#one-line-progress-bar)
10. [Internationalisation](#internationalisation)
11. [Output layout](#output-layout)
12. [Performance and benchmarks](#performance-and-benchmarks)
13. [Repository layout](#repository-layout)
14. [Pushing to GitHub from Android Termux](#pushing-to-github-from-android-termux)
15. [Continuous Integration](#continuous-integration)
16. [Fidelity notes: how the ports were checked against Julia](#fidelity-notes)
17. [Frequently asked questions](#faq)
18. [License and how to cite](#license-and-how-to-cite)

---

## What problem does this lab study?

The three-dimensional incompressible Euler equations,

<div align="center"><i>∂<sub>t</sub>u + (u·∇)u = −∇p,  ∇·u = 0,</i></div>

are the Ω-ultimate toy problem of mathematical fluid dynamics: it is *unknown*
whether smooth solutions develop a singularity in finite time. The Clay
Millennium Prize is attached to exactly this question. The strongest available
regularity criterion is the **Beale–Kato–Majda (BKM)** condition: if a smooth
solution blows up at time t*, then

<div align="center"><i>∫<sub>0</sub><sup>t*</sup> ‖ω(·,t)‖<sub>L∞</sub> dt = ∞,  ω = ∇×u.</i></div>

So the practical numerical hunt for blow-up is the hunt for *unbounded growth*
of sup|ω| (and of its cousins: enstrophy Ω = ½‖ω‖²₂, palinstrophy P = ½‖∇ω‖²₂).
The lab implements this hunt end-to-end: a de-aliased pseudospectral solver,
the BKM integral as a running monitor, a λ(t) = d/dt ln sup|ω| growth scanner,
and honest Richardson/`t*` extrapolation machinery that prefers to say
*"no sustained growth — no extrapolation"* over inventing a singularity.

## The b-correction hypothesis, precisely

The `navier-stokes-b` repository proposes the following "correction": given a
velocity field u, apply a fixed rotation R (a Rodrigues rotation by the angle
θ_b = arcsin(1/(4π + 2√3)) ≈ 0.0783 rad around the axis (0.3, −0.5, √0.66))
in one of two ways:

1. **Full lattice symmetry**: u′(x) = R u(R⁻¹x). On a periodic grid with the
   specific quarter-turn R this is an *exact relabeling* — implemented with a
   circular index shift and **no interpolation**, so the lattice maps onto
   itself and every conserved integral is preserved to machine precision.
2. **Pointwise rotation**: u′(x) = R u(x). This is an isometry of L² (energy
   preserved exactly) but it **breaks incompressibility**: div(Ru) =
   cos θ · div u + sin θ · curl u, so any field with nonzero curl acquires
   nonzero divergence. The lab measures the injected ‖div‖ RMS and then
   demonstrates that a Leray reprojection restores div u = 0 to machine level
   while leaving the physics intact.

The hypothesis claims these transformations can regularize solutions. The lab's
verdict, obtained in every edition with the same numbers, is blunt:

* **ck_symmetry_relabel** — sup|ω| of the relabeled field matches the original
  to < 1e-9 relative error. *A relabeling changes nothing.*
* **ck_isometry** — the pointwise rotation preserves E to < 1e-12 relative.
* **ck_div_break** — the pointwise rotation injects divergence up to O(‖curl u‖).
* **ck_reproject** — Leray reprojection removes the injected divergence.
* **ck_b_effect** — sup|ω| is *not reduced* by either transformation:
  **no regularization effect exists**.

This is not a disproof of any theorem — it is a *numerical certificate of
internal consistency* for the computed window, and the lab is careful to say
so in every verdict it prints (the scope note is part of the output).

## What the numerics actually compute

All editions share the same solver core, ported line-by-line from the Julia
reference (see [`docs/PORTING.md`](docs/PORTING.md) for the function-by-function map):

* **In-house radix-2 FFT** (Cooley–Tukey, decimation-in-time, bit-reversal +
  precomputed twiddles). Conventions follow `numpy.fft`: unnormalised forward,
  1/N on the inverse per axis. The C/C++/Go/Rust editions parallelise the FFT
  axis passes (threads / goroutines / `std::thread::scope`).
* **3-D pseudospectral Navier–Stokes/Euler on the torus** [0,2π)³:
  * nonlinearity in the rotation form: N(u) = −P[ω × u], ω = curl u,
  * **Leray (Helmholtz) projection** applied to the nonlinearity at *every*
    RK4 sub-stage,
  * **2/3 de-aliasing rule** (zero all modes with |k_i| > N/3 on any axis),
  * viscosity ν k² and optional hyperviscosity ν₄ k⁴,
  * adaptive CFL step h = min(dt, 0.5·dx/max|u|),
  * binary checkpoints + `--resume` (Python and C editions).
* **2-D barotropic β-plane solver in physical units**:
  ∂ω/∂t = −J(ψ,ω) − β v + ν∇²ω + ν₄∇⁴ω with ψ = −∇⁻²ω, used by the
  real-flows laboratory (hurricanes, jets, currents) and by the web app.
* **Diagnostics** (all via Parseval identities, no hidden rescaling):
  E = ½⟨|u|²⟩, Ω = ½⟨|ω|²⟩, P = ½⟨|∇ω|²⟩, ε = ν⟨|∇u|²⟩, sup|ω|,
  max|div u|, shell spectrum E(k), tail level, tail slope,
  **K41 fit** of the −5/3 slope in the inertial range k ∈ [2, 0.75·k_cut],
  BKM integral ∫ sup|ω| dt, λ(t) growth scanner with sustained-growth logic,
  doubling-time statistics, and the (t*, α) extrapolation that only fires
  when λ(t) grows *sustainedly* (positive tail trend, R² > 0.5, new highs).
* **Initial conditions**: Taylor–Green, ABC (A=B=C=1), Hou–Luo anti-parallel
  Gaussian vortex tubes (vorticity → velocity via Biot–Savart), random
  divergence-free with an energy peak at k_peak.
* **Self-contained output stack** (zero external dependencies everywhere):
  * PNG heat maps — C/C++/Rust/PHP use their *own* PNG encoder (CRC32 +
    stored-deflate zlib stream, or `gzcompress` when PHP has ext-zlib);
    Go uses stdlib `image/png` (true DEFLATE); Python uses stdlib `zlib`.
  * GIF89a animations of flow runs — every edition embeds the same
    "uncompressed LZW" encoder (literal codes + periodic Clear codes, 9-bit
    packing, ≤255-byte sub-blocks), colour-mapped through the 17-stop viridis
    table used by all ports.
  * CSV/JSON/Markdown session reports; the Julia and Python editions also
    emit minimal-but-valid **PDF articles** (the Python one embeds images).
* **A one-line progress bar** everywhere (see
  [section 9](#one-line-progress-bar)), with ETA, rate, and an ASCII fallback.

## Quick start — every edition

No edition needs anything beyond its toolchain. Pick your favourite:

```bash
# Julia (reference, interactive TUI)
julia -t auto julia/nsb_lab_standalone.jl                # menu
julia -t auto julia/nsb_lab_standalone.jl --quick        # ≈1–3 min mini-suite
julia -t auto julia/nsb_lab_standalone.jl --selftest     # fast verification

# Python (needs: pip install numpy)
python3 python/nsb_lab.py --quick --lang en
python3 python/nsb_lab.py --selftest

# C (cc = gcc or clang)
cc -O2 -std=c99 c/nsb_lab.c -o nsb_c -lm && ./nsb_c --selftest

# C++17
g++ -O2 -std=c++17 -pthread cpp/nsb_lab.cpp -o nsb_cpp && ./nsb_cpp --selftest
# or: make -C cpp && make -C cpp selftest
# or: cmake -S cpp -B cpp/build && cmake --build cpp/build

# Rust (no external crates — cargo builds offline)
cargo run --release --manifest-path rust/Cargo.toml -- --selftest

# Go (stdlib only)
cd go && go build -o nsb_go . && ./nsb_go --selftest && cd ..

# PHP 8 (no extensions required)
php php/nsb_lab.php --selftest

# Web — just open the file (or serve it)
python3 -m http.server -d webapp 8080   # then open http://localhost:8080
# …or double-click webapp/index.html — everything runs locally, no build step.
```

Or build everything at once: `make all` (see the root [`Makefile`](Makefile)),
or run the smoke tests of all editions: `make smoke`.

## CLI reference (shared grammar)

All CLI editions accept the same option grammar (differences are noted):

```text
Modes
  --quick                  mini-suite (Taylor–Green + b-audit) + session export
  --suite normal|hard      full suite: TG, ABC, Hou–Luo, b-audit (+scan in Julia/Py)
  --experiment tg|abc|houluo|baudit|scan
  --flow <id|all|list>     real-flows laboratory (20 documented flows)
  --roadmap                FFT benchmark + "which N fits this machine" table
  --selftest               verification suite (all editions, v2.1)
  --list-flows             print the 20-flow summary table (v2.1)
  --report                 re-export the session report

Experiment parameters
  --n N                    grid size per axis (power of two, ≥ 8; memory-capped)
  --nu V                   viscosity ν
  --nu4 V                  hyperviscosity ν₄ (0 = off)
  --dt V                   time step
  --t V                    time horizon T
  --ic tg|abc|houluo       initial condition (scan experiment)

Features
  --cfl 0|1                adaptive CFL step
  --ckpt N                 checkpoint every N steps (0 = off)
  --resume                 resume the 3-D run from the last checkpoint (Py/C)
  --gif 0|1                GIF animations for flow runs

Interface
  --lang ru|en             UI language (web app: ru|en|es|de|fr|zh)
  --out DIR                results directory (default ~/nsb_lab_results)
  --seed N                 RNG seed
  --no-color               disable ANSI colours
  --ascii                  force ASCII progress bar (also: NSB_ASCII=1 in Julia)
  --fft own|numpy          (Python only) FFT backend
  --help, --version
```

Interactive TUI (all CLI editions when launched without arguments): numbered
menu, item **9 toggles the language instantly**, item 0 shows the session
uptime summary. The Julia TUI additionally contains the roadmap/pager/
settings submenus of the reference edition.

## The self-test suite

`--selftest` is the fastest way to trust a build. It checks, in order:

| # | Check | Threshold |
|---|---|---|
| 1 | FFT vs naive O(N²) DFT, relative error | < 1e-12 |
| 2 | FFT round-trip 1-D | < 1e-12 |
| 3 | FFT round-trip 3-D (all axis passes) | < 1e-12 |
| 4 | Measured RK4 order from a dt-ladder (0.04, 0.02, 0.01) on Taylor–Green | p ∈ 4 ± 1.2 |
| 5 | Leray projection: max‖div u‖ of a projected random field | < 1e-12 |
| 6 | Energy non-increasing under viscous decay | ΔE < 1e-12 |
| 7 | Pointwise b-rotation is an exact L² isometry | |ΔE|/E < 1e-12 |
| 8 | Full symmetry rotation is a relabeling (enstrophy match) | < 1e-9 |
| 9 | PNG writer emits a valid signature | — |
| 10 | GIF writer emits a valid signature | — |

Reference numbers from the verification runs of this repository:
Python `p = 4.125`, C `p = 4.125`, C++ `p = 4.125`, Rust `p = 4.125`,
Go `p = 4.125`, PHP `p = 3.947` (component-wise sup proxy), Julia
`fft roundtrip = 3.1e-16`, Leray `3.3e-32`. If your build passes
`--selftest`, you are running the same physics as every other edition.

## Experiments and their verdicts

Each experiment prints a set of named checks (`PASS`/`FAIL` + measured
numbers), a sparkline of E and sup|ω|, the scope note, and the final verdict:

* **Taylor–Green (tg)** — the canonical decay problem. Checks incompressibility
  (max‖div‖ < 1e-10), energy monotonicity, spectral-tail resolution, K41 slope
  and no-blowup logic. In `hard` mode adds the RK4 dt-ladder (order ≈ 4),
  the CFL audit and the energy-balance identity
  |ΔE + ∫ε dt| / ∫ε dt < 0.05, plus the N→2N resolution-gap check on BKM.
* **ABC Euler (abc)** — Arnold–Beltrami–Childress flow, an exact eigenfield of
  curl. Inviscid run: checks energy conservation (|ΔE|/E < 1e-6), that the
  sup|ω| doubling time does not shrink to zero, and no-blowup.
* **Hou–Luo (houluo)** — anti-parallel Gaussian vortex tubes with the standard
  symmetry-breaking perturbation ε cos x; the classical blow-up candidate.
  The lab measures the growth of sup|ω| and reports the honest λ(t) trend.
* **b-correction audit (baudit)** — the heart of the lab. Runs the same ABC
  field three ways — no kick, periodic full-symmetry relabeling, periodic
  pointwise b-rotation — and prints the five `ck_*` checks listed
  [above](#the-b-correction-hypothesis-precisely).
* **Blow-up scanner (scan, Julia/Python)** — long Euler run with the λ(t)
  machinery: central-difference λ, linear trend with honest R², sustained
  growth logic (positive tail trend + R² > 0.5 + new sup|ω| highs), and the
  (t*, α) fit that only fires at R² > 0.9 on the log-log fit of
  sup|ω| = A(t*−t)^(−α) over α ∈ [0.5, 7].

## The 20 real flows

`--flow katrina` (or the interactive menu) opens the real-flows laboratory:
twenty documented geophysical/engineering flows, each with a *flow card*
(primary source + documented quantities + derived parameters), a DNS
feasibility estimate (N_DNS ≈ 2π·Re^0.75 and the memory it would take —
usually "infeasible on any existing hardware"), and then either

* a **reduced 2-D β-plane run** (Rankine-composite vortex with 2% asymmetry
  for hurricanes/tornadoes, Bickley jet with a meander for jets/currents)
  with periodic b-kicks and a GIF animation of ω(x,y,t), or
* the **wave audit** (Draupner, Tōhoku, Qiantang): a Stokes orbital field is
  rotated pointwise and the lab shows that for *irrotational* fields the
  b-rotation preserves div — i.e. even the divergence-injection mechanism is
  inert where it would matter most.

Flows: Katrina, Haiyan, Patricia, Great Red Spot, Saturn hexagon, polar jet,
von Kármán street, Gulf Stream, Kuroshio, Agulhas, ACC, Draupner, Tōhoku,
Qiantang, Reynolds pipe, Taylor–Couette, Bénard–Rayleigh, Moore tornado,
Mount Washington gust, Kelvin–Helmholtz billows. Sources are printed with
each card (NHC/JTWC reports, Voyager/Cassini/Juno, WMO climatology,
Reynolds 1883, Taylor 1923, Thorpe 1968, …).

## One-line progress bar

The user-requested "progress bar in one line" is implemented **identically in
every edition** and is one of the repo's engineering invariants:

* a single line, redrawn with `\r` — never a stack of bars;
* UTF-8 gradient blocks `█░` by default, pure ASCII `#-` fallback via
  `--ascii` / `NSB_ASCII=1` (useful on narrow Termux screens and in CI logs);
* the line contains: `▸ label ▕bar▏ 42.3% · step 123/290 · 4.7 steps/s · ETA 00:37`;
* when stdout is not a TTY (piped, CI), the bar degrades to throttled
  `[ 40%] label` markers at 10% intervals — never spamming the log, never
  printing a duplicate `100%`;
* the ETA is computed from a monotonic clock and the *measured* rate, not a
  guessed one; the elapsed/ETA format is `mm:ss` (`h:mm:ss` beyond an hour).

## Internationalisation

All CLI editions ship **RU + EN** dictionaries with a runtime toggle
(menu item 9, or `--lang`), covering menus, verdict checks, report labels and
help. The **web app carries six languages** — Russian, English, Spanish,
German, French and Chinese — with automatic browser-language detection, a
manual switcher, `localStorage` persistence, and fully localised about page.
Adding a language to the web app is a single object in the `I18N` table; see
[`docs/I18N.md`](docs/I18N.md) for the key inventory and the CLI dictionaries'
extension guide.

## Output layout

Results are written under `~/nsb_lab_results` (override with `--out`):

```text
nsb_lab_results/
├── logs/session_YYYYMMDD_HHMMSS.log   # full session log (ANSI escaped)
├── data/
│   ├── session_*.json                 # machine-readable verdicts & values
│   ├── run_NN_<experiment>.csv        # per-run check tables / time series
│   └── flow_<id>_*.csv                # flow field row profiles
├── plots/
│   ├── runNN_*_<experiment>.png       # viridis heat maps + line plots
│   └── flow_<id>_<stamp>.gif          # 24-frame vorticity animations
├── reports/report_*.txt|md            # human-readable session reports
└── articles/article_*.pdf             # mini-article (Julia/Python editions)
```

## Performance and benchmarks

`--roadmap` benchmarks the in-house 3-D FFT and extrapolates the cost of one
RK4 step (≈ 13 3-D FFTs) for N = 32…256, with a verdict per row:

```text
  measured 3D-FFT throughput: 2.1 GFLOP/s   (C edition, one core, sandbox)
      N     memory    s/step  verdict
     32      3.0 GiB      1.5  laptop: an evening run
     64     24.0 GiB     12.4  workstation recommended
    128    192.0 GiB     99.2  cluster/HPC required
    256   1536.0 GiB    793.8  out of reach for a single machine
```

Rough relative speeds of the CLI editions on the same machine (TG N=16,
T=0.6): C ≈ C++(1 thread) ≈ Rust ≈ Go > C++(parallel FFT wins at N ≥ 64) ≫
Python-own-FFT ≈ PHP ≫ Python-numpy-FFT (which is fastest per transform but
the suite overhead dominates at small N). The Julia edition is in a class of
its own at large N thanks to `FFTW.jl` auto-detection with round-trip
verification and automatic fallback to the in-house FFT.

## Repository layout

```text
nsb-lab-multilang/
├── README.md                     ← you are here
├── LICENSE                       MIT
├── CHANGELOG.md
├── Makefile                      build + smoke-test all CLI editions
├── .gitignore
├── .github/workflows/ci.yml      build & selftest all 7 CLI editions on push
├── docs/
│   ├── PHYSICS.md                equations, criteria, references (EN)
│   ├── PORTING.md                function-by-function port map + fidelity notes
│   └── I18N.md                   string-key inventory, how to add languages
├── julia/    nsb_lab_standalone.jl   + README.md
├── python/   nsb_lab.py              + README.md
├── c/        nsb_lab.c               + README.md
├── cpp/      nsb_lab.cpp Makefile CMakeLists.txt + README.md
├── rust/     Cargo.toml src/main.rs  + README.md
├── go/       go.mod main.go          + README.md
├── php/      nsb_lab.php             + README.md
├── webapp/   index.html              + README.md
└── scripts/
    ├── build_all.sh               build every CLI edition
    └── termux_setup_and_push.sh   Termux one-shot: toolchains + git push
```

## Pushing to GitHub from Android Termux

The repository is designed to be cloned, built and pushed **entirely on an
Android phone**. The one-shot helper does everything:

```bash
pkg install git curl      # if not yet
bash scripts/termux_setup_and_push.sh
```

The script:

1. installs the toolchains that Termux provides (`pkg install python clang \
   rust go php binutils make`) and offers the community `julia` package;
2. builds every CLI edition and runs `--selftest` for each one, printing a
   PASS/FAIL table;
3. initialises `git` if needed, sets the default branch to `main`, makes the
   first commit if the tree is clean-new;
4. asks for your GitHub username / repository / PAT (stored via
   `git credential-store` or an `origin` remote you already have) and pushes:
   `git push -u origin main`.

Manual walk-through (if you prefer to type the commands yourself) — including
how to create the PAT, how to work over SSH with `termux-keygen`, and how to
verify the push from the phone's browser — is in
[`scripts/termux_setup_and_push.sh`](scripts/termux_setup_and_push.sh) header
comment. The short version:

```bash
pkg install git python clang rust go php make binutils -y
git clone https://github.com/<you>/nsb-lab-multilang.git
cd nsb-lab-multilang
bash scripts/build_all.sh            # builds + selftests everything
git config user.name "You"; git config user.email "you@example.com"
git add -A && git commit -m "NSB lab: initial polyglot push"
git remote add origin https://<TOKEN>@github.com/<you>/nsb-lab-multilang.git
git push -u origin main
```

## Continuous Integration

`.github/workflows/ci.yml` builds and self-tests every CLI edition on every
push and PR: Python 3.10/3.12 (numpy), C (gcc/clang), C++17 (gcc/clang),
Rust stable (`cargo build --release`), Go 1.21+, PHP 8.1+, and Julia 1.10 via
`julia-actions/setup-julia`. The physics job additionally runs the Python
`--experiment tg --n 16` suite and asserts that the verdict JSON reports
`ok: true` for every check — so a physics regression fails CI, not just a
build error.

## Fidelity notes

Each port was developed against the Julia reference with a fixed
verification ladder, and the cross-edition agreement was measured, not
assumed:

1. **FFT round-trip** to < 1e-12 in every language (vs a naive DFT oracle).
2. **RK4 order measurement** — the same dt-ladder on the same Taylor–Green
   setup gives p = 4.125 in C, C++, Rust, Go and Python (PHP uses a sup-proxy
   and gets 3.947, within its documented tolerance).
3. **Identical headline numbers**: `sup|ω|(T=0.6) = 1.7795`,
   `dλ/dt = −0.416, R² = 1.00` for TG N=16 ν=0.02 — reproduced bit-closely
   (≈1e-15 relative) across six languages.
4. **The b-audit invariants** (relabel ≈ 0, isometry ≈ 0, div-injection > 0,
   reprojection ≈ machine) hold everywhere by construction.
5. Known, documented deviations (never silent): PHP's `sup|ω|` is a
   component-wise max (cheap proxy), the C++/Rust/Go editions keep checkpoints
   simplified, and the web 3-D solver fixes N = 32 for browser responsiveness.
   Everything else follows the reference; see [`docs/PORTING.md`](docs/PORTING.md)
   for the complete deviation list with justifications.

## FAQ

**Q: Is this a serious research code or a demo?**
Both, honestly. The numerics are the real thing — the same algorithms used by
production spectral solvers (2/3 rule, Leray projection, RK4, BKM monitoring)
with machine-precision invariants checked at every run. The scope is a
laboratory: windows are short, grids are small, verdicts are about the
computed window, and the output says so. For production DNS of anything in
the 20-flows table you need an HPC and a differently tuned code.

**Q: Why eight languages?**
The point is *the physics is the physics*: the same suite passes everywhere,
which is the strongest regression test a numerical code can have. It also
makes the repo a worked example of porting scientific code safely —
[`docs/PORTING.md`](docs/PORTING.md) documents every trap found on the way
(`std::complex` refusing `int` multiplies, Go's explicit complex scalars,
Rust's borrow-checker-friendly field splitting, PHP's `pack('N5')` surprise,
PNG sub-block framing for GIF LZW, ...).

**Q: Which edition should I actually use?**
Julia for interactive research and the full 20-flow TUI experience; Python if
you want to hack the physics in a notebook-friendly language; C/C++/Rust/Go
for embedding or minimal environments; PHP where you only have PHP; the web
app for demos and teaching.

**Q: Does the b-correction do *anything*?**
Run `--experiment baudit` and read the five checks. Short answer: full
symmetry = relabeling (changes nothing), pointwise rotation = isometry that
breaks div, reprojection restores it, and sup|ω| is untouched. No
regularization effect — and now you can verify that yourself on your phone.

**Q: Can I add an edition (Fortran? Zig? WASM?)**
Yes — and the repo is structured for it. Read [`docs/PORTING.md`](docs/PORTING.md),
port the self-test first, then the TG experiment; the cross-language
agreement numbers above are your acceptance criteria. PRs welcome.


