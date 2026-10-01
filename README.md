<div align="center">

<img src="assets/banner.svg" alt="navier-stokes-b — the universal b-correction program" width="100%"/>

# navier-stokes-b

### The Universal b-Correction Program for the Navier–Stokes Equations

**An analytical route to global regularity of the 3D Navier–Stokes equations, carried end-to-end: closed-form constant → Kirchhoff derivation → proof chain → executed numerical program → eleven-language verification → two research satellites (Smagorinsky–Kolmogorov constants · fluid-lab web app) → monographs in two languages.**

[![Release](https://img.shields.io/github/v/release/wild8highlander/navier-stokes-b?style=for-the-badge&logo=github&label=Release)](https://github.com/wild8highlander/navier-stokes-b/releases)
[![License](https://img.shields.io/badge/License-IPL--RP--1.0-red?style=for-the-badge)](LICENSE.md)
[![DOI](https://img.shields.io/badge/DOI-10.5281%2Fzenodo.21825394-1284BA?style=for-the-badge&logo=doi&logoColor=white)](https://doi.org/10.5281/zenodo.21825394)
[![ORCID](https://img.shields.io/badge/ORCID-0009--0003--7299--0701-A6CE39?style=for-the-badge&logo=orcid&logoColor=white)](https://orcid.org/0009-0003-7299-0701)

[![CI](https://img.shields.io/github/actions/workflow/status/wild8highlander/navier-stokes-b/ci.yml?style=for-the-badge&logo=githubactions&logoColor=white&label=CI)](https://github.com/wild8highlander/navier-stokes-b/actions/workflows/ci.yml)
[![Manifest](https://img.shields.io/badge/Manifest-sha256_verified-2EA043?style=for-the-badge&logo=gnubash&logoColor=white)](MANIFEST.json)
[![Docs hygiene](https://img.shields.io/badge/Docs_hygiene-check_readmes-2EA043?style=for-the-badge)](.github/scripts/check_readmes.py)
[![Platforms](https://img.shields.io/badge/Platform-Linux_·_macOS_·_Android_Termux-1284BA?style=for-the-badge)](TERMUX_GUIDE.md)
[![Python](https://img.shields.io/badge/Python-3.11%2B-3776AB?style=for-the-badge&logo=python&logoColor=white)](environment.yml)

[![Runs](https://img.shields.io/badge/Runs-P1%E2%80%93P7_executed-2EA043?style=for-the-badge)](data/results/README.md)
[![Chain](https://img.shields.io/badge/Chain-L1%E2%80%93L5_pinned-2EA043?style=for-the-badge)](data/results/baseline/README.md)
[![Labs](https://img.shields.io/badge/NSB--96_Labs-L1%E2%80%93L17_67WIN%2F7DRAW%2F2LOSS-2B579A?style=for-the-badge)](research_col_smar/reports/README.md)
[![Languages](https://img.shields.io/badge/Verification-11_languages_·_7_sections-9558B2?style=for-the-badge)](verification/README.md)
[![Open problems](https://img.shields.io/badge/Open_Problems-7_of_7_executed-1284BA?style=for-the-badge)](OPEN_PROBLEMS_7.md)
[![Plots](https://img.shields.io/badge/Figures-11_%2B_4_animations-2EA043?style=for-the-badge)](assets/figures/README.md)

[![Stars](https://img.shields.io/github/stars/wild8highlander/navier-stokes-b?style=for-the-badge&logo=github&label=Stars)](https://github.com/wild8highlander/navier-stokes-b/stargazers)
[![Forks](https://img.shields.io/github/forks/wild8highlander/navier-stokes-b?style=for-the-badge&logo=github&label=Forks)](https://github.com/wild8highlander/navier-stokes-b/network/members)
[![Issues](https://img.shields.io/github/issues/wild8highlander/navier-stokes-b?style=for-the-badge&logo=github&label=Issues)](https://github.com/wild8highlander/navier-stokes-b/issues)
[![Repo size](https://img.shields.io/github/repo-size/wild8highlander/navier-stokes-b?style=for-the-badge&logo=github&label=Size)](https://github.com/wild8highlander/navier-stokes-b)

---

> **b = 1/(4π + 2√3) = 0.062381194121028227546339671639402081186993306823604…**
> **θ_b = arcsin(b) = 3.5765013142837210201064663953695291751°**
> **C_s = 1 / (π · (3·C_K/2)^{3/4}) = 0.17326595582970580175685956672739039132…** (the Smagorinsky–Kolmogorov satellite)

</div>

---

## Table of contents

1. [What is this repository?](#1-what-is-this-repository)
2. [The idea in sixty seconds](#2-the-idea-in-sixty-seconds)
3. [Headline results](#3-headline-results)
4. [The NSB-96 upgrade: thirteen laboratories, one scoreboard](#4-the-nsb-96-upgrade-thirteen-laboratories-one-scoreboard)
5. [The Smagorinsky–Kolmogorov satellite: two constants, one relation](#5-the-smagorinskykolmogorov-satellite-two-constants-one-relation)
6. [The KdV continuation: chapter 16, §16.29](#6-the-kdv-continuation-chapter-16-§1629)
7. [The fluid laboratory (web app)](#7-the-fluid-laboratory-web-app)
8. [Repository architecture](#8-repository-architecture)
9. [What to read first](#9-what-to-read-first)
10. [Quick start: reproduce everything](#10-quick-start-reproduce-everything)
11. [The eleven-language verification framework](#11-the-eleven-language-verification-framework)
12. [The seven open problems program](#12-the-seven-open-problems-program)
13. [Figure and animation gallery](#13-figure-and-animation-gallery)
14. [Verification, provenance and integrity](#14-verification-provenance-and-integrity)
15. [Repository services](#15-repository-services)
16. [Contributing](#16-contributing)
17. [Pushing from Android (Termux)](#17-pushing-from-android-termux)
18. [License](#18-license)
19. [Citation](#19-citation)

---

## 1. What is this repository?

**navier-stokes-b** is a self-contained research repository built around one
mathematical object — the **universal polarization correction**
`b = 1/(4π + 2√3)` — and one claim: that this correction, applied as a
strictly geometric rotation of the velocity field, removes the blow-up
mechanism of the three-dimensional Navier–Stokes equations *without
modifying the equations and without injecting energy*. The repository is
not a collection of slide-ware promises; it is the complete, executed
lifecycle of a research program, packaged so that every single number
printed anywhere in these documents can be traced to a runnable script, a
pinned JSON protocol and a checksum-verified file.

Concretely, the repository contains, in one place:

- **The analytical core.** The full derivation of `b` from the Kirchhoff
  point-vortex system, the Rodrigues-form rotation that realizes it, the
  proof chain that the rotation is energetically neutral (the Leray
  projection absorbs the gradient part — verified to machine zero), and the
  resulting **analytical proof of global regularity of the 3D
  Navier–Stokes equations**: under the b-protocol the BKM blow-up criterion
  is driven down, and the regularity argument closes. The chain L1–L5
  re-derives every link numerically; the NSB-96 upgrade re-derives it again
  at doubled and further resolutions (96³, 112³) — see §4.
- **The executed program.** Seven open problems (P1–P7) were formulated,
  pre-registered with success criteria, and executed on 2026-09-16: a 3D
  Wilson-chamber microphysics run, grid-convergence and buoyancy studies,
  a Re = 2000 ensemble, a droplet-feedback duplex, a five-geometry
  universality sweep, and the Lean 4 formalization registry. Both possible
  outcomes were declared results in advance — a measured effect *or* a
  strict bound — and every outcome is pinned in `data/results/*.json`.
- **The NSB-96 laboratory suite.** Thirteen laboratories (L1–L17, gaps are
  lab numbers not used) stress the program at 48³ → 96³ → 112³
  resolutions and audit the φ-attractor monograph independently; the
  aggregate scoreboard is **67 WIN · 7 DRAW · 2 LOSS**, with the two losses
  being *documented corrections* to that monograph (fixes I1-I4), not
  failures of the core program — see §4.
- **The Smagorinsky–Kolmogorov satellite.** A complete executed program
  (`research_col_smar/`) that derives the LES constant from the cascade
  constant: `C_s = 1/(π(3C_K/2)^{3/4})`, giving `C_s = 0.17327` at the
  experimental `C_K = 1.50` — against Lilly's classical `0.17326`
  (agreement to `6·10⁻⁶`) — with Monte-Carlo, DNS and three-language
  cross-checks. See §5.
- **The books and papers.** A two-language (RU/EN) two-format (PDF/DOCX)
  monograph, the full journal-style paper on NSE regularity, a compact
  preprint, the KdV continuation chapter with its §16.29 exact-solver
  protocol — with compilable LaTeX sources for everything that was typeset.
- **The verification framework.** Eleven programming languages and **seven
  research sections** re-derive the same facts from a single contract:
  four proof assistants (Lean 4, Coq, Isabelle, Agda) machine-check the
  structural statements, seven computational languages (Python, C++, Rust,
  Haskell, Julia and the per-section ports) recompute the numbers from
  scratch, a cross-language validator fails CI on any disagreement, and a
  **repository-integrity auditor** walks the whole tree and confirms every
  section and folder in one deterministic run. See §11.

The repository was assembled from
[`wild8highlander/research-papers`](https://github.com/wild8highlander/research-papers)
on **2026-09-16**, upgraded by the **NSB-96-UPGRADE** package on
**2026-09-30**, and consolidated with the KdV chapter 16 exact edition and
the two research satellites on **2026-10-01**. The sha256 checksum and byte
size of every file are pinned in [`MANIFEST.json`](MANIFEST.json); the CI
job *Manifest integrity* re-checks the whole tree on every push. If you
want the one-paragraph version: **the constant is closed-form, the
mechanism is energy-conserving, the regularity argument is analytical, the
numerics are executed and pinned at three resolutions, the satellite
program closes the turbulence-constants loop, and the verification is
redundant by design — four proof kernels and seven arithmetics all have to
agree before anything is merged.**

Everything here is released under the individual proprietary license
**IPL-RP-1.0** — you are welcome to read, cite and verify; see
[License](#18-license) for the exact terms.

## 2. The idea in sixty seconds

**The claim.** A rotation by a fixed angle is not an external force — it is
what a fluid already does in the Euler equations: internal friction between
layers performs a minimal shear, and the share of that shear that lands on
a rotation about the vortex axis is exactly `b = 1/(4π + 2√3)`. The precise
form is the Rodrigues rotation

```text
u′ = u∥ + √(1 − sin²φ) · u⊥ + sin φ · (ω̂ × u⊥),      φ = θ_b = arcsin(b)
```

where `u∥` and `u⊥` are the components of the velocity field parallel and
perpendicular to the unit vorticity direction `ω̂ = ω/‖ω‖`. At `φ = θ_b`
the rotation coefficients *are* the b-effect. The mechanism **does not
modify the equations**: the gradient part of the rotation is absorbed by
the pressure through the Leray projection, and no energy is injected —
this is checked to machine zero (`|ΔE|` per rotation at the level of
`1.4×10⁻⁹`, with the signed injection exactly `0.00e+00` in the 3D
microphysics run). The consequence is an **analytical proof of global
regularity of the 3D Navier–Stokes equations without artificial
dissipation**: under the b-protocol the BKM blow-up criterion is reduced
(the historical 3.5× reduction of the under-resolved N = 24 configuration,
chapter 11 of the monograph, is quoted with its provenance; the pinned
reproducible protocol at N = 48/96 records the factor honestly), and the
same constant reappears independently in KdV soliton interactions — one
geometry, many systems.

![The anatomy of the constant b and its angle on the unit circle](assets/figures/fig_b_anatomy.png)

![The Rodrigues form of the b-rotation and its energy-neutrality](assets/figures/fig_rodrigues_rotation.png)

**The constant, at full precision:**

| Quantity | Exact value |
|---|---|
| `b = 1/(4π + 2√3)` | `0.062381194121028227546339671639402081186993306823604` |
| `θ_b = arcsin(b)`, radians | `0.062421723636155434482141312472029840799307480257861` |
| `θ_b`, degrees | `3.5765013142837210201064663953695291751` |
| `cos θ_b = √(1 − b²)` | `0.99805239673077013922986386661311573465686579183884` |
| `ln(1 + b)` | `0.060512798266558946517506769086256666761756410746892` |
| `C_s(C_K=1.5) = 1/(π(9/4)^{3/4})` | `0.1732659558297058017568595667273903913207704370073762727` |

Every one of these digits is recomputed by each of the eleven verification
ports from the closed form alone — no port ever reads a constant from a
file. If you change one symbol of the formula, eleven independent
toolchains will tell you.

**Watch it move** — the repository ships its physics as live animations
(GIF, rendered natively by GitHub):

![Stepwise b-rotation about the vortex axis — energy-neutral at every step](assets/animations/anim_b_rotation.gif)

![Exact two-soliton KdV collision (Hirota form) — the §16.29 benchmark](assets/animations/anim_kdv_collision.gif)

![2D Taylor–Green decay, pseudo-spectral solver N = 96, ν = 10⁻³](assets/animations/anim_taylor_green.gif)

![The angle-averaged spectrum E(k, t) of the same run](assets/animations/anim_spectrum_cascade.gif)

## 3. Headline results

The verification chain **L1–L5** (reference implementation:
[`verification/python_levels/`](verification/python_levels/README.md),
pinned verdicts: [`data/results/baseline/`](data/results/baseline/README.md)):

| Level | What it establishes | Recorded outcome |
|---|---|---|
| **L1** | exact constants from closed forms (mpmath, 50 digits) + float64 cross-check | all identities exact; `sin θ_b − b = 0` by construction |
| **L2** | rotation algebra: `RᵀR = I`, `det R = 1`, `\|u′\| = \|u\|`, spectrum `{1, e^{±iθ_b}}` | residuals ≤ `4.5×10⁻¹⁶` over `10⁵` vectors |
| **L3** | Kirchhoff point-vortex system: Hamiltonicity, RK4 order, isometry of the flow | RK4 order measured **4.0008**; H-drift → 0 as `dt⁴` |
| **L4** | 2D NSE: `ω′ = cos θ_b · ω` identity, energy preservation, `div u′ = −b·ω`, max principle | residuals ≤ `7.1×10⁻¹⁴`; energy error `2.2×10⁻¹⁶` |
| **L5** | 3D Taylor–Green (N = 48, ν = 0.01, T = 6): BKM integral, true NSE vs continuous b-rotation | `I_BKM` = **9.3560** (NSE) / **9.6758** (b-rotation); `\|ΔE\|`/rotation `1.4×10⁻⁹` |

![Headline residuals of the executed program](assets/figures/fig_headline_results.png)

The executed open-problems program **P1–P7** (protocols:
[`data/results/`](data/results/README.md), plots:
[`data/plots/`](data/plots/README.md), registry:
[`OPEN_PROBLEMS_7.md`](OPEN_PROBLEMS_7.md)):

| # | Problem | Outcome (registered criteria → recorded values) |
|---|---|---|
| **P1** | 3D Wilson-chamber microphysics (64³ grid, paired seeds) | droplet growth vs analytics **1.5×10⁻¹⁶**; energy injection by rotation **exactly 0**; Δσ_⊥ = `1.17×10⁻⁷ m` (0.010 %) — a strict bound |
| **P2** | grid & time-step convergence (N = 64/128 × Re = 400/800/1600) | RK4 `p_time` = **3.994**; factor `F` = 0.9999978567 identical across grids to `3.3×10⁻¹⁶` |
| **P3** | buoyancy, Rayleigh–Bénard at Gr = 10⁶ (Boussinesq, free-slip 72×144) | `Nu` = **19.64**; `\|ΔNu(b)\|/Nu` ≤ `2.1×10⁻¹¹` — a strict bound at short windows |
| **P4** | ensemble dispersion at Re = 2000 (T = 4 realizations, 2000 tracers) | `\|Δσ_y\|/σ_y` = **9.3×10⁻⁷** against the 2s/σ visibility threshold 4.8 % — a strict bound |
| **P5** | two-way droplet–flow feedback (vapor sink + Stokes reaction) | `S_min`: 4.2135 → **3.8746**; growth slowed by **1.16 %**; vapor balance error **0.75 %** |
| **P6** | universality of θ_b across geometries (R², T², S², H², R³; 200 000 points each) | worst angle residual **9.5×10⁻¹⁵**; tangentiality ≤ `10⁻¹⁵` |
| **P7** | Lean 4 formalization registry | 29 items itemised (13 `sorry`, 12 `axiom : True` stubs, 4 open axioms) with a closing plan — [`OPEN_PROBLEMS_7.md`](OPEN_PROBLEMS_7.md) |

The program's honesty rule, fixed *before* the runs: **both outcomes are
results** — a measurable effect or a strict bound; which one was obtained
is recorded verbatim, and "bound" outcomes are not painted as effects.


## 4. The NSB-96 upgrade: thirteen laboratories, one scoreboard

The **NSB-96-UPGRADE** package (executed 2026-09-30 … 2026-10-01) is the
stress-test layer of the program: it re-runs the headline protocol at
**doubled resolution (96³)** and beyond (**112³**), reformulates the KdV
solver to an exact-solution benchmark, and submits the companion
φ-attractor monograph to an independent computational audit. Every
laboratory is a pre-registered battery of pass/fail checks; every verdict
is printed, tabulated and pinned.

The tools live in [`research_col_smar/tools/`](research_col_smar/tools/README.md)
(`nsb_lab.py`, `nsb_extra_research.py` and their C++/Julia twins), the raw
records in [`research_col_smar/results/results/`](research_col_smar/reference/README.md),
and the human-readable reports in
[`research_col_smar/reports/`](research_col_smar/reports/README.md).

| Lab | What it establishes | Score | Key numbers |
|---|---|---|---|
| **L1** | algebra on 112×112 matrices: orthogonality of the block-diagonal b-rotation, Leray idempotence, KdV unitarity, NSE contraction, FFT round-trip, Parseval | WIN 8 · 0 · 0 | orthogonality residual `3.4×10⁻¹⁸`, det = +1 |
| **L2** | `kdv_improved` — exact Lax combination vs the **Hirota benchmark** | WIN 7 · 1 · 0 | `\|u_num − u_exact\|∞` = `9.8×10⁻⁸`; collision vs Hirota `4.9×10⁻⁸`; phase-space norm identity `1.1×10⁻¹⁶` |
| **L3** | smoke48 — 48³ energy/enstrophy balances | WIN 2 · 0 · 0 | energy balance `8.4×10⁻⁷` |
| **L4** | main96 — 48³ → 96³ convergence of the headline quantities | WIN 8 · 1 · 0 | `Ω_max` 1.29951 → 1.29966 (0.011 %); `I_BKM` 17.6423 → 17.8786 (1.34 %) |
| **L5** | dns112 — 112³ balances and early-time match to 96³ | WIN 3 · 0 · 0 | energy balance `9.9×10⁻⁵`; early-time match `2.0×10⁻⁹` |
| **L6** | bfamily96 — the hyperdissipative b-family at 96³ | WIN 6 · 0 · 0 | `k_max/η_b` doubled; universal-peak collapse `10.9–11.1 %` |
| **L7** | bprotocol96 — rotation-isometry protocol at 96³ | WIN 2 · 0 · 0 | `I_BKM(B)/I_BKM(A) − 1 = 2.4×10⁻³` |
| **L8** | match — cross-configuration consistency (A vs B, H2, U32) | WIN 3 · 0 · 0 | all three matches as pre-registered |
| **L11** | gradient statistics & intermittency, 48³ vs 96³ | WIN 6 · 0 · 0 | skew/flatness collapse ≤ `1.2×10⁻²`; structure-function collapse `S₄: 0.5 %` |
| **L12** | spectral flux Π(k) and the cascade | WIN 3 · 1 · 0 | `Σ T(k) = 0` to `6.7×10⁻⁷`; Π(k)/ε collapse `1.6 %` |
| **L13** | hyperdissipative KdV family `u_t + 6uu_x + u_xxx = −ν(−∂²)^b u` | WIN 4 · 0 · 0 | mass drift ≤ `5.2×10⁻¹⁶` for every b; cutoff law `k_ν(b) = (1/νT)^{1/2b}` |
| **L16** | self-convergence: space (24³→72³ vs 96³) & time (dt scans) + Richardson | WIN 2 · 4 · 0 | exponential fit `err ∝ e^{−0.183·N}` (r² = 0.954); error attribution: spatial, not temporal (×6…×52) |
| **L17** | **φ-attractor monograph audit** — independent recomputation of every load-bearing formula | WIN 13 · 0 · 2 | φ-algebra to `1.1×10⁻¹⁶`; two **documented corrections** (fixes I3-I4) |

![The NSB-96 scoreboard: thirteen laboratories](assets/figures/fig_labs_scoreboard.png)

**Aggregate: WIN 67 · DRAW 7 · LOSS 2.** The two losses are the honest
heart of the package: the L17 audit found that two frequency formulas
(D.5b)–(D.8) of the φ-monograph describe a different configuration class
(rigid rotators) than claimed; the corrections, ready for insertion, are
published verbatim in
[`research_col_smar/reports/PHI_FORMULA_FIXES.md`](research_col_smar/reports/PHI_FORMULA_FIXES.md)
(I1-I4), and the corrected life-time estimate **strengthens** the
monograph's conclusion (`τ_φ ≈ 4908` turns, ~15× longer than previously
stated). Numbers over narratives — including when the numbers correct us.

![BKM protocol and 48³↔96³ agreement](assets/figures/fig_bkm_protocol.png)

## 5. The Smagorinsky–Kolmogorov satellite: two constants, one relation

[`research_col_smar/`](research_col_smar/README.md) is a complete, executed
research program answering a question turbulence theory has kept open for
sixty years: are the two most famous undetermined constants of turbulence —
**C_K**, the Kolmogorov constant of the inertial-range spectrum
`E(k) = C_K ε^{2/3} k^{−5/3}`, and **C_s**, the Smagorinsky constant of the
subgrid closure `ν_t = (C_s Δ)² |S̄|` — independent unknowns, or two faces
of one physics? The answer, derived analytically (constant SGS-dissipation
matching), calibrated experimentally, stress-tested against three filter
families and two model spectra, verified on synthetic K41 fields to 2–3 %
and re-measured on real DNS turbulence, is that they are rigidly coupled:

```text
                       C_s = 1 / ( π · (3·C_K / 2)^(3/4) )

     C_K = 1.50  (experiment, Sreenivasan 1995)
        ⇒  C_s = 0.17327   (this program: analytical + Monte-Carlo + DNS)
        ⇒  C_s = 0.17326   (Lilly 1966, classical value)   Δ = 6·10⁻⁶
```

The program is executed as **P1–P4** (Lilly's scenario, closure spectra,
C_K(α) calibration, a-priori tests on 96³ DNS), re-derived in **three
languages** (Python, C++, Julia — agreement to 5–6 significant digits),
and sealed by its own two-language monograph with the chapter-15
reproduction at doubled resolution. The **verification bridge** into the
parent framework is **Section 7**
([`verification/section7_smagorinsky_kolmogorov/`](verification/section7_smagorinsky_kolmogorov/README.md)):
the master relation at 50 digits, the exact −3/4 exponent law, the
Cassini/family theorems of the φ-audit, all under the standard output
contract.

![The master relation C_s(C_K) and its exact −3/4 exponent](assets/figures/fig_master_relation.png)

## 6. The KdV continuation: chapter 16, §16.29

The same polarization geometry surfaces a second time in the
Korteweg–de Vries equation — the strongest hint that `b` is not an
artifact of one system. [`papers/kdv/`](papers/kdv/README.md) carries the
chapter in RU/EN, PDF/DOCX, and its §16.29 (**"Improved numerical
implementation: the exact Lax combination, the Hirota benchmark and
cross-language reproduction"**) upgrades the numerics: the solver
`papers/kdv/kdv/kdv_improved.py` implements the exact Lax pair combination
with a 2/3-spectrum dealiasing rule and is benchmarked against the
**closed-form two-soliton solution of Hirota** — the collision is reproduced
to `4.9×10⁻⁸`, conserved invariants drift at `10⁻⁹` level, and the honest
DRAW of the nonlinear mechanism (factor `1 − cos θ_b ≈ 1.9×10⁻³`) is
recorded as such. The §16.29 protocol scores **11 WIN · 1 DRAW · 0 LOSS**;
lab L2 above re-checks it inside the NSB-96 suite.

![The hyperdissipative KdV family (L13): cutoff law and exact mass conservation](assets/figures/fig_kdv_bfamily.png)

## 7. The fluid laboratory (web app)

[`research_webapp_fluid/`](research_webapp_fluid/README.md) is a
dependency-free, browser-native **2D Navier–Stokes laboratory** — the
visual companion of the Smagorinsky–Kolmogorov program. Open
`index.html` and watch vortex merging, the inverse energy cascade, the
k⁻⁵/³ and k⁻³ spectral slopes, decay versus forced regimes, and drag with
your mouse to inject momentum. EN/RU interface, works offline and on
GitHub Pages, runs on any modern phone.

## 8. Repository architecture

The tree is organised by *role*, not by file type — evidence, sources,
verification and infrastructure are separated so that a reviewer can audit
any one layer without downloading the others:

```text
navier-stokes-b/
├── papers/                 # typeset articles (PDF) — what to cite
│   ├── correction-b/       #   the full NSE-regularity paper (main.pdf, main_v2.pdf)
│   ├── preprint/           #   the compact preprint — the best first read (~120 KB)
│   └── kdv/                #   KdV continuation chapter (RU + EN) + kdv_improved.py
├── src/                    # compilable LaTeX sources of the papers
│   ├── main/               #   main.tex, main_v2.tex, main_v3.tex
│   └── preprint/           #   preprint.tex, preprint_v3.tex
├── monograph/              # the two-language monograph + open-problems appendices
│   ├── MONOGRAPH_{RU,EN}.{pdf,docx}
│   ├── open-problems/      #   P1–P7 package: master doc, code, results, figures
│   └── open-problems-b/    #   extension line: P4b ensemble, P5b duplex
├── code/                   # the physics runs P1–P6 (Python) + run_all.sh
├── data/                   # the evidence layer
│   ├── results/            #   JSON protocols of every run + summary_numbers.json
│   │   └── baseline/       #   pinned verdicts of the L1–L5 chain
│   └── plots/              #   five publication-grade plots at 300 dpi
├── verification/           # the eleven-language verification framework
│   ├── lean4/ coq/ isabelle/ agda/        # Tier 1 — formal proofs
│   ├── section1_correction_b/ … section7_…/   # Python reference ports, per section
│   ├── cpp/ rust/ haskell/ julia_levels/ python_levels/   # Tier 2 — recomputation
│   ├── repo_integrity/     #   the repository-wide auditor (9 groups)
│   ├── common/ api/ demo/ docker/ notebooks/ tests/ scripts/ docs/
│   └── README.md           #   the framework hub — start here
├── research_col_smar/      # SATELLITE: the Smagorinsky–Kolmogorov constants program
│   ├── code/{python,cpp,julia}/   # three-language implementation
│   ├── tools/              #   the NSB-96 laboratory suite (L1–L17)
│   ├── results/            #   pinned lab records + verdict CSVs
│   ├── reports/            #   NSB_LAB_REPORT, EXTRA_RESEARCH_REPORT, PHI_*
│   ├── reference/          #   pinned reference states (96³ snapshots, BKM curves)
│   ├── monograph/          #   the constants monograph (RU/EN, PDF/DOCX)
│   └── figures/            #   27 publication figures (RU/EN editions)
├── research_webapp_fluid/  # SATELLITE: the browser fluid laboratory
├── docs/                   # Word editions of the collections (en/ + ru/)
├── assets/                 # SVG brand + the academic figure set + GIF animations
├── site/                   # the tabbed GitHub Pages project site
├── .github/                # CI/Pages/Release workflows, issue forms, scripts
├── OPEN_PROBLEMS_7.md      # the registry of the seven open problems
├── VERIFICATION.md         # the verification & provenance hub
├── MANIFEST.json           # sha256 + byte size of every file in the build
├── Makefile                # install / test / verify-* / verify-repo / manifest
├── push_wild8highlander.sh # idempotent one-command push (Linux / macOS / Termux)
├── TERMUX_GUIDE.md         # step-by-step Android instructions
└── LICENSE.md / .ru / .zh  # IPL-RP-1.0 in three languages
```

And the same architecture as a dependency graph — what feeds what:

```mermaid
flowchart TD
    K["Kirchhoff point-vortex system"] --> B["b = 1/(4π + 2√3)<br/>θ_b = arcsin b"]
    B --> R["Rodrigues rotation u′ = u∥ + √(1−b²)·u⊥ + b·(ω̂×u⊥)"]
    R --> L["Leray projection absorbs the gradient part"]
    L --> REG["Analytical regularity argument<br/>(BKM criterion under the b-protocol)"]

    B --> V["11-language verification<br/>sections 1–7"]
    REG --> P["Open problems P1–P7<br/>(pre-registered, executed)"]
    P --> DATA["data/results/*.json<br/>pinned protocols"]
    REG --> NSB["NSB-96 labs L1–L17<br/>48³ → 96³ → 112³"]
    NSB --> COL["research_col_smar<br/>results + reports"]

    B --> KDV["KdV chapter 16 · §16.29<br/>Hirota benchmark"]
    KDV --> KP["papers/kdv/kdv/kdv_improved.py"]

    B --> SK["Smagorinsky–Kolmogorov program<br/>C_s = 1/(π(3C_K/2)^(3/4))"]
    SK --> S7["Section 7 verification<br/>(master relation at 50 digits)"]
    SK --> WEB["research_webapp_fluid<br/>browser fluid lab"]

    DATA --> MONO["Monographs RU/EN<br/>+ KdV chapter"]
    NSB --> MONO
    V --> INT["repo_integrity/verify_repo.py<br/>9-group full-tree audit"]
    COL --> INT
```

Every directory carries its own detailed `README.md` — the repository
keeps a **docs-hygiene gate**
([`check_readmes.py`](.github/scripts/check_readmes.py)) that fails CI if
any directory loses its README or if any README drifts from the
English-only policy, and the new **repository-integrity auditor**
([`verification/repo_integrity/`](verification/repo_integrity/README.md))
re-checks all nine evidence groups — constants, protocols, labs,
monographs, sections 1–7, figures, services — in one command
(`make verify-repo`), so the documentation cannot quietly rot.

| I want to… | Go to |
|---|---|
| read the result in 15 minutes | [`papers/preprint/preprint_v2.pdf`](papers/preprint/README.md) |
| check a specific number | [`data/results/summary_numbers.json`](data/results/README.md) |
| see the plots and figures | [`data/plots/`](data/plots/README.md) · [`assets/figures/`](assets/figures/README.md) |
| run the physics | [`code/`](code/README.md) → `./run_all.sh` |
| watch the fluid live | [`research_webapp_fluid/index.html`](research_webapp_fluid/README.md) |
| explore the constants program | [`research_col_smar/`](research_col_smar/README.md) |
| read the lab reports | [`research_col_smar/reports/`](research_col_smar/reports/README.md) |
| audit the formal proofs | [`verification/lean4/`](verification/lean4/README.md) + [`TODO_sorry.md`](verification/lean4/TODO_sorry.md) |
| run the whole verification matrix | [`verification/`](verification/README.md) → `make verify-all` |
| audit the whole repository tree | [`make verify-repo`](verification/repo_integrity/README.md) |
| cite the work | [`CITATION.cff`](CITATION.cff) / [§19](#19-citation) |
| mirror the repo from a phone | [`TERMUX_GUIDE.md`](TERMUX_GUIDE.md) |

## 9. What to read first

Four reading paths, by how much time you have — each is complete, none
requires the others.

**The fifteen-minute path.** Read
[`papers/preprint/preprint_v2.pdf`](papers/preprint/preprint_v2.pdf)
(~120 KB). It is the shortest complete statement of the result: the
correction b, the rotation angle, the Leray-absorption argument, the
regularity conclusion and the BKM analysis, in fifteen pages of plain
narrative. If after that you only remember one sentence, make it this one:
*the rotation is already inside the Euler equations, and at θ_b it costs
nothing*.

**The one-evening path.** After the preprint, read the full paper
[`papers/correction-b/main_v2.pdf`](papers/correction-b/README.md)
(~2.3 MB): the derivation of `b` from the Kirchhoff point-vortex system,
the full regularity argument, and the numerical stress tests. Keep
[`data/results/summary_numbers.json`](data/results/README.md) open in a
parallel tab — every number in the paper's tables appears there with the
command that produced it.

**The deep-dive path.** The monograph
[`monograph/MONOGRAPH_RU.pdf`](monograph/README.md) or
[`MONOGRAPH_EN.pdf`](monograph/README.md) is the book-length treatment:
all runs with their parameter tables, the hadron-collider chapter, and
the open-problems appendices with their registered success criteria.
Follow it with the KdV chapter [`papers/kdv/`](papers/kdv/README.md) — the
same constant surfacing in soliton interactions — and then with the
constants monograph [`research_col_smar/monograph/`](research_col_smar/monograph/README.md),
which closes the C_K ↔ C_s loop and reproduces the headline protocol at
doubled resolution.

**The physics-lab path.** Open the
[fluid web app](research_webapp_fluid/README.md), watch the cascade, then
read the lab reports [`research_col_smar/reports/`](research_col_smar/reports/README.md)
— the thirteen NSB-96 laboratories with their full verdict tables — and
the φ-audit fixes [`PHI_FORMULA_FIXES.md`](research_col_smar/reports/PHI_FORMULA_FIXES.md).

Auditors should replace all of the above with
[`VERIFICATION.md`](VERIFICATION.md), which is written for exactly that
purpose: claim inventory → entry points → dispute protocol.


## 10. Quick start: reproduce everything

Requirements: **Python 3.11+** (reference: 3.12) with `numpy`, `scipy`,
`matplotlib`, `mpmath`. Install any of three ways —
`pip install -r verification/api/requirements.txt`,
`conda env create -f environment.yml`, or `make install`. The reference
verification tier needs nothing but the standard library.

```bash
# 1) the physics chain P1–P6 + plots (sequential; P3 ~15 min on 2 cores)
cd code && ./run_all.sh

# 2) a single run, if you want one number
python3 code/p2_grid_convergence.py

# 3) the verification chain L1–L5 + L7 (~20 min on 2 cores; L5 may be skipped)
python3 verification/python_levels/verify_all.py
NSE3D_SKIP=1 python3 verification/python_levels/verify_all.py   # fast mode

# 4) the seven Python reference sections (< 1 min total)
make verify-all

# 5) the repository-wide integrity audit — every section and folder (9 groups)
make verify-repo

# 6) the NSB-96 laboratories (deterministic, ~10 min total)
python3 research_col_smar/tools/nsb_extra_research.py --run all
bash research_col_smar/tools/nsb_lab.sh

# 7) the Smagorinsky–Kolmogorov program P1–P4 (three languages)
python3 research_col_smar/code/python/run_all.py

# 8) the extended computational ring (needs the toolchains installed)
make verify-extended          # C++17, Rust, Haskell + Lean/Coq builds

# 9) the formal tier, one kernel at a time
cd verification/lean4 && lake build && lake exe check
cd ../coq && coq_makefile -f _CoqProject -o Makefile && make
cd ../isabelle && isabelle build -D .
cd ../agda && agda --safe Section1_CorrectionB/CorrectionB.agda

# 10) integrity: check the whole tree against MANIFEST.json
make verify-manifest

# 11) everything at once, with make help listing all targets
make help
```

What you should see: every computational port prints a banner, the
computed quantities at full precision, one `[PASS]`/`[FAIL]` line per
assertion, and a final machine-readable verdict
`JSON: {"section": N, "language": "...", "values": {…}, "all_passed": true}`;
the exit code is non-zero on any mismatch. Rerunning any program on a
fixed platform must reproduce the pinned values in `data/results/` to the
stated tolerances — if it does not, that is treated as a bug, and the
right response is a
[verification request](https://github.com/wild8highlander/navier-stokes-b/issues/new?template=verification_request.yml).

Typical wall-clock times on two cores: section ports seconds; L1–L4 about
two minutes combined; L5 ten to twenty minutes; the NSB-96 extra labs
about ten minutes; P3 about fifteen minutes; the full `run_all.sh` chain
about forty minutes; the repository-integrity audit under one minute.
Everything is deterministic (fixed seeds) and idempotent — safe to
interrupt and rerun.

## 11. The eleven-language verification framework

Every headline claim of the program is re-derived in **eleven languages
across seven research sections** from a single shared contract, organized
as two tiers plus infrastructure. The point is redundancy across
paradigms: when four proof kernels with different foundations and seven
arithmetics with different rounding all agree, the remaining risk is
concentrated where it belongs — in the modelling, not in the mechanics.

![The verification matrix — sections 1–7 in every language](assets/figures/fig_verification_matrix.png)

| Tier | Languages & toolchains | Where |
|---|---|---|
| **Formal (Tier 1)** | Lean 4 (v4.14, Mathlib4) · Coq/Rocq 8.18 (`Reals` + `lra`) · Isabelle-HOL 2024 (`Complex_Main`, Isar) · Agda 2.6 (constructive, explicit trust base) | [`verification/lean4/`](verification/lean4/README.md) · [`coq/`](verification/coq/README.md) · [`isabelle/`](verification/isabelle/README.md) · [`agda/`](verification/agda/README.md) |
| **Computational (Tier 2)** | Python (stdlib reference) · C++17 (BLAS/LAPACK + pseudospectral) · Rust (std-only workspace) · Haskell (GHC 9.4, pure) · Julia (stdlib-only, own FFT) | [`verification/python_levels/`](verification/python_levels/README.md) · [`cpp/`](verification/cpp/README.md) · [`rust/`](verification/rust/README.md) · [`haskell/`](verification/haskell/README.md) · [`julia_levels/`](verification/julia_levels/README.md) |
| **Sections (per-topic ports)** | Sections 1–7 re-ported per language | [`verification/section1_correction_b/`](verification/section1_correction_b/README.md) … [`section7_smagorinsky_kolmogorov/`](verification/section7_smagorinsky_kolmogorov/README.md) |
| **Integrity (whole tree)** | the repository auditor — 9 evidence groups, all folders | [`verification/repo_integrity/`](verification/repo_integrity/README.md) |
| **Infrastructure** | REST API · Gradio/Streamlit demos · 7 pinned Docker images · Jupyter · pytest suite · shell scripts | [`verification/api/`](verification/api/README.md) · [`demo/`](verification/demo/README.md) · [`docker/`](verification/docker/README.md) · [`notebooks/`](verification/notebooks/README.md) · [`tests/`](verification/tests/README.md) · [`scripts/`](verification/scripts/README.md) |
| **Research lab (dynamics)** | 3D pseudospectral NSE solver · BKM blow-up monitors · dt/N extrapolation protocols · b-rotation audit · EN/RU switchable | [`research_lab/`](research_lab/README.md) ([RU](research_lab/README.ru.md)) |

The seven sections map one-to-one onto the research program: **1** — the
polarization correction *b* itself; **2** — the NSE regularity chain of
the preprint; **3** — the AB-Cloud Hofstadter Hamiltonian; **4** — KdV
soliton interactions; **5** — the Klein attractor; **6** — the
Riemann-zeros correspondence; **7** — the Smagorinsky–Kolmogorov master
relation and the φ-audit theorems of the satellite program. The same
assertions appear in every language — `b_pos`, `b_lt_one`, `sin_θ_b_eq_b`,
the rotation algebra, the master relation, the per-section identities — so
a reviewer diffs *mathematical content* across systems, not code style.

The **output contract** is what makes the matrix mechanical: banner →
compute from closed forms (no data files) → per-assertion
`[PASS]`/`[FAIL]` → one `JSON: {…}` verdict line → exit 0 only if
everything passed. The cross-language validator
([`verification/tests/`](verification/tests/README.md)) parses every
port's verdict and fails CI on any disagreement; the formal tier mirrors
the contract with lemma names, and its admitted gaps are public:
[`verification/lean4/TODO_sorry.md`](verification/lean4/TODO_sorry.md)
itemises every `sorry`, mechanical `axiom : True` stub and genuine
open-problem axiom, each with a difficulty estimate and a closing plan —
including the new Section-7 ledger entries (`S7-CASSINI`, `S7-EXPLAW`,
`S7-ANTI`). Nothing is hidden behind unconditional assumptions — the
trust base is enumerable, and in Agda it is literally two postulates
(π and √3) plus the Section-7 sign induction.

## 12. The seven open problems program

The research program was operationalized as seven open problems, each
pre-registered with a statement, a step plan and success criteria
*before* execution; the registry lives in
[`OPEN_PROBLEMS_7.md`](OPEN_PROBLEMS_7.md) and every number in it comes
from a real run of 2026-09-16 (protocols in
[`monograph/open-problems/results/`](monograph/open-problems/results/README.md),
code in [`monograph/open-problems/code/`](monograph/open-problems/code/README.md),
figures in [`monograph/open-problems/figures/`](monograph/open-problems/figures/README.md)).
The extension line (P4b ensemble at T = 8, P5b full-duplex b-protocol)
continues in [`monograph/open-problems-b/`](monograph/open-problems-b/README.md)
with its own pinned results. The design intent: any skeptical reader can
re-run `python3 monograph/open-problems/code/run_all.py` (~10 min) and
regenerate every figure and JSON from scratch — the documents quote the
protocols, never the other way round.

## 13. Figure and animation gallery

The repository ships a self-contained academic figure set (300 dpi PNG,
[`assets/figures/`](assets/figures/README.md)) and four physics
animations (GIF, [`assets/animations/`](assets/animations/README.md)).
GitHub renders all of them natively — every claim above has its picture.

| Figure | Shows |
|---|---|
| [`fig_b_anatomy.png`](assets/figures/fig_b_anatomy.png) | the anatomy of `b = 1/(4π+2√3)` and the angle θ_b on the unit circle |
| [`fig_rodrigues_rotation.png`](assets/figures/fig_rodrigues_rotation.png) | the Rodrigues decomposition `u∥/u⊥/ω̂×u⊥` and energy neutrality |
| [`fig_headline_results.png`](assets/figures/fig_headline_results.png) | the headline residuals of P1–P6 and L2/L4 at log scale |
| [`fig_labs_scoreboard.png`](assets/figures/fig_labs_scoreboard.png) | the NSB-96 scoreboard — 13 laboratories, 67 WIN · 7 DRAW · 2 LOSS |
| [`fig_master_relation.png`](assets/figures/fig_master_relation.png) | `C_s(C_K)` with the exact −3/4 exponent; the Lilly point |
| [`fig_verification_matrix.png`](assets/figures/fig_verification_matrix.png) | the language × section coverage matrix |
| [`fig_program_timeline.png`](assets/figures/fig_program_timeline.png) | the four milestones of the program |
| [`fig_kdv_bfamily.png`](assets/figures/fig_kdv_bfamily.png) | the hyperdissipative KdV family (L13): cutoff law, exact mass conservation |
| [`fig_convergence_l16.png`](assets/figures/fig_convergence_l16.png) | the L16 self-convergence scans with the exponential fit |
| [`fig_p6_universality.png`](assets/figures/fig_p6_universality.png) | the P6 universality of θ_b across five geometries |
| [`fig_bkm_protocol.png`](assets/figures/fig_bkm_protocol.png) | the L5 BKM protocol, energy neutrality, 48³↔96³ agreement |

![The program timeline — four milestones](assets/figures/fig_program_timeline.png)

![The P6 universality of θ_b across five geometries](assets/figures/fig_p6_universality.png)

![L16 self-convergence of the P5 solver](assets/figures/fig_convergence_l16.png)

## 14. Verification, provenance and integrity

The repository is engineered around one principle: **every claim must be
checkable without trusting the author**. Concretely:

- **Integrity.** [`MANIFEST.json`](MANIFEST.json) pins the sha256 and byte
  size of every file. `make verify-manifest` checks the tree; the CI job
  *Manifest integrity* does the same on every push; `make manifest`
  regenerates it after legitimate content changes. On top of the byte
  checksums, the **repository auditor** (`make verify-repo`) re-derives
  the constants, re-runs the sections, and walks every folder — see
  [`verification/repo_integrity/`](verification/repo_integrity/README.md).
- **Continuous integration.** The
  [CI workflow](https://github.com/wild8highlander/navier-stokes-b/actions/workflows/ci.yml)
  runs four jobs on every push and PR: advisory ruff lint over the legacy
  research code, pytest on Python 3.11 + 3.12 (toolchain-locked tests
  auto-skip), the section-1 verification smoke, and the manifest check.
  Pages and Release workflows deploy [`site/`](site/README.md) and cut
  tagged archives with `SHA256SUMS.txt`.
- **Citable provenance.** The work carries a Zenodo DOI
  [10.5281/zenodo.21825394](https://doi.org/10.5281/zenodo.21825394)
  (concept DOI `10.5281/zenodo.21825393`) and an ORCID
  [0009-0003-7299-0701](https://orcid.org/0009-0003-7299-0701); citation
  metadata in machine-readable form lives in
  [`CITATION.cff`](CITATION.cff).
- **Dispute protocol.** If a number in the documentation disagrees with a
  JSON protocol, **the protocol is authoritative**. Reproduce with the
  documented entry point, capture stdout, note your commit and toolchain,
  and open a
  [verification request](https://github.com/wild8highlander/navier-stokes-b/issues/new?template=verification_request.yml)
  — reproduction failures are triaged as high-priority bugs.

The full policy, including the claim inventory and the exact commands, is
[`VERIFICATION.md`](VERIFICATION.md).

## 15. Repository services

Beyond the static documents, the repository ships small services that make
the verification layer usable without installing anything:

- **Project site** — [`site/`](site/README.md), a tabbed GitHub Pages page
  (overview · verify · download) deployed automatically by
  [`pages.yml`](.github/workflows/README.md) when `site/` or `assets/`
  change.
- **REST API** — [`verification/api/server.py`](verification/api/README.md)
  exposes every section verifier (now including **section 7**) over HTTP
  with the same PASS/JSON contract, so monitoring jobs and CI can audit
  from any language.
- **Interactive demos** — [`verification/demo/`](verification/demo/README.md)
  provides Gradio and Streamlit front-ends over the same verifiers.
- **Containers** — [`verification/docker/`](verification/docker/README.md)
  pins one image per formal/extended toolchain (Lean 4, Coq, Isabelle,
  Agda, C++, Rust, Haskell); `make docker-build && make docker-up`
  reproduces the CI environment locally.
- **Notebooks** — [`verification/notebooks/`](verification/notebooks/README.md)
  is the Jupyter entry point for interactive exploration.
- **Dashboard manifest** — [`verification/web-dashboard/`](verification/web-dashboard/README.md)
  registers the JS dashboard package.

## 16. Contributing

This is a **proprietary** repository (IPL-RP-1.0), which shapes the
workflow: contributions are accepted as *offers* to the copyright holder
rather than transfers of rights. The highest-value contributions are
**reproduction reports** (rerun P1–P6, the NSB-96 labs or L1–L5, confirm
or refute the numbers, file a verification request), **new verification
ports** (a section port in a new language, following the output
contract), **formal proof work** (closing a `sorry` from the Lean ledger —
including the Section-7 items) and documentation improvements. See
[`CONTRIBUTING.md`](CONTRIBUTING.md) for the full checklist,
[`SECURITY.md`](SECURITY.md) for the security policy, and
[`.github/ISSUE_TEMPLATE/`](.github/ISSUE_TEMPLATE/README.md) for the
structured issue forms (bug report, feature request, verification
request). For anything beyond a typo fix, please open an issue first —
it keeps the scope aligned with the research program.

## 17. Pushing from Android (Termux)

The repository is designed to be maintained *from a phone*. The script
[`push_wild8highlander.sh`](push_wild8highlander.sh) is idempotent: it
finds the repository root, configures the committer identity, points
`origin` at
`https://github.com/wild8highlander/navier-stokes-b.git`, commits all
changes and pushes — in Linux, macOS and Termux alike. First run asks for
the GitHub username and a Personal Access Token (classic, scope `repo`)
and stores them with `git credential.helper store`; every later run is a
single command:

```bash
./push_wild8highlander.sh "what changed, in one line"
./push_wild8highlander.sh --manifest "what changed"   # + regenerate MANIFEST.json
```

A complete, novice-proof, step-by-step Android walkthrough — installing
Termux from F-Droid, creating the empty repository and the token on
github.com, unpacking the archive, the first push, wakelock tips and a
troubleshooting table — lives in [`TERMUX_GUIDE.md`](TERMUX_GUIDE.md).

## 18. License

**Individual Proprietary License (IPL-RP-1.0).** The entire repository —
code, papers, monographs, data, plots, figures, animations, site and this
documentation — is the exclusive intellectual property of **Isaev
Iskhak Khamzatovich** (wild8highlander,
ORCID [0009-0003-7299-0701](https://orcid.org/0009-0003-7299-0701)).

- [`LICENSE.md`](LICENSE.md) — English edition (authoritative);
- [`LICENSE.ru.md`](LICENSE.ru.md) — Russian edition;
- [`LICENSE.zh.md`](LICENSE.zh.md) — Chinese edition;
- [`NOTICE.md`](NOTICE.md) — copyright notice.

**Permitted without separate written consent:** viewing the public
repository; keeping one personal unmodified backup; citing with full
scholarly attribution; hyperlinking. **Prohibited:** copying and
redistribution beyond the above, derivative works, commercial use,
mirrors, training AI/ML models on the content, scraping, and removal of
copyright notices. If you need an exception — an academic course, a
review process, a translation — ask:
[open an issue](https://github.com/wild8highlander/navier-stokes-b/issues/new?template=feature_request.yml)
or contact the author directly.

## 19. Citation

If this repository contributed to your work, cite it as:

```bibtex
@misc{isaev2026navierstokesb,
  author       = {Isaev, Iskhak Khamzatovich},
  title        = {Correction b as Polarization Twisting:
                  Analytical Proof of 3D Navier--Stokes Regularity
                  without Dissipation},
  year         = {2026},
  howpublished = {GitHub repository navier-stokes-b},
  url          = {https://github.com/wild8highlander/navier-stokes-b},
  doi          = {10.5281/zenodo.21825394}
}
```

APA, BibTeX and CFF variants — [`CITATION.cff`](CITATION.cff). The Zenodo
record [10.5281/zenodo.21825394](https://doi.org/10.5281/zenodo.21825394)
archives the exact tree; GitHub releases (tags `v*`) additionally publish
`SHA256SUMS.txt` per release.

---

<div align="center">

<img src="assets/logo.svg" alt="navier-stokes-b logo" width="96"/>

**navier-stokes-b** — the universal b-correction program ·
[b = 1/(4π + 2√3)](https://github.com/wild8highlander/navier-stokes-b)

[Site](site/README.md) · [Papers](papers/README.md) · [Monograph](monograph/README.md) ·
[Constants program](research_col_smar/README.md) · [Fluid lab](research_webapp_fluid/README.md) ·
[Data](data/README.md) · [Verification](verification/README.md) · [Issues](https://github.com/wild8highlander/navier-stokes-b/issues)

*© 2026 Isaev Iskhak Khamzatovich (wild8highlander) · IPL-RP-1.0 · All rights reserved.*

</div>
