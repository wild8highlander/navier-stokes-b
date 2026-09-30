# -*- coding: utf-8 -*-
"""
chamber3d.py — ядро 3D-микрофизики камеры Вильсона (P1/P5).

Физическая постановка (СИ, все параметры зафиксированы в JSON результата):
  * Адиабатическое расширение: T1 = T0·(V0/V1)^(γ−1), P1 = P0·(V0/V1)^γ, γ = 1.4;
  * Давление насыщенного пара — формула Магнуса (вода);
  * Пересыщение S0 = e1/p_sat(T1), e1 = RH0·p_sat(T0)·(V0/V1);
  * Ионная дорожка: прямолинейный отрезок ионизированных узлов (α-частица);
  * Нуклеация на ионах при S > S_crit_ion, рост капли диффузионный:
      dR/dt = α_g·(S_cell − 1)/R,  α_g = D_v·ρ_vs/ρ_l;
  * Седиментация: Стокс v_s = (2/9)(ρ_l − ρ_a)gR²/μ_a;
  * Поле скорости: дивергентно-свободный шум (остаток расширения),
    вязкое затухание exp(−ν k² dt) + НЕПРЕРЫВНЫЙ b-ПОВОРОТ по протоколу L5:
    угол за шаг dt·θ_b, форма Родригеса u' = u∥ + √(1−sin²φ)·u⊥ + sinφ·(ω̂×u⊥),
    ось — сглаженный вихрь (k ≤ N/6, квадратичный вес), проекция Лерэ.
  Это ровно тот протокол, который верифицирован на L2/L4/L5.

Запуск:  python3 p1_3d_microphysics.py        # P1 (односторонняя связь)
         python3 p5_droplet_feedback.py       # P5 (двусторонняя связь)
"""
import math
import numpy as np

# ---- константа b (точная форма монографии) ----
B = 1.0 / (4.0 * math.pi + 2.0 * math.sqrt(3.0))
THETA_B = math.asin(B)                    # рад
THETA_B_DEG = math.degrees(THETA_B)       # 3.5765013142837210°

# ---- физика камеры (СИ) ----
T0 = 293.15                # K, начальная температура
P0 = 101325.0              # Па
RH0 = 0.95                 # начальная относительная влажность пара
GAMMA = 1.4                # показатель адиабаты воздуха
EXPANSION = 1.25           # V1/V0
L_DOM = 0.10               # м, размер камеры
N_GRID = 64                # сетка N³
D_V = 2.2e-5               # м²/с, коэффициент диффузии пара в воздухе
RHO_L = 1000.0             # кг/м³, вода
MU_A = 1.72e-5             # Па·с, вязкость воздуха
NU_A = 1.33e-5             # м²/с, кинематическая вязкость воздуха (268 K)
G = 9.81                   # м/с²
R_V = 461.5                # Дж/(кг·К), газовая постоянная пара
S_CRIT_ION = 2.5           # порог нуклеации на ионах (диапазон Флетчера 2–3)
R_SEED = 0.5e-6            # м, радиус зародыша после нуклеации


def p_sat_magnus(T):
    """Давление насыщенного пара воды, Па (Магнус, T в K)."""
    tc = T - 273.15
    return 610.94 * math.exp(17.625 * tc / (tc + 243.04))


def expansion_state():
    """Состояние после адиабатического расширения."""
    r = 1.0 / EXPANSION                       # V0/V1
    T1 = T0 * r ** (GAMMA - 1.0)
    P1 = P0 * r ** GAMMA
    e1 = RH0 * p_sat_magnus(T0) * r
    S0 = e1 / p_sat_magnus(T1)
    rho_vs = p_sat_magnus(T1) / (R_V * T1)    # кг/м³ плотность насыщенного пара
    rho_a = 1.204 * (P1 / P0) * (T0 / T1)     # плотность воздуха после расширения
    return {"T1": T1, "P1": P1, "e1": e1, "S0": S0,
            "rho_vs": rho_vs, "rho_a": rho_a}


def alpha_growth(rho_vs):
    """Коэффициент диффузионного роста α_g = D_v·ρ_vs/ρ_l, м²/с."""
    return D_V * rho_vs / RHO_L


def stokes_velocity(R, rho_a):
    """Скорость оседания Стокса, м/с (вниз, −z)."""
    return (2.0 / 9.0) * (RHO_L - rho_a) * G * R * R / MU_A


class ChamberFlow3D:
    """Слабое дивергентно-свободное поле скорости + b-поворот по протоколу L5."""

    def __init__(self, N=N_GRID, L=L_DOM, u_rms=2e-3, seed=42, b_rotation=True):
        self.N, self.L = N, L
        self.b_rotation = b_rotation
        rng = np.random.default_rng(seed)
        kh = np.fft.fftfreq(N, d=1.0 / N)
        # rfft-решётки: kx — полная ось, ky — полная ось, kz — полуось
        self.kx = kh[:, None, None]                       # (N,1,1)
        self.ky = kh[None, :, None]                       # (1,N,1)
        self.kz = kh[None, None, : N // 2 + 1]            # (1,1,N//2+1)
        K2 = self.kx**2 + self.ky**2 + self.kz**2         # (N,N,N//2+1)
        K2[0, 0, 0] = 1.0
        # случайное div-free поле (остаточные движения после расширения)
        uhat = [np.fft.rfftn(rng.normal(size=(N, N, N))) for _ in range(3)]
        # проекция Лерэ в спектральном пространстве
        div = self.kx * uhat[0] + self.ky * uhat[1] + self.kz * uhat[2]
        uh = [uhat[i] - (self.kx if i == 0 else self.ky if i == 1 else self.kz)
              * div / K2 for i in range(3)]
        # нормировка на заданную u_rms
        uu = [np.fft.irfftn(h, s=(N, N, N)) for h in uh]
        cur = math.sqrt(sum(float((a**2).mean()) for a in uu))
        sc = u_rms / cur
        self.kmax_smooth = N / 6.0
        # остаточные движения после расширения — крупномасштабные:
        # обрезаем спектр на k ≤ N/6 (та же полоса, что у оси в протоколе L5),
        # иначе точечный поворот грубого поля даёт большую дивергентную часть
        mask_lo = K2 <= self.kmax_smooth**2
        self.uh = [h * sc * mask_lo for h in uh]
        self.K2 = K2
        self.mask_smooth = K2 <= self.kmax_smooth**2      # (N,N,N//2+1)
        self.last_dE_rot = 0.0     # |ΔE|/E через операцию поворота (протокол L5)
        self._vel_cache = None

    def _norm3(self, u):
        return sum(float((a**2).sum()) for a in u)

    def step(self, dt):
        """Вязкое затухание + непрерывный b-поворот (протокол L5)."""
        self.last_dE_rot = 0.0
        self._vel_cache = None
        # 1) вязкое затухание exp(−ν k² dt)
        damp = np.exp(-NU_A * self.K2 * dt)
        uh = [h * damp for h in self.uh]
        # 2) b-поворот: угол φ = dt·θ_b вокруг локальной оси сглаженного вихря
        if self.b_rotation:
            phi = dt * THETA_B
            c, s = math.cos(phi), math.sin(phi)
            u = [np.fft.irfftn(h, s=(self.N,) * 3) for h in uh]
            E_pre = self._norm3(u)
            # сглаженный вихрь: обнуляем моды k > N/6 ДО обратного преобразования
            wh = [1j * (self.ky * uh[2] - self.kz * uh[1]),
                  1j * (self.kz * uh[0] - self.kx * uh[2]),
                  1j * (self.kx * uh[1] - self.ky * uh[0])]
            m = self.mask_smooth
            w = [np.fft.irfftn(h * m, s=(self.N,) * 3) for h in wh]
            wnorm2 = w[0]**2 + w[1]**2 + w[2]**2
            wnorm = np.sqrt(wnorm2); wnorm[wnorm == 0] = 1.0
            q = (wnorm / wnorm.max()) ** 2          # квадратичный вес (L5)
            wx, wy, wz = (wi / wnorm for wi in w)
            # u∥ = (u·ω̂)ω̂; u⊥ = u − u∥; u' = c·u⊥ + s·(ω̂×u⊥) + u∥
            upar = (u[0]*wx + u[1]*wy + u[2]*wz)
            upx, upy, upz = u[0] - upar*wx, u[1] - upar*wy, u[2] - upar*wz
            crx = wy*upz - wz*upy
            cry = wz*upx - wx*upz
            crz = wx*upy - wy*upx
            u2 = [c*upx + s*crx + upar*wx,
                  c*upy + s*cry + upar*wy,
                  c*upz + s*crz + upar*wz]
            # вес поворота q (как в L5: ось от взвешенного вихря)
            u2 = [u2[i] * (1.0 - q) + u[i] * q for i in range(3)]
            uh = [np.fft.rfftn(a) for a in u2]
            # повторная проекция Лерэ
            div = self.kx * uh[0] + self.ky * uh[1] + self.kz * uh[2]
            uh = [uh[i] - (self.kx if i == 0 else self.ky if i == 1 else self.kz)
                  * div / self.K2 for i in range(3)]
            # |ΔE| строго через операцию поворота (как в L5: остаток проекции);
            # ЗНАКОВЫЙ критерий: инжекция — только положительное изменение
            u_post = [np.fft.irfftn(h, s=(self.N,) * 3) for h in uh]
            E_post = self._norm3(u_post)
            self.last_dE_rot = (E_post - E_pre) / E_pre
            self._vel_cache = u_post
        else:
            self._vel_cache = [np.fft.irfftn(h, s=(self.N,) * 3) for h in uh]
        self.uh = uh

    def velocity(self):
        if self._vel_cache is None:
            self._vel_cache = [np.fft.irfftn(h, s=(self.N,) * 3) for h in self.uh]
        return self._vel_cache

    def u_rms_now(self):
        u = self.velocity()
        return math.sqrt(sum(float((a**2).mean()) for a in u))


def trilinear_interp(u, v, w, X, Y, Z, N, L):
    """Трилинейная интерполяция полей в лагранжевых точках (период. по осям)."""
    pos = [X, Y, Z]
    out = []
    for field in (u, v, w):
        idx = [p / L * N for p in pos]
        i0 = [np.floor(t).astype(np.int64) % N for t in idx]
        fr = [t - np.floor(t) for t in idx]
        i1 = [(a + 1) % N for a in i0]
        acc = np.zeros_like(fr[0])
        for dx_ in (0, 1):
            wx_ = fr[0] if dx_ else 1 - fr[0]
            for dy_ in (0, 1):
                wy_ = fr[1] if dy_ else 1 - fr[1]
                for dz_ in (0, 1):
                    wz_ = fr[2] if dz_ else 1 - fr[2]
                    acc += (wx_ * wy_ * wz_ *
                            field[i0[0] if dx_ == 0 else i1[0],
                                  i0[1] if dy_ == 0 else i1[1],
                                  i0[2] if dz_ == 0 else i1[2]])
        out.append(acc)
    return out


def ion_track_positions(N, L, n_sites=None):
    """Узлы ионной дорожки: слегка наклонённый отрезок через камеру."""
    if n_sites is None:
        n_sites = N - 8
    t = np.linspace(0.05, 0.95, n_sites)
    x = t * L
    y = (0.55 - 0.10 * t) * L
    z = 0.5 * L + 0.02 * np.sin(2 * math.pi * t) * L  # лёгкая кривизна трека
    return x, y, z
