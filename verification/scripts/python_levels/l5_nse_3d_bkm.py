# -*- coding: utf-8 -*-
"""
L5 — 3D-эталон: Тейлор–Грин в T³, спектральный метод
(2/3-правило через 3/2-паддинг — без алиасинга; RK4).

Протокол (зафиксирован, воспроизводим):
  N=48, ν=0.01 (Re_TG = 100), T=6, dt=0.004;
  непрерывный b-поворот: угол за шаг φ = dt·θ_b (кумулятивно θ_b·T ≈ 21,459°),
  точная форма Родригеса u' = u_∥ + cos φ·u_⊥ + sin φ·(ω̂×u_⊥), sin θ_b = b;
  ось ω̂ — направление СГЛАЖЕННОГО вихря (моды k ≤ N/6) — регуляризация оси
  в нулях ω (без неё карта нелинейна и неустойчива); квадратичный вес
  q = (|ω|/max|ω|)² гасит поворот там, где вихрь слаб;
  вихрь пересчитывается из повёрнутой скорости; проекция Лерэ.

Сравниваются два прогона: истинные NSE и NSE с поворотом после каждого шага.
Метрики: BKM-интеграл ∫‖ω‖_∞ dt (трапеция, ‖ω‖∞ — каждый шаг),
max‖ω‖_∞, E(t), |ΔE| за один поворот (остаток проекции Лерэ).

Честность: числа печатаются и сохраняются в JSON при каждом запуске;
историческое значение 3,5× относится к недоразрешённой конфигурации N=24
(глава 11 монографии) и здесь НЕ воспроизводится — фиксированный протокол
даёт свои факторы.
"""
import json, math, sys, time, os
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).parent))
from config import L5_PARAMS, float_theta_b_deg

RESULTS_DIR = Path(__file__).parent / "results"
B = 1 / (4 * math.pi + 2 * math.sqrt(3))
THETA = math.asin(B)


class Spectral3D:
    def __init__(self, N):
        self.N = N
        self.crit = N // 3                 # 2/3-правило
        self.NP = int(1.5 * N)             # 3/2-паддинг
        k = np.fft.fftfreq(N, d=1.0 / N)
        self.kx = k[:, None, None]
        self.ky = k[None, :, None]
        self.kz = k[None, None, : k.size // 2 + 1]
        self.K2 = self.kx**2 + self.ky**2 + self.kz**2
        self.K2s = self.K2.copy()
        self.K2s[0, 0, 0] = 1.0
        kP = np.fft.fftfreq(self.NP, d=1.0 / self.NP)
        self.kPx = kP[:, None, None]
        self.kPy = kP[None, :, None]
        self.kPz = kP[None, None, : kP.size // 2 + 1]
        self._mask = ((np.abs(self.kx) <= self.crit)
                      & (np.abs(self.ky) <= self.crit)
                      & (np.abs(self.kz) <= self.crit))[None]
        # маска сглаженного вихря для оси поворота (регуляризация ω̂ в нулях ω)
        cs = self.crit // 2
        self._mask_smooth = ((np.abs(self.kx) <= cs)
                             & (np.abs(self.ky) <= cs)
                             & (np.abs(self.kz) <= cs))[None]
        self._blocks = self._corner_blocks()

    def _corner_blocks(self):
        c = self.crit
        idx = [(slice(None, c + 1), slice(None, c + 1), slice(None, c + 1)),
               (slice(-c, None), slice(None, c + 1), slice(None, c + 1)),
               (slice(None, c + 1), slice(-c, None), slice(None, c + 1)),
               (slice(-c, None), slice(-c, None), slice(None, c + 1)),
               (slice(None, c + 1), slice(None, c + 1), slice(-c, None)),
               (slice(-c, None), slice(None, c + 1), slice(-c, None)),
               (slice(None, c + 1), slice(-c, None), slice(-c, None)),
               (slice(-c, None), slice(-c, None), slice(-c, None))]
        return idx

    def trunc(self, fh):
        return fh * self._mask

    def pad(self, fh):
        out = np.zeros((3, self.NP, self.NP, self.NP // 2 + 1), complex)
        for i, j, kk in self._blocks:
            out[:, i, j, kk] = fh[:, i, j, kk]
        return out

    def unpad(self, fhp):
        out = np.zeros((3, self.N, self.N, self.N // 2 + 1), complex)
        for i, j, kk in self._blocks:
            out[:, i, j, kk] = fhp[:, i, j, kk]
        return out

    def curl(self, fh):
        return np.stack([
            1j * (self.ky * fh[2] - self.kz * fh[1]),
            1j * (self.kz * fh[0] - self.kx * fh[2]),
            1j * (self.kx * fh[1] - self.ky * fh[0]),
        ])

    def curl_p(self, fhp):
        return np.stack([
            1j * (self.kPy * fhp[2] - self.kPz * fhp[1]),
            1j * (self.kPz * fhp[0] - self.kPx * fhp[2]),
            1j * (self.kPx * fhp[1] - self.kPy * fhp[0]),
        ])

    def project(self, fh):
        div = (self.kx * fh[0] + self.ky * fh[1] + self.kz * fh[2]) / self.K2s
        return np.stack([fh[0] - self.kx * div, fh[1] - self.ky * div, fh[2] - self.kz * div])

    def project_p(self, fhp):
        div = (self.kPx * fhp[0] + self.kPy * fhp[1] + self.kPz * fhp[2])
        KP2 = (self.kPx**2 + self.kPy**2 + self.kPz**2)
        KP2[0, 0, 0] = 1.0
        p = div / KP2
        return np.stack([fhp[0] - self.kPx * p, fhp[1] - self.kPy * p, fhp[2] - self.kPz * p])

    def to_real(self, fh):
        return np.fft.irfftn(fh, s=(self.N,) * 3, axes=(1, 2, 3))

    def to_real_p(self, fhp):
        return np.fft.irfftn(fhp, s=(self.NP,) * 3, axes=(1, 2, 3))

    def to_spec(self, f):
        return np.fft.rfftn(f, axes=(1, 2, 3))


def run_case(solver, uh, nu, T, dt, rotate=False, theta=THETA):
    N = solver.N
    phi = dt * theta
    cph, sph = math.cos(phi), math.sin(phi)

    def rhs(uh):
        # скоростная форма: dû/dt = −P(u·∇u) − νk²û; нелинейный член — на 3/2-сетке
        uhp = solver.pad(uh)
        u = solver.to_real_p(uhp)
        gx = solver.to_real_p(1j * solver.kPx * uhp)
        gy = solver.to_real_p(1j * solver.kPy * uhp)
        gz = solver.to_real_p(1j * solver.kPz * uhp)
        adv = np.stack([u[0] * gx[0] + u[1] * gy[0] + u[2] * gz[0],
                        u[0] * gx[1] + u[1] * gy[1] + u[2] * gz[1],
                        u[0] * gx[2] + u[1] * gy[2] + u[2] * gz[2]])
        nlp = solver.project_p(solver.to_spec(adv))
        return solver.unpad(-nlp) - nu * solver.K2 * uh

    n_steps = int(round(T / dt))
    t_series = [0.0]
    w0 = solver.to_real(solver.curl(uh))
    wmax_series = [float(np.linalg.norm(w0, axis=0).max())]
    E_series = [float((solver.to_real(uh)**2).sum() / 2 / N**3)]
    om_max_abs = wmax_series[0]
    max_dE_rot = 0.0
    t = 0.0
    wall0 = time.time()

    for n in range(n_steps):
        k1 = rhs(uh)
        k2 = rhs(uh + 0.5 * dt * k1)
        k3 = rhs(uh + 0.5 * dt * k2)
        k4 = rhs(uh + dt * k3)
        uh = uh + (dt / 6) * (k1 + 2 * k2 + 2 * k3 + k4)
        t += dt

        # диагностика: u и ω считаются один раз и переиспользуются поворотом
        u = solver.to_real(uh)
        w = solver.to_real(solver.curl(uh))

        if rotate:
            wnorm_all = np.linalg.norm(w, axis=0)
            # сглаженный вихрь для оси: регуляризация ω̂ в нулях ω
            ws = solver.to_real(solver.curl(uh * solver._mask_smooth))
            wnorm = np.linalg.norm(ws, axis=0)
            q = (wnorm / wnorm.max()) ** 2          # квадратичный вес
            what = ws / np.maximum(wnorm, 1e-30)[None]
            u_par = (u * what).sum(0)[None] * what
            u_perp = u - u_par
            E_pre = float((u**2).sum() / 2 / N**3)
            Ru = u_par + cph * u_perp + sph * np.cross(what, u_perp, axis=0)
            u_new = u + q[None] * (Ru - u)          # поворот с весом q
            uh = solver.trunc(solver.project(solver.to_spec(u_new)))
            u = solver.to_real(uh)
            E_post = float((u**2).sum() / 2 / N**3)
            max_dE_rot = max(max_dE_rot, abs(E_post - E_pre))
            w = solver.to_real(solver.curl(uh))

        wmax = float(np.linalg.norm(w, axis=0).max())
        E = float((u**2).sum() / 2 / N**3)
        wmax_series.append(wmax)
        t_series.append(t)
        E_series.append(E)
        om_max_abs = max(om_max_abs, wmax)

    I_BKM = float(np.trapezoid(np.array(wmax_series), np.array(t_series)))
    return {
        "mode": "b_rotation" if rotate else "true_nse",
        "I_BKM": I_BKM,
        "omega_max_series": wmax_series,
        "t_series": t_series,
        "E_series": E_series,
        "omega_max_abs": om_max_abs,
        "E_final": E_series[-1],
        "wall_seconds": round(time.time() - wall0, 1),
        "max_dE_per_rotation": max_dE_rot if rotate else None,
    }


def run(N=None, nu=None, T=None, dt=None):
    p = {**L5_PARAMS, **{k: v for k, v in dict(N=N, nu=nu, T=T, dt=dt).items() if v is not None}}
    if os.environ.get("NSE3D_SMALL"):  # быстрый контрольный режим
        p = dict(N=24, nu=0.01, T=1.0, dt=0.01)
    solver = Spectral3D(p["N"])

    # начальное условие Тейлора–Грина
    x = np.arange(p["N"]) * 2 * math.pi / p["N"]
    X, Y, Z = np.meshgrid(x, x, x, indexing="ij")
    u = np.stack([np.sin(X) * np.cos(Y) * np.cos(Z),
                  -np.cos(X) * np.sin(Y) * np.cos(Z),
                  np.zeros_like(X)])
    uh0 = solver.trunc(solver.project(solver.to_spec(u)))

    print(f"L5: N={p['N']}, ν={p['nu']}, T={p['T']}, dt={p['dt']} — истинные NSE…", flush=True)
    true_nse = run_case(solver, uh0.copy(), p["nu"], p["T"], p["dt"], rotate=False)
    print(f"    I_BKM={true_nse['I_BKM']:.4f}, max‖ω‖∞={true_nse['omega_max_abs']:.4f}, "
          f"{true_nse['wall_seconds']} c", flush=True)

    print("    NSE с непрерывным b-поворотом…", flush=True)
    b_rot = run_case(solver, uh0.copy(), p["nu"], p["T"], p["dt"], rotate=True)
    print(f"    I_BKM={b_rot['I_BKM']:.4f}, max‖ω‖∞={b_rot['omega_max_abs']:.4f}, "
          f"{b_rot['wall_seconds']} c", flush=True)

    out = {
        "level": "L5",
        "params": {**p, "theta_b_deg": float_theta_b_deg(),
                   "cumulative_rotation_deg": float_theta_b_deg() * p["T"],
                   "protocol": "continuous: per-step angle dt·θ_b; exact Rodrigues form; axis from "
                               "smoothed vorticity (k ≤ N/6), quadratic weight (|ω|/max)²; Leray "
                               "projection; 2/3-правило через 3/2-паддинг"},
        "true_nse": true_nse,
        "b_rotation": b_rot,
        "factor_BKM": true_nse["I_BKM"] / b_rot["I_BKM"],
        "factor_omega_max": true_nse["omega_max_abs"] / b_rot["omega_max_abs"],
        "max_dE_per_rotation": b_rot["max_dE_per_rotation"],
        "note": "исторический фактор 3,5× относится к недоразрешённой конфигурации N=24 "
                "(глава 11 монографии); здесь зафиксированный воспроизводимый протокол",
    }
    RESULTS_DIR.mkdir(exist_ok=True)
    (RESULTS_DIR / "l5_nse_3d_bkm.json").write_text(
        json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
    # ok = целостность численного эксперимента (стабильность, без инжекции),
    # а не «помог ли поворот»: фактор — измерение, печатается и сохраняется как есть
    import math as _m
    ok = (_m.isfinite(out["factor_BKM"]) and _m.isfinite(out["factor_omega_max"])
          and out["max_dE_per_rotation"] < 1e-4
          and true_nse["omega_max_abs"] < 10.0 and b_rot["omega_max_abs"] < 10.0)
    print(f"L5: {'PASS' if ok else 'FAIL'} | фактор BKM {out['factor_BKM']:.4f}×, "
          f"фактор ω_max {out['factor_omega_max']:.4f}×, max|ΔE| {out['max_dE_per_rotation']:.2e}")
    return ok


if __name__ == "__main__":
    sys.exit(0 if run() else 1)
