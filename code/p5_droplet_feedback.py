# -*- coding: utf-8 -*-
"""
P5 — обратная связь капель на поток: истощение пара + динамическое торможение
(следующий уровень P1; двусторонняя связь).

Над P1 добавлено (флаг feedback=True):
  1) истощение пара: каждая капля поглощает пар
       ṁ_i = 4π R_i·D_v·ρ_vs·(S_cell − 1)  [кг/с]
     поле S обновляется по ячейкам: ΔS = −Σ ṁ·dt/(ρ_vs·V_cell),
     далее диффузионное выравнивание пара: ∂S/∂t = D_v∇²S (Фурье, периодика);
  2) динамическое торможение потока каплями (Стокс): сила на жидкость
       f_cell = −Σ 6πμ_a R_i (u_cell − v_drop)/V_cell,  u += f·dt/ρ_a.

Дизайн сравнения: два прогона с b-протоколом (включён в обоих — эффект b уже
зафиксирован в P1), отличаются только обратной связью:
  A) one_way (feedback=False) — как P1;
  B) two_way (feedback=True).

Критерии успеха (OPEN_PROBLEMS_7.md, P5):
  C1: истощение пара реально: S_min(T) < S0 − 0.1·(S0 − 1) в треке (two_way);
  C2: средний радиус R̄_two_way(T) < R̄_one_way(T) (рост замедлен истощением);
  C3: эффект на поток зафиксирован: Δu_rms(t) измерен (величина любая —
      эффект или строгая граница, указано, что получено);
  C4: массовый баланс пара: испарённый дефицит Σ|ΔS|·V_cell·ρ_vs согласован
      с суммарной массой конденсата в каплях (отн. ошибка ≤ 5%).

Запуск: python3 p5_droplet_feedback.py
Выход:  ../data/results/p5_droplet_feedback.json, ../data/plots/plot_P5_feedback.png
"""
import json, math, sys, time
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).parent))
from chamber3d import (B, THETA_B, THETA_B_DEG, T0, P0, RH0, GAMMA, EXPANSION,
                       L_DOM, N_GRID, D_V, RHO_L, MU_A, NU_A, G, R_V,
                       S_CRIT_ION, R_SEED, expansion_state, alpha_growth,
                       stokes_velocity, ChamberFlow3D, trilinear_interp,
                       ion_track_positions)

HERE = Path(__file__).parent
DT = 0.01
T_END = 1.0
U_RMS0 = 2e-3
SEED = 42


def cell_index(x, y, z, N, L):
    i = np.clip((x / L * N).astype(int), 0, N - 1)
    j = np.clip((y / L * N).astype(int), 0, N - 1)
    k = np.clip((z / L * N).astype(int), 0, N - 1)
    return i, j, k


def run_mode(feedback, st):
    N, L = N_GRID, L_DOM
    S0 = st["S0"]
    alpha_g = alpha_growth(st["rho_vs"])
    rho_vs, rho_a = st["rho_vs"], st["rho_a"]
    flow = ChamberFlow3D(N=N, L=L, u_rms=U_RMS0, seed=SEED, b_rotation=True)

    tx, ty, tz = ion_track_positions(N, L)
    drop_x, drop_y, drop_z = tx.copy(), ty.copy(), tz.copy()
    drop_R = np.full(tx.shape, R_SEED)

    p0 = np.array([tx[0], ty[0], tz[0]]); p1 = np.array([tx[-1], ty[-1], tz[-1]])
    axis = p1 - p0; axis /= np.linalg.norm(axis)

    def sigma_perp():
        """Ширина трека относительно текущего центра масс (как в P1)."""
        d = np.stack([drop_x - drop_x.mean(), drop_y - drop_y.mean(),
                      drop_z - drop_z.mean()])
        along = axis @ d
        perp = d - np.outer(axis, along)
        return float(np.sqrt((perp**2).sum(axis=0).mean()))

    S = np.full((N, N, N), S0)
    V_cell = (L / N)**3
    n_steps = int(round(T_END / DT))
    t_s, Smin_s, Smean_s, R_s, sig_s, urms_s = [], [], [], [], [], []
    dep_mass = 0.0             # суммарный дефицит пара (по полю), кг
    t_wall0 = time.perf_counter()

    for step in range(n_steps):
        flow.step(DT)
        u, v, w = flow.velocity()

        if feedback:
            # --- 1) истощение пара и масса-точный рост капель (единый поток)
            i_c, j_c, k_c = cell_index(drop_x, drop_y, drop_z, N, L)
            S_cell = S[i_c, j_c, k_c]
            flux = 4.0 * math.pi * drop_R * D_V * rho_vs * np.maximum(S_cell - 1.0, 0.0)
            dS = np.zeros((N, N, N))
            np.add.at(dS, (i_c, j_c, k_c), -flux * DT / (rho_vs * V_cell))
            S += dS
            dep_mass += float(flux.sum() * DT)          # пар, снятый с поля
            # рост капель: точная форма по R² (та же, что без обратной связи):
            # d(R²)/dt = 2α_g(S−1) — совпадает с потоком массы 4πR·D_v·ρ_vs(S−1)
            drop_R = np.sqrt(np.maximum(
                drop_R**2 + 2.0 * alpha_g * np.maximum(S_cell - 1.0, 0.0) * DT,
                R_SEED**2))
            # диффузионное выравнивание пара (консервативно, rfft-решётка)
            Sh = np.fft.rfftn(S)
            kh = np.fft.fftfreq(N, d=1.0 / N)
            K2 = (kh[:, None, None]**2 + kh[None, :, None]**2
                  + kh[None, None, : N // 2 + 1]**2)
            S = np.fft.irfftn(Sh * np.exp(-D_V * K2 * DT),
                              s=(N, N, N), axes=(0, 1, 2))
            # --- 2) реакция оседания на поток (Стокс): капли тянут воздух вниз
            vs_i = stokes_velocity(drop_R, rho_a)
            fz = np.zeros((N, N, N))
            np.add.at(fz, (i_c, j_c, k_c),
                      -6.0 * math.pi * MU_A * drop_R * vs_i)
            w += fz * DT / (rho_a * V_cell)
            # фиксируем реакцию в спектре поля — обратная связь накапливается
            flow.uh = [np.fft.rfftn(a) for a in (u, v, w)]
            flow._vel_cache = [u, v, w]

        # --- адвекция капель текущим полем + седиментация
        un, vn, wn = trilinear_interp(u, v, w, drop_x, drop_y, drop_z, N, L)
        vs = stokes_velocity(drop_R, rho_a)
        drop_x = (drop_x + un * DT) % L
        drop_y = (drop_y + vn * DT) % L
        drop_z = drop_z + wn * DT - vs * DT

        # --- рост без обратной связи (аналитический закон, как в P1)
        if not feedback:
            drop_R = np.sqrt(drop_R**2 + 2.0 * alpha_g * (S0 - 1.0) * DT)

        t_now = (step + 1) * DT
        t_s.append(t_now)
        Smin_s.append(float(S.min()) if feedback else S0)
        Smean_s.append(float(S.mean()) if feedback else S0)
        R_s.append(float(drop_R.mean()))
        sig_s.append(sigma_perp())
        if (step + 1) % 10 == 0:
            urms_s.append(flow.u_rms_now())

    wall = time.perf_counter() - t_wall0
    cond_final = float((4.0 / 3.0 * math.pi * drop_R**3 * RHO_L).sum())
    return {"mode": "two_way" if feedback else "one_way",
            "t_series": t_s, "S_min_series": Smin_s, "S_mean_series": Smean_s,
            "R_mean_series": R_s, "sigma_perp_series": sig_s,
            "u_rms_series": urms_s,
            "R_mean_final": R_s[-1], "S_min_final": Smin_s[-1],
            "sigma_perp_final": sig_s[-1],
            "condensate_mass_kg": cond_final,
            "vapor_deficit_mass_kg": dep_mass,
            "wall_seconds": round(wall, 1)}


def main():
    st = expansion_state()
    t0 = time.perf_counter()
    m_two = run_mode(True, st)
    m_one = run_mode(False, st)
    wall_total = time.perf_counter() - t0

    S0 = st["S0"]
    bal_err = abs(m_two["vapor_deficit_mass_kg"] - m_two["condensate_mass_kg"]) \
              / max(m_two["condensate_mass_kg"], 1e-300)
    criteria = {
        "C1_истощение_пара": bool(m_two["S_min_final"] < S0 - 0.1 * (S0 - 1.0)),
        "C1_S_min_final": m_two["S_min_final"],
        "C2_R_two_way_lt_one_way": bool(m_two["R_mean_final"] < m_one["R_mean_final"]),
        "C2_R_two_way": m_two["R_mean_final"], "C2_R_one_way": m_one["R_mean_final"],
        "C2_замедление_роста_отн": 1.0 - m_two["R_mean_final"] / m_one["R_mean_final"],
        "C3_delta_u_rms_final": (m_two["u_rms_series"][-1]
                                 if m_two["u_rms_series"] else None),
        "C4_баланс_пара_отн_ошибка": bal_err,
        "C4_ok": bool(bal_err <= 0.05),
    }
    out = {
        "problem": "P5",
        "title": "Обратная связь капель на поток: истощение пара + торможение",
        "command": "python3 code/p5_droplet_feedback.py",
        "params": {"N_grid": N_GRID, "L_m": L_DOM, "dt_s": DT, "T_end_s": T_END,
                   "S0": S0, "seed": SEED, "theta_b_deg": THETA_B_DEG,
                   "b_protocol": "включён в обоих прогонах (как P1)",
                   "feedback": "истощение пара (сток 4πR·D_v·ρ_vs(S−1)) + "
                               "динамическое торможение (Стокс, реакция)"},
        "expansion_state": {k: round(v, 8) for k, v in st.items()},
        "runs": {"two_way": m_two, "one_way": m_one},
        "criteria": criteria,
        "wall_seconds_total": round(wall_total, 1),
        "ok": bool(criteria["C1_истощение_пара"] and criteria["C2_R_two_way_lt_one_way"]
                   and criteria["C4_ok"]),
    }
    res_dir = HERE.parent / "data" / "results"
    res_dir.mkdir(exist_ok=True)
    (res_dir / "p5_droplet_feedback.json").write_text(
        json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"P5: {'PASS' if out['ok'] else 'FAIL'} | S_min = {m_two['S_min_final']:.3f} "
          f"(S0 = {S0:.3f}) | R: two_way {m_two['R_mean_final']*1e6:.2f} мкм vs "
          f"one_way {m_one['R_mean_final']*1e6:.2f} мкм | баланс пара {bal_err:.2%}")
    return 0 if out["ok"] else 1


if __name__ == "__main__":
    sys.exit(main())
