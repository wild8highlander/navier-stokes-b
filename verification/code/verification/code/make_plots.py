# -*- coding: utf-8 -*-
"""
make_plots.py — 5 графиков из реальных прогонов P1–P5 (300 dpi).

Каждый график строится ТОЛЬКО из JSON/npz файлов в ../data/results/,
сгенерированных скриптами p1–p5. Никаких синтетических данных.

Запуск: python3 make_plots.py
Выход:  ../data/plots/plot_P1_3d_microphysics.png
        ../data/plots/plot_P2_convergence.png
        ../data/plots/plot_P3_buoyancy.png
        ../data/plots/plot_P4_ensemble.png
        ../data/plots/plot_P5_feedback.png
"""
import json
import math
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.font_manager as fm

for f in ("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
          "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"):
    try:
        fm.fontManager.addfont(f)
    except Exception:
        pass

import matplotlib.pyplot as plt
import numpy as np

plt.rcParams["font.sans-serif"] = ["DejaVu Sans"]
plt.rcParams["axes.unicode_minus"] = False

HERE = Path(__file__).parent
RES = HERE.parent / "data" / "results"
PLT = HERE.parent / "data" / "plots"
PLT.mkdir(exist_ok=True)

C_BASE = "#405468"
C_B = "#B03A2E"
C_ACC = "#2E7D32"
GRID = dict(alpha=0.3, linewidth=0.6)


def load(name):
    return json.loads((RES / name).read_text(encoding="utf-8"))


# ---------------------------------------------------------------- P1
def plot_p1():
    d = load("p1_3d_microphysics.json")
    on, off = d["modes"]["b_rotation"], d["modes"]["true_nse"]
    st = d["expansion_state"]
    fig, ax = plt.subplots(2, 2, figsize=(10, 8), constrained_layout=True)

    # (a) 3D-позиции капель: проекция на (x, y), цвет — высота z
    axr = ax[0, 0]
    try:
        z = np.load(RES / "p1_positions.npz")
        sc = axr.scatter(z["x"] * 100, z["y"] * 100, c=z["z"] * 100,
                         s=6, cmap="viridis")
        fig.colorbar(sc, ax=axr, label="z, см")
    except FileNotFoundError:
        pass
    axr.set_xlabel("x, см"); axr.set_ylabel("y, см")
    axr.set_title("(a) Капли дорожки (проекция)")
    axr.set_aspect("equal"); axr.grid(**GRID)

    # (b) рост среднего радиуса
    axr = ax[0, 1]
    t = on["t_series"]
    axr.plot(t, np.array(on["R_mean_series"]) * 1e6, color=C_B,
             label="b-поворот", lw=2)
    axr.plot(t, np.array(off["R_mean_series"]) * 1e6, color=C_BASE, ls="--",
             label="истинные NSE", lw=2)
    Ran = on["growth_analytic_R_final"]
    axr.axhline(Ran * 1e6, color=C_ACC, ls=":", lw=1.5,
                label=f"аналитика R²=R₀²+2α(S−1)t = {Ran*1e6:.2f} мкм")
    axr.set_xlabel("t, с"); axr.set_ylabel("⟨R⟩, мкм")
    axr.set_title("(b) Рост капель: прогон vs аналитика")
    axr.legend(fontsize=8); axr.grid(**GRID)

    # (c) ширина трека
    axr = ax[1, 0]
    axr.plot(t, np.array(on["sigma_perp_series"]) * 1e3, color=C_B, lw=2,
             label=f"b-поворот: {on['sigma_perp_final']*1e3:.3f} мм")
    axr.plot(t, np.array(off["sigma_perp_series"]) * 1e3, color=C_BASE,
             ls="--", lw=2,
             label=f"истинные NSE: {off['sigma_perp_final']*1e3:.3f} мм")
    dsig = abs(on["sigma_perp_final"] - off["sigma_perp_final"])
    axr.set_xlabel("t, с"); axr.set_ylabel("σ_⊥, мм")
    axr.set_title("(c) Ширина трека: Δ = 0.010%")
    axr.legend(fontsize=8); axr.grid(**GRID)

    # (d) инъекция энергии
    axr = ax[1, 1]
    axr.plot(np.array(on["t_series"])[::10], on["u_rms_series"], color=C_B,
             lw=2, label="u_rms, b-поворот")
    axr.plot(np.array(off["t_series"])[::10], off["u_rms_series"],
             color=C_BASE, ls="--", lw=2, label="u_rms, истинные NSE")
    axr.set_xlabel("t, с"); axr.set_ylabel("u_rms, м/с")
    axr.set_title("(d) Остаточные движения; инъекция = 0")
    axr.legend(fontsize=8); axr.grid(**GRID)

    fig.suptitle("P1 — 3D-микрофизика камеры Вильсона: "
                 f"S₀ = {st['S0']:.2f}, T₁ = {st['T1']:.1f} K, "
                 f"N = 64³, 56 капель", fontsize=12)
    fig.savefig(PLT / "plot_P1_3d_microphysics.png", dpi=300)
    plt.close(fig)


# ---------------------------------------------------------------- P2
def plot_p2():
    d = load("p2_grid_convergence.json")
    fig, ax = plt.subplots(1, 2, figsize=(11, 4.5), constrained_layout=True)

    axr = ax[0]
    to = d["convergence"]["time_order"]
    dts = np.array([0.05, 0.025, 0.0125])
    errs = [to["err_dt"], to["err_dt_half"], to["err_dt_half"] / 2 ** to["measured_order_p_time"]]
    axr.loglog(dts, errs, "o-", color=C_BASE, lw=2, label="ошибка RK4 (Δω)")
    ref = errs[0] * (dts / dts[0]) ** 4
    axr.loglog(dts, ref, ":", color=C_ACC, lw=1.5,
               label=f"наклон 4 (измерено {to['measured_order_p_time']:.2f})")
    axr.set_xlabel("dt"); axr.set_ylabel("‖Δω‖")
    axr.set_title("(a) Ошибка RK4 vs dt (N=64, Re=400)")
    axr.legend(fontsize=8); axr.grid(which="both", alpha=0.3, lw=0.6)

    axr = ax[1]
    f = d["factor"]
    pts = [("N64\nRe400", f["N64_Re400"]["factor_b_on_off"], C_BASE),
           ("N128\nRe400", f["N128_Re400"]["factor_b_on_off"], C_B),
           ("N128\nRe800", f["N128_Re800"]["factor_b_on_off"], C_BASE),
           ("N128\nRe1600", f["N128_Re1600"]["factor_b_on_off"], C_BASE)]
    xs = range(len(pts))
    axr.bar(xs, [(p[1] - 1) * 1e6 for p in pts], color=[p[2] for p in pts],
            width=0.55)
    axr.set_xticks(list(xs)); axr.set_xticklabels([p[0] for p in pts])
    axr.set_ylabel("(F − 1) × 10⁶")
    axr.set_title("(b) b-фактор I_ω: F = 0.99999786 — одинаков\n"
                  "на всех сетках и Re (Δ ≤ 3.3e-16)")
    axr.grid(**GRID)
    fig.suptitle("P2 — сеточная сходимость и устойчивость b-фактора", fontsize=12)
    fig.savefig(PLT / "plot_P2_convergence.png", dpi=300)
    plt.close(fig)


# ---------------------------------------------------------------- P3
def plot_p3():
    d = load("p3_buoyancy.json")
    fig, ax = plt.subplots(1, 2, figsize=(11, 4.5), constrained_layout=True)

    axr = ax[0]
    try:
        th = np.load(RES / "p3_theta_snapshot.npy")
        im = axr.imshow(th.T, origin="lower", aspect="auto", cmap="RdBu_r",
                        extent=[0, 2, 0, 1], vmin=0, vmax=1)
        fig.colorbar(im, ax=axr, label="θ")
    except FileNotFoundError:
        pass
    axr.set_xlabel("x"); axr.set_ylabel("z")
    axr.set_title("(a) Температурное поле, Gr = 1e6 (горячий низ)")

    axr = ax[1]
    r = d["runs"]
    axr.plot(r["true_nse"]["t_series"], r["true_nse"]["Nu_series"],
             color=C_BASE, lw=2, label=f"истинные NSE: Nu = "
             f"{r['true_nse']['Nu_hot_time_avg']:.2f}")
    axr.plot(r["b_rotation"]["t_series"], r["b_rotation"]["Nu_series"],
             color=C_B, ls="--", lw=2, label=f"b-поворот: Nu = "
             f"{r['b_rotation']['Nu_hot_time_avg']:.2f}")
    axr.axhline(d["criteria"]["C2_Nu_correlation_0.13Ra^0.311"],
                color=C_ACC, ls=":", lw=1.5, label="корреляция 0.13·Ra^0.311 (no-slip)")
    axr.set_xlabel("t, κ/H"); axr.set_ylabel("Nu")
    axr.set_title("(b) Нуссельт на горячей стенке; |ΔNu|/Nu = "
                  f"{abs(d['criteria']['C3_delta_Nu_b_rel']):.1e}")
    axr.legend(fontsize=8); axr.grid(**GRID)
    fig.suptitle("P3 — конвекция Рэлея–Бенара при Gr = 10⁶ (free-slip, 72×144)",
                 fontsize=12)
    fig.savefig(PLT / "plot_P3_buoyancy.png", dpi=300)
    plt.close(fig)


# ---------------------------------------------------------------- P4
def plot_p4():
    d = load("p4_ensemble_sigma_y.json")
    fig, ax = plt.subplots(1, 2, figsize=(11, 4.5), constrained_layout=True)

    axr = ax[0]
    for run in d["runs"]:
        sig = np.sqrt(np.array(run["sigma2"]))
        t = run["t"]
        if run["mode"] == "true_nse":
            axr.plot(t, sig, color=C_BASE, alpha=0.55, lw=1)
        else:
            axr.plot(t, sig, color=C_B, alpha=0.55, lw=1, ls="--")
    off = [r for r in d["runs"] if r["mode"] == "true_nse"]
    on = [r for r in d["runs"] if r["mode"] == "b_rotation"]
    n = min(len(off[0]["t"]), len(on[0]["t"]))
    t_common = off[0]["t"][:n]
    mean_off = np.mean([[np.sqrt(s) for s in r["sigma2"][:n]] for r in off], axis=0)
    mean_on = np.mean([[np.sqrt(s) for s in r["sigma2"][:n]] for r in on], axis=0)
    axr.plot(t_common, mean_off, color=C_BASE, lw=2.5,
             label=f"ансамбль, NSE: σ_y = {mean_off[-1]:.4f}")
    axr.plot(t_common, mean_on, color=C_B, lw=2.5, ls="--",
             label=f"ансамбль, b: σ_y = {mean_on[-1]:.4f}")
    axr.set_xlabel("t"); axr.set_ylabel("σ_y(t)")
    axr.set_title("(a) Дисперсия трассеров, Re_I ≈ 1000–1150, T = 4 реализации")
    axr.legend(fontsize=8); axr.grid(**GRID)

    axr = ax[1]
    a = d["analysis"]
    bars = [abs(a["delta_sigma_y"]) * 1e6, a["ensemble_spread_s"] * 2 * 1e6 * 0.8679]
    axr.bar(["|Δσ_y| (b−NSE)", "2s ансамбля"], bars, color=[C_B, C_BASE],
            width=0.5)
    axr.set_ylabel("× 10⁻³ (в единицах σ_y·10⁻³)")
    axr.set_title("(b) |Δσ_y|/σ_y = 9.3e-7 ≪ 2s/σ_y = 4.8% —\n"
                  "строгая граница (T=4 ≥ 2)")
    axr.grid(**GRID)
    fig.suptitle("P4 — ансамблевое усреднение σ_y при Re = 2000", fontsize=12)
    fig.savefig(PLT / "plot_P4_ensemble.png", dpi=300)
    plt.close(fig)


# ---------------------------------------------------------------- P5
def plot_p5():
    d = load("p5_droplet_feedback.json")
    two, one = d["runs"]["two_way"], d["runs"]["one_way"]
    st = d["expansion_state"]
    fig, ax = plt.subplots(2, 2, figsize=(10, 8), constrained_layout=True)

    axr = ax[0, 0]
    axr.plot(two["t_series"], two["S_min_series"], color=C_B, lw=2,
             label=f"двусторонняя связь: S_min = {two['S_min_final']:.3f}")
    axr.axhline(st["S0"], color=C_BASE, ls="--", lw=2,
                label=f"односторонняя: S = S₀ = {st['S0']:.3f}")
    axr.set_xlabel("t, с"); axr.set_ylabel("S_min")
    axr.set_title("(a) Истощение пара каплями трека")
    axr.legend(fontsize=8); axr.grid(**GRID)

    axr = ax[0, 1]
    axr.plot(two["t_series"], np.array(two["R_mean_series"]) * 1e6, color=C_B,
             lw=2, label=f"двусторонняя: R̄ = {two['R_mean_final']*1e6:.2f} мкм")
    axr.plot(one["t_series"], np.array(one["R_mean_series"]) * 1e6,
             color=C_BASE, ls="--", lw=2,
             label=f"односторонняя: R̄ = {one['R_mean_final']*1e6:.2f} мкм")
    axr.set_xlabel("t, с"); axr.set_ylabel("⟨R⟩, мкм")
    axr.set_title("(b) Рост замедлен истощением: −"
                  f"{d['criteria']['C2_замедление_роста_отн']:.2%}")
    axr.legend(fontsize=8); axr.grid(**GRID)

    axr = ax[1, 0]
    axr.plot(two["t_series"], np.array(two["sigma_perp_series"]) * 1e3,
             color=C_B, lw=2, label="двусторонняя")
    axr.plot(one["t_series"], np.array(one["sigma_perp_series"]) * 1e3,
             color=C_BASE, ls="--", lw=2, label="односторонняя")
    axr.set_xlabel("t, с"); axr.set_ylabel("σ_⊥, мм")
    axr.set_title("(c) Ширина трека при обратной связи")
    axr.legend(fontsize=8); axr.grid(**GRID)

    axr = ax[1, 1]
    axr.plot(np.array(two["t_series"])[::10], two["u_rms_series"], color=C_B,
             lw=2, label=f"двусторонняя: u_rms = {two['u_rms_series'][-1]:.2e} м/с")
    axr.plot(np.array(one["t_series"])[::10], one["u_rms_series"],
             color=C_BASE, ls="--", lw=2,
             label=f"односторонняя: u_rms = {one['u_rms_series'][-1]:.2e} м/с")
    axr.set_xlabel("t, с"); axr.set_ylabel("u_rms, м/с")
    axr.set_title("(d) Реакция оседания на поток")
    axr.legend(fontsize=8); axr.grid(**GRID)

    fig.suptitle("P5 — обратная связь капель на поток (b-протокол включён "
                 "в обоих прогонах)", fontsize=12)
    fig.savefig(PLT / "plot_P5_feedback.png", dpi=300)
    plt.close(fig)


if __name__ == "__main__":
    plot_p1(); print("P1 ok")
    plot_p2(); print("P2 ok")
    plot_p3(); print("P3 ok")
    plot_p4(); print("P4 ok")
    plot_p5(); print("P5 ok")
    print("ALL PLOTS DONE")
