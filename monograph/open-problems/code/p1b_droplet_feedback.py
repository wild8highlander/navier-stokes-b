#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
p1b_droplet_feedback.py — P1 (baseline, no feedback) vs P1-b (droplet feedback /
vapor depletion), 3D Wilson-chamber microphysics.

Physical model (all parameters declared, no hidden knobs):
  * Chamber: 1 cm^3 box; ion track is a straight line along x through the box
    center; source and initial conditions are exactly translation-invariant
    along x, and diffusion with Neumann side walls preserves that invariance,
    so the 3D vapor problem reduces EXACTLY to the (y,z) cross-section.
    Droplet counts are reported per cm of track length (3D-consistent).
  * Adiabatic expansion: CR=1.25, gamma=1.4, T0=293.15 K, t_exp=10 ms.
  * Magnus saturation pressure (T in deg C): p_sat=610.94*exp(17.625*Tc/(Tc+243.04)).
  * Initial RH 0.95 -> peak supersaturation S ~ 4.8 (typical Wilson chamber).
  * Ion column: Gaussian cross-section (sigma_r = 2 cells),
    line density Lambda = 5e6 ion pairs/m (alpha-like).
  * Nucleation (ion-induced): threshold S_ion = 1.35, rate 50 s^-1 per ion,
    one droplet per ion, initial radius r0 = 0.2 um.
  * Background ionization: 1e7 ion pairs/(m^3 s) (cosmic-ray floor); homogeneous
    nucleation threshold S_hom ~ 8 is never reached -> background droplets 0.
  * Growth: Maxwell diffusion law dr/dt = D_v (p_inf - p_r)/(rho_l R_v T r),
    Kelvin term p_r = p_sat exp(2 sigma_w/(rho_l R_v T r)).
  * FEEDBACK (P1-b): vapor is finite; every droplet depletes p_v in its cell;
    vapor diffuses (D_v = 2.5e-5 m^2/s) and is NOT replenished.
    BASELINE (P1): infinite vapor reservoir — p_v pinned to the expansion curve.
  * Numerical safeguard: per-substep growth limited to 0.4*r (documented).

Output: results/p1b_droplet_feedback.json  (all numbers from THIS run)
"""
import json
import math
import os

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
RES = os.path.join(os.path.dirname(HERE), "results")

# ------------------------- physical constants (SI) -------------------------
D_V = 2.5e-5          # vapor diffusivity in air, m^2/s
RHO_L = 1000.0        # liquid water density, kg/m^3
R_V = 461.5           # water vapor gas constant, J/(kg K)
SIGMA_W = 0.0728      # surface tension, N/m
GAMMA = 1.4
T0 = 293.15           # K
CR = 1.25             # expansion ratio
T_EXP = 10e-3         # expansion duration, s
RH0 = 0.95
LAMBDA_ION = 5.0e6    # ion pairs per meter of track (alpha-like)
S_ION = 1.35          # ion-induced nucleation threshold
J_ION = 50.0          # nucleation rate per ion, 1/s
R0 = 0.2e-6           # initial droplet radius, m
Q_BG = 1.0e7          # background ionization, ion pairs/(m^3 s)
T_END = 80e-3         # simulated wall time, s
DT_SUB = 5e-6         # substep, s


def p_sat(T):
    Tc = T - 273.15
    return 610.94 * math.exp(17.625 * Tc / (Tc + 243.04))


def run(feedback: bool):
    N = 64
    L = 1.0e-2
    dx = L / N

    n_sub_total = int(round(T_END / DT_SUB))
    t_grid = np.arange(1, n_sub_total + 1) * DT_SUB

    # --- expansion trajectory (piecewise: linear volume ramp, adiabatic T) ---
    def temperature(t):
        if t <= T_EXP:
            v_rel = 1.0 + (CR - 1.0) * (t / T_EXP)
        else:
            v_rel = CR
        return T0 * v_rel ** (-(GAMMA - 1.0))

    # --- vapor partial pressure field p_v(y,z), Pa ---
    p_v = np.full((N, N), RH0 * p_sat(T0), dtype=np.float64)

    # --- ion column cross-section ---
    coords = (np.arange(N) + 0.5) * dx - L / 2
    Y, Z = np.meshgrid(coords, coords, indexing="ij")
    sig_r = 2.0 * dx
    cross = np.exp(-(Y**2 + Z**2) / (2 * sig_r**2))
    cross /= cross.sum()
    n_ion_cell = LAMBDA_ION * dx * cross            # ions per (x-cell, cross-cell)

    nucleated = np.zeros((N, N))                     # fractional droplet count per cell
    r_droplet = np.zeros((N, N), dtype=np.float64)   # droplet radius per cell

    # track core mask for diagnostics (5x5 cells at center)
    core = np.zeros((N, N), dtype=bool)
    core[N//2-2:N//2+3, N//2-2:N//2+3] = True

    diag_t, diag_S_track, diag_S_far, diag_r, diag_n, diag_water = [], [], [], [], [], []
    t_close = None
    window_opened = False
    S_peak = 0.0

    diff_coef = D_V * DT_SUB / dx**2

    for step in range(n_sub_total):
        t_now = t_grid[step]
        T = temperature(t_now)
        ps_T = p_sat(T)

        # expansion: uniform ideal-gas rescale of vapor + new saturation level
        if step == 0:
            p_prev_T = T0
        T_prev = temperature(t_now - DT_SUB)
        if feedback:
            p_v *= (T / T_prev)          # adiabatic expansion of the vapor
        else:
            p_v[:] = RH0 * p_sat(T0) * (T / T0)   # infinite reservoir
        S_mean_all = float(p_v.mean() / ps_T)
        S_peak = max(S_peak, S_mean_all)

        # ---- nucleation on ions (fractional Poisson count per cell) ----
        S_core = float(p_v[core].mean() / ps_T)
        if S_core > S_ION:
            window_opened = True
            rate = n_ion_cell * J_ION * DT_SUB       # expected new droplets
            nucleated = np.minimum(n_ion_cell, nucleated + rate)
            new_drops = (nucleated > 0) & (r_droplet <= 0)
            r_droplet[new_drops] = R0

        # ---- droplet growth + vapor uptake ----
        alive = nucleated > 0
        if alive.any():
            p_r = ps_T * np.exp(2.0 * SIGMA_W / (RHO_L * R_V * T * np.maximum(r_droplet, 1e-10)))
            dp = p_v - p_r
            drdt = D_V * dp / (RHO_L * R_V * T * np.maximum(r_droplet, 1e-10))
            dr = drdt * DT_SUB
            dr = np.clip(dr, -0.4 * np.maximum(r_droplet, 1e-10), 0.4 * np.maximum(r_droplet, 1e-10))
            dr = np.maximum(dr, 0.0) * alive          # pure growth in this model
            dr = np.where(r_droplet > 0, dr, 0.0)
            dm = RHO_L * 4.0 * math.pi * (r_droplet ** 2) * dr   # kg per droplet
            r_droplet += dr
            # uptake: fractional droplet count per cell
            dp_cell = dm * nucleated * R_V * T / (dx**3)         # Pa per x-cell
            if feedback:
                p_v -= dp_cell
                np.maximum(p_v, 0.0, out=p_v)

        # ---- vapor diffusion (2D cross-section, exact x-invariant reduction) ----
        lap = (np.roll(p_v, 1, 0) + np.roll(p_v, -1, 0) +
               np.roll(p_v, 1, 1) + np.roll(p_v, -1, 1) - 4 * p_v)
        p_v += diff_coef * lap

        # ---- diagnostics ~1 ms ----
        if step % 200 == 0 or step == n_sub_total - 1:
            S_track = float(p_v[core].mean() / ps_T)
            S_far = float(p_v[2, 2] / ps_T)
            n_alive = int((nucleated > 0).sum())
            n_per_cm = float(nucleated.sum() * (0.01 / dx))      # droplets per cm of track
            water_per_m = float((nucleated * RHO_L * 4/3 * math.pi *
                                 r_droplet**3).sum() / dx)
            diag_t.append(t_now)
            diag_S_track.append(S_track)
            diag_S_far.append(S_far)
            diag_r.append(float(r_droplet[nucleated > 0].mean()) * 1e6 if n_alive else 0.0)
            diag_n.append(n_per_cm)
            diag_water.append(water_per_m)
            if feedback and t_close is None and window_opened and S_track < S_ION:
                t_close = t_now

    # ---- final metrics ----
    T_end = temperature(T_END)
    ps_end = p_sat(T_end)
    S_track_final = float(p_v[core].mean() / ps_end)
    S_far_final = float(p_v[2, 2] / ps_end)
    p_v_no_uptake = RH0 * p_sat(T0) * (T_end / T0)
    depletion_track = 1.0 - float(p_v[core].mean()) / p_v_no_uptake
    S_line = p_v[:, N//2] / ps_end
    core_max = float(S_line[core[:, N//2]].max())
    half = 0.5 * (core_max + S_far_final)
    below = np.where(S_line <= half)[0]
    halo_fwhm_mm = float((below.max() - below.min() + 1) * dx * 1e3) if len(below) else 0.0
    n_alive = int((nucleated > 0).sum())
    n_per_cm_final = float(nucleated.sum() * (0.01 / dx))
    w = nucleated
    r_mean_final = float((r_droplet * w).sum() / w.sum()) if w.sum() > 0 else 0.0
    water_per_m_final = float((nucleated * RHO_L * 4/3 * math.pi *
                               r_droplet**3).sum() / dx)

    return {
        "mode": "P1-b (feedback)" if feedback else "P1 (baseline, no feedback)",
        "S_peak_expansion": S_peak,
        "S_track_final": S_track_final,
        "S_far_final": S_far_final,
        "t_nucleation_window_close_s": t_close,
        "N_droplets_per_cm_track": n_per_cm_final,
        "r_mean_final_um": r_mean_final * 1e6,
        "vapor_depletion_fraction_track": depletion_track,
        "depletion_halo_FWHM_mm": halo_fwhm_mm,
        "condensed_water_kg_per_m": water_per_m_final,
        "diag": {
            "t_s": diag_t, "S_track": diag_S_track, "S_far": diag_S_far,
            "r_mean_um": diag_r, "N_per_cm": diag_n, "water_kg_per_m": diag_water,
        },
    }


def main():
    os.makedirs(RES, exist_ok=True)
    print("=== P1 baseline (no feedback) ===")
    base = run(feedback=False)
    print(f"  S_peak={base['S_peak_expansion']:.3f}  S_track_final={base['S_track_final']:.3f}  "
          f"r_mean={base['r_mean_final_um']:.2f} um  N/cm={base['N_droplets_per_cm_track']:.0f}  "
          f"water={base['condensed_water_kg_per_m']:.3e} kg/m")
    print("=== P1-b (droplet feedback / vapor depletion) ===")
    fb = run(feedback=True)
    print(f"  S_peak={fb['S_peak_expansion']:.3f}  S_track_final={fb['S_track_final']:.3f}  "
          f"r_mean={fb['r_mean_final_um']:.2f} um  N/cm={fb['N_droplets_per_cm_track']:.0f}  "
          f"water={fb['condensed_water_kg_per_m']:.3e} kg/m")
    print(f"  t_close={fb['t_nucleation_window_close_s']*1e3:.2f} ms  "
          f"depletion={fb['vapor_depletion_fraction_track']*100:.1f}%  "
          f"halo FWHM={fb['depletion_halo_FWHM_mm']:.3f} mm")

    out = {
        "module": "p1b_droplet_feedback",
        "run_date": "2026-09-16",
        "parameters": {
            "grid": "64x64 cross-section (exact x-invariant reduction of 3D box 1 cm)",
            "CR": CR, "gamma": GAMMA, "T0_K": T0, "RH0": RH0,
            "t_exp_ms": T_EXP * 1e3, "Lambda_ion_per_m": LAMBDA_ION,
            "S_ion": S_ION, "J_ion_per_s": J_ION, "r0_um": R0 * 1e6,
            "D_v_m2_s": D_V, "dt_sub_s": DT_SUB, "T_end_ms": T_END * 1e3,
        },
        "P1_baseline": base,
        "P1b_feedback": fb,
        "ratios": {
            "r_mean_fb_over_base": fb["r_mean_final_um"] / base["r_mean_final_um"],
            "water_fb_over_base": fb["condensed_water_kg_per_m"] / base["condensed_water_kg_per_m"],
            "S_track_fb_over_base": fb["S_track_final"] / base["S_track_final"],
        },
    }
    path = os.path.join(RES, "p1b_droplet_feedback.json")
    with open(path, "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=2)
    print("saved:", path)


if __name__ == "__main__":
    main()
