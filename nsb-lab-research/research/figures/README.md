# 🖼 `research/figures/` — the figure gallery

13 publication-grade figures. **English set** (titled — this directory) and
**Russian set** (caption-ready, no in-image titles — [`ru/`](ru/)) — the same
12 experiments rendered twice, so the monographs and the README can embed
them without re-running anything.

All figures follow the same style contract: 200 DPI PNG, dashed grid,
no top/right spines, palette `#0F2440 / #C25E00 / #5B7C99` (+ gold
`#d5c080` accents), constrained layout, legends placed to avoid data.

## Base series (experiments T–F)

| File | Experiment | What it shows |
|---|---|---|
| `fig1_theorem.png` | **T** | div(R_b u) vs −θ_b(n_b·ω) on Taylor–Green: slope −1.0006, R² = 0.99992 |
| `fig2_nscan.png` | **A** | kick flux and energy cost vs N merged rings — linear, R² = 0.99999 |
| `fig3_orientation.png` | **B** | orientation algebra: Q/(θ_b·Γ·L) for ring normals x/y/z |
| `fig4_volume.png` | **C** | volume scans: fixed Γ (flat) and fixed ω₀ (linear, slope θ_b·ω₀) |
| `fig5_annihilation.png` | **D** | pair merging: co-rotating additive, anti-parallel 2 → 0 |
| `fig6_netangle.png` | **G** | net angle of N composed kicks: aligned Θ = N·θ_b, random √N·θ_b |
| `fig7_decay.png` | **E** | free decay of 8 rings: B(t)/B₀ ≈ const (viscosity is the only sink) |
| `fig8_water.png` | **F** | Kolmogorov bridge: η and quantum vortex volume for 4 real flows |

## Extended battery (experiments H–K)

| File | Experiment | What it shows |
|---|---|---|
| `fig9_crosschecks.png` | **H** | exact-identity regression (R² = 1.00000000) + L²-carrier additivity |
| `fig10_convergence.png` | **I** | convergence ladder n = 32→96 + monitor stability |
| `fig11_anchors.png` | **J** | projected-volume check (≤ 0.002%) + elementary b-volume anchors |
| `fig12_houluo.png` | **K** | Hou–Luo dynamics: B(t), annihilated fraction, ω_max decay, monitors |
| `fig13_houluo_fields.png` | **K** | vorticity fields: dipole (top) vs co-rotating pair (bottom) |

## Regenerating

```bash
python3 b_volume_experiment.py --lang en --outdir out_en   # figs 1–8 (titled)
NSB_NO_TITLES=1 python3 b_volume_experiment.py --lang ru --outdir out_ru   # figs 1–8 (captions)
python3 b_volume_extension.py  --lang en --outdir out_ext_en    # figs 9–13 (titled)
NSB_NO_TITLES=1 python3 b_volume_extension.py --figs-only --lang ru \
    --indir out_ext_en --outdir figs_ru                          # figs 9–13 (captions)
```

Embedding note: the `ru/` set carries no in-image titles — captions live in
the document text (monograph typesetting rule), while the EN set is
self-titled for GitHub browsing.
