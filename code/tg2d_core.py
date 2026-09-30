# -*- coding: utf-8 -*-
"""
tg2d_core.py — 2D спектральное ядро Навье–Стокса для P2/P4.

В точности machinery верифицированного уровня L4 (verification/python_levels/
l4_nse_2d.py): псевдоспектральный метод, 2/3-правило через 3/2-паддинг,
RK4, проекция Лерэ, непрерывный b-поворот u' = cos φ·u + sin φ·(ẑ×u) в
спектральных коэффициентах (эквивалент точной формы Родригеса в 2D),
угол за шаг φ = dt·θ_b.
"""
import math

import numpy as np

B = 1.0 / (4.0 * math.pi + 2.0 * math.sqrt(3.0))
THETA_B = math.asin(B)
THETA_B_DEG = math.degrees(THETA_B)


class TG2D:
    """Псевдоспектральный решатель 2D NSE на торе [0, 2π]²."""

    def __init__(self, N, nu, dt, b_rotation=False):
        self.N, self.nu, self.dt, self.b_rotation = N, nu, dt, b_rotation
        crit = N // 3
        NP = int(1.5 * N)
        k = np.fft.fftfreq(N, d=1.0 / N)
        self.k0 = k[:, None]
        self.k1 = k[None, : N // 2 + 1]
        self.K2 = self.k0**2 + self.k1**2
        self.K2[0, 0] = 1.0
        kP = np.fft.fftfreq(NP, d=1.0 / NP)
        self.kP0 = kP[:, None]; self.kP1 = kP[None, : NP // 2 + 1]
        self.crit, self.NP = crit, NP
        self.phi = dt * THETA_B
        self.cph, self.sph = math.cos(self.phi), math.sin(self.phi)

    # --- служебные
    def div_free(self, fh):
        p = (self.k0 * fh[0] + self.k1 * fh[1]) / self.K2
        return np.stack([fh[0] - self.k0 * p, fh[1] - self.k1 * p])

    def trunc(self, fh):
        m = (np.abs(self.k0) <= self.crit) & (np.abs(self.k1) <= self.crit)
        return fh * m[None]

    def _pad(self, fh):
        c = self.crit
        out = np.zeros((2, self.NP, self.NP // 2 + 1), complex)
        out[:, :c+1, :c+1] = fh[:, :c+1, :c+1]
        out[:, -c:, :c+1] = fh[:, -c:, :c+1]
        out[:, :c+1, -c:] = fh[:, :c+1, -c:]
        out[:, -c:, -c:] = fh[:, -c:, -c:]
        return out

    def _unpad(self, nlp):
        c = self.crit
        out = np.zeros((2, self.N, self.N // 2 + 1), complex)
        out[:, :c+1, :c+1] = nlp[:, :c+1, :c+1]
        out[:, -c:, :c+1] = nlp[:, -c:, :c+1]
        out[:, :c+1, -c:] = nlp[:, :c+1, -c:]
        out[:, -c:, -c:] = nlp[:, -c:, -c:]
        return out

    def curl_h(self, fh):
        return 1j * self.k0 * fh[1] - 1j * self.k1 * fh[0]

    # --- RHS
    def rhs(self, wh):
        fhp = self._pad(wh)
        uu = np.fft.irfftn(fhp, s=(self.NP, self.NP))
        d0 = np.fft.irfftn(1j * self.kP0 * fhp, s=(self.NP, self.NP))
        d1 = np.fft.irfftn(1j * self.kP1 * fhp, s=(self.NP, self.NP))
        # (u·∇)u, компоненты: [u ∂₀u + v ∂₁u, u ∂₀v + v ∂₁v]
        adv = np.stack([uu[0] * d0[0] + uu[1] * d1[0],
                        uu[0] * d0[1] + uu[1] * d1[1]])
        return self.div_free(-self._unpad(np.fft.rfftn(adv))) - self.nu * self.K2 * wh

    def init_taylor_green(self):
        x = np.arange(self.N) / self.N * 2 * math.pi
        X, Y = np.meshgrid(x, x, indexing="ij")
        u0 = np.sin(X) * np.cos(Y)
        v0 = -np.cos(X) * np.sin(Y)
        wh = self.div_free(self.trunc(np.fft.rfftn(np.stack([u0, v0]))))
        return wh

    def init_decaying_turbulence(self, seed, kp=4.0, u_rms_target=1.0):
        """Затухающая турбулентность: E(k) ∝ k³·exp(−(k/kp)²), случайные фазы."""
        rng = np.random.default_rng(seed)
        a = rng.normal(size=(self.N, self.N))
        b2 = rng.normal(size=(self.N, self.N))
        fh = self.div_free(self.trunc(np.fft.rfftn(np.stack([a, b2]))))
        kk = np.sqrt(self.k0**2 + self.k1**2)
        spec = kk**1.5 * np.exp(-0.5 * (kk / kp)**2)   # ~k^{3/2}·... амплитуда поля
        spec[0, 0] = 0.0
        fh = fh * spec[None]
        uu = np.fft.irfftn(fh, s=(self.N, self.N))
        cur = math.sqrt(float((uu**2).mean()))
        fh = fh * (u_rms_target / cur)
        return fh

    def integrate(self, wh, T, callback=None, cb_every=10):
        """RK4 + непрерывный b-поворот. Возвращает (wh, диагностика)."""
        n_steps = int(round(T / self.dt))
        diag = {"t": [], "Z": [], "E": [], "om_max": [], "I_om": 0.0}
        om_prev = None
        for n in range(n_steps):
            k1a = self.rhs(wh)
            k2a = self.rhs(wh + 0.5 * self.dt * k1a)
            k3a = self.rhs(wh + 0.5 * self.dt * k2a)
            k4a = self.rhs(wh + self.dt * k3a)
            wh = wh + (self.dt / 6) * (k1a + 2 * k2a + 2 * k3a + k4a)
            if self.b_rotation:
                wh = self.div_free(np.stack([
                    self.cph * wh[0] - self.sph * wh[1],
                    self.sph * wh[0] + self.cph * wh[1]]))
            if (n + 1) % cb_every == 0:
                om = np.fft.irfftn(self.curl_h(wh), s=(self.N, self.N))
                uu = np.fft.irfftn(wh, s=(self.N, self.N))
                Z = 0.5 * float((om**2).sum()) / self.N**2
                E = 0.5 * float((uu**2).sum()) / self.N**2
                t_now = (n + 1) * self.dt
                diag["t"].append(t_now); diag["Z"].append(Z)
                diag["E"].append(E); diag["om_max"].append(float(np.abs(om).max()))
                if om_prev is not None:
                    # интеграл ∫‖ω‖∞ dt (BKM-типа, 2D) трапецией
                    diag["I_om"] += 0.5 * (diag["om_max"][-1] + diag["om_max"][-2]) \
                                    * (t_now - diag["t"][-2])
                om_prev = om
                if callback is not None:
                    callback(wh, t_now)
        return wh, diag

    def vorticity(self, wh):
        return np.fft.irfftn(self.curl_h(wh), s=(self.N, self.N))

    def velocity(self, wh):
        return np.fft.irfftn(wh, s=(self.N, self.N))
