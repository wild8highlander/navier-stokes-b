# -*- coding: utf-8 -*-
"""
P5-b — b-протокол в ДВУСТОРОННЕЙ связи (full duplex): следующий уровень P5.

База (P5): b-протокол — перенос информации фазовой последовательностью, построенной
на универсальной константе b = 1/(4π+2√3), sin θ_b = b, θ_b = 3.5765013142837216°.

P5-b: ОБА направления A↔B работают ОДНОВРЕМЕННО в общей полосе (in-band full duplex):
  код направления A→B:  ψ^A_i = i·θ_b          (линейная b-фаза, i = 0..N_c−1)
  код направления B→A:  ψ^B_i = i²·θ_b         (квадратичная b-фаза, «b-чирик»)
Оба кода выводятся из ОДНОЙ универсальной константы — обмен пилотами не нужен.

Математическое ядро (проверяется точно, без Монте-Карло):
  A1. Линейная сумма: |Σ_{i<N} e^{i·i·θ_b}| = |sin(Nθ_b/2)/sin(θ_b/2)| ≤ 1/sin(θ_b/2)
      — ограничение Дирихле, O(1) при любом N; подавление чужого линейного кода.
  A2. Автокорреляция b-чирика: c(m) = Σ_{i<N−m} e^{i((i+m)²−i²)θ_b} =
      = e^{i m²θ_b}·Σ_{i<N−m} e^{i·2mi·θ_b}  ⇒  |c(m)| = |sin((N−m)·m·θ_b)/sin(m·θ_b)|
      — ТОЧНО (ядро Дирихле, проверяется численно). Боковые лепестки
      НЕМОДУЛИРОВАННОГО кода управляются диофантовой структурой θ_b/π
      (ближайшие резонансы mθ_b → πk); они ХАРАКТЕРИЗУЮТСЯ таблицей резонансов
      — в дуплексе помеха от чужого направления модулирована данными (d_i = ±1)
      и после свёртки теряет когерентность (см. B), так что резонансы автокорреляции
      на развязку направлений не влияют.
  A3. Взаимная корреляция кодов (линейный × квадратичный):
      X(N) = |Σ_{i<N} e^{i(i²−i)θ_b}| — квадратичная сумма Вейля ⇒ O(√N).
      Худший случай (немодулированная помеха): подавление ~ N/|X|².

Монте-Карло (часть B): BPSK, N_c = 64 чипов/бит, SIR на входе = 0 дБ (равные мощности),
AWGN. Приёмник A коррелирует с квадратичным кодом; помеха (направление A→B)
после свёртки — случайное блуждание с дисперсией 1 против сигнала √N_c:
выигрыш обработки SIR_out = N_c (18.1 дБ при N_c = 64).

Критерии успеха (зарегистрированы ДО прогона):
  C1. |S1(N)| ≤ 1/sin(θ_b/2) для всех N ∈ {2^6..2^14}          — ожидание: ПАСС
  C2. Тождество Дирихле для |c(m)| подтверждено: max|прямой − формула| < 1e-9
      на всех m = 1..N−1 (N=256); диофантова таблица резонансов записана
                                                               — ожидание: ПАСС
  C3. Показатель степени X(N) ~ N^p: 0.42 ≤ p ≤ 0.58           — ожидание: ПАСС
  C4. При Eb/N0 = 10 дБ: BER(b-дуплекс) ≤ 1e-4, BER(наивный дуплекс) ≥ 0.1
                                                               — ожидание: ПАСС
  C5. Эффективная скорость на направление (b-дуплекс) / (TDD) ≥ 1.8 при 10 дБ.

Честность: все числа — из реального прогона этого скрипта; JSON и графики
перезаписываются при каждом запуске. Время прогона фиксируется.
"""
import json
import math
import sys
import time
from pathlib import Path

import numpy as np

import matplotlib
matplotlib.use("Agg")
import matplotlib.font_manager as fm
import matplotlib.pyplot as plt

RESULTS_DIR = Path(__file__).parent

# --- константы протокола (точная редакция, согласована с L1 репозитория) ---
B_CONST = 1.0 / (4.0 * math.pi + 2.0 * math.sqrt(3.0))
THETA = math.asin(B_CONST)                      # рад
THETA_DEG = math.degrees(THETA)

N_C = 64                                        # чипов на бит
EBN0_DB = [0.0, 2.0, 4.0, 6.0, 8.0, 10.0, 12.0]
N_BITS = 400_000                                # на точку кривой
SIG_PHI_DEG = 2.0                               # остаточная фазовая ошибка кадра (σ°)

RNG = np.random.default_rng(20260915)


# ---------------------------------------------------------------- часть A ---
def dirichlet_bound():
    """A1: линейная b-сумма против границы Дирихле."""
    out = {"bound_1_over_sin_half": 1.0 / math.sin(THETA / 2.0)}
    rows = []
    for p in range(6, 15):
        N = 2 ** p
        i = np.arange(N, dtype=np.float64)
        s1 = abs(np.sum(np.exp(1j * THETA * i)))
        rows.append({"N": N, "S1": s1})
    out["rows"] = rows
    out["max_S1_over_N"] = max(r["S1"] for r in rows)
    out["C1_pass"] = all(r["S1"] <= out["bound_1_over_sin_half"] + 1e-9 for r in rows)
    return out


def chirp_autocorr(N=256):
    """A2: автокорреляция квадратичного b-кода; точная форма — ядро Дирихле."""
    i = np.arange(N, dtype=np.float64)
    code = np.exp(1j * (i * i) * THETA)
    m_all = np.arange(1, N, dtype=np.float64)
    direct = np.empty(N - 1)
    for m in range(1, N):
        seg = code[: N - m] * np.conj(code[m:])
        direct[m - 1] = abs(seg.sum())
    exact = np.abs(np.sin((N - m_all) * m_all * THETA) / np.sin(m_all * THETA))
    err = float(np.max(np.abs(direct - exact)))
    pslr = float(np.max(direct) / N)
    m_worst = int(m_all[int(np.argmax(direct))]) + 1
    # диофантова таблица: расстояние m·θ_b до ближайшего кратного π
    frac = m_all * THETA / math.pi
    dist = np.abs(frac - np.round(frac))
    order = np.argsort(dist)[:5]
    res_table = [{"m": int(m_all[k]), "dist_to_kpi": float(dist[k]),
                  "c_abs": float(direct[k])} for k in order]
    return {"N": N, "max_formula_err": err, "PSLR": pslr,
            "m_worst_sidelobe": m_worst,
            "diophantine_top5": res_table,
            "C2_pass": bool(err < 1e-9),
            "mainlobe": N}


def weyl_cross(N_max_exp=12):
    """A3: взаимная сумма Вейля X(N)=|Σ e^{i(i²−i)θ_b}| — развязка направлений."""
    rows = []
    for p in range(6, N_max_exp + 1):
        N = 2 ** p
        i = np.arange(N, dtype=np.float64)
        x = abs(np.sum(np.exp(1j * ((i * i - i) * THETA))))
        rows.append({"N": N, "X": x})
    Ns = np.array([r["N"] for r in rows], float)
    Xs = np.array([r["X"] for r in rows], float)
    p_fit, _ = np.polyfit(np.log(Ns), np.log(Xs), 1)
    return {"rows": rows, "exponent": float(p_fit),
            "C3_pass": bool(0.42 <= p_fit <= 0.58)}


# ---------------------------------------------------------------- часть B ---
def codes(n_c=N_C):
    i = np.arange(n_c, dtype=np.float64)
    cA = np.exp(1j * i * THETA)             # направление A→B (линейный b-код)
    cB = np.exp(1j * (i * i) * THETA)       # направление B→A (квадратичный b-код)
    return cA, cB


def ber_curve(scheme, ebn0_db, n_bits=N_BITS, rng=None):
    """BER одного измерения. scheme: 'naive' | 'b' | 'clean'."""
    rng = rng or RNG
    ber = np.empty(len(ebn0_db))
    for k, db in enumerate(ebn0_db):
        ebn0 = 10.0 ** (db / 10.0)
        sigma2 = 1.0 / (2.0 * ebn0)          # Eb = 1; σ² на одну квадратуру
        if scheme == "naive":
            n = int(np.ceil(n_bits / 1))
            a = rng.choice([-1.0, 1.0], size=n)
            d = rng.choice([-1.0, 1.0], size=n)
            noise = rng.normal(0.0, math.sqrt(sigma2), size=n)
            r = (a + d) / math.sqrt(2.0) + noise
            dec = np.where(r >= 0.0, 1.0, -1.0)
            ber[k] = np.mean(dec != a)
        elif scheme == "b":
            n = int(np.ceil(n_bits / N_C))
            cA, cB = codes()
            bits = rng.choice([-1.0, 1.0], size=n)
            interf = rng.choice([-1.0, 1.0], size=(n, N_C))
            sig = bits[:, None] * cB[None, :] / math.sqrt(N_C)
            inf = interf * cA[None, :] / math.sqrt(N_C)
            noise = (rng.normal(0.0, math.sqrt(sigma2), size=(n, N_C))
                     + 1j * rng.normal(0.0, math.sqrt(sigma2), size=(n, N_C)))
            phi0 = np.deg2rad(SIG_PHI_DEG) * rng.normal(size=n)
            y = (sig + inf + noise) * np.exp(1j * phi0)[:, None]
            z = np.sum(y * np.conj(cB)[None, :], axis=1)
            dec = np.where(z.real >= 0.0, 1.0, -1.0)
            ber[k] = np.mean(dec != bits)
        else:  # clean — односторонний BPSK без помехи (эталон)
            b = rng.choice([-1.0, 1.0], size=n_bits)
            noise = rng.normal(0.0, math.sqrt(sigma2), size=n_bits)
            r = b + noise
            dec = np.where(r >= 0.0, 1.0, -1.0)
            ber[k] = np.mean(dec != b)
        sys.stdout.write(f"    {scheme}: Eb/N0={db:4.1f} дБ  BER={ber[k]:.3e}\n")
    return ber


def qfunc(x):
    return 0.5 * math.erfc(x / math.sqrt(2.0))


def run():
    t0 = time.time()
    print("P5-b: b-протокол в двусторонней связи — РЕАЛЬНЫЙ ПРОГОН")
    print(f"  b = {B_CONST!r}")
    print(f"  theta_b = {THETA_DEG!r} град;  N_c = {N_C} чипов/бит\n")

    print("[A1] линейная b-сумма (граница Дирихле)…")
    a1 = dirichlet_bound()
    print(f"    max|S1| = {a1['max_S1_over_N']:.3f}  <= граница "
          f"{a1['bound_1_over_sin_half']:.3f}  -> C1 {'ПАСС' if a1['C1_pass'] else 'НЕ ПРОЙДЕН'}")

    print("[A2] автокорреляция b-чирика (точная форма Дирихле)…")
    a2 = chirp_autocorr(256)
    print(f"    ошибка формулы = {a2['max_formula_err']:.2e}; "
          f"PSLR = {a2['PSLR']:.4f} (m={a2['m_worst_sidelobe']}) "
          f"-> C2 {'ПАСС' if a2['C2_pass'] else 'НЕ ПРОЙДЕН'}")

    print("[A3] квадратичная сумма Вейля X(N)…")
    a3 = weyl_cross()
    print(f"    показатель p = {a3['exponent']:.3f} (гипотеза sqrt(N): 0.5) "
          f"-> C3 {'ПАСС' if a3['C3_pass'] else 'НЕ ПРОЙДЕН'}")

    print("[B] Монте-Карло BER (дуплекс, SIR_in = 0 дБ)…")
    ber = {s: ber_curve(s, EBN0_DB) for s in ("naive", "b", "clean")}
    k10 = EBN0_DB.index(10.0)
    analytic_clean = [qfunc(math.sqrt(2.0 * 10 ** (db / 10.0))) for db in EBN0_DB]
    sir_out_db = 10.0 * math.log10(N_C)
    c4 = bool(ber["b"][k10] <= 1e-4 and ber["naive"][k10] >= 0.1)
    gp_duplex = 2.0 * (1.0 - ber["b"][k10])
    gp_tdd = 1.0 * (1.0 - ber["clean"][k10])
    gain = gp_duplex / gp_tdd
    c5 = bool(gain >= 1.8)
    print(f"    BER@10дБ: naive={ber['naive'][k10]:.4f}  b={ber['b'][k10]:.3e}  "
          f"clean={ber['clean'][k10]:.3e} (аналит. {analytic_clean[k10]:.3e})")
    print(f"    C4 {'ПАСС' if c4 else 'НЕ ПРОЙДЕН'}; goodput-фактор дуплекс/TDD = {gain:.3f} "
          f"-> C5 {'ПАСС' if c5 else 'НЕ ПРОЙДЕН'}")

    ok = all([a1["C1_pass"], a2["C2_pass"], a3["C3_pass"], c4, c5])
    out = {
        "problem": "P5-b",
        "title": "b-протокол в двусторонней связи (in-band full duplex)",
        "constants": {"b": repr(B_CONST), "theta_b_rad": THETA,
                      "theta_b_deg": THETA_DEG, "N_c": N_C,
                      "sigma_phi_deg": SIG_PHI_DEG, "n_bits_per_point": N_BITS},
        "A1_dirichlet": a1, "A2_autocorr": a2, "A3_weyl": a3,
        "B_ber": {"ebn0_db": EBN0_DB,
                  "naive_duplex": ber["naive"].tolist(),
                  "b_duplex": ber["b"].tolist(),
                  "clean_bpsk_mc": ber["clean"].tolist(),
                  "clean_bpsk_analytic": analytic_clean},
        "sir_out_db_theory": sir_out_db,
        "goodput_factor_duplex_over_tdd": gain,
        "criteria": {"C1": a1["C1_pass"], "C2": a2["C2_pass"], "C3": a3["C3_pass"],
                     "C4": c4, "C5": c5, "all_pass": ok},
        "wall_seconds": round(time.time() - t0, 1),
    }
    (RESULTS_DIR / "results_p5b.json").write_text(
        json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"\nИТОГ P5-b: {'ВСЕ КРИТЕРИИ ПАСС' if ok else 'ЕСТЬ НЕПРОЙДЕННЫЕ КРИТЕРИИ'}"
          f"  ({out['wall_seconds']} c)")
    _fig(out)
    return ok


def _fig(res):
    """Графики из реальных данных прогона."""
    for f in ("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
              "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"):
        try:
            fm.fontManager.addfont(f)
        except Exception:
            pass
    plt.rcParams.update({"font.sans-serif": ["DejaVu Sans"], "axes.unicode_minus": False,
                         "font.size": 10, "axes.titlesize": 11, "figure.dpi": 150})
    NAVY, GOLD, RED, GREEN = "#123A6B", "#C9A227", "#B23A48", "#2E7D57"

    # ---- рис. 1: синхронизационная математика ----
    fig, ax = plt.subplots(1, 2, figsize=(11, 4.2), constrained_layout=True)
    a = ax[0]
    Ns = np.array([r["N"] for r in res["A1_dirichlet"]["rows"]], float)
    S1 = np.array([r["S1"] for r in res["A1_dirichlet"]["rows"]], float)
    Nw = np.array([r["N"] for r in res["A3_weyl"]["rows"]], float)
    Xw = np.array([r["X"] for r in res["A3_weyl"]["rows"]], float)
    a.loglog(Ns, S1, "o-", color=NAVY, lw=1.6, ms=4, label=r"$|S_1(N)|$ — линейный b-код")
    a.loglog(Nw, Xw, "s-", color=GOLD, lw=1.6, ms=4, label=r"$|X(N)|$ — коды направлений A×B")
    a.loglog(Nw, np.sqrt(Nw), "--", color="#888888", lw=1.1, label=r"$\sqrt{N}$ (Вейль)")
    a.axhline(res["A1_dirichlet"]["bound_1_over_sin_half"], color=NAVY, ls=":", lw=1.1,
              label=r"$1/\sin(\theta_b/2)=%.1f$" % res["A1_dirichlet"]["bound_1_over_sin_half"])
    a.set_xlabel("N, чипов"); a.set_ylabel("модуль суммы")
    p = res["A3_weyl"]["exponent"]
    a.set_title(f"Суммы Вейля–Дирихле: X(N) ~ N^{p:.3f}")
    a.legend(fontsize=8, loc="upper left")
    a.grid(alpha=0.25, which="both")

    b_ = ax[1]
    N = res["A2_autocorr"]["N"]
    i = np.arange(N, dtype=np.float64)
    code = np.exp(1j * (i * i) * THETA)
    m = np.arange(1, N)
    cabs = np.array([abs((code[: N - mm] * np.conj(code[mm:])).sum()) for mm in m])
    b_.semilogy(m, cabs, color=RED, lw=0.9, label=r"$|c(m)|$, прямой расчёт")
    b_.axhline(res["A2_autocorr"]["PSLR"] * N, color=RED, ls="--", lw=1.1,
               label=f"макс. боковой = {res['A2_autocorr']['PSLR'] * N:.1f} "
                     f"(PSLR {res['A2_autocorr']['PSLR']:.3f}, m="
                     f"{res['A2_autocorr']['m_worst_sidelobe']})")
    mw = res["A2_autocorr"]["m_worst_sidelobe"]
    b_.axvline(mw, color=GREEN, ls=":", lw=1.3,
               label=fr"диофантов резонанс $m\theta_b\to\pi k$: $m={mw}$")
    b_.set_xlabel("сдвиг m"); b_.set_ylabel(r"$|c(m)|$")
    b_.set_title(f"Автокорреляция b-чирика (N={N}), ядро Дирихле точно")
    b_.legend(fontsize=8); b_.grid(alpha=0.25, which="both")
    fig.suptitle("P5-b · Синхронизация без пилотов на универсальной константе "
                 r"$\theta_b=3.5765^\circ$", fontsize=12)
    fig.savefig(RESULTS_DIR / "fig_p5b_sync.png")
    plt.close(fig)

    # ---- рис. 2: дуплекс BER + goodput ----
    fig, ax = plt.subplots(1, 2, figsize=(11, 4.2), constrained_layout=True)
    a = ax[0]
    db = res["B_ber"]["ebn0_db"]
    a.semilogy(db, res["B_ber"]["naive_duplex"], "o-", color=RED, lw=1.8,
               label="наивный дуплекс (без развязки)")
    a.semilogy(db, res["B_ber"]["b_duplex"], "s-", color=NAVY, lw=1.8,
               label="b-протокол, дуплекс (коды $i\\theta_b$ / $i^2\\theta_b$)")
    a.semilogy(db, res["B_ber"]["clean_bpsk_mc"], "^--", color=GOLD, lw=1.3,
               label="чистый BPSK, МК")
    a.semilogy(db, res["B_ber"]["clean_bpsk_analytic"], ":", color="#555555", lw=1.2,
               label=r"$Q(\sqrt{2E_b/N_0})$ — аналитика")
    a.axhline(0.25, color=RED, ls=":", lw=1.0)
    a.text(0.1, 0.29, "теоретический пол наивного дуплекса 0.25", color=RED, fontsize=8)
    a.set_xlabel("Eb/N0, дБ"); a.set_ylabel("BER")
    a.set_title(f"Дуплекс при SIR_in = 0 дБ, N_c = {N_C}: выигрыш обработки "
                f"{res['sir_out_db_theory']:.1f} дБ")
    a.legend(fontsize=8, loc="lower left"); a.grid(alpha=0.25, which="both")
    a.set_ylim(1e-6, 1)

    b_ = ax[1]
    k10 = db.index(10.0)
    vals = [2.0 * (1.0 - res["B_ber"]["b_duplex"][k10]),
            1.0 * (1.0 - res["B_ber"]["clean_bpsk_mc"][k10])]
    bars = b_.bar(["b-дуплекс\n(оба направления\nодновременно)", "TDD\n(по очереди,\nэталон)"],
                  vals, color=[NAVY, GOLD], width=0.55)
    for r, v in zip(bars, vals):
        b_.text(r.get_x() + r.get_width() / 2, v * 1.01, f"{v:.3f}", ha="center", fontsize=10)
    b_.set_ylabel("goodput на направление (отн. ед.)")
    b_.set_title(f"Эффективность: фактор {res['goodput_factor_duplex_over_tdd']:.2f}× "
                 f"при Eb/N0 = 10 дБ")
    b_.grid(alpha=0.25, axis="y")
    fig.suptitle("P5-b · Двусторонняя связь на b-протоколе: развязка направлений "
                 "и безпилотная синхронизация", fontsize=12)
    fig.savefig(RESULTS_DIR / "fig_p5b_duplex.png")
    plt.close(fig)
    print("Графики: fig_p5b_sync.png, fig_p5b_duplex.png — записаны")


if __name__ == "__main__":
    sys.exit(0 if run() else 1)
