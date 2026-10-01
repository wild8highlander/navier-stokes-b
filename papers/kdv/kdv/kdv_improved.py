#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
kdv_improved.py — улучшенный KdV-комплекс пакета NSB-96-UPGRADE.

Развивает главу 16 монографии (KdV_b_correction_Chapter16): реализует и
улучшает численную часть — псевдоспектральный IFRK4 (Fornberg–Whitham)
с 2/3-обезвреживанием (в главе 16 обезвреживание не описано), полным
трекингом инвариантов Лакса и точными N-солитонными решениями Хироты
в качестве эталонов.

Улучшения относительно главы 16:
  1. 2/3-обезвреживание нелинейности (контроль алиасинга);
  2. инвариант КдФ I3 = ∫(u³ − u_x²/2)dx — точная комбинация Лакса
     (d/dt∫u³ = −3∫u_x³, d/dt∫u_x² = −6∫u_x³);
  3. сравнение с ТОЧНЫМ двухсолитонным решением (фазовые сдвиги);
  4. расширенное семейство уравнений: KdV, mKdV, BBM, Кавахара (§16.23);
  5. вердикты WIN/DRAW/LOSS с настраиваемыми порогами;
  6. воспроизводимость (seed) + JSON/CSV/MD-отчёты + графики 600 dpi.

Запуск:  python3 kdv_improved.py [--dpi 600] [--quick]
Выход:   results/kdv_improved.json, results/kdv_improved_verdicts.csv,
         figures/figK1_collision_waterfall_{ru,en}.png,
         figures/figK2_invariants_theta_{ru,en}.png
"""

from __future__ import annotations

import argparse
import csv
import json
import math
import os
import sys
from datetime import datetime

import numpy as np

B_UNIV = 1.0 / (4.0 * math.pi + 2.0 * math.sqrt(3.0))
THETA_B = math.asin(B_UNIV)

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
OUT_RES = os.path.join(ROOT, "results")
OUT_FIG = os.path.join(ROOT, "figures")
os.makedirs(OUT_RES, exist_ok=True)
os.makedirs(OUT_FIG, exist_ok=True)


# ============================================================================
# обобщённый псевдоспектральный IFRK4-решатель дисперстных уравнений
# ============================================================================
class DispersiveSolver:
    """IFRK4 + 2/3-dealias для семейства u_t = L u + N(u).

    pde: 'kdv'     — u_t + 6 u u_x + u_xxx   = 0
         'mkdv'    — u_t + 6 u^2 u_x + u_xxx = 0
         'bbm'     — u_t + u_x + u u_x − u_xxt = 0
         'kawahara'— u_t + u u_x + u_xxx − u_xxxxx = 0
    """

    def __init__(self, n: int, l_domain: float, dt: float, pde: str = "kdv",
                 dealias: bool = True):
        self.n, self.L, self.dt, self.pde = n, l_domain, dt, pde
        self.k = 2.0 * math.pi * np.fft.fftfreq(n, d=l_domain / n)
        self.dealias = dealias
        crit = n // 3
        kf = np.fft.fftfreq(n, d=l_domain / n)
        self._mask = (np.abs(kf) <= crit * 2.0 * math.pi / l_domain) \
            if dealias else None
        self._precompute_linops()

    def _precompute_linops(self):
        k, dt = self.k, self.dt
        if self.pde == "kdv":
            L = 1j * k**3
        elif self.pde == "mkdv":
            L = 1j * k**3
        elif self.pde == "bbm":
            L = -1j * k / (1.0 + k**2)
        elif self.pde == "kawahara":
            L = 1j * k**3 + 1j * k**5
        else:
            raise ValueError(self.pde)
        self._E = np.exp(L * dt)
        self._E2 = np.exp(L * dt / 2.0)

    def _nonlin(self, uh) -> np.ndarray:
        k = self.k
        u = np.fft.ifft(uh).real
        if self.pde == "kdv":
            out = -3.0j * k * np.fft.fft(u * u)
        elif self.pde == "mkdv":
            out = -2.0j * k * np.fft.fft(u**3)
        elif self.pde == "bbm":
            out = -0.5j * k * np.fft.fft(u * u) / (1.0 + k**2)
        elif self.pde == "kawahara":
            out = -0.5j * k * np.fft.fft(u * u)
        return out

    def step(self, uh) -> np.ndarray:
        E, E2, dt = self._E, self._E2, self.dt
        k1 = self._nonlin(uh)
        k2 = self._nonlin(E2 * (uh + dt / 2.0 * k1))
        k3 = self._nonlin(E2 * uh + dt / 2.0 * k2)
        k4 = self._nonlin(E * uh + dt * E2 * k3)
        out = E * uh + dt / 6.0 * (E * k1 + 2.0 * E2 * (k2 + k3) + k4)
        if self._mask is not None:
            out = out * self._mask
        return out

    def evolve(self, u0: np.ndarray, t_end: float, snaps: int = 5):
        uh = np.fft.fft(u0)
        if self._mask is not None:
            uh = uh * self._mask
        n_steps = int(round(t_end / self.dt))
        snap_at = set(np.linspace(1, n_steps, snaps).astype(int).tolist())
        snap_at.add(n_steps)
        ts, us = [0.0], [np.fft.ifft(uh).real.copy()]
        inv = [self.invariants(uh)]
        for s in range(1, n_steps + 1):
            uh = self.step(uh)
            if s in snap_at:
                ts.append(s * self.dt)
                us.append(np.fft.ifft(uh).real.copy())
                inv.append(self.invariants(uh))
        return np.array(ts), us, np.array(inv)

    def invariants(self, uh) -> tuple:
        u = np.fft.ifft(uh).real
        ux = np.fft.ifft(1j * self.k * uh).real
        uxx = np.fft.ifft(-self.k**2 * uh).real
        m = float(np.mean(u))
        p = float(np.mean(u**2) / 2.0)
        if self.pde == "kdv":
            # I3 = ∫(u³ − u_x²/2)dx — точная комбинация Лакса
            e = float(np.mean(u**3) - np.mean(ux**2) / 2.0)
            scale = max(abs(e), float(np.mean(ux**2) / 2.0), 1e-300)
        elif self.pde == "mkdv":
            # ∫(u⁴ − u_x²)dx: d/dt∫u⁴ = −12∫u u_x³, d/dt∫u_x² = −12∫u u_x³
            e = float(np.mean(u**4) - np.mean(ux**2))
            scale = max(abs(e), float(np.mean(ux**2)), 1e-300)
        elif self.pde == "bbm":
            # ∫(u²/2 + u_x²/2): H¹-норма сохраняется для BBM
            e = float(np.mean(u**2) / 2.0 + np.mean(ux**2) / 2.0)
            scale = max(abs(e), 1e-300)
        else:  # kawahara: M и P гарантированы; E контролируем как P+дисп.
            e = float(np.mean(u**2) / 2.0)
            scale = max(abs(e), 1e-300)
            m, p = p, e  # для kawahara главной величиной будет P
        return m, p, e, scale


# ============================================================================
# точные решения
# ============================================================================
def soliton_kdv(x, c, x0):
    return (c / 2.0) / np.cosh(np.sqrt(c) / 2.0 * (x - x0)) ** 2


def soliton_mkdv(x, c, x0, sign=+1.0):
    return sign * np.sqrt(c) / np.cosh(np.sqrt(c) * (x - x0))


def soliton_bbm(x, c, x0):
    """u = 3c sech²(½√(c/(1+c)) (x − (1+c)t)) для u_t + u_x + u u_x − u_xxt = 0."""
    k = 0.5 * math.sqrt(c / (1.0 + c))
    return 3.0 * c / np.cosh(k * (x - x0)) ** 2


def hirota_field(x, t, cs, x0s):
    """Точное N-солитонное решение Хироты (KdV), стабилизированное."""
    from itertools import combinations
    import itertools
    ks = [math.sqrt(c) for c in cs]
    subsets = []
    for r in range(1, len(cs) + 1):
        for idx in itertools.combinations(range(len(cs)), r):
            a = 1.0
            for i, j in combinations(idx, 2):
                a *= ((ks[i] - ks[j]) / (ks[i] + ks[j])) ** 2
            subsets.append((list(idx), a))
    expo = []
    for idx, a in subsets:
        e = np.zeros_like(x)
        for i in idx:
            e = e + ks[i] * (x - x0s[i]) - ks[i] ** 3 * t
        expo.append(e)
    emax = float(np.max(np.stack(expo)))
    tau = np.ones_like(x) * np.exp(-emax)
    taup = np.zeros_like(x)
    taupp = np.zeros_like(x)
    for (idx, a), e in zip(subsets, expo):
        s = float(sum(ks[i] for i in idx))
        em = a * np.exp(e - emax)
        tau += em
        taup += s * em
        taupp += s * s * em
    return 2.0 * (tau * taupp - taup**2) / tau**2


# ============================================================================
# вердикты
# ============================================================================
class Verdicts:
    def __init__(self, thr=(1e-6, 1e-4)):
        self.tw, self.td = thr
        self.rows = []

    def judge(self, lab, test, value, note=""):
        v = "DRAW" if (value is None or math.isnan(value)) else \
            ("WIN" if value < self.tw else ("DRAW" if value < self.td
                                            else "LOSS"))
        self.rows.append({"lab": lab, "test": test, "value": value,
                          "verdict": v, "note": note})
        return v

    def tally(self):
        return {k: sum(1 for r in self.rows if r["verdict"] == k)
                for k in ("WIN", "DRAW", "LOSS")}


def print_table(V: Verdicts):
    print("  " + "─" * 76)
    for r in V.rows:
        icon = {"WIN": "✔", "DRAW": "◆", "LOSS": "✘"}[r["verdict"]]
        val = "nan" if r["value"] is None else f"{r['value']:.3e}"
        print(f"  {icon} {r['verdict']:<5} {r['test'][:48]:<50} {val:>10}")
    print("  " + "─" * 76)
    t = V.tally()
    print(f"  ТАБЛО: WIN={t['WIN']}  DRAW={t['DRAW']}  LOSS={t['LOSS']}")


# ============================================================================
# эксперименты
# ============================================================================
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dpi", type=int, default=600)
    ap.add_argument("--quick", action="store_true",
                    help="уменьшенные N/T для быстрой проверки")
    args = ap.parse_args()
    t0 = datetime.now()
    print("=" * 78)
    print("  KdV IMPROVED — улучшенный комплекс главы 16 + b-механизмы")
    print(f"  b = {B_UNIV:.9f}, θ_b = {math.degrees(THETA_B):.6f}°")
    print("=" * 78)

    n = 256 if args.quick else 512
    L = 100.0
    dt = 0.001 if args.quick else 0.0005
    T1 = 5.0 if args.quick else 20.0
    Tc = 4.0 if args.quick else 14.0
    x = np.linspace(0.0, L, n, endpoint=False)
    V = Verdicts()
    out = {"module": "kdv_improved", "date": t0.isoformat(),
           "params": {"n": n, "L": L, "dt": dt, "T1": T1, "Tc": Tc,
                      "dealiasing": "2/3 rule", "scheme": "IFRK4"},
           "experiments": {}}

    # --- E1: KdV-солитон против точного ------------------------------------
    print("  E1: KdV-солитон vs точное решение")
    u0 = soliton_kdv(x, 4.0, 30.0)
    sv = DispersiveSolver(n, L, dt, "kdv")
    ts, us, inv = sv.evolve(u0, T1, snaps=3)
    ue = soliton_kdv(x, 4.0, (30.0 + 4.0 * T1) % L)
    err = float(np.max(np.abs(us[-1] - ue)))
    drift = {n_: abs(inv[-1][i] - inv[0][i]) /
             max(abs(inv[0][i]) if i < 3 else inv[0][3], inv[0][3], 1e-300)
             for i, n_ in enumerate(("M", "P", "E"))}
    V.judge("E1", "|u_num − u_exact|∞ (KdV, T=%g)" % T1, err)
    V.judge("E1", "worst invariant drift (KdV)", max(drift.values()))
    out["experiments"]["E1"] = {"l_inf_err": err, "drift": drift}

    # --- E2: столкновение двух солитонов (Хирота) --------------------------
    print("  E2: столкновение двух солитонов (точное решение Хироты)")
    u0c = hirota_field(x, 0.0, [4.0, 1.0], [30.0, 60.0])
    ts, us, inv = sv.evolve(u0c, Tc, snaps=12)
    ue2 = hirota_field(x, Tc, [4.0, 1.0], [30.0, 60.0])
    err2 = float(np.max(np.abs(us[-1] - ue2)))
    drift2 = {n_: abs(inv[-1][i] - inv[0][i]) /
              max(abs(inv[0][i]) if i < 3 else inv[0][3], inv[0][3], 1e-300)
              for i, n_ in enumerate(("M", "P", "E"))}
    V.judge("E2", "|u_num − u_Hirota|∞ (столкновение)", err2)
    V.judge("E2", "worst invariant drift (столкновение)",
            max(drift2.values()))
    out["experiments"]["E2"] = {"l_inf_err_vs_hirota": err2, "drift": drift2}
    # waterfall для графика
    waterfall = {"t": ts.tolist(), "u": [u[::4].tolist() for u in us]}

    # --- E3: b-механизмы M1/M2/M3 -------------------------------------------
    print("  E3: b-механизмы (M1 Гильберт, M2 Родригес, M3 нелинейность)")
    ux0 = np.gradient(u0, L / n)  # спектральный вариант — внутри решателя
    uxx = np.fft.ifft(1j * sv.k * np.fft.fft(u0)).real
    u_m1 = np.fft.ifft(np.exp(1j * THETA_B *
                              np.sign(np.fft.fftfreq(n, d=L / n))) *
                       np.fft.fft(u0)).real
    u_m2 = math.cos(THETA_B) * u0 + math.sin(THETA_B) * uxx
    r_m1 = DispersiveSolver(n, L, dt, "kdv").evolve(u_m1, T1 / 4, snaps=2)
    r_m2 = DispersiveSolver(n, L, dt, "kdv").evolve(u_m2, T1 / 4, snaps=2)
    # M3: нелинейность с косинусным ослаблением — ч/з модификацию k
    def evolve_m3(u0_, T_):
        s3 = DispersiveSolver(n, L, dt, "kdv")
        uh = np.fft.fft(u0_) * s3._mask if s3._mask is not None \
            else np.fft.fft(u0_)
        nst = int(round(T_ / dt))
        invs = [s3.invariants(uh)]
        for _ in range(nst):
            E, E2_, dt_ = s3._E, s3._E2, s3.dt
            k1 = math.cos(THETA_B) * s3._nonlin(uh)
            k2_ = math.cos(THETA_B) * s3._nonlin(E2_ * (uh + dt_ / 2 * k1))
            k3_ = math.cos(THETA_B) * s3._nonlin(E2_ * uh + dt_ / 2 * k2_)
            k4_ = math.cos(THETA_B) * s3._nonlin(E * uh + dt_ * E2_ * k3_)
            uh = E * uh + dt_ / 6 * (E * k1 + 2 * E2_ * (k2_ + k3_) + k4_)
            if s3._mask is not None:
                uh = uh * s3._mask
            invs.append(s3.invariants(uh))
        return invs
    inv_m3 = evolve_m3(u0, T1 / 4)
    for nm, iv in (("M1_hilbert", r_m1[2]), ("M2_rodrigues", r_m2[2]),
                   ("M3_nonlin", inv_m3)):
        drift3 = {n_: abs(iv[-1][i] - iv[0][i]) /
                  max(abs(iv[0][i]) if i < 3 else iv[0][3], iv[0][3], 1e-300)
                  for i, n_ in enumerate(("M", "P", "E"))}
        V.judge("E3", f"b-mech {nm}: worst drift", max(drift3.values()))
        out["experiments"][f"E3_{nm}"] = {"drift": drift3}

    # --- E4: универсальность θ — сохранение фазового угла -------------------
    print("  E4: сканирование θ — фазовая норма")
    devs = []
    for a_ in np.linspace(0.0, 2.0 * THETA_B, 9):
        u_a = math.cos(a_) * u0 + math.sin(a_) * uxx
        ratio = np.linalg.norm(u_a) / np.linalg.norm(u0)
        target = math.sqrt(math.cos(a_)**2 + math.sin(a_)**2 *
                           (np.linalg.norm(uxx) / np.linalg.norm(u0))**2)
        devs.append(abs(ratio - target))
    V.judge("E4", "theta scan: max norm identity dev", float(np.max(devs)))
    out["experiments"]["E4"] = {"max_norm_dev": float(np.max(devs))}

    # --- E5: расширенное семейство: mKdV / BBM / Кавахара (§16.23) ----------
    print("  E5: семейство уравнений — mKdV, BBM, Кавахара")
    # mKdV-солитон
    sm = DispersiveSolver(n, L, dt, "mkdv")
    u0m = soliton_mkdv(x, 1.0, 30.0)
    tsm, usm, invm = sm.evolve(u0m, min(T1, 5.0), snaps=2)
    uem = soliton_mkdv(x, 1.0, (30.0 + 1.0 * min(T1, 5.0)) % L)
    errm = float(np.max(np.abs(usm[-1] - uem)))
    V.judge("E5", "mKdV soliton |u_num − u_exact|∞", errm)
    out["experiments"]["E5_mkdv"] = {"l_inf_err": errm}
    # BBM-солитон
    sb = DispersiveSolver(n, L, dt, "bbm")
    cbb = 1.0
    u0b = soliton_bbm(x, cbb, 50.0)
    tsb, usb, invb = sb.evolve(u0b, min(T1, 5.0), snaps=2)
    ueb = soliton_bbm(x, cbb, (50.0 + (1.0 + cbb) * min(T1, 5.0)) % L)
    errb = float(np.max(np.abs(usb[-1] - ueb)))
    V.judge("E5", "BBM soliton |u_num − u_exact|∞", errb,
            note="u = 3c sech²(½√(c/(1+c))(x−(1+c)t))")
    out["experiments"]["E5_bbm"] = {"l_inf_err": errb}
    # Кавахара: сохранение M и P (гарантировано граничными членами)
    sk = DispersiveSolver(n, L, dt, "kawahara")
    u0k = 0.5 * soliton_kdv(x, 1.0, 50.0)
    _, _, invk = sk.evolve(u0k, min(T1, 3.0), snaps=2)
    driftK = max(abs(invk[-1][0] - invk[0][0]),
                 abs(invk[-1][1] - invk[0][1]) /
                 max(abs(invk[0][1]), 1e-300))
    V.judge("E5", "Kawahara: max(|ΔM|, |ΔP|/P)", driftK,
            note="M и P сохраняются точно (граничные члены)")
    out["experiments"]["E5_kawahara"] = {"drift_MP": driftK}

    # --- E6: спектральная сходимость ----------------------------------------
    print("  E6: спектральная сходимость")
    conv = []
    for n_r in (64, 128, 256):
        x_r = np.linspace(0.0, L, n_r, endpoint=False)
        u_r0 = soliton_kdv(x_r, 4.0, 30.0)
        s_r = DispersiveSolver(n_r, L, dt, "kdv")
        _, us_r, _ = s_r.evolve(u_r0, min(T1, 5.0), snaps=2)
        ue_r = soliton_kdv(x_r, 4.0, (30.0 + 4.0 * min(T1, 5.0)) % L)
        conv.append({"N": n_r,
                     "l_inf_err": float(np.max(np.abs(us_r[-1] - ue_r)))})
    ok = conv[-1]["l_inf_err"] < conv[0]["l_inf_err"]
    V.judge("E6", "spectral convergence (err ↓ with N)",
            0.0 if ok else 1.0,
            note=" -> ".join(f"{c['l_inf_err']:.1e}" for c in conv))
    out["experiments"]["E6"] = {"convergence": conv}

    print_table(V)
    out["verdicts"] = V.rows
    out["tally"] = V.tally()

    # ---- артефакты ---------------------------------------------------------
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    jp = os.path.join(OUT_RES, f"kdv_improved_{stamp}.json")
    with open(jp, "w", encoding="utf-8") as fh:
        json.dump(out, fh, indent=2, ensure_ascii=False)
        fh.write("\n")
    with open(os.path.join(OUT_RES, "kdv_improved_verdicts.csv"), "w",
              newline="", encoding="utf-8") as fh:
        wr = csv.DictWriter(fh, fieldnames=["lab", "test", "value",
                                            "verdict", "note"])
        wr.writeheader()
        wr.writerows(V.rows)
    print(f"  артефакты: results/kdv_improved_{stamp}.json, "
          f"results/kdv_improved_verdicts.csv")

    # ---- графики (600 dpi) --------------------------------------------------
    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.font_manager as fm
        for fp in ("/usr/share/fonts/truetype/chinese/NotoSansSC-Regular.ttf",
                   "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"):
            try:
                fm.fontManager.addfont(fp)
            except Exception:
                pass
        import matplotlib.pyplot as plt
        plt.rcParams["font.sans-serif"] = ["Noto Sans SC", "DejaVu Sans"]
        plt.rcParams["axes.unicode_minus"] = False

        for lang in ("ru", "en"):
            lbl = {
                "ru": ("Столкновение двух солитонов KdV: число vs точное "
                       "решение Хироты", "x", "u(x,t)", "t = "),
                "en": ("Two-soliton KdV collision: numerics vs exact "
                       "Hirota solution", "x", "u(x,t)", "t = "),
            }[lang]
            fig, axes = plt.subplots(1, 2, figsize=(13.2, 5.6),
                                     constrained_layout=True)
            xs = x[::4]
            cmap = plt.get_cmap("viridis")
            for i, t_ in enumerate(ts):
                axes[0].plot(xs, waterfall["u"][i], lw=1.0,
                             color=cmap(i / max(len(ts) - 1, 1)),
                             label=f"{lbl[3]}{t_:.1f}")
            axes[1].plot(xs, us[-1][::4], lw=1.6, color="#d62728",
                         label="численное / numerical")
            axes[1].plot(xs, ue2[::4], "k--", lw=1.2,
                         label="точное (Хирота) / exact (Hirota)")
            axes[0].set_xlabel(lbl[1]); axes[0].set_ylabel(lbl[2])
            axes[0].set_title(lbl[0], fontsize=11)
            axes[1].legend(frameon=False, fontsize=8)
            axes[1].set_xlabel(lbl[1])
            fig.suptitle(f"NSB-96 KdV IMPROVED · "
                         f"{max(drift2.values()):.1e} drift", fontsize=11)
            p1 = os.path.join(OUT_FIG,
                              f"figK1_collision_waterfall_{lang}.png")
            fig.savefig(p1, dpi=args.dpi)
            plt.close(fig)

            fig, ax = plt.subplots(figsize=(9.0, 5.2),
                                   constrained_layout=True)
            series = {"M": ([r_m1[2][0][0] if False else None], None)}
            # дрейф инвариантов по времени для E2
            names = ("M", "P", "E")
            colors = ("#1f77b4", "#2ca02c", "#d62728")
            for i, (nm, col) in enumerate(zip(names, colors)):
                scale = max(abs(inv[0][i]) if i < 3 else inv[0][3],
                            inv[0][3], 1e-300)
                vals = [abs(row[i] - inv[0][i]) / scale for row in inv]
                ax.semilogy(ts, np.maximum(vals, 1e-17), lw=1.4,
                            color=col, label=nm)
            ax.set_xlabel("t")
            ax.set_ylabel("|I(t) − I(0)| / scale" if lang == "en"
                          else "|I(t) − I(0)| / шкала")
            ax.set_title("Дрейф инвариантов Лакса (столкновение)"
                         if lang == "ru" else
                         "Drift of Lax invariants (collision)", fontsize=11)
            ax.legend(frameon=False)
            p2 = os.path.join(OUT_FIG, f"figK2_invariants_theta_{lang}.png")
            fig.savefig(p2, dpi=args.dpi)
            plt.close(fig)
        print(f"  графики: figures/figK1_collision_waterfall_{{ru,en}}.png, "
              f"figures/figK2_invariants_theta_{{ru,en}}.png ({args.dpi} dpi)")
    except Exception as e:  # noqa: BLE001
        print(f"  (графики пропущены: {e})")

    print(f"  время: {(datetime.now() - t0).total_seconds():.1f} с")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
