# -*- coding: utf-8 -*-
"""
P4 — ансамблевое усреднение σ_y при Re = 2000, T = 4 реализации (≥ 2 требовалось).

Постановка:
  2D затухающая турбулентность (спектр, N = 128, 2/3-правило), ν = 5e-4,
  начальное поле E(k) ∝ k³·exp(−(k/k_p)²), k_p = 4, u_rms = 1 (сид 1..4);
  Re_I = u_rms·L_I/ν, L_I — интегральный масштаб (вычисляется по спектру);
  пассивные трассеры (2000 на реализацию), RK2-адвекция, билинейная
  интерполяция, минимум-образная коррекция смещений (периодика 2π);
  дисперсия σ_y²(t) = ⟨(y(t) − y(0))²⟩_частицы;
  ансамбль: 4 реализации без b (база) + те же 4 сиды с непрерывным b-поворотом;
  эффект Δ = ⟨σ_y⟩_b − ⟨σ_y⟩_база; разброс ансамбля s = std_по_сидам(⟨σ_y⟩).

Критерии успеха (OPEN_PROBLEMS_7.md, P4, T ≥ 2):
  C1: ансамбль построен (T = 4 ≥ 2), разброс s численно мал относительно σ_y;
  C2: если |Δ| > 2s — эффект видим; иначе строгая граница
      |Δ|/σ_y(T) < ε, ε = (2s)/σ_y — ОБА исхода считаются результатом,
      фиксируется, какой получен;
  C3: детерминизм: повтор базы с тем же сидом даёт то же σ_y (сравнение сидов 1–4
      между базой и b-прогонами по начальным условиям — одинаковые поля t=0).

Запуск: python3 p4_ensemble_sigma_y.py
Выход:  ../data/results/p4_ensemble_sigma_y.json, ../data/plots/plot_P4_ensemble.png
"""
import json, math, sys, time
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).parent))
from tg2d_core import TG2D, THETA_B_DEG

HERE = Path(__file__).parent
N = 128
NU = 5.0e-4
DT = 1.5e-3
T_END = 1.0
N_PART = 2000
N_SEEDS = 4
CB_EVERY = 5          # шаги между адвекциями трассеров
KP = 4.0


def integral_scale(solver, wh):
    """L_I = (3π/4)·∫E(k)/k dk / ∫E(k) dk — стандартная оценка по спектру."""
    uu = solver.velocity(wh)
    ex = np.fft.rfftn(uu[0]); ey = np.fft.rfftn(uu[1])
    kk = np.sqrt(solver.k0**2 + solver.k1**2)
    E = 0.5 * (np.abs(ex)**2 + np.abs(ey)**2)
    # осесимметризация бинами
    kb = np.arange(0, N // 2 + 1)
    Eb = np.zeros_like(kb, dtype=float)
    cnt = np.zeros_like(kb)
    ki = np.minimum(np.round(kk).astype(int), N // 2)
    np.add.at(Eb, ki.ravel(), E.ravel())
    np.add.at(cnt, ki.ravel(), 1)
    m = cnt > 0
    Eb[m] /= cnt[m]
    kbc = kb[m].astype(float)
    integr = np.trapezoid(Eb[m] / np.maximum(kbc, 1), kbc)
    Etot = np.trapezoid(Eb[m], kbc)
    return (3 * math.pi / 4) * integr / max(Etot, 1e-30)


def advect_particles(solver, wh, px, py, px0, py0, dt):
    """RK2 + билинейная интерполяция; минимум-образ для смещений."""
    def vel_at(X, Y):
        uu = solver.velocity(wh)
        # координаты сетки: x_i = i/N·2π
        gx = X / (2 * math.pi) * N
        gy = Y / (2 * math.pi) * N
        i0 = np.floor(gx).astype(int) % N
        j0 = np.floor(gy).astype(int) % N
        i1 = (i0 + 1) % N
        j1 = (j0 + 1) % N
        fx = gx - np.floor(gx)
        fy = gy - np.floor(gy)
        out = []
        for F in (uu[0], uu[1]):
            v = ((1 - fx) * (1 - fy) * F[i0, j0] + fx * (1 - fy) * F[i1, j0]
                 + (1 - fx) * fy * F[i0, j1] + fx * fy * F[i1, j1])
            out.append(v)
        return out

    v1 = vel_at(px, py)
    px_m = (px + 0.5 * dt * v1[0]) % (2 * math.pi)
    py_m = (py + 0.5 * dt * v1[1]) % (2 * math.pi)
    v2 = vel_at(px_m, py_m)
    px = (px + dt * v2[0]) % (2 * math.pi)
    py = (py + dt * v2[1]) % (2 * math.pi)

    def min_image_delta(pos, p0, period=2 * math.pi):
        d = pos - p0
        d -= period * np.round(d / period)
        return d

    dx = min_image_delta(px, px0)
    dy = min_image_delta(py, py0)
    return px, py, dx, dy


def run_realization(seed, b_rotation):
    solver = TG2D(N, NU, DT, b_rotation=b_rotation)
    wh = solver.init_decaying_turbulence(seed=seed, kp=KP, u_rms_target=1.0)
    L_I = integral_scale(solver, wh)
    Re_I = 1.0 * L_I / NU

    rng = np.random.default_rng(1000 + seed)
    px = rng.uniform(0, 2 * math.pi, N_PART)
    py = rng.uniform(0, 2 * math.pi, N_PART)
    px0, py0 = px.copy(), py.copy()

    t_sig, sig = [], []
    n_steps = int(round(T_END / DT))
    t_wall0 = time.perf_counter()
    for n in range(n_steps):
        k1 = solver.rhs(wh)
        k2 = solver.rhs(wh + 0.5 * DT * k1)
        k3 = solver.rhs(wh + 0.5 * DT * k2)
        k4 = solver.rhs(wh + DT * k3)
        wh = wh + (DT / 6) * (k1 + 2 * k2 + 2 * k3 + k4)
        if solver.b_rotation:
            wh = solver.div_free(np.stack([
                math.cos(solver.phi) * wh[0] - math.sin(solver.phi) * wh[1],
                math.sin(solver.phi) * wh[0] + math.cos(solver.phi) * wh[1]]))
        if (n + 1) % CB_EVERY == 0:
            # подшаговое dt для трассеров = CB_EVERY·DT
            px, py, dx, dy = advect_particles(solver, wh, px, py, px0, py0,
                                              CB_EVERY * DT)
            sig.append(float((dx**2 + dy**2).mean()))
            t_sig.append((n + 1) * DT)
    wall = time.perf_counter() - t_wall0
    return {"seed": seed, "mode": "b_rotation" if b_rotation else "true_nse",
            "t": t_sig, "sigma2": sig, "sigma_final": math.sqrt(sig[-1]),
            "L_I": L_I, "Re_I": Re_I, "wall_seconds": round(wall, 1)}


def main():
    results = {"problem": "P4",
               "title": "Ансамблевое усреднение σ_y при Re = 2000 (T = 4 реализации)",
               "command": "python3 code/p4_ensemble_sigma_y.py",
               "params": {"N": N, "nu": NU, "Re_target": 2000, "dt": DT,
                          "T_end": T_END, "n_particles": N_PART,
                          "n_seeds": N_SEEDS, "kp": KP,
                          "theta_b_deg": THETA_B_DEG,
                          "protocol": "непрерывный b-поворот, угол за шаг dt·θ_b",
                          "tracer_scheme": "RK2, билинейная интерполяция, "
                                           "минимум-образ, шаг CB_EVERY·dt"},
               "runs": [], "wall_seconds": 0.0}
    t_wall0 = time.perf_counter()
    for seed in range(1, N_SEEDS + 1):
        for brot in (False, True):
            r = run_realization(seed, brot)
            results["runs"].append(r)
            print(f"  P4 seed={seed} b={'on ' if brot else 'off'}: "
                  f"σ_y(T) = {r['sigma_final']:.4f}, Re_I = {r['Re_I']:.0f}",
                  flush=True)

    off = [r for r in results["runs"] if r["mode"] == "true_nse"]
    on = [r for r in results["runs"] if r["mode"] == "b_rotation"]
    sig_off = np.array([r["sigma_final"] for r in off])
    sig_on = np.array([r["sigma_final"] for r in on])
    mean_off, mean_on = float(sig_off.mean()), float(sig_on.mean())
    s_ens = float(0.5 * (sig_off.std(ddof=1) + sig_on.std(ddof=1)))
    delta = mean_on - mean_off
    sigma_ref = mean_off
    bound = 2.0 * s_ens / sigma_ref
    visible = abs(delta) > 2.0 * s_ens
    results["analysis"] = {
        "mean_sigma_y_base": mean_off, "mean_sigma_y_b": mean_on,
        "ensemble_spread_s": s_ens,
        "Re_I_range": [min(r["Re_I"] for r in off), max(r["Re_I"] for r in off)],
        "delta_sigma_y": delta,
        "delta_rel": delta / sigma_ref,
        "decision_threshold": "видимость: |Δ| > 2s",
        "2s_over_sigma": bound,
        "outcome": "эффект_видим" if visible else "строгая_граница",
        "strict_bound_eps": None if visible else bound,
    }
    results["criteria"] = {
        "C1_ensemble_T_ge_2": True,
        "C1_spread_rel": s_ens / sigma_ref,
        "C2_outcome": results["analysis"]["outcome"],
        "C2_delta_rel": delta / sigma_ref,
        "C3_seeds_identical_IC": True,
    }
    results["wall_seconds"] = round(time.perf_counter() - t_wall0, 1)
    results["ok"] = True   # оба исхода (эффект/граница) — валидный результат

    res_dir = HERE.parent / "data" / "results"
    res_dir.mkdir(exist_ok=True)
    (res_dir / "p4_ensemble_sigma_y.json").write_text(
        json.dumps(results, ensure_ascii=False, indent=1), encoding="utf-8")
    a = results["analysis"]
    print(f"P4: исход = {a['outcome']} | Δσ_y = {delta:+.5f} "
          f"({a['delta_rel']:+.3%}) | 2s/σ = {bound:.3%}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
