# -*- coding: utf-8 -*-
"""
L4 — 2D NSE: точные тождества b-поворота и энергетика.

Математическое ядро (проверяется численно с машинной точностью):
  Для дивергентно-свободного u в 2D поворот u' = cos θ_b·u + b·(ẑ×u) (эквивалент
  точной формы u' = u∥ + √(1−b²)·u⊥ + b·(ω̂×u⊥), т.к. в 2D u∥ = 0, ω̂ = ẑ):
    (i)   ω' = cos θ_b · ω   — ТОЧНО (слагаемое b·(ẑ×u) даёт curl = ∇·u = 0);
    (ii)  |u'|² = |u|²        — ТОЧНО (u ⊥ ẑ×u, |ẑ×u| = |u|) — инжекции энергии нет;
    (iii) div u' = −b·ω       — градиентная часть уходит в давление (проекция Лерэ).
Численный эталон: 2D NSE (вихрь Тейлора–Грина), спектральный метод, RK4:
  * энергетическое тождество dE/dt = −2νZ (Z — энстрофия) на сетке;
  * максимум-принцип для ω;
  * непрерывный b-поворот за шаг dt·θ_b: |ΔE| на повороте ~ машинный ноль.
"""
import json, math, sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).parent))
from config import float_theta_b_deg

RESULTS_DIR = Path(__file__).parent / "results"
B = 1 / (4 * math.pi + 2 * math.sqrt(3))
THETA = math.asin(B)
COS, SIN = math.sqrt(1 - B * B), B


def run(N=64, nu=0.001, T=2.0, dt=0.002):
    crit = N // 3                      # 2/3-правило: храним моды |k| ≤ crit
    NP = int(1.5 * N)                  # 3/2-паддинг: перемножение без алиасинга
    k = np.fft.fftfreq(N, d=1.0 / N)   # целые волновые числа (период 2π)
    k0 = k[:, None]                    # производная по оси 0 (полная ось)
    k1 = k[None, : N // 2 + 1]         # производная по оси 1 (rfft, половинная)
    K2 = k0**2 + k1**2
    K2[0, 0] = 1.0
    kP = np.fft.fftfreq(NP, d=1.0 / NP)
    kP0 = kP[:, None]; kP1 = kP[None, : NP // 2 + 1]
    x = np.arange(N) / N * 2 * math.pi
    X, Y = np.meshgrid(x, x, indexing="ij")

    def div_free(fh):
        p = (k0 * fh[0] + k1 * fh[1]) / K2
        return np.stack([fh[0] - k0 * p, fh[1] - k1 * p])

    def trunc(fh):
        m = (np.abs(k0) <= crit) & (np.abs(k1) <= crit)
        return fh * m[None]

    def pad(fh):
        out = np.zeros((2, NP, NP // 2 + 1), complex)
        out[:, :crit+1, :crit+1] = fh[:, :crit+1, :crit+1]
        out[:, -crit:, :crit+1] = fh[:, -crit:, :crit+1]
        out[:, :crit+1, -crit:] = fh[:, :crit+1, -crit:]
        out[:, -crit:, -crit:] = fh[:, -crit:, -crit:]
        return out

    def unpad(nlp):
        out = np.zeros((2, N, N // 2 + 1), complex)
        out[:, :crit+1, :crit+1] = nlp[:, :crit+1, :crit+1]
        out[:, -crit:, :crit+1] = nlp[:, -crit:, :crit+1]
        out[:, :crit+1, -crit:] = nlp[:, :crit+1, -crit:]
        out[:, -crit:, -crit:] = nlp[:, -crit:, -crit:]
        return out

    def curl_h(fh):
        """ω̂ = i k0·v̂ − i k1·û  (ω = ∂₀v − ∂₁u)."""
        return 1j * k0 * fh[1] - 1j * k1 * fh[0]

    def div_h(fh):
        return 1j * k0 * fh[0] + 1j * k1 * fh[1]

    # Тейлор–Грин 2D
    u0 = np.sin(X) * np.cos(Y)
    v0 = -np.cos(X) * np.sin(Y)
    w = np.stack([u0, v0])
    wh = div_free(trunc(np.fft.rfftn(w)))
    om0 = np.fft.irfftn(curl_h(wh), s=(N, N))

    # --- (i): тождество ω' = cos θ_b·ω на 200 случайных div-free полях
    rng = np.random.default_rng(7)
    max_id = 0.0
    for _ in range(200):
        a = rng.normal(size=(N, N)); b2 = rng.normal(size=(N, N))
        fh = div_free(np.fft.rfftn(np.stack([a, b2])))
        om = np.fft.irfftn(curl_h(fh), s=(N, N))
        rot = np.stack([COS * fh[0] - SIN * fh[1], SIN * fh[0] + COS * fh[1]])
        om_r = np.fft.irfftn(curl_h(rot), s=(N, N))
        max_id = max(max_id, float(np.abs(om_r - COS * om).max()))

    # --- (ii): энергия при повороте сохраняется точно (в физическом пространстве)
    E = float((w**2).sum())
    w_rot = np.stack([COS * w[0] - SIN * w[1], SIN * w[0] + COS * w[1]])
    E_rot = float((w_rot**2).sum())
    energy_err = abs(E_rot - E) / E

    # --- (iii): div u' = −b·ω на поле Тейлора–Грина
    rot_tg = np.stack([COS * wh[0] - SIN * wh[1], SIN * wh[0] + COS * wh[1]])
    div_rot = np.fft.irfftn(div_h(rot_tg), s=(N, N))
    div_err = float(np.abs(div_rot - (-SIN * om0)).max())

    # --- NSE 2D: энергетическое тождество + max-принцип + непрерывный поворот
    def rhs(wh):
        # нелинейный член считаем на 3/2-сетке — без алиасинга (2/3-правило)
        fhp = pad(wh)
        uu = np.fft.irfftn(fhp, s=(NP, NP))
        d0 = np.fft.irfftn(1j * kP0 * fhp, s=(NP, NP))
        d1 = np.fft.irfftn(1j * kP1 * fhp, s=(NP, NP))
        adv = np.stack([uu[0] * d0[0] + uu[1] * d1[0],
                        uu[0] * d0[1] + uu[1] * d1[1]])
        return div_free(-unpad(np.fft.rfftn(adv))) - nu * K2 * wh

    n_steps = int(round(T / dt))
    E_prev = float((w[0]**2 + w[1]**2).sum() / 2 / N**2)
    diss_int = 0.0
    Z_prev = None
    om_max0 = float(np.abs(om0).max())
    om_max_viol = 0.0
    phi = dt * THETA
    cph, sph = math.cos(phi), math.sin(phi)
    max_dE_rot = 0.0
    wh_run = wh.copy()
    E_series = []

    for n in range(n_steps):
        k1a = rhs(wh_run)
        k2a = rhs(wh_run + 0.5 * dt * k1a)
        k3a = rhs(wh_run + 0.5 * dt * k2a)
        k4a = rhs(wh_run + dt * k3a)
        wh_run = wh_run + (dt / 6) * (k1a + 2 * k2a + 2 * k3a + k4a)

        om_now = np.fft.irfftn(curl_h(wh_run), s=(N, N))
        om_max_viol = max(om_max_viol, float(np.abs(om_now).max()) - om_max0)
        # энстрофия Z = ½‖ω‖²: трапецией, чтобы ∫2νZ dt был 2-го порядка
        Z_now = 0.5 * float((om_now**2).sum()) / N**2
        if Z_prev is not None:
            diss_int += nu * dt * (Z_prev + Z_now)  # 2ν·½(Zprev+Znow)dt = νdt(Zprev+Znow)
        Z_prev = Z_now

        if (n + 1) % 20 == 0:
            uu = np.fft.irfftn(wh_run, s=(N, N))
            E_series.append(float((uu**2).sum() / 2 / N**2))

        # непрерывный b-поворот
        uu = np.fft.irfftn(wh_run, s=(N, N))
        E_pre = float((uu**2).sum() / 2 / N**2)
        wh_rot = div_free(np.stack([cph * wh_run[0] - sph * wh_run[1],
                                    sph * wh_run[0] + cph * wh_run[1]]))
        uu2 = np.fft.irfftn(wh_rot, s=(N, N))
        E_post = float((uu2**2).sum() / 2 / N**2)
        max_dE_rot = max(max_dE_rot, abs(E_post - E_pre))
        wh_run = wh_rot

    E_final = E_series[-1] if E_series else E_prev
    energy_balance = abs(E_final - E_prev - (-1.0) * (diss_int))  # E(T) ≈ E(0) − ∫2νZ dt

    out = {
        "level": "L4",
        "params": {"N": N, "nu": nu, "T": T, "dt": dt, "theta_b_deg": float_theta_b_deg(),
                   "protocol": "continuous: per-step angle dt·θ_b; 2/3-правило через 3/2-паддинг"},
        "checks": {
            "тождество ω' = cos θ_b·ω, макс. невязка (200 полей)": max_id,
            "энергия при повороте: |E'−E|/E": energy_err,
            "div u' = −b·ω, макс. невязка": div_err,
            "максимум-принцип ω (превышение)": om_max_viol,
            "|ΔE| за один поворот (инжекции нет)": max_dE_rot,
            "энергетический баланс E(T)−E(0)+∫2νZ dt": energy_balance,
        },
        "ok": bool(max_id < 1e-12 and energy_err < 1e-13 and div_err < 1e-10
                   and om_max_viol < 1e-9 and max_dE_rot < 1e-7 and energy_balance < 1e-3),
    }
    RESULTS_DIR.mkdir(exist_ok=True)
    (RESULTS_DIR / "l4_nse_2d.json").write_text(
        json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"L4: {'PASS' if out['ok'] else 'FAIL'} | ω'=cosθ·ω: {max_id:.2e}, "
          f"|ΔE| поворот: {max_dE_rot:.2e}, баланс: {energy_balance:.2e}")
    return out["ok"]


if __name__ == "__main__":
    sys.exit(0 if run() else 1)
