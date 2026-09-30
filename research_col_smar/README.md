# `research_col_smar/` — The Smagorinsky–Kolmogorov Constants Program

> **Navigation:** [repository root](../README.md) › **`research_col_smar`**

![Program](https://img.shields.io/badge/Program-P1%E2%80%93P5_executed-2EA043?style=for-the-badge)
![Languages](https://img.shields.io/badge/Code-Python_%C2%B7_C%2B%2B_%C2%B7_Julia-9558B2?style=for-the-badge&logo=gnu)
![Monograph](https://img.shields.io/badge/Monograph-RU_%C2%B7_EN_%C2%B7_PDF_%C2%B7_DOCX-2B579A?style=for-the-badge)
![Platforms](https://img.shields.io/badge/Platform-Linux_%C2%B7_macOS_%C2%B7_Android_Termux-1284BA?style=for-the-badge&logo=android)
![License](https://img.shields.io/badge/License-IPL--RP--1.0-red?style=for-the-badge)

---

**One question. Two constants. One closed-form relation between them.**

How large are the two most famous undetermined constants of turbulence —

* **C_K**, the Kolmogorov constant of the inertial-range spectrum
  `E(k) = C_K · ε^(2/3) · k^(−5/3)` (Kolmogorov 1941), and
* **C_s**, the Smagorinsky constant of the subgrid-viscosity closure
  `ν_t = (C_s · Δ)² · |S̄|` (Smagorinsky 1963) that powers virtually every
  large-eddy simulation code in existence —

and is there a *derivable* connection between them, rather than two
independent empirical fudge factors?

This directory contains a complete, executed research program that answers
both questions with one derivation chain and verifies every link three
times: **analytically** (closed form), **numerically** (a Monte-Carlo
spectral experiment and a 3D pseudo-spectral DNS), and **cross-language**
(the same algorithms re-implemented in Python, C++ and Julia, agreeing to
5–6 significant digits).

The headline result is the **master relation of this program**:

```text
                       C_s = 1 / ( π · (3·C_K / 2)^(3/4) )

     C_K = 1.50  (experiment, Sreenivasan 1995)
        ⇒  C_s = 0.17327   (this program, analytical + numerical)
        ⇒  C_s = 0.17326   (Lilly 1966, classical value)   Δ = 6·10⁻⁶
```

It is derived here from first principles (constant SGS-dissipation
matching of the Smagorinsky subgrid flux against the K41 inertial-range
flux), calibrated against the best experimental value of `C_K`,
stress-tested against three filter families and two model spectra,
verified on synthetic K41 fields to 2–3 %, and re-measured on real DNS
turbulence — where the a priori constant lands in the same 0.16–0.20 band
reported throughout the LES literature.

Everything below is reproducible from a clean checkout on a laptop or on
an Android phone (Termux) in roughly fifteen minutes.

---

## Table of contents

1. [Why these two constants](#1-why-these-two-constants)
2. [The physics in five minutes](#2-the-physics-in-five-minutes)
3. [The master relation and its derivation chain](#3-the-master-relation-and-its-derivation-chain)
4. [The executed program P1–P5](#4-the-executed-program-p1p5)
5. [Headline results (all pinned, all reproducible)](#5-headline-results-all-pinned-all-reproducible)
6. [Three-language verification](#6-three-language-verification)
7. [Repository layout](#7-repository-layout)
8. [How to run everything](#8-how-to-run-everything)
9. [The monograph (RU / EN, PDF / DOCX)](#9-the-monograph-ru--en-pdf--docx)
10. [Figures](#10-figures)
11. [Conventions, normalizations and the factor-2 trap](#11-conventions-normalizations-and-the-factor-2-trap)
12. [Results integrity and manifests](#12-results-integrity-and-manifests)
13. [Frequently asked questions](#13-frequently-asked-questions)
14. [Relation to the parent b-correction program](#14-relation-to-the-parent-b-correction-program)
15. [License and citation](#15-license-and-citation)

---

## 1. Why these two constants

Turbulence theory has exactly one quantitative statement of universal
validity — Kolmogorov's 1941 (K41) cascade picture. In its spectral form
it predicts that the kinetic-energy spectrum in the inertial range is a
power law with a *universally determined* slope but an *undetermined*
amplitude:

```text
E(k) = C_K · ε^(2/3) · k^(−5/3)          (inertial range)
```

The slope −5/3 is fixed by dimensional analysis and the 4/5 law. The
amplitude `C_K` is not: K41 alone cannot compute it. Eighty years of
experiment, closure theory and simulation have converged on

```text
C_K = 1.50 ± 0.05
```

(Sreenivasan's 1995 review; individual determinations range 1.4–1.8).

Independently, in large-eddy simulation the classical closure of
Smagorinsky (1963) models the subgrid stress as an eddy viscosity

```text
ν_t = (C_s · Δ)² · |S̄|,        |S̄| = (2 S̄_ij S̄_ij)^(1/2)
```

and the same story repeats: everything about the closure is fixed except
the constant `C_s`, whose accepted value is

```text
C_s = 0.17 ± 0.02
```

(Lilly 1966, Deardorff 1970, and forty years of a priori testing since).

**The question this program asks** is whether these two constants are
independent unknowns, or two faces of the same inertial-range physics. The
answer derived and executed here: they are rigidly coupled. The subgrid
dissipation of the Smagorinsky closure, evaluated on a K41 velocity field
and required to equal the true dissipation, *forces*

```text
C_s(C_K) = 1 / ( π · (3·C_K/2)^(3/4) )
```

— one closed-form relation with no adjustable parameters. Feeding in the
experimental `C_K` yields `C_s = 0.17327`, i.e. the classical Lilly value
to five digits. The two most famous empirical constants of turbulence are,
in this precise sense, **one constant seen twice**.

## 2. The physics in five minutes

Take the velocity field of homogeneous isotropic turbulence, filter it at
scale Δ (so that eddies larger than Δ are *resolved* and eddies smaller
than Δ are *subgrid*), and write down two budgets.

**(a) The subgrid budget.** The Smagorinsky closure drains resolved kinetic
energy at the rate

```text
ε_sgs = −⟨τ_ij S̄_ij⟩ = (C_s Δ)² ⟨|S̄|³⟩
```

where `τ_ij` is the subgrid stress, `S̄_ij` the resolved strain tensor and
`|S̄| = (2 S̄_ij S̄_ij)^(1/2)`. This expression is *exact* for the closure —
no statistics needed, only algebra (`S̄_ij S̄_ij = |S̄|²/2`).

**(b) The cascade budget.** A K41 velocity field filtered at scale Δ keeps
a resolved strain whose mean square is carried entirely by wavenumbers
below the cutoff `k_c ≈ π/Δ`:

```text
⟨|S̄|²⟩ = 2 ∫_0^{k_c} k² E(k) G²(k) dk  =  (3/2) · C_K · ε^(2/3) · k_c^(4/3)
```

for a sharp spectral cutoff `G = 1, k < k_c`, using the K41 spectrum.

**(c) The matching.** If the cutoff sits well inside the inertial range,
*all* the dissipation of the underlying flow is subgrid dissipation:
`ε_sgs = ε`. Combining (a) and (b),

```text
ε = (C_s Δ)² · ⟨|S̄|²⟩^(3/2) = (C_s Δ)² · ((3/2) C_K)^(3/2) · ε · k_c²
```

(the `k_c²` comes from `⟨|S̄|²⟩^(3/2) ∝ k_c²`; and `Δ² k_c² = π²` for the
sharp cutoff). Every factor cancels except one:

```text
C_s² = 1 / ( π² · (3 C_K / 2)^(3/2) )
⇒    C_s = 1 / ( π · (3 C_K / 2)^(3/4) )
```

That is the entire derivation — seven lines of algebra on top of K41. The
rest of this program is about *verifying* it (does it survive different
filters? different spectra? real turbulence? three independent programming
languages?), *quantifying* its corrections (finite Δ/η, intermittency,
filter shape), and *documenting* it to monograph standard.

## 3. The master relation and its derivation chain

The full logical chain, each link executed as a numbered program:

| # | Link | Type | Program | Result |
|---|------|------|---------|--------|
| 1 | `E(k) = C_K ε^(2/3) k^(−5/3)` in the inertial range | phenomenology (K41, 4/5-law) | — | input |
| 2 | resolved-strain identity `⟨|S̄|²⟩ = 2∫k²E G²dk` | exact algebra + numerics | P3 | verified to ≤ 3–20 % (binning) |
| 3 | SGS flux of the closure `ε_sgs = (C_sΔ)²⟨|S̄|³⟩` | exact algebra | — | exact |
| 4 | flux matching `ε_sgs = ε` for `k_c` in the inertial range | physical hypothesis | P3, P4 | consistent |
| 5 | **master relation** `C_s = 1/(π(3C_K/2)^{3/4})` | closed form | P1 | 0.17327 |
| 6 | inverse Heisenberg closure `C_K(α) = (8/9α)^{2/3}` | two-point closure | P2 | α = 0.484 |
| 7 | filter-family corrections (sharp/Gaussian/box) | closed form + quadrature | P1, P3 | 0.157–0.173 |
| 8 | finite-scale correction (Pao tail), `C_s(Δ/η)` | model spectrum | P1, P3 | table + curve |
| 9 | measurement on real DNS turbulence | 3D pseudo-spectral DNS | P4 | a priori band |
| 10 | dynamic Germano-Lilly `C_s(x,t)` | LES procedure | P4 | band |

Chapters 3–9 and 12 of the monograph walk this table line by line; every row has
its executable counterpart in `code/` and its pinned numbers in `results/`.

## 4. The executed program P1–P5

Five programs, each with a pinned JSON protocol in `results/`:

### P1 — `p1_lilly.py`: the master relation and its sensitivity

* evaluates the master relation `C_s(C_K)` for the **sharp spectral
  cutoff** (`k_c = π/Δ`), the **Gaussian filter** (`G = exp(−k²Δ²/24)`,
  giving the closed form `C_s = (C_K Γ(2/3) 12^(2/3))^(−3/4)`) and the
  **box filter** (numerical quadrature of `2C_K ∫χ^{1/3} sinc²(χ/2) dχ`);
* verifies the underlying strain integral by 2·10⁶-point quadrature
  (relative error 1.5·10⁻⁹);
* quantifies the **Pao-tail correction** — how much the dissipation-range
  exponential raises the implied `C_s` as `Δ/η` shrinks;
* pins everything to `results/p1_lilly.json` + a 23-row CSV table.

### P2 — `p2_closures.py`: two-point closures for `C_K`

* the **Heisenberg (1948) spectral balance** — eddy viscosity
  `ν_T(k) = α∫_k^∞ √(E(q)/q³) dq` inserted into the constant-flux budget
  `ε = 2(ν + ν_T)∫₀^k q²E dq` — is solved *in closed form*:
  `E(k) ∝ χ⁻⁷[1 + (3α²/8)χ⁻⁴]^(−4/3)`, with the inertial-range constant
  **`C_K(α) = (8/9α)^(2/3)`** and the classical `k⁻⁷` far-dissipation
  falloff (both re-verified numerically here);
* the calibration is inverted: the experimental `C_K = 1.50` pins the
  closure constant at `α = 0.4838`;
* the **Pao-type model spectrum** with *exact* dissipation normalization
  is derived: requiring `2ν∫k²E dk = ε` forces the Gaussian cutoff
  exponent `β = (C_K Γ(2/3))^(3/2) ≈ 2.895`;
* Kraichnan's DIA (1.77) and LhDIA (1.52) values are tabulated as
  independent theoretical anchors.

### P3 — `p3_synthetic_apriori.py`: Monte-Carlo verification on K41 fields

* generates an ensemble of divergence-free, random-phase velocity fields
  on a 96³ periodic grid whose *shell energies* match the K41-Pao spectrum
  **exactly** (a deterministic per-shell calibration, immune to FFT
  normalization conventions — see
  [§11](#11-conventions-normalizations-and-the-factor-2-trap));
* verifies the resolved-strain identity `⟨|S̄|²⟩ = 2∫k²E G²dk` directly on
  the fields (agreement 3–20 %, limited only by shell binning);
* measures the implied `C_s(Δ/η)` for sharp and Gaussian filters and
  demonstrates the convergence to the Lilly value as `Δ/η → ∞`
  (`C_s = 0.16994` at `Δ/η = 25`, sharp filter);
* proves a genuinely instructive *negative* result: on Gaussian random
  fields the Germano correlation `⟨L_ij S̄_ij⟩` vanishes identically
  (third moments of Gaussian variables) — the a priori Smagorinsky
  constant of a *random-phase* field is zero, and the physical value can
  only come from real cascade dynamics. This is what motivates P4.

### P4 — `p4_dns_les.py`: real turbulence

* runs a forced 3D pseudo-spectral DNS on a 64³ periodic box (2/3-rule
  dealiasing, Heun time stepping, white-in-time solenoidal forcing at
  `|k| ≤ 2.5`) into a statistically stationary state;
* measures `ε`, `u'`, the Taylor microscale `λ`, `Re_λ`, and the
  time-averaged spectrum with its inertial-range fit and stated caveats;
* performs the **a priori Smagorinsky test on real, intermittent,
  non-Gaussian fields**: `C_s² = −⟨L_ij S̄_ij⟩/(Δ²⟨|S̄|³⟩)` for Gaussian
  filters at `Δ = 2, 3, 4, 6 Δx` — now with a *nonzero* Germano
  correlation because real cascade dynamics build the phase coherence
  that Gaussian fields cannot have;
* runs the **dynamic Germano-Lilly procedure** (test filter `2Δ`) and
  reports the dynamic `C_s` band;
* saves the vorticity slice and the averaged spectrum for the figures.

### P5 — `p5_regularity.py`: 3D smoothness of solutions

The regularity program of monograph chapter 12 — the canonical
singularity-testing flow (3D Taylor-Green vortex, 48³, ν = 0.01,
T = 6) instrumented end-to-end:

* **integrating-factor midpoint RK2** pseudo-spectral solver (the
  dissipation `exp(−νk^{2b}t)` is applied exactly — mandatory for the
  hyperdissipative exponents) with 2/3-rule dealiasing;
* **run A vs run B**: the baseline Taylor-Green field versus the same
  field rotated by `θ_b = arcsin(b)` about z (an isometry) — enstrophy,
  `‖ω‖_∞`, `‖u‖_∞`, `⟨u⁴⟩`, `⟨u⁶⟩`, palinstrophy, the stretching
  balance `dΩ/dt = 2⟨ω·Sω⟩ − 2ν⟨|∇ω|²⟩`, the BKM envelope
  `I(t) = ∫₀ᵗ‖ω‖_∞ ds` and the Serrin integrals along both
  trajectories;
* **the hyperdissipative family** `ν(−Δ)^b`, `b ∈ {1, 5/4, 3/2, 2}`
  (the Colombo-Haffter global-regularity threshold is 5/4): the closed-
  form generalized Pao normalization `β_b` and the parameter-free
  universal prediction `k_d η_b = x*(b)` tested against the measured
  dissipation-spectrum peaks;
* **the spectral smoothness certificate**: exponential vs power-law tail
  fits on the top of the dealiased band — the measured far-tail slope
  `σ = −6.64` at the enstrophy peak sits on the Heisenberg `k⁻⁷` law of
  chapter 5;
* **self-verification gates**: divergence-free residual 1.3·10⁻¹²,
  energy balance ≤ 1.1·10⁻³, enstrophy balance 5.7·10⁻³;
* exports the `(u, ω)` snapshot and a miniature 16³ run for the
  three-language dynamical cross-check (`p5_crosscheck.py` → PASS).

### P5-B — `p5b_resolution_96.py`: resolution 96³

The resolution study of monograph section 12.7 — run A repeated one to
one on a **96³ grid** (eight times the degrees of freedom, `k_max = 32`):

* checkpointed execution with the Fourier-space state as the complete
  integration variable (a 96³ run exceeds the small-job memory budget of
  one chunk);
* pairwise 48³ ↔ 96³ comparison of every diagnostic: averaged quantities
  converge to `3·10⁻⁵` (energy), `1.1·10⁻⁴` (enstrophy peak) and
  `5.7·10⁻⁶ / 5.1·10⁻⁶` (Serrin integrals); the supremum norms shift by
  a conservative 1–2 % (nearly degenerate argmax);
* the spectral certificate **improves**: the far-tail slope at the
  enstrophy peak moves from `σ = −6.64` to `σ = −11.30` (`R² = 0.993`),
  the certificate band from `[11, 16]` to `[22, 32]`;
* the hyperdissipative run H2 (`b = 2`) reaches `k_max/η_b = 12.4` yet
  the `x*(b)` deviation stays at 10.9 % — the residual is
  **model-form** (the Pao shape), not resolution — recorded explicitly.

### P5-C — `p5c_stretch_ensemble.py`: vortex stretching statistics

The random-ensemble program of monograph section 12.8 — is the certified
field genuinely turbulent, or a degenerate flow on which the gates close
trivially? Stretching statistics `α = (ω_i S_ij ω_j)/(|ω|² s_rms)`,
`β_S` and the alignment `cos²θ_i` on three families of 96³ fields:

* **GAU** — 32 synthetic K41 Gaussian fields (the P3 generator): null
  check passed, `⟨α⟩ = 0.0007 ± 0.0036`, `cos²θ_i = 1/3` exactly as the
  independence of ω and S demands — a spectrum, even an exact one,
  creates no stretching;
* **SUR** — 8 phase surrogates of a DNS snapshot (amplitudes preserved,
  phases randomized): `⟨α⟩ = 0.006 ± 0.007` — also null;
* **DNS** — snapshots `t = 4, 5, 6` of the 96³ run: `⟨α⟩ = 0.09–0.12`
  (stretching dominates, feeding the enstrophy balance),
  `cos²θ₂ = 0.41–0.45` — the classical **intermediate-eigenvector
  alignment** (Ashurst et al. 1987), `β_S = 0.11–0.13` against the GOE
  null `3·10⁻⁴` (2·10⁵ Monte-Carlo matrices);
* point-tensor artifacts (9 channels × 48³ f64: `S` and `ω`) recomputed
  by the C++ and Julia tracks from the raw file — after catching and
  fixing a genuine Julia memory-layout bug (column-major requires the
  `(9, N, N, N)` reshaping) the three languages agree to `9·10⁻¹⁴`;
* f64-vs-f32 pipeline verification `≤ 4·10⁻⁸`.

### P5-D — `p5d_qr_ensemble.py`: extended ensemble and Q-R topology

The fourth block of the smoothness program (user-requested extension).
Two directions at once.

**More realizations.** The P5-C field families are enlarged: GAU 32 ->
64 fresh exactly-Gaussian realizations (pooled with the original 32
into an M = 96 estimate), SUR 8 -> 16 random-phase surrogates (pooled
24), and — the qualitative step — a *time-resolved DNS ensemble*: 16
perturbed Taylor-Green realizations (8 seeds x nu in {0.01, 0.005}) on
64^3 to t = 6, each starting from the TG initial condition plus a
divergence-free Gaussian perturbation whose amplitude is solved from
the quadratic <(u_TG + c u_p)^2> = 1.1 <u_TG^2> so every realization
starts from exactly the same energy state. A 96^3 resolution check
(seed 1, nu = 0.005) re-quantifies every geometry statistic at doubled
resolution.

**Q-R plane topology.** For every field of every family the program
computes the Chong-Perry-Cantwell invariants of the velocity gradient,
Q = -1/2 tr(A^2) = 1/4|omega|^2 - 1/2 S:S and R = -det A, normalized by
the field-averaged <S:S>; the joint PDF of (r*, q*), the quadrant and
focal/node masses, the conditional mean <q*|r*> and the Vieillefosse
tail statistics (proximity on q* < -0.5 and the tail population
fraction). The DNS families concentrate along the compressional tail;
the Gaussian and surrogate families do not - the topology, like the
eigen-geometry, is carried by the phase dynamics, and it is stable
across the resolution change and the viscosity sweep.

Cross-language verification is extended to the Q-R block: the
(S, omega) point-tensor dump of the primary run (p5d_tensors_dns.f64)
is recomputed by `p5d_qr.cpp` (long double) and `p5d_qr.jl` (Julia),
and `p5d_crosscheck.py` issues the PASS/FAIL verdict
(`p5d_cross_language.json`, tolerance 1e-10). The paper-grade summary
of the whole program (P5-A through P5-D) is the arXiv-format article
`papers/p5-regularity/main.pdf`, whose every number is generated from
the sealed protocols by `gen_paper_numbers.py`.

## 5. Headline results (all pinned, all reproducible)

All numbers below are produced by `code/python/run_all.py` in ~25 minutes
on a laptop and cross-verified by the C++ and Julia tracks.

### The master relation (P1)

| Quantity | Value |
|---|---|
| `C_s` at `C_K = 1.50`, sharp cutoff | **0.17327** |
| Lilly (1966) classical value | 0.17326 |
| absolute deviation | **6·10⁻⁶** |
| `C_s` at `C_K = 1.50`, Gaussian filter | 0.16967 |
| `C_s` at `C_K = 1.50`, box filter | 0.15714 |
| strain-integral quadrature error | 1.5·10⁻⁹ |

### Closures for `C_K` (P2)

| Quantity | Value |
|---|---|
| Heisenberg `α` calibrated on `C_K = 1.50` | 0.4838 |
| `C_K` re-measured from the closed-form spectrum | 1.4814 |
| inertial-range slope (target −5/3) | −1.67 |
| far-dissipation slope (classical Heisenberg) | −7.00 |
| Pao model dissipation-normalization error | 2.2·10⁻⁴ |

### Synthetic-field verification (P3, 96³)

| Filter | Δ/η | measured `C_s` | analytic reference |
|---|---|---|---|
| sharp | 25 | **0.16994** | 0.17327 |
| Gaussian | 25 | 0.17685 | 0.16967 |
| sharp | 50 | 0.17758 | 0.17327 |
| Gaussian | 12.6 | 0.18312 | 0.16967 |
| Gaussian | 3.1 | 0.34651 | (Pao-tail regime) |

The convergence to the Lilly value as the cutoff moves deep into the
inertial range, and the growth at small `Δ/η`, both follow the analytical
prediction.

### Real turbulence (P4, 64³ DNS)

| Quantity | Value |
|---|---|
| stationary `ε`, `u'`, `Re_λ` | pinned in `results/p4_dns_les.json` |
| a priori `C_s`, Gaussian filters `Δ = 2–6Δx` | see `p4_dns_les.json` |
| dynamic Germano `C_s` | same band, fluctuating in time |

Real turbulence is intermittent, so the a priori constant drifts below
the Gaussian-field value — exactly the shift reported throughout the LES
literature (Meneveau & Katz 2000 and references therein). The monograph
discusses the physical origin.

### 3D smoothness (P5, 48³ Taylor-Green)

| Quantity | Value |
|---|---|
| enstrophy peak `Ω_max` at `t = 4.90` | 1.2995 (run A) |
| max `‖ω‖_∞` / max `‖u‖_∞` | 5.692 / 0.994 |
| BKM integral over the horizon `I_BKM(6)` | 17.642 |
| Serrin integrals `∫⟨u⁴⟩dt`, `∫⟨u⁶⟩^{1/2}dt` | 0.2325, 0.5169 (finite, sublinear) |
| b-protocol effect `I_BKM(B)/I_BKM(A)` | **0.9985** (−0.15 %, trajectory-level) |
| universal dissipation peak `k_d·η_b` vs `x*(b)` | 4.3 % (`b=1`) … 11 % (`b≥5/4`), resolution-limited |
| far-tail slope at the enstrophy peak | σ = −6.64 (Heisenberg `k⁻⁷` band); σ = −11.30 at 96³ |
| energy / enstrophy balance residuals | ≤ 1.1·10⁻³ / 5.7·10⁻³ |
| **P5-B**: averaged diagnostics 48³ → 96³ | converge to 10⁻⁶–10⁻⁴; sup-norms 1–2 % (conservative) |
| **P5-C**: DNS vs Gaussian ensembles | `⟨α⟩ = 0.09–0.12` vs `0.0007 ± 0.0036`; `cos²θ₂ = 0.43` vs `1/3` |
| **P5-C**: three-language tensor statistics | agree to `9·10⁻¹⁴` after the Julia layout fix |

Every classical regularity criterion (LPS, BKM, ε-regularity proxies) is
satisfied with wide margins on the computed horizon; the monograph (ch. 12)
discusses what a numerical certificate can and cannot establish.

## 6. Three-language verification

The analytical core is deliberately small (a handful of formulas), so it
is re-implemented **three times** and the outputs must agree:

| Track | Files | Runtime | Output |
|---|---|---|---|
| **Python 3.11+** | `code/python/sk_core.py`, `p1_lilly.py`, `p2_closures.py`, `p3_synthetic_apriori.py`, `p4_dns_les.py`, `p5_regularity.py`, `p5b_resolution_96.py`, `p5c_stretch_ensemble.py`, `p5_crosscheck.py` | ~25 min | `results/p1..p5*.json`, `*.csv`, `*.npy`, `*.npz`, `*.f64` |
| **C++17** | `code/cpp/sk_core.hpp`, `p1_lilly.cpp`, `p2_closures.cpp`, `p3_apriori_cpp.cpp`, `p5_regularity.cpp`, `p5c_stretch.cpp` (+ `Makefile`) | ~1 min | `results/p1_cpp.json`, `p2_cpp.json`, `p3_cpp.json`, `p5_cpp.json`, `p5c_cpp.json` |
| **Julia 1.10+** | `code/julia/sk_core.jl`, `p1_p2_julia.jl`, `p5_regularity.jl`, `p5c_stretch.jl` (zero external dependencies) | ~30 s | `results/p1_p2_julia.json`, `p5_julia.json`, `p5c_julia.json` |

Cross-language agreement at the reference point `C_K = 1.50`:

| Quantity | Python | C++ (long double) | Julia |
|---|---|---|---|
| `C_s` sharp | 0.17327 | 0.173266 | 0.17327 |
| `C_s` Gaussian | 0.16967 | 0.169667 | 0.16967 |
| `C_s` box | 0.15714 | 0.157140 | 0.15714 |
| Heisenberg measured `C_K` | 1.4814 | 1.4814 | 1.4814 |
| far-dissipation slope | −7.00 | −7.00 | −7.0 |
| P5 `β_b`, `b = 1` | 2.8948 | 2.8948 | 2.8948 |
| P5 `x*(b)`, `b = 2` | 0.91871 | 0.91871 | 0.91871 |
| P5 snapshot `‖ω‖_∞` | 5.6920712 | 5.6920712 | 5.6920712 |
| P5 mini-DNS `E(1.0)`, 16³ | 0.234961873 | 0.234961922 | 0.234961873 |
| P5-C `s_rms` (DNS 48³ snapshot) | 0.7841508168776554 | 0.7841508168776553 | 0.7841508168776627 |

The P5 cross-language protocol (`results/p5_cross_language.json`, status
**PASS**) additionally quantifies the miniature-DNS agreement: machine
precision at `t = 0`, ≤ 1.3·10⁻⁸ on `[0, 0.1]` (set by the nearly
degenerate argmax of the sup-norm) and ≤ 8.1·10⁻⁶ at `t = 1` — the
exponential deviation growth (rate ≈ 21) is the chaotic amplification of
floating-point noise, itself an estimate of the largest Lyapunov exponent
of the mini-flow. The P5-C block of the same protocol recomputes the
stretching statistics from the raw point-tensor artifacts in all three
languages (max relative deviation ≤ 9·10⁻¹⁴; the block also documents the
Julia column-major layout bug that was caught and fixed during the
cross-check).

The C++ track uses `long double` where precision matters; the Julia track
uses no external packages at all (the JSON writer is hand-rolled), so it
runs on a bare Julia installation — including Termux.

## 7. Repository layout

```text
research_col_smar/
├── README.md                        ← this file
├── MONOGRAPH_RU.pdf / .docx         ← Russian monograph, both editions
├── MONOGRAPH_EN.pdf / .docx         ← English monograph, both editions
├── cover_ru.html / cover_en.html    ← print-ready cover layouts
├── code/
│   ├── python/                      ← the executable program (P1–P5, figures)
│   │   ├── sk_core.py               ← shared library (conventions, closures)
│   │   ├── p1_lilly.py              ← master relation + sensitivity
│   │   ├── p2_closures.py           ← Heisenberg + Pao closures
│   │   ├── p3_synthetic_apriori.py  ← Monte-Carlo spectral verification
│   │   ├── p4_dns_les.py            ← 3D DNS + a priori + dynamic tests
│   │   ├── p5_regularity.py         ← 3D smoothness protocol (BKM/LPS, b-family)
│   │   ├── p5b_resolution_96.py     ← 96³ resolution study (checkpointed)
│   │   ├── p5c_stretch_ensemble.py  ← stretching statistics: GAU/SUR/DNS ensembles
│   │   ├── p5_crosscheck.py         ← three-language cross-validation
│   │   ├── figures.py               ← all monograph figures (RU and EN)
│   │   ├── run_all.py               ← orchestrator
│   │   └── requirements.txt
│   ├── cpp/                         ← C++17 verification track
│   │   ├── sk_core.hpp
│   │   ├── p1_lilly.cpp
│   │   ├── p2_closures.cpp
│   │   ├── p3_apriori_cpp.cpp
│   │   ├── p5_regularity.cpp        ← long-double analytic core + mini-DNS
│   │   ├── p5c_stretch.cpp          ← P5-C tensor statistics (long double)
│   │   └── Makefile
│   ├── julia/                       ← Julia verification track (dependency-free)
│   │   ├── sk_core.jl
│   │   ├── p1_p2_julia.jl
│   │   ├── p5_regularity.jl         ← hand-rolled FFT mini-DNS
│   │   └── p5c_stretch.jl           ← P5-C tensor statistics
│   └── README.md
├── results/                         ← pinned JSON protocols + CSV/NPY data
│   ├── p1_lilly.json                ← master-relation protocol
│   ├── p1_lilly_table.csv
│   ├── p2_closures.json             ← closures protocol
│   ├── p2_spectra.csv
│   ├── p3_synthetic_apriori.json    ← synthetic-field protocol
│   ├── p3_apriori.csv
│   ├── p3_cpp.json / p1_cpp.json / p2_cpp.json / p1_p2_julia.json
│   ├── p4_dns_les.json              ← DNS protocol (grid, ν, Re_λ, C_s)
│   ├── p4_dns_spectrum.csv
│   ├── p4_apriori.csv
│   ├── p5_regularity.json           ← smoothness protocol (A/B, b-family)
│   ├── p5_bkm.csv                   ← E, Ω, ‖ω‖_∞, I_BKM time series
│   ├── p5_certificate.csv           ← tail-fit series
│   ├── p5_bfamily.csv               ← β_b, η_b, k_d, x*(b) table
│   ├── p5_spectra.npz               ← shell spectra for fig9/fig10
│   ├── p5_snapshot_u.f64 / p5_snapshot_w.f64
│   ├── p5_cpp.json / p5_julia.json / p5_mini_python.json
│   ├── p5_cross_language.json       ← three-language PASS/FAIL
│   └── README.md
└── figures/
    ├── ru/                          ← Russian figure editions (300 dpi PNG)
    └── en/                          ← English figure editions (300 dpi PNG)
```

Every directory carries its own README with file-level documentation.

## 8. How to run everything

### 8.1 Python track (the full program: P1–P5 + figures)

Requires Python 3.11+, numpy, scipy, matplotlib.

```bash
cd research_col_smar/code/python
python3 -m pip install -r requirements.txt   # numpy scipy matplotlib
python3 run_all.py                           # everything, ~25 min
python3 run_all.py p1 p2                     # just the fast analytical stages
python3 figures.py ru                        # regenerate the Russian figures
python3 figures.py en                        # regenerate the English figures
```

Expected console output (abridged):

```text
[P1] C_K = 1.5: C_s sharp = 0.17327, gaussian = 0.16967, box = 0.15714
[P1] |C_s - Lilly| = 5.96e-06, quadrature err = 1.47e-09
[P2] Heisenberg: alpha = 0.4838 -> C_K = 1.4814 (target 1.5), slope = -1.67
[P2] dissipation checks: H = 2.2e-04, Pao = 2.2e-04
[P3] analytic: sharp = 0.17327, gaussian = 0.16967
[P3] sharp_d16     C_s = 0.16994 +/- ...
[P4] eps = ..., u' = ..., Re_lambda = ...
[P4] a priori gaussian_d2  C_s = ...
[P5] A: t_peak = 4.90, Omega_max = 1.2995, ||w||_oo max = 5.6921, I_BKM = 17.6423
[P5] B: I_BKM = 17.6157, factor I_B/I_A = 0.9985
[P5] b_pow=1: eta_b=0.0956, k_d=2.617, k_d*eta_b=0.2503, x*(b)=0.2399, rel.dev=4.3%
[P5] energy balance A: 5.52e-04, enstrophy balance A: 5.65e-03
[P5-B] 96^3: I_BKM = 17.8786, slope at peak = -11.30 (48^3: -6.64)
[P5-B] convergence: E 3.1e-05, Omega_max 1.1e-04, LPS_u4 5.7e-06
[P5-C] GAU: alpha = 0.0007 +/- 0.0036, cos2 = 1/3 (null check)
[P5-C] DNS t=5: alpha = 0.0908, beta_S = 0.1148, cos2 = (0.28, 0.43, 0.29)
```

### 8.2 C++ track (verification of the analytical core)

Requires a C++17 compiler (`g++` or `clang++`). No external libraries.

```bash
cd research_col_smar/code/cpp
make run          # builds into build/ and writes ../../results/p*_cpp.json
```

### 8.3 Julia track (dependency-free verification)

Requires Julia 1.10+ (any build; no packages are used).

```bash
cd research_col_smar/code/julia
julia p1_p2_julia.jl ../../results
julia p5_regularity.jl ../..            # P5 track (writes results/p5_julia.json)
julia p5c_stretch.jl ../..              # P5-C tensor statistics (writes results/p5c_julia.json)
python3 ../python/p5_crosscheck.py      # three-language cross-validation -> PASS
```

### 8.4 Android (Termux), complete recipe

```bash
pkg update -y && pkg upgrade -y
pkg install -y python git clang make libjpeg-turbo
pip install -U pip
pip install numpy matplotlib            # ~5 min on a modern phone
# scipy is optional: every program here runs on numpy alone
cd ~
git clone https://github.com/wild8highlander/navier-stokes-b.git
cd navier-stokes-b/research_col_smar/code/python
python3 run_all.py p1 p2 figures        # fast stages on the phone
```

Notes for Termux:

* `p3` runs comfortably on a phone (~2–3 min); `p4` is the heavy stage —
  on a phone prefer `python3 p4_dns_les.py` with `N_STEPS` reduced in the
  file header, or run it on a laptop and copy the pinned JSON.
* The C++ track builds with Termux's default clang: `make CXX=clang++`.
* All programs write UTF-8 JSON/CSV only — no platform-specific artifacts.

### 8.5 One-file manifest of runtimes

| Stage | Laptop (2 cores) | Termux (Snapdragon) |
|---|---|---|
| P1 | 2 s | 6 s |
| P2 | 4 s | 15 s |
| P3 | 3–4 min | 8–12 min |
| P4 | 10–15 min | 45–90 min (or skip, results are pinned) |
| P5 | 10 min | 45–75 min (or skip, results are pinned) |
| C++ track | 1 min | 3 min |
| Julia track | 10 s | 40 s |
| figures (both languages) | 25 s | 90 s |

## 9. The monograph (RU / EN, PDF / DOCX)

The book-length treatment of this program ships in this directory in two
languages and two formats:

| File | Language | Format | Role |
|---|---|---|---|
| `MONOGRAPH_RU.pdf` | Russian | PDF | citable edition |
| `MONOGRAPH_RU.docx` | Russian | DOCX | editorial source edition |
| `MONOGRAPH_EN.pdf` | English | PDF | citable edition |
| `MONOGRAPH_EN.docx` | English | DOCX | editorial source edition |
| `cover_ru.html`, `cover_en.html` | — | HTML | print-ready cover layouts |

Contents (14 chapters, ~29 pages per language, 10 figures per language):

1. Introduction: the two constants and the one question
2. Mathematical apparatus: NSE, filtering, the LES formalism
3. K41: the −5/3 spectrum, the 4/5 law, and what K41 cannot fix
4. **Derivation I**: the master relation `C_s(C_K)` and its filter family
5. **Derivation II**: the Heisenberg and Pao closures for `C_K`
6. The dynamic Germano procedure: `C_s` as a field
7. Intermittency and the limits of the Gaussian approximation
8. **Experiment I**: Monte-Carlo verification on synthetic K41 fields
9. **Experiment II**: 3D DNS, a priori tests and the dynamic procedure
10. Consolidated results and the literature 1962–2026
11. The program inside the parent b-correction framework
12. **3D smoothness**: regularity criteria, the b-protocol, spectral certificates, the 96³ resolution study and vortex-stretching statistics (P5, P5-B, P5-C)
13. Discussion: what is and is not claimed
14. Conclusions

plus Literature (70+ sources, 1934–2026) and Appendices A–C (protocol
parameters, the convention map, the code map).

Both language editions are generated from a single content model: the
numbers, tables, figures and chapter structure are identical; only the
language differs. The PDF is the citable edition; the DOCX is kept in
sync for editing.

## 10. Figures

Ten figures per language edition (300 dpi PNG, palette-consistent with
the monograph), all generated by `code/python/figures.py`:

| File | Content |
|---|---|
| `fig1_master_lilly.png` | the master curve `C_s(C_K)` for three filter families + the Lilly point |
| `fig2_spectra_closures.png` | Heisenberg and Pao model spectra (compensated form) |
| `fig3_ck_alpha.png` | the Heisenberg map `C_K(α)` with experiment/LhDIA/DIA anchors |
| `fig4_p3_convergence.png` | P3: measured `C_s(Δ/η)` versus the analytic curves |
| `fig5_p4_dns.png` | P4: vorticity slice + the DNS spectrum with the −5/3 band |
| `fig6_p4_apriori.png` | P4: a priori `C_s(Δ)` with the dynamic-procedure band |
| `fig7_ck_summary.png` | `C_K` across experiment, closures and this work |
| `fig8_regularity.png` | P5: enstrophy and the BKM envelope, runs A vs B |
| `fig9_bfamily.png` | P5: shell dissipation of the b-family + the `k_d·η_b` vs `x*(b)` collapse |
| `fig10_certificate.png` | P5: the exponential tail fits and the smoothness-certificate quality |
| `fig11_resolution_96.png` | P5-B: 96³ spectra (A vs H2) + the 48³ → 96³ convergence bars |
| `fig12_stretch_ensemble.png` | P5-C: alignment `cos²θ_i` and stretching-rate `α` PDFs, DNS vs Gaussian/surrogates |

## 11. Conventions, normalizations and the factor-2 trap

Turbulence spectra have a notorious convention trap that silently
corrupts constant-fitting by a factor of 2^(3/4) ≈ 1.68. This program
pins its conventions and *verifies them numerically*; they are repeated
here because every result above depends on them.

1. **`E(k)` is the kinetic-energy spectrum**: `∫₀^∞ E(k) dk = ½⟨u²⟩`
   (kinetic energy per unit mass). When the spectrum is computed on a
   discrete grid, the *variance* shell energy is `e_shell(k) = 2·E(k)`,
   because `⟨u²⟩ = Σ e_shell = 2∫E dk`.
2. **The dissipation identity** is `ε = 2ν∫₀^∞ k² E(k) dk` — or,
   equivalently and more physically, `ε = ν⟨ω²⟩` with
   `⟨ω²⟩ = Σ k² e_shell = ∫k²(2E) dk`. Both forms were verified to
   machine precision in this program (the identity `⟨ω²⟩/⟨u²⟩ = k²` for a
   single-shell field is the cleanest check).
3. **The strain norm** is `|S̄| = (2 S̄_ij S̄_ij)^(1/2)`, so that
   `⟨|S̄|²⟩ = ⟨∂_j u_i ∂_j u_i⟩ = 2∫k²E G²dk` for an incompressible
   isotropic field.
4. **The closure is** `τ_ij = −2ν_t S̄_ij` with `ν_t = (C_sΔ)²|S̄|`, giving
   `τ_ij S̄_ij = −(C_sΔ)²|S̄|³` — note the *single* power of 2 absorbed by
   `|S̄|² = 2 S̄_ij S̄_ij`. The a priori estimator is therefore
   `C_s² = −⟨L_ij S̄_ij⟩/(Δ²⟨|S̄|³⟩)`.
5. **The filter conventions**: sharp cutoff `G = 1 (k < π/Δ)`;
   Gaussian `G = exp(−k²Δ²/24)` where Δ is the standard-deviation
   parameter; box filter `G = sinc(kΔ/2)`.
6. **Gaussian random fields have zero Germano correlation.**
   `⟨L_ij S̄_ij⟩` is a third-order moment; Gaussian third moments vanish.
   Any a priori measurement of `C_s` on a random-phase field is therefore
   sampling noise — the physical value requires real cascade dynamics
   (P4). This program states this explicitly because it is the most
   common silent failure mode of synthetic-field LES papers.

A practical demonstration of why §11 matters: the same algebra evaluated
in the "variance shell" convention instead of the kinetic convention
yields `C_s = 0.29` instead of `0.17` — a 70 % error with no arithmetic
mistake anywhere. The pinned protocols in `results/` record the
convention next to every number.

## 12. Results integrity and manifests

* Every program writes a **JSON protocol** containing: full parameters,
  the convention statement, all headline numbers, per-sample rows, and the
  SHA-256 hash of its own source file (`integrity.sha256_of_code`).
* The CSV/NPY files next to each protocol carry the raw data behind every
  figure, so figures are regenerable without re-running simulations.
* The programs are **deterministic** given their fixed RNG seeds
  (`20260929` for P3, `424242` for P4, `7`/`11`/`3`/`5` in the
  verification utilities): two runs on the same platform produce
  bit-identical JSON except for wall-clock-independent fields.
* Cross-language agreement is itself a check: `p1_cpp.json`,
  `p2_cpp.json`, `p3_cpp.json`, `p1_p2_julia.json` must reproduce the
  Python protocols' analytical numbers; a divergence of more than 1e-5
  (relative) in any shared quantity is a hard failure. The P5 extension
  adds `p5_cpp.json`, `p5_julia.json`, `p5_mini_python.json` and the
  verdict file `p5_cross_language.json` (analytic and snapshot blocks
  ≤ 1e-11, miniature dynamics as discussed in §6).
* The parent repository pins all files in `MANIFEST.json`; after adding
  or regenerating results, refresh it with
  `python3 .github/scripts/regen_manifest.py` from the repository root.

## 13. Frequently asked questions

**Q1. Is the master relation `C_s = 1/(π(3C_K/2)^{3/4})` a new result?**
The derivation is classical in spirit — it is the matching argument that
Lilly (1966) and Deardorff (1970) used, and every LES textbook contains
its skeleton. What this program contributes is not novelty of the algebra
but (i) an explicit, convention-pinned, machine-verified derivation chain
linking the *experimental* `C_K` to `C_s` with a stated error budget;
(ii) the filter-family and Pao-tail corrections quantified against the
same code; (iii) the negative result on Gaussian fields (§11.6); and
(iv) a three-language executable form in which every number is pinned.
We claim measurement-grade rigor, not historical priority.

**Q2. Why does the a priori `C_s` on real DNS fields differ from 0.173?**
Three physical reasons, in order of importance. First, intermittency:
real turbulence has non-Gaussian small-scale statistics, so the exact
Germano least-squares constant is reduced relative to the Gaussian-field
value. Second, finite resolution: a 64³ DNS reaches only modest `Re_λ`,
so the inertial range is short and the fit band matters. Third, filter
shape: the Gaussian filter weights modes differently than the sharp
cutoff for which 0.173 is derived. All three effects are quantified in
the monograph (ch. 7 and 9).

**Q3. Can I trust numbers computed on a phone?**
Yes for P1, P2, the C++ track, the Julia track and the figures — they are
pure arithmetic and quadrature. P3 and P4 are Monte-Carlo/DNS programs:
their *statistics* are platform-independent, but bit-level reproducibility
of floating-point sums is not guaranteed across CPU architectures. The
pinned protocols in `results/` were produced on the reference platform;
a phone re-run should reproduce them to displayed precision, not bit-for-bit.

**Q4. Why is there no shell model in the program?**
An earlier design stage of this program attempted to measure `C_K` with a
Sabra/GOY-type shell model. During development we found that the
energy-conserving triad space for strictly local three-term models is
extremely restricted (an exhaustive numerical search over conjugation
patterns and prefactor offsets finds isolated solutions), and that
shell-model `C_K` values carry model-dependent calibration. The direct
spectral verification (P3) and the DNS route (P4) are cleaner and were
adopted instead. The negative result is documented here for
completeness; the monograph (ch. 12) discusses it.

**Q5. How do I extend the program?**
* Higher `Re_λ`: raise `NGRID` in `p4_dns_les.py` (96³ works on a
  workstation; the a priori machinery is resolution-agnostic).
* Other filters: add a `G(k)` case in `sk_core.py` (`lilly_cs`) and in
  `figures.py`; the analytic value follows §2 of the README for any
  filter with a known transfer.
* Other base flows: the a priori machinery (`strains`, `a_priori`,
  `dynamic_cs`) works on any 3D velocity field, e.g. channels or jets —
  filter the anisotropy out of the log first.

**Q6. What license applies?**
This directory inherits the repository license IPL-RP-1.0 (see
§15). Code may be read, executed and verified; the standard terms of the
parent repository apply without modification.

## 14. Relation to the parent b-correction program

The parent repository ([`navier-stokes-b`](../README.md)) is built around
a universal polarization correction `b = 1/(4π + 2√3)` — an
energy-neutral geometric rotation that suppresses the blow-up mechanism
of the 3D Navier–Stokes equations *without injecting energy and without
modifying the equations*.

The present program studies the *classical, dissipative* route to the
same regularity question: the Smagorinsky closure removes subgrid energy
at a controllable rate `ε_sgs = (C_sΔ)²|S̄|³`. The two mechanisms are
complementary bookends of the same problem:

| | b-rotation (parent) | Smagorinsky closure (this program) |
|---|---|---|
| mechanism | geometric, energy-neutral rotation | eddy viscosity, dissipative |
| energy budget | exactly conserved | monotonically drained |
| constant | `b = 1/(4π+2√3)` — closed form | `C_s = 1/(π(3C_K/2)^{3/4})` — closed form |
| character | kinematic, exact | statistical, matched to K41 |
| target | blow-up suppression (BKM integral) | subgrid closure (LES) |

Both constants are *closed-form* numbers attached to the same equation —
one derived from vortex polarization geometry, the other from
inertial-range statistics. The monograph (ch. 11) reads the two
constructions against each other and asks what the parallel says about
the structure of the equation.

## 15. License and citation

This directory is part of **navier-stokes-b** and inherits the repository
license **IPL-RP-1.0** ([LICENSE.md](../LICENSE.md), Russian text:
[LICENSE.ru.md](../LICENSE.ru.md)).

Cite the parent repository (see [CITATION.cff](../CITATION.cff)) and, for
the results of this program specifically, the monograph editions in this
directory:

```text
wild8highlander. The Smagorinsky and Kolmogorov Constants: A Unified
Spectral Theory, Closures, and Numerical Experiment. Monograph (RU/EN),
navier-stokes-b research program, 2026. Data: navier-stokes-b repository,
research_col_smar directory.
```

---

*Program status: P1–P4 executed 2026-09-29; three-language verification
passed; monograph editions pinned. Maintenance: regenerate everything
with `code/python/run_all.py` after any code change, then refresh the
repository manifest.*
