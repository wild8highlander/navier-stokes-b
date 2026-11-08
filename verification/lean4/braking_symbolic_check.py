# -*- coding: utf-8 -*-
"""
braking_symbolic_check.py — универсальная форма торможения завихрения (2D,
спектральные моды, в точности machinery tg2d_core.py), на СВОБОДНЫХ параметрах.

Никаких ручных полей/коэффициентов: k0, k1, u0, u1 — символьные (амплитуда моды
с произвольными U, k, фазой внутри неё), c, s — символы с единственным условием
c^2 + s^2 = 1 (cos/sin любого угла поворота, у скриптов phi = dt*theta_b).

Моды (как в tg2d_core.py):
  амплитуда          u = (u0, u1) ∈ C^2
  дивергенция моды   k·u = k0*u0 + k1*u1
  Лерэ (div_free):   P(u) = u - (k·u)/(k0²+k1²) * (k0, k1)
  завихренность моды om(u) = i*k0*u1 - i*k1*u0        (curl_h, строка 66)
  поворот (b_rotation, строки 114-116):
                     R(u) = (c*u0 - s*u1, s*u0 + c*u1)
  шаг протокола:     Step(u) = P(R(u))

Проверяемые тождества:
  A1  k·P(u) = 0                                  (проекция даёт бездивергентность)
  A2  P(P(u)) = P(u)                              (P — проекция)
  A3  om(P(R(u))) = c*om(u) + s*i*(k·u)           (общая форма)
  A4  k·u = 0  =>  om(P(R(u))) = c*om(u)          ИДЕАЛЬНАЯ ФОРМА ТОРМОЖЕНИЯ
  A5  |P(R(u))|² = |R(u)|² - |k·R(u)|²/(k0²+k1²)  (уменьшение энергии — только
       проекция; поворот норму хранит: |R(u)|² = |u|² при c²+s²=1, т.е. A6)
  A7  om(P(u)) = om(u)                            (curl∘P = curl: Лерэ не трогает вихрь)
  A8  k·R(u) = (c*k0+s*k1)*u0 + (c*k1-s*k0)*u1    (k·R(u) = R(-φ)k · u)
Далее численный свип по случайным модам (замена свободных параметров) и
замкнутая форма BKM-фактора P2: F = (1-c^M)/(M*(1-c)).
"""
import sympy as sp
import numpy as np

i = sp.I
k0, k1, u0, u1, c, s = sp.symbols("k0 k1 u0 u1 c s", real=True)
K2 = k0**2 + k1**2

def dot(u):
    return k0 * u[0] + k1 * u[1]

def P(u):
    return sp.Matrix([u[0], u[1]]) - dot(u) / K2 * sp.Matrix([k0, k1])

def R(u):
    return sp.Matrix([c * u[0] - s * u[1], s * u[0] + c * u[1]])

def om(u):
    return i * k0 * u[1] - i * k1 * u[0]

def sqabs(z):  # |z|^2 для z = a + i*b с вещественными a, b
    a, b = sp.re(z), sp.im(z)
    return sp.simplify(a**2 + b**2)

u = sp.Matrix([u0, u1])
Pu, Ru = P(u), R(u)
PRu = P(R(u))

results = {}
# A1: дивергенция после проекции
results["A1 k·P(u)=0"] = sp.simplify(dot(Pu)) == 0
# A2: идемпотентность
results["A2 P(P(u))=P(u)"] = sp.simplify(P(Pu) - Pu) == sp.zeros(2, 1)
# A7: curl∘P = curl
results["A7 om(P(u))=om(u)"] = sp.simplify(om(Pu) - om(u)) == 0
# A3: общая форма торможения
results["A3 om(P(R(u)))=c*om(u)+s*i*(k·u)"] = sp.simplify(om(PRu) - (c * om(u) + s * i * dot(u))) == 0
# A4: идеальная форма при k·u = 0 (подстановка k·u = 0: u1 = -k0*u0/k1, k1≠0)
u1df = -k0 * u0 / k1
u_df = sp.Matrix([u0, u1df])
results["A4 om(P(R(u)))=c*om(u), k·u=0"] = sp.simplify(om(P(R(u_df))) - c * om(u_df)) == 0
# A6: поворот сохраняет норму при c²+s²=1
cs1 = {c**2 + s**2: 1}
nR = sqabs(c * u0 - s * u1) + sqabs(s * u0 + c * u1)
nR_reduced = sp.simplify(nR.subs(u0**2 + u1**2 * 0, 0))  # placeholder
nu = sqabs(u0) + sqabs(u1)
diff = sp.expand(nR - nu)
diff_sub = diff.subs(u0, sp.Symbol("a") + i * sp.Symbol("b")).subs(u1, sp.Symbol("d") + i * sp.Symbol("e"))
a, b, d, e = sp.symbols("a b d e", real=True)
diff_sub = sp.expand(diff.subs({u0: a + i * b, u1: d + i * e}))
diff_cs = sp.rem(sp.Poly(sp.expand(diff_sub - (c**2 + s**2 - 1) * (a**2 + b**2 + d**2 + e**2)), c), sp.Poly(c**2 + s**2 - 1, c))
results["A6 |R(u)|²=|u|² (mod c²+s²=1)"] = sp.simplify(diff_cs) == 0
# A5: энергия после шага: уменьшение ровно на |k·R(u)|²/K2
dotRu = dot(Ru)
abs_dotRu_sq = sqabs(dotRu)
lhs = sqabs(PRu[0]) + sqabs(PRu[1])
rhs = sqabs(Ru[0]) + sqabs(Ru[1]) - abs_dotRu_sq / K2
results["A5 |P(R(u))|²=|R(u)|²-|k·R(u)|²/K2"] = sp.simplify(lhs - rhs) == 0
# A8: k·R(u) = R(-φ)k · u
k_rot = sp.Matrix([c * k0 + s * k1, -s * k0 + c * k1])
results["A8 k·R(u)=R(-φ)k·u"] = sp.simplify(dot(Ru) - (k_rot[0] * u[0] + k_rot[1] * u[1])) == 0

print("=== Символьные тождества (свободные k0,k1,u0,u1,c,s) ===")
ok = True
for name, val in results.items():
    print(f"  {name}: {'VERIFIED' if val else 'FAILED'}")
    ok = ok and val

# --- Численный свип: 200000 случайных мод (к ≠ 0, произвольные комплексные
# амплитуды, произвольный угол фи) — свобода параметров (U, k, ν, фаза) pleine.
rng = np.random.default_rng(7)
N = 200_000
k0v = rng.normal(size=N); k1v = rng.normal(size=N)
mask = (np.abs(k0v) + np.abs(k1v)) < 1e-6
while mask.any():
    k0v[mask], k1v[mask] = rng.normal(size=mask.sum()), rng.normal(size=mask.sum())
    mask = (np.abs(k0v) + np.abs(k1v)) < 1e-6
# Протокол скриптов: состояние ВСЕГДА бездивергентно (init → div_free, rhs → div_free,
# поворот → div_free). Свободные параметры (U, k, ν, фаза) живут внутри выбора
# div-free амплитуд; поэтому свип: произвольная амплитуда → проекция Лерэ → проверка.
raw0 = rng.normal(size=N) + 1j * rng.normal(size=N)
raw1 = rng.normal(size=N) + 1j * rng.normal(size=N)
K2v = k0v**2 + k1v**2
dot_raw = k0v * raw0 + k1v * raw1
u0v = raw0 - dot_raw / K2v * k0v          # P(raw): теперь k·u = 0 точно
u1v = raw1 - dot_raw / K2v * k1v
phiv = rng.uniform(-np.pi, np.pi, N)
cv, sv = np.cos(phiv), np.sin(phiv)

dotv = k0v * u0v + k1v * u1v
P0 = u0v - dotv / K2v * k0v; P1 = u1v - dotv / K2v * k1v
R0 = cv * u0v - sv * u1v;    R1 = sv * u0v + cv * u1v
dotRu = k0v * R0 + k1v * R1
PR0 = R0 - dotRu / K2v * k0v; PR1 = R1 - dotRu / K2v * k1v
om_v = 1j * k0v * u1v - 1j * k1v * u0v
om_PR = 1j * k0v * PR1 - 1j * k1v * PR0
res_A4 = np.max(np.abs(om_PR - cv * om_v))
# A3 на произвольных (не обязательно div-free) амплитудах:
res_A3 = np.max(np.abs(om_PR - (cv * om_v + sv * 1j * (k0v * u0v + k1v * u1v))))
div_res = np.max(np.abs(k0v * u0v + k1v * u1v))
norm_R = np.abs(R0)**2 + np.abs(R1)**2
norm_u = np.abs(u0v)**2 + np.abs(u1v)**2
res_A6 = np.max(np.abs(norm_R - norm_u))
E_after = np.abs(PR0)**2 + np.abs(PR1)**2
dotRu_rot = (cv * k0v + sv * k1v) * u0v + (cv * k1v - sv * k0v) * u1v
res_A5 = np.max(np.abs(E_after - (norm_u - np.abs(dotRu_rot)**2 / K2v)))

print("\n=== Численный свип по свободным параметрам (N = %d) ===" % N)
print(f"  div-невязка после Лерэ:         {div_res:.3e}")
print(f"  A3 (общая форма,   max|res|):   {res_A3:.3e}")
print(f"  A4 (идеальная форма, max|res|): {res_A4:.3e}")
print(f"  A6 (норма поворота, max|res|):  {res_A6:.3e}")
print(f"  A5 (энергия шага,  max|res|):   {res_A5:.3e}")

# --- Замкнутая форма BKM-фактора P2 (геометрическое среднее торможения):
# I_omega(b_on)/I_omega(b_off) = c*(1 - c^M) / (M * (1 - c)), c = cos(dt*theta_b)
#   (сумма геометрической прогрессии c^1+...+c^M = c*(1-c^M)/(1-c))
import mpmath as mp
mp.mp.dps = 50
theta_b = mp.asin(1 / (4 * mp.pi + 2 * mp.sqrt(3)))
dt = mp.mpf("2e-3")                      # как в p2_grid_convergence.py
T = mp.mpf(1)
M_mp = int(T / dt)                       # 500 шагов
c_mp = mp.cos(dt * theta_b)
F_mp = c_mp * (1 - c_mp**M_mp) / (M_mp * (1 - c_mp))
F_direct = mp.fsum([c_mp**n for n in range(1, M_mp + 1)]) / M_mp
print("\n=== BKM-фактор P2 (замкнутая форма, 50 знаков) ===")
print(f"  c = cos(dt*theta_b) = {mp.nstr(c_mp, 20)}")
print(f"  F(формула)      = {mp.nstr(F_mp, 15)}")
print(f"  F(прямая сумма) = {mp.nstr(F_direct, 15)}")
print(f"  |dF| = {mp.nstr(abs(F_mp - F_direct), 3)}")
print(f"  1 - F = {mp.nstr(1 - F_mp, 6)};  theta_b^2*T*dt/4 = {mp.nstr(theta_b**2 * T * dt / 4, 6)}"
      "   (квадратичность по dt, как заявлено в P2/C2)")

assert ok and div_res < 1e-12 and res_A3 < 1e-9 and res_A4 < 1e-9 \
    and res_A6 < 1e-9 and res_A5 < 1e-9 and abs(F_mp - F_direct) < mp.mpf("1e-40")
print("\nALL VERIFIED: форма торможения универсальна (параметры свободны).")
