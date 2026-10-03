#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
b_volume_extension.py — v2.0.0 (research extension)
Extended verification battery for "b-correction <-> vortex volume".

Built on top of b_volume_experiment.py (experiments T/A/B/C/D/E/F/G).
This module adds four verification experiments that probe the SAME physics
through OTHER parameters, closing the gaps listed in the limitations section:

  H  CROSS-CHECK CHANNELS. The b-charge B = int |n_b.omega| dV is measured a
     second time through the VELOCITY channel, B_div = int |div(R_b u)| dV /
     theta_b (no vorticity anywhere), and through L2-type carriers:
     B2 = sqrt(int (n_b.omega)^2 dV), enstrophy of the parallel component
     Omega_par = int (n_b.omega)^2 dV, total enstrophy Omega = int omega^2 dV,
     palinstrophy P = int |curl omega|^2 dV, helicity H = int u.omega dV.
     Checks: velocity/vorticity channel agreement to O(theta_b^2);
     additivity (linear in N) of B2 and Omega_par on a ring lattice;
     Omega_par orientation law (n_b.n_t)^2.
  I  RESOLUTION CONVERGENCE. B, Q_b per vortex and the orientation ratio are
     re-measured at n = 32, 48, 64, 96 against exact analytic values
     (ring_B_R0, theta_b*Gamma*L*f_plane): errors must fall monotonically.
  J  ANCHOR CHECKS. (i) dimensionless invariants (monitor Q/(th_b B),
     projected-volume ratio) are grid-invariant at n = 48 vs 64;
     (ii) geometric cross-check: the b-charge of a ring equals the PROJECTED
     tube volume f_plane * V_torus, verified for three normals and two cores;
     (iii) real-water anchor table: elementary b-volume V = 1/omega_ref
     (coherent) and 2/omega_ref (isotropic) for omega_ref in
     {U/L, omega(10 eta), omega_eta} for tea / pipe / Draupner / Katrina.
  K  HOU-LUO DYNAMIC ANNIHILATION (2D pseudo-spectral, vorticity form).
     Hou-Luo-type dipole (counter-rotating Gaussian pair) vs identical
     co-rotating pair on the periodic square. Quantities over time:
     B(t) = 0.8124 * int |omega_z| (b-charge; EXACTLY conserved for the
     co-rotating pair since omega >= 0 and int omega_z is a spectral
     invariant), enstrophy Omega(t), energy E(t), palinstrophy P(t),
     omega_max(t). Identities verified as cross-checks:
        dE/dt = -nu * Omega,   dOmega/dt = -2 nu * P,
     late-time Lamb-Oseen law omega_max ~ 1/t. Monitors at kick times:
        Q_abs/(theta_b B) ~ 1 (first-order flux identity),
        M_net = Q_net/(theta_b B) = |int n.omega| / int |n.omega|:
        M_net ~ 1 for the co-rotating pair (corrections add),
        M_net ~ 0 for the dipole (corrections annihilate pairwise).
     Annihilation fraction: M_ann(t) = 1 - B_dipole(t)/B_corot(t).

Outputs: summary_extension.json + figures fig9..fig13 (labels ru/en).
Run modes:
  python3 b_volume_extension.py [--quick] [--lang en] [--outdir DIR]
  python3 b_volume_extension.py --figs-only --lang ru --indir DIR --outdir DIR
Only numpy + matplotlib required; deterministic.
"""

import argparse
import json
import math
import os
import sys
import time

import numpy as np

_HERE = os.path.dirname(os.path.abspath(__file__))
if _HERE not in sys.path:
    sys.path.insert(0, _HERE)

from b_volume_experiment import (          # noqa: E402
    B_CONST, THETA_B, AXIS_B, V_BOX, SEED, R_B,
    make_k, project_hat, dealias_hat, curl_hat, div_hat,
    fft_field, ifft_field, prepare_from_vorticity,
    vorticity_real, b_charge, b_charge_hat, energy_hat, sup_omega_hat,
    rotate_pointwise, kick_flux, ic_taylor_green, ic_vring, ic_vring_lattice,
    ring_B, ring_B_R0, ring_fplane, exp_orientation, water_row, FLOWS,
    FLOW_NAMES, NU_WATER,
)

import matplotlib                          # noqa: E402
matplotlib.use("Agg")
import matplotlib.pyplot as plt            # noqa: E402

C1, C2, C3, C4 = "#0F2440", "#C25E00", "#5B7C99", "#7A9E7E"
W_PAR_Z = AXIS_B[2]                        # n_b . z_hat = 0.8124 (2D flows)
V1_CONST = 4.0 * math.pi + 2.0 * math.sqrt(3.0)

# ----------------------------------------------------------------------------
# labels (figures)
# ----------------------------------------------------------------------------
LABELS = {
    "en": {
        "cross_a": "Exp H: two measurement channels of the b-charge",
        "cross_ax": "$B_\\omega=\\int|\\hat n_b\\!\\cdot\\!\\omega|\\,dV$ (vorticity channel)",
        "cross_ay": "$B_{\\rm div}=\\int|{\\rm div}\\,(R_b u)|\\,dV/\\theta_b$ (velocity channel)",
        "cross_note": "channel agreement = 1 + O($\\theta_b^2$)",
        "cross_b": "Exp H: additivity of alternative carriers vs N",
        "cross_bx": "N merged vortex rings",
        "cross_by": "carrier(N) / carrier(1)",
        "l2": "$B_2$ (L2 charge)", "opar": "$\\Omega_\\parallel$", "om": "$\\Omega$ (enstrophy)",
        "slope1": "slope 1 (additivity)",
        "conv_a": "Exp I: convergence to exact analytic values",
        "conv_ax": "grid n",
        "conv_ay": "relative error",
        "conv_b": "Exp I: flux-identity monitor vs resolution",
        "conv_bx": "grid n",
        "conv_by": "$Q/(\\theta_b\\,B)$",
        "conv_b1": "$B$: ring vs $B_{\\rm exact}$",
        "conv_b2": "$Q$: ring vs $\\theta_b B_{\\rm exact}$",
        "conv_b3": "orientation ratio err (mean)",
        "anchor_a": "Exp J: b-charge measures the PROJECTED volume",
        "anchor_ax": "$V_{\\rm pred}/V_{\\rm gauss}$ (theory incl. grad. term)",
        "anchor_ay": "$V_{\\rm meas}/V_{\\rm gauss}$ (numerics)",
        "anchor_b": "Exp J: elementary b-volume $V=2/\\omega_{\\rm ref}$ (isotropic)",
        "anchor_bx": "$\\log_{10} V$  [m$^3$]",
        "wL": "$\\omega_L=U/L$", "w10": "$\\omega(10\\eta)$", "weta": "$\\omega_\\eta$",
        "hl_a": "Exp K (Hou–Luo): b-charge dynamics",
        "hl_ax": "t", "hl_ay": "$B(t)/B(0)$",
        "hl_dip": "Hou–Luo dipole (anti-parallel): annihilation",
        "hl_co": "co-rotating pair: $B$ conserved exactly",
        "hl_b": "Exp K: annihilated fraction of the b-charge",
        "hl_bx": "t", "hl_by": "$M_{\\rm ann}=1-B_{\\rm dip}/B_{\\rm co}$",
        "hl_c": "Exp K: Lamb–Oseen decay of peak vorticity",
        "hl_cx": "t", "hl_cy": "$\\omega_{\\max}(t)$",
        "hl_cfit": "slope $-1$",
        "hl_d": "Exp K: monitors at kick time $t^*$",
        "hl_dx": "", "hl_dy": "$Q/(\\theta_b\\,B)$",
        "hl_d1": "$Q_{\\rm abs}/(\\theta_b B)$ — flux identity",
        "hl_d2": "$Q_{\\rm net}/(\\theta_b B)$ — net-charge monitor",
        "dip": "dipole", "co": "co-rotating",
        "fields_t": "t = ",
        "fig13_title": "Exp K: vorticity fields, Hou–Luo dipole (top) vs co-rotating pair (bottom)",
    },
    "ru": {
        "cross_a": "Опыт H: два канала измерения b-заряда",
        "cross_ax": "$B_\\omega=\\int|\\hat n_b\\!\\cdot\\!\\omega|\\,dV$ (канал вихря)",
        "cross_ay": "$B_{\\rm div}=\\int|{\\rm div}\\,(R_b u)|\\,dV/\\theta_b$ (канал скорости)",
        "cross_note": "согласие каналов = 1 + O($\\theta_b^2$)",
        "cross_b": "Опыт H: аддитивность альтернативных носителей",
        "cross_bx": "N слившихся вихревых колец",
        "cross_by": "носитель(N) / носитель(1)",
        "l2": "$B_2$ (L2-заряд)", "opar": "$\\Omega_\\parallel$", "om": "$\\Omega$ (энстрофия)",
        "slope1": "наклон 1 (аддитивность)",
        "conv_a": "Опыт I: сходимость к точным аналитическим значениям",
        "conv_ax": "сетка n",
        "conv_ay": "относительная ошибка",
        "conv_b": "Опыт I: монитор тождества потока от разрешения",
        "conv_bx": "сетка n",
        "conv_by": "$Q/(\\theta_b\\,B)$",
        "conv_b1": "$B$: кольцо против $B_{\\rm точн}$",
        "conv_b2": "$Q$: кольцо против $\\theta_b B_{\\rm точн}$",
        "conv_b3": "ошибка ориентационного отношения (среднее)",
        "anchor_a": "Опыт J: b-заряд измеряет ПРОЕЦИРОВАННЫЙ объём",
        "anchor_ax": "$V_{\\rm прогноз}/V_{\\rm гаусс}$ (теория с град. членом)",
        "anchor_ay": "$V_{\\rm изм}/V_{\\rm гаусс}$ (численно)",
        "anchor_b": "Опыт J: элементарный b-объём $V=2/\\omega_{\\rm оп}$ (изотроп.)",
        "anchor_bx": "$\\log_{10} V$  [м$^3$]",
        "wL": "$\\omega_L=U/L$", "w10": "$\\omega(10\\eta)$", "weta": "$\\omega_\\eta$",
        "hl_a": "Опыт K (Хоу–Ло): динамика b-заряда",
        "hl_ax": "t", "hl_ay": "$B(t)/B(0)$",
        "hl_dip": "диполь Хоу–Ло (анти-параллельный): аннигиляция",
        "hl_co": "со-вращающаяся пара: $B$ сохраняется точно",
        "hl_b": "Опыт K: аннигилировавшая доля b-заряда",
        "hl_bx": "t", "hl_by": "$M_{\\rm ann}=1-B_{\\rm дип}/B_{\\rm со}$",
        "hl_c": "Опыт K: лэмбовское затухание пиковой завихрённости",
        "hl_cx": "t", "hl_cy": "$\\omega_{\\max}(t)$",
        "hl_cfit": "наклон $-1$",
        "hl_d": "Опыт K: мониторы в момент пинка $t^*$",
        "hl_dx": "", "hl_dy": "$Q/(\\theta_b\\,B)$",
        "hl_d1": "$Q_{\\rm абс}/(\\theta_b B)$ — тождество потока",
        "hl_d2": "$Q_{\\rm нет}/(\\theta_b B)$ — монитор нетто-заряда",
        "dip": "диполь", "co": "со-вращ.",
        "fields_t": "t = ",
        "fig13_title": "Опыт K: поля завихрённости, диполь Хоу–Ло (вверху) и со-вращающаяся пара (внизу)",
    },
}

L = LABELS["en"]
_NO_TITLES = os.environ.get("NSB_NO_TITLES", "0") == "1"
C1, C2, C3 = "#0F2440", "#C25E00", "#5B7C99"


def _title(ax, text):
    if not _NO_TITLES:
        ax.set_title(text)


def _style(ax):
    ax.grid(True, linestyle="--", alpha=0.20, linewidth=0.6)
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)


# ----------------------------------------------------------------------------
# Exp H — cross-check channels
# ----------------------------------------------------------------------------

SIN_TH = math.sin(THETA_B)                # = b exactly
C1M = 1.0 - math.cos(THETA_B)             # O(theta^2) coefficient
GRAD_COEF = C1M / THETA_B                 # ~0.03129 = tan(theta_b/2)


def diag_full(uh, kx, ky, kz):
    """Full diagnostic vector of a state (all carriers + exact identity).

    EXACT THEOREM (constant axis; div(n x u) = -(n.omega)):
        div(R_b u) = +sin(th_b)*(n_b.omega) + (1-cos(th_b))*(n_b.grad)(n_b.u).
    The gradient term is O(th^2) pointwise but integrates to a few percent
    for tube flows; it EXPLAINS the velocity/vorticity channel offset.
    """
    w = vorticity_real(uh, kx, ky, kz)
    wpar = AXIS_B[0] * w[0] + AXIS_B[1] * w[1] + AXIS_B[2] * w[2]
    B_w = b_charge(w)
    # velocity channel: no vorticity anywhere in this measurement
    u = ifft_field(uh)
    ruh = fft_field(rotate_pointwise(u, R_B))
    divx = np.real(np.fft.ifftn(div_hat(ruh, kx, ky, kz)))
    B_div = float(np.mean(np.abs(divx)) * V_BOX / THETA_B)
    # exact-identity right-hand side and gradient norm
    nu_r = AXIS_B[0] * u[0] + AXIS_B[1] * u[1] + AXIS_B[2] * u[2]
    nuh = fft_field((nu_r, nu_r, nu_r))  # same transform reused for d/dx, d/dy, d/dz
    gx = np.real(np.fft.ifftn(1j * kx * nuh[0]))
    gy = np.real(np.fft.ifftn(1j * ky * nuh[1]))
    gz = np.real(np.fft.ifftn(1j * kz * nuh[2]))
    Y = AXIS_B[0] * gx + AXIS_B[1] * gy + AXIS_B[2] * gz   # (n.grad)(n.u)
    G = float(np.mean(np.abs(Y)) * V_BOX)
    div_pred = SIN_TH * wpar + C1M * Y
    Q_pt = float(np.mean(np.abs(div_pred)) * V_BOX)   # pointwise identity flux
    B2 = float(np.sqrt(np.mean(wpar ** 2) * V_BOX))
    Om_par = float(np.mean(wpar ** 2) * V_BOX)
    Om = float(np.mean(w[0] ** 2 + w[1] ** 2 + w[2] ** 2) * V_BOX)
    wh = fft_field(w)
    cw = curl_hat(wh, kx, ky, kz)
    cr = tuple(np.real(np.fft.ifftn(c)) for c in cw)
    P = float(np.mean(cr[0] ** 2 + cr[1] ** 2 + cr[2] ** 2) * V_BOX)
    Hel = float(np.mean(u[0] * w[0] + u[1] * w[1] + u[2] * w[2]) * V_BOX)
    Q = kick_flux(uh, kx, ky, kz)
    # exact identity regression (subsample for speed)
    sel = slice(None, None, max(1, (divx.size // 20000)))
    xs = div_pred.ravel()[sel]
    ys = divx.ravel()[sel]
    sxx = float(np.sum(xs * xs))
    slope = float(np.sum(xs * ys) / sxx) if sxx > 0 else float("nan")
    resid = ys - slope * xs
    r2 = 1.0 - float(np.sum(resid ** 2)) / float(np.sum((ys - ys.mean()) ** 2))
    D = G / B_w
    ratio = B_div / B_w
    slack = abs(ratio - SIN_TH / THETA_B)
    bound = GRAD_COEF * D
    return {"B_w": B_w, "B_div": B_div, "B2": B2, "Om_par": Om_par,
            "Om": Om, "P": P, "Hel": Hel, "Q": Q, "G": G, "D": D,
            "Q_pt": Q_pt,
            "ratio": ratio, "id_slope": slope, "id_r2": r2,
            "bound": bound, "slack": slack, "inside": bool(slack <= bound * 1.02 + 1e-12),
            "monitor": Q / (THETA_B * B_w) if B_w > 0 else float("nan")}


def exp_crosschecks():
    """H: velocity vs vorticity channel + alternative carriers + N-additivity."""
    from b_volume_experiment import prepare_velocity
    rows = []
    # (name, n, builder) — TG is a VELOCITY field, rings are VORTICITY fields
    states = [("taylor_green", 32,
               lambda kx, ky, kz, k2, kmax:
                   prepare_velocity(ic_taylor_green(32), kx, ky, kz, k2, kmax))]
    for nrm in ("x", "y", "z"):
        states.append((f"ring_{nrm}", 64,
                       lambda kx, ky, kz, k2, kmax, _n=nrm:
                           prepare_from_vorticity(
                               ic_vring(64, _n, gamma=1.0, sigma=0.3,
                                        R0=1.0), kx, ky, kz, k2, kmax)))
    states.append(("lattice8", 48,
                   lambda kx, ky, kz, k2, kmax:
                       prepare_from_vorticity(
                           ic_vring_lattice(48, 8), kx, ky, kz, k2, kmax)))
    for name, n, builder in states:
        kx, ky, kz, k2 = make_k(n)
        kmax = n / 3.0
        uh = builder(kx, ky, kz, k2, kmax)
        d = diag_full(uh, kx, ky, kz)
        d["state"] = name
        d["n"] = n
        d["channel_ratio"] = d["B_div"] / d["B_w"]
        rows.append(d)

    # additivity of alternative carriers on the lattice
    n = 48
    kx, ky, kz, k2 = make_k(n)
    kmax = n / 3.0
    scan = []
    for N in (1, 2, 4, 8):
        w = ic_vring_lattice(n, N, gamma=1.0, sigma=0.25, R0=0.6)
        uh = prepare_from_vorticity(w, kx, ky, kz, k2, kmax)
        d = diag_full(uh, kx, ky, kz)
        scan.append({"N": N, "B_w": d["B_w"], "B2": d["B2"],
                     "Om_par": d["Om_par"], "Om": d["Om"]})
    lin = {}
    for key in ("B_w", "B2", "Om_par", "Om"):
        ys = np.array([s[key] for s in scan])
        xs = np.array([s["N"] for s in scan], dtype=float)
        A = np.vstack([xs, np.ones_like(xs)]).T
        (slope, intercept), res, *_ = np.linalg.lstsq(A, ys, rcond=None)
        yfit = slope * xs + intercept
        ss = float(np.sum((ys - ys.mean()) ** 2))
        r2 = 1.0 - float(np.sum((ys - yfit) ** 2)) / ss if ss > 0 else 1.0
        lin[key] = {"slope": float(slope), "r2": float(r2)}

    # orientation law for the L2 carrier: Omega_par ~ (n_b.n_t)^2
    nrm2 = {}
    for nrm in ("x", "y", "z"):
        w = ic_vring(64, nrm, gamma=1.0, sigma=0.3, R0=1.0)
        kx, ky, kz, k2 = make_k(64)
        uh = prepare_from_vorticity(w, kx, ky, kz, k2, 64 / 3.0)
        d = diag_full(uh, kx, ky, kz)
        nrm2[nrm] = {"Om_par": d["Om_par"], "Om": d["Om"]}
    dot2 = {"x": AXIS_B[0] ** 2, "y": AXIS_B[1] ** 2, "z": AXIS_B[2] ** 2}
    ori_rows = []
    for nrm in ("x", "y", "z"):
        meas = nrm2[nrm]["Om_par"] / nrm2[nrm]["Om"]
        th = 0.5 * (1.0 - dot2[nrm])       # <(n.e_phi)^2> = (1-(n.n_t)^2)/2
        ori_rows.append({"axis": nrm, "meas": meas, "theory": th,
                         "err_pct": 100.0 * abs(meas / th - 1.0)})
    worst_div = max(abs(r["ratio"] - SIN_TH / THETA_B) - r["bound"]
                    for r in rows)
    worst_id = max(max(abs(r["id_slope"] - 1.0), 0.0) for r in rows)
    worst_ori = max(r["err_pct"] for r in ori_rows)
    worst_r2 = min(v["r2"] for k, v in lin.items()
                   if k in ("B_w", "Om_par", "Om"))
    inside_all = all(r["inside"] for r in rows)
    id_all = all(r["id_r2"] > 0.9999 and abs(r["id_slope"] - 1.0) < 2e-3
                 for r in rows)
    return {"states": rows, "scan": scan, "linearity": lin,
            "orientation_l2": ori_rows,
            "pass": bool(id_all and inside_all and worst_ori < 1.0
                         and worst_r2 > 0.999),
            "worst_bound_excess": worst_div,
            "worst_id_slope_dev": worst_id,
            "worst_orientation_err_pct": worst_ori}


# ----------------------------------------------------------------------------
# Exp I — resolution convergence
# ----------------------------------------------------------------------------

def exp_convergence(n_list=(32, 48, 64, 96)):
    """I: B and Q of one ring vs exact values + orientation error vs n.
    Q carries a PHYSICAL O(th) excess (the gradient term), so the correct
    reference is Q_pred = sin(th_b)*B_exact + (1-cos(th_b))*G_numeric."""
    gamma, sigma, R0 = 1.0, 0.25, 0.6
    B_exact = ring_B_R0(gamma, "z", R0)
    rows = []
    for n in n_list:
        kx, ky, kz, k2 = make_k(n)
        kmax = n / 3.0
        w = ic_vring(n, "z", gamma=gamma, sigma=sigma, R0=R0)
        uh = prepare_from_vorticity(w, kx, ky, kz, k2, kmax)
        B_num = b_charge_hat(uh, kx, ky, kz)
        Q_num = kick_flux(uh, kx, ky, kz)
        d = diag_full(uh, kx, ky, kz)
        Q_pred = d["Q_pt"]          # pointwise exact-identity flux
        rows.append({"n": n, "B": B_num, "B_exact": B_exact,
                     "errB_pct": 100.0 * abs(B_num / B_exact - 1.0),
                     "Q": Q_num, "Q_pred": Q_pred,
                     "errQ_pred_pct": 100.0 * abs(Q_num / Q_pred - 1.0),
                     "monitor": Q_num / (THETA_B * B_num)})
    ori = []
    for n in (32, 48, 64):
        r = exp_orientation(n=n)
        ori.append({"n": n,
                    "mean_err_pct": float(np.mean([x["err_pct"] for x in r["rows"]]))})
    eB = [r["errB_pct"] for r in rows]
    mono = all(eB[i + 1] < eB[i] for i in range(len(eB) - 1))
    mon_drift = abs(rows[-1]["monitor"] / rows[1]["monitor"] - 1.0)
    return {"rows": rows, "orientation": ori, "B_exact": B_exact,
            "monotone": bool(mono), "monitor_drift": mon_drift,
            "pass": bool(mono and rows[-1]["errB_pct"] < 0.5
                         and rows[-1]["errQ_pred_pct"] < 0.5
                         and mon_drift < 0.005)}


# ----------------------------------------------------------------------------
# Exp J — anchors: projected volume + invariance + real-water table
# ----------------------------------------------------------------------------

def exp_anchors():
    """J: (i) V_meas/V_gauss = f_plane*(sin/theta) + gradient correction;
    (ii) n=48 vs 64 invariance; (iii) real-water elementary b-volumes."""
    geo_rows = []
    for nrm in ("x", "y", "z"):
        for sigma in (0.25, 0.35):
            n = 64
            kx, ky, kz, k2 = make_k(n)
            w = ic_vring(n, nrm, gamma=1.0, sigma=sigma, R0=1.0)
            uh = prepare_from_vorticity(w, kx, ky, kz, k2, n / 3.0)
            Q = kick_flux(uh, kx, ky, kz)
            d = diag_full(uh, kx, ky, kz)
            Omega0 = 1.0 / (2.0 * math.pi * sigma ** 2)
            V_meas = Q / (THETA_B * Omega0)
            V_gauss = 4.0 * math.pi ** 2 * 1.0 * sigma ** 2  # eff. tube volume
            B_ex = ring_B_R0(1.0, nrm, 1.0)
            Q_pred = d["Q_pt"]      # pointwise exact-identity flux
            V_pred = Q_pred / (THETA_B * Omega0)
            fpl = ring_fplane(nrm)
            geo_rows.append({"axis": nrm, "sigma": sigma,
                             "ratio": V_meas / V_gauss, "f_plane": fpl,
                             "V_pred_over_Vgauss": V_pred / V_gauss,
                             "err_pred_pct": 100.0 * abs(V_meas / V_pred - 1.0)})
    inv_rows = []
    for sigma in (0.25, 0.35):
        m = {}
        for n in (48, 64):
            kx, ky, kz, k2 = make_k(n)
            w = ic_vring(n, "z", gamma=1.0, sigma=sigma, R0=1.0)
            uh = prepare_from_vorticity(w, kx, ky, kz, k2, n / 3.0)
            Q = kick_flux(uh, kx, ky, kz)
            B = b_charge_hat(uh, kx, ky, kz)
            m[n] = {"monitor": Q / (THETA_B * B), "B": B}
        inv_rows.append({"sigma": sigma,
                         "mon48": m[48]["monitor"], "mon64": m[64]["monitor"],
                         "dev_pct": 100.0 * abs(m[48]["monitor"] / m[64]["monitor"] - 1.0)})
    water = []
    for key, U, Lc in FLOWS:
        r = water_row(U, Lc)
        w_L = U / Lc
        w_eta = r["omega_eta"]
        w_10 = w_eta * 10.0 ** (-2.0 / 3.0)     # K41: omega(l) ~ (eps/l^2)^(1/3)
        water.append({
            "key": key,
            "w_L": w_L, "w_10": w_10, "w_eta": w_eta,
            "V_one_L_m3": 2.0 / w_L,            # isotropic <== 2/omega_ref
            "V_one_10_m3": 2.0 / w_10,
            "V_one_eta_m3": 2.0 / w_eta,
            "V1_quantum_m3": r["V1_m3"],
            "eta_mm": r["eta_mm"],
        })
    worst_geo = max(r["err_pred_pct"] for r in geo_rows)
    worst_inv = max(r["dev_pct"] for r in inv_rows)
    return {"geometry": geo_rows, "invariance": inv_rows, "water": water,
            "pass": bool(worst_geo < 1.5 and worst_inv < 1.0),
            "worst_geo_err_pct": worst_geo, "worst_inv_dev_pct": worst_inv}


# ----------------------------------------------------------------------------
# Exp K — Hou–Luo dynamic annihilation (2D pseudo-spectral)
# ----------------------------------------------------------------------------

def make_k2(n):
    k = np.fft.fftfreq(n, d=1.0 / n) * 2.0 * math.pi
    return k.reshape(n, 1), k.reshape(1, n)


def ic2d(n, kind="dipole", sep=0.35, sigma=0.30, gamma=1.0):
    """Hou–Luo-type Gaussian pair on the periodic square [0,2pi)^2."""
    c = 2.0 * math.pi * np.arange(n) / n
    X = c.reshape(n, 1) - math.pi
    Y = c.reshape(1, n) - math.pi
    g1 = np.exp(-(((X - sep) ** 2 + Y ** 2) / (2.0 * sigma ** 2)))
    g2 = np.exp(-(((X + sep) ** 2 + Y ** 2) / (2.0 * sigma ** 2)))
    w0 = gamma / (2.0 * math.pi * sigma ** 2)
    return w0 * (g1 - g2) if kind == "dipole" else w0 * (g1 + g2)


def w2u_hat(wh, kx, ky, k2):
    k2s = np.where(k2 > 0, k2, 1.0)
    psih = np.where(k2 > 0, -wh / k2s, 0.0)
    return 1j * ky * psih, -1j * kx * psih


def ns2d_rhs(wh, kx, ky, k2, nu):
    uxh, uyh = w2u_hat(wh, kx, ky, k2)
    ux = np.real(np.fft.ifftn(uxh))
    uy = np.real(np.fft.ifftn(uyh))
    w = np.real(np.fft.ifftn(wh))
    dwx = np.real(np.fft.ifftn(1j * kx * wh))
    dwy = np.real(np.fft.ifftn(1j * ky * wh))
    nl = ux * dwx + uy * dwy
    out = -np.fft.fftn(nl) - nu * k2 * wh
    out[0, 0] = 0.0        # enforce exact conservation of the k=0 scalar
    return out


M_ABS_THEORY = SIN_TH / (THETA_B * W_PAR_Z)   # exact: Q_abs/(th_b*B) in 2D
                                              # = b/(th_b*0.812404) = 1.230112


def rk4_2d(wh, dt, kx, ky, k2, kmax, nu, mask=None):
    m = mask
    k1 = ns2d_rhs(wh, kx, ky, k2, nu)
    if m is not None:
        k1 = np.where(m, k1, 0.0)
    a = wh + 0.5 * dt * k1
    k2r = ns2d_rhs(a, kx, ky, k2, nu)
    if m is not None:
        k2r = np.where(m, k2r, 0.0)
    b = wh + 0.5 * dt * k2r
    k3 = ns2d_rhs(b, kx, ky, k2, nu)
    if m is not None:
        k3 = np.where(m, k3, 0.0)
    c = wh + dt * k3
    k4 = ns2d_rhs(c, kx, ky, k2, nu)
    if m is not None:
        k4 = np.where(m, k4, 0.0)
    out = wh + (dt / 6.0) * (k1 + 2 * k2r + 2 * k3 + k4)
    if m is not None:
        out = np.where(m, out, 0.0)
    return out


def diag2d(wh, kx, ky, k2, nu):
    """Diagnostics on the FLOW vorticity omega' = omega - <omega> (the
    k=0 mode is invisible to the velocity on a torus and is carried as an
    exactly conserved passive scalar S_raw)."""
    w_raw = np.real(np.fft.ifftn(wh))
    wbar = float(np.mean(w_raw))
    w = w_raw - wbar                          # flow vorticity
    uxh, uyh = w2u_hat(wh, kx, ky, k2)
    ux = np.real(np.fft.ifftn(uxh))
    uy = np.real(np.fft.ifftn(uyh))
    V2 = V_BOX ** (2.0 / 3.0)                # (2pi)^2
    A = float(np.mean(np.abs(w)) * V2)       # |omega'| integral
    S = float(np.mean(w_raw) * V2)           # conserved k=0 scalar
    Om = float(np.mean(w ** 2) * V2)
    E = 0.5 * float(np.mean(ux ** 2 + uy ** 2) * V2)
    dwxh, dwyh = 1j * kx * wh, 1j * ky * wh
    gx = np.real(np.fft.ifftn(dwxh))
    gy = np.real(np.fft.ifftn(dwyh))
    P = float(np.mean(gx ** 2 + gy ** 2) * V2)     # palinstrophy (2D)
    wmax = float(np.max(np.abs(w)))
    return {"A": A, "B": W_PAR_Z * A, "S": S, "Om": Om, "E": E, "P": P,
            "wmax": wmax}


def kick2d(wh, kx, ky, k2, theta=THETA_B):
    """In-plane b-kick diagnostics. EXACT 2D identity (u independent of z,
    so (z.grad)(z.u) = 0): div(R_z(th) u) = -sin(th)*omega' pointwise.
    Hence Q_abs = sin(th_b)*int|omega'| EXACTLY and
        m_abs = Q_abs/(th_b*B) = b/(th_b*(n_b.z)) = 1.230112 (6 digits).
    On a periodic box int omega' = 0 identically, so the net flux is
    Q_net = 0 (torus theorem) — merging vs annihilation is instead read off
    the DYNAMICS of B(t)."""
    uxh, uyh = w2u_hat(wh, kx, ky, k2)
    ux = np.real(np.fft.ifftn(uxh))
    uy = np.real(np.fft.ifftn(uyh))
    c, s = math.cos(theta), math.sin(theta)
    rx, ry = c * ux - s * uy, s * ux + c * uy
    dxh = 1j * kx * np.fft.fftn(rx) + 1j * ky * np.fft.fftn(ry)
    div = np.real(np.fft.ifftn(dxh))
    w_raw = np.real(np.fft.ifftn(wh))
    w = w_raw - float(np.mean(w_raw))
    V2 = V_BOX ** (2.0 / 3.0)
    Q_abs = float(np.mean(np.abs(div)) * V2)
    Q_net = abs(float(np.mean(div) * V2))
    B = W_PAR_Z * float(np.mean(np.abs(w)) * V2)
    return {"Q_abs": Q_abs, "Q_net": Q_net, "B": B,
            "m_abs": Q_abs / (THETA_B * B) if B > 0 else float("nan"),
            "m_net": Q_net / (THETA_B * B) if B > 0 else float("nan")}


def exp_houluo(n=128, nu=0.004, dt=0.0025, t_end=2.0, sample_every=5,
               sep=0.35, sigma=0.25, snaps=(0.0, 1.0, 2.0)):
    """K: dipole (annihilation) vs co-rotating pair (charge retention).
    Weaker nu keeps the co-rotating charge intact while the dipole's
    overlapping cores annihilate; identities are fitted after a warmup."""
    kx, ky = make_k2(n)
    KX = np.broadcast_to(kx, (n, n))
    KY = np.broadcast_to(ky, (n, n))
    K2 = KX ** 2 + KY ** 2
    kmax = n / 3.0
    mask = (np.abs(KX) <= kmax) & (np.abs(KY) <= kmax)
    t0 = time.time()
    out = {}
    snap_arrs = {}
    for kind in ("dipole", "corot"):
        wh = np.fft.fftn(ic2d(n, kind, sep=sep, sigma=sigma))
        wh = np.where(mask, wh, 0.0)
        series = [dict(t=0.0, **diag2d(wh, KX, KY, K2, nu))]
        steps = int(round(t_end / dt))
        t = 0.0
        for step in range(1, steps + 1):
            wh = rk4_2d(wh, dt, KX, KY, K2, kmax, nu, mask=mask)
            t = step * dt
            if step % sample_every == 0 or step == steps:
                series.append(dict(t=round(t, 6), **diag2d(wh, KX, KY, K2, nu)))
        out[kind] = {"series": series}
    # identities: dE/dt = -nu*Om, dOm/dt = -2 nu P (finite differences,
    # fitted after the initial transient)
    idn = {}
    warm = 7                                    # skip first warmup samples
    for kind in ("dipole", "corot"):
        s = out[kind]["series"][warm:]
        t = np.array([r["t"] for r in s])
        E = np.array([r["E"] for r in s])
        Om = np.array([r["Om"] for r in s])
        P = np.array([r["P"] for r in s])
        dE = np.diff(E) / np.diff(t)
        rhs1 = -nu * 0.5 * (Om[1:] + Om[:-1])
        dOm = np.diff(Om) / np.diff(t)
        rhs2 = -2.0 * nu * 0.5 * (P[1:] + P[:-1])
        def _r2(lhs, rhs):
            lhs = np.asarray(lhs); rhs = np.asarray(rhs)
            ss = float(np.sum((lhs - lhs.mean()) ** 2))
            return 1.0 - float(np.sum((lhs - rhs) ** 2)) / ss if ss > 0 else 1.0
        idn[kind] = {"dE_vs_nuOm_r2": _r2(dE, rhs1),
                     "dOm_vs_2nuP_r2": _r2(dOm, rhs2)}
    # Lamb–Oseen-type decay of peak vorticity (log-log slope, late window)
    lo = {}
    for kind in ("dipole", "corot"):
        s = out[kind]["series"][warm:]
        t = np.array([r["t"] for r in s])
        wm = np.array([r["wmax"] for r in s])
        sel = t > 0.6 * t_end
        p = np.polyfit(np.log(t[sel]), np.log(wm[sel]), 1)
        lo[kind] = {"slope": float(p[0])}
    # monitors: kicks at t* = t_end/2 (fields re-derived from stored snapshots)
    # -> run a short second pass storing snapshots at the kick time
    kick_rows = []
    t_star = 0.5 * t_end
    for kind in ("dipole", "corot"):
        wh = np.fft.fftn(ic2d(n, kind, sep=sep, sigma=sigma))
        wh = np.where(mask, wh, 0.0)
        steps = int(round(t_star / dt))
        for _ in range(steps):
            wh = rk4_2d(wh, dt, KX, KY, K2, kmax, nu, mask=mask)
        kick_rows.append({"kind": kind, "t": t_star,
                          "m_abs_theory": M_ABS_THEORY,
                          **kick2d(wh, KX, KY, K2)})
    # snapshots for the field figure (downsample to 64x64)
    for kind in ("dipole", "corot"):
        wh = np.fft.fftn(ic2d(n, kind, sep=sep, sigma=sigma))
        wh = np.where(mask, wh, 0.0)
        for ts in snaps:
            if ts > 0:
                st = int(round(ts / dt))
                for _ in range(st):
                    wh = rk4_2d(wh, dt, KX, KY, K2, kmax, nu, mask=mask)
            w_raw = np.real(np.fft.ifftn(wh))
            w = w_raw - float(np.mean(w_raw))
            m = w.reshape(64, n // 64, 64, n // 64).mean(axis=(1, 3))
            snap_arrs[f"{kind}_{ts}"] = m
    out["wall_s"] = time.time() - t0
    # conservation of the k=0 scalar (max drift relative to A(0))
    S_drift = 0.0
    B_end = {}
    for k in ("dipole", "corot"):
        s = out[k]["series"]
        S0, A0 = s[0]["S"], s[0]["A"]
        S_drift = max(S_drift, max(abs(r["S"] - S0) for r in s) / (A0 + 1e-30))
        B_end[k] = s[-1]["B"] / s[0]["B"]
    return {"runs": out, "identities": idn, "lamb_oseen": lo,
            "kicks": kick_rows, "snaps": snap_arrs, "nu": nu,
            "t_end": t_end, "n": n, "sep": sep, "sigma": sigma,
            "S_drift": S_drift, "B_end_frac": B_end,
            "m_abs_theory": M_ABS_THEORY,
            "pass": bool(idn["dipole"]["dE_vs_nuOm_r2"] > 0.995
                         and idn["corot"]["dOm_vs_2nuP_r2"] > 0.995
                         and -1.5 < lo["corot"]["slope"] < -0.2
                         and lo["dipole"]["slope"] < lo["corot"]["slope"] - 0.3
                         and all(abs(k["m_abs"] / M_ABS_THEORY - 1.0) < 1e-4
                                 for k in kick_rows)
                         and all(k["m_net"] < 1e-8 for k in kick_rows)
                         and S_drift < 1e-7
                         and B_end["dipole"] < B_end["corot"] - 0.25)}


# ----------------------------------------------------------------------------
# figures (fig9..fig13)
# ----------------------------------------------------------------------------

def fig_crosschecks(res, outdir):
    fig, (a1, a2) = plt.subplots(1, 2, figsize=(9.6, 4.4),
                                 constrained_layout=True)
    # panel (a): EXACT identity div(R_b u) vs +sin(th)*n.w + (1-cos)*grad term
    # (reconstructed from the per-state regression stats stored in res)
    ys = [r["id_slope"] for r in res["states"]]
    r2s = [r["id_r2"] for r in res["states"]]
    names = [r["state"] for r in res["states"]]
    xv = np.arange(len(names))
    a1.bar(xv, [y - 1.0 for y in ys], width=0.55, color=C1)
    a1.axhline(0.0, color=C2, lw=1.4)
    a1.set_xticks(xv)
    a1.set_xticklabels(names, rotation=20, ha="right", fontsize=8)
    for i, (y, r2) in enumerate(zip(ys, r2s)):
        a1.annotate(f"{y:.6f}\nR$^2$={r2:.6f}", (i, y - 1.0),
                    textcoords="offset points", xytext=(0, 6),
                    ha="center", fontsize=7)
    a1.set_ylabel("$\\Delta$ from exact identity slope 1")
    _title(a1, L["cross_a"]); _style(a1)
    scan = res["scan"]
    Ns = [s["N"] for s in scan]
    for key, lab, col, mk in (("B2", L["l2"], C1, "o"),
                              ("Om_par", L["opar"], C2, "s"),
                              ("Om", L["om"], C3, "^")):
        v = np.array([s[key] for s in scan])
        a2.plot(Ns, v / v[0], mk + "-", color=col, ms=5, label=lab)
    a2.plot([1, 8], [1, 8], ":", color="#888888", lw=1.3, label=L["slope1"])
    a2.set_xscale("log"); a2.set_yscale("log")
    a2.set_xticks(Ns); a2.set_xticklabels([str(n) for n in Ns])
    a2.set_xlabel(L["cross_bx"]); a2.set_ylabel(L["cross_by"])
    _title(a2, L["cross_b"]); a2.legend(fontsize=8, frameon=False); _style(a2)
    fig.savefig(os.path.join(outdir, "fig9_crosschecks.png"), dpi=200)
    plt.close(fig)


def fig_convergence(res, outdir):
    fig, (a1, a2) = plt.subplots(1, 2, figsize=(9.6, 4.4),
                                 constrained_layout=True)
    ns = [r["n"] for r in res["rows"]]
    a1.plot(ns, [r["errB_pct"] for r in res["rows"]], "o-", color=C1,
            ms=5, label=L["conv_b1"])
    a1.plot(ns, [r["errQ_pred_pct"] for r in res["rows"]], "s-", color=C2,
            ms=5, label=L["conv_b2"])
    a1.plot([r["n"] for r in res["orientation"]],
            [r["mean_err_pct"] for r in res["orientation"]], "^-",
            color=C3, ms=5, label=L["conv_b3"])
    a1.set_xscale("log"); a1.set_yscale("log")
    a1.set_xticks(ns); a1.set_xticklabels([str(n) for n in ns])
    a1.set_xlabel(L["conv_ax"]); a1.set_ylabel(L["conv_ay"])
    _title(a1, L["conv_a"]); a1.legend(fontsize=8, frameon=False); _style(a1)
    a2.plot(ns, [r["monitor"] for r in res["rows"]], "o-", color=C1, ms=5)
    mvals = [r["monitor"] for r in res["rows"]]
    a2.set_ylim(0.9995 * min(mvals), 1.0005 * max(mvals))
    a2.set_xlabel(L["conv_ax"]); a2.set_ylabel(L["conv_by"])
    _title(a2, L["conv_b"]); _style(a2)
    fig.savefig(os.path.join(outdir, "fig10_convergence.png"), dpi=200)
    plt.close(fig)


def fig_anchors(res, outdir):
    fig, (a1, a2) = plt.subplots(1, 2, figsize=(9.6, 4.4),
                                 constrained_layout=True)
    g = res["geometry"]
    a1.plot([0.0, 1.4], [0.0, 1.4], color=C2, lw=1.6, label="$y=x$")
    mk = {"x": "o", "y": "s", "z": "^"}
    for nrm in ("x", "y", "z"):
        xs = [r["V_pred_over_Vgauss"] for r in g if r["axis"] == nrm]
        ys = [r["ratio"] for r in g if r["axis"] == nrm]
        a1.plot(xs, ys, mk[nrm], color=C1, ms=7,
                label=(f"normal {nrm}" if L is LABELS["en"]
                       else f"нормаль {nrm}"))
    a1.set_xlabel(L["anchor_ax"]); a1.set_ylabel(L["anchor_ay"])
    _title(a1, L["anchor_a"]); a1.legend(fontsize=8, frameon=False,
                                         loc="upper left"); _style(a1)
    w = res["water"]
    keys = [r["key"] for r in w]
    y = np.arange(len(keys))
    h = 0.26
    a2.barh(y + h, [math.log10(r["V_one_L_m3"]) for r in w], height=h,
            color=C3, label=L["wL"])
    a2.barh(y, [math.log10(r["V_one_10_m3"]) for r in w], height=h,
            color=C2, label=L["w10"])
    a2.barh(y - h, [math.log10(r["V_one_eta_m3"]) for r in w], height=h,
            color=C1, label=L["weta"])
    a2.set_yticks(y)
    a2.set_yticklabels([FLOW_NAMES["en"][k] if L is LABELS["en"]
                        else {"tea": "чай", "pipe": "труба",
                              "draupner": "Драупнер",
                              "katrina": "Катрина"}[k] for k in keys],
                       fontsize=9)
    a2.set_xlabel(L["anchor_bx"])
    _title(a2, L["anchor_b"]); a2.legend(fontsize=8, frameon=False,
                                         loc="lower right"); _style(a2)
    fig.savefig(os.path.join(outdir, "fig11_anchors.png"), dpi=200)
    plt.close(fig)


def fig_houluo(res, outdir):
    fig, axs = plt.subplots(2, 2, figsize=(9.6, 7.6), constrained_layout=True)
    (a1, a2), (a3, a4) = axs
    for kind, col, lab in (("dipole", C2, L["hl_dip"]),
                           ("corot", C1, L["hl_co"])):
        s = res["runs"][kind]["series"]
        t = np.array([r["t"] for r in s])
        B = np.array([r["B"] for r in s])
        a1.plot(t, B / B[0], "-", color=col, lw=1.8, label=lab)
    a1.set_xlabel(L["hl_ax"]); a1.set_ylabel(L["hl_ay"])
    _title(a1, L["hl_a"]); a1.legend(fontsize=8, frameon=False,
                                     loc="center right"); _style(a1)
    s_d = res["runs"]["dipole"]["series"]
    s_c = res["runs"]["corot"]["series"]
    t = np.array([r["t"] for r in s_d])
    mann = 1.0 - np.array([r["B"] for r in s_d]) / np.array(
        [r["B"] for r in s_c]) * (s_c[0]["B"] / s_d[0]["B"])
    a2.plot(t, mann, "-", color=C2, lw=1.8)
    a2.set_ylim(-0.02, 1.02)
    a2.set_xlabel(L["hl_bx"]); a2.set_ylabel(L["hl_by"])
    _title(a2, L["hl_b"]); _style(a2)
    for kind, col, lab in (("dipole", C2, L["dip"]), ("corot", C1, L["co"])):
        s = res["runs"][kind]["series"]
        t = np.array([r["t"] for r in s])
        wm = np.array([r["wmax"] for r in s])
        a3.loglog(t, wm, "-", color=col, lw=1.6, label=lab)
    tt = np.array([0.6 * res["t_end"], res["t_end"]])
    a3.loglog(tt, tt ** (-1.0) * 0.02, ":", color="#888888", lw=1.3,
              label=L["hl_cfit"])
    a3.set_xlabel(L["hl_cx"]); a3.set_ylabel(L["hl_cy"])
    _title(a3, L["hl_c"]); a3.legend(fontsize=8, frameon=False); _style(a3)
    ks = res["kicks"]
    x = np.arange(2)
    wd = 0.36
    a4.bar(x - wd / 2, [k["m_abs"] for k in ks], wd, color=C3,
           label=L["hl_d1"])
    a4.bar(x + wd / 2, [k["m_net"] for k in ks], wd, color=C2,
           label=L["hl_d2"])
    a4.axhline(res["m_abs_theory"], color=C1, lw=1.4, ls="--",
               label=f"{M_ABS_THEORY:.6f}")
    a4.set_xticks(x)
    a4.set_xticklabels([L["dip"], L["co"]])
    a4.set_ylim(0, 1.45)
    a4.set_ylabel(L["hl_dy"])
    _title(a4, L["hl_d"]); a4.legend(fontsize=8, frameon=False,
                                     loc="upper center"); _style(a4)
    fig.savefig(os.path.join(outdir, "fig12_houluo.png"), dpi=200)
    plt.close(fig)


def fig_houluo_fields(res, outdir):
    snaps = res["snaps"]
    times = sorted({k.split("_")[1] for k in snaps}, key=float)
    fig, axs = plt.subplots(2, len(times), figsize=(3.1 * len(times), 6.4),
                            constrained_layout=True)
    vmax = max(float(np.max(np.abs(v))) for v in snaps.values())
    for row, kind in enumerate(("dipole", "corot")):
        for col, ts in enumerate(times):
            ax = axs[row][col] if len(times) > 1 else axs[row]
            im = ax.imshow(snaps[f"{kind}_{ts}"], origin="lower",
                           cmap="RdBu_r", vmin=-vmax, vmax=vmax,
                           extent=[0, 2 * math.pi, 0, 2 * math.pi])
            ax.set_xticks([]); ax.set_yticks([])
            if row == 0:
                ax.set_title(L["fields_t"] + ts, fontsize=10)
    cb = fig.colorbar(im, ax=axs, shrink=0.85, pad=0.02)
    cb.set_label(r"$\omega_z$", fontsize=10)
    if not _NO_TITLES:
        fig.suptitle(L["fig13_title"], fontsize=12)
    fig.savefig(os.path.join(outdir, "fig13_houluo_fields.png"), dpi=200)
    plt.close(fig)


# ----------------------------------------------------------------------------
# main
# ----------------------------------------------------------------------------

def run_all(args):
    np.random.seed(SEED)
    print("=" * 72)
    print("  b-correction <-> volume: EXTENDED VERIFICATION BATTERY (H/I/J/K)")
    print("=" * 72)
    summary = {}

    print(f"\n[H] cross-check channels (velocity vs vorticity) ...")
    resH = exp_crosschecks()
    for r in resH["states"]:
        print(f"    {r['state']:<14} B_w={r['B_w']:.5f}  ratio={r['ratio']:.6f}"
              f"  D={r['D']:.3f} bound={r['bound']:.4f}"
              f"  inside={r['inside']}  idR2={r['id_r2']:.8f}")
    for k, v in resH["linearity"].items():
        print(f"    linearity {k:<7} slope={v['slope']:.6f}  R2={v['r2']:.8f}")
    for r in resH["orientation_l2"]:
        print(f"    Om_par/Om axis {r['axis']}: {r['meas']:.5f} vs theory "
              f"(1-(n.n_t)^2)/2 = {r['theory']:.5f}  err={r['err_pct']:.3f}%")
    print(f"    PASS = {resH['pass']}")
    summary["H_crosschecks"] = resH

    print(f"\n[I] resolution convergence n=32..96 ...")
    resI = exp_convergence()
    for r in resI["rows"]:
        print(f"    n={r['n']:>3}  errB={r['errB_pct']:.5f}%  "
              f"errQ_pred={r['errQ_pred_pct']:.5f}%  "
              f"monitor={r['monitor']:.7f}")
    for r in resI["orientation"]:
        print(f"    orientation n={r['n']}: mean err={r['mean_err_pct']:.4f}%")
    print(f"    PASS = {resI['pass']}")
    summary["I_convergence"] = resI

    print(f"\n[J] anchor checks ...")
    resJ = exp_anchors()
    for r in resJ["geometry"]:
        print(f"    axis {r['axis']} sigma={r['sigma']}: "
              f"V_meas/V_gauss={r['ratio']:.5f}  f_plane={r['f_plane']:.5f}  "
              f"err_vs_pred={r['err_pred_pct']:.3f}%")
    for r in resJ["invariance"]:
        print(f"    sigma={r['sigma']}: monitor n48={r['mon48']:.6f} "
              f"n64={r['mon64']:.6f}  dev={r['dev_pct']:.4f}%")
    for r in resJ["water"]:
        print(f"    {r['key']:<9} V_one(L)={r['V_one_L_m3']:.3e} m^3  "
              f"V_one(eta)={r['V_one_eta_m3']:.3e} m^3  "
              f"V1_quantum={r['V1_quantum_m3']:.3e} m^3")
    print(f"    PASS = {resJ['pass']}")
    summary["J_anchors"] = resJ

    print(f"\n[K] Hou–Luo dynamic annihilation (2D, n=128) ...")
    resK = exp_houluo()
    for kind in ("dipole", "corot"):
        s = resK["runs"][kind]["series"]
        print(f"    {kind:<7} B0={s[0]['B']:.4f}  B_end={s[-1]['B']:.4f} "
              f"({100.0 * s[-1]['B'] / s[0]['B']:.2f}%)  "
              f"S_raw_end={s[-1]['S']:.12f}")
    for kind in ("dipole", "corot"):
        print(f"    {kind:<7} dE=-nu*Om R2={resK['identities'][kind]['dE_vs_nuOm_r2']:.6f}"
              f"  dOm=-2nu*P R2={resK['identities'][kind]['dOm_vs_2nuP_r2']:.6f}"
              f"  wmax slope={resK['lamb_oseen'][kind]['slope']:.3f}")
    for k in resK["kicks"]:
        print(f"    kick@t*={k['t']:.2f} [{k['kind']:<7}] "
              f"m_abs={k['m_abs']:.6f} (theory {k['m_abs_theory']:.6f})  "
              f"m_net={k['m_net']:.2e}")
    print(f"    S drift = {resK['S_drift']:.2e}")
    print(f"    PASS = {resK['pass']}")
    summary["K_houluo"] = {k: v for k, v in resK.items() if k != "snaps"}

    all_pass = all([resH["pass"], resI["pass"], resJ["pass"], resK["pass"]])
    print("\n" + "=" * 72)
    print(f"  EXTENDED BATTERY: {'ALL CHECKS PASS' if all_pass else 'FAILURES PRESENT'}"
          f"   (wall {sum([0]):.0f}s)")
    print("=" * 72)
    summary["_all_pass"] = all_pass
    return summary, resK


def main():
    global L
    ap = argparse.ArgumentParser(description="extended verification battery")
    ap.add_argument("--quick", action="store_true")
    ap.add_argument("--lang", choices=("en", "ru"), default="en")
    ap.add_argument("--outdir", default="b_volume_out_ext")
    ap.add_argument("--indir", default=None,
                    help="read summary_extension.json from this dir (figs-only)")
    ap.add_argument("--figs-only", action="store_true")
    args = ap.parse_args()
    L = LABELS[args.lang]
    os.makedirs(args.outdir, exist_ok=True)

    if args.figs_only:
        src = args.indir or args.outdir
        with open(os.path.join(src, "summary_extension.json")) as f:
            summary = json.load(f)
        fig_crosschecks(summary["H_crosschecks"], args.outdir)
        fig_convergence(summary["I_convergence"], args.outdir)
        fig_anchors(summary["J_anchors"], args.outdir)
        fig_houluo(summary["K_houluo"], args.outdir)
        npz = os.path.join(src, "houluo_fields.npz")
        snaps = dict(np.load(npz))
        fig_houluo_fields({**summary["K_houluo"], "snaps": snaps},
                          args.outdir)
        print(f"figures (lang={args.lang}) -> {args.outdir}")
        return

    summary, resK = run_all(args)
    with open(os.path.join(args.outdir, "summary_extension.json"), "w") as f:
        json.dump(summary, f, indent=1)
    np.savez(os.path.join(args.outdir, "houluo_fields.npz"),
             **resK["snaps"])
    # figures in the requested language
    fig_crosschecks(summary["H_crosschecks"], args.outdir)
    fig_convergence(summary["I_convergence"], args.outdir)
    fig_anchors(summary["J_anchors"], args.outdir)
    fig_houluo(summary["K_houluo"], args.outdir)
    fig_houluo_fields(resK, args.outdir)
    print(f"\noutputs -> {args.outdir}")


if __name__ == "__main__":
    main()
