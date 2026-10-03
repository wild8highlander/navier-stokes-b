#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
b_volume_experiment.py — v1.0.0
Research add-on for the Navier-Stokes b-Lab (b-correction <-> liquid volume).

Research question (repo wild8highlander/navier-stokes-b):
the b-correction of the lab is a pure mathematical angle
    b   = 1/(4*pi + 2*sqrt(3)) ~ 0.062381,
    th_b = arcsin(b)           ~ 3.577 deg,
applied as a pointwise rotation of the velocity field followed by the Leray
re-projection. The hypothesis to test: ONE water vortex carries ONE b-correction,
merging vortices accumulate their corrections, and the correction is tied to the
VOLUME of the liquid. What volume corresponds to one b-correction?

What this script establishes numerically (pseudo-spectral solver, same
algorithm as the lab: RK4 + Leray + 2/3 dealiasing, unit box [0,2*pi)^3):

  T  THEOREM CHECK. For any incompressible u,
         div(R_b u) = -th_b * (n_b . omega) + O(th_b^2),
     i.e. one b-kick injects divergence proportional to the vorticity
     component along the b-axis. Hence the measurable "b-charge" of a flow
         B = integral |n_b . omega| dV            ("rotating volume")
     and one kick on one vortex injects the flux Q_b = th_b * B.
  A  ADDITIVITY. N co-rotating vortex tubes: Q_b and kick energy loss grow
     exactly linearly in N (b-charge is extensive, like volume).
  B  ORIENTATION ALGEBRA. For a tube with axis n_t: Q/(th_b*Gamma*L) =
     |n_b . n_t| — verified for x/y/z tubes (factors 0.3 / 0.5 / 0.8124).
  C  WHAT VOLUME MEANS. At fixed circulation Q_b is independent of the core
     size; at fixed vorticity density Q_b is exactly proportional to the
     vortex volume. Slope dQ_b/dV = th_b * <omega_par>: the correction counts
     the VORTICITY-WEIGHTED volume. Elementary b-volume at unit vorticity:
     V1 = 4*pi + 2*sqrt(3) ~ 16.03 code units = 6.46% of the periodic box.
  D  MERGING. Co-rotating pair: b-charge additive at any separation.
     Anti-parallel pair: b-charge ANNIHILATES as the tubes merge.
  E  TIME SERIES. Free decay of an 8-tube state: b-charge(t) is approximately
     conserved (viscosity is its only sink), sup|omega| reacts to merging.
  F  REAL WATER. Kolmogorov bridge: eta=(nu^3/eps)^(1/4), omega_eta=(eps/nu)^1/2,
     one quantum vortex V1=(4*pi/3)*eta^3; table for tea / tap pipe /
     Draupner wave / Katrina; b-flux density = 0.5*th_b*omega_eta per unit volume.
  G  NET ANGLE. Composition of N kicks: aligned axes add angles exactly
     (Theta = N*th_b, SO(3)), random axes give a random walk Theta_rms ~
     sqrt(N)*th_b (Monte-Carlo on the rotation group).

Outputs: JSON summary + PNG figures (labels ru/en via --lang, default en).
Only numpy + matplotlib are required. Deterministic (fixed seed).

Run:  python3 b_volume_experiment.py [--quick] [--lang ru] [--outdir DIR]
"""

import argparse
import json
import math
import os
import time

import numpy as np

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D

# ----------------------------------------------------------------------------
# b-constants (exactly as in nsb_lab_standalone.jl / constants)
# ----------------------------------------------------------------------------
B_CONST = 1.0 / (4.0 * math.pi + 2.0 * math.sqrt(3.0))   # 0.062381...
THETA_B = math.asin(B_CONST)                             # 0.062422 rad = 3.577 deg
AXIS_B = np.array([0.3, -0.5, math.sqrt(1.0 - 0.3 ** 2 - 0.5 ** 2)])  # unit
V_BOX = (2.0 * math.pi) ** 3                             # 248.050...

SEED = 20260103


def rodrigues(theta: float, axis: np.ndarray) -> np.ndarray:
    """Rotation matrix (same construction as nsb_rodrigues in the lab)."""
    ex, ey, ez = axis
    cross = np.array([[0.0, -ez, ey], [ez, 0.0, -ex], [-ey, ex, 0.0]])
    outer = np.outer(axis, axis)
    return (math.cos(theta) * np.eye(3)
            + (1.0 - math.cos(theta)) * outer
            - math.sin(theta) * cross)


R_B = rodrigues(THETA_B, AXIS_B)

# ----------------------------------------------------------------------------
# tiny label dictionary for figures
# ----------------------------------------------------------------------------
LABELS = {
    "en": {
        "th_scatter": "Exp T: div(R$_b$u) vs $-\\theta_b\\,(\\hat n_b\\!\\cdot\\!\\omega)$",
        "th_x": "$-\\theta_b\\,(\\hat n_b\\cdot\\omega)$   [1/time]",
        "th_y": "div(R$_b$u)   [1/time]",
        "th_note": "slope = {slope:.4f} (theory: $-1$),  R$^2$ = {r2:.6f}",
        "nscan_a": "Exp A: kick flux $Q_b$ vs number of merged vortices",
        "nscan_b": "Exp A: kick energy cost $\\delta E$ vs N",
        "nscan_x": "N merged vortex rings",
        "nscan_ay": "$Q_b$   [volume flux]",
        "nscan_by": "$\\delta E$   [energy]",
        "orient": "Exp B: kick flux per unit circulation — orientation algebra",
        "orient_y": "$Q_b\\,/\\,(\\theta_b\\,\\Gamma L)$",
        "orient_x": "ring normal",
        "volume_a": "Exp C: fixed circulation $\\Gamma=1$ (core size varies)",
        "volume_b": "Exp C: fixed vorticity $\\omega_0=1$ (volume varies)",
        "volume_x": "vortex volume $V$   [code units]",
        "volume_y": "$Q_b$   [volume flux]",
        "vol_flat": "theory: $Q_b$ indep. of $V$ at fixed $\\Gamma$",
        "vol_lin": "theory: $Q_b=\\theta_b\\,\\omega_\\parallel V$",
        "annih": "Exp D: merging of a vortex pair — b-charge vs separation",
        "annih_x": "separation $\\delta z\\,/\\,\\sigma$",
        "annih_y": "pair b-charge  $\\mathcal{B}\\,/\\,\\mathcal{B}_1$",
        "annih_co": "co-rotating pair (corrections add)",
        "annih_ap": "anti-parallel pair (corrections annihilate)",
        "netang": "Exp G: net rotation angle of N composed b-kicks",
        "netang_x": "N kicks",
        "netang_y": "net angle $\\Theta$   [rad]",
        "netang_al": "aligned axes: $\\Theta=N\\theta_b$ (slope 1)",
        "netang_rnd": "random axes: $\\Theta_{\\rm rms}=\\sqrt{N}\\,\\theta_b$ (slope 1/2)",
        "decay": "Exp E: free decay of 8 co-rotating vortex rings",
        "decay_x": "time",
        "decay_yL": "b-charge $\\mathcal{B}(t)\\,/\\,\\mathcal{B}(0)$",
        "decay_yR": "sup$\\,|\\omega|$",
        "decay_b": "b-charge (normalised)",
        "decay_w": "sup$\\,|\\omega|$ (right axis)",
        "water": "Exp F: one b-correction = one Kolmogorov vortex of water",
        "water_x": "dissipation rate $\\varepsilon$   [m$^2$/s$^3$]",
        "water_y": "quantum vortex volume $V_1=\\frac{4\\pi}{3}\\eta^3$   [m$^3$]",
        "water_line": "water at 20$^\\circ$C:  $V_1(\\varepsilon)$",
    },
    "ru": {
        "th_scatter": "Опыт T: div(R$_b$u) против $-\\theta_b\\,(\\hat n_b\\!\\cdot\\!\\omega)$",
        "th_x": "$-\\theta_b\\,(\\hat n_b\\cdot\\omega)$   [1/время]",
        "th_y": "div(R$_b$u)   [1/время]",
        "th_note": "наклон = {slope:.4f} (теория: $-1$),  R$^2$ = {r2:.6f}",
        "nscan_a": "Опыт A: поток пинка $Q_b$ против числа слившихся вихрей",
        "nscan_b": "Опыт A: энергетическая цена пинка $\\delta E$ против N",
        "nscan_x": "N слившихся вихревых колец",
        "nscan_ay": "$Q_b$   [поток объёма]",
        "nscan_by": "$\\delta E$   [энергия]",
        "orient": "Опыт B: поток пинка на единицу циркуляции — алгебра ориентаций",
        "orient_y": "$Q_b\\,/\\,(\\theta_b\\,\\Gamma L)$",
        "orient_x": "нормаль кольца",
        "volume_a": "Опыт C: фиксированная циркуляция $\\Gamma=1$ (меняется ядро)",
        "volume_b": "Опыт C: фиксированная завихренность $\\omega_0=1$ (меняется объём)",
        "volume_x": "объём вихря $V$   [кодовые ед.]",
        "volume_y": "$Q_b$   [поток объёма]",
        "vol_flat": "теория: $Q_b$ не зависит от $V$ при фиксированной $\\Gamma$",
        "vol_lin": "теория: $Q_b=\\theta_b\\,\\omega_\\parallel V$",
        "annih": "Опыт D: слияние пары вихрей — б-заряд против расстояния",
        "annih_x": "расстояние $\\delta z\\,/\\,\\sigma$",
        "annih_y": "б-заряд пары  $\\mathcal{B}\\,/\\,\\mathcal{B}_1$",
        "annih_co": "со-вращающаяся пара (поправки складываются)",
        "annih_ap": "анти-параллельная пара (поправки аннигилируют)",
        "netang": "Опыт G: суммарный угол N последовательных б-пинков",
        "netang_x": "N пинков",
        "netang_y": "суммарный угол $\\Theta$   [рад]",
        "netang_al": "выровненные оси: $\\Theta=N\\theta_b$ (наклон 1)",
        "netang_rnd": "случайные оси: $\\Theta_{\\rm rms}=\\sqrt{N}\\,\\theta_b$ (наклон 1/2)",
        "decay": "Опыт E: свободное затухание 8 со-вращающихся вихревых колец",
        "decay_x": "время",
        "decay_yL": "б-заряд $\\mathcal{B}(t)\\,/\\,\\mathcal{B}(0)$",
        "decay_yR": "sup$\\,|\\omega|$",
        "decay_b": "б-заряд (норм.)",
        "decay_w": "sup$\\,|\\omega|$ (правая ось)",
        "water": "Опыт F: одна поправка «б» = один колмогоровский вихрь воды",
        "water_x": "скорость диссипации $\\varepsilon$   [м$^2$/с$^3$]",
        "water_y": "объём квантового вихря $V_1=\\frac{4\\pi}{3}\\eta^3$   [м$^3$]",
        "water_line": "вода при 20$^\\circ$C:  $V_1(\\varepsilon)$",
    },
}

# ----------------------------------------------------------------------------
# pseudo-spectral toolkit (mirrors the lab's solver: Leray + 2/3 rule)
# ----------------------------------------------------------------------------


def make_k(n: int):
    k1 = np.fft.fftfreq(n, d=1.0 / n)          # integer wavenumbers, box 2*pi
    kx = k1.reshape(n, 1, 1)
    ky = k1.reshape(1, n, 1)
    kz = k1.reshape(1, 1, n)
    k2 = kx * kx + ky * ky + kz * kz
    return kx, ky, kz, k2


def project_hat(uh, kx, ky, kz, k2):
    """Leray projection onto divergence-free fields (spectral)."""
    kdot = kx * uh[0] + ky * uh[1] + kz * uh[2]
    safe_k2 = np.where(k2 > 0, k2, 1.0)
    coeff = np.where(k2 > 0, kdot / safe_k2, 0.0)
    return (uh[0] - kx * coeff, uh[1] - ky * coeff, uh[2] - kz * coeff)


def dealias_hat(uh, k2, kmax):
    mask = (k2 <= kmax * kmax).astype(np.float64)
    return (uh[0] * mask, uh[1] * mask, uh[2] * mask)


def curl_hat(uh, kx, ky, kz):
    return (1j * (ky * uh[2] - kz * uh[1]),
            1j * (kz * uh[0] - kx * uh[2]),
            1j * (kx * uh[1] - ky * uh[0]))


def div_hat(uh, kx, ky, kz):
    return 1j * (kx * uh[0] + ky * uh[1] + kz * uh[2])


def fft_field(u):
    return (np.fft.fftn(u[0]), np.fft.fftn(u[1]), np.fft.fftn(u[2]))


def ifft_field(uh):
    return (np.real(np.fft.ifftn(uh[0])),
            np.real(np.fft.ifftn(uh[1])),
            np.real(np.fft.ifftn(uh[2])))


def prepare_from_vorticity(w, kx, ky, kz, k2, kmax):
    """Biot-Savart: u_hat = (i/k^2) k x w_hat, then Leray + 2/3 dealiasing."""
    wh = fft_field(w)
    safe_k2 = np.where(k2 > 0, k2, 1.0)
    inv = np.where(k2 > 0, 1.0 / safe_k2, 0.0)
    uh = (1j * inv * (ky * wh[2] - kz * wh[1]),
          1j * inv * (kz * wh[0] - kx * wh[2]),
          1j * inv * (kx * wh[1] - ky * wh[0]))
    uh = project_hat(uh, kx, ky, kz, k2)
    return dealias_hat(uh, k2, kmax)


def prepare_velocity(u, kx, ky, kz, k2, kmax):
    uh = fft_field(u)
    uh = project_hat(uh, kx, ky, kz, k2)
    return dealias_hat(uh, k2, kmax)


# ----------------------------------------------------------------------------
# real-space diagnostics
# ----------------------------------------------------------------------------


def vorticity_real(uh, kx, ky, kz):
    return ifft_field(curl_hat(uh, kx, ky, kz))


def b_charge(w, nb=AXIS_B):
    """B = integral |n_b . omega| dV  — the 'b-charge' (rotating volume flux)."""
    return float(np.mean(np.abs(nb[0] * w[0] + nb[1] * w[1] + nb[2] * w[2])) * V_BOX)


def b_charge_hat(uh, kx, ky, kz):
    return b_charge(vorticity_real(uh, kx, ky, kz))


def energy_hat(uh):
    u = ifft_field(uh)
    return float(0.5 * (np.mean(u[0] ** 2 + u[1] ** 2 + u[2] ** 2)) * V_BOX)


def sup_omega_hat(uh, kx, ky, kz):
    w = vorticity_real(uh, kx, ky, kz)
    return float(np.sqrt(max(
        float(np.max(w[0] ** 2 + w[1] ** 2 + w[2] ** 2)), 0.0)))


def rotate_pointwise(u, R):
    """u'(x) = R u(x) — the pointwise b-rotation (lab: nsb_rotate_pointwise!)."""
    return (R[0, 0] * u[0] + R[0, 1] * u[1] + R[0, 2] * u[2],
            R[1, 0] * u[0] + R[1, 1] * u[1] + R[1, 2] * u[2],
            R[2, 0] * u[0] + R[2, 1] * u[1] + R[2, 2] * u[2])


def kick_flux(uh, kx, ky, kz, R=None):
    """Q_b = integral |div(R u)| dV for one pointwise rotation (before
    re-projection). R defaults to the b-matrix R_B."""
    if R is None:
        R = R_B
    u = ifft_field(uh)
    ru = rotate_pointwise(u, R)
    ruh = fft_field(ru)
    divx = np.real(np.fft.ifftn(div_hat(ruh, kx, ky, kz)))
    return float(np.mean(np.abs(divx)) * V_BOX)


def kick_energy_cost(uh, kx, ky, kz, k2, kmax):
    """Energy removed by the Leray re-projection after one b-kick."""
    u = ifft_field(uh)
    ru = rotate_pointwise(u, R_B)
    ruh = dealis_and_project(fft_field(ru), kx, ky, kz, k2, kmax)
    return energy_hat(uh) - energy_hat(ruh)


def dealis_and_project(uh, kx, ky, kz, k2, kmax):
    uh = project_hat(uh, kx, ky, kz, k2)
    return dealias_hat(uh, k2, kmax)


def kick_apply(uh, kx, ky, kz, k2, kmax):
    """Apply one full b-kick: rotate pointwise, re-project, dealias."""
    u = ifft_field(uh)
    ru = rotate_pointwise(u, R_B)
    return dealis_and_project(fft_field(ru), kx, ky, kz, k2, kmax)


def div_break_map(uh, kx, ky, kz, w=None):
    """Return (div(R_b u), -th_b*(n_b.omega)) sampled in real space (Exp T)."""
    u = ifft_field(uh)
    ru = rotate_pointwise(u, R_B)
    ruh = fft_field(ru)
    divx = np.real(np.fft.ifftn(div_hat(ruh, kx, ky, kz)))
    if w is None:
        w = vorticity_real(uh, kx, ky, kz)
    wpar = AXIS_B[0] * w[0] + AXIS_B[1] * w[1] + AXIS_B[2] * w[2]
    return divx.ravel(), (-THETA_B * wpar).ravel()


# ----------------------------------------------------------------------------
# initial conditions
# ----------------------------------------------------------------------------

def ic_taylor_green(n):
    x1 = 2.0 * math.pi * np.arange(n) / n
    sx, cx = np.sin(x1), np.cos(x1)
    X = sx.reshape(n, 1, 1)
    CX = cx.reshape(n, 1, 1)
    Y = sx.reshape(1, n, 1)
    CY = cx.reshape(1, n, 1)
    Z = cx.reshape(1, 1, n)
    u1 = X * CY * Z
    u2 = -CX * Y * Z
    u3 = np.zeros((n, n, n))
    return (u1, u2, u3)


def ic_vring(n, normal="z", gamma=1.0, sigma=0.3, R0=1.0,
             center=(math.pi, math.pi, math.pi)):
    """One axisymmetric vortex ring (exactly solenoidal, zero-mean vorticity).

    omega = Omega0*exp(-((r-R0)^2 + h^2)/(2 sigma^2)) * e_phi(r),
    Omega0 = Gamma/(2 pi sigma^2); r = distance from the ring axis, h =
    offset along the axis; e_phi = unit toroidal direction.
    Exact identities used by the theory checks:
        Gamma = Omega0 * 2*pi*sigma^2
        V_tube = 2*pi^2 * R0 * sigma^2          (torus volume)
        B = Gamma * (2*pi*R0) * f_plane        (EXACT, f_plane below)
    """
    c = 2.0 * math.pi * np.arange(n) / n
    ones = np.ones((n, n, n))
    X = c.reshape(n, 1, 1) * ones - center[0]
    Y = c.reshape(1, n, 1) * ones - center[1]
    Z = c.reshape(1, 1, n) * ones - center[2]
    if normal == "z":                    # ring in the (x,y) plane
        r = np.hypot(X, Y); h = Z
        er, ep = (X, Y), None
        ex = -Y / np.where(r > 1e-12, r, 1.0)
        ey = X / np.where(r > 1e-12, r, 1.0)
        ez = np.zeros_like(r)
    elif normal == "x":                  # ring in the (y,z) plane
        r = np.hypot(Y, Z); h = X
        ex = np.zeros_like(r)
        ey = -Z / np.where(r > 1e-12, r, 1.0)
        ez = Y / np.where(r > 1e-12, r, 1.0)
    else:                                # normal == "y": ring in the (x,z) plane
        r = np.hypot(X, Z); h = Y
        ex = Z / np.where(r > 1e-12, r, 1.0)
        ey = np.zeros_like(r)
        ez = -X / np.where(r > 1e-12, r, 1.0)
    Omega0 = gamma / (2.0 * math.pi * sigma ** 2)
    F = Omega0 * np.exp(-(((r - R0) ** 2 + h ** 2) / (2.0 * sigma ** 2)))
    return (F * ex, F * ey, F * ez)


RP = 2.0 * math.pi   # shorthand


def ring_fplane(normal):
    """Exact f_plane = <|n_b . e_phi(phi)|> for a ring with the given normal."""
    phi = np.linspace(0.0, 2.0 * math.pi, 8192, endpoint=False)
    if normal == "z":
        t = (-np.sin(phi), np.cos(phi), np.zeros_like(phi))
    elif normal == "x":
        t = (np.zeros_like(phi), -np.sin(phi), np.cos(phi))
    else:
        t = (np.cos(phi), np.zeros_like(phi), -np.sin(phi))
    d = AXIS_B[0] * t[0] + AXIS_B[1] * t[1] + AXIS_B[2] * t[2]
    return float(np.mean(np.abs(d)))


def ring_B(gamma, normal):
    """Exact b-charge of one ring: Gamma * L_ring * f_plane."""
    return gamma * 2.0 * math.pi * 1.0 * ring_fplane(normal)   # R0=1 -> L=2pi


def ring_B_R0(gamma, normal, R0):
    return gamma * 2.0 * math.pi * R0 * ring_fplane(normal)


def ic_vring_lattice(n, n_rings, gamma=1.0, sigma=0.25, R0=0.6):
    """Up to 8 identical rings on the 2x2x2 lattice sites (normal = z)."""
    sites = [(math.pi + sx * math.pi / 2, math.pi + sy * math.pi / 2,
              math.pi + sz * math.pi / 2)
             for sx in (-1, 1) for sy in (-1, 1) for sz in (-1, 1)]
    w = (np.zeros((n, n, n)), np.zeros((n, n, n)), np.zeros((n, n, n)))
    for j in range(min(n_rings, 8)):
        wr = ic_vring(n, "z", gamma=gamma, sigma=sigma, R0=R0, center=sites[j])
        w = (w[0] + wr[0], w[1] + wr[1], w[2] + wr[2])
    return w

# ----------------------------------------------------------------------------
# EXP T — theorem check: div(R_b u) = -th_b (n_b . omega) + O(th_b^2)
# ----------------------------------------------------------------------------

def exp_theorem(n=32, tol_slope=0.02):
    kx, ky, kz, k2 = make_k(n)
    kmax = n / 3.0
    results = []
    fields = {
        "taylor_green": prepare_velocity(ic_taylor_green(n), kx, ky, kz, k2, kmax),
        "ring_x": prepare_from_vorticity(
            ic_vring(n, "x", sigma=0.3, R0=1.0), kx, ky, kz, k2, kmax),
        "ring_y": prepare_from_vorticity(
            ic_vring(n, "y", sigma=0.3, R0=1.0), kx, ky, kz, k2, kmax),
        "ring_z": prepare_from_vorticity(
            ic_vring(n, "z", sigma=0.3, R0=1.0), kx, ky, kz, k2, kmax),
    }
    slopes = {}
    results = []
    for name, uh in fields.items():
        xd, yd = div_break_map(uh, kx, ky, kz)
        # least squares y = slope * x (no intercept: theory predicts pure line)
        slope = float(np.dot(xd, yd) / np.dot(xd, xd))
        pred = slope * xd
        ss_res = float(np.sum((yd - pred) ** 2))
        ss_tot = float(np.sum((yd - np.mean(yd)) ** 2))
        r2 = 1.0 - ss_res / max(ss_tot, 1e-300)
        slopes[name] = (slope, r2)
        results.append({"field": name, "slope": slope, "r2": r2,
                        "pass": bool(abs(slope + 1.0) < tol_slope)})
    # attach TG scatter for the figure + fit object
    xd, yd = div_break_map(fields["taylor_green"], kx, ky, kz)
    scatter = (xd, yd)
    tg_slope = {"slope": slopes["taylor_green"][0],
                "r2": slopes["taylor_green"][1]}
    return {"slopes": slopes, "results": results, "scatter": scatter,
            "tg_slope": tg_slope,
            "pass": all(r["pass"] for r in results)}


# ----------------------------------------------------------------------------
# EXP A — additivity: N merged co-rotating vortex rings
# ----------------------------------------------------------------------------

def exp_nscan(n=64, n_list=(1, 2, 4, 8), gamma=1.0, sigma=0.25, R0=0.6):
    kx, ky, kz, k2 = make_k(n)
    kmax = n / 3.0
    rows = []
    for N in n_list:
        w = ic_vring_lattice(n, N, gamma=gamma, sigma=sigma, R0=R0)
        uh = prepare_from_vorticity(w, kx, ky, kz, k2, kmax)
        B = b_charge_hat(uh, kx, ky, kz)
        Q = kick_flux(uh, kx, ky, kz)
        dE = kick_energy_cost(uh, kx, ky, kz, k2, kmax)
        sw = sup_omega_hat(uh, kx, ky, kz)
        rows.append({"N": N, "B": B, "Q": Q, "dE": dE, "sup_omega": sw})
    # linear fits through origin
    Ns = np.array([r["N"] for r in rows], dtype=float)
    Qs = np.array([r["Q"] for r in rows])
    Es = np.array([r["dE"] for r in rows])
    q_per_n = float(np.dot(Ns, Qs) / np.dot(Ns, Ns))
    e_per_n = float(np.dot(Ns, Es) / np.dot(Ns, Ns))
    r2_q = 1.0 - float(np.sum((Qs - q_per_n * Ns) ** 2) / np.sum(
        (Qs - np.mean(Qs)) ** 2))
    return {"rows": rows, "Q_per_vortex": q_per_n, "dE_per_vortex": e_per_n,
            "Q_vs_N_r2": r2_q,
            "theory_Q_per_vortex": THETA_B * ring_B_R0(gamma, "z", R0),
            "additivity_pass": bool(r2_q > 0.9999 and
                                    abs(q_per_n /
                                        (THETA_B * ring_B_R0(gamma, "z", R0))
                                        - 1.0) < 0.05)}


# ----------------------------------------------------------------------------
# EXP B — orientation algebra: Q/(th_b * Gamma * L_ring) = f_plane
# ----------------------------------------------------------------------------

def exp_orientation(n=64, gamma=1.0, sigma=0.3, R0=1.0):
    """Q/(th_b * Gamma * L_ring) = f_plane, plus the O(theta^2) check:
    halving the kick angle must cut the relative error ~4x."""
    kx, ky, kz, k2 = make_k(n)
    kmax = n / 3.0
    R_half = rodrigues(THETA_B / 2.0, AXIS_B)
    rows = []
    for normal in ("x", "y", "z"):
        w = ic_vring(n, normal, gamma=gamma, sigma=sigma, R0=R0)
        uh = prepare_from_vorticity(w, kx, ky, kz, k2, kmax)
        Q_full = kick_flux(uh, kx, ky, kz)
        Q_half = kick_flux(uh, kx, ky, kz, R=R_half)
        theory = ring_fplane(normal)
        norm = gamma * 2.0 * math.pi * R0
        ratio_full = Q_full / (THETA_B * norm)
        ratio_half = Q_half / ((THETA_B / 2.0) * norm)
        err_full = 100.0 * abs(ratio_full - theory) / theory
        err_half = 100.0 * abs(ratio_half - theory) / theory
        rows.append({"axis": normal, "ratio": ratio_full,
                     "ratio_half": ratio_half, "theory": theory,
                     "err_pct": err_full, "err_half_pct": err_half})
    o2 = all(r["err_half_pct"] < 0.6 * r["err_pct"] for r in rows)
    return {"rows": rows, "o2_confirmed": o2,
            "pass": bool(o2 and all(r["err_pct"] < 4.0 for r in rows))}


# ----------------------------------------------------------------------------
# EXP C — what volume means: two core-size scans
# ----------------------------------------------------------------------------

def exp_volume_scan(n=64, sigmas=(0.2, 0.25, 0.3, 0.35, 0.45), R0=1.0):
    kx, ky, kz, k2 = make_k(n)
    kmax = n / 3.0
    fixed_gamma, fixed_omega = [], []
    fz = ring_fplane("z")
    for sigma in sigmas:
        # (a) fixed circulation Gamma = 1: Omega0 = 1/(2 pi sigma^2)
        w = ic_vring(n, "z", gamma=1.0, sigma=sigma, R0=R0)
        uh = prepare_from_vorticity(w, kx, ky, kz, k2, kmax)
        V_tube = 2.0 * math.pi ** 2 * R0 * sigma ** 2
        fixed_gamma.append({"sigma": sigma, "V": V_tube,
                            "Q": kick_flux(uh, kx, ky, kz)})
        # (b) fixed vorticity density Omega0 = 1: Gamma = 2 pi sigma^2
        w2 = ic_vring(n, "z", gamma=2.0 * math.pi * sigma ** 2,
                      sigma=sigma, R0=R0)
        uh2 = prepare_from_vorticity(w2, kx, ky, kz, k2, kmax)
        fixed_omega.append({"sigma": sigma, "V": V_tube,
                            "Q": kick_flux(uh2, kx, ky, kz)})
    qg = np.array([r["Q"] for r in fixed_gamma])
    vo = np.array([r["V"] for r in fixed_omega])
    qo = np.array([r["Q"] for r in fixed_omega])
    flat_dev = float(np.max(np.abs(qg - np.mean(qg))) / np.mean(qg))
    slope = float(np.dot(vo, qo) / np.dot(vo, vo))       # through origin
    r2_lin = 1.0 - float(np.sum((qo - slope * vo) ** 2) / np.sum(
        (qo - np.mean(qo)) ** 2))
    theory_slope = 2.0 * THETA_B * fz                    # dQ/dV = th_b*2*f_z*Omega0
    return {"fixed_gamma": fixed_gamma, "fixed_omega": fixed_omega,
            "flat_rel_dev": flat_dev,
            "slope_fixed_omega": slope, "theory_slope": theory_slope,
            "slope_r2": r2_lin,
            "pass": bool(flat_dev < 0.03 and
                         abs(slope / theory_slope - 1.0) < 0.03)}


# ----------------------------------------------------------------------------
# EXP D — merging: co-rotating vs anti-parallel pair
# ----------------------------------------------------------------------------

def exp_merging(n=64, gamma=1.0, sigma=0.25, R0=0.6,
                sep_list=(0.0, 0.5, 1.0, 2.0, 4.0, 8.0)):
    kx, ky, kz, k2 = make_k(n)
    kmax = n / 3.0
    rows = []
    for dz_sigma in sep_list:
        dz = dz_sigma * sigma
        r1 = ic_vring(n, "z", gamma=gamma, sigma=sigma, R0=R0,
                      center=(math.pi, math.pi, math.pi - dz / 2))
        r2 = ic_vring(n, "z", gamma=gamma, sigma=sigma, R0=R0,
                      center=(math.pi, math.pi, math.pi + dz / 2))
        zero = np.zeros((n, n, n))
        w_co = (r1[0] + r2[0], r1[1] + r2[1], r1[2] + r2[2])
        w_ap = (r1[0] - r2[0], r1[1] - r2[1], r1[2] - r2[2])
        B_co = b_charge(w_co)
        B_ap = b_charge(w_ap)
        rows.append({"dz_over_sigma": dz_sigma, "B_co": B_co, "B_ap": B_ap})
    B1 = b_charge(ic_vring(n, "z", gamma=gamma, sigma=sigma, R0=R0))
    for r in rows:
        r["B_co_norm"] = r["B_co"] / B1
        r["B_ap_norm"] = r["B_ap"] / B1
    return {"rows": rows, "B1_single": B1,
            "co_additive": bool(abs(rows[-1]["B_co_norm"] - 2.0) < 0.02),
            "ap_annihilates": bool(rows[0]["B_ap_norm"] < 0.02)}


# ----------------------------------------------------------------------------
# EXP E — time series: free decay of 8 co-rotating tubes (RK4 + Leray + 2/3)
# ----------------------------------------------------------------------------

def ns_rhs_hat(uh, kx, ky, kz, k2, nu):
    """du/dt = P[ u x omega ] - nu k^2 u   (pseudo-spectral, vorticity form)."""
    u = ifft_field(uh)
    w = vorticity_real(uh, kx, ky, kz)
    nl = (u[1] * w[2] - u[2] * w[1],
          u[2] * w[0] - u[0] * w[2],
          u[0] * w[1] - u[1] * w[0])
    nlh = project_hat(fft_field(nl), kx, ky, kz, k2)
    return (nlh[0] - nu * k2 * uh[0],
            nlh[1] - nu * k2 * uh[1],
            nlh[2] - nu * k2 * uh[2])


def rk4_step(uh, dt, kx, ky, kz, k2, kmax, nu):
    k1 = ns_rhs_hat(uh, kx, ky, kz, k2, nu)
    t2 = tuple(uh[a] + 0.5 * dt * k1[a] for a in range(3))
    k2r = ns_rhs_hat(t2, kx, ky, kz, k2, nu)
    t3 = tuple(uh[a] + 0.5 * dt * k2r[a] for a in range(3))
    k3 = ns_rhs_hat(t3, kx, ky, kz, k2, nu)
    t4 = tuple(uh[a] + dt * k3[a] for a in range(3))
    k4 = ns_rhs_hat(t4, kx, ky, kz, k2, nu)
    out = tuple(uh[a] + (dt / 6.0) * (k1[a] + 2 * k2r[a] + 2 * k3[a] + k4[a])
                for a in range(3))
    return dealias_hat(out, k2, kmax)


def exp_decay(n=48, n_rings=8, nu=0.005, dt=0.004, t_horizon=2.0,
              gamma=1.0, sigma=0.25, R0=0.6, sample_every=10, verbose=True):
    kx, ky, kz, k2 = make_k(n)
    kmax = n / 3.0
    w = ic_vring_lattice(n, n_rings, gamma=gamma, sigma=sigma, R0=R0)
    uh = prepare_from_vorticity(w, kx, ky, kz, k2, kmax)
    B0 = b_charge_hat(uh, kx, ky, kz)
    series = [{"t": 0.0, "B_norm": 1.0,
               "sup_omega": sup_omega_hat(uh, kx, ky, kz),
               "energy": energy_hat(uh)}]
    steps = int(round(t_horizon / dt))
    t = 0.0
    t0 = time.time()
    for step in range(1, steps + 1):
        uh = rk4_step(uh, dt, kx, ky, kz, k2, kmax, nu)
        t = step * dt
        if step % sample_every == 0 or step == steps:
            series.append({"t": t,
                           "B_norm": b_charge_hat(uh, kx, ky, kz) / B0,
                           "sup_omega": sup_omega_hat(uh, kx, ky, kz),
                           "energy": energy_hat(uh)})
            if verbose:
                print(f"    [decay] step {step:5d}/{steps}  t={t:6.3f}  "
                      f"B/B0={series[-1]['B_norm']:.4f}  "
                      f"sup|w|={series[-1]['sup_omega']:.4f}")
    return {"series": series, "B0": B0, "nu": nu, "t_horizon": t,
            "wall_s": time.time() - t0,
            "B_final_over_B0": series[-1]["B_norm"]}


# ----------------------------------------------------------------------------
# EXP G — net rotation angle of N composed kicks (Monte-Carlo on SO(3))
# ----------------------------------------------------------------------------

def _quat_axis_angle(axis, ang):
    return np.concatenate(([math.cos(ang / 2.0)], np.sin(ang / 2.0) * axis))


def _quat_mul(q1, q2):
    w1, x1, y1, z1 = q1
    w2, x2, y2, z2 = q2
    return np.array([w1 * w2 - x1 * x2 - y1 * y2 - z1 * z2,
                     w1 * x2 + x1 * w2 + y1 * z2 - z1 * y2,
                     w1 * y2 - x1 * z2 + y1 * w2 + z1 * x2,
                     w1 * z2 + x1 * y2 - y1 * x2 + z1 * w2])


def _quat_angle(q):
    return 2.0 * math.acos(min(1.0, abs(float(q[0]))))


def exp_net_angle(n_list=(1, 2, 4, 8, 16, 32, 64), trials=4000, seed=SEED):
    rng = np.random.default_rng(seed)
    rows = []
    for N in n_list:
        angles = np.empty(trials)
        for i in range(trials):
            q = np.array([1.0, 0.0, 0.0, 0.0])
            for _ in range(N):
                ax = rng.normal(size=3)
                ax /= np.linalg.norm(ax)
                q = _quat_mul(q, _quat_axis_angle(ax, THETA_B))
            angles[i] = _quat_angle(q)
        rows.append({"N": N,
                     "mean": float(np.mean(angles)),
                     "rms": float(np.sqrt(np.mean(angles ** 2))),
                     "aligned_theory": N * THETA_B,
                     "rms_theory": math.sqrt(N) * THETA_B})
    return {"rows": rows, "trials": trials}


# ----------------------------------------------------------------------------
# EXP F — real water: Kolmogorov bridge from code units to m^3
# ----------------------------------------------------------------------------

NU_WATER = 1.004e-6          # m^2/s, 20 C
FLOWS = [                    # (key, U [m/s], L [m])
    ("tea", 0.1, 0.05),
    ("pipe", 1.0, 0.01),
    ("draupner", 10.0, 100.0),
    ("katrina", 50.0, 30000.0),
]
FLOW_NAMES = {
    "en": {"tea": "stirred tea", "pipe": "tap pipe (1 cm, 1 m/s)",
           "draupner": "Draupner wave", "katrina": "Katrina eyewall"},
    "ru": {"tea": "размешиваемый чай", "pipe": "водопроводная труба",
           "draupner": "волна Драупнера", "katrina": "глаз урагана Катрина"},
}


def water_row(U, L, nu=NU_WATER):
    eps = U ** 3 / L                       # engineering estimate eps ~ U^3/L
    eta = (nu ** 3 / eps) ** 0.25          # Kolmogorov length
    t_eta = math.sqrt(nu / eps)            # Kolmogorov time
    omega_eta = 1.0 / t_eta                # Kolmogorov vorticity
    V1 = 4.0 * math.pi / 3.0 * eta ** 3    # quantum vortex (sphere of radius eta)
    return {"eps": eps, "eta_m": eta, "eta_mm": 1e3 * eta, "t_eta_s": t_eta,
            "omega_eta": omega_eta, "V1_m3": V1, "V1_uL": V1 * 1e9,
            "quanta_per_m3": 1.0 / V1,
            "B_density": 0.5 * omega_eta,            # <|n_b.w|> = 1/2 (random)
            "Q_density": THETA_B * 0.5 * omega_eta,  # kick flux per unit volume
            "kick_turn_fraction": THETA_B / (2.0 * math.pi)}


def exp_water():
    rows = []
    for key, U, L in FLOWS:
        r = water_row(U, L)
        r["key"] = key
        rows.append(r)
    return {"rows": rows, "nu": NU_WATER}


# ----------------------------------------------------------------------------
# figures
# ----------------------------------------------------------------------------

C1, C2, C3 = "#0F2440", "#C25E00", "#5B7C99"

_NO_TITLES = os.environ.get("NSB_NO_TITLES", "0") == "1"


def _title(ax, text):
    """Internal chart title; suppressed when figures get external captions
    (NSB_NO_TITLES=1, used for PDF embedding per charts.md caption rule)."""
    if not _NO_TITLES:
        ax.set_title(text)


def _style(ax):
    ax.grid(True, linestyle="--", alpha=0.20, linewidth=0.6)
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)


def fig_theorem(res, lang, outdir):
    (xd, yd) = res["scatter"]
    fig, ax = plt.subplots(figsize=(6.4, 4.6), constrained_layout=True)
    slobj = res["tg_slope"]
    lim = max(np.max(np.abs(xd)), np.max(np.abs(yd))) * 1.05
    ref = np.linspace(-lim, lim, 10)
    ax.plot(ref, ref, color=C2, lw=1.6, label=r"$y=x$ (theory)")
    ax.plot(ref, slobj["slope"] * ref, color=C3, lw=1.2, ls="--",
            label=f"fit: {slobj['slope']:.4f}$\\,x$")
    step = max(1, len(xd) // 2500)
    ax.scatter(xd[::step], yd[::step], s=4, alpha=0.25, color=C1, edgecolors="none")
    ax.set_xlabel(L["th_x"]); ax.set_ylabel(L["th_y"])
    _title(ax, L["th_scatter"])
    ax.annotate(L["th_note"].format(slope=slobj["slope"], r2=slobj["r2"]),
                xy=(0.03, 0.93), xycoords="axes fraction", fontsize=10,
                bbox=dict(boxstyle="round", fc="#F4F6F8", ec="#C8D0D8"))
    ax.legend(loc="lower right", fontsize=9, frameon=False)
    _style(ax)
    fig.savefig(os.path.join(outdir, "fig1_theorem.png"), dpi=200)
    plt.close(fig)


def fig_nscan(res, lang, outdir):
    rows = res["rows"]
    Ns = [r["N"] for r in rows]
    fig, (a1, a2) = plt.subplots(1, 2, figsize=(9.6, 4.2), constrained_layout=True)
    a1.plot(Ns, [r["Q"] for r in rows], "o-", color=C1, ms=5, label="numerics")
    qv = res["Q_per_vortex"]
    a1.plot(Ns, [qv * n for n in Ns], "--", color=C2, lw=1.4,
            label=f"linear fit: {qv:.4f}$\\cdot N$")
    th = res["theory_Q_per_vortex"]
    a1.plot(Ns, [th * n for n in Ns], ":", color=C3, lw=1.4,
            label=f"theory $\\theta_b\\,\\hat n_{{b,x}}\\Gamma L$: {th:.4f}$\\cdot N$")
    a1.set_xlabel(L["nscan_x"]); a1.set_ylabel(L["nscan_ay"])
    _title(a1, L["nscan_a"]); a1.legend(fontsize=8, frameon=False); _style(a1)
    a2.plot(Ns, [r["dE"] for r in rows], "s-", color=C1, ms=5)
    ev = res["dE_per_vortex"]
    a2.plot(Ns, [ev * n for n in Ns], "--", color=C2, lw=1.4,
            label=f"linear fit: {ev:.3e}$\\cdot N$")
    a2.set_xlabel(L["nscan_x"]); a2.set_ylabel(L["nscan_by"])
    _title(a2, L["nscan_b"]); a2.legend(fontsize=8, frameon=False); _style(a2)
    fig.savefig(os.path.join(outdir, "fig2_nscan.png"), dpi=200)
    plt.close(fig)


def fig_orientation(res, lang, outdir):
    rows = res["rows"]
    xs = np.arange(len(rows))
    fig, ax = plt.subplots(figsize=(6.4, 4.2), constrained_layout=True)
    ax.bar(xs - 0.18, [r["ratio"] for r in rows], width=0.36, color=C1,
           label="numerics")
    ax.bar(xs + 0.18, [r["theory"] for r in rows], width=0.36, color=C2,
           alpha=0.85, label=r"theory $f_{\rm plane}=\langle|\hat n_b\!\cdot\!\hat e_\varphi|\rangle$")
    for i, r in enumerate(rows):
        ax.annotate(f"{r['err_pct']:.2f}%", xy=(i, max(r["ratio"], r["theory"]) + 0.03),
                    ha="center", fontsize=9, color=C1)
    ax.set_xticks(xs)
    ax.set_xticklabels([f"$\\hat m={r['axis']}$" for r in rows])
    ax.set_ylabel(L["orient_y"]); ax.set_xlabel(L["orient_x"])
    _title(ax, L["orient"]); ax.legend(fontsize=9, frameon=False); _style(ax)
    fig.savefig(os.path.join(outdir, "fig3_orientation.png"), dpi=200)
    plt.close(fig)


def fig_volume(res, lang, outdir):
    fg, fo = res["fixed_gamma"], res["fixed_omega"]
    fig, (a1, a2) = plt.subplots(1, 2, figsize=(9.6, 4.2), constrained_layout=True)
    a1.plot([r["V"] for r in fg], [r["Q"] for r in fg], "o-", color=C1, ms=5)
    m = float(np.mean([r["Q"] for r in fg]))
    a1.axhline(m, color=C2, ls="--", lw=1.4, label=L["vol_flat"])
    a1.set_xlabel(L["volume_x"]); a1.set_ylabel(L["volume_y"])
    _title(a1, L["volume_a"]); a1.legend(fontsize=8, frameon=False); _style(a1)
    a2.plot([r["V"] for r in fo], [r["Q"] for r in fo], "s-", color=C1, ms=5,
            label="numerics")
    vmax = max(r["V"] for r in fo)
    slope = res["slope_fixed_omega"]
    a2.plot([0, vmax], [0, slope * vmax], "--", color=C2, lw=1.4,
            label=L["vol_lin"] + f"\n$dQ_b/dV$ = {slope:.5f}")
    a2.set_xlabel(L["volume_x"]); a2.set_ylabel(L["volume_y"])
    _title(a2, L["volume_b"]); a2.legend(fontsize=8, frameon=False); _style(a2)
    fig.savefig(os.path.join(outdir, "fig4_volume.png"), dpi=200)
    plt.close(fig)


def fig_annihilation(res, lang, outdir):
    rows = res["rows"]
    x = [r["dz_over_sigma"] for r in rows]
    fig, ax = plt.subplots(figsize=(6.8, 4.4), constrained_layout=True)
    ax.plot(x, [r["B_co_norm"] for r in rows], "o-", color=C1, ms=5,
            label=L["annih_co"])
    ax.plot(x, [r["B_ap_norm"] for r in rows], "s-", color=C2, ms=5,
            label=L["annih_ap"])
    ax.axhline(2.0, color=C3, ls=":", lw=1.2)
    ax.axhline(0.0, color="#999999", lw=0.8)
    ax.set_xlabel(L["annih_x"]); ax.set_ylabel(L["annih_y"])
    _title(ax, L["annih"]); ax.legend(fontsize=9, frameon=False); _style(ax)
    fig.savefig(os.path.join(outdir, "fig5_annihilation.png"), dpi=200)
    plt.close(fig)


def fig_netang(res, lang, outdir):
    rows = res["rows"]
    Ns = np.array([r["N"] for r in rows], dtype=float)
    fig, ax = plt.subplots(figsize=(6.6, 4.4), constrained_layout=True)
    ax.loglog(Ns, [r["mean"] for r in rows], "o-", color=C1, ms=5,
              label="MC: mean $\\Theta$")
    ax.loglog(Ns, [r["rms"] for r in rows], "s--", color=C2, ms=5,
              label="MC: rms $\\Theta$")
    ref = np.array([Ns[0], Ns[-1]])
    ax.loglog(ref, THETA_B * ref, ":", color=C3, lw=1.4, label=L["netang_al"])
    ax.loglog(ref, THETA_B * np.sqrt(ref), "-.", color="#3B7A57", lw=1.4,
              label=L["netang_rnd"])
    ax.set_xlabel(L["netang_x"]); ax.set_ylabel(L["netang_y"])
    _title(ax, L["netang"]); ax.legend(fontsize=8, frameon=False); _style(ax)
    fig.savefig(os.path.join(outdir, "fig6_netangle.png"), dpi=200)
    plt.close(fig)


def fig_decay(res, lang, outdir):
    s = res["series"]
    t = [r["t"] for r in s]
    b = [r["B_norm"] for r in s]
    w = [r["sup_omega"] for r in s]
    fig, ax = plt.subplots(figsize=(7.0, 4.4), constrained_layout=True)
    ax.plot(t, b, "-", color=C1, lw=1.8, label=L["decay_b"])
    ax.set_xlabel(L["decay_x"]); ax.set_ylabel(L["decay_yL"])
    ax2 = ax.twinx()
    ax2.plot(t, w, "--", color=C2, lw=1.6, label=L["decay_w"])
    ax2.set_ylabel(L["decay_yR"], color=C2)
    ax2.tick_params(axis="y", labelcolor=C2)
    lines = [Line2D([0], [0], color=C1, lw=1.8),
             Line2D([0], [0], color=C2, lw=1.6, ls="--")]
    ax.legend(lines, [L["decay_b"], L["decay_w"]], fontsize=9, frameon=False)
    _title(ax, L["decay"]); _style(ax)
    fig.savefig(os.path.join(outdir, "fig7_decay.png"), dpi=200)
    plt.close(fig)


def fig_water(res, lang, outdir):
    nu = res["nu"]
    fig, ax = plt.subplots(figsize=(7.0, 4.8), constrained_layout=True)
    eps = np.logspace(-3, 4, 200)
    eta = (nu ** 3 / eps) ** 0.25
    V1 = 4.0 * math.pi / 3.0 * eta ** 3
    ax.loglog(eps, V1, "-", color=C1, lw=1.8, label=L["water_line"])
    names = FLOW_NAMES[lang]
    for r in res["rows"]:
        ax.scatter([r["eps"]], [r["V1_m3"]], s=45, color=C2, zorder=5)
        ax.annotate(f"{names[r['key']]}\n"
                    f"$\\eta$={r['eta_mm']:.2f} mm, $V_1$={r['V1_uL']:.3g} $\\mu$L",
                    xy=(r["eps"], r["V1_m3"]), xytext=(8, -4),
                    textcoords="offset points", fontsize=8, color=C1)
    ax.set_xlabel(L["water_x"]); ax.set_ylabel(L["water_y"])
    _title(ax, L["water"]); ax.legend(fontsize=9, loc="lower left", frameon=False)
    _style(ax)
    fig.savefig(os.path.join(outdir, "fig8_water.png"), dpi=200)
    plt.close(fig)


# ----------------------------------------------------------------------------
# main
# ----------------------------------------------------------------------------

L = LABELS["en"]


def _print_water_table(res, lang):
    names = FLOW_NAMES[lang]
    hdr = (f"{'flow':<26}{'eps [m2/s3]':>12}{'eta [mm]':>10}"
           f"{'t_eta [s]':>10}{'omega_eta':>10}{'V1 [uL]':>12}{'N per m3':>12}")
    print("\n  " + hdr)
    print("  " + "-" * len(hdr))
    for r in res["rows"]:
        print(f"  {names[r['key']]:<26}{r['eps']:>12.3g}{r['eta_mm']:>10.3f}"
              f"{r['t_eta_s']:>10.3g}{r['omega_eta']:>10.3g}"
              f"{r['V1_uL']:>12.3g}{r['quanta_per_m3']:>12.3g}")
    print("\n  b-flux density of water = 0.5*theta_b*omega_eta (per unit volume)")
    for r in res["rows"]:
        print(f"  {names[r['key']]:<26} B/W = {r['B_density']:.4g} 1/s"
              f"   Q_b/W = {r['Q_density']:.4g} 1/s")


def main():
    global L
    ap = argparse.ArgumentParser(
        description="b-correction <-> volume research add-on for the NS b-Lab")
    ap.add_argument("--quick", action="store_true",
                    help="smaller grids/shorter runs (CI smoke mode)")
    ap.add_argument("--lang", choices=("en", "ru"), default="en",
                    help="figure label language")
    ap.add_argument("--outdir", default="b_volume_out",
                    help="output directory (default: ./b_volume_out)")
    args = ap.parse_args()
    L = LABELS[args.lang]
    os.makedirs(args.outdir, exist_ok=True)
    np.random.seed(SEED)

    print("=" * 72)
    print("  b-correction <-> volume research  (add-on for navier-stokes-b)")
    print("=" * 72)
    print(f"  b      = 1/(4pi+2*sqrt3) = {B_CONST:.9f}")
    print(f"  theta_b= arcsin(b)       = {THETA_B:.9f} rad = "
          f"{math.degrees(THETA_B):.4f} deg")
    print(f"  n_b    = ({AXIS_B[0]:.4f}, {AXIS_B[1]:.4f}, {AXIS_B[2]:.4f})")
    print(f"  V_box  = (2pi)^3         = {V_BOX:.4f}")
    V_b = 4.0 * math.pi + 2.0 * math.sqrt(3.0)
    print(f"  V_b = 4pi+2*sqrt3        = {V_b:.6f}  (b-volume at unit vorticity)"
          f"  -> {100.0*V_b/V_BOX:.3f}% of the box")
    print(f"  1/theta_b                = {1.0/THETA_B:.6f}  (differs from V_b"
          f" by {100.0*abs(1.0/THETA_B/V_b-1.0):.3f}%)")

    t0 = time.time()
    summary = {
        "constants": {"b": B_CONST, "theta_b": THETA_B,
                      "axis_b": AXIS_B.tolist(), "V_box": V_BOX,
                      "V1_unit_omega": 1.0 / THETA_B,
                      "V1_box_fraction": (4 * math.pi + 2 * math.sqrt(3)) / V_BOX},
    }

    # --- T ------------------------------------------------------------
    nT = 32
    print(f"\n[T] theorem check, n={nT} ...")
    resT = exp_theorem(n=nT)
    for r in resT["results"]:
        print(f"    {r['field']:<14} slope={r['slope']:+.5f}  R2={r['r2']:.6f}"
              f"  {'PASS' if r['pass'] else 'FAIL'}")
    summary["theorem"] = resT["results"]
    fig_theorem(resT, args.lang, args.outdir)

    # --- A ------------------------------------------------------------
    nA = 48 if args.quick else 64
    nlist = (1, 2, 4) if args.quick else (1, 2, 4, 8)
    print(f"\n[A] additivity scan N={nlist}, n={nA} ...")
    resA = exp_nscan(n=nA, n_list=nlist)
    for r in resA["rows"]:
        print(f"    N={r['N']:>3}  B={r['B']:.5f}  Q_b={r['Q']:.5f}"
              f"  dE={r['dE']:.3e}  sup|w|={r['sup_omega']:.4f}")
    print(f"    Q per vortex = {resA['Q_per_vortex']:.6f} "
          f"(theory {resA['theory_Q_per_vortex']:.6f}), "
          f"R2 = {resA['Q_vs_N_r2']:.8f} -> "
          f"{'PASS' if resA['additivity_pass'] else 'FAIL'}")
    summary["nscan"] = resA
    fig_nscan(resA, args.lang, args.outdir)

    # --- B ------------------------------------------------------------
    nB = 48 if args.quick else 64
    print(f"\n[B] orientation algebra, n={nB} ...")
    resB = exp_orientation(n=nB)
    for r in resB["rows"]:
        print(f"    axis {r['axis']}: ratio={r['ratio']:.6f}  "
              f"theory={r['theory']:.6f}  err={r['err_pct']:.3f}%  "
              f"(half-b err={r['err_half_pct']:.3f}%)")
    print(f"    O(theta^2) scaling confirmed: {resB['o2_confirmed']} -> "
          f"{'PASS' if resB['pass'] else 'FAIL'}")
    summary["orientation"] = resB
    fig_orientation(resB, args.lang, args.outdir)

    # --- C ------------------------------------------------------------
    nC = 48 if args.quick else 64
    sig = (0.25, 0.35) if args.quick else (0.2, 0.25, 0.3, 0.35, 0.45)
    print(f"\n[C] volume scans, n={nC} ...")
    resC = exp_volume_scan(n=nC, sigmas=sig)
    print(f"    fixed Gamma: rel dev = {100*resC['flat_rel_dev']:.3f}% "
          f"(should be ~0)")
    print(f"    fixed omega: slope = {resC['slope_fixed_omega']:.6f} "
          f"(theory {resC['theory_slope']:.6f}), "
          f"R2 = {resC['slope_r2']:.8f} -> "
          f"{'PASS' if resC['pass'] else 'FAIL'}")
    summary["volume"] = resC
    fig_volume(resC, args.lang, args.outdir)

    # --- D ------------------------------------------------------------
    nD = 48 if args.quick else 64
    print(f"\n[D] merging pair, n={nD} ...")
    resD = exp_merging(n=nD)
    for r in resD["rows"]:
        print(f"    dz/sigma={r['dz_over_sigma']:>4}: "
              f"B_co/B1={r['B_co_norm']:.4f}  B_ap/B1={r['B_ap_norm']:.4f}")
    print(f"    co-rotating additive: {resD['co_additive']}, "
          f"anti-parallel annihilates: {resD['ap_annihilates']}")
    summary["merging"] = {k: v for k, v in resD.items() if k != "rows"}
    summary["merging_rows"] = resD["rows"]
    fig_annihilation(resD, args.lang, args.outdir)

    # --- E ------------------------------------------------------------
    tE = 0.5 if args.quick else 2.0
    dtE = 0.005 if args.quick else 0.004
    print(f"\n[E] decay of 8 vortex rings, n=48, T={tE} ...")
    resE = exp_decay(n=48, n_rings=8, nu=0.005, dt=dtE, t_horizon=tE,
                     sigma=0.3, R0=0.6)
    print(f"    B_final/B0 = {resE['B_final_over_B0']:.4f} "
          f"(wall {resE['wall_s']:.1f}s)")
    summary["decay"] = {k: v for k, v in resE.items() if k != "series"}
    summary["decay_series"] = resE["series"]
    fig_decay(resE, args.lang, args.outdir)

    # --- G ------------------------------------------------------------
    trials = 600 if args.quick else 4000
    print(f"\n[G] net angle MC, trials={trials} ...")
    resG = exp_net_angle(trials=trials)
    for r in resG["rows"]:
        print(f"    N={r['N']:>3}: mean={r['mean']:.4f} "
              f"(aligned {r['aligned_theory']:.4f})"
              f"  rms={r['rms']:.4f} (sqrt-theory {r['rms_theory']:.4f})")
    summary["net_angle"] = resG
    fig_netang(resG, args.lang, args.outdir)

    # --- F ------------------------------------------------------------
    print("\n[F] real water table ...")
    resF = exp_water()
    _print_water_table(resF, args.lang)
    summary["water"] = resF
    fig_water(resF, args.lang, args.outdir)

    # --- save summary -------------------------------------------------
    passes = {
        "T_theorem": resT["pass"],
        "A_additivity": resA["additivity_pass"],
        "B_orientation": resB["pass"],
        "C_volume": resC["pass"],
        "D_merging": resD["co_additive"] and resD["ap_annihilates"],
    }
    summary["PASS"] = passes
    with open(os.path.join(args.outdir, "summary.json"), "w",
              encoding="utf-8") as f:
        json.dump(summary, f, indent=1, default=float)

    print("\n" + "=" * 72)
    for k, v in passes.items():
        print(f"  {k:<16} {'PASS' if v else 'FAIL'}")
    print(f"  wall total: {time.time()-t0:.1f}s   outdir: {args.outdir}")
    print("=" * 72)
    return 0 if all(passes.values()) else 1


if __name__ == "__main__":
    raise SystemExit(main())
