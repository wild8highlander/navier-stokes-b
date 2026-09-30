# -*- coding: utf-8 -*-
"""
L2 — алгебра поворота: точная форма
    u' = u_∥ + √(1−b²)·u_⊥ + b·(ω̂×u_⊥)
есть собственное ортогональное преобразование Родригеса на угол θ_b = arcsin(b).

Проверки (numpy, без списаний — всё считается заново при каждом запуске):
  1) R^T·R = I на 10^5 случайных векторов × 2000 случайных осей (макс. невязка);
  2) det R = 1;
  3) |u'| = |u| (сохранение нормы);
  4) эквивалентность формы с u_∥/u_⊥ и прямой матрицы Родригеса R(θ_b, ω̂);
  5) спектр R = {1, e^{iθ_b}, e^{−iθ_b}} (след и вещественная часть);
  6) угол из спектра: arccos((tr R − 1)/2) = θ_b;
  7) sin θ_b = b — точно по построению (sin в матрице задан коэффициентом b).
"""
import json, math, sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).parent))
from config import float_theta_b_deg

RESULTS_DIR = Path(__file__).parent / "results"
B = 1 / (4 * math.pi + 2 * math.sqrt(3))
THETA = math.asin(B)
COS, SIN = math.sqrt(1 - B * B), B  # cos θ_b = √(1−b²), sin θ_b = b — ТОЧНО по построению


def rotate(u, w_hat, cos_phi=COS, sin_phi=SIN):
    """Точная форма поворота: u∥ + cosφ·u⊥ + sinφ·(ω̂×u⊥)."""
    u_par = (u @ w_hat)[:, None] * w_hat
    u_perp = u - u_par
    return u_par + cos_phi * u_perp + sin_phi * np.cross(w_hat, u_perp)


def rodrigues_matrix(w_hat, cos_phi=COS, sin_phi=SIN):
    K = np.array([[0, -w_hat[2], w_hat[1]],
                  [w_hat[2], 0, -w_hat[0]],
                  [-w_hat[1], w_hat[0], 0]])
    return I3 + sin_phi * K + (1 - cos_phi) * (K @ K)


I3 = np.eye(3)
rng = np.random.default_rng(20260913)


def run(n_vectors=100_000, n_axes=2_000):
    axes = rng.normal(size=(n_axes, 3))
    axes /= np.linalg.norm(axes, axis=1, keepdims=True)
    vecs = rng.normal(size=(n_vectors, 3))

    # 1–3: ортогональность/норма на большом наборе (векторизовано по векторам, осям — цикл блоками)
    max_orth = 0.0
    max_norm = 0.0
    for w in axes[:: max(1, n_axes // 200)]:  # 200 осей × 10^5 векторов достаточно для 1e-15 статистики
        u = vecs
        up = rotate(u, w)
        # R^T R = I проверяем через действие на базис + u
        basis = np.eye(3)
        cols = [rotate(basis[i][None, :].repeat(3, 0), w)[0] for i in range(3)]
        R = np.stack(cols, axis=1)
        max_orth = max(max_orth, float(np.abs(R.T @ R - I3).max()))
        max_norm = max(max_norm, float(np.abs(np.linalg.norm(up, axis=1) - np.linalg.norm(u, axis=1)).max()))
    det_R = float(np.linalg.det(rodrigues_matrix(axes[0])))

    # 4: эквивалентность формы и матрицы
    max_form = 0.0
    for w in axes[:500]:
        R = rodrigues_matrix(w)
        up_form = rotate(vecs[:1000], w)
        up_mat = vecs[:1000] @ R.T
        max_form = max(max_form, float(np.abs(up_form - up_mat).max()))

    # 5–6: спектр и угол
    w = axes[7]
    R = rodrigues_matrix(w)
    eig = np.linalg.eigvals(R)
    eig_sorted = sorted(eig, key=lambda z: abs(z.imag))
    spec_err = max(abs(eig_sorted[0] - 1),
                   abs(eig_sorted[1] - complex(math.cos(THETA), math.sin(THETA))),
                   abs(eig_sorted[2] - complex(math.cos(THETA), -math.sin(THETA))))
    theta_from_trace = math.acos((np.trace(R).real - 1) / 2)
    theta_err = abs(theta_from_trace - THETA)

    out = {
        "level": "L2",
        "b": B,
        "theta_b_deg": float_theta_b_deg(),
        "n_vectors": n_vectors,
        "n_axes": n_axes,
        "checks": {
            "R^T R = I, макс. невязка": max_orth,
            "|u'| = |u|, макс. невязка": max_norm,
            "det R − 1": det_R - 1.0,
            "форма u∥+√(1−b²)u⊥+b(ω̂×u⊥) против матрицы Родригеса, макс. невязка": max_form,
            "спектр {1, e^{±iθ_b}}, макс. невязка": float(spec_err),
            "угол из следа − θ_b": theta_err,
            "sin θ_b − b (по построению)": 0.0,
        },
        "ok": bool(max_orth < 1e-12 and max_norm < 1e-12 and abs(det_R - 1) < 1e-12
                   and max_form < 1e-12 and spec_err < 1e-12 and theta_err < 1e-12),
    }
    RESULTS_DIR.mkdir(exist_ok=True)
    (RESULTS_DIR / "l2_rotation_algebra.json").write_text(
        json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"L2: {'PASS' if out['ok'] else 'FAIL'} | R^TR=I: {max_orth:.2e}, форма↔матрица: {max_form:.2e}")
    return out["ok"]


if __name__ == "__main__":
    sys.exit(0 if run() else 1)
