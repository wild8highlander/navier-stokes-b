# Julia verification, levels L1–L5

**A fully independent implementation** in pure stdlib Julia:

* L1 — BigFloat (120 bits), formulas checked against 50-digit string references;
* L2 — rotation algebra (1000 vectors × 200 axes, in-house Rodrigues matrix);
* L3 — Kirchhoff vortices: RK4 order, isometry, area preservation;
* L4 — 2D NSE: **in-house radix-2 FFT with a self-test against the direct DFT**,
  the 2/3 rule with 2N-padding, the identity ω′ = cos θ_b·ω, energy bookkeeping;
* L5 — 3D Taylor–Green N=32: the BKM integral, continuous b-rotation
  (smoothed axis k ≤ N/6, quadratic weight), 2N-padding.

Nothing to install: no FFTW, no JSON, no other packages are required.

## How to Run

```bash
julia verify_all.jl                 # everything; L5 ≈ 5–15 min
NSE3D_SKIP=1 julia verify_all.jl    # without L5 (~1 minute)
NSE3D_SMALL=1 julia verify_all.jl   # L5 in the control regime
```

The results of each run are saved to `results/*.json`.

The differences from the Python version are honestly documented: Julia-L5 uses N=32
(the in-house FFT requires a power of two), Python-L5 uses N=48; these are two independent
references, not one task in two languages. The L1–L4 constants are cross-checked by `scripts/compare_python_julia.py`.
