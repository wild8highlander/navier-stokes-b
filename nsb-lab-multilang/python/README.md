# NSB Python Lab — the NumPy-vectorised edition

**`nsb_lab.py`** — the complete Navier–Stokes b-Laboratory in one Python
file: in-house radix-2 FFT (vectorised with NumPy), the 3-D pseudospectral
solver with Leray projection and 2/3 de-aliasing, the 2-D barotropic
β-plane solver, the full BKM diagnostics suite, the five experiments, the
20 real flows with DNS-feasibility estimates, and a zero-dependency output
stack (own PNG writer, GIF89a animator, minimal PDF article writer,
CSV/JSON/Markdown reports).

* **Language**: Python ≥ 3.9
* **Dependencies**: `numpy` (the only one). Everything else is stdlib.
  `matplotlib` is *not* required — plots are rendered by the built-in
  rasteriser; if you prefer matplotlib-quality figures, the time series
  are all in `data/*.csv` and trivially plottable.
* **Size**: ~2 800 lines, one file.

---

## Table of contents

1. [Quick start](#quick-start)
2. [Why the FFT is in-house even in Python](#why-the-fft-is-in-house)
3. [What exactly is ported](#what-exactly-is-ported)
4. [CLI reference](#cli-reference)
5. [The self-test in detail](#the-self-test-in-detail)
6. [The 3-D solver and its buffers](#the-3-d-solver-and-its-buffers)
7. [The 2-D β-plane and the flows](#the-2-d-β-plane-and-the-flows)
8. [The output stack](#the-output-stack)
9. [Experiments and expected numbers](#experiments-and-expected-numbers)
10. [i18n and the one-line progress bar](#i18n-and-the-one-line-progress-bar)
11. [Performance guide](#performance-guide)
12. [Using it as a library](#using-it-as-a-library)
13. [Running on Termux](#running-on-termux)
14. [Troubleshooting](#troubleshooting)

## Quick start

```bash
pip install numpy                  # the only dependency
python3 nsb_lab.py                 # interactive menu (RU/EN, item 9 toggles)
python3 nsb_lab.py --quick --lang en
python3 nsb_lab.py --selftest      # 12 checks, ≈40 s at N=16
python3 nsb_lab.py --experiment tg --n 32 --t 2
python3 nsb_lab.py --flow katrina --gif 1
python3 nsb_lab.py --roadmap       # FFT benchmark + cost table
python3 nsb_lab.py --list-flows
python3 nsb_lab.py --suite hard    # the full criterion set (long!)
```

Results land in `~/nsb_lab_results/` (`--out` overrides). Session JSON in
`data/`, plots in `plots/`, reports in `reports/`, the mini-article PDF in
`articles/`.

## Why the FFT is in-house even in Python

`numpy.fft` is one import away — so why does this edition ship its own
radix-2 Cooley–Tukey on top of NumPy arrays? Because the *point* of the
polyglot repository is that the same algorithms run everywhere, and the FFT
conventions (unnormalised forward, 1/N per axis inverse, bit-reversal
ordering, 2/3 mask placement) are part of the physics contract that the
self-test verifies. The NumPy port implements the same DIT butterfly loop
but *vectorises it over all transform lines at once* (reshaping to
`(..., n/size, size)` blocks, broadcasting the twiddle vector) — so it is
still the lab's FFT, ~50× faster than a scalar loop, and it still passes
the same naive-DFT oracle. If you want pure speed instead of provenance,
`--fft numpy` switches the transforms to `numpy.fft` (verified equivalent
by the same round-trip test); the default remains the in-house backend so
that the repo's cross-language numbers stay comparable.

## What exactly is ported

From the Julia reference (see `../docs/PORTING.md` for the full map):

* FFT (1/2/3-D), the 3-D operator (`NSE3D`: k-arrays, 2/3 mask, k²safe),
  Leray projection, rotation-form RHS, RK4 stepping with per-stage
  projection+masking, CFL estimate;
* ICs: Taylor–Green, ABC, Hou–Luo (vorticity → Biot–Savart → velocity),
  random div-free with k_peak seeding;
* the two b-rotations: `rotate_pointwise3` (Rodrigues matrix applied to the
  physical field) and `rotate_full_symmetry3` (the exact quarter-turn
  index-shift relabeling, `(n − i) mod n` mapping);
* all diagnostics: energy, enstrophy, palinstrophy, dissipation (+hyper),
  sup|ω|, divergence, shell spectrum, tail level/slope, K41 fit, OLS with
  R², observed order, Richardson extrapolation, BKM integral, λ(t) scanner
  with the sustained-growth gate, doubling times, the guarded (t*, α) fit;
* the runner with one-line progress, adaptive CFL, checkpoints
  (`pickle` files) and `--resume`, b-kick scheduling;
* the five experiments with their full check lists (TG includes the hard
  mode ladder: RK4 order, CFL audit, energy-balance identity, N→2N gap);
* the 2-D barotropic solver and the 20 real flows (cards, DNS feasibility,
  vortex/jet reduced runs with b-kicks + GIF, wave audits);
* the output stack: PNG (stdlib `zlib` deflate + own CRC32 chunking),
  GIF89a (uncompressed-LZW trick, 9-bit packing, sub-blocks), the minimal
  PDF article writer, CSV/JSON/MD/TXT reports, terminal half-block viridis
  images, sparklines;
* RU/EN i18n and the one-line progress bar with ASCII fallback.

## CLI reference

Identical grammar to the root README §5. Python-specific extras:

* `--fft own|numpy` — transform backend (default `own`);
* `--ascii` / `NSB_ASCII=1` — ASCII progress blocks;
* `--resume` consumes the pickle checkpoint written by `--ckpt N`.

## The self-test in detail

`--selftest` runs 12 checks and exits non-zero on any failure:

1. FFT round-trip 1-D (vs input copy) — 5e-16 typical
2. FFT vs naive O(N²) DFT — 3e-15 typical
3. FFT round-trip 2-D
4. FFT round-trip 3-D
5. RK4 order from the dt-ladder on TG (N=16) — `p = 4.125` typical
6. Leray projection on a *random* field — `max|div| ≈ 3e-16`
7. Energy non-increasing under viscous decay
8. Pointwise b-rotation isometry — `|ΔE|/E ≈ 0`
9. Full-symmetry relabeling — `|ΔΩ|/Ω ≈ 0`
10. PNG writer signature
11. GIF writer signature
12. PDF writer signature

The two subtleties worth knowing: check 6 uses a *random* IC (Taylor–Green
is already solenoidal by construction and would pass with a broken
projector), and check 9 compares enstrophy, not energy — any index
permutation conserves energy, only the correct mirror mapping conserves the
spectral content.

## The 3-D solver and its buffers

Fields are `np.ndarray` triples of complex128. `rhs3` computes: curl in
spectral space (`i k×`), two inverse transform sets into physical space,
the cross product `ω×u`, the forward transform, the 2/3 mask, projection,
damping. All work arrays are preallocated once per run (`K1..K4, T1, T2`)
and the state swap is reference swapping. The runner samples diagnostics
every `sample_every` steps (default 4): curl → sup|ω|, energy, divergence,
BKM increment with the trapezoid over the sampling interval.

The time loop prints the one-line progress bar (`▸ label ▕bar▏ pct · step
n/N · rate · ETA`), honours `blowup_stop` (halts at sup|ω| > 1e8), writes
checkpoints, and records the CFL audit counters.

## The 2-D β-plane and the flows

`Baro2D` carries *physical* wavenumbers (`2πk/L_box`), builds ψ̂ from ω̂,
evaluates the advection `−(u ∂xω + v ∂yω)` pseudospectrally, adds the β
term and the ν/ν₄ dissipation, masks, and steps with RK4. Diagnostics
(E, Z, P) come from Parseval over the physical-units spectra. The flow
runner picks the Rankine-vortex or Bickley-jet IC from the flow's model
type, sets `Re_model = 2000` (8000 in hard mode), derives the timestep
from `0.4·dx/umax`, schedules b-kicks every `t_adv`, captures 24 frames
for the GIF, and produces the verdict checks (stability, growth, kick
injection).

## The output stack

* **PNG** (`write_png_rgb`): raw RGB rows + filter bytes → `zlib.compress`
  → CRC32-chunked IHDR/IDAT/IEND. `heat_png` maps a field through viridis,
  upscales nearest-neighbour ×6, pads with a dark frame, and embeds the
  title as a `tEXt` chunk.
* **Line plots** (`plot_png`): grid, frame, polylines with the lab palette,
  legend, optional log-y — enough for E/Ω/P histories.
* **GIF** (`write_gif`): GIF89a, global 256-colour viridis palette,
  NETSCAPE loop, per-frame GCE with disposal flags, the uncompressed-LZW
  bit stream (Clear + literals + periodic Clear + EOI, 9-bit packed,
  ≤255-byte sub-blocks) — verified byte-compatible with PIL/Chrome/Firefox.
* **PDF** (`write_pdf_article`): a minimal but valid PDF-1.4 writer —
  Helvetica/Bold text pages, word-wrapped, plus full-page raw-RGB image
  XObjects for the heat maps. English-only text (base-14 fonts carry no
  Cyrillic; documented in `docs/I18N.md`).
* **Reports**: session JSON (every check with detail strings), per-run
  CSVs, TXT/MD reports.

## Experiments and expected numbers

Reference run on the verification machine (Python 3.12, numpy 2.1):

```text
$ python3 nsb_lab.py --experiment tg --n 16 --t 0.6 --dt 0.01 --lang en
  incompressibility: max|div u| at machine level   (max|div| = 1.59e-17)
  energy non-increasing (viscous decay)            (ΔE_max = 0.00e+00)
  spectral tail resolved                           (tail/peak = 1.35e-06)
  stability: no NaN/Inf                            (sup|ω|_final = 1.7795)
  no finite-time blow-up signature                 (dλ/dt = -0.416, R²=1.00)
  VERDICT: all checks passed
```

`sup|ω|(T=0.6) = 1.7795` is the cross-language handshake number: the C,
C++, Rust, Go and PHP editions reproduce it to ≈1e-12 (see root README §
"Fidelity notes"). The hard-mode TG additionally reports the measured RK4
order (`p = 4.125`), the CFL audit, the energy-balance residual (< 0.05)
and the N→2N BKM gap (< 5%).

## i18n and the one-line progress bar

The RU/EN dictionary mirrors the Julia key set (`docs/I18N.md`). Menu item
9 flips the language instantly; `--lang` and `NSB_LAB_LANG` set it for
batch runs. The progress bar is a single `\r`-redrawn line with a UTF-8
gradient bar (`#-` with `--ascii`), the measured rate and ETA; when stdout
is not a TTY it prints throttled `[ 40%] label` markers at 10% intervals
and never duplicates the final 100%.

## Performance guide

Back-of-envelope for the default quick suite (TG N=32, 400 steps):

* own FFT (vectorised): ≈ 60–90 s total on a laptop CPU;
* `--fft numpy`: ≈ 25–40 s (the transforms dominate);
* N=16 selftest ladder: ≈ 40 s with the in-house FFT.

Memory: N=32 needs ≈ 3 GB, N=64 ≈ 24 GB (the config probes RAM and caps
`max_n` at startup — the banner prints the cap). For flows: N=64 2-D runs
are seconds; hard-mode N=128 with 2400 steps is minutes.

## Using it as a library

Every block is importable:

```python
import sys; sys.argv = ['nsb_lab.py']
import importlib.util
spec = importlib.util.spec_from_file_location('nsb', 'python/nsb_lab.py')
nsb = importlib.util.module_from_spec(spec); spec.loader.exec_module(nsb)

import numpy as np
s = nsb.NSE3D(32, nu=0.02)
wk = nsb.Work3D(32) if hasattr(nsb, 'Work3D') else None
uhat = nsb.prepare_state3(nsb.ic_taylor_green(32), s)
res  = nsb.run_decay_3d(s, uhat, dt=0.005, t_horizon=0.5, label='lib')
print(res['ts'].sup_omega[-1])
spec_tail = nsb.tail_diagnostics3(s, res['uhat'])
print('K41 slope:', spec_tail['k41_slope'], 'R²:', spec_tail['k41_r2'])
```

(the exact helper names are the public functions documented in the module
docstring; `Config` fields control language/seed/output before calls).
The module never prints unless you call the `exp_*`/`flow_*` front-ends,
so the numerics layer is script-friendly.

## Running on Termux

`pkg install python numpy` (numpy comes from the Termux repo as a compiled
wheel — no compilation needed on the phone). Everything else is stdlib.
The quick suite runs comfortably on a modern phone in a few minutes; use
`--ascii` and `termux-wake-lock` for long hard-mode runs. The animated GIF
outputs open directly in the gallery.

## Troubleshooting

* **`ModuleNotFoundError: numpy`** — `pip install numpy`.
* **MemoryError at startup** — the RAM probe chose `max_n` too high
  (containers often report host RAM); pass `--n 16`/`--n 32` explicitly.
* **selftest RK4 order off by > 1.5** — almost always a modified butterfly
  or a mask applied at the wrong RK4 stage; diff your `step_rk4_3d` against
  this file's.
* **GIF rejected by a viewer** — check that the LZW stream is sub-blocked
  (≤255-byte chunks with length prefixes); see `write_gif` and the porting
  notes in `../docs/PORTING.md` §4.
* **PDF opens blank in some viewers** — the writer is minimal but valid;
  if your viewer chokes on raw (uncompressed) image streams, tell the lab
  via an issue and use the MD report meanwhile.
