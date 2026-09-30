#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
p6_taylor_green_bkm.py — P6: 3D Taylor-Green pseudo-spectral run and the
Beale-Kato-Majda envelope under the universal rotation theta_b.

Setup (declared):
  * Periodic box [0, 2pi)^3, N = 32^3, de-aliasing 2/3 rule.
  * Taylor-Green initial condition:
      u = (sin x cos y cos z, -cos x sin y cos z, 0)
  * Viscosity nu = 0.01, dt = 2e-3, T_end = 5, RK2 (midpoint) + spectral
    projection each stage.
  * Run A (baseline): TG initial condition.
    Run B (b-rotation): the SAME field rotated by theta_b = arcsin(b)
    about the z-axis at every point (energy identical by construction).
  * BKM envelope: I(t) = integral_0^t max|omega| dt' (Beale-Kato-Majda
    criterion integrand); factor = I_B(T)/I_A(T).
  * |dE| = max_t |E_b(t) - E_A(t)|, E = 0.5 <u,u>  (trajectory separation).

Output: results/p6_taylor_green_bkm.json  (all numbers from THIS run)
"""
import json
import math
import os

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
RES = os.path.join(os.path.dirname(HERE), "results")

B = 1.0 / (4.0 * math.pi + 2.0 * math.sqrt(3))
THETA_B = math.asin(B)

N = 32
NU = 0.01
DT = 2e-3
T_END = 5.0


def tg_ic():
    x = y = z = (np.arange(N) + 0.5) * (2 * math.pi / N)
    X, Y, Z = np.meshgrid(x, y, z, indexing="ij")
    u = np.stack([np.sin(X) * np.cos(Y) * np.cos(Z),
                  -np.cos(X) * np.sin(Y) * np.cos(Z),
                  np.zeros_like(X)])
    return u


def rotate_z(u, theta):
    c, s = math.cos(theta), math.sin(theta)
    out = np.empty_like(u)
    out[0] = c * u[0] - s * u[1]
    out[1] = s * u[0] + c * u[1]
    out[2] = u[2]
    return out


def wavenumbers():
    k = np.fft.fftfreq(N, d=1.0 / N)
    KX, KY, KZ = np.meshgrid(k, k, k, indexing="ij")
    K2 = KX**2 + KY**2 + KZ**2
    K2[0, 0, 0] = 1.0  # avoid /0 in projection; mean mode handled separately
    # 2/3 dealiasing mask
    kmax = N // 3
    mask = (np.abs(KX) <= kmax) & (np.abs(KY) <= kmax) & (np.abs(KZ) <= kmax)
    return KX, KY, KZ, K2, mask


def rhs(u_hat, KX, KY, KZ, K2, mask):
    """Pseudo-spectral right-hand side: -P[(u.grad)u] + nu*lap u."""
    u = np.stack([np.real(np.fft.ifftn(u_hat[i])) for i in range(3)])
    w_hat = [1j * (KY * u_hat[2] - KZ * u_hat[1]),
             1j * (KZ * u_hat[0] - KX * u_hat[2]),
             1j * (KX * u_hat[1] - KY * u_hat[0])]
    w = np.stack([np.real(np.fft.ifftn(w_hat[i])) for i in range(3)])
    # (u.grad)u = curl(u x w)   [incompressible identity]
    cross = [u[1] * w[2] - u[2] * w[1],
             u[2] * w[0] - u[0] * w[2],
             u[0] * w[1] - u[1] * w[0]]
    c_hat = [np.fft.fftn(cross[i]) for i in range(3)]
    nl = [1j * (KY * c_hat[2] - KZ * c_hat[1]),
          1j * (KZ * c_hat[0] - KX * c_hat[2]),
          1j * (KX * c_hat[1] - KY * c_hat[0])]
    for i in range(3):
        nl[i] *= -1.0
    # pressure projection P = I - k k / k^2
    div = (KX * nl[0] + KY * nl[1] + KZ * nl[2]) / K2
    for i in range(3):
        Karr = (KX, KY, KZ)[i]
        nl[i] = nl[i] - Karr * div
    out = [nl[i] + (-NU * K2) * u_hat[i] for i in range(3)]
    out = [o * mask for o in out]
    return out


def run(u0_real):
    KX, KY, KZ, K2, mask = wavenumbers()
    u_hat = [np.fft.fftn(u0_real[i]) * mask for i in range(3)]
    # project initial field
    div = (KX * u_hat[0] + KY * u_hat[1] + KZ * u_hat[2]) / K2
    for i, Karr in enumerate((KX, KY, KZ)):
        u_hat[i] = (u_hat[i] - Karr * div) * mask

    n_steps = int(round(T_END / DT))
    t_log, om_log, E_log = [0.0], [None], [None]
    w_hat = [1j * (KY * u_hat[2] - KZ * u_hat[1]),
             1j * (KZ * u_hat[0] - KX * u_hat[2]),
             1j * (KX * u_hat[1] - KY * u_hat[0])]
    wmax = max(float(np.max(np.abs(np.real(np.fft.ifftn(w_hat[i]))))) for i in range(3))
    u0 = [np.real(np.fft.ifftn(u_hat[i])) for i in range(3)]
    E = 0.5 * float(np.sum(u0[0]**2 + u0[1]**2 + u0[2]**2)) / N**3
    t_log, om_log, E_log = [0.0], [wmax], [E]

    for step in range(1, n_steps + 1):
        k1 = rhs(u_hat, KX, KY, KZ, K2, mask)
        u_mid = [u_hat[i] + 0.5 * DT * k1[i] for i in range(3)]
        k2 = rhs(u_mid, KX, KY, KZ, K2, mask)
        for i in range(3):
            u_hat[i] = (u_hat[i] + DT * k2[i]) * mask
        # diagnostics
        w_hat = [1j * (KY * u_hat[2] - KZ * u_hat[1]),
                 1j * (KZ * u_hat[0] - KX * u_hat[2]),
                 1j * (KX * u_hat[1] - KY * u_hat[0])]
        wmax = max(float(np.max(np.abs(np.real(np.fft.ifftn(w_hat[i]))))) for i in range(3))
        u_now = [np.real(np.fft.ifftn(u_hat[i])) for i in range(3)]
        E = 0.5 * float(np.sum(u_now[0]**2 + u_now[1]**2 + u_now[2]**2)) / N**3
        t_log.append(step * DT)
        om_log.append(wmax)
        E_log.append(E)
        if step % 500 == 0:
            print(f"    step {step:5d}  t={step*DT:.2f}  max|w|={wmax:.4f}  E={E:.6f}")
    return np.array(t_log), np.array(om_log), np.array(E_log)


def main():
    os.makedirs(RES, exist_ok=True)
    print("=== P6: Taylor-Green 3D, N=32, nu=0.01, baseline ===")
    t, om0, E0 = run(tg_ic())
    print("=== P6: b-rotated initial condition (theta_b about z) ===")
    t2, omb, Eb = run(rotate_z(tg_ic(), THETA_B))

    I0 = float(np.trapezoid(om0, t))
    Ib = float(np.trapezoid(omb, t2))
    factor = Ib / I0
    dE = float(np.max(np.abs(Eb - E0)))
    print(f"I_BKM baseline   = {I0:.4f}")
    print(f"I_BKM b-rotated  = {Ib:.4f}")
    print(f"factor Ib/I0     = {factor:.6f}")
    print(f"max|E_b - E_0|   = {dE:.3e}")

    out = {
        "module": "p6_taylor_green_bkm",
        "run_date": "2026-09-16",
        "parameters": {"N": N, "nu": NU, "dt": DT, "T_end": T_END,
                       "method": "pseudo-spectral RK2, 2/3 dealias, projection",
                       "theta_b_deg": math.degrees(THETA_B)},
        "I_BKM_baseline": I0,
        "I_BKM_b_rotated": Ib,
        "factor_b_over_baseline": factor,
        "max_abs_dE": dE,
        "E_final_baseline": float(E0[-1]),
        "E_final_b": float(Eb[-1]),
        "max_omega_baseline": float(om0.max()),
        "max_omega_b": float(omb.max()),
        "diag": {"t": t.tolist(), "max_omega_baseline": om0.tolist(),
                 "max_omega_b": omb.tolist(), "E_baseline": E0.tolist(),
                 "E_b": Eb.tolist()},
    }
    path = os.path.join(RES, "p6_taylor_green_bkm.json")
    with open(path, "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=2)
    print("saved:", path)


if __name__ == "__main__":
    main()
