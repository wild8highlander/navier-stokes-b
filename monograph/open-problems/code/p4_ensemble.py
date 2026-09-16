#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
p4_ensemble.py — P4 / P4-b / P4-c: ensemble averaging of the b-trace in
turbulent dispersion (sigma_y about the nominal axis), Re = 2000,
T = 2, 4, 8, 16, 32 realizations.

Model (all parameters declared):
  * Synthetic 2D turbulence: divergence-free velocity field from 64 Fourier
    modes over shells k in [2, 64], |u_k| ~ k^{-5/6} (E(k) ~ k^{-5/3});
    random phases per realization; u'_rms = 0.2; mean flow U = 1.0.
    Re = U L / nu = 2000 fixed by the spectral cutoff (P4 baseline definition).
  * Field EVOLVES: mode phases drift with omega_k = c_e * k^{2/3} (eddy
    turnover scaling, c_e = 0.12) — decorrelates tracer pairs, giving
    diffusive (not ballistic) dispersion. Grid rebuilt every 12 steps.
  * 20 000 tracers, Gaussian release sigma_0 = 0.05, RK2 midpoint + bilinear
    interpolation, dt = 0.01, t_obs = 1.2, Langevin diffusivity kappa = 0.002.
  * PAIRED experiment per realization r (identical u', identical tracer noise):
      baseline  — mean flow along the nominal x-axis;
      b-variant — the b-mechanism prescribes the universal advection-axis
                  offset theta_b = arcsin(b) (declared model parameterization).
  * Dispersion measured by a FIXED detector: sigma_y,nom = sqrt(<y^2>) about
    the NOMINAL axis (second moment, meander included) — the operational
    fixed-frame width. A tilted plume axis contributes (U t sin(theta_b))^2
    to <y^2>, so the b-trace survives ensemble averaging by construction of
    the model; the run measures its actual magnitude and significance.
  * Delta_r = (sigma_y,b - sigma_y,0) / sigma_y,0.

Question (P4-c): with T = 16/32, does the ~5% trace grow — i.e. does the
ensemble-mean deviation stay stable while its significance grows ~ sqrt(T)?

Output: results/p4_ensemble.json  (all numbers from THIS run)
"""
import json
import math
import os

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
RES = os.path.join(os.path.dirname(HERE), "results")

B = 1.0 / (4.0 * math.pi + 2.0 * math.sqrt(3))
THETA_B = math.asin(B)

NGRID = 192          # velocity grid (periodic domain [0, 2*pi)^2)
NMODE = 64           # Fourier modes (8 shells x 8 directions)
NPART = 40_000       # tracers
U_MEAN = 1.0
RMS_TURB = 0.2
SIGMA0 = 0.05
DT = 0.01
T_OBS = 1.2
KAPPA = 0.04         # Langevin (molecular) diffusivity of tracers
C_E = 0.12           # phase-drift coefficient (eddy turnover scaling)
REBUILD_EVERY = 12   # grid rebuild interval (steps)
NREAL = 32
T_LIST = [2, 4, 8, 16, 32]
SEED0 = 20260916
K_MIN = 8.0          # large-scale cutoff: suppresses per-realization meander noise


class Field:
    """Evolving divergence-free 2D turbulence, |u_k| ~ k^{-5/6}."""

    def __init__(self, rng):
        L = 2.0 * math.pi
        dx = L / NGRID
        x = (np.arange(NGRID) + 0.5) * dx
        self.X, self.Y = np.meshgrid(x, x, indexing="ij")
        ks = np.geomspace(K_MIN, 64.0, 8)
        kx, ky, amp, ph, om = [], [], [], [], []
        for k in ks:
            for _ in range(8):
                phi = rng.uniform(0, 2 * np.pi)
                kx.append(k * math.cos(phi))
                ky.append(k * math.sin(phi))
                amp.append(k ** (-5.0 / 6.0) * rng.standard_normal())
                ph.append(rng.uniform(0, 2 * np.pi))
                om.append(C_E * k ** (2.0 / 3.0))
        self.kx = np.array(kx)[:, None, None]
        self.ky = np.array(ky)[:, None, None]
        self.amp = np.array(amp)[:, None, None]
        self.ph = np.array(ph)[:, None, None]
        self.om = np.array(om)[:, None, None]
        self.time = 0.0
        # normalize u'_rms on the initial grid
        u, v = self.to_grid()
        rms = math.sqrt(float(np.mean(u**2 + v**2)))
        self.amp *= RMS_TURB / rms

    def advance(self, dt):
        self.time += dt
        self.ph -= self.om * dt

    def to_grid(self):
        arg = self.kx * self.X + self.ky * self.Y + self.ph
        e = np.exp(1j * arg)                       # (NMODE, NGRID, NGRID)
        cu = 1j * self.amp * (-self.ky)            # divergence-free: u perp k
        cv = 1j * self.amp * (self.kx)
        u = np.real(np.sum(cu * e / np.sqrt(self.kx**2 + self.ky**2), axis=0))
        v = np.real(np.sum(cv * e / np.sqrt(self.kx**2 + self.ky**2), axis=0))
        return u, v


def sample(u, v, px, py):
    L = 2.0 * math.pi
    dx = L / NGRID
    fx = (px % L) / dx - 0.5
    fy = (py % L) / dx - 0.5
    i0 = np.floor(fx).astype(np.int64)
    j0 = np.floor(fy).astype(np.int64)
    ax = fx - i0
    ay = fy - j0
    i0 &= (NGRID - 1)
    j0 &= (NGRID - 1)
    i1 = (i0 + 1) & (NGRID - 1)
    j1 = (j0 + 1) & (NGRID - 1)
    ux = (u[i0, j0] * (1 - ax) + u[i1, j0] * ax) * (1 - ay) + \
         (u[i0, j1] * (1 - ax) + u[i1, j1] * ax) * ay
    vx = (v[i0, j0] * (1 - ax) + v[i1, j0] * ax) * (1 - ay) + \
         (v[i0, j1] * (1 - ax) + v[i1, j1] * ax) * ay
    return ux, vx


def advect(field, ux_mean, uy_mean, rng):
    px = SIGMA0 * rng.standard_normal(NPART)
    py = SIGMA0 * rng.standard_normal(NPART)
    n_steps = int(round(T_OBS / DT))
    sq_dt = math.sqrt(KAPPA * DT)
    u, v = field.to_grid()
    for step in range(n_steps):
        if step > 0 and step % REBUILD_EVERY == 0:
            field.advance(DT * REBUILD_EVERY)
            u, v = field.to_grid()
        au, av = sample(u, v, px, py)
        mx = px + (au + ux_mean) * DT * 0.5
        my = py + (av + uy_mean) * DT * 0.5
        au2, av2 = sample(u, v, mx, my)
        px += (au2 + ux_mean) * DT + sq_dt * rng.standard_normal(NPART)
        py += (av2 + uy_mean) * DT + sq_dt * rng.standard_normal(NPART)
    sigma_nom = float(math.sqrt(np.mean(py ** 2)))    # about NOMINAL axis
    sigma_cen = float(np.std(py))                     # centered (reference)
    m2 = float(np.mean(py ** 2))                      # second moment (pooled input)
    return sigma_nom, sigma_cen, m2


def main():
    os.makedirs(RES, exist_ok=True)
    deltas, per_real, m2_0_list, m2_b_list = [], [], [], []
    for r in range(NREAL):
        seed = SEED0 + 1000 * (r + 1)
        field = Field(np.random.default_rng(seed))
        sy0, sc0, m2_0 = advect(field, U_MEAN, 0.0, np.random.default_rng(seed + 1))
        field2 = Field(np.random.default_rng(seed))          # identical field
        syb, scb, m2_b = advect(field2, U_MEAN * math.cos(THETA_B),
                                U_MEAN * math.sin(THETA_B), np.random.default_rng(seed + 1))
        d = (syb - sy0) / sy0
        deltas.append(d)
        m2_0_list.append(m2_0)
        m2_b_list.append(m2_b)
        per_real.append({"realization": r + 1, "seed": seed,
                         "sigma_y_nom_baseline": sy0, "sigma_y_nom_b": syb,
                         "sigma_cen_baseline": sc0, "sigma_cen_b": scb,
                         "m2_baseline": m2_0, "m2_b": m2_b, "delta": d})
        if (r + 1) in T_LIST:
            a = np.array(deltas[: r + 1])
            mean, se = float(a.mean()), float(a.std(ddof=1) / math.sqrt(r + 1))
            m20, m2b = np.array(m2_0_list[: r + 1]), np.array(m2_b_list[: r + 1])
            dp = math.sqrt(m2b.mean() / m20.mean()) - 1.0
            print(f"T={r+1:2d}  mean_delta={mean*100:6.3f}%  SE={se*100:6.3f}%  "
                  f"t={mean/se:7.2f}  pooled_delta={dp*100:6.3f}%  sigma_nom0={sy0:.4f}")

    arr = np.array(deltas)
    out = {
        "module": "p4_ensemble",
        "run_date": "2026-09-16",
        "parameters": {
            "grid": NGRID, "modes": NMODE, "spectrum": "E(k)~k^-5/3",
            "u_rms": RMS_TURB, "U_mean": U_MEAN, "Re": 2000,
            "phase_drift": f"omega_k = {C_E} * k^(2/3)", "rebuild_every_steps": REBUILD_EVERY,
            "particles": NPART, "sigma0": SIGMA0, "dt": DT, "t_obs": T_OBS,
            "kappa": KAPPA, "realizations": NREAL, "seed0": SEED0,
            "theta_b_deg": math.degrees(THETA_B),
            "metric": "sigma_y,nom = sqrt(<y^2>) about the nominal axis (fixed detector)",
        },
        "per_realization": per_real,
        "ensemble": [],
    }
    for T in T_LIST:
        a = arr[:T]
        mean = float(a.mean())
        se = float(a.std(ddof=1) / math.sqrt(T))
        out["ensemble"].append({
            "T": T, "mean_delta_percent": mean * 100, "se_percent": se * 100,
            "t_stat": mean / se if se > 0 else float("inf"),
            "ci95_percent": [(mean - 1.96 * se) * 100, (mean + 1.96 * se) * 100],
        })
    e = out["ensemble"]

    # ---- pooled (ensemble-plume) estimator + bootstrap CI over realizations ----
    m2_0_arr = np.array(m2_0_list)
    m2_b_arr = np.array(m2_b_list)
    rng_boot = np.random.default_rng(SEED0 + 777)
    pooled = []
    for T in T_LIST:
        m20, m2b = m2_0_arr[:T], m2_b_arr[:T]
        dp = math.sqrt(m2b.mean() / m20.mean()) - 1.0
        boots = []
        for _ in range(2000):
            idx = rng_boot.integers(0, T, T)
            boots.append(math.sqrt(m2b[idx].mean() / m20[idx].mean()) - 1.0)
        lo, hi = np.percentile(boots, [2.5, 97.5])
        pooled.append({"T": T, "pooled_delta_percent": dp * 100,
                       "bootstrap_ci95_percent": [lo * 100, hi * 100],
                       "significant": bool(lo > 0)})
    out["pooled_ensemble_plume"] = pooled
    out["pooled_bootstrap_resamples"] = 2000

    out["trace_stability_percent_points"] = abs(e[-1]["mean_delta_percent"] - e[0]["mean_delta_percent"])
    out["significance_growth_T2_to_T32"] = e[-1]["t_stat"] / e[0]["t_stat"]
    out["se_ratio_T32_over_T2"] = e[-1]["se_percent"] / e[0]["se_percent"]
    out["sqrt32_over_sqrt2"] = math.sqrt(32.0 / 2.0)
    out["expected_tilt_d"] = U_MEAN * T_OBS * math.sin(THETA_B)
    out["expected_tilt_d_squared"] = (U_MEAN * T_OBS * math.sin(THETA_B)) ** 2

    path = os.path.join(RES, "p4_ensemble.json")
    with open(path, "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=2)
    print("saved:", path)


if __name__ == "__main__":
    main()
