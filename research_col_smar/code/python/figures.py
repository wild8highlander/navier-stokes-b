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
        # P5-B: resolution study, P5-C: stretch ensemble
        "spec96A": "A (TG), 96³",
        "spec96H": "H2 ($b$=2), 96³",
        "conv4896": "относительное расхождение диагностик 48³ → 96³",
        "bar_E": "$E(t_6)$",
        "bar_Om": r"$\Omega_{\max}$",
        "bar_I": "$I_{BKM}(T)$",
        "bar_w": r"$\|\omega\|_\infty$",
        "bar_u4": r"$\int\langle u^4\rangle dt$",
        "bar_u6": r"$\int\langle u^6\rangle^{1/2} dt$",
        "pdfden": "плотность распределения",
        "alpha_pdf": r"плотность $\alpha = (\omega_i S_{ij}\omega_j)/(\omega^2 s_{rms})$",
        "e1": r"$e_1$ (растяжение)",
        "e2": r"$e_2$ (промежуточный)",
        "e3": r"$e_3$ (сжатие)",
        "gausfam": "гауссов ансамбль (32 поля)",
        "dnsfam": "DNS 96³, $t$ =",
        "surfam": "фазовые суррогаты (8)",
        "null_th": "случайное направление: $\\cos^2\\theta_i = 1/3$",
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
        # P5-B: resolution study, P5-C: stretch ensemble
        "spec96A": "A (TG), 96³",
        "spec96H": "H2 ($b$=2), 96³",
        "conv4896": "relative deviation of diagnostics 48³ → 96³",
        "bar_E": "$E(t_6)$",
        "bar_Om": r"$\Omega_{\max}$",
        "bar_I": "$I_{BKM}(T)$",
        "bar_w": r"$\|\omega\|_\infty$",
        "bar_u4": r"$\int\langle u^4\rangle dt$",
        "bar_u6": r"$\int\langle u^6\rangle^{1/2} dt$",
        "pdfden": "probability density",
        "alpha_pdf": r"density of $\alpha = (\omega_i S_{ij}\omega_j)/(\omega^2 s_{rms})$",
        "e1": r"$e_1$ (extensive)",
        "e2": r"$e_2$ (intermediate)",
        "e3": r"$e_3$ (compressive)",
        "gausfam": "Gaussian ensemble (32 fields)",
        "dnsfam": "DNS 96³, $t$ =",
        "surfam": "phase surrogates (8)",
        "null_th": "random direction: $\\cos^2\\theta_i = 1/3$",
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


def fig11_resolution_96():
    path = os.path.join(RESULTS, "p5b_resolution_96.json")
    if not os.path.exists(path):
        print("[fig] p5b_resolution_96.json missing, skip fig11")
        return
    with open(path) as fh:
        d = json.load(fh)
    npz = np.load(os.path.join(RESULTS, "p5b_spectra_96.npz"))
    k = np.arange(npz["A96_t5"].shape[0], dtype=float)

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(9.6, 4.2), constrained_layout=True)
    ax1.semilogy(k, npz["A96_t5"], color=C_ACCENT, lw=1.8, label=L["spec96A"])
    ax1.semilogy(k, npz["H2_96_t5"], color=C_ACCENT2, lw=1.8, ls="--", label=L["spec96H"])
    kk = np.linspace(10.0, 30.0, 50)
    ref = npz["A96_t5"][20] * np.exp(-3.0 * (kk - 20.0))
    ax1.semilogy(kk, ref, color=C_MUTED, lw=0.9, ls=":", label=r"$\propto e^{-3k}$")
    ax1.set_xlabel(L["k"])
    ax1.set_ylabel(L["ek_semilog"])
    ax1.set_ylim(1e-22, 1e1)
    ax1.set_title(L["cert_t"] + " 5 (96³)", fontsize=10, color=C_TEXT, loc="left")
    style_ax(ax1)
    ax1.legend(frameon=False, loc="lower left", fontsize=9)

    conv = d["convergence_48_vs_96"]
    bars = [
        (L["bar_E"], conv["E_final"]["rel_diff"]),
        (L["bar_Om"], conv["Omega_max"]["rel_diff"]),
        (L["bar_w"], conv["omega_inf_max"]["rel_diff"]),
        (L["bar_I"], conv["I_BKM_T"]["rel_diff"]),
        (L["bar_u4"], conv["LPS_int_u4"]["rel_diff"]),
        (L["bar_u6"], conv["LPS_int_u6half"]["rel_diff"]),
    ]
    labels = [b[0] for b in bars]
    vals = np.array([b[1] for b in bars])
    ax2.bar(range(len(vals)), vals, color=[C_ACCENT] * 4 + [C_ACCENT2] * 2, width=0.62)
    ax2.set_yscale("log")
    ax2.set_ylim(1e-6, 1e-1)
    ax2.set_xticks(range(len(labels)))
    ax2.set_xticklabels(labels, fontsize=8.5)
    for i, v in enumerate(vals):
        ax2.text(i, v * 1.35, f"{v:.1e}", ha="center", fontsize=7.5, color=C_TEXT)
    ax2.set_ylabel(L["conv4896"])
    style_ax(ax2)
    save(fig, "fig11_resolution_96.png")


def fig12_stretch_ensemble():
    path = os.path.join(RESULTS, "p5c_pdfs.csv")
    if not os.path.exists(path):
        print("[fig] p5c_pdfs.csv missing, skip fig12")
        return
    rows = []
    with open(path) as fh:
        for r in csv.DictReader(fh):
            rows.append((r["kind"], r["family"], float(r["x"]), float(r["pdf"])))

    def series(kind, family):
        pts = sorted((x, y) for kk, ff, x, y in rows if kk == kind and ff == family)
        return np.array([p[0] for p in pts]), np.array([p[1] for p in pts])

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(9.6, 4.2), constrained_layout=True)
    colors = {"cos1": C_MUTED, "cos2": C_ACCENT, "cos3": C_ACCENT2}
    names = {"cos1": L["e1"], "cos2": L["e2"], "cos3": L["e3"]}
    for kind in ("cos1", "cos2", "cos3"):
        xg, yg = series(kind, "GAU")
        ax1.plot(xg, yg, color=colors[kind], lw=1.2, ls="--", alpha=0.75)
        xd, yd = series(kind, "DNS_t5")
        ax1.plot(xd, yd, color=colors[kind], lw=2.0, label=names[kind])
    ax1.axhline(1.0, color=C_MUTED, lw=0.9, ls=":")
    ax1.text(0.02, 1.04, L["null_th"], fontsize=8, color=C_MUTED)
    ax1.set_xlabel(r"$\cos^2\theta_i$")
    ax1.set_ylabel(L["pdfden"])
    ax1.set_xlim(0, 1)
    style_ax(ax1)
    ax1.legend(frameon=False, loc="upper center", fontsize=9)
    ax1.set_title(L["dnsfam"] + " 5 — " + L["gausfam"], fontsize=10, color=C_TEXT, loc="left")

    for fam, col, lsty, lab in (
        ("DNS_t5", C_ACCENT, "-", L["dnsfam"] + " 5"),
        ("GAU", C_ACCENT2, "--", L["gausfam"]),
        ("SUR", C_MUTED, ":", L["surfam"]),
    ):
        x, y = series("alpha", fam)
        ax2.plot(x, y, color=col, lw=2.0 if fam == "DNS_t5" else 1.5, ls=lsty, label=lab)
    ax2.axvline(0.0, color=C_MUTED, lw=0.9, ls=":")
    ax2.set_xlabel(r"$\alpha$")
    ax2.set_ylabel(L["pdfden"])
    ax2.set_xlim(-1, 1)
    style_ax(ax2)
    ax2.legend(frameon=False, loc="upper right", fontsize=9)
    ax2.set_title(L["alpha_pdf"], fontsize=10, color=C_TEXT, loc="left")
    save(fig, "fig12_stretch_ensemble.png")


def _qr_labels():
    return {
        "en": {
            "t1": "DNS 96$^3$, t = 5 (A96)",
            "t2": "Gaussian ensemble (GAU2, M = 64)",
            "t3": "DNS 64$^3$ ensemble, $\\nu$ = 0.005, t = 5 (8 seeds)",
            "vt": "Vieillefosse tail",
            "x": r"$r^* = R/\langle S:S\rangle^{3/2}$",
            "y": r"$q^* = Q/\langle S:S\rangle$",
            "cb": r"$\log_{10}$ PDF",
        },
        "ru": {
            "t1": "DNS 96$^3$, t = 5 (A96)",
            "t2": "гауссов ансамбль (GAU2, M = 64)",
            "t3": "ансамбль DNS 64$^3$, $\\nu$ = 0.005, t = 5 (8 сидов)",
            "vt": "хвост Вейлефосса",
            "x": r"$r^* = R/\langle S:S\rangle^{3/2}$",
            "y": r"$q^* = Q/\langle S:S\rangle$",
            "cb": r"$\log_{10}$ PDF",
        },
    }[LANG]


def fig13_qr_topology():
    path = os.path.join(RESULTS, "p5d_qr_topology.json")
    if not os.path.exists(path):
        print("[fig] p5d_qr_topology.json missing, skip fig13")
        return
    lab = _qr_labels()
    with open(path, encoding="utf-8") as fh:
        d = json.load(fh)
    nb = len(d["pooled_pdfs"]["DNS96_t5"]["pdf"])
    half = 3.0
    cs = np.linspace(-half + half / nb, half - half / nb, nb)
    fig, axes = plt.subplots(
        1, 3, figsize=(12.6, 4.3), constrained_layout=True, sharey=True
    )
    panels = (
        ("DNS96_t5", lab["t1"]),
        ("GAU2", lab["t2"]),
        ("nu0p005_t5", lab["t3"]),
    )
    qq, rr = np.meshgrid(cs, cs)
    tail_r = np.where(
        np.abs(qq) > 1e-9, np.sqrt(np.clip(-4.0 * qq**3 / 27.0, 0.0, None)), 0.0
    )
    vmin = -6.0
    for ax, (fam, title) in zip(axes, panels):
        if fam not in d["pooled_pdfs"]:
            print(f"[fig] family {fam} missing, skip panel")
            continue
        pdf = np.array(d["pooled_pdfs"][fam]["pdf"])
        im = ax.imshow(
            np.log10(np.maximum(pdf.T, 1e-7)),
            origin="lower",
            extent=(-half, half, -half, half),
            aspect="auto",
            cmap="magma",
            vmin=vmin,
            vmax=0.0,
            interpolation="bilinear",
        )
        mpos = qq >= 0
        ax.plot(rr[mpos], qq[mpos], color="cyan", lw=1.0, ls="--", label=lab["vt"])
        ax.plot(-rr[mpos], qq[mpos], color="cyan", lw=1.0, ls="--")
        ax.axhline(0.0, color="w", lw=0.5, alpha=0.6)
        ax.axvline(0.0, color="w", lw=0.5, alpha=0.6)
        ax.set_xlabel(lab["x"])
        if ax is axes[0]:
            ax.set_ylabel(lab["y"])
        ax.set_title(title, fontsize=10, color=C_TEXT, loc="left")
        ax.legend(frameon=False, loc="upper left", fontsize=8)
    cb = fig.colorbar(im, ax=axes, shrink=0.9, pad=0.01)
    cb.set_label(lab["cb"])
    save(fig, "fig13_qr_topology.png")


def fig14_ensemble_ext():
    ens_path = os.path.join(RESULTS, "p5d_ensemble_dns.json")
    if not os.path.exists(ens_path):
        print("[fig] p5d_ensemble_dns.json missing, skip fig14")
        return
    lab = {
        "en": {
            "a": "enstrophy: ensemble mean $\\pm$ std",
            "b": "geometry vs Reynolds number",
            "b1": r"$\beta_S$",
            "b2": r"$\langle\cos^2\theta_2\rangle$",
            "b3": r"$\langle\cos^2\theta_1\rangle$",
            "x2": r"$\mathrm{Re}_\lambda$ (t = 5)",
            "tg": "TG reference (deterministic)",
            "nu1": r"$\nu$ = 0.01, 64$^3$",
            "nu2": r"$\nu$ = 0.005, 64$^3$",
            "r96": "96$^3$ check",
        },
        "ru": {
            "a": "энстрофия: среднее по ансамблю $\\pm$ с.к.о.",
            "b": "геометрия против числа Рейнольдса",
            "b1": r"$\beta_S$",
            "b2": r"$\langle\cos^2\theta_2\rangle$",
            "b3": r"$\langle\cos^2\theta_1\rangle$",
            "x2": r"$\mathrm{Re}_\lambda$ (t = 5)",
            "tg": "TG-референс (детерминированный)",
            "nu1": r"$\nu$ = 0.01, 64$^3$",
            "nu2": r"$\nu$ = 0.005, 64$^3$",
            "r96": "проверка 96$^3$",
        },
    }[LANG]
    with open(ens_path, encoding="utf-8") as fh:
        d = json.load(fh)
    fig, (ax1, ax2) = plt.subplots(
        1, 2, figsize=(9.6, 4.2), constrained_layout=True
    )
    # --- panel A: Omega(t) mean +/- std from per-run traces -----------------
    for nu, col in ((0.01, C_ACCENT), (0.005, C_ACCENT2)):
        tags = [
            r["tag"]
            for r in d["runs"]
            if r["nu"] == nu and r["n"] == 64
        ]
        curves, ts = [], None
        for tag in tags:
            p = os.path.join(RESULTS, f"p5d_trace_{tag}.npz")
            if not os.path.exists(p):
                continue
            z = np.load(p)
            curves.append(z["Omega"])
            ts = z["t"]
        if not curves:
            continue
        A = np.array(curves)
        mean, std = A.mean(axis=0), A.std(axis=0, ddof=1)
        ax1.fill_between(ts, mean - std, mean + std, color=col, alpha=0.22, lw=0)
        ax1.plot(ts, mean, color=col, lw=1.8, label=lab[f"nu{1 if nu == 0.01 else 2}"])
    ax1.set_xlabel("t")
    ax1.set_ylabel(r"$\Omega(t)=\langle\omega^2\rangle$")
    ax1.set_title(lab["a"], fontsize=10, color=C_TEXT, loc="left")
    ax1.legend(frameon=False, fontsize=9)
    style_ax(ax1)
    # --- panel B: geometry vs Re_lambda --------------------------------------
    pts = []
    for key, nu in (("nu0.01", 0.01), ("nu0.005", 0.005)):
        if key in d["ensemble_aggregates"]:
            a = d["ensemble_aggregates"][key]
            pts.append(
                (
                    a["Re_lambda_t5"]["mean"],
                    a["stats_t5"]["beta_S"]["mean"],
                    a["stats_t5"]["beta_S"]["std"],
                    a["stats_t5"]["cos2_1"]["mean"],
                    a["stats_t5"]["cos2_1"]["std"],
                    lab[f"nu{1 if nu == 0.01 else 2}"],
                )
            )
    rc = d.get("resolution_check_64_vs_96")
    if rc:
        s96 = rc["n96"]
        b96 = rc.get("geometry_rel_dev", {}).get("stats.beta_S")
        if b96 is not None:
            # 96^3 check: plot its beta_S reconstructed from the 64^3 value
            # and the relative deviation (no ensemble std for a single run)
            b64 = d["ensemble_aggregates"]["nu0.005"]["stats_t5"]["beta_S"]["mean"]
            pts.append(
                (s96["Re_lambda_t5"], b64 * (1.0 + b96), 0.0, None, None, lab["r96"])
            )
    p5c = os.path.join(RESULTS, "p5c_stretch_ensemble.json")
    if os.path.exists(p5c):
        with open(p5c, encoding="utf-8") as fh:
            c = json.load(fh)
        b = c["families"]["DNS_t5"]["beta_S"]["mean"]
        c2 = c["families"]["DNS_t5"]["cos2"]["mean"][1]
        ax2.axhline(b, color=C_MUTED, lw=1.0, ls=":", label=lab["tg"] + " " + lab["b1"])
        ax2.axhline(c2, color=C_MUTED, lw=1.0, ls="-.", label=lab["tg"] + " " + lab["b2"])
    xs = [p[0] for p in pts if p[1] is not None]
    ys = [p[1] for p in pts if p[1] is not None]
    es = [p[2] for p in pts if p[1] is not None]
    ax2.errorbar(xs, ys, yerr=es, color=C_ACCENT, marker="o", ms=5,
                 lw=1.6, capsize=3, label=lab["b1"])
    xs2 = [p[0] for p in pts if p[3] is not None]
    ys2 = [p[3] for p in pts if p[3] is not None]
    es2 = [p[4] for p in pts if p[3] is not None]
    ax2.errorbar(xs2, ys2, yerr=es2, color=C_ACCENT2, marker="s", ms=5,
                 lw=1.6, capsize=3, label=lab["b2"])
    ax2.set_xlabel(lab["x2"])
    ax2.set_title(lab["b"], fontsize=10, color=C_TEXT, loc="left")
    ax2.legend(frameon=False, fontsize=8, loc="center right")
    style_ax(ax2)
    save(fig, "fig14_ensemble_ext.png")


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
    fig11_resolution_96()
    fig12_stretch_ensemble()
    fig13_qr_topology()
    fig14_ensemble_ext()
    print("[fig] done")
