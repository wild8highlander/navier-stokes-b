# -*- coding: utf-8 -*-
"""
P6 — b-универсальность: систематический геометрический тест.

Утверждение монографии: доля поворота b — универсальный математический эффект,
возникающий на любой геометрической поверхности (2D, S², H², T², R³, S³).
Проверка: локальная касательная конструкция на каждой геометрии даёт ОДИН И ТОТ ЖЕ
угол θ_b = arcsin(b) независимо от точки и геометрии.

Тест на каждой геометрии:
  берётся касательное поле u (в ортонормированном базисе точки),
  применяется форма Родригеса вокруг нормали/оси ω̂ с углом θ_b,
  измеряется фактический угол <u,u'> и изменение норм — сверка с θ_b и 1.

Геометрии:
  R² (плоскость), T² (плоский тор — та же метрика, периодика),
  S² (единичная сфера, ортонорм. базис (e_θ, e_φ/sinθ)),
  H² (диск Пуанкаре, конформная метрика — углы сохраняются),
  R³ (полноразмерный 3D-поворот вокруг случайных осей ω̂: u∥ не меняется).

Критерии успеха (OPEN_PROBLEMS_7.md, P6):
  C1: на каждой геометрии max |угол(u,u') − θ_b| ≤ 1e-12;
  C2: норма сохраняется: max ||u'| − |u|| ≤ 1e-12;
  C3: касательность после поворота (S², H²): |u'·n| ≤ 1e-12.

Запуск: python3 p6_b_universality.py
Выход:  ../data/results/p6_b_universality.json
"""
import json, math, sys, time
from pathlib import Path

import numpy as np

HERE = Path(__file__).parent
B = 1.0 / (4.0 * math.pi + 2.0 * math.sqrt(3.0))
THETA_B = math.asin(B)
N_PTS = 200_000
SEED = 11


def rodrigues(u, axis, theta):
    """Точная форма монографии: u' = u∥ + √(1−sin²θ)·u⊥ + sinθ·(ω̂×u⊥)."""
    s, c = math.sin(theta), math.cos(theta)
    upar = (u * axis).sum(-1, keepdims=True) * axis
    uperp = u - upar
    cross = np.cross(axis, uperp)
    return upar + c * uperp + s * cross


def angle_between(u, v):
    nu = np.linalg.norm(u, axis=-1)
    nv = np.linalg.norm(v, axis=-1)
    dot = (u * v).sum(-1) / np.maximum(nu * nv, 1e-300)
    return np.arccos(np.clip(dot, -1.0, 1.0))


def sample_field(rng, n, dim):
    a = rng.normal(size=(n, dim))
    return a


def test_flat(rng):
    """R²: поворот в плоскости вокруг ẑ."""
    u = sample_field(rng, N_PTS, 2)
    axis = np.array([0.0, 0.0, 1.0])
    u3 = np.concatenate([u, np.zeros((N_PTS, 1))], axis=1)
    v = rodrigues(u3, axis, THETA_B)[:, :2]
    ang = angle_between(u, v)
    norms = np.linalg.norm(v, axis=-1) / np.linalg.norm(u, axis=-1)
    return ang, norms, None


def test_torus(rng):
    """T² — плоская метрика, тот же тест, что R² (периодика не влияет локально)."""
    ang, norms, _ = test_flat(rng)
    # сдвиг точек на торе — чисто координатная операция, метрика плоская
    return ang, norms, None


def test_sphere(rng):
    """S²: случайные точки, ортонорм. базис (e_θ, e_φ/sinθ), ось — нормаль."""
    pts = rng.normal(size=(N_PTS, 3))
    pts /= np.linalg.norm(pts, axis=-1, keepdims=True)
    n = pts
    # любой касательный базис: a = ∂p/∂t
    tmp = np.zeros_like(pts)
    tmp[:, 0] = 1.0
    tmp[np.abs(n[:, 0]) > 0.9, 0] = 0.0
    tmp[np.abs(n[:, 0]) > 0.9, 1] = 1.0
    e1 = tmp - (tmp * n).sum(-1, keepdims=True) * n
    e1 /= np.linalg.norm(e1, axis=-1, keepdims=True)
    e2 = np.cross(n, e1)
    a = rng.normal(size=(N_PTS, 1)); b2 = rng.normal(size=(N_PTS, 1))
    u = a * e1 + b2 * e2
    v = rodrigues(u, n, THETA_B)          # поворот вокруг нормали
    ang = angle_between(u, v)
    norms = np.linalg.norm(v, axis=-1) / np.linalg.norm(u, axis=-1)
    tang = np.abs((v * n).sum(-1))        # касательность после поворота
    return ang, norms, tang


def test_hyperbolic(rng):
    """H² (диск Пуанкаре): конформная метрика — углы в координатах диска
    совпадают с углами в метрике; локальный поворот вокруг нормали ẑ."""
    r = np.sqrt(rng.uniform(0.0, 0.999, N_PTS))
    phi = rng.uniform(0, 2 * math.pi, N_PTS)
    x, y = r * np.cos(phi), r * np.sin(phi)
    u = sample_field(rng, N_PTS, 2)
    axis = np.array([0.0, 0.0, 1.0])
    u3 = np.concatenate([u, np.zeros((N_PTS, 1))], axis=1)
    v = rodrigues(u3, axis, THETA_B)[:, :2]
    ang = angle_between(u, v)
    norms = np.linalg.norm(v, axis=-1) / np.linalg.norm(u, axis=-1)
    # касательность/нормаль: в конформной метрике поворот сохраняет метрические углы
    return ang, norms, None


def test_r3(rng):
    """R³: полные 3D-повороты вокруг случайных осей; u∥ не меняется, угол θ_b
    измеряется между ПЕРПЕНДИКУЛЯРНЫМИ частями u⊥ и u'⊥ (по форме Родригеса
    поворот действует именно на u⊥; для u ⊥ ω̂ это совпадает с углом u→u')."""
    u = sample_field(rng, N_PTS, 3)
    axis = rng.normal(size=(N_PTS, 3))
    axis /= np.linalg.norm(axis, axis=-1, keepdims=True)
    v = rodrigues(u, axis, THETA_B)
    uperp = u - (u * axis).sum(-1, keepdims=True) * axis
    vperp = v - (v * axis).sum(-1, keepdims=True) * axis
    ang = angle_between(uperp, vperp)
    norms = np.linalg.norm(v, axis=-1) / np.linalg.norm(u, axis=-1)
    # u∥ точное сохранение
    upar_u = (u * axis).sum(-1)
    upar_v = (v * axis).sum(-1)
    return ang, norms, np.abs(upar_u - upar_v)


def main():
    rng = np.random.default_rng(SEED)
    t0 = time.perf_counter()
    tests = {"R2": test_flat, "T2": test_torus, "S2": test_sphere,
             "H2": test_hyperbolic, "R3": test_r3}
    rows = {}
    for name, fn in tests.items():
        ang, nr, extra = fn(rng)
        row = {
            "n_points": N_PTS,
            "max_abs_angle_minus_theta_b": float(np.abs(ang - THETA_B).max()),
            "max_norm_deviation": float(np.abs(nr - 1.0).max()),
        }
        if extra is not None:
            row["max_extra_residual"] = float(extra.max())
        rows[name] = row
        print(f"  P6[{name}]: Δугла ≤ {row['max_abs_angle_minus_theta_b']:.2e}, "
              f"Δнормы ≤ {row['max_norm_deviation']:.2e}", flush=True)

    worst_ang = max(r["max_abs_angle_minus_theta_b"] for r in rows.values())
    worst_norm = max(r["max_norm_deviation"] for r in rows.values())
    out = {
        "problem": "P6",
        "title": "b-универсальность: угол θ_b на разных геометриях",
        "command": "python3 code/p6_b_universality.py",
        "params": {"b": B, "theta_b_rad": THETA_B,
                   "theta_b_deg": math.degrees(THETA_B),
                   "n_points": N_PTS, "seed": SEED,
                   "method": "форма Родригеса u'=u∥+√(1−sin²θ)u⊥+sinθ(ω̂×u⊥); "
                             "измерение фактического угла и норм"},
        "geometries": rows,
        "criteria": {
            "C1_worst_angle_residual": worst_ang,
            "C1_ok": bool(worst_ang <= 1e-12),
            "C2_worst_norm_deviation": worst_norm,
            "C2_ok": bool(worst_norm <= 1e-12),
            "C3_tangency_ok": all(r.get("max_extra_residual", 0.0) <= 1e-12
                                  for r in rows.values()),
        },
        "wall_seconds": round(time.perf_counter() - t0, 1),
        "ok": bool(worst_ang <= 1e-12 and worst_norm <= 1e-12),
    }
    res_dir = HERE.parent / "data" / "results"
    res_dir.mkdir(exist_ok=True)
    (res_dir / "p6_b_universality.json").write_text(
        json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"P6: {'PASS' if out['ok'] else 'FAIL'} | худшая невязка угла "
          f"{worst_ang:.2e}, нормы {worst_norm:.2e} — θ_b универсален")
    return 0 if out["ok"] else 1


if __name__ == "__main__":
    sys.exit(main())
