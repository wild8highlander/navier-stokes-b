# Python verification, levels L1–L5

An independent multi-level suite. Every check recomputes everything from scratch on each
run; the results are saved to `results/*.json` (honest numbers, no manual edits).

| Level | What it verifies | Time |
|---|---|---|
| L1 | Constants from closed-form formulas (mpmath, 50 digits): b in two forms, sin θ_b = b — exact, cos θ_b, ln(1+b), Z = exp(b·β_K·L_min) — the Klein closure, Lilly's C_s, φ, e; float64 cross-check of every quantity | ~1 s |
| L2 | Rotation algebra: the exact form u′ = u∥ + √(1−b²)u⊥ + b(ω̂×u⊥) = Rodrigues at θ_b: R^T·R = I (10⁵ vectors), det R = 1, |u′| = |u|, spectrum {1, e^{±iθ_b}} | ~10 s |
| L3 | Kirchhoff vortices: Hamiltonian character (H drift → 0 as dt⁴), RK4 order = 4, isometry of the phase flow | ~30 s |
| L4 | 2D NSE: the identity ω′ = cos θ_b·ω — exact; energy is preserved under rotation; div u′ = −b·ω; the energy identity; the max principle for ω; continuous rotation without energy injection | ~2–5 min |
| L5 | 3D Taylor–Green N=48, ν=0.01, T=6: the BKM integral and max‖ω‖∞ for the true NSE versus the continuous b-rotation; |ΔE| per rotation | ~10–20 min |

## How to Run

```bash
python3 verify_all.py                 # everything
NSE3D_SKIP=1 python3 verify_all.py    # without L5 (~1 minute)
NSE3D_SMALL=1 python3 verify_all.py   # L5 in the control regime N=24, T=1
```

Dependencies: `numpy`, `mpmath` (required), `sympy` (optional, for the symbolic
proof of the equivalence of the two forms of b).

## The L5 Protocol (fixed)

Taylor–Green in T³, 2/3-dealiasing, RK4, dt=0.004, T=6. Continuous rotation:
the angle per step φ = dt·θ_b (cumulatively θ_b·T ≈ 21.459°), axis ω̂ = ω/‖ω‖,
the vorticity is recomputed from the rotated velocity, Leray projection.

The historical 3.5× factor refers to the under-resolved N=24 configuration (chapter 11
of the monograph) and is NOT reproduced here; the fixed protocol yields its own factors
(in the completed run: 1.032× on the BKM integral, 1.014× on max‖ω‖∞, |ΔE| ≤ 5.1·10⁻⁵).
