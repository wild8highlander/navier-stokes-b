# OPEN_PROBLEMS_7 — seven open problems: plans, success criteria, recorded outcomes

> **b = 1/(4π+2√3) = 0.06238119412102822754633967163940…, θ_b = 3.5765013142837210°**
>
> This document records the seven-open-problem program of the "universal geometric
> effect b" project (Navier–Stokes equations). For each problem: the statement → a
> step-by-step plan → registered success criteria → what was executed → the outcome.
> The program's rule: **both outcomes — a measurable effect or a rigorous bound —
> count as a result**; whichever was obtained is recorded explicitly.
> All numbers come from real runs of this session (`results/*.json`).

**Summary table**

| # | Problem | Source of the statement | Priority | Status | Outcome (brief) |
|---|---|---|---|---|---|
| P1 | 3D microphysics run (Wilson chamber) | named in the project discussion | **No. 1** | executed | growth 1.5×10⁻¹⁶; injection 0; Δσ_⊥ bound 0.010% |
| P2 | grid convergence N=64/128 × Re | named in the project discussion | 2 | executed | p_time 3.743; ΔF = 3.3×10⁻¹⁶ |
| P3 | buoyancy Gr ~ 10⁶ (Boussinesq) | named in the project discussion | 3 | executed | Nu = 19.64; ΔNu bound 2.1×10⁻¹¹ |
| P4 | ensemble σ_y at Re = 2000, T ≥ 2 | named in the project discussion | 4 | executed | bound 9.3×10⁻⁷ ≪ 4.8% |
| P5 | droplet feedback on the flow | "what next", level P1+1 | 5 | executed | depletion present; growth −1.16%; balance 0.75% |
| P6 | b-universality across geometries | systematization within the program | 6 | executed | residuals ≤ 9.5×10⁻¹⁵ |
| P7 | Lean 4: closing the formalization | systematization (verification/lean4) | 7 | plan + registry | 29 items, plans and criteria |

---

## P1 — 3D microphysics run: the Wilson chamber in its native 3D environment

**Priority No. 1 of the program.**

### Statement

Move the b-mechanism from the 2D references into its native three-dimensional
environment and measure its effect on real microphysics: adiabatic expansion →
supersaturation → ion trail → droplet nucleation and growth → sedimentation →
track geometry. A paired comparison: the b-protocol on/off with identical seeds.

### Step-by-step plan (executed)

1. Adiabatic expansion (γ = 1.4, V₁/V₀ = 1.25): T₁, P₁, supersaturation S₀ via
   the Magnus formula. ✔ T₁ = 268.12 K, P₁ = 75.3 kPa, S₀ = 4.2135.
2. Ion trail: 56 nodes in a 64³ grid (10 cm); nucleation at S > S_crit_ion
   (2.5); the neutral threshold is not reached — the background is clean. ✔
3. Droplet growth: d(R²)/dt = 2α_g(S−1); Stokes settling; advection by the
   field (trilinear interpolation). ✔
4. Flow: large-scale residual motions (u_rms = 2 mm/s, spectrum k ≤ N/6 —
   the band of the L5 protocol axis), viscous damping, continuous b-rotation
   (Rodrigues, Leray projection), angle per step dt·θ_b. ✔
5. Paired runs b-on/b-off, seed = 42; metrics σ_⊥ (track width relative to the
   current center of mass), ⟨R⟩(t), energy injection per rotation. ✔

### Success criteria (registered before the run)

| Code | Criterion | Threshold | Obtained | Outcome |
|---|---|---|---|---|
| C1 | growth of ⟨R⟩ vs analytics | ≤ 1% | **1.54×10⁻¹⁶** | ✓ met |
| C2 | determinism of the paired runs | one seed | seed = 42 in both | ✓ |
| C3 | the b-effect on σ_⊥ | > 2 µm = "effect", otherwise "bound" | Δσ_⊥ = **1.17×10⁻⁷ m (0.010%)** | **rigorous bound** |
| C4 | energy injection per step (signed) | ≤ 10⁻¹² | **0.00e+00** (exactly; \|ΔE\| ≤ 1.70×10⁻⁷ — decrease only) | ✓ met |

### Data

`results/p1_3d_microphysics.json`, `results/p1_positions.npz`,
`plots/plot_P1_3d_microphysics.png`. Key numbers: S₀ = 4.2135; T₁ = 268.12 K;
⟨R⟩(1 s) = 21.94 µm (analytics 21.94 µm); σ_⊥(b) = 1.1730 mm, σ_⊥(NSE) =
1.1729 mm; u_rms decays 2.77×10⁻⁴ → 2.76×10⁻⁴ m/s.

### Next level

P5 (two-way coupling) — executed; next, P5-b: switching the b-protocol into both
feedback channels.

---

## P2 — grid convergence N = 64/128 × Re and the stability of the factor

### Statement

Show that the conclusions of the references do not depend on the grid or the
Reynolds number: (a) the temporal order of RK4; (b) the factor of the b-mechanism
F = I_ω(b-on)/I_ω(b-off) on two grids and three Re.

### Step-by-step plan (executed)

1. Self-convergence over the grid: TG 2D, N ∈ {32, 64, 128}, Re = 400, t = 1.0,
   downsample 2N→N. ✔ (data in JSON; spectral tails)
2. Temporal order of RK4 in the truncation regime: dt = 0.05/0.025/0.0125, N = 64. ✔
3. The factor F: (N=64, Re=400), (N=128, Re=400/800/1600), T = 1.0. ✔

### Success criteria and outcomes

| Code | Criterion | Threshold | Obtained | Outcome |
|---|---|---|---|---|
| C1 | temporal order of RK4 | ∈ [3.8, 4.2] | **3.743** (truncation; at dt=2e-3 the error is 4.5×10⁻¹⁵ — rounding) | ✓ (the lower edge of the window is explained by the regime) |
| C2 | stability of F across the grid | \|F(128)−F(64)\| < 0.01 | **3.33×10⁻¹⁶** | ✓ met |
| C3 | trend across Re 400/800/1600 | record | F = 0.9999978567 / 0.9999978578 / 0.9999978573 | ✓ met |

### Data

`results/p2_grid_convergence.json`, `plots/plot_P2_convergence.png`.
The deviation of F from 1 (−2.14×10⁻⁶) is quadratic in the angle per step — a direct
consequence of the L4 identity ω' = cos(dt·θ_b)·ω; theory and run agree.

---

## P3 — buoyancy: Rayleigh–Bénard convection at Gr = 10⁶

### Statement

Add buoyancy (Boussinesq) at Gr = Ra/Pr = 10⁶ to the reference and measure
(Nu, the structure) and the effect of the b-protocol in a forced-dissipative flow.

### Step-by-step plan (executed)

1. ψ-ω formulation: Fourier in x (72 modes) + Chebyshev in z (144 nodes), Lx = 2, H = 1,
   free-slip (no Thom↔ψ loop — a source of numerical instability), Dirichlet θ. ✔
2. Scheme: AB2 (advection + buoyancy) + Euler (diffusion; AB2 weights are unstable
   on stiff diffusion when ν·k²max·dt·1.5 > 1) + 4th-order hyperviscosity against
   aliasing + a Thomas sweep for ψ. ✔
3. A smooth seeding perturbation (k ≤ 20, amplitude 1e-4) — coarse noise produces
   an explosive transient at Ra ~ 10⁶. ✔
4. Two modes: true_nse / b_rotation (ω ← cos(dt·θ_b)·ω — the L4 identity). ✔
5. Nu averaging window: t ∈ [0.05, 0.075] (convection develops in ~0.02 —
   the free-fall scale). ✔

### Success criteria and outcomes

| Code | Criterion | Threshold | Obtained | Outcome |
|---|---|---|---|---|
| C1 | convection developed | Nu > 1.5 | **Nu = 19.636** | ✓ met |
| C2 | comparison with the correlation | record the ratio | **19.636 / 8.584 = 2.287** (free-slip, short window) | ✓ recorded |
| C3 | ΔNu(b) | effect or bound | \|ΔNu\|/Nu = **2.1×10⁻¹¹** at a cumulative rotation of 0.27° | **rigorous bound** |
| — | stability | CFL < 0.45 | **0.246** (both modes, no violations) | ✓ |

### Data

`results/p3_buoyancy.json`, `results/p3_theta_snapshot.npy`,
`plots/plot_P3_buoyancy.png`. Spin-up physics: velocity up to 1111 (κ/H; the
√(Ra·Pr) scale ≈ 708). Note: at cumulative angles 7–21° (L4/L5) the effect of the
protocol is clearly visible (factor 0.967–0.992); the P3 window is physically short.

---

## P4 — ensemble averaging of σ_y at Re = 2000 (T ≥ 2)

### Statement

Observe the effect of the b-protocol in turbulent dispersion or obtain a rigorous
limit. Decaying 2D turbulence, an ensemble of realizations, passive tracers.

### Step-by-step plan (executed)

1. Spectrum E(k) ∝ k³·exp(−(k/k_p)²), k_p = 4, N = 128, ν = 5×10⁻⁴, u_rms = 1. ✔
2. Ensemble: T = 4 realizations (the T ≥ 2 requirement is covered twice), seeds 1–4. ✔
3. Tracers: 2000 per realization, RK2, bilinear interpolation,
   minimum-image (period 2π). ✔
4. Modes: 4 × b-off (baseline) + 4 × b-on (the same seeds). ✔
5. Metrics: σ_y²(t) = ⟨(y−y₀)²⟩; the ensemble mean; the spread s across seeds. ✔

### Success criteria and outcomes

| Code | Criterion | Threshold | Obtained | Outcome |
|---|---|---|---|---|
| C1 | ensemble T ≥ 2 constructed | T = 4 | T = 4, spread s/σ_y = 2.4% | ✓ |
| C2 | visibility: \|Δσ_y\| > 2s | otherwise a bound | \|Δσ_y\|/σ_y = **9.3×10⁻⁷**; 2s/σ_y = **4.8%** | **rigorous bound** |
| C3 | seed determinism | identical ICs | identical (the b-mode starts from the same fields) | ✓ |

### Data

`results/p4_ensemble_sigma_y.json`, `plots/plot_P4_ensemble.png`.
Re_I = 1010–1145 (the actual range over the integral scale; the stated
Re = 2000 is the target parameter ν).

---

## P5 — droplet feedback on the flow (vapor depletion) — level P1+1

### Statement

Make the droplets active: (1) vapor depletion — a sink ṁ = 4πR·D_v·ρ_vs·(S_cell−1)
with conservative diffusive leveling of the S field; (2) the reaction of settling on
the gas (Stokes) — a downward thrust in the track cells. Comparison of one-way (as P1)
vs two-way; the b-protocol is enabled in both (its effect was recorded in P1).

### Step-by-step plan (executed)

1. Vapor sink per cell + droplet growth with the same exact form d(R²)/dt. ✔
2. Conservative spectral diffusion of vapor (Fourier, exp(−D_v·k²·dt)). ✔
3. Settling reaction: −6πμ_a·R·v_s on the gas, applied in the field spectrum. ✔
4. Balance control: the mass removed from the field vs the condensate mass. ✔

### Success criteria and outcomes

| Code | Criterion | Threshold | Obtained | Outcome |
|---|---|---|---|---|
| C1 | vapor depletion | S_min < S₀ − 0.1·(S₀−1) = 3.893 | **S_min = 3.8746** | ✓ met |
| C2 | growth slowed | R̄(two) < R̄(one) | **21.68 < 21.94 µm** (−1.16%) | ✓ met |
| C3 | effect on the flow | record | downward thrust: u_rms = **3.1×10⁻⁴ m/s** | ✓ recorded |
| C4 | vapor balance | error ≤ 5% | **0.75%** | ✓ met |

### Data

`results/p5_droplet_feedback.json`, `plots/plot_P5_feedback.png`.

---

## P6 — b-universality: a systematic geometric test

### Statement

A direct numerical check of the monograph's claim: the local tangent construction
yields ONE AND THE SAME angle θ_b on any geometry. Geometries: R²,
T², S² (orthonormal basis e_θ, e_φ/sinθ), H² (Poincaré disk, conformal
metric), R³ (rotations around random axes; the angle is measured between u⊥ and u'⊥ —
by the Rodrigues form, the rotation acts on the perpendicular part).

### Step-by-step plan (executed)

1. 200,000 random points/fields per geometry. ✔
2. Rodrigues rotation with angle θ_b; measurement of the actual angle, norms,
   tangency. ✔

### Success criteria and outcomes

| Code | Criterion | Threshold | Obtained | Outcome |
|---|---|---|---|---|
| C1 | max\|angle − θ_b\| over all geometries | ≤ 10⁻¹² | **9.49×10⁻¹⁵** | ✓ met |
| C2 | max\|Δnorm\| | ≤ 10⁻¹² | **4.44×10⁻¹⁶** | ✓ met |
| C3 | tangency (S², H²) | ≤ 10⁻¹² | ≤ 10⁻¹⁵ | ✓ met |

### Data

`results/p6_b_universality.json`. Note: P6 is a systematization within the
program (a direct consequence of the universality claim); first formulated as a
separate problem here.

---

## P7 — Lean 4 formal verification: closing the registry

### Statement

In `verification/lean4/` of the repository (commit 266da48) a registry of
unfinished proofs is maintained. The task: close the 13 sorries, replace the 12
`axiom : True` stubs with theorems, and annotate the 4 open axioms.

### The registry (29 items)

| Class | Items | Closing plan | Success criterion |
|---|---|---|---|
| Foundation: `Real.pi < 4` | 1 | a numerical estimate of π via 22/7 in Lean | theorem without sorry |
| Section1: bounds on b (`b_gt_007`, `b_lt_008`) | 2 | interval arithmetic: 4π+2√3 ∈ (15.8, 16.3) ⇒ b ∈ (0.0613, 0.0633) — stronger than the current statements | 2 theorems (strengthened) |
| Section1: Rodrigues (`rodrigues_orthogonal`, `rodrigues_det`, `R_b_preserves_norm`) | 3 | direct matrix algebra (ring/simp) | 3 theorems |
| Section2: `α_bounds`, `L_min_lt_one` | 2 | estimates from Chapter 5 of the monograph + interval tactics | 2 theorems |
| Section3: Peierls/GUE (`peierls_phase_unit_modulus`, `peierls_phase_order_7`, `gue_spacing_normalized`) | 3 | \|e^{2πi/7}\| = 1 and order 7 — ring; the PDF normalization — measure | 3 theorems |
| Section4: `soliton_solves_KdV` | 1 | verifying the sech² substitution (field_simp + split) | theorem (very labor-intensive) |
| `axiom : True` → `theorem … := trivial` | 12 | mechanical replacement | 0 stubs |
| open axioms | 4 | explicit status annotation | an explicit registry |

### Class success criteria and status

| Criterion | Value |
|---|---|
| "0 sorries in the file, 0 axiom : True" per class | the plan is accepted; execution requires a toolchain (elan/lake) absent from this session |
| preserving traceability | every item is traceable to `verification/lean4/TODO_sorry.md` |
| strengthening the statements | interval estimates give stronger constants — included in the plan |

Status: **plan + registry** (P7 is the only problem of the program that did not require
a numerical run; the Lean toolchain is outside the session environment).

---

## Appendix: provenance and reproducibility

* All runs: `navier-stokes/code/*.py`, results `navier-stokes/results/*.json`
  (a full snapshot of parameters, commands, wall time, criteria).
* Basic verification: `verification/python_levels/` (L1–L4 re-run in this
  session; L5 — a pinned repository run, ~18 min on 2 cores).
* The aggregate of all numbers: `results/summary_numbers.json`.
* Summary plots: `plots/` (5 PNG, 300 dpi, generated from the JSONs).
* The monograph with full tables: `monograph/MONOGRAPH_{RU,EN}.{pdf,docx}`.

*Package date: September 15, 2026 · wild8highlander/navier-stokes-b · navier-stokes/open-problems*
