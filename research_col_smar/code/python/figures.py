"""figures.py — publication figures for the monograph, RU and EN editions.

Usage:  python3 figures.py ru   /   python3 figures.py en

Reads results/*.json, *.csv and *.npy produced by P1-P4 and writes
figures/<lang>/fig_*.png at 300 dpi. Style follows the document palette
(cascade palette of the PDF track) and the chart rules of the pdf skill:
no top/right spines, dashed grid at 20% opacity, legends without frames.
"""

from __future__ import annotations

import csv
import json
import os
import sys

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
RESULTS = os.path.join(ROOT, "results")
FIG = os.path.join(ROOT, "figures")

# cascade palette (auto-generated, seed 42)
C_ACCENT = "#92761f"
C_ACCENT2 = "#3aa0c2"
C_HEADER = "#4e4732"
C_ICON = "#a48e4b"
C_TEXT = "#151513"
C_MUTED = "#7e7c74"
C_BORDER = "#c5bfac"

plt.rcParams.update(
    {
        "font.family": "DejaVu Sans",
        "font.size": 11,
        "axes.edgecolor": C_BORDER,
        "axes.labelcolor": C_TEXT,
        "xtick.color": C_MUTED,
        "ytick.color": C_MUTED,
        "axes.linewidth": 0.8,
    }
)

L = {
    "ru": {
        "ck": r"постоянная Колмогорова $C_K$",
        "cs": r"постоянная Смагоринского $C_s$",
        "cs_imp": r"$C_s$ (вывод из согласования)",
        "chi": r"$k\eta$",
        "comp": r"$k^{5/3}E(k)/\varepsilon^{2/3}$",
        "E": r"$E(k)$",
        "k": r"$k$",
        "d_eta": r"$\Delta/\eta$",
        "inertial": "инерционный интервал",
        "sharp": "спектральный срез",
        "gaussian": "гауссов фильтр",
        "box": "фильтр-прямоугольник",
        "heisenberg": "замыкание Гейзенберга",
        "pao": "модель Пао",
        "alpha": r"константа замыкания $\alpha$",
        "synth": "синтетические K41-поля (P3)",
        "analytic": "аналитика",
        "real": "DNS-турбулентность (P4)",
        "dynamic": "динамическая процедура Германо",
        "vorticity": "завихренность $|\\omega|$ (срез)",
        "exp": "эксперимент",
        "closure": "замыкания/теория",
        "thiswork": "эта работа",
        "ck_liter": r"значения $C_K$ в литературе и в этой работе",
        # P5: regularity / smoothness figures
        "enst": r"энстрофия $\Omega(t) = \langle \omega^2 \rangle$",
        "bkm": r"интеграл BKM $I(t) = \int_0^t \|\omega\|_\infty ds$",
        "t": r"$t$",
        "runA": "базовый TG (A)",
        "runB": "b-поворот (B)",
        "peak": "пик энстрофии",
        "dk": r"$D_b(k) = 2\nu k^{2b} E(k)$, $t = 2$",
        "kdeta": r"$k_d \eta_b$ (измерение)",
        "xstar": r"$x^*(b)$ (теория)",
        "collapse": r"универсальный пик диссипации: $k_d\eta_b$ против $x^*(b)$",
        "bis": r"$b$ (степень гипердиссипации)",
        "ek_semilog": r"$E(k)$, полулог. масштаб",
        "cert_t": "экспоненциальный хвост при $t$ =",
        "r2": r"качество подгонки $R^2$",
        "r2exp": r"$R^2$ экспоненты $e^{-ck}$",
        "r2pow": r"$R^2$ степени $k^{-\sigma}$",
        "cert_title": "спектральный сертификат гладкости (P5, прогон A)",
        "colorbar": "завихренность",
    },
    "en": {
        "ck": r"Kolmogorov constant $C_K$",
        "cs": r"Smagorinsky constant $C_s$",
        "cs_imp": r"$C_s$ (matching inference)",
        "chi": r"$k\eta$",
        "comp": r"$k^{5/3}E(k)/\varepsilon^{2/3}$",
        "E": r"$E(k)$",
        "k": r"$k$",
        "d_eta": r"$\Delta/\eta$",
        "inertial": "inertial range",
        "sharp": "sharp spectral cutoff",
        "gaussian": "Gaussian filter",
        "box": "box filter",
        "heisenberg": "Heisenberg closure",
        "pao": "Pao model",
        "alpha": r"closure constant $\alpha$",
        "synth": "synthetic K41 fields (P3)",
        "analytic": "analytic",
        "real": "DNS turbulence (P4)",
        "dynamic": "dynamic Germano procedure",
        "vorticity": r"vorticity $|\omega|$ (slice)",
        "exp": "experiment",
        "closure": "closures / theory",
        "thiswork": "this work",
        "ck_liter": r"$C_K$ values in the literature and this work",
        # P5: regularity / smoothness figures
        "enst": r"enstrophy $\Omega(t) = \langle \omega^2 \rangle$",
        "bkm": r"BKM integral $I(t) = \int_0^t \|\omega\|_\infty ds$",
        "t": r"$t$",
        "runA": "baseline TG (A)",
        "runB": "b-rotated (B)",
        "peak": "enstrophy peak",
        "dk": r"$D_b(k) = 2\nu k^{2b} E(k)$, $t = 2$",
        "kdeta": r"$k_d \eta_b$ (measured)",
        "xstar": r"$x^*(b)$ (theory)",
        "collapse": r"universal dissipation peak: $k_d\eta_b$ vs $x^*(b)$",
        "bis": r"$b$ (hyperdissipation power)",
        "ek_semilog": r"$E(k)$, semilog scale",
        "cert_t": "exponential tail at $t$ =",
        "r2": r"fit quality $R^2$",
        "r2exp": r"$R^2$ of exponential $e^{-ck}$",
        "r2pow": r"$R^2$ of power law $k^{-\sigma}$",
        "cert_title": "spectral smoothness certificate (P5, run A)",
        "colorbar": "vorticity",
    },
}[sys.argv[1] if len(sys.argv) > 1 else "en"]

LANG = sys.argv[1] if len(sys.argv) > 1 else "en"


def style_ax(ax):
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.grid(True, linestyle="--", linewidth=0.5, alpha=0.2, color=C_HEADER)


def save(fig, name):
    out = os.path.join(FIG, LANG, name)
    fig.savefig(out, dpi=300, facecolor="white")
    plt.close(fig)
    print(f"[fig] {out}")


def fig1_master_lilly():
    rows = []
    with open(os.path.join(RESULTS, "p1_lilly_table.csv")) as fh:
        for r in csv.DictReader(fh):
            rows.append({k: float(v) for k, v in r.items()})
    ck = [r["C_K"] for r in rows]
    fig, ax = plt.subplots(figsize=(7.2, 4.4), constrained_layout=True)
    ax.plot(
        ck, [r["C_s_sharp"] for r in rows], color=C_ACCENT, lw=2.2, label=L["sharp"]
    )
    ax.plot(
        ck,
        [r["C_s_gaussian"] for r in rows],
        color=C_ACCENT2,
        lw=2.2,
        label=L["gaussian"],
    )
    ax.plot(
        ck, [r["C_s_box"] for r in rows], color=C_ICON, lw=2.2, ls="--", label=L["box"]
    )
    ax.axhspan(0.16, 0.185, color=C_ACCENT, alpha=0.08, lw=0)
    ax.plot(
        [1.5], [0.17326], marker="o", ms=9, mfc="white", mec=C_ACCENT, mew=2.0, zorder=5
    )
    ax.annotate(
        r"$C_s = \frac{1}{\pi(3C_K/2)^{3/4}} \approx 0.173$",
        xy=(1.5, 0.17326),
        xytext=(1.32, 0.139),
        color=C_TEXT,
        fontsize=12,
        arrowprops=dict(arrowstyle="->", color=C_MUTED, lw=1.0),
    )
    ax.set_xlabel(L["ck"])
    ax.set_ylabel(L["cs"])
    ax.set_xlim(1.28, 1.87)
    ax.set_ylim(0.13, 0.202)
    style_ax(ax)
    ax.legend(frameon=False, loc="upper right")
    save(fig, "fig1_master_lilly.png")


def fig2_spectra_closures():
    chi = []
    eh = []
    ep = []
    with open(os.path.join(RESULTS, "p2_spectra.csv")) as fh:
        for r in csv.DictReader(fh):
            chi.append(float(r["chi"]))
            eh.append(float(r["E_heisenberg_scaled"]))
            ep.append(float(r["E_pao_scaled"]))
    fig, ax = plt.subplots(figsize=(7.2, 4.4), constrained_layout=True)
    ax.axvspan(0.05, 0.5, color=C_ACCENT, alpha=0.06, lw=0)
    ax.plot(chi, eh, color=C_ACCENT, lw=2.2, label=L["heisenberg"])
    ax.plot(chi, ep, color=C_ACCENT2, lw=2.2, ls="--", label=L["pao"])
    ax.axhline(1.5, color=C_MUTED, lw=1.0, ls=":")
    ax.annotate(L["inertial"], xy=(0.06, 1.9), color=C_MUTED, fontsize=10)
    ax.set_xscale("log")
    ax.set_yscale("log")
    ax.set_xlabel(L["chi"])
    ax.set_ylabel(L["comp"])
    ax.set_ylim(1e-5, 4)
    style_ax(ax)
    ax.legend(frameon=False, loc="lower left")
    save(fig, "fig2_spectra_closures.png")


def fig3_ck_alpha():
    alpha = np.linspace(0.28, 0.9, 200)
    ckh = (8.0 / (9.0 * alpha)) ** (2.0 / 3.0)
    fig, ax = plt.subplots(figsize=(7.2, 4.2), constrained_layout=True)
    ax.plot(alpha, ckh, color=C_ACCENT, lw=2.2, label=L["heisenberg"])
    pts = [
        (1.50, "Sreenivasan 1995", C_ACCENT),
        (1.52, "LhDIA (Kraichnan 1965)", C_ACCENT2),
        (1.77, "DIA (Kraichnan 1959)", C_ICON),
    ]
    for yv, name, col in pts:
        ax.axhline(yv, color=col, lw=1.0, ls=":", alpha=0.8)
        ax.annotate(
            name,
            xy=(0.88, yv),
            xycoords=("axes fraction", "data"),
            fontsize=9,
            color=C_MUTED,
            va="bottom",
            ha="right",
        )
    for yv, _, col in pts:
        ax.plot(
            [sk_alpha(yv)],
            [yv],
            marker="o",
            ms=7,
            mfc="white",
            mec=col,
            mew=1.8,
            zorder=5,
        )
    ax.set_xlabel(L["alpha"])
    ax.set_ylabel(L["ck"])
    ax.set_ylim(1.1, 2.2)
    style_ax(ax)
    save(fig, "fig3_ck_alpha.png")


def sk_alpha(ckv):
    return 8.0 / (9.0 * ckv**1.5)


def fig4_p3_convergence():
    with open(os.path.join(RESULTS, "p3_synthetic_apriori.json")) as fh:
        p3 = json.load(fh)
    rows = p3["rows"]
    fig, ax = plt.subplots(figsize=(7.2, 4.4), constrained_layout=True)
    for fkind, col, marker in (("sharp", C_ACCENT, "o"), ("gaussian", C_ACCENT2, "s")):
        dd = [r["Delta_over_eta"] for r in rows if r["filter"] == fkind]
        cc = [r["C_s_implied"] for r in rows if r["filter"] == fkind]
        ax.plot(
            dd,
            cc,
            marker=marker,
            ms=6,
            lw=1.4,
            color=col,
            alpha=0.85,
            label=f"{L['synth']}, {L[fkind]}",
        )
    # analytic curves from C++ track
    p3c = os.path.join(RESULTS, "p3_cpp.json")
    if os.path.exists(p3c):
        with open(p3c) as fh:
            p3cpp = json.load(fh)
        for fkind, col in (("sharp", C_ACCENT), ("gaussian", C_ACCENT2)):
            rr = [r for r in p3cpp["rows"] if r["filter"] == fkind]
            ax.plot(
                [r["Delta_over_eta"] for r in rr],
                [r["C_s"] for r in rr],
                color=col,
                lw=1.6,
                ls="--",
                alpha=0.9,
            )
        ax.plot([], [], color=C_MUTED, lw=1.6, ls="--", label=L["analytic"])
    ax.axhline(0.17326, color=C_MUTED, lw=1.0, ls=":")
    ax.annotate(
        "Lilly 1966: 0.173",
        xy=(0.98, 0.17326),
        xycoords=("axes fraction", "data"),
        xytext=(0, 4),
        textcoords="offset points",
        ha="right",
        color=C_MUTED,
        fontsize=9,
    )
    ax.set_xscale("log")
    ax.set_xlabel(L["d_eta"])
    ax.set_ylabel(L["cs"])
    ax.set_ylim(0.148, 0.42)
    style_ax(ax)
    ax.legend(frameon=False, loc="upper right", fontsize=9)
    save(fig, "fig4_p3_convergence.png")


def fig5_p4_dns():
    spec_path = os.path.join(RESULTS, "p4_spectrum.npy")
    vor_path = os.path.join(RESULTS, "p4_vorticity_slice.npy")
    if not (os.path.exists(spec_path) and os.path.exists(vor_path)):
        print("[fig] p4 outputs missing, skip fig5")
        return
    e = np.load(spec_path)
    vor = np.load(vor_path)
    fig, (ax1, ax2) = plt.subplots(
        1,
        2,
        figsize=(9.6, 4.2),
        constrained_layout=True,
        gridspec_kw={"width_ratios": [1.0, 1.15]},
    )
    im = ax1.imshow(
        vor.T,
        origin="lower",
        cmap="RdBu_r",
        vmin=0.0,
        vmax=np.percentile(vor, 99),
        extent=[0, 2 * np.pi, 0, 2 * np.pi],
    )
    ax1.set_title(L["vorticity"], fontsize=11, color=C_TEXT)
    ax1.set_xticks([])
    ax1.set_yticks([])
    fig.colorbar(im, ax=ax1, shrink=0.85, pad=0.02)
    kk = np.arange(len(e), dtype=float)
    kk = kk[1:]
    ee = e[1:]
    ax2.loglog(
        kk,
        ee,
        color=C_ACCENT,
        lw=1.8,
        marker="o",
        ms=3.5,
        mfc="white",
        mec=C_ACCENT,
        mew=0.8,
        label=L["real"],
    )
    kref = np.logspace(np.log10(6), np.log10(14), 20)
    mask = (kk >= 6) & (kk <= 14)
    if mask.any():
        scale = float(np.mean(ee[mask] * kk[mask] ** (5.0 / 3.0)))
        ax2.loglog(
            kref,
            scale * kref ** (-5.0 / 3.0),
            color=C_MUTED,
            ls="--",
            lw=1.4,
            label=r"$k^{-5/3}$",
        )
    ax2.set_xlabel(L["k"])
    ax2.set_ylabel(L["E"])
    style_ax(ax2)
    ax2.legend(frameon=False, loc="lower left", fontsize=9)
    save(fig, "fig5_p4_dns.png")


def fig6_p4_apriori():
    path = os.path.join(RESULTS, "p4_apriori.csv")
    if not os.path.exists(path):
        print("[fig] p4 apriori missing, skip fig6")
        return
    rows = []
    with open(path) as fh:
        for r in csv.DictReader(fh):
            rows.append({k: float(v) for k, v in r.items()})
    dd = sorted({r["Delta_over_dx"] for r in rows})
    means = []
    stds = []
    for d in dd:
        sel = [r["C_s"] for r in rows if r["Delta_over_dx"] == d]
        means.append(float(np.mean(sel)))
        stds.append(float(np.std(sel)))
    fig, ax = plt.subplots(figsize=(7.2, 4.4), constrained_layout=True)
    ax.errorbar(
        dd,
        means,
        yerr=stds,
        fmt="o",
        ms=7,
        color=C_ACCENT,
        ecolor=C_BORDER,
        capsize=4,
        mfc="white",
        mew=1.6,
        label=L["real"],
    )
    with open(os.path.join(RESULTS, "p4_dns_les.json")) as fh:
        p4 = json.load(fh)
    dyn = [
        d["C_s_dynamic"]
        for d in p4.get("dynamic_C_s", [])
        if d["C_s_dynamic"] == d["C_s_dynamic"]
    ]
    if dyn:
        ax.axhspan(min(dyn), max(dyn), color=C_ACCENT2, alpha=0.15, lw=0)
        ax.axhline(
            float(np.mean(dyn)), color=C_ACCENT2, lw=1.6, ls="--", label=L["dynamic"]
        )
    ax.axhline(0.17326, color=C_MUTED, lw=1.0, ls=":", label="Lilly 1966")
    ax.set_xlabel(r"$\Delta / \Delta x$")
    ax.set_ylabel(L["cs"])
    style_ax(ax)
    ax.legend(frameon=False, loc="upper left", fontsize=9)
    save(fig, "fig6_p4_apriori.png")


def fig7_ck_summary():
    entries = [
        ("Grant et al. 1962", 1.46, "exp"),
        ("Champagne 1978", 1.50, "exp"),
        ("Sreenivasan 1995", 1.50, "exp"),
        ("LhDIA 1965", 1.52, "closure"),
        ("DIA 1959", 1.77, "closure"),
        ("Heisenberg (P2)", None, "this"),
        ("Sabra/LES (P4)", None, "this"),
    ]
    with open(os.path.join(RESULTS, "p2_closures.json")) as fh:
        p2 = json.load(fh)
    heis_ck = p2["heisenberg"]["inertial_C_K_measured"]
    vals, names, colors = [], [], []
    for name, val, kind in entries:
        if kind == "this":
            if name.startswith("Heisenberg"):
                val = heis_ck
            else:
                p4p = os.path.join(RESULTS, "p4_dns_les.json")
                if not os.path.exists(p4p):
                    continue
                with open(p4p) as fh:
                    val = json.load(fh)["kolmogorov_constant"]["C_K_constrained_fit"]
        vals.append(val)
        names.append(name)
        colors.append({"exp": C_ACCENT, "closure": C_ACCENT2, "this": C_HEADER}[kind])
    fig, ax = plt.subplots(figsize=(7.6, 4.6), constrained_layout=True)
    ypos = np.arange(len(vals))[::-1]
    ax.barh(ypos, vals, height=0.62, color=colors, alpha=0.88)
    for y, v in zip(ypos, vals):
        ax.text(v + 0.015, y, f"{v:.3f}", va="center", fontsize=9.5, color=C_TEXT)
    ax.axvline(1.5, color=C_MUTED, lw=1.2, ls=":")
    ax.set_yticks(ypos)
    ax.set_yticklabels(names, fontsize=9.5)
    ax.set_xlabel(L["ck"])
    ax.set_title(L["ck_liter"], fontsize=11, color=C_TEXT, loc="left")
    ax.set_xlim(1.2, 1.95)
    style_ax(ax)
    save(fig, "fig7_ck_summary.png")


def fig8_regularity():
    path = os.path.join(RESULTS, "p5_bkm.csv")
    if not os.path.exists(path):
        print("[fig] p5_bkm.csv missing, skip fig8")
        return
    rows = []
    with open(path) as fh:
        for r in csv.DictReader(fh):
            rows.append({k: float(v) for k, v in r.items()})
    t = np.array([r["t"] for r in rows])
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(9.6, 4.2), constrained_layout=True)
    ax1.plot(t, [r["Omega_A"] for r in rows], color=C_ACCENT, lw=2.0, label=L["runA"])
    ax1.plot(t, [r["Omega_B"] for r in rows], color=C_ACCENT2, lw=2.0, ls="--", label=L["runB"])
    om_a = np.array([r["Omega_A"] for r in rows])
    tp = t[int(np.argmax(om_a))]
    ax1.axvline(tp, color=C_MUTED, lw=1.0, ls=":")
    ax1.annotate(L["peak"], xy=(tp, om_a.max()), xytext=(0.35, 1.24),
                 color=C_MUTED, fontsize=9,
                 arrowprops=dict(arrowstyle="->", color=C_MUTED, lw=0.9))
    ax1.set_xlabel(L["t"])
    ax1.set_ylabel(L["enst"])
    style_ax(ax1)
    ax1.legend(frameon=False, loc="upper right", fontsize=9)
    ax2.plot(t, [r["I_BKM_A"] for r in rows], color=C_ACCENT, lw=2.0, label=L["runA"])
    ax2.plot(t, [r["I_BKM_B"] for r in rows], color=C_ACCENT2, lw=2.0, ls="--", label=L["runB"])
    ax2.set_xlabel(L["t"])
    ax2.set_ylabel(L["bkm"])
    style_ax(ax2)
    ax2.legend(frameon=False, loc="upper left", fontsize=9)
    save(fig, "fig8_regularity.png")


def fig9_bfamily():
    path = os.path.join(RESULTS, "p5_bfamily.csv")
    if not os.path.exists(path):
        print("[fig] p5_bfamily.csv missing, skip fig9")
        return
    rows = []
    with open(path) as fh:
        for r in csv.DictReader(fh):
            rows.append({k: float(v) for k, v in r.items()})
    npz_path = os.path.join(RESULTS, "p5_spectra.npz")
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(9.6, 4.2), constrained_layout=True)
    cols = [C_ACCENT, C_ACCENT2, C_ICON, C_HEADER]
    if os.path.exists(npz_path):
        data = np.load(npz_path)
        for i, row in enumerate(rows):
            lab = "A" if row["b_pow"] == 1.0 else f"H{row['b_pow']:g}"
            key = f"{lab}_t2"
            if key not in data:
                continue
            e = data[key]
            kk = np.arange(len(e), dtype=float)
            d = kk ** (2.0 * row["b_pow"]) * e
            ax1.loglog(kk[1:], d[1:], color=cols[i % 4], lw=1.8,
                       label=f"$b$ = {row['b_pow']:g}")
            if row["kd_measured"] == row["kd_measured"]:
                ax1.plot([row["kd_measured"]], [row["kd_measured"] ** (2.0 * row["b_pow"]) * np.interp(row["kd_measured"], kk, e)],
                         marker="o", ms=6, mfc="white", mec=cols[i % 4], mew=1.6)
    ax1.set_xlabel(L["k"])
    ax1.set_ylabel(L["dk"])
    ax1.set_ylim(1e-14, 1e-2)
    style_ax(ax1)
    ax1.legend(frameon=False, loc="lower left", fontsize=9)
    xx = np.linspace(0.0, 1.05, 10)
    ax2.plot(xx, xx, color=C_MUTED, lw=1.2, ls=":")
    ax2.plot([r["x_star_theory"] for r in rows], [r["kd_times_eta_b"] for r in rows],
             marker="o", ms=8, mfc="white", mec=C_ACCENT, mew=1.8, lw=0)
    for r in rows:
        if r["kd_times_eta_b"] == r["kd_times_eta_b"]:
            ax2.annotate(
                f"$b$={r['b_pow']:g} ({r['rel_dev']*100:.0f}%)",
                xy=(r["x_star_theory"], r["kd_times_eta_b"]),
                xytext=(4, -11), textcoords="offset points", fontsize=8.5,
                color=C_TEXT,
            )
    ax2.set_xlabel(L["xstar"])
    ax2.set_ylabel(L["kdeta"])
    ax2.set_xlim(0.0, 1.05)
    ax2.set_ylim(0.0, 1.05)
    ax2.set_title(L["collapse"], fontsize=10, color=C_TEXT, loc="left")
    style_ax(ax2)
    save(fig, "fig9_bfamily.png")


def fig10_certificate():
    path = os.path.join(RESULTS, "p5_certificate.csv")
    npz_path = os.path.join(RESULTS, "p5_spectra.npz")
    if not (os.path.exists(path) and os.path.exists(npz_path)):
        print("[fig] p5 certificate outputs missing, skip fig10")
        return
    rows = []
    with open(path) as fh:
        for r in csv.DictReader(fh):
            rows.append({k: float(v) for k, v in r.items()})
    data = np.load(npz_path)
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(9.6, 4.2), constrained_layout=True)
    cols = [C_ACCENT, C_ACCENT2, C_ICON]
    for i, ts in enumerate((0.5, 2.0, 4.0)):
        key = f"A_t{ts:g}"
        if key not in data:
            continue
        e = data[key]
        kk = np.arange(len(e), dtype=float)
        m = (kk >= 1) & (e > 0)
        ax1.semilogy(kk[m], e[m], color=cols[i], lw=1.6, alpha=0.9,
                     label=f"$t$ = {ts:g}")
        # exponential fit line over the certification band
        sel = [r for r in rows if abs(r["t"] - ts) < 0.011]
        if sel:
            c = sel[0]["c_exp"]
            kk2 = np.linspace(11.0, 16.0, 10)
            base = np.interp(11.0, kk[m], e[m])
            ax1.semilogy(kk2, base * np.exp(-c * (kk2 - 11.0)),
                         color=cols[i], lw=1.0, ls="--", alpha=0.8)
    ax1.set_xlabel(L["k"])
    ax1.set_ylabel(L["ek_semilog"])
    ax1.set_title(L["cert_t"] + " 0.5, 2, 4", fontsize=10, color=C_TEXT, loc="left")
    ax1.set_ylim(1e-18, 1e-1)
    style_ax(ax1)
    ax1.legend(frameon=False, loc="lower left", fontsize=9)
    t_arr = np.array([r["t"] for r in rows])
    ax2.plot(t_arr, [r["r2_exp"] for r in rows], color=C_ACCENT, lw=2.0, label=L["r2exp"])
    ax2.plot(t_arr, [r["r2_pow"] for r in rows], color=C_ACCENT2, lw=2.0, ls="--", label=L["r2pow"])
    ax2.set_xlabel(L["t"])
    ax2.set_ylabel(L["r2"])
    ax2.set_ylim(0.5, 1.005)
    ax2.set_title(L["cert_title"], fontsize=10, color=C_TEXT, loc="left")
    style_ax(ax2)
    ax2.legend(frameon=False, loc="lower left", fontsize=9)
    save(fig, "fig10_certificate.png")


if __name__ == "__main__":
    os.makedirs(os.path.join(FIG, LANG), exist_ok=True)
    fig1_master_lilly()
    fig2_spectra_closures()
    fig3_ck_alpha()
    fig4_p3_convergence()
    fig5_p4_dns()
    fig6_p4_apriori()
    fig7_ck_summary()
    fig8_regularity()
    fig9_bfamily()
    fig10_certificate()
    print("[fig] done")
