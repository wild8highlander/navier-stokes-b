#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""make_figures.py — 5 figures from THIS session's real run data (results/*.json)."""
import json
import math
import os

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
RES = os.path.join(ROOT, "results")
FIG = os.path.join(ROOT, "figures")
os.makedirs(FIG, exist_ok=True)

plt.rcParams.update({"font.size": 10, "axes.grid": True, "grid.alpha": 0.3})


def load(name):
    with open(os.path.join(RES, name), encoding="utf-8") as f:
        return json.load(f)


def fig_p1b():
    d = load("p1b_droplet_feedback.json")
    b, fb = d["P1_baseline"]["diag"], d["P1b_feedback"]["diag"]
    fig, ax = plt.subplots(1, 3, figsize=(12, 3.6), constrained_layout=True)
    t = np.array(b["t_s"]) * 1e3
    ax[0].plot(t, b["S_track"], "-", lw=2, label="track, no feedback (P1)")
    ax[0].plot(t, b["S_far"], "--", lw=1.2, label="far field, no feedback")
    tf = np.array(fb["t_s"]) * 1e3
    ax[0].plot(tf, fb["S_track"], "-", lw=2, label="track, feedback (P1-b)")
    ax[0].plot(tf, fb["S_far"], "--", lw=1.2, label="far field, feedback")
    ax[0].axhline(1.35, color="k", ls=":", lw=1, label="$S_{ion}$ = 1.35")
    ax[0].set_xlabel("t, ms"); ax[0].set_ylabel("supersaturation S")
    ax[0].set_title("(a) Vapor feedback: S(t)")
    ax[0].legend(fontsize=7.5, loc="upper right")
    ax[0].set_ylim(0, 5.4)

    ax[1].plot(t, b["r_mean_um"], "-", lw=2, label="no feedback (P1)")
    ax[1].plot(tf, fb["r_mean_um"], "-", lw=2, label="feedback (P1-b)")
    ax[1].set_xlabel("t, ms"); ax[1].set_ylabel("mean droplet radius, um")
    ax[1].set_title("(b) Droplet growth r(t)")
    ax[1].legend(fontsize=8)

    ax[2].semilogy(t, np.maximum(np.array(b["water_kg_per_m"]), 1e-12), "-",
                   lw=2, label="no feedback (P1)")
    ax[2].semilogy(tf, np.maximum(np.array(fb["water_kg_per_m"]), 1e-12), "-",
                   lw=2, label="feedback (P1-b)")
    ax[2].set_xlabel("t, ms"); ax[2].set_ylabel("condensed water, kg/m")
    ax[2].set_title("(c) Track visibility (condensed mass)")
    ax[2].legend(fontsize=8)
    fig.suptitle("P1-b: droplet feedback / vapor depletion — 3D Wilson chamber "
                 "(run 2026-09-16)", fontsize=11)
    fig.savefig(os.path.join(FIG, "fig_p1b_feedback.png"), dpi=200)
    plt.close(fig)


def fig_p4c():
    d = load("p4_ensemble.json")
    e = d["ensemble"]
    pooled = d["pooled_ensemble_plume"]
    T = [x["T"] for x in e]
    mean = [x["mean_delta_percent"] for x in e]
    se = [x["se_percent"] for x in e]
    tstat = [x["t_stat"] for x in e]
    fig, ax = plt.subplots(1, 2, figsize=(10, 4), constrained_layout=True)
    ax[0].errorbar(T, mean, yerr=[1.96 * s for s in se], fmt="o-", capsize=4,
                   lw=1.8, label="per-realization mean $\\pm$ 1.96 SE")
    ax[0].plot(T, [p["pooled_delta_percent"] for p in pooled], "s--", ms=5,
               lw=1.2, color="tab:red", label="pooled ensemble-plume width")
    ax[0].axhspan(4.0, 6.5, alpha=0.12, color="green", label="~5% trace band")
    ax[0].set_xscale("log", base=2)
    ax[0].set_xticks(T); ax[0].set_xticklabels([str(x) for x in T])
    ax[0].set_xlabel("ensemble size T"); ax[0].set_ylabel("$\\Delta\\sigma_y$ / $\\sigma_y$, %")
    ax[0].set_title("(a) The b-trace vs ensemble size (Re = 2000)")
    ax[0].legend(fontsize=8)
    ax2 = ax[1]
    ax2.plot(T, tstat, "o-", lw=1.8, label="t-statistic")
    ax2.set_xscale("log", base=2)
    ax2.set_xticks(T); ax2.set_xticklabels([str(x) for x in T])
    ax2.set_xlabel("ensemble size T"); ax2.set_ylabel("t = mean / SE")
    ref = [tstat[0] * math.sqrt(x / T[0]) for x in T]
    ax2.plot(T, ref, "k:", lw=1.2, label="$\\propto\\sqrt{T}$ reference")
    ax2.set_title("(b) Significance growth")
    ax2.legend(fontsize=8)
    fig.suptitle("P4-c: does the 5%-trace grow? — magnitude stable, significance grows "
                 "(run 2026-09-16)", fontsize=11)
    fig.savefig(os.path.join(FIG, "fig_p4c_ensemble.png"), dpi=200)
    plt.close(fig)


def fig_p5():
    d = load("p5_bprotocol.json")
    fig, ax = plt.subplots(2, 2, figsize=(11, 8), constrained_layout=True)
    iso = d["P5b"]["isolation_vs_Np"]
    nps = [x["N_p"] for x in iso]
    ax[0, 0].plot(nps, [x["isolation_dB"] for x in iso], "o-", lw=1.8,
                  label="closed form (Dirichlet kernel)")
    ax[0, 0].plot(nps, [-20 * math.log10(x["leakage_montecarlo"]) for x in iso],
                  "x", ms=7, label="Monte-Carlo check")
    ax[0, 0].set_xscale("log", base=2)
    ax[0, 0].set_xticks(nps); ax[0, 0].set_xticklabels([str(x) for x in nps])
    ax[0, 0].set_xlabel("preamble length $N_p$ (chips)")
    ax[0, 0].set_ylabel("cross-isolation, dB")
    ax[0, 0].set_title("(a) P5-b: duplex isolation vs preamble length")
    ax[0, 0].legend(fontsize=8)

    snrs = d["P5b"]["snr_db"]
    ax[0, 1].semilogy(snrs, np.maximum(d["P5b"]["ber_b_protocol"], 1e-5), "o-",
                      lw=1.8, label="b-protocol ($N_p$=128)")
    ax[0, 1].semilogy(snrs, np.maximum(d["P5b"]["ber_ideal"], 1e-5), "s--",
                      lw=1.2, label="ideal isolation (bound)")
    ax[0, 1].semilogy(snrs, np.maximum(d["P5b"]["ber_no_protocol"], 1e-5), "^-",
                      lw=1.5, label="no protocol (collision)")
    ax[0, 1].set_xlabel("chip SNR, dB"); ax[0, 1].set_ylabel("BER")
    ax[0, 1].set_title("(b) P5-b: duplex BER")
    ax[0, 1].legend(fontsize=8); ax[0, 1].set_ylim(1e-5, 1)

    mat = np.array(d["P5c"]["isolation_matrix_dB"])
    im = ax[1, 0].imshow(mat, cmap="viridis_r", vmin=0, vmax=40)
    for i in range(mat.shape[0]):
        for j in range(mat.shape[1]):
            ax[1, 0].text(j, i, f"{mat[i, j]:.1f}", ha="center", va="center",
                          color="w", fontsize=7)
    ax[1, 0].set_xticks(range(8)); ax[1, 0].set_xticklabels(range(1, 9))
    ax[1, 0].set_yticks(range(8)); ax[1, 0].set_yticklabels(range(1, 9))
    ax[1, 0].set_xlabel("station l"); ax[1, 0].set_ylabel("station k")
    ax[1, 0].set_title("(c) P5-c: isolation matrix (dB), K=8")
    fig.colorbar(im, ax=ax[1, 0], shrink=0.85)

    snrs2 = d["P5c"]["se_snr_db"]
    ax[1, 1].plot(snrs2, d["P5c"]["se_b_protocol"], "o-", lw=1.8,
                  label="b-protocol K=8, M=4")
    ax[1, 1].plot(snrs2, d["P5c"]["se_ideal"], "s--", lw=1.2,
                  label="ideal orthogonal (bound)")
    ax[1, 1].plot(snrs2, d["P5c"]["se_no_protocol"], "^-", lw=1.5,
                  label="no protocol (collision)")
    ax[1, 1].set_xlabel("chip SNR, dB")
    ax[1, 1].set_ylabel("aggregate SE, bit/chip (sum over 8)")
    ax[1, 1].set_title("(d) P5-c: aggregate spectral efficiency")
    ax[1, 1].legend(fontsize=8)
    fig.suptitle("P5-b / P5-c: b-protocol in bidirectional and multi-station "
                 "duplex (run 2026-09-16)", fontsize=11)
    fig.savefig(os.path.join(FIG, "fig_p5c_duplex.png"), dpi=200)
    plt.close(fig)


def fig_p6():
    d = load("p6_taylor_green_bkm.json")
    dg = d["diag"]
    t = dg["t"]
    fig, ax = plt.subplots(1, 2, figsize=(10, 4), constrained_layout=True)
    ax[0].plot(t, dg["max_omega_baseline"], lw=1.8, label="baseline TG")
    ax[0].plot(t, dg["max_omega_b"], lw=1.8, ls="--",
               label=f"$\\theta_b$-rotated (factor {d['factor_b_over_baseline']:.4f})")
    ax[0].set_xlabel("t"); ax[0].set_ylabel("max $|\\omega|$")
    ax[0].set_title(f"(a) BKM envelope: I = $\\int$ max$|\\omega|$ dt  "
                    f"= {d['I_BKM_baseline']:.3f} / {d['I_BKM_b_rotated']:.3f}")
    ax[0].legend(fontsize=8)
    ax[1].plot(t, dg["E_baseline"], lw=1.8, label="baseline TG")
    ax[1].plot(t, dg["E_b"], lw=1.8, ls="--",
               label=f"$\\theta_b$-rotated (max|$\\Delta$E| = {d['max_abs_dE']:.2e})")
    ax[1].set_xlabel("t"); ax[1].set_ylabel("E(t)")
    ax[1].set_title("(b) Energy trajectories")
    ax[1].legend(fontsize=8)
    fig.suptitle("P6: Taylor-Green 3D (N=32, $\\nu$=0.01): universal rotation "
                 "$\\theta_b$ response (run 2026-09-16)", fontsize=11)
    fig.savefig(os.path.join(FIG, "fig_p6_bkm.png"), dpi=200)
    plt.close(fig)


def fig_p27():
    p2 = load("p2_track_momentum.json")
    p7 = load("p7_collider_scale.json")
    fig, ax = plt.subplots(1, 3, figsize=(13, 3.8), constrained_layout=True)
    for name, style in (("b_beading_1mm", "o-"), ("fine_reference", "s--")):
        row = p2["resolution_table"][name]
        ps = [r["p_GeV"] for r in row]
        res = [r["sigma_dp_over_p"] * 100 for r in row]
        ax[0].semilogy(ps, res, style, lw=1.8,
                       label=f"{name} ($\\sigma_{{pos}}$={p2['sigma_pos'][name]*1e6:.0f} um)")
    ax[0].set_xlabel("p, GeV/c"); ax[0].set_ylabel("$\\sigma(\\Delta p/p)$, %")
    ax[0].set_title("(a) P2: track momentum, B=0.5 T, L=5 cm")
    ax[0].legend(fontsize=8)

    jt = p7["preamble_sync"]["jitter_table"]
    ax[1].semilogy([r["SNR_chip_dB"] for r in jt],
                   [r["sigma_t_ns"] for r in jt], "o-", lw=1.8)
    ax[1].set_xlabel("chip SNR, dB"); ax[1].set_ylabel("timing jitter, ns")
    ax[1].set_title("(b) P7-a: b-preamble sync, $T_c$=25 ns, $N_p$=256")
    ax[1].axhline(25, color="k", ls=":", lw=1, label="1 bunch crossing")
    ax[1].legend(fontsize=8)

    wins = p7["momentum_window"]["windows"]
    labels = [f"L={w['L_cm']:.0f} cm" for w in wins]
    ax[2].bar(labels, [w["p_max_GeV_3sigma"] for w in wins], color=["#3776ab", "#2ea043"])
    for i, w in enumerate(wins):
        ax[2].text(i, w["p_max_GeV_3sigma"] * 1.05,
                   f"{w['p_max_GeV_3sigma']:.1f} GeV\n({w['sigma_dp_over_p_at_1GeV']*100:.2f}% @1GeV)",
                   ha="center", fontsize=8)
    ax[2].set_ylabel("p reach at 3$\\sigma$, GeV/c")
    ax[2].set_title("(c) P7-b: monitor momentum window, B=3.8 T")
    ax[2].set_ylim(0, 130)
    fig.suptitle("P2 / P7: detector- and collider-scale applications of the "
                 "b-geometry (run 2026-09-16)", fontsize=11)
    fig.savefig(os.path.join(FIG, "fig_p2_p7_applications.png"), dpi=200)
    plt.close(fig)


if __name__ == "__main__":
    fig_p1b(); print("fig_p1b_feedback.png done")
    fig_p4c(); print("fig_p4c_ensemble.png done")
    fig_p5(); print("fig_p5c_duplex.png done")
    fig_p6(); print("fig_p6_bkm.png done")
    fig_p27(); print("fig_p2_p7_applications.png done")
