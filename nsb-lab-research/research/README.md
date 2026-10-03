# 🧪 `research/` — the experiment suite

Deterministic numerical verification of the **b-correction ↔ vortex volume**
theory for [navier-stokes-b](https://github.com/wild8highlander/navier-stokes-b).

![status](https://img.shields.io/badge/experiments-12%2F12%20PASS-2ea043?style=flat-square)
![python](https://img.shields.io/badge/python-3.10%2B-3776AB?style=flat-square&logo=python&logoColor=white)
![julia](https://img.shields.io/badge/julia-1.10-9558B2?style=flat-square&logo=julia)
![seed](https://img.shields.io/badge/seed-20260103-8b8881?style=flat-square)

---

## Files

| File | Role |
|---|---|
| `b_volume_experiment.py` | **Base series** `T A B C D E G F` — 8 experiments, 8 figures, ~4 min |
| `b_volume_extension.py` | **Extended battery** `H I J K` — the cross-check channels, resolution ladder, volume anchors and the dynamic Hou–Luo annihilation; 5 figures, ~3 min |
| `b_volume_check.jl` | **Julia mirror** of the key states (Taylor–Green b-charge, monitor, ring analytics) — stdlib only |
| `B_VOLUME_RESEARCH.md` | The research write-up (EN abstract + RU full text) |
| `summary.json` | Full machine-readable results of the base series |
| `summary_extension.json` | Full machine-readable results of the battery H/I/J/K |
| `figures/` | 13 figures (EN titled) + `figures/ru/` (RU, caption-ready) |

## Run

```bash
python3 b_volume_experiment.py --lang en --outdir out_en          # base series
python3 b_volume_extension.py  --lang en --outdir out_ext_en      # battery H/I/J/K
python3 b_volume_extension.py  --figs-only --lang ru --indir out_ext_en --outdir figs_ru
julia b_volume_check.jl                                           # mirror
```

Dependencies: `numpy`, `matplotlib` (Python ≥ 3.10); Julia ≥ 1.10 (stdlib only).
Everything is deterministic: **seed 20260103**, no random inputs to the physics,
fixed resolution ladders and time windows.

---

## The theory in four formulas

**1. The exact flux identity** (proved pointwise for any incompressible field,
constant axis; `div(n×u) = −(n·ω)`):

```text
div(R_b u) = + sin θ_b · (n_b·ω) + (1 − cos θ_b) · (n_b·∇)(n_b·u)
```

**2. The b-charge** — the carrier of the correction, a «rotating volume»:

```text
B = ∫ |n_b·ω| dV            one kick injects   Q_b = θ_b·B
```

**3. The flux monitor** (a well-posedness indicator, not an invariant):

```text
m = Q_b / (θ_b·B) = 1 + O(θ_b),      |m − sin θ_b/θ_b| ≤ tan(θ_b/2)·D(u)
D(u) = ∫|(n_b·∇)(n_b·u)|dV / ∫|n_b·ω|dV
```

**4. The elementary b-volume** — the answer to «which volume is one correction»:

```text
V₁ = 4π + 2√3 ≈ 16.02 code units = 6.46% of the box   (at unit vorticity)
V(one correction) = 1/ω_ref (coherent)  or  2/ω_ref (isotropic)   [m³ in water]
```

---

## Base series results (experiments T–F)

| Exp | Verifies | Result | Status |
|---|---|---|---|
| **T** | div-injection, O(θ) | slopes −1.000568 (TG), −1.000539/−1.000516/−1.000169 (rings x/y/z), R² ≥ 0.9995 | ✅ |
| **A** | additivity in N | Q/N = 0.08896 vs analytic 0.08735, R² = 0.99999; dE linear, 1.44·10⁻⁴ per vortex | ✅ |
| **B** | orientation algebra | ratios 0.6155/0.5604/0.3830 vs f_plane 0.6073/0.5513/0.3712 (x/y/z) | ✅ |
| **C** | volume scans | fixed Γ: flat to 1.3%; fixed ω₀: slope 0.047509 vs θ_b·ω₀ = 0.046343, R² = 0.99985 | ✅ |
| **D** | merging | co-rotating: additive at any separation; anti-parallel: 2 → 0 | ✅ |
| **E** | decay dynamics | 8 rings, T = 2.0, ν = 0.005: B(T)/B(0) = 0.98275 | ✅ |
| **G** | composition on SO(3) | aligned Θ = N·θ_b; random Θ_rms = √N·θ_b (4000 MC trials, < 0.2%) | ✅ |
| **F** | Kolmogorov bridge | tea/pipe/Draupner/Katrina: η = 0.084 mm … 22 mm; V₁ = 2.5·10⁻¹² … 4.6·10⁻¹⁴ m³ | ✅ |

## Extended battery results (experiments H–K)

### H — cross-check channels
The b-charge is measured **twice**: through the vorticity channel
`B_ω = ∫|n_b·ω|dV` and through the velocity channel
`B_div = ∫|div(R_b u)|dV/θ_b` (no vorticity anywhere). The exact identity is
verified by pointwise regression: **slope 1.000000, R² = 1.00000000 on all
five states**. Integrated deviations sit inside the rigorous bound
`tan(θ_b/2)·D(u)`:

| State | B_ω | B_div/B_ω | D(u) | Bound | Identity R² |
|---|---|---|---|---|---|
| taylor_green (n=32) | 118.6386 | 0.999688 | 0.31 | 0.0096 | 1.00000000 |
| ring_x (n=64) | 3.81600 | 1.013462 | 0.94 | 0.0294 | 1.00000000 |
| ring_y (n=64) | 3.46431 | 1.016303 | 1.08 | 0.0335 | 1.00000000 |
| ring_z (n=64) | 2.33246 | 1.031683 | 1.98 | 0.0619 | 1.00000000 |
| lattice8 (n=48) | 11.21059 | 1.016138 | 1.50 | 0.0469 | 1.00000000 |

Also: L²-carrier additivity (B₂ R² = 0.982 with visible cross-terms;
Ω∥ and Ω R² = 1.000) and the **exact L² orientation law**
`Ω∥/Ω = (1 − (n_b·n_t)²)/2` — measured 0.45500/0.37500/0.17000 vs theory
0.45500/0.37500/0.17000 (**0.000% error**).

### I — resolution convergence (n = 32 → 96)
err(B) falls monotonically **13.149% → 0.407% → 0.261% → 0.202%**; the flux
predicted by the pointwise identity matches the measured flux to
**≤ 0.014%** on every grid; the monitor stabilizes (drift < 0.2% after n = 48).

### J — volume anchors and grid invariance
The measured b-charge equals the **projected Gaussian tube volume**
`V_gauss = 4π²R₀σ²` times `f_plane` — the pointwise-identity prediction
matches to **≤ 0.002%** for three normals × two cores. The monitor is
grid-invariant: n = 48 vs n = 64 differ by 0.13% / 0.006%.

### K — the dynamic Hou–Luo annihilation (2-D, n = 128, ν = 0.004, T = 2.0)
Two states with identical Gaussian cores on the torus:

| Quantity | Hou–Luo dipole | Co-rotating pair |
|---|---|---|
| B(T)/B(0) | **28.78%** (annihilation) | **62.96%** (retention) |
| dE/dt = −ν·Ω′ (R²) | 1.000000 | 1.000000 |
| dΩ′/dt = −2ν·P (R²) | 0.999999 | 1.000000 |
| slope of ω_max(t) | −1.267 | −0.878 |
| monitor m_abs (theory 1.230112) | **1.230116** | **1.230116** |
| net flux m_net (torus theorem: 0) | 9.8·10⁻¹⁷ | 0 |
| circulation drift | 1.2·10⁻¹⁶ | 1.2·10⁻¹⁶ |

**The torus theorem**: on a periodic box ∫ω′ ≡ 0 for any flow, so the net
flux of any kick vanishes identically — corrections are quasi-neutral, and
merging vs annihilation is read off the dynamics of |B(t)|. The 2-D monitor
is exact: for the in-plane kick `(ẑ·∇)(ẑ·u) = 0`, hence
`m_abs = b/(θ_b·(n_b·ẑ)) = 1.230112` — measured **1.230116** at every sample
time (six digits).

---

## Determinism and the Julia mirror

- Seed `20260103`; all ladders fixed; identical output on re-runs.
- `b_volume_check.jl` reproduces: TG b-charge **118.638640**, monitor
  **0.999688**, ring analytics — matching Python to 10⁻⁶ (real Julia 1.10.9 run).
- Known porting trap (documented in the lab `docs/PORTING.md`): the spectral
  divergence carries a factor **i**; without it the real div field is purely
  imaginary and its L¹ norm vanishes silently.
