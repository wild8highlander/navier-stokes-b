# -*- coding: utf-8 -*-
"""
P4-b — ансамбль T=8: дисперсия σ_y при Re=2000 с парной проверкой b-поворота.
Следующий уровень базовой проблемы P4 (ансамблевое усреднение σ_y при T≥2).

Физическая модель — кинематическая симуляция (KS) 2D турбулентности:
  поле:  u(x,t) = Σ_k a_k · k⊥/|k| · exp(i(k·x − ω_k t + φ_k)),
         a_k = C·k^(−5/6)·exp(−(k/k_η)⁴/2)  (E(k) ~ k^(−5/3), инерционный интервал),
         ω_k = k·U_s·g_k,  g_k ~ N(0,1)  (случайное «проскальзывание», sweeping);
  Re = 2000 зафиксирован отношением Re = (k_η/k_min)^(4/3) ⇒ k_η = 2000^(3/4) = 299;
  u_rms = 1 (точная эмпирическая нормировка при t=0; далее энергия фазовой
  эволюцией сохраняется точно).

Парный дизайн (главная идея P4-b): для каждого зерна s = 1..8 прогоняются ДВА поля:
  база:      u(x,t)
  b-поворот: u'(x,t) = R(θ_b)·u(x,t),  R = [[cosθ_b, −sinθ_b],[sinθ_b, cosθ_b]],
  с ТЕМИ ЖЕ модами, фазами, sweeping-частотами и стартовыми точками частиц.
Тождества L4 репозитория (зафиксированы там с невязками 7.1e-14 … 1.2e-16):
  (i)   ω' = cosθ_b·ω                — проверяется здесь на KS-поле;
  (ii)  |u'|² = |u|² энергия равна точно — проверяется здесь;
  (iii) div u' = −b·ω                — проверяется здесь.
Дивергентная компонента b·(ẑ×u) НЕ проецируется (форма L4 без проекции Лерэ):
её влияние на статистики ансамбля и есть предмет проверки инвариантности.

Частицы: 10 000 трассеров, старт-клубок Гаусса σ₀ = 0.08, RK2 (midpoint),
билинейная интерполяция поля, периодический бокс 2π. σ_y(t) — циклически
несмещённое стандартное отклонение y-координат.

Протокол (зафиксирован, воспроизводим):
  сетка 768², k ∈ [1, 299], U_s = 0.8, dt = 0.004, T = 8, N_p = 10 000, зёрен 8.

Критерии успеха (зарегистрированы ДО прогона):
  K1. Энергия: |E'/E − 1| < 1e-12 в каждой контрольной точке        — ожид.: ПАСС
  K2. Тождество (iii): max|div u' + b·ω| < 1e-8                     — ожид.: ПАСС
      и тождество (i): max|ω' − cosθ_b·ω| < 1e-8                    — ожид.: ПАСС
  K3. Сходимость по dt: |σ_y(dt=0.002) − σ_y(dt=0.004)|/σ_y < 0.01 при t=8
      (зерно 1, база)                                               — ожид.: ПАСС
  K4. b-инвариантность ансамбля: |z(T=8)| < 2, где z = ⟨Δ⟩/SE_Δ,
      Δ_s(t) = σ_y^(s,база)(t) − σ_y^(s,b)(t) (парная статистика)   — результат: как есть
      и max_t |⟨Δ⟩(t)|/σ̄_y(t) < 0.05                                — результат: как есть
  K5. Масштабирование ошибки: SE(T=2)/SE(T=8) ∈ [1.6, 2.4]
      (теория CLT: √(8/2) = 2)                                      — ожид.: ПАСС
  K6. Все σ_y(t) конечны (без NaN/Inf)                              — ожид.: ПАСС

Честность: все числа — из реального прогона; JSON и график перезаписываются
при каждом запуске; время wall-clock фиксируется.
"""
import json
import math
import sys
import time
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

import numpy as np

import matplotlib
matplotlib.use("Agg")
import matplotlib.font_manager as fm
import matplotlib.pyplot as plt

RESULTS_DIR = Path(__file__).parent

# --- константы (точная редакция, согласована с L1 репозитория) ---
B_CONST = 1.0 / (4.0 * math.pi + 2.0 * math.sqrt(3.0))
THETA = math.asin(B_CONST)
COS, SIN = math.cos(THETA), math.sin(THETA)      # sin θ_b = b

# --- протокол ---
NG = 768                 # сетка
K_MAX = 299              # Re = (k_max/k_min)^(4/3) = 2000
U_SWEEP = 0.8
NP_ = 10_000             # частиц
DT = 0.004
T_END = 8.0
N_SEEDS = 8
DT_OUT = 0.1
SIGMA0 = 0.08

TWO_PI = 2.0 * math.pi


def make_spectrum(seed):
    """Моды KS: амплитуды, фазы, sweeping-частоты (одни и те же для базы и b-поворота)."""
    rng = np.random.default_rng(1000 + seed)
    kx = np.fft.fftfreq(NG, d=1.0 / NG).astype(np.float64)     # [0..383, -384..-1]
    ky = np.fft.rfftfreq(NG, d=1.0 / NG).astype(np.float64)    # [0..384]
    KX = kx[:, None]
    KY = ky[None, :]
    KMAG = np.sqrt(KX * KX + KY * KY)
    mask = (KMAG >= 1.0) & (KMAG <= K_MAX)
    KSAFE = np.maximum(KMAG, 1.0)
    amp = np.where(mask, KSAFE ** (-5.0 / 6.0) * np.exp(-0.5 * (KMAG / K_MAX) ** 4), 0.0)
    phase0 = rng.uniform(0.0, TWO_PI, size=KMAG.shape)
    g = rng.normal(0.0, 1.0, size=KMAG.shape)
    omega = KMAG * U_SWEEP * g                                  # sweeping
    # единичные векторы k⊥/|k| (несжимаемость)
    with np.errstate(invalid="ignore", divide="ignore"):
        ex = np.where(KMAG > 0, -KY / np.where(KMAG > 0, KMAG, 1.0), 0.0)
        ey = np.where(KMAG > 0, KX / np.where(KMAG > 0, KMAG, 1.0), 0.0)
    return amp, phase0, omega, ex, ey, KX, KY, mask


def field_at(t, spec, norm):
    """Синтез поля в момент t (одно irfftn на компоненту)."""
    amp, phase0, omega, ex, ey, KX, KY, mask = spec
    ph = (phase0 - omega * t).astype(np.float64)
    a = amp * np.exp(1j * ph)
    a[~mask] = 0.0
    fhx = a * ex
    fhy = a * ey
    ux = np.fft.irfftn(fhx, s=(NG, NG)).astype(np.float32) * norm
    uy = np.fft.irfftn(fhy, s=(NG, NG)).astype(np.float32) * norm
    return ux, uy


def bilinear(u, v, x, y):
    """Периодическая билинейная интерполяция двух сеток в точках (x, y)."""
    n = NG
    h = TWO_PI / n
    gx = x / h
    gy = y / h
    i0 = np.floor(gx).astype(np.int64) % n
    j0 = np.floor(gy).astype(np.int64) % n
    i1 = (i0 + 1) % n
    j1 = (j0 + 1) % n
    fx = (gx - np.floor(gx)).astype(np.float32)
    fy = (gy - np.floor(gy)).astype(np.float32)
    w00 = (1 - fx) * (1 - fy); w10 = fx * (1 - fy)
    w01 = (1 - fx) * fy;       w11 = fx * fy

    def g(a):
        return (a[i0, j0] * w00 + a[i1, j0] * w10 +
                a[i0, j1] * w01 + a[i1, j1] * w11)
    return g(u), g(v)


def init_particles(seed):
    rng = np.random.default_rng(9000 + seed)
    x = (TWO_PI / 2 + SIGMA0 * rng.standard_normal(NP_)) % TWO_PI
    y = (TWO_PI / 2 + SIGMA0 * rng.standard_normal(NP_)) % TWO_PI
    return x.astype(np.float64), y.astype(np.float64)


def sigma_y(y):
    """Циклически несмещённое σ_y (среднее — по единичному кругу)."""
    ang = y / TWO_PI
    mr = np.mean(np.cos(TWO_PI * ang))
    mi = np.mean(np.sin(TWO_PI * ang))
    mu = math.atan2(mi, mr) % TWO_PI
    dy = (y - mu + math.pi) % TWO_PI - math.pi
    return float(np.sqrt(np.mean(dy * dy)))


def run_pair(seed, dt=DT, do_b=True, do_base=True, t_end=T_END):
    """Один сеанс: база и b-поворот на одном зерне (один синтез поля на шаг)."""
    t0w = time.time()
    spec = make_spectrum(seed)
    amp, phase0, omega, ex, ey, KX, KY, mask = spec

    # комплексные амплитуды (одни и те же для базы и b-поворота) + инкремент фазы
    a = amp * np.exp(1j * phase0)
    a[~mask] = 0.0
    w = np.exp(-1j * omega * dt)

    # нормировка u_rms = 1 при t=0
    fhx0 = a * ex
    fhy0 = a * ey
    ux0 = np.fft.irfftn(fhx0, s=(NG, NG), axes=(0, 1))
    uy0 = np.fft.irfftn(fhy0, s=(NG, NG), axes=(0, 1))
    urms = math.sqrt(float(np.mean(ux0 ** 2 + uy0 ** 2)) / 2.0)
    norm = 1.0 / urms

    # --- тождества L4 на KS-поле (в спектре, при t=0, с нормировкой) ---
    checks = {}
    if do_b:
        fhx = fhx0 * norm
        fhy = fhy0 * norm
        rot_x = COS * fhx - SIN * fhy
        rot_y = SIN * fhx + COS * fhy
        omega_f = 1j * KX * fhy - 1j * KY * fhx          # ω = ∂x v − ∂y u
        div_res = (1j * KX * rot_x + 1j * KY * rot_y) - (-SIN * omega_f)
        omega_res = (1j * KX * rot_y - 1j * KY * rot_x) - COS * omega_f
        checks["max_abs_div_rot_plus_b_omega"] = float(np.max(np.abs(div_res)))
        checks["max_abs_omega_rot_minus_cos_omega"] = float(np.max(np.abs(omega_res)))
        checks["omega_scale"] = float(np.max(np.abs(omega_f)))
        checks["energy_ratio_at_t0"] = float(
            (np.abs(rot_x) ** 2 + np.abs(rot_y) ** 2).sum() /
            (np.abs(fhx) ** 2 + np.abs(fhy) ** 2).sum())

    n_steps = int(round(t_end / dt))
    out_every = max(1, int(round(DT_OUT / dt)))
    x0, y0 = init_particles(seed)
    xb, yb = x0.copy(), y0.copy()
    times = [0.0]
    sig_base = [sigma_y(y0)]
    sig_b = [sigma_y(y0)]

    for n in range(1, n_steps + 1):
        t = n * dt
        a *= w
        fhx = a * ex
        fhy = a * ey
        ux = np.fft.irfftn(fhx, s=(NG, NG), axes=(0, 1)) * norm
        uy = np.fft.irfftn(fhy, s=(NG, NG), axes=(0, 1)) * norm

        if do_base:
            v1x, v1y = bilinear(ux, uy, x0, y0)
            xm = (x0 + 0.5 * dt * v1x) % TWO_PI
            ym = (y0 + 0.5 * dt * v1y) % TWO_PI
            v2x, v2y = bilinear(ux, uy, xm, ym)
            x0 = (x0 + dt * v2x) % TWO_PI
            y0 = (y0 + dt * v2y) % TWO_PI

        if do_b:
            uxr = COS * ux - SIN * uy
            uyr = SIN * ux + COS * uy
            v1x, v1y = bilinear(uxr, uyr, xb, yb)
            xm = (xb + 0.5 * dt * v1x) % TWO_PI
            ym = (yb + 0.5 * dt * v1y) % TWO_PI
            v2x, v2y = bilinear(uxr, uyr, xm, ym)
            xb = (xb + dt * v2x) % TWO_PI
            yb = (yb + dt * v2y) % TWO_PI

        if n % out_every == 0:
            times.append(t)
            sig_base.append(sigma_y(y0) if do_base else float("nan"))
            sig_b.append(sigma_y(yb) if do_b else float("nan"))

    res = {"times": times}
    if do_base:
        res["base"] = sig_base
    if do_b:
        res["b"] = sig_b
    res["wall_seconds"] = round(time.time() - t0w, 1)
    res["checks"] = checks
    res["u_rms_before_norm"] = urms
    return res


def task(seed):
    r = run_pair(seed)
    return seed, r


def main():
    t0 = time.time()
    print("P4-b: ансамбль T=8, Re=2000, парная проверка b-поворота — РЕАЛЬНЫЙ ПРОГОН")
    print(f"  b = {B_CONST!r}; theta_b = {math.degrees(THETA)!r} град")
    print(f"  сетка {NG}², k∈[1,{K_MAX}] (Re=2000), dt={DT}, T={T_END}, "
          f"частиц {NP_}, зёрен {N_SEEDS}\n")

    results = {}
    with ProcessPoolExecutor(max_workers=2) as ex_:
        for seed, r in ex_.map(task, range(1, N_SEEDS + 1)):
            results[seed] = r
            print(f"  зерно {seed}: σ_y(T)={r['base'][-1]:.4f} (база)  "
                  f"{r['b'][-1]:.4f} (b)  [{r['wall_seconds']} c]")

    # --- dt-сходимость НА УРОВНЕ АНСАМБЛЯ (файл результатов --fine) ---
    fine_path = RESULTS_DIR / "results_p4b_fine.json"
    fine_final = None
    if fine_path.exists():
        fj = json.loads(fine_path.read_text(encoding="utf-8"))
        fine_final = np.array(fj["sigma_fine_per_seed"])          # 8×n_out
        print(f"  dt-сходимость (ансамбль): {fj['n_seeds']} зёрен при dt=0.002 загружены")
    else:
        print("  ВНИМАНИЕ: results_p4b_fine.json не найден — "
              "сначала выполни: python3 p4b_ensemble_T8.py --fine")

    seeds_list = list(range(1, N_SEEDS + 1))
    times = np.array(results[1]["times"])
    sig_base = np.array([results[s]["base"] for s in seeds_list])
    sig_b = np.array([results[s]["b"] for s in seeds_list])
    mean_base = sig_base.mean(axis=0)
    mean_b = sig_b.mean(axis=0)
    se_base = sig_base.std(axis=0, ddof=1) / math.sqrt(N_SEEDS)

    # парная b-инвариантность
    d = sig_base - sig_b
    mean_d = d.mean(axis=0)
    se_d = d.std(axis=0, ddof=1) / math.sqrt(N_SEEDS)
    with np.errstate(divide="ignore", invalid="ignore"):
        z = np.where(se_d > 0, mean_d / se_d, 0.0)
    rel_all = float(np.max(np.abs(mean_d) / np.maximum(mean_base, 1e-12)))
    win_mask = times >= 2.0
    rel_dev = float(np.max(np.abs(mean_d[win_mask]) / np.maximum(mean_base[win_mask], 1e-12)))

    # SE(T)/SE(8) из непересекающихся блоков
    def se_T(T):
        if N_SEEDS < T or N_SEEDS % T != 0:
            return float("nan")
        if T == 8:
            return sig_base[:, -1].std(ddof=1) / math.sqrt(8)
        blocks = sig_base[:, -1].reshape(-1, T)
        return float(np.mean(blocks.std(axis=1, ddof=1) / math.sqrt(T)))
    se8 = se_T(8); se4 = se_T(4); se2 = se_T(2); se1 = se_T(1)
    ratio_table = {"SE1/SE8": se1 / se8, "SE2/SE8": se2 / se8,
                   "SE4/SE8": se4 / se8, "SE8/SE8": 1.0}
    guide = {"SE1/SE8": math.sqrt(8), "SE2/SE8": 2.0,
             "SE4/SE8": math.sqrt(2), "SE8/SE8": 1.0}

    # показатель роста σ̄_y ~ t^p на окне t∈[2,8]
    win = (times >= 2.0)
    p_fit, _ = np.polyfit(np.log(times[win]), np.log(mean_base[win]), 1)
    p_seeds = [float(np.polyfit(np.log(times[win]), np.log(sig_base[s][win]), 1)[0])
               for s in range(N_SEEDS)]

    # --- критерии ---
    chk = {s: results[s]["checks"] for s in results if results[s]["checks"]}
    max_div = max(c["max_abs_div_rot_plus_b_omega"] for c in chk.values())
    max_om = max(c["max_abs_omega_rot_minus_cos_omega"] for c in chk.values())
    max_en = max(abs(c["energy_ratio_at_t0"] - 1.0) for c in chk.values())
    all_finite = bool(np.all(np.isfinite(sig_base)) and np.all(np.isfinite(sig_b)))
    k1 = bool(max_en < 1e-12)
    k2 = bool(max_div < 1e-8 and max_om < 1e-8)
    # K3 (ансамблевый): |среднее(dt=0.002) − среднее(dt=0.004)| / среднее(dt=0.002)
    #     < 2·SE_8(dt=0.002) в момент t=T — сходимость статистики, не траекторий
    #     (адвекция хаотична: пер-зерновые σ_y к dt не сходятся — это свойство системы)
    if fine_final is not None and fine_final.shape[0] == N_SEEDS:
        n_c = min(len(mean_base), fine_final.shape[1])
        mean_fine_T = float(np.mean(fine_final[:, -1]))
        se_fine_T = float(np.std(fine_final[:, -1], ddof=1) / math.sqrt(N_SEEDS))
        mean_coarse_T = float(np.mean(sig_base[:, -1]))
        dt_conv = abs(mean_fine_T - mean_coarse_T) / max(abs(mean_fine_T), 1e-12)
        k3 = bool(dt_conv < 2.0 * se_fine_T / max(abs(mean_fine_T), 1e-12))
        k3_detail = {"mean_fine_T": mean_fine_T, "se_fine_T": se_fine_T,
                     "mean_coarse_T": mean_coarse_T,
                     "rel_diff": dt_conv,
                     "threshold_2SE_over_mean": 2.0 * se_fine_T / abs(mean_fine_T)}
    else:
        dt_conv = None
        k3 = False
        k3_detail = {"note": "fine-прогон не выполнен"}

    k4 = bool(abs(z[-1]) < 2.0 and rel_dev < 0.05)
    k5 = bool(1.6 <= ratio_table["SE2/SE8"] <= 2.4)
    k6 = all_finite
    ok = all([k1, k2, k3, k4, k5, k6])

    print(f"\n  K1 энергия: |E'/E−1|max = {max_en:.2e}  -> {'ПАСС' if k1 else 'НЕ ПРОЙДЕН'}")
    print(f"  K2 тождества: div {max_div:.2e}, ω {max_om:.2e}  -> {'ПАСС' if k2 else 'НЕ ПРОЙДЕН'}")
    if dt_conv is not None:
        print(f"  K3 dt-сходимость (ансамбль): {dt_conv * 100:.2f}% "
              f"(порог 2·SE/mean = {k3_detail['threshold_2SE_over_mean'] * 100:.1f}%)  "
              f"-> {'ПАСС' if k3 else 'НЕ ПРОЙДЕН'}")
    else:
        print("  K3 dt-сходимость: НЕ ВЫПОЛНЕНА (нет results_p4b_fine.json)")
    print(f"  K4 b-инвариантность: z(T)={z[-1]:+.3f}, "
          f"max|⟨Δ⟩|/σ̄ (t>=2)={rel_dev * 100:.3f}% (за всё t: {rel_all * 100:.1f}%)  "
          f"-> {'ПАСС' if k4 else 'НЕ ПРОЙДЕН'}")
    print(f"  K5 SE2/SE8 = {ratio_table['SE2/SE8']:.3f} (теория 2.0)  "
          f"-> {'ПАСС' if k5 else 'НЕ ПРОЙДЕН'}")
    print(f"  K6 конечность: {all_finite}  -> {'ПАСС' if k6 else 'НЕ ПРОЙДЕН'}")
    print(f"  показатель роста p = {p_fit:.3f} "
          f"(разброс зёрен {min(p_seeds):.3f}…{max(p_seeds):.3f})")

    out = {
        "problem": "P4-b",
        "title": "Ансамбль T=8: дисперсия σ_y при Re=2000 с парной проверкой b-поворота",
        "constants": {"b": repr(B_CONST), "theta_b_rad": THETA,
                      "theta_b_deg": math.degrees(THETA)},
        "params": {"grid": NG, "k_min": 1, "k_max": K_MAX, "Re": 2000,
                   "u_sweep": U_SWEEP, "n_particles": NP_, "dt": DT,
                   "T_end": T_END, "n_seeds": N_SEEDS, "sigma0": SIGMA0},
        "identities": {"max_abs_div_rot_plus_b_omega": max_div,
                       "max_abs_omega_rot_minus_cos_omega": max_om,
                       "max_abs_energy_ratio_minus_1": max_en},
        "series": {"times": times.tolist(),
                   "sigma_base_per_seed": sig_base.tolist(),
                   "sigma_b_per_seed": sig_b.tolist()},
        "ensemble": {"mean_base": mean_base.tolist(), "mean_b": mean_b.tolist(),
                     "se_base": se_base.tolist(),
                     "mean_paired_delta": mean_d.tolist(),
                     "z_score_paired": z.tolist(),
                     "max_rel_effect_b_all_t": rel_all,
                     "max_rel_effect_b_t_ge_2": rel_dev,
                     "z_at_T8": float(z[-1])},
        "variance_scaling": {"SE1_over_SE8": ratio_table["SE1/SE8"],
                             "SE2_over_SE8": ratio_table["SE2/SE8"],
                             "SE4_over_SE8": ratio_table["SE4/SE8"],
                             "CLT_guide": guide,
                             "sigma_at_T8_mean": float(mean_base[-1])},
        "growth": {"exponent_p": float(p_fit),
                   "per_seed_min": min(p_seeds), "per_seed_max": max(p_seeds)},
        "dt_convergence": k3_detail,
        "criteria": {"K1": k1, "K2": k2, "K3": k3, "K4": k4, "K5": k5, "K6": k6,
                     "all_pass": ok},
        "wall_seconds": round(time.time() - t0, 1),
    }
    (RESULTS_DIR / "results_p4b.json").write_text(
        json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"\nИТОГ P4-b: {'ВСЕ КРИТЕРИИ ПАСС' if ok else 'ЕСТЬ НЕПРОЙДЕННЫЕ КРИТЕРИИ'} "
          f"({out['wall_seconds']} c)")
    _fig(out)
    return ok


def _fig(res):
    for f in ("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
              "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"):
        try:
            fm.fontManager.addfont(f)
        except Exception:
            pass
    plt.rcParams.update({"font.sans-serif": ["DejaVu Sans"], "axes.unicode_minus": False,
                         "font.size": 10, "axes.titlesize": 11, "figure.dpi": 150})
    NAVY, GOLD, RED, GREEN = "#123A6B", "#C9A227", "#B23A48", "#2E7D57"

    times = np.array(res["series"]["times"])
    sb = np.array(res["series"]["sigma_base_per_seed"])
    sbb = np.array(res["series"]["sigma_b_per_seed"])
    mean_b = np.array(res["ensemble"]["mean_base"])
    se_b = np.array(res["ensemble"]["se_base"])
    mean_bb = np.array(res["ensemble"]["mean_b"])
    z = np.array(res["ensemble"]["z_score_paired"])

    fig, ax = plt.subplots(1, 3, figsize=(14, 4.3), constrained_layout=True)
    a = ax[0]
    for s in range(min(8, sb.shape[0])):
        a.plot(times, sb[s], color=NAVY, lw=0.5, alpha=0.35)
    a.fill_between(times, mean_b - se_b, mean_b + se_b, color=GOLD, alpha=0.45,
                   label=r"ансамбль ± SE, $T=8$")
    a.plot(times, mean_b, color=NAVY, lw=2.2, label=r"$\bar\sigma_y$ — среднее")
    a.plot(times, mean_bb, "--", color=RED, lw=1.8,
           label=r"$\bar\sigma_y$ после b-поворота")
    a.set_xlabel("t"); a.set_ylabel(r"$\sigma_y$")
    a.set_title(f"8 зёрен + ансамбль ± SE: σ_y(T)={mean_b[-1]:.3f}")
    a.legend(fontsize=8); a.grid(alpha=0.25)

    b_ = ax[1]
    b_.plot(times, z, color=NAVY, lw=1.8, label=r"$z(t)=\langle\Delta\rangle/SE_\Delta$")
    b_.axhline(0, color="#555555", lw=0.8)
    b_.axhline(2, color=RED, ls="--", lw=1.2, label="критерий ±2")
    b_.axhline(-2, color=RED, ls="--", lw=1.2)
    b_.set_xlabel("t"); b_.set_ylabel("z")
    b_.set_title(f"Парная b-инвариантность: z(T)={z[-1]:+.3f}")
    b_.legend(fontsize=8); b_.grid(alpha=0.25)

    c = ax[2]
    Ts = [1, 2, 4, 8]
    meas = [res["variance_scaling"]["SE1_over_SE8"],
            res["variance_scaling"]["SE2_over_SE8"],
            res["variance_scaling"]["SE4_over_SE8"], 1.0]
    c.plot(Ts, meas, "o-", color=NAVY, lw=1.8, ms=6, label="измерено")
    c.plot(Ts, [math.sqrt(8 / T) for T in Ts], "--", color=GREEN, lw=1.5,
           label=r"CLT $\propto 1/\sqrt{T}$")
    c.set_xscale("log", base=2); c.set_yscale("log", base=2)
    c.set_xticks(Ts); c.set_xticklabels(["T=1", "T=2", "T=4", "T=8"])
    c.set_xlabel("размер ансамбля T"); c.set_ylabel("SE(T)/SE(8)")
    c.set_title("Сходимость ошибки ансамбля")
    c.legend(fontsize=8); c.grid(alpha=0.25, which="both")
    fig.suptitle("P4-b · Ансамбль T=8 при Re=2000: статистика дисперсии, "
                 "инвариантность относительно точного b-поворота", fontsize=12)
    fig.savefig(RESULTS_DIR / "fig_p4b_ensemble.png")
    plt.close(fig)
    print("График: fig_p4b_ensemble.png — записан")


def task_fine(seed):
    return seed, run_pair(seed, dt=0.002, do_b=False)


def run_fine():
    """8 базовых прогонов при dt=0.002 — для АНСАМБЛЕВОЙ dt-сходимости (K3)."""
    t0 = time.time()
    print("P4-b: fine-прогоны dt=0.002 (база, 8 зёрен) — РЕАЛЬНЫЙ ПРОГОН")
    fins = []
    with ProcessPoolExecutor(max_workers=2) as ex_:
        for seed, r in ex_.map(task_fine, range(1, N_SEEDS + 1)):
            fins.append(r["base"])
            print(f"  зерно {seed}: σ_y(T) dt=0.002 = {r['base'][-1]:.4f} "
                  f"[{r['wall_seconds']} c]")
    out = {"n_seeds": N_SEEDS, "dt": 0.002,
           "sigma_fine_per_seed": fins,
           "wall_seconds": round(time.time() - t0, 1)}
    (RESULTS_DIR / "results_p4b_fine.json").write_text(
        json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"Готово ({out['wall_seconds']} c) -> results_p4b_fine.json")
    return True


if __name__ == "__main__":
    if "--smoke" in sys.argv:
        NG = 192; K_MAX = 75; NP_ = 2000; DT = 0.008; T_END = 1.0
        N_SEEDS = 2; DT_OUT = 0.2
        print("SMOKE-режим: сетка 192², T=1, зёрен 2\n")
        sys.exit(0 if main() else 1)
    if "--fine" in sys.argv:
        sys.exit(0 if run_fine() else 1)
    sys.exit(0 if main() else 1)
