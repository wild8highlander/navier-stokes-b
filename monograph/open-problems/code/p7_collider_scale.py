#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
p7_collider_scale.py — P7: hadron-collider-scale numerical experiments with
public LHC parameters (b-protocol timing + track-momentum window).

(a) b-preamble synchronization at bunch-crossing timing:
    chip = one bunch crossing, T_c = 25 ns (40.079 MHz RF bucket rate);
    preamble spans N_p = 256 bunches (LHC bunch trains: up to 288 bunches),
    preamble duration = 6.4 us.
    Phase-estimate error (AWGN, Cramer-Rao): sigma_phi = 1/sqrt(2 N_p SNR_chip);
    timing jitter sigma_t = sigma_phi * T_c / (2 pi).
    Direction isolation at N_p = 256 from the P5 Dirichlet kernel (recomputed).

(b) Track-momentum window for a monitor-class detector inside the collider
    environment: B = 3.8 T (CMS-class solenoid), chord L in {5, 20} cm,
    b-beading hit resolution sigma_pos = 18.0 um (from P2, lambda_bead = 1 mm).
    Momentum reach: largest p with sagitta s = 3 sigma_pos.

Output: results/p7_collider_scale.json  (all numbers from THIS run)
"""
import json
import math
import os

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
RES = os.path.join(os.path.dirname(HERE), "results")

B_C = 1.0 / (4.0 * math.pi + 2.0 * math.sqrt(3))
THETA_B = math.asin(B_C)

T_C = 25e-9          # bunch crossing period, s
F_RF = 40.079e6      # LHC RF frequency (public)
N_P = 256
LAMBDA_BEAD = 1.0e-3


def dirichlet(N_p, delta):
    x = delta * THETA_B / 2.0
    return abs(math.sin(N_p * x) / (N_p * math.sin(x)))


def main():
    os.makedirs(RES, exist_ok=True)
    out = {"module": "p7_collider_scale", "run_date": "2026-09-16",
           "public_parameters": {"T_c_ns": T_C * 1e9, "f_RF_Hz": F_RF,
                                 "bunches_per_train_max": 288, "B_solenoid_T": 3.8}}

    # ---------- (a) b-preamble timing ----------
    print("=== P7-a: b-preamble sync at bunch-crossing timing (T_c = 25 ns) ===")
    rows = []
    for snr_db in (-20, -15, -10, -5, 0, 5):
        snr = 10.0 ** (snr_db / 10.0)
        sig_phi = 1.0 / math.sqrt(2.0 * N_P * snr)
        sig_t = sig_phi * T_C / (2.0 * math.pi)
        rows.append({"SNR_chip_dB": snr_db, "sigma_phi_rad": sig_phi,
                     "sigma_t_ns": sig_t * 1e9})
        print(f"  SNR_chip={snr_db:3d} dB  sigma_phi={sig_phi:.4f} rad  "
              f"sigma_t={sig_t*1e9:7.3f} ns")
    iso_dir = -20 * math.log10(dirichlet(N_P, 2.0))
    iso_adj = -20 * math.log10(dirichlet(N_P, 1.0))
    print(f"  isolation @N_p=256: direction(+/-theta_b) {iso_dir:.2f} dB, "
          f"adjacent slope {iso_adj:.2f} dB")
    out["preamble_sync"] = {
        "N_p_bunches": N_P, "preamble_duration_us": N_P * T_C * 1e6,
        "jitter_table": rows,
        "direction_isolation_dB": iso_dir, "adjacent_isolation_dB": iso_adj}

    # ---------- (b) momentum window ----------
    print("=== P7-b: monitor-class momentum window (B = 3.8 T) ===")
    w_bead = LAMBDA_BEAD * math.sin(THETA_B)
    sigma_pos = w_bead / math.sqrt(12.0)
    print(f"  b-beading sigma_pos = {sigma_pos*1e6:.1f} um")
    B_SOL = 3.8
    mom = []
    for L in (0.05, 0.20):
        s3 = 3.0 * sigma_pos
        p_max = 0.3 * B_SOL * L * L / (8.0 * s3)
        # resolution at p = 1 GeV/c
        s1 = L * L / (8.0 * (1.0 / (0.3 * B_SOL)))
        res_1gev = sigma_pos / s1
        mom.append({"L_cm": L * 100, "p_max_GeV_3sigma": p_max,
                    "sigma_dp_over_p_at_1GeV": res_1gev})
        print(f"  L={L*100:4.0f} cm: p_max(3 sigma) = {p_max:6.2f} GeV/c, "
              f"sigma(dp/p) @1 GeV = {res_1gev*100:5.2f}%")
    out["momentum_window"] = {"sigma_pos_um": sigma_pos * 1e6, "B_T": B_SOL,
                              "windows": mom}

    path = os.path.join(RES, "p7_collider_scale.json")
    with open(path, "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=2)
    print("saved:", path)


if __name__ == "__main__":
    main()
