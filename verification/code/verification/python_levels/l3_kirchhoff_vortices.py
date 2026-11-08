# -*- coding: utf-8 -*-
"""
L3 — вихри Кирхгофа: система dx/dt = ∂H/∂y, dy/dt = −∂H/∂x
есть гамильтонов поток; φ-динамика — чистый поворот без диссипации.

Проверки:
  1) инвариант H при интегрировании RK4 (дрейф ~ dt⁴);
  2) порядок метода RK4 = 4 (сходимость по тройному измельчению сетки);
  3) сохранение расстояния между точками фазовой жидкости (изометрия потока);
  4) эллиптический случай H = (x²+y²)/2: траектория — окружность, угловая скорость 1.
"""
import json, math, sys
from pathlib import Path

import numpy as np

RESULTS_DIR = Path(__file__).parent / "results"


def H(q):
    """Гамильтониан Кирхгофа-типа: эллиптическая точка + нелинейность (глобальна)."""
    x, y = q
    return 0.5 * (x * x + y * y) + 0.25 * math.sin(x) * math.sin(y)


def grad_H(q):
    x, y = q
    return np.array([x + 0.25 * math.cos(x) * math.sin(y),
                     y + 0.25 * math.sin(x) * math.cos(y)])


def grad_H_harm(q):
    """Гармонический случай H = (x²+y²)/2: поток — жёсткое вращение (изометрия)."""
    x, y = q
    return np.array([x, y])


def rk4_step(q, dt, grad=grad_H):
    def v(qq):
        g = grad(qq)
        return np.array([g[1], -g[0]])
    k1 = v(q)
    k2 = v(q + 0.5 * dt * k1)
    k3 = v(q + 0.5 * dt * k2)
    k4 = v(q + dt * k3)
    return q + (dt / 6) * (k1 + 2 * k2 + 2 * k3 + k4)


def integrate(q0, T, dt, grad=grad_H):
    q = np.asarray(q0, float).copy()
    n = int(round(T / dt))
    for _ in range(n):
        q = rk4_step(q, dt, grad)
    return q


def run():
    rng = np.random.default_rng(42)
    q0 = np.array([0.7, -1.1])
    T = 10.0

    # 1) дрейф инварианта H
    H0 = H(q0)
    drifts = {}
    for dt in (0.1, 0.05, 0.025):
        qT = integrate(q0, T, dt)
        drifts[dt] = abs(H(qT) - H0)

    # 2) порядок RK4: err(dt/2)/err(dt) → 1/16; порядок p = log2(err(dt)/err(dt/2))
    ref = integrate(integrate(q0, T, 0.025), 0.0, 0.001)  # ≈ точка q(T)
    fine = integrate(q0, T, 0.00125)
    e1 = np.linalg.norm(integrate(q0, T, 0.05) - fine)
    e2 = np.linalg.norm(integrate(q0, T, 0.025) - fine)
    order = math.log2(e1 / e2)

    # 3) изометрия: в ГАРМОНИЧЕСКОМ случае (жёсткое вращение) попарные
    #    расстояния между 50 точками сохраняются; в общем нелинейном случае
    #    поток сохраняет площадь, но не расстояния (это НЕ ошибка метода)
    pts = rng.normal(size=(50, 2))
    pts_T = np.stack([integrate(p, T, 0.01, grad_H_harm) for p in pts])
    d0 = np.linalg.norm(pts[:, None, :] - pts[None, :, :], axis=-1)
    dT = np.linalg.norm(pts_T[:, None, :] - pts_T[None, :, :], axis=-1)
    iso_err = float(np.abs(dT - d0).max())
    # сохранение площади в нелинейном случае: det J = 1 — площадь параллелограмма
    # (векторное произведение) сохраняется точно, сдвиг её не меняет
    base = rng.normal(size=2); eps = 1e-4
    tri = [base, base + [eps, 0], base + [0, eps]]
    tri_T = [integrate(p, T, 0.01) for p in tri]
    def para_area(q0, q1, q2):
        d1, d2 = q1 - q0, q2 - q0
        return abs(d1[0] * d2[1] - d1[1] * d2[0])
    a0 = para_area(*tri)
    a1 = para_area(*tri_T)
    area_err = abs(a1 - a0) / a0

    # 4) круговая траектория гармонического случая (dt = 2π/2000 — период делится нацело;
    #    остаточная невязка — реальная фазовая ошибка RK4 порядка z³/6 за шаг)
    qh = np.array([1.0, 0.0])
    dt_c = 2 * math.pi / 2000
    qh_T = integrate(qh, 2 * math.pi, dt_c, grad_H_harm)
    circle_err = float(np.linalg.norm(qh_T - qh))

    out = {
        "level": "L3",
        "checks": {
            "дрейф H, dt=0.1": drifts[0.1],
            "дрейф H, dt=0.05": drifts[0.05],
            "дрейф H, dt=0.025": drifts[0.025],
            "измеренный порядок RK4 (ожидаeтся ≈4)": order,
            "изометрия жёсткого вращения (гармонич. случай), макс. |Δd|": iso_err,
            "сохранение площади (нелинейный случай), отн. ошибка": area_err,
            "гармонический случай: невязка замыкания окружности за 2π": circle_err,
        },
        "ok": bool(drifts[0.025] < drifts[0.05] < drifts[0.1]  # дрейф падает с dt
                   and 3.7 < order < 4.3
                   and iso_err < 1e-9 and area_err < 1e-4
                   and circle_err < 1e-3),
    }
    RESULTS_DIR.mkdir(exist_ok=True)
    (RESULTS_DIR / "l3_kirchhoff_vortices.json").write_text(
        json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"L3: {'PASS' if out['ok'] else 'FAIL'} | порядок RK4 = {order:.2f}, изометрия {iso_err:.2e}")
    return out["ok"]


if __name__ == "__main__":
    sys.exit(0 if run() else 1)
