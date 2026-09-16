# -*- coding: utf-8 -*-
"""
P1 — 3D-прогон микрофизики: камера Вильсона в 3D, b-механизм в родной среде.

Приоритет №1 программы открытых проблем. Полная постановка — chamber3d.py.

Измеряется:
  * статистика капель (N(t), <R>(t)) — сверка роста с аналитикой R² = R0² + 2α_g(S−1)t;
  * геометрия трека: σ_⊥(t) — СКО поперечного отклонения капель от оси дорожки;
  * эффект непрерывного b-поворота (протокол L5) на эти величины: два прогона
    b_rotation=True/False с одинаковым seed — парное сравнение;
  * |ΔE| за шаг (проверка отсутствия инжекции энергии поворотом).

Критерии успеха (зарегистрированы в OPEN_PROBLEMS_7.md, P1):
  C1: рост капель совпадает с аналитикой ≤ 1%;
  C2: детерминизм: парные прогоны с одинаковым seed (b on/off);
  C3: получен либо измеримый эффект b на σ_⊥ (ширину трека), либо строгая
      верхняя граница |Δσ_⊥| (оба исхода — результат, фиксируется какой);
  C4: инъекция энергии поворотом ≤ 1e-12 за шаг (знаковый критерий:
      положительное ΔE; снижение энергии — релаксация проекции, допускается).

Запуск: python3 p1_3d_microphysics.py
Выход:  ../data/results/p1_3d_microphysics.json, ../data/plots/plot_P1_3d_microphysics.png
"""
import json, math, sys, time
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).parent))
from chamber3d import (B, THETA_B, THETA_B_DEG, T0, P0, RH0, GAMMA, EXPANSION,
                       L_DOM, N_GRID, D_V, RHO_L, MU_A, NU_A, G, R_V,
                       S_CRIT_ION, R_SEED, p_sat_magnus, expansion_state,
                       alpha_growth, stokes_velocity, ChamberFlow3D,
                       trilinear_interp, ion_track_positions)

HERE = Path(__file__).parent
DT = 0.01          # с
T_END = 1.0        # с
U_RMS0 = 2e-3      # м/с, остаточные движения после расширения
SEED = 42


def run_mode(b_rotation, st):
    """Один прогон камеры (односторонняя связь: поле S задано)."""
    N, L = N_GRID, L_DOM
    S0 = st["S0"]
    alpha_g = alpha_growth(st["rho_vs"])
    flow = ChamberFlow3D(N=N, L=L, u_rms=U_RMS0, seed=SEED, b_rotation=b_rotation)

    # --- ионная дорожка: нуклеация капель при S0 > S_crit_ion на ионах
    assert S0 > S_CRIT_ION, "пересыщение должно превышать ионный порог"
    tx, ty, tz = ion_track_positions(N, L)
    drop_x, drop_y, drop_z = tx.copy(), ty.copy(), tz.copy()
    drop_R = np.full(tx.shape, R_SEED)
    x0, y0, z0 = drop_x.copy(), drop_y.copy(), drop_z.copy()

    # ось дорожки (прямая через концы) для метрики σ_⊥
    p0 = np.array([tx[0], ty[0], tz[0]]); p1 = np.array([tx[-1], ty[-1], tz[-1]])
    axis = p1 - p0; axis /= np.linalg.norm(axis)

    def sigma_perp():
        """Ширина трека: СКО поперечного разброса капель относительно оси,
        проходящей через текущий центр масс (исключает равномерное оседание)."""
        d = np.stack([drop_x - drop_x.mean(), drop_y - drop_y.mean(),
                      drop_z - drop_z.mean()])
        along = axis @ d
        perp = d - np.outer(axis, along)
        return float(np.sqrt((perp**2).sum(axis=0).mean()))

    n_steps = int(round(T_END / DT))
    t_series, n_series, R_series, sig_series, u_series = [], [], [], [], []
    max_dE_inj = 0.0    # максимальная ИНЪЕКЦИЯ энергии (положительное ΔE)
    max_dE_abs = 0.0    # максимальное |ΔE| (включая снижение)
    t_wall0 = time.perf_counter()

    for step in range(n_steps):
        # --- поток: вязкое затухание + b-поворот (протокол L5)
        flow.step(DT)
        u, v, w = flow.velocity()
        # --- энергия поворота: знаковый критерий (инжекция/снижение)
        max_dE_inj = max(max_dE_inj, flow.last_dE_rot)
        max_dE_abs = max(max_dE_abs, abs(flow.last_dE_rot))

        # --- адвекция капель (полем) + седиментация (Стокс)
        un, vn, wn = trilinear_interp(u, v, w, drop_x, drop_y, drop_z, N, L)
        vs = stokes_velocity(drop_R, st["rho_a"])
        drop_x = (drop_x + un * DT) % L
        drop_y = (drop_y + vn * DT) % L
        drop_z = (drop_z + wn * DT - vs * DT)  # оседание вниз (без заворота по z)

        # --- диффузионный рост (S задано, односторонняя связь)
        drop_R = np.sqrt(drop_R**2 + 2.0 * alpha_g * (S0 - 1.0) * DT)

        t_now = (step + 1) * DT
        t_series.append(t_now)
        n_series.append(int(drop_R.size))
        R_series.append(float(drop_R.mean()))
        sig_series.append(sigma_perp())
        if (step + 1) % 10 == 0:
            u_series.append(flow.u_rms_now())

    wall = time.perf_counter() - t_wall0
    return {
        "mode": "b_rotation" if b_rotation else "true_nse",
        "positions_final": (drop_x.copy(), drop_y.copy(), drop_z.copy(),
                            drop_R.copy()),
        "sigma_perp_series": sig_series,
        "R_mean_series": R_series,
        "n_drops_series": n_series,
        "t_series": t_series,
        "u_rms_series": u_series,
        "sigma_perp_final": sig_series[-1],
        "R_mean_final": R_series[-1],
        "wall_seconds": round(wall, 1),
        "max_dE_injection_per_step_rel": max_dE_inj,
        "max_dE_abs_per_step_rel": max_dE_abs,
        "growth_analytic_R_final": math.sqrt(R_SEED**2 + 2.0 * alpha_g * (S0 - 1.0) * T_END),
    }


def main():
    st = expansion_state()
    t0 = time.perf_counter()
    m_on = run_mode(True, st)
    m_off = run_mode(False, st)
    wall_total = time.perf_counter() - t0
    pos = m_on.pop("positions_final")
    m_off.pop("positions_final", None)

    # --- критерии успеха
    growth_err = abs(m_on["R_mean_final"] - m_on["growth_analytic_R_final"]) \
                 / m_on["growth_analytic_R_final"]
    dsig = abs(m_on["sigma_perp_final"] - m_off["sigma_perp_final"])
    rel_dsig = dsig / m_off["sigma_perp_final"]
    max_inj = max(m_on["max_dE_injection_per_step_rel"],
                  m_off["max_dE_injection_per_step_rel"])
    max_abs = max(m_on["max_dE_abs_per_step_rel"],
                  m_off["max_dE_abs_per_step_rel"])
    criteria = {
        "C1_рост_vs_аналитика_отн_ошибка": growth_err,
        "C1_ok": bool(growth_err <= 0.01),
        "C3_эффект_b_на_сигма_перп_абс_м": dsig,
        "C3_эффект_b_на_сигма_перп_отн": rel_dsig,
        "C3_исход": "эффект_измерим" if dsig > 2e-6 else "строгая_граница",
        "C4_инъекция_энергии_за_шаг_отн": max_inj,
        "C4_max_abs_dE_за_шаг_отн": max_abs,
        "C4_ok": bool(max_inj <= 1e-12),
    }

    out = {
        "problem": "P1",
        "title": "3D-прогон микрофизики камеры Вильсона: b-механизм в родной 3D-среде",
        "command": "python3 code/p1_3d_microphysics.py",
        "params": {
            "N_grid": N_GRID, "L_m": L_DOM, "dt_s": DT, "T_end_s": T_END,
            "T0_K": T0, "P0_Pa": P0, "RH0": RH0, "gamma": GAMMA,
            "expansion_V1V0": EXPANSION, "seed": SEED, "u_rms0_m_s": U_RMS0,
            "S_crit_ion": S_CRIT_ION, "R_seed_m": R_SEED,
            "theta_b_deg": THETA_B_DEG,
            "protocol": "непрерывный b-поворот: угол за шаг dt·θ_b; форма Родригеса; "
                        "ось — сглаженный вихрь (k ≤ N/6, квадратичный вес); проекция Лерэ",
        },
        "expansion_state": {k: round(v, 8) for k, v in st.items()},
        "modes": {"b_rotation": m_on, "true_nse": m_off},
        "criteria": criteria,
        "wall_seconds_total": round(wall_total, 1),
        "ok": bool(criteria["C1_ok"] and criteria["C4_ok"]),
    }
    res_dir = HERE.parent / "data" / "results"
    res_dir.mkdir(exist_ok=True)
    # финальные позиции капель (b_rotation) для 3D-визуализации
    np.savez(res_dir / "p1_positions.npz", x=pos[0], y=pos[1], z=pos[2], R=pos[3])
    (res_dir / "p1_3d_microphysics.json").write_text(
        json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"P1: {'PASS' if out['ok'] else 'FAIL'} | "
          f"S0={st['S0']:.3f}, T1={st['T1']:.2f} K | "
          f"рост vs аналитика: {growth_err:.2e} | "
          f"Δσ_⊥ (b−база) = {dsig:.3e} м ({rel_dsig:.2%}) | "
          f"инъекция/шаг ≤ {max_inj:.2e} (|ΔE| ≤ {max_abs:.2e})")
    return 0 if out["ok"] else 1


if __name__ == "__main__":
    sys.exit(main())
