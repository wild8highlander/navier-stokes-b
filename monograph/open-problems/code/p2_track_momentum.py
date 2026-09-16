#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
p2_track_momentum.py — P2: momentum measurement of Wilson-chamber tracks
in a magnetic field, with the b-beading track-width model.

Model (declared):
  * Track: charged particle in uniform B, chord L, sagitta s = L^2/(8R),
    R = p/(0.3 B)  [R in m, p in GeV/c, B in T].
  * Hits: N_seg = 8 measurement points on the arc; parabolic refit;
    Gaussian hit noise sigma_pos.
  * b-beading width model: droplet clusters bead along the track with the
    universal half-angle theta_b = arcsin(b); a bead of pitch lambda_bead
    presents transverse visual width w = lambda_bead * sin(theta_b);
    sigma_pos = w / sqrt(12) (uniform within width).
    Variants: lambda_bead = 1 mm (b-beading, sigma_pos = 18.0 um);
              diffuse halo from P1-b (FWHM 2.812 mm -> sigma_pos = 1.194 mm);
              fine-grain reference (sigma_pos = 5 um).
  * B = 0.5 T, L = 5 cm; p in 0.05..5 GeV/c; 10 000 MC tracks per point.

Output: results/p2_track_momentum.json  (all numbers from THIS run)
"""
import json
import math
import os

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
RES = os.path.join(os.path.dirname(HERE), "results")

B_CONST = 1.0 / (4.0 * math.pi + 2.0 * math.sqrt(3))
THETA_B = math.asin(B_CONST)


def mc_resolution(p, B, L, sigma_pos, n_mc=10_000, n_seg=8, rng=None):
    """MC of sagitta momentum measurement; returns sigma(dp/p)."""
    rng = rng or np.random.default_rng(0)
    R = p / (0.3 * B)                      # m
    s_true = L * L / (8.0 * R)             # m
    x = np.linspace(-L / 2, L / 2, n_seg)
    y_true = x**2 / (2.0 * R)              # parabolic arc approx (fine at these s)
    p_rec = np.empty(n_mc)
    for i in range(n_mc):
        y = y_true + rng.standard_normal(n_seg) * sigma_pos
        c = np.polyfit(x, y, 2)            # y = c2 x^2 + ...
        R_rec = 1.0 / (2.0 * c[0])
        p_rec[i] = 0.3 * B * R_rec
    dp = (p_rec - p) / p
    return float(np.std(dp)), float(s_true)


def main():
    os.makedirs(RES, exist_ok=True)
    rng = np.random.default_rng(20260916)

    lambda_bead = 1.0e-3                    # m
    w_bead = lambda_bead * math.sin(THETA_B)
    sigma_bead = w_bead / math.sqrt(12.0)
    fwhm_halo = 2.812e-3                    # from P1-b run (halo FWHM)
    sigma_halo = fwhm_halo / 2.355
    sigma_fine = 5e-6

    variants = {
        "b_beading_1mm": sigma_bead,
        "diffuse_halo_P1b": sigma_halo,
        "fine_reference": sigma_fine,
    }
    ps = [0.05, 0.1, 0.2, 0.5, 1.0, 2.0, 5.0]
    B, L = 0.5, 0.05

    print("=== P2: track momentum resolution, B=0.5 T, L=5 cm ===")
    print(f"  b-beading width w = lambda*sin(theta_b) = {w_bead*1e6:.1f} um "
          f"(sigma_pos = {sigma_bead*1e6:.1f} um)")
    table = {}
    for name, sig in variants.items():
        row = []
        for p in ps:
            sd, s_true = mc_resolution(p, B, L, sig, rng=rng)
            row.append({"p_GeV": p, "sigma_dp_over_p": sd, "sagitta_um": s_true * 1e6})
        table[name] = row
        r05 = [r for r in row if r["p_GeV"] == 0.5][0]["sigma_dp_over_p"]
        print(f"  {name:18s} sigma_pos={sig*1e6:7.1f} um  ->  dP/P @0.5GeV = {r05*100:6.2f}%")

    out = {
        "module": "p2_track_momentum",
        "run_date": "2026-09-16",
        "parameters": {"B_T": B, "L_m": L, "n_seg": 8, "n_mc": 10_000,
                       "theta_b_deg": math.degrees(THETA_B),
                       "lambda_bead_m": lambda_bead,
                       "w_bead_um": w_bead * 1e6,
                       "halo_FWHM_mm_from_P1b": fwhm_halo * 1e3},
        "sigma_pos": {k: float(v) for k, v in variants.items()},
        "resolution_table": table,
    }
    path = os.path.join(RES, "p2_track_momentum.json")
    with open(path, "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=2)
    print("saved:", path)


if __name__ == "__main__":
    main()
