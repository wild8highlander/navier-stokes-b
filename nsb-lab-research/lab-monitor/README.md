# 🔭 `lab-monitor/` — the `Q/(θ_b·B)` monitor inside the b-Lab (v2.2.0)

The research needed a *live* measurement of the flux-identity monitor inside
the Navier–Stokes b-Lab itself. Since **v2.2.0** the polyglot port
([nsb-lab-multilang](https://github.com/wild8highlander/navier-stokes-b))
ships it in the two reference editions:

| Edition | Functions added | Where |
|---|---|---|
| **Python** | `b_charge3`, `kick_flux3`, `b_monitor3` | `python/nsb_lab.py`, after `b_rotation_matrix()` |
| **Julia** | `nsb_b_charge`, `nsb_kick_flux`, `nsb_b_monitor` | `julia/nsb_lab_standalone.jl`, after `nsb_b_rotation_matrix()` |

Both the `--experiment baudit` audit **and** `--selftest` print and assert
the monitor (`0.97 < m < 1.03`).

---

## Definitions

```text
B     = ∫ |n_b·ω| dV            the b-charge (rotating volume)      [vorticity channel]
Q_b   = ∫ |div(R_b u)| dV       the flux of ONE pointwise kick      [velocity channel]
m     = Q_b / (θ_b·B)           the flux-identity monitor
```

The exact identity behind the monitor (constant axis; `div(n×u) = −(n·ω)`):

```text
div(R_b u) = + sin θ_b (n_b·ω) + (1 − cos θ_b) (n_b·∇)(n_b·u)
⇒  m = 1 + O(θ_b),   |m − sin θ_b/θ_b| ≤ tan(θ_b/2)·D(u),
   D(u) = ∫|(n_b·∇)(n_b·u)|dV / ∫|n_b·ω|dV
```

The deviation from 1 is **physical** (the gradient term), not numerical — so
the monitor is a validity indicator of the whole measurement pipeline.

## Python snippet (as merged)

```python
def b_charge3(s, uhat):
    """B = ∫|n_b·ω| dV — the b-charge ('rotating volume') of the flow."""
    wh = [np.empty_like(uhat[0]) for _ in range(3)]
    curl_hat3(wh, uhat, s)
    w = ifft_field3(wh)
    wpar = (NSB_AXIS[0]*w[0] + NSB_AXIS[1]*w[1] + NSB_AXIS[2]*w[2])
    return float(np.mean(np.abs(wpar)) * (2.0*math.pi)**3)

def kick_flux3(s, uhat):
    """Q_b = ∫|div(R_b u)| dV — velocity channel; mind the spectral i!"""
    ruh = [np.empty_like(uhat[0]) for _ in range(3)]
    rotate_pointwise3(ruh, uhat, b_rotation_matrix(), s)
    dhat = 1j * (s.kx*ruh[0] + s.ky*ruh[1] + s.kz*ruh[2])
    div = ifft_field3([dhat])[0]
    return float(np.mean(np.abs(div)) * (2.0*math.pi)**3)

def b_monitor3(s, uhat):
    B, Q = b_charge3(s, uhat), kick_flux3(s, uhat)
    return {"B": B, "Q": Q,
            "monitor": Q / (NSB_THETA_B * B) if B > 0 else float("nan")}
```

## Julia snippet (as merged)

```julia
function nsb_b_charge(s::NsbNSE3D, uhat, W::NsbWork3D)
    nsb_curl_hat!(W.wh, uhat, s)
    nsb_ifft_field!(W.w, W.wh, W, s)
    acc = 0.0
    @inbounds for i in eachindex(W.w[1])
        wp = NSB_AXIS[1]*W.w[1][i] + NSB_AXIS[2]*W.w[2][i] + NSB_AXIS[3]*W.w[3][i]
        acc += abs(wp)
    end
    return acc / s.n^3 * (2.0*π)^3
end

function nsb_kick_flux(s::NsbNSE3D, uhat, W::NsbWork3D)
    T = W.wh
    nsb_rotate_pointwise!(T, uhat, nsb_b_rotation_matrix(), s, W)
    d = W.kd
    @inbounds for i in eachindex(d)
        d[i] = 1.0im * (s.kx[i]*T[1][i] + s.ky[i]*T[2][i] + s.kz[i]*T[3][i])
    end
    copyto!(W.tmp[1], d)
    nsb_fftn!(W.tmp[1], s.plan, true)
    acc = 0.0
    @inbounds for i in eachindex(W.tmp[1])
        acc += abs(real(W.tmp[1][i]))
    end
    return acc / s.n^3 * (2.0*π)^3
end
```

## Measured values (v2.2.0, verified runs)

| Run | State | B | Q/(θ_b·B) | Verdict |
|---|---|---|---|---|
| Python `--selftest` | random field, n = 16 | 548.1199 | **0.998968** | PASS |
| Julia `--selftest` (1.10.9) | Taylor–Green, n = 16 | 118.4254 | **1.000183** | PASS |
| Python `--experiment baudit` | ABC, n = 32 | 203.0695 | **0.999487** | PASS |
| research exp. H | Taylor–Green, n = 32 | 118.6386 | **0.999688** | PASS |
| research exp. K (2-D, dynamic) | Hou–Luo dipole, t* = 1.0 | — | **1.230116** (theory 1.230112) | PASS |

## Porting notes (the two traps)

1. **The spectral `i`.** Divergence in Fourier space is `Σ i k_i û_i`. The
   lab's `divergence_max` only uses `|Σ k_i û_i|` (the `i` drops out of the
   magnitude), so it was tempting to reuse the pattern — but for the *field*
   the missing `i` makes the real-space div purely imaginary and its L¹ norm
   silently vanishes (`m` reads exactly 0).
2. **The k = 0 mode on a torus.** A periodic velocity never sees the mean
   vorticity: ∫ω′ ≡ 0. Carry the mean as an exactly conserved scalar (zero
   the RHS at k = 0) and compute the b-charge on ω′ = ω − ⟨ω⟩. The net kick
   flux on a torus is identically zero — use the magnitude flux |div| instead.

C and C++/Rust/Go/PHP editions can adopt the same monitor with the recipe
above; the reference implementations to copy are the two snippets on this
page.
