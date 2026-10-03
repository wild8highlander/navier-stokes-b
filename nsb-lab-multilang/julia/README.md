# NSB Julia Lab — the reference edition

**`nsb_lab_standalone.jl`** — a single-file, self-contained laboratory for
the three-dimensional incompressible Euler/Navier–Stokes equations and their
two-dimensional β-plane reduced models, built around the *b-correction
hypothesis* audit (see the [root README](../README.md) for the research
context and [`../docs/PHYSICS.md`](../docs/PHYSICS.md) for every equation).

This is the **reference edition**: the largest, oldest and most feature-
complete of the eight ports. Every other edition in this repository is a
line-by-line port of the algorithms that were first written here, and the
cross-language verification numbers quoted everywhere come from this file.

* **Language**: Julia ≥ 1.10 (written and verified on 1.10.9)
* **Dependencies**: none. Standard library only — `Printf`, `LinearAlgebra`,
  `Random`, `Base64`, `Dates`, `Serialization`, `Statistics`. If `FFTW.jl`
  happens to be installed it is *optionally* used as a faster FFT backend,
  verified by a round-trip against the in-house FFT and silently rolled
  back on any mismatch.
* **Size**: ~6 200 lines, one file, zero package installs.

---

## Table of contents

1. [Why a single file](#why-a-single-file)
2. [Quick start](#quick-start)
3. [The interactive TUI](#the-interactive-tui)
4. [CLI reference](#cli-reference)
5. [Architecture walkthrough](#architecture-walkthrough)
6. [The in-house FFT](#the-in-house-fft)
7. [The 3-D solver](#the-3-d-solver)
8. [The 2-D β-plane and the 20 flows](#the-2-d-β-plane-and-the-20-flows)
9. [The output stack: PNG, PDF, GIF without packages](#the-output-stack)
10. [Diagnostics and the blow-up scanner](#diagnostics-and-the-blow-up-scanner)
11. [Checkpoints, CFL, hyperviscosity](#checkpoints-cfl-hyperviscosity)
12. [What v2.1 changed](#what-v21-changed)
13. [Performance notes and the roadmap table](#performance-notes)
14. [Running on Termux](#running-on-termux)
15. [Troubleshooting](#troubleshooting)

## Why a single file

The lab is deliberately a *standalone bundle*: `julia nsb_lab_standalone.jl`
works on any machine with Julia installed and nothing else — no
`Pkg.add`, no network, no project environment. That constraint shaped
everything: the FFT is hand-written, PNG/PDF/GIF encoders are implemented
from their format specifications, the TUI is built from ANSI escapes, and
even the viridis colormap is a 17-entry table in the source. The payoff is
that this file runs identically on a laptop, in a CI container, on a
cluster login node, and in Termux on an Android phone — which is exactly
the demonstration the polyglot repository wants to make.

The file is assembled from logical "source units" (00_boot, 01_i18n, …
18_menu, 99_main) whose boundaries are marked in comments; if you want to
restructure it into a package, those markers are the cut lines.

## Quick start

```bash
julia -t auto nsb_lab_standalone.jl             # interactive menu
julia -t auto nsb_lab_standalone.jl --quick     # mini-suite + PDF, ≈1–3 min
julia -t auto nsb_lab_standalone.jl --selftest  # fast verification (v2.1)
julia -t auto nsb_lab_standalone.jl --list-flows
julia -t auto nsb_lab_standalone.jl --flow katrina --gif 1
julia -t auto nsb_lab_standalone.jl --suite hard --ckpt 100 --resume
julia -t auto nsb_lab_standalone.jl --help
```

From a live REPL, `include("nsb_lab_standalone.jl")` opens the menu; after
exit (item 0) the namespace stays available:

```julia
nsb_lab()                     # menu again
nsb_lab("--quick")            # batch mode from the REPL
nsb_lab("--experiment", "tg", "--n", "64")
```

The `-t auto` flag enables multithreaded FFT (≈×5 on 8 cores). The strict
superset of speed: `julia -O3 --check-bounds=no -t auto
nsb_lab_standalone.jl` shaves 20–40% off solver time.

Results go to `~/nsb_lab_results/{logs,data,plots,reports,articles}`
(configurable via `--out`; persisted defaults in `~/.nsb_lab.json`).

## The interactive TUI

Launch without arguments. The banner shows the title, the config line
(output dir, DPI cap, memory-derived N cap, FFT backend) and the session
uptime. Menu items:

1. **Quick run** — Taylor–Green mini-suite + b-audit + final PDF.
2. **Full suite, NORMAL** — TG, ABC, Hou–Luo, b-audit at N=32-ish settings.
3. **Full suite, HARD** — same at N=64-ish with the extra criteria (RK4
   order ladder, CFL audit, energy-balance identity, N→2N resolution gap).
4. **Custom experiment** — prompts for N, ν, dt, T, IC (TG/ABC/Hou–Luo/
   random), b-correction mode (off/full-symmetry/pointwise), Euler toggle.
5. **Real-flows laboratory** — the 20 documented flows (§8).
6. **Roadmap & this hardware** — FFT benchmark + the N→cost table.
7. **Session reports** — re-exports everything computed this session.
8. **Settings & about** — DPI, output dir, the project abstract.
9. **Language toggle** — RU ↔ EN, instant, everything re-renders.
0. **Exit** — prints the session uptime summary.

The TUI includes a pager for long tables (`Enter/space` next, `b` back,
`q` quit), terminal half-block viridis images of 2-D fields (truecolor or
256-colour with a quantiser), and sparklines of E/sup|ω| in verdicts.

## CLI reference

The grammar below is shared by all CLI editions (see root README §5); the
Julia edition implements the full superset:

```
--quick | --suite normal|hard | --experiment tg|abc|houluo|baudit|scan
--flow <id|all|list> | --roadmap | --selftest | --list-flows
--report | --timings
--n N --nu V --nu4 V --dt V --t V --ic tg|abc|houluo
--cfl 0|1 --ckpt N --resume --gif 0|1
--lang ru|en --dpi N --out DIR --seed N --no-color --ascii --help
```

`--timings` prints the per-run wall-clock table of the session (start,
finish, duration of every experiment). `NSB_LAB_LANG`, `NSB_FFT=own`,
`NSB_ASCII=1`, `NO_COLOR` environment variables are honoured.

## Architecture walkthrough

The bundle's units, in file order:

* **00_boot** — version, machine probe (CPU model, threads, RAM → the
  memory-safe `max_n` cap), config struct, TTY/colour detection
  (`NO_COLOR`, `TERM=dumb`, `COLORTERM=truecolor`), session log file,
  `~/.nsb_lab.json` settings persistence.
* **01_i18n** — the RU/EN dictionary (≈120 keys) with compiled-printf
  caching.
* **02_ui** — ANSI helpers, the **one-line progress bar** (§ v2.1 notes),
  sparklines, terminal half-block images, boxes, verdict lines, pager.
* **03_deflate_png + 04_font + 05_plots** — a from-scratch PNG stack:
  own zlib-compatible stored+fixed-Huffman deflate, CRC32, a bitmap
  Helvetica font (for plot labels!), a line-plot rasteriser with axes,
  ticks, legend, log-y; viridis via the 17-stop table.
* **05b_gif** — GIF89a writer with a real LZW encoder and per-frame
  colour mapping (used for flow animations).
* **06_fft** — the in-house radix-2 FFT (next section) + optional verified
  FFTW backend.
* **07_solver3d** — the 3-D operator, Leray projection, curl form, RK4,
  Biot–Savart IC conversion, the two b-rotations, CFL estimate.
* **08_diagnostics** — every integral from `PHYSICS.md` §4, shell spectra,
  tail/K41 fits, OLS with R².
* **09_ic_bcorr** — ICs and the Rodrigues machinery, the θ_b constant,
  the exact quarter-turn relabeling.
* **10_blowup** — λ(t) scanner, doubling times, sustained-growth logic,
  the (t*, α) search, Richardson extrapolation helpers.
* **11_experiments** — the five experiments with their check lists.
* **12_flows** — the 2-D barotropic solver (zero-allocation work buffers)
  and the 20-flow laboratory with DNS feasibility.
* **13_roadmap** — benchmark + the cost table.
* **14_reports / 15_pdf / 16_final_report / 16b_features** — session
  export in TXT/MD/CSV/JSON/HTML+SVG/PDF, the embedded-font PDF article
  writer, settings persistence, timings.
* **17_cli / 18_menu / 99_main** — argument parsing, dispatch, the TUI.

## The in-house FFT

Radix-2 decimation-in-time, in-place, with precomputed twiddles and a
bit-reversal table per plan. Conventions follow `numpy.fft` (unnormalised
forward, 1/N per axis on the inverse). 3-D transforms run each axis pass
under `Threads.@threads`; axis 1/2 passes use per-thread scratch buffers
to stay allocation-free. The self-test compares against a naive O(N²) DFT
(round-trip error ~3e-16 at N=16) *and* verifies any FFTW plan with a
round-trip against the in-house result before trusting it (falling back
on any discrepancy or on `NSB_FFT=own`).

## The 3-D solver

The operator evaluates, per RK4 stage: curl in spectral space (`i k×`), two
inverse FFT sets (u, ω) with reusable work buffers, the physical-space
cross product ω×u, the forward FFT set, the 2/3 mask, the Leray projection
and the dissipation `(νk² + ν₄k⁴)û`. The state is always kept
masked/de-aliased: the final combination of each RK4 step re-masks.
`PHYSICS.md` §3 documents why the rotation form + projection is exact for
the periodic torus. Checkpoint files are Julia `Serialization` streams
written every `ckpt_every` steps (label, step, t, û triple, time series)
and consumed by `--resume`.

## The 2-D β-plane and the 20 flows

The barotropic operator works in *physical units*: wavenumbers
`k_phys = 2πk/L_box`, streamfunction `ψ̂ = −ω̂/kp²`, velocities
`û = i kpy ψ̂`, `v̂ = −i kpx ψ̂`, and the RHS
`−(u ∂xω + v ∂yω) − βv̂ + (νkp² + ν₄kp⁴)ω̂`, masked by the 2/3 rule.
All matrix work happens in pre-allocated buffers (`NsbBaroWork`) — the RHS
is zero-allocation, which matters at N=128 hard mode.

Each flow gets a **card**: primary source and documented quantities
(quoted from NHC/JTWC reports, Voyager/Cassini/Juno papers, Reynolds 1883,
Taylor 1923, Thorpe 1968, …), derived parameters (molecular and effective
Re, Coriolis f, β, Rossby number, advective time, Kolmogorov scale,
N_DNS ≈ 2πRe^0.75 and its memory), and a DNS-feasibility verdict. Then:
vortex/jet flows run the reduced β-plane model with periodic b-kicks and
emit a GIF; wave flows (Draupner, Tōhoku, Qiantang) run the Stokes
orbital-field audit showing that the b-rotation *preserves* divergence on
irrotational fields.

## The output stack

* **PNG** — own deflate (stored + fixed-Huffman blocks, CRC32, Adler32),
  viridis heat maps and rasterised line plots with a bitmap font.
* **GIF** — LZW-encoded GIF89a animations of the flow runs (24 frames).
* **PDF** — a from-scratch PDF writer with an embedded bitmap Helvetica
  (the *only* edition that renders Cyrillic text in PDF), plots and heat
  maps, producing the final "mini-article" of a session.
* **Reports** — TXT/MD/CSV/JSON per session; the JSON carries every check
  with its measured detail string, ready for CI consumption.

## Diagnostics and the blow-up scanner

Everything from `PHYSICS.md` §4–5 is implemented here first: the Parseval
diagnostics, shell spectra, tail level/slope, the K41 fit, the BKM running
integral, the λ(t) scanner with its sustained-growth gate (positive tail
trend AND R²>0.5 AND new sup|ω| highs), doubling-time statistics and the
guarded (t*, α) extrapolation. The scanner's honesty gates are the point:
in all the runs this repository has ever produced, Taylor–Green and ABC
windows end with *"no sustained λ growth → no t* extrapolation"* — exactly
as they should.

## Checkpoints, CFL, hyperviscosity

`--ckpt N` writes a serialised checkpoint every N steps (and removes it at
successful completion); `--resume` restarts the labelled run from it —
state, clock and time series. `--cfl 1` switches on the adaptive step
`h = min(dt, 0.5·dx/max|u|)` (audited; the verdict reports the count of
adapted steps). `--nu4` switches on hyperviscosity for tail stabilisation;
the energy-balance check accounts for both ε terms.

## Research 

Relative to the upstream reference (all changes documented in the
file header and in [`../CHANGELOG.md`](../CHANGELOG.md)):

1. **ASCII progress fallback** (`NSB_ASCII=1`): `#-` blocks instead of
   gradient `█░`, for narrow terminals and log scrapers.
2. **`--selftest`**: FFT round-trips, Leray machine-level divergence, and
   the PASS/FAIL summary — the five-second trust builder.
3. **`--list-flows`**: the 20-flow summary table straight to stdout.
4. **Batch progress de-duplication**: the non-TTY path no longer prints a
   duplicate 100% marker at run end.
5. Physics, numerics and formats are **untouched** — is interface
   only, verified by running the upstream experiments before and after.

## Performance notes

On the reference laptop (8 threads): 3-D in-house FFT ≈ 1.2 GFLOP/s single
thread, ≈ 5× with `-t auto`; a TG N=32 normal run is ≈ 40 s; the hard suite
(N=64 + ladders) is an evening. With FFTW.jl installed the transform stage
accelerates a further 3–6× and the roadmap table's "evening run" boundary
moves from N=64 to N=96. `--roadmap` prints the machine-specific table:

```text
      N     memory    s/step  verdict
     32      3.0 GiB      0.9  laptop: an evening run
     64     24.0 GiB      7.4  workstation recommended
    128    192.0 GiB     59.1  cluster/HPC required
    256   1536.0 GiB    472.9  out of reach for a single machine
```

## Running on Termux

Termux ships Julia in the community repo (`pkg install julia` via
`tur-reboot`/`tur`; see `../scripts/termux_setup_and_push.sh` which
detects and offers it). On a modern phone expect the normal-mode suite at
N=32 to take minutes and the quick run ≈ 2–5 minutes — perfectly usable.
The TUI degrades gracefully: if `stdout` is not a TTY (e.g. `termux-wake-
lock` + piped logging) the progress bar switches to the throttled percent
markers automatically.

