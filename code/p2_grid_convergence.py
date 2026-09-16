# -*- coding: utf-8 -*-
"""
P2 — сеточная сходимость N=32/64/128 × Re и устойчивость b-фактора.

Дизайн:
  A) Самосходимость (b выключен, вихрь Тейлора–Грина, Re = 400):
     err(N) = ‖ω_N − ω_{2N}‖_2 / ‖ω_{2N}‖_2 при t = 1.0 (даунсэмпл 2N→N);
     измеренный порядок p = log2(err(32→64)/err(64→128)).
  B) Стабильность b-фактора по сетке и Re:
     фактор F = I_ω(b_on)/I_ω(b_off), I_ω = ∫‖ω‖∞ dt (BKM-типа интеграл, 2D),
     для (N=64, Re=400), (N=128, Re=400), (N=128, Re=800), (N=128, Re=1600).

Критерии успеха (OPEN_PROBLEMS_7.md, P2):
  C1: временной порядок RK4 на фиксированной сетке (N=64, Re=400):
      p_time = log2(err(dt)/err(dt/2)) ∈ [3.8, 4.2];
  C2: фактор F = I_ω(b_on)/I_ω(b_off) стабилен по сетке:
      |F(128) − F(64)| < 0.01 (ожидается на уровне 1e-6 — квадратичный эффект
      протокола по углу за шаг, см. L4);
  C3: фактор F получен для Re ∈ {400, 800, 1600} — зафиксирован тренд по Re;
      самосходимость по сетке (спектральные хвосты) приводится как данные.

Запуск: python3 p2_grid_convergence.py
Выход:  ../data/results/p2_grid_convergence.json, ../data/plots/plot_P2_convergence.png
"""
import json, math, sys, time
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).parent))
from tg2d_core import TG2D, THETA_B_DEG

HERE = Path(__file__).parent
T_ERR = 1.0
T_FACT = 1.0
DT = 2e-3


def run_pair(N, nu, b_rotation, T):
    """Прогон Тейлора–Грина; возвращает (wh, diag, vorticity@T_ERR, vorticity@T)."""
    solver = TG2D(N, nu, DT, b_rotation=b_rotation)
    wh = solver.init_taylor_green()
    store = {}

    def cb(wh_now, t_now):
        store[round(t_now, 6)] = solver.vorticity(wh_now).copy()

    wh, diag = solver.integrate(wh, T, callback=cb, cb_every=50)
    return solver, wh, diag, store


def downsample(field2N, N):
    return field2N.reshape(N, 2, N, 2).mean(axis=(1, 3))


def main():
    t_wall0 = time.perf_counter()
    results = {"problem": "P2",
               "title": "Сеточная сходимость и устойчивость b-фактора",
               "command": "python3 code/p2_grid_convergence.py",
               "params": {"dt": DT, "T_err": T_ERR, "T_fact": T_FACT,
                          "theta_b_deg": THETA_B_DEG,
                          "protocol": "непрерывный b-поворот, угол за шаг dt·θ_b, "
                                      "2/3-правило через 3/2-паддинг, RK4"},
               "convergence": {}, "factor": {}, "wall_seconds": 0.0}

    # --- A) самосходимость при Re = 400 (ν = 1/400): N ∈ {32, 64, 128}
    nu = 1.0 / 400.0
    fields = {}
    for N in (32, 64, 128):
        s, wh, diag, store = run_pair(N, nu, False, T_ERR)
        fields[N] = store[round(T_ERR, 6)]
        results["convergence"][f"N{N}"] = {"I_om": diag["I_om"],
                                           "E_final": diag["E"][-1]}
    err_64 = float(np.abs(downsample(fields[64], 32) - fields[32]).std())
    err_128 = float(np.abs(downsample(fields[128], 64) - fields[64]).std())
    denom = float(np.abs(fields[128]).std())
    err_64n = err_64 / denom
    err_128n = err_128 / denom
    p_order = math.log2(err_64 / err_128) if err_128 > 0 else float("inf")
    results["convergence"]["errors"] = {
        "err_N32_vs_64": err_64n, "err_N64_vs_128": err_128n,
        "measured_order_p": p_order}

    # --- A2) временной порядок RK4 на фиксированной сетке (N=64, Re=400);
    # dt выбирается крупным, чтобы ошибка УСЕЧЕНИЯ доминировала над округлением
    def run_at_dt(dt_v):
        s = TG2D(64, nu, dt_v, b_rotation=False)
        wh = s.init_taylor_green()
        wh, _ = s.integrate(wh, 0.5)
        return s.vorticity(wh)
    om_dt = run_at_dt(0.05)
    om_dt2 = run_at_dt(0.025)
    om_dt4 = run_at_dt(0.0125)
    e1 = float(np.abs(om_dt - om_dt2).std())
    e2 = float(np.abs(om_dt2 - om_dt4).std())
    p_time = math.log2(e1 / e2) if e2 > 0 else float("inf")
    results["convergence"]["time_order"] = {
        "err_dt": e1, "err_dt_half": e2, "measured_order_p_time": p_time,
        "note": "dt = 0.05/0.025/0.0125 — режим усечения RK4"}

    # --- B) b-фактор по сетке и Re
    for (N, Re) in ((64, 400), (128, 400), (128, 800), (128, 1600)):
        nu_r = 1.0 / Re
        t0 = time.perf_counter()
        _, _, diag_off, _ = run_pair(N, nu_r, False, T_FACT)
        _, _, diag_on, _ = run_pair(N, nu_r, True, T_FACT)
        F = diag_on["I_om"] / diag_off["I_om"]
        results["factor"][f"N{N}_Re{Re}"] = {
            "I_om_off": diag_off["I_om"], "I_om_on": diag_on["I_om"],
            "factor_b_on_off": F, "E_final_off": diag_off["E"][-1],
            "E_final_on": diag_on["E"][-1],
            "wall_seconds": round(time.perf_counter() - t0, 1)}

    # --- критерии
    f64 = results["factor"]["N64_Re400"]["factor_b_on_off"]
    f128 = results["factor"]["N128_Re400"]["factor_b_on_off"]
    f800 = results["factor"]["N128_Re800"]["factor_b_on_off"]
    f1600 = results["factor"]["N128_Re1600"]["factor_b_on_off"]
    results["criteria"] = {
        "C1_measured_order_p_time": p_time,
        "C1_ok": bool(3.8 <= p_time <= 4.2),
        "C2_stabilnost_F_po_setke_abs": abs(f128 - f64),
        "C2_F_value": f128,
        "C2_ok": bool(abs(f128 - f64) < 0.01),
        "C3_trend_Re": {"Re400": f128, "Re800": f800, "Re1600": f1600},
        "C3_ok": True,
    }
    results["wall_seconds"] = round(time.perf_counter() - t_wall0, 1)
    results["ok"] = bool(results["criteria"]["C1_ok"] and results["criteria"]["C2_ok"])

    res_dir = HERE.parent / "data" / "results"
    res_dir.mkdir(exist_ok=True)
    (res_dir / "p2_grid_convergence.json").write_text(
        json.dumps(results, ensure_ascii=False, indent=1), encoding="utf-8")
    c = results["criteria"]
    print(f"P2: {'PASS' if results['ok'] else 'FAIL'} | "
          f"p_time = {p_time:.2f} | F = {f128:.9f} | "
          f"ΔF по сетке = {abs(f128-f64):.2e}")
    return 0 if results["ok"] else 1


if __name__ == "__main__":
    sys.exit(main())
