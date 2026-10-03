# NSB Web Lab — the browser edition

**`index.html`** — the entire Navier–Stokes b-Laboratory as a single
self-contained HTML file (~1 270 lines): a Web-Worker pseudospectral
solver, a viridis canvas, live E/Ω charts, the **one-line HTML progress
bar**, PNG/CSV/JSON export, two tabs (Laboratory / About), and **six UI
languages** (Russian, English, Spanish, German, French, Chinese) with
browser auto-detection. No build step, no network, no frameworks — open
the file and the turbulence starts.

* **Runtime**: any modern browser (Chrome/Edge/Firefox/Safari ≥ 2021)
* **Dependencies**: none — no CDN, no fonts, no icon packs
* **Run**: double-click `index.html`, or
  `python3 -m http.server -d webapp 8080` → `http://localhost:8080`

---

## Table of contents

1. [What runs when you open the page](#what-runs)
2. [The two experiment modes](#the-two-experiment-modes)
3. [The Web Worker and the message protocol](#the-web-worker)
4. [The shared solver core in JavaScript](#the-shared-solver-core)
5. [The one-line progress bar (HTML edition)](#the-one-line-progress-bar)
6. [Six languages, auto-detected](#six-languages)
7. [Exports: PNG, CSV, JSON](#exports)
8. [The About tab](#the-about-tab)
9. [Physics fidelity and documented deviations](#physics-fidelity)
10. [Performance notes](#performance-notes)
11. [Hosting on GitHub Pages](#hosting)
12. [Troubleshooting](#troubleshooting)

## What runs

On load the page detects the browser language (falling back to English),
applies all `data-i18n` strings, and immediately starts the default
experiment: **2-D β-plane turbulence** on a 64² grid with ν = 1e-4 m²/s
and β = 1.6e-11 1/(m·s) — a Bickley jet with a weak perturbation
integrating live on your screen. The vorticity field ω(x, y) renders
through the shared 17-stop viridis table; the stat cards show model
time, energy E, enstrophy Ω and the step count; the chart below plots
the E (blue) and Ω (yellow) histories.

Nothing leaves the page: no analytics, no fonts, no requests. The
"About" tab states it and means it.

## The two experiment modes

**2-D β-plane turbulence (real-time).** The barotropic vorticity
equation `∂ω/∂t = −J(ψ,ω) − βv + ν∇²ω` integrated pseudospectrally:
FFT-based derivatives, 2/3 de-aliasing, RK4 with a CFL-aware timestep
`dt = min(0.4·dx/umax, 0.05)`. The sliders control the grid N (32…128),
the viscosity ν (1e-6…1e-2 m²/s), the β-plane parameter and the speed
(steps per animation frame). This mode runs *endlessly* — it is a
living painting of jet meandering and vortex shedding; the progress bar
shows the frame phase.

**3-D Taylor–Green mini-run.** The compact 3-D solver (N=32 on the
torus, ν = 0.02, 400 RK4 steps) — the same Leray-projected,
de-aliased core as the compiled editions — showing the mid-z |ω(x,y)|
slice: the classical four-vortex lattice decaying into filaments.
This mode runs a *fixed program* (400 steps) with a real progress bar
and ETA; the E/Ω chart shows the physically correct decay/growth pair.
It is the browser-scale version of the cross-language handshake
experiment.

## The Web Worker

The solver lives in a **Web Worker** created from a `Blob` URL — the
entire FFT + solver source is a template string inside the page, so the
file stays self-contained. The protocol:

```text
main → worker:  { cmd: 'beta2d-init',  n, nu, beta, lbox }
                { cmd: 'beta2d-steps', count }
                { cmd: 'tg3d-init',    n, dt }
                { cmd: 'tg3d-steps',   count }
worker → main:  { type: 'frame', mode, n, t, step,
                  w: ArrayBuffer (transferred),
                  E, Z, seriesT, seriesE, seriesZ [, sup] }
```

Frames are transferred (zero-copy) `ArrayBuffer`s of the physical
vorticity field; the main thread maps them through viridis into an
`ImageData` and draws. Because the solver runs off the main thread the
UI stays at 60 fps even during the 3-D run — the whole point of the
Worker design.

## The shared solver core

The worker carries the same algorithms as every edition, in typed
arrays:

* `makePlan/fft1d/fft2d/fft3d` — radix-2 DIT with bit-reversal and
  cached twiddles over `Float64Array` re/im pairs; the 2-D and 3-D
  transforms are in-place with gather/scatter for the strided axes;
* `b2Init/b2Rhs/b2Step/b2Diag` — the β-plane operator with physical
  wavenumbers, Parseval diagnostics, and the CFL-aware step;
* `g3Init/g3Rhs/g3Step/g3Diag` — the 3-D Taylor–Green core with
  spectral IC construction, Leray projection at every RK4 sub-stage,
  the 2/3 mask and the mid-z |ω| slice extraction;
* the guard rail: `makePlan` throws on non-power-of-two sizes (the
  first draft silently corrupted 48³ transforms — see
  `../docs/PORTING.md` §4).

## The one-line progress bar

The user-requested one-line bar, HTML edition: a single non-wrapping
line with a CSS gradient fill bar, the percentage, the label and the
ETA —

```html
<span id="progLabel">running</span>
<span class="pbar"><i id="progFill" style="width:64%"></i></span>
<span id="progPct">64%</span><span id="progEta">ETA 0:20</span>
```

— identical information content to the CLI bars (`▸ label ▕bar▏ 64% ·
ETA 0:20`), updated by the same fraction logic: the 3-D mode maps
`step/400`, the 2-D mode shows the frame phase, the ETA comes from the
measured rate against the known 400-step program.

## Six languages

The `I18N` object carries complete ru/en/es/de/fr/zh dictionaries —
every label, caption, toast, stat card, chart note, and the full About
page (≈45 keys per language). On first visit the page reads
`navigator.language` and picks a supported language; the header select
switches instantly (all `data-i18n` elements re-render, the canvas
captions switch with the experiment mode); `localStorage('nsb_lang')`
persists the choice. Adding a language is one object + one `<option>`
(see `../docs/I18N.md`).

## Exports

* **PNG snapshot** — `canvas.toDataURL('image/png')` of the current
  vorticity frame, downloaded directly.
* **CSV series** — the full sampled history (`t, energy, enstrophy[,
  sup_omega]`) as a Blob download, ready for notebooks.
* **JSON state** — version, mode, grid, model time, step, the final
  diagnostics and the complete series; the same schema the CLI editions
  write to `data/session_*.json`, so the CI physics check can consume a
  browser run's JSON verbatim.

## The About tab

A fully localised research write-up: what the b-correction hypothesis
claims, what the lab's five checks actually verify, the β-plane
equation rendered in the page, the BKM/K41 bullet points, the
eight-edition port table (with this page as the Web row), copy-paste
quick-start commands for every CLI edition (including the Termux flow),
and the scope-note paragraph explaining what a verdict is — *a
certificate of internal consistency, evidence not theorem*.

## Physics fidelity

The 2-D mode is the same operator as the CLI flow runner (Bickley jet
IC, β-plane RHS, 2/3 rule, RK4). The 3-D mode reproduces the
Taylor–Green physics qualitatively by design: the four-vortex lattice,
enstrophy growth to the peak, monotone energy decay under ν = 0.02 —
the same shapes the compiled editions print as CSV. **Documented
deviations** (also in `../docs/PORTING.md` §3): the 3-D web solver
fixes N=32 and T=2.0 for browser responsiveness, and the 2-D demo is
endless rather than horizon-terminated. The numeric handshake
(`sup|ω| = 1.7795`) is a *compiled-edition* number; the web edition's
role is interactive demonstration, and its About tab says so.

## Performance notes

The 2-D 64² solver runs ≈ 2–6 ms per RK4 step in the worker (V8 JIT) —
the default 4 steps/frame hold 60 fps comfortably. The 3-D N=32 run
costs ≈ 12 ms/step (≈ 5 s for the 400-step program) — the progress bar
makes the wait legible. Grid slider up to 128² stays real-time on
desktop; on phones 64² is the sweet spot. Memory: three complex N³
field triples ≈ 50 MB at N=64 — fine everywhere, including Termux's
Chromium-based browsers.

## Hosting

The file is self-contained: push the repo to GitHub, enable Pages on
the repo root (or `/webapp`), and the lab is a URL. No build step, no
service worker, no CSP gymnastics — the Worker is inline. For Termux
local use, `python3 -m http.server -d webapp 8080` and open
`localhost:8080` in the phone browser.

## Troubleshooting

* **The 3-D run stays at 0%** — you are on an old build of the file
  where the grid slider passed 48 to a power-of-two FFT; the guard now
  throws in the worker. Update the file (or the slider value).
* **No turbulence visible** — the jet needs a few hundred steps to
  meander; raise the speed slider, lower ν, or press Reset to reseed.
* **Language didn't stick** — `localStorage` may be disabled; the
  select still works for the session.
* **Worker errors are silent** — by design errors inside workers don't
  reach the page console; open `browser://` devtools and check the
  worker's own console, or look for the frame counter stalling.
