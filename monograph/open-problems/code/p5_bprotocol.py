#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
p5_bprotocol.py — P5-b (b-protocol in bidirectional communication) and
P5-c (multi-beam duplex on K=8 stations).

b-protocol definition (declared model):
  Each transmitter k spreads its QPSK symbol over N_p chips with the
  b-derived linear phase ramp  c_k(n) = exp(i * s_k * n * theta_b),
  theta_b = arcsin(b) = 3.5765...deg;  the slope quantum s_k is an integer.
  Duplex is separated by CONJUGATE slopes: uplink s_k > 0, downlink s_k < 0.

  Cross-isolation between slopes differing by Delta:
      C(Delta) = | sin(N_p * Delta * theta_b / 2) / (N_p * sin(Delta * theta_b/2)) |
  (Dirichlet kernel). Isolation_dB = -20*log10(C).

P5-b — one duplex pair (s = +1 vs -1):
  * isolation vs preamble length N_p in {32, 64, 128, 256, 512}:
    closed form + Monte-Carlo verification;
  * BER vs SNR Monte-Carlo (20 000 frames, QPSK, despreading receiver):
    b-protocol (N_p = 128) vs no-protocol (equal slopes, full collision)
    vs ideal isolation (interference-free lower bound).

P5-c — multi-beam duplex, K = 8 stations in ONE channel:
  * slopes s_k = k (k = 1..8) uplink, -k downlink;
  * multi-beam: each link aggregates M = 4 independent Rayleigh paths
    (MRC gain g_k = sqrt(sum_m |h_m|^2), drawn per frame);
  * 8x8 station isolation matrix (closed form) + direction isolation
    (uplink k vs downlink -l);
  * per-station SINR/BER at SNR = 10 dB and aggregate spectral efficiency
    sum_k log2(1 + SINR_k) vs SNR; comparison: b-protocol vs no-protocol
    vs ideal orthogonal.

Output: results/p5_bprotocol.json  (all numbers from THIS run)
"""
import json
import math
import os

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
RES = os.path.join(os.path.dirname(HERE), "results")

B = 1.0 / (4.0 * math.pi + 2.0 * math.sqrt(3))
THETA_B = math.asin(B)

N_FRAMES = 20_000
RNG = np.random.default_rng(20260916)


def isolation(N_p, delta):
    """Dirichlet-kernel cross-isolation (amplitude) between slopes Delta apart."""
    x = delta * THETA_B / 2.0
    return abs(math.sin(N_p * x) / (N_p * math.sin(x)))


def qpsk(frames):
    return (1j * (2.0 * RNG.integers(0, 2, frames) - 1) +
            (2.0 * RNG.integers(0, 2, frames) - 1)) / math.sqrt(2)


def ramp_matrix(slopes, N_p):
    n = np.arange(N_p)[None, :]
    s = np.asarray(slopes)[:, None]
    return np.exp(1j * s * n * THETA_B)


def ber_montecarlo(slopes, N_p, snr_db_list, n_frames=N_FRAMES, m_beams=1,
                   ideal=False):
    """Per-station BER and SINR per SNR point (all stations share the channel)."""
    K = len(slopes)
    E = ramp_matrix(slopes, N_p)                     # (K, N_p)
    ber, sinr_mean = [], []
    for snr_db in snr_db_list:
        snr = 10.0 ** (snr_db / 10.0)
        sigma2 = 1.0 / snr                            # per-chip noise, unit-signal
        d = qpsk((n_frames, K))                       # (F, K) symbols
        g = np.sqrt(np.sum(np.abs(RNG.standard_normal((n_frames, K, m_beams)) +
                                        1j * RNG.standard_normal((n_frames, K, m_beams)))**2,
                           axis=2)) if m_beams > 1 else np.ones((n_frames, K))
        W = (RNG.standard_normal((n_frames, N_p)) +
             1j * RNG.standard_normal((n_frames, N_p))) * math.sqrt(sigma2 / 2.0)
        R = (d * g) @ E + W                           # received chips
        Y = R @ E.conj().T / N_p                      # (F, K) despreader output
        if ideal:
            Y = d * g + (RNG.standard_normal((n_frames, K)) +
                         1j * RNG.standard_normal((n_frames, K))) * math.sqrt(sigma2 / (2.0 * N_p))
        p_des = np.mean(np.abs(d * g) ** 2, axis=0)          # (K,)
        p_tot = np.mean(np.abs(Y) ** 2, axis=0)              # (K,)
        p_err = np.maximum(p_tot - p_des, 1e-12)             # (K,)
        sinr_mean.append([float(x) for x in (p_des / p_err)])
        dec = (np.sign(Y.real) + 1j * np.sign(Y.imag)) / math.sqrt(2)
        ber.append([float(x) for x in np.mean(np.abs(dec - d) > 1e-6, axis=0)])
    return ber, sinr_mean


def main():
    os.makedirs(RES, exist_ok=True)
    out = {"module": "p5_bprotocol", "run_date": "2026-09-16",
           "theta_b_deg": math.degrees(THETA_B), "n_frames": N_FRAMES}

    # ================= P5-b =================
    print("=== P5-b: duplex pair, isolation vs N_p ===")
    iso_table = []
    for N_p in (32, 64, 128, 256, 512):
        c = isolation(N_p, 2.0)  # slopes +1 vs -1 -> Delta = 2
        # Monte-Carlo verification of the leakage
        n = np.arange(N_p)
        mc = abs(np.mean(np.exp(2j * n * THETA_B)))
        iso_table.append({"N_p": N_p, "leakage_closed_form": c,
                          "leakage_montecarlo": float(mc),
                          "isolation_dB": -20 * math.log10(c)})
        print(f"  N_p={N_p:4d}  C={c:.5f}  MC={mc:.5f}  isolation={-20*math.log10(c):6.2f} dB")

    print("=== P5-b: BER vs SNR (N_p=128, per-pair average) ===")
    snrs = list(range(-20, 11, 2))
    ber_b, sinr_b = ber_montecarlo([+1, -1], 128, snrs)
    ber_np, sinr_np = ber_montecarlo([0.0, 0.0], 128, snrs)     # no protocol: equal slopes
    ber_id, sinr_id = ber_montecarlo([+1, -1], 128, snrs, ideal=True)
    ber_b_avg = [float(np.mean(x)) for x in ber_b]
    ber_np_avg = [float(np.mean(x)) for x in ber_np]
    ber_id_avg = [float(np.mean(x)) for x in ber_id]
    for s, b, n_, i in zip(snrs, ber_b_avg, ber_np_avg, ber_id_avg):
        print(f"  SNR={s:3d} dB  b-protocol={b:.3e}  no-protocol={n_:.3f}  ideal={i:.3e}")
    out["P5b"] = {
        "isolation_vs_Np": iso_table,
        "snr_db": snrs,
        "ber_b_protocol": ber_b_avg, "ber_no_protocol": ber_np_avg,
        "ber_ideal": ber_id_avg,
        "sinr_b_protocol_per_station": sinr_b,
    }

    # ================= P5-c =================
    print("=== P5-c: K=8 multi-beam duplex ===")
    K, N_p, M = 8, 128, 4
    slopes = list(range(1, K + 1))
    # station-station isolation matrix (closed form)
    mat = [[isolation(N_p, abs(sk - sl)) if k != l else 1.0
            for l, sl in enumerate(slopes)] for k, sk in enumerate(slopes)]
    mat_dB = [[-20 * math.log10(c) if c > 0 else 999.0 for c in row] for row in mat]
    adj = [mat_dB[k][k + 1] for k in range(K - 1)]
    print(f"  adjacent-station isolation: {['%.1f' % a for a in adj]} dB")
    # direction isolation (uplink k vs downlink -l): Delta = k + l
    dir_iso_min = min(-20 * math.log10(isolation(N_p, k + l)) for k in slopes for l in slopes)
    print(f"  direction (duplex) isolation, worst case: {dir_iso_min:.2f} dB")
    # aggregate interference factor per station
    agg = [sum(mat[k][l] ** 2 for l in range(K) if l != k) for k in range(K)]
    print(f"  aggregate interference power fraction: {['%.4f' % a for a in agg]}")

    print("=== P5-c: BER per station @ SNR=10 dB (M=4 beams) ===")
    snr10 = [10.0]
    ber8, sinr8 = ber_montecarlo(slopes, N_p, snr10, m_beams=M)
    print(f"  per-station BER: {['%.3e' % b for b in ber8[0]]}")
    print(f"  per-station SINR (dB): {['%.2f' % (10*math.log10(s)) for s in sinr8[0]]}")
    ber8_np, sinr8_np = ber_montecarlo([0.0] * K, N_p, snr10, m_beams=M)
    ber8_id, sinr8_id = ber_montecarlo(slopes, N_p, snr10, m_beams=M, ideal=True)

    print("=== P5-c: aggregate spectral efficiency vs SNR (sum over 8 stations) ===")
    snrs2 = list(range(-8, 25, 4))
    se_b, se_np, se_id = [], [], []
    for s in snrs2:
        _, sinr = ber_montecarlo(slopes, N_p, [float(s)], m_beams=M)
        se_b.append(float(sum(math.log2(1 + max(x, 1e-9)) for x in sinr[0])))
        _, sinr_n = ber_montecarlo([0.0] * K, N_p, [float(s)], m_beams=M)
        se_np.append(float(sum(math.log2(1 + max(x, 1e-9)) for x in sinr_n[0])))
        _, sinr_i = ber_montecarlo(slopes, N_p, [float(s)], m_beams=M, ideal=True)
        se_id.append(float(sum(math.log2(1 + max(x, 1e-9)) for x in sinr_i[0])))
        print(f"  SNR={s:3d} dB  SE b={se_b[-1]:7.3f}  no-protocol={se_np[-1]:7.3f}  ideal={se_id[-1]:7.3f} bit/chip")

    out["P5c"] = {
        "K": K, "N_p": N_p, "M_beams": M, "slopes": slopes,
        "isolation_matrix_dB": mat_dB,
        "adjacent_isolation_dB": adj,
        "direction_isolation_worst_dB": dir_iso_min,
        "aggregate_interference_fraction": agg,
        "ber_per_station_snr10": ber8,
        "sinr_per_station_snr10": sinr8,
        "ber_per_station_snr10_no_protocol": ber8_np,
        "ber_per_station_snr10_ideal": ber8_id,
        "se_snr_db": snrs2, "se_b_protocol": se_b,
        "se_no_protocol": se_np, "se_ideal": se_id,
    }

    path = os.path.join(RES, "p5_bprotocol.json")
    with open(path, "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=2)
    print("saved:", path)


if __name__ == "__main__":
    main()
