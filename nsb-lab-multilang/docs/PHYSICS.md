# The Physics of NSB Lab — a complete reference

This document collects every equation, criterion and algorithm that the eight
editions implement. It is written to be readable on its own; the code comments
reference the section numbers below. The Julia file
`julia/nsb_lab_standalone.jl` is the normative reference implementation.

---

## 1. The equations

**3-D incompressible Navier–Stokes** on the torus `[0, 2π)³` (nondimensional):

```
∂u/∂t + (u·∇)u = −∇p + νΔu + ν₄Δ²u ,   ∇·u = 0
```

Euler corresponds to `ν = ν₄ = 0` (the lab uses `ν = 1e-14` for numerical
regularity). The momentum form is never discretised directly: with periodic
boundary conditions the *rotation form* is exact and cheaper:

```
(u·∇)u = ω × u − ∇(½|u|²) ,  ω = ∇×u
```

so the RHS that the code actually evaluates is

```
∂û/∂t = −P[ ω × u ]^ − (νk² + ν₄k⁴) û
```

with P the Leray (Helmholtz) projector, defined spectrally in §3. The
gradient part of the nonlinearity is absorbed into the pressure and vanishes
under P.

**2-D barotropic β-plane** (the real-flows model, *physical units*):

```
∂ω/∂t = −J(ψ, ω) − β ∂ψ/∂x + ν∇²ω + ν₄∇⁴ω ,   ω = ∇²ψ
```

where ψ is the streamfunction, J the Jacobian `J(ψ,ω) = ψ_x ω_y − ψ_y ω_x`,
and β = 2Ω_e cos φ / R_e the β-plane parameter at latitude φ
(Ω_e = 7.2921e-5 s⁻¹, R_e = 6.371e6 m). In spectral space the code evaluates
`−J(ψ,ω)` as `−(u ∂xω + v ∂yω)` with `u = ∂yψ`, `v = −∂xψ`.

## 2. Initial conditions

* **Taylor–Green**: `u = (sin x cos y cos z, −cos x sin y cos z, 0)`.
  Smooth, divergence-free, decays through a vortex-lattice cascade; the
  standard benchmark for order-of-accuracy measurements.
* **ABC** (A=B=C=1): `u = (A sin z + C cos y, B sin x + A cos z, C sin y + B cos x)`.
  An exact Beltrami eigenfield (ω = u) of the curl operator, hence a fixed
  point of the inviscid dynamics' linear part; the classical Euler blow-up
  candidate.
* **Hou–Luo**: two anti-parallel Gaussian vortex tubes along x centred at
  (y, z) = (π/2, π/2) and (π/2, 3π/2) with core width σ = π/16, plus the
  symmetry-breaking perturbation `(1 + ε cos x)`, ε = 0.05. The IC is given
  as *vorticity* and converted to velocity by Biot–Savart:
  `û = i k × ŵ / |k|²` followed by projection and masking.
* **Random**: Gaussian white noise plus a deterministic k_peak = 4 seeding
  pattern, projected to solenoidality.
* **Rankine composite vortex** (flows): solid-body rotation inside R_max
  (ζ = 2U/R), a R^-1.6 decay outside, a Gaussian shelf at 4R, and a 2%
  azimuthal asymmetry `1 + 0.02 sin(2θ + 0.7)` that triggers barotropic
  instability.
* **Bickley jet** (flows): `u(y) = U sech²((y−y_c)/W)` with a meander
  `1 + 0.02 cos(4πx/L)`; vorticity is the analytic −dU/dy.

## 3. The pseudospectral method

Grid quantities live on an N×N×N lattice; spectral quantities on the same
number of complex modes with wavenumbers

```
k_i ∈ {0, 1, …, N/2 − 1, −N/2, …, −1}
```

(the standard `numpy.fft` frequency ordering; the lab's own FFT follows the
same convention: unnormalised forward, 1/N per axis on the inverse).

**Derivatives** are exact: `∂x → i k_x` in spectral space.

**Leray projection.** For any spectral vector field â, the solenoidal part is

```
P[â] = â − k (k·â)/|k|²   (with the k = 0 mode zeroed)
```

The code applies it to the nonlinearity at *every* RK4 sub-stage, which is
what keeps ‖div u‖ at machine level (~1e-16) despite round-off.

**2/3 de-aliasing.** All modes with `|k_i| > N/3` on any axis are zeroed
after every nonlinearity evaluation and after every full RK4 step. This
removes the aliasing contamination of the cubic nonlinearity completely at
the cost of 1−(2/3)³ ≈ 70% of the modes.

**RK4.** The classic four-stage Runge–Kutta on the spectral state:

```
k1 = F(u),  k2 = F(u + dt/2 k1),  k3 = F(u + dt/2 k2),
k4 = F(u + dt k3),  u' = u + dt/6 (k1 + 2k2 + 2k3 + k4)
```

Each stage re-evaluates the projected, de-aliased nonlinearity. The measured
order on Taylor–Green enstrophy is 4.125 for the dt-ladder (0.04, 0.02, 0.01)
— the .125 offset is the pre-asymptotic tail contamination, which is why the
self-test tolerance is ±1.2.

**Adaptive CFL.** `h = min(dt, 0.4·dx/max|u|)` in 2-D and
`h = min(dt, 0.5·dx/max|u|)` in 3-D, evaluated either every step (3-D) or
every 8 steps (2-D, cost amortisation). The audit counts steps where the CFL
bound bit.

**Hyperviscosity.** `ν₄Δ²u → −ν₄k⁴û` stabilises the spectral tail of
long 2-D runs without touching the inertial range.

## 4. Diagnostics (all Parseval-exact)

With the normalisation ⟨f⟩ = Σ|f̂|²/N⁶ in 3-D (N⁴ in 2-D):

| quantity | definition |
|---|---|
| energy | `E = ½ ⟨|u|²⟩` |
| enstrophy | `Ω = ½ ⟨|ω|²⟩` |
| palinstrophy | `P = ½ ⟨|∇ω|²⟩` |
| dissipation | `ε = ν ⟨|∇u|²⟩` (hyper: `+ ν₄ ⟨|Δu|²⟩`) |
| sup vorticity | `sup|ω|` collocation max (L∞ proxy) |
| divergence | `max‖div u‖ = √Σ|i k·û|² / N³` |
| shell spectrum | `E(k) = mean over shells of ½|û|²/N⁶` |
| tail level | `max E(k near cutoff) / max E(k)` |
| K41 slope | OLS of `log E vs log k` for k ∈ [2, 0.75·k_cut] |
| BKM integral | `∫₀ᵗ sup|ω| dt` (trapezoid per sampling interval) |

**K41.** Kolmogorov 1941 predicts `E(k) ∝ k^(−5/3)` (slope −1.666…) in the
inertial range. The 2-D β-plane runs develop a −3 (enstrophy cascade) and a
−5/3 range at larger scales; the fit window `[2, 0.75·k_cut]` targets the
direct-cascade side of the spectrum and reports slope + R² honestly.

## 5. The blow-up scanner

`λ(t) = d/dt ln sup|ω|` is the exponential growth rate of the vorticity
maximum; a finite-time singularity of type `(t*−t)^(−α)` implies
`λ(t) ~ α/(t*−t) → ∞`. The scanner:

1. computes λ by central differences of the sampled sup|ω| series;
2. fits a linear trend `dλ/dt` with honest R² over the whole window *and*
   over the last 25% tail;
3. declares growth **sustained** only if: tail trend > 0, tail R² > 0.5,
   λ_max > 0, and the tail sup|ω| reaches ≥ 98% of the historical maximum
   (a decaying flow with micro-bumps is *not* a singularity);
4. only then searches `(t*, α)` over α ∈ [0.5, 7] step 0.25 and
   t* = T_end·frac, frac ∈ [1.02, 2.5] step 0.02, maximising the R² of the
   log-log fit `ln sup|ω| = ln A − α ln(t* − t)`, accepting R² > 0.9.

Every verdict carries the scope note: *"a certificate of internal consistency
of the computed solution within the window, not a general theorem."*

## 6. The b-correction mathematics

Rotation R = Rodrigues(θ_b, axis (0.3, −0.5, √0.66)) with
θ_b = arcsin(1/(4π + 2√3)) ≈ 0.0783.

**Full symmetry** u′(x) = R u(R⁻¹x): for the specific quarter-turn R about z
implemented by the lab (R(x,y,z) = (−y, x, z)), R⁻¹ maps the lattice onto
itself *exactly*, so the transform is a circular index shift —
`u′(x_i, y_j, z_k) = R·u(y_j, −x_i, z_k)` with `−x_i` the mirrored index
`(N − i) mod N`. No interpolation error exists; every L² norm is preserved
to machine precision. It is a relabeling of Fourier modes: it cannot remove
or damp anything, and the audit verifies `|sup ω′ − sup ω| / sup ω < 1e-9`.

**Pointwise rotation** u′(x) = R u(x): pointwise isometry of L² (energy
exactly preserved, verified to 1e-12), but

```
div(Ru) = cos θ · div u + sin θ · curl u
```

so a Beltrami field (curl u = u ≠ 0) acquires ‖div‖ = sin θ · ‖u‖ ≈ 0.078‖u‖.
The audit measures the injected RMS divergence, then reprojects (Leray) and
verifies the divergence returns to machine level. Since BKM-type criteria
rely on the vorticity structure and the structure is untouched
(`sup|ω′| = sup|ω(R·)|` collocation-wise after reprojection), no
regularization effect is possible — which is exactly what `ck_b_effect`
asserts numerically.

**2-D kicks in the flow lab**: the same rotation is applied to (u, v) of the
β-plane model every t_adv (or t_adv/2 in hard mode). The injected divergence
is measured in spectral space before reprojection; typical values
O(1e-5 … 1e-3) document that the injection is real but small, and the
subsequent dynamics is unchanged.

**Wave audit** (Draupner / Tōhoku / Qiantang): a finite-depth Stokes orbital
field `u = a ω₀ cosh(kz)/sinh(kh) cos kx`, `v = a ω₀ sinh(kz)/sinh(kh) sin kx`
with ω₀ = √(gk tanh kh) is essentially irrotational; rotating it pointwise
*preserves* div (since sin θ·curl ≈ 0) — the injection mechanism itself is
inert on the flow classes where the hypothesis would matter most.

## 7. DNS feasibility arithmetic

For a flow with velocity scale U, length scale L and molecular viscosity ν_mol:

```
Re = UL/ν_mol
η (Kolmogorov) = L · Re^(−3/4)
N_DNS ≈ 2π · Re^(3/4)          (grid points per dimension)
mem ≈ N³ · 16 B · 22            (complex fields × working set)
```

Example: Hurricane Katrina (U = 77 m/s, L = 37 km, air) → Re ≈ 1.9e11,
N_DNS ≈ 1.8e9 nodes, ≈ 1.1e27 bytes of memory — "infeasible on any existing
hardware", which is why the flow lab runs reduced β-plane models and says so.

## 8. References

1. Beale, J.T., Kato, T., Majda, A. *Remarks on the breakdown of smooth
   solutions for the 3-D Euler equations*. Commun. Math. Phys. 94 (1984).
2. Kerr, R.M. *Evidence for a singularity of the three-dimensional,
   incompressible Euler equations*. Phys. Fluids A 5 (1993).
3. Hou, T.Y., Luo, R. *On the finite-time blowup of a 1-D model system of the
   3-D incompressible Euler equations*. (2013) — and the 3-D tubes setup the
   lab mirrors.
4. Orszag, S.A. *Numerical simulation of incompressible viscous flow within
   closed boundaries*. J. Fluid Mech. 49 (1971) — 2/3 rule.
5. Taylor, G.I., Green, A.E. *Mechanism of the production of small eddies
   from large ones*. Proc. R. Soc. A 158 (1937).
6. Kolmogorov, A.N. *The local structure of turbulence in incompressible
   viscous fluid for very large Reynolds numbers*. Dokl. Akad. Nauk SSSR 30
   (1941).
7. Brachet, M.E. et al. *Small-scale structure of the Taylor–Green vortex*.
   J. Fluid Mech. 130 (1983).
8. Cooley, J.W., Tukey, J.W. *An algorithm for the machine calculation of
   complex Fourier series*. Math. Comp. 19 (1965).
