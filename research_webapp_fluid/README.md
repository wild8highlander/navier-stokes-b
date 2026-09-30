# `research_webapp_fluid/` — Navier–Stokes Fluid Lab (Web Application)

> **Navigation:** [repository root](../README.md) › **`research_webapp_fluid`**

![App](https://img.shields.io/badge/App-standalone_index.html-2EA043?style=for-the-badge)
![Stack](https://img.shields.io/badge/Stack-vanilla_JS_%C2%B7_Canvas_%C2%B7_zero_deps-9558B2?style=for-the-badge)
![i18n](https://img.shields.io/badge/Languages-EN_%C2%B7_RU-1284BA?style=for-the-badge)
![License](https://img.shields.io/badge/License-IPL--RP--1.0-red?style=for-the-badge)

---

An interactive, dependency-free **2D Navier–Stokes laboratory** that runs in
any modern browser — desktop or Android — directly from this directory.
It is the visual companion of the
[`research_col_smar`](../research_col_smar/README.md) Smagorinsky–Kolmogorov
program: everything the monograph describes statistically (vortex merging,
the energy cascade, the spectral slopes, decay versus forcing) can be
watched here live.

**No build step, no server, no dependencies**: open `index.html` and the
simulation starts. The file also works offline and on GitHub Pages.

---

## 1. What it shows

| Panel | Content |
|---|---|
| **Field** | the 2D flow on a 256 × 160 periodic lattice, colored by vorticity ω (diverging blue–dark–gold), speed \|u\|, or schlieren \|∇ω\| |
| **Tracer particles** | 3600 Lagrangian tracers advected by the resolved velocity field |
| **Velocity arrows** | coarse-grained vector field overlay |
| **E(k) spectrum** | the live angle-averaged kinetic-energy spectrum on log–log axes with the two canonical slopes of two-dimensional turbulence — **k⁻⁵ᐟ³** (inverse energy cascade) and **k⁻³** (enstrophy cascade) — plus the *measured* slope in the shaded band k ∈ [6, 20] |
| **Readouts** | time t, kinetic energy E, enstrophy Ω, Reynolds-number proxy Re, FPS |

## 2. The two operating modes

* **Decay · no external force** — the lattice is initialized with
  Taylor–Green vortices plus random eddies and then evolves *freely*:
  energy monotonically decays, like-signed vortices merge, the spectrum
  steepens. This is the "no external force" branch requested for the
  program.
* **Forced · mouse = force** — dragging the cursor injects momentum
  (an external force localized under the pointer). An optional
  deterministic **stirrer** (five alternating vortex cores) and a weak
  Rayleigh drag hold the flow in a statistically stationary state, which
  is the regime where the spectral slopes can be watched lazily for
  minutes. This is the "external force" branch.

Switching between the two modes, resetting and pausing are one click each.

## 3. Controls

| Control | Range | Effect |
|---|---|---|
| View | vorticity / speed / schlieren | display field |
| Vorticity confinement | 0 – 0.4 | the classical confinement term that keeps small vortices crisp |
| Viscosity ν | 10⁻⁵ – 2·10⁻³ | explicit diffusion of velocity; watch the spectrum steepen and the small scales die |
| Simulation speed | 0.2× – 2.5× | sub-stepping per frame |
| Tracers / arrows | toggles | overlays |
| Language | EN / RU | the entire interface |

## 4. Physics and numerics (what is actually solved)

The incompressible 2D Navier–Stokes equations on a periodic square,

```text
∂_t u + (u·∇)u = −∇p + ν∇²u + f,      ∇·u = 0,
```

integrated with the classical operator-splitting scheme of Stam's *Stable
Fluids*:

1. external forces (mouse / stirrer / drag) are accumulated and applied;
2. **semi-Lagrangian advection** (unconditionally stable backtrace with
   bilinear interpolation and periodic wrap);
3. explicit diffusion (Jacobi sweeps of the implicit system);
4. **pressure projection** — a Jacobi solution of the Poisson equation
   ∇²p = ∇·u followed by `u ← u − ∇p` (the divergence-free projection);
5. optional **vorticity confinement** `F = ε (N × ω)`, N = ∇|ω|/|∇|ω||.

The spectrum is computed every few frames by a hand-written **radix-2
2D FFT** of the velocity components on a 128 × 128 periodic window,
followed by shell averaging — the same diagnostic that the monograph's
P4 program performs offline on DNS output.

### A note on 2D versus 3D spectra

Two-dimensional turbulence is *not* three-dimensional K41: the inverse
energy cascade carries `E(k) ~ k⁻⁵ᐟ³` at scales *larger* than the forcing
scale, while the enstrophy cascade gives `E(k) ~ k⁻³` at smaller scales
(Kraichnan 1967, Batchelor 1969). The spectrum panel therefore shows both
reference slopes and the live measured slope, and the interface copy
explains which is which. The three-dimensional Smagorinsky–Kolmogorov
theory of the parent program (`research_col_smar`) is deliberately kept
separate: there the constants are measured on true 3D DNS.

## 5. Running it

* **Locally:** double-click `index.html` (or `python3 -m http.server` in
  this directory and open `http://localhost:8000`).
* **GitHub Pages:** enable Pages for the repository; the app lives at
  `https://wild8highlander.github.io/navier-stokes-b/research_webapp_fluid/`.
* **Android:** any modern mobile browser; the field accepts touch drags
  as force injection (the pointer events are touch-aware).

## 6. Files

| File | Purpose |
|---|---|
| `index.html` | the complete application (HTML + CSS + JS, ~900 lines, zero dependencies) |
| `docs/screenshot_decay.png` | decay mode, vorticity field |
| `docs/screenshot_forced.png` | forced mode with the stirrer active |
| `docs/screenshot_ru.png` | the Russian interface |
| `README.md` | this file |

## 7. Numerical caveats (stated honestly)

* Semi-Lagrangian advection and a 28-sweep Jacobi projection are
  *visual-grade* numerics: they conserve neither energy nor enstrophy to
  spectral accuracy, and the effective resolution is coarser than the
  lattice suggests. The E(k) slopes measured here are therefore
  qualitative companions to — not replacements for — the pinned
  pseudo-spectral DNS numbers of `research_col_smar/results/`.
* At very low viscosity with confinement above ≈ 0.3 the flow can develop
  grid-scale noise; lowering the confinement or raising ν restores it.
* The Reynolds number shown is a proxy `u′/(k_eff ν)` built from the
  measured energy and enstrophy, not a tunnel-verified value.

## 8. License

Part of **navier-stokes-b**, license IPL-RP-1.0
([LICENSE.md](../LICENSE.md)).
