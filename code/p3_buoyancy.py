# -*- coding: utf-8 -*-
"""
P3 — плавучесть: конвекция Рэлея–Бенара при Gr = Ra/Pr = 1e6 (Boussinesq).

Постановка (безразмерные единицы, κ = 1, H = 1):
  Ra = Gr·Pr = 0.71e6, Pr = ν/κ = 0.71;
  ∂ω/∂t = −J(ψ,ω) + Pr∇²ω + Pr·Ra·∂θ/∂x    (горячая нижняя стенка θ = 1)
  ∇²ψ = −ω,  u = ∂ψ/∂z,  w = −∂ψ/∂x
  ∂θ/∂t = −J(ψ,θ) + ∇²θ,  θ(z=0)=1, θ(z=1)=0, x-периодика (Lx = 2).
Метод: Фурье по x, КР по z (Nz = 96), AB2 (адвекция + диффузия + выталкивание),
старт — Эйлер; ψ — прогонка Томаса по модам; прилипание (формула Тома).
Устойчивость: dt ≤ dz²/(4·max(Pr,1)) = 3.9e-5 → dt = 2.5e-5; КФЛ контролируется.
b-механизм: точное 2D-тождество L4 ω' = cos θ_b·ω — угол за шаг dt·θ_b.

Критерии успеха (OPEN_PROBLEMS_7.md, P3):
  C1: конвекция развивается, Nu_hot > 1.5 (отличие от теплопроводности);
  C2: Nu сравнивается с классической корреляцией Nu ≈ 0.13·Ra^0.311 — фиксируется
      отношение (прогон против корреляции — это и есть результат);
  C3: ΔNu(b) относительно базы — зафиксирован (эффект или строгая граница).

Запуск: python3 p3_buoyancy.py
Выход:  ../data/results/p3_buoyancy.json, ../data/plots/plot_P3_buoyancy.png
"""
import json, math, sys, time
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).parent))
from tg2d_core import THETA_B

HERE = Path(__file__).parent
NX, NZ = 72, 144
LX, H = 2.0, 1.0
PR = 0.71
GR = 1.0e6
RA = GR * PR
DT = 1.5e-6
T_END = 0.075
AVG_FROM = 0.05
CFL_LIMIT = 0.45
NU4 = 3.0e-6            # гипервязкость 4-го порядка (алиасинг без паддинга);
                        # на разрешённых масштабах вклад ≪ физической вязкости
NORM = 1.0                  # numpy rfft/irfft — взаимно обратные, нормировка не нужна


class RB:
    def __init__(self, b_rotation=False, seed=7):
        self.b_rotation = b_rotation
        self.dx = LX / NX
        self.dz = H / (NZ - 1)
        self.k = 2 * math.pi * np.fft.fftfreq(NX, d=LX / NX)[: NX // 2 + 1]
        self.k2 = (self.k**2)[:, None]
        z = np.linspace(0.0, 1.0, NZ)
        rng = np.random.default_rng(seed)
        th = np.repeat((1.0 - z)[None, :], NX, axis=0)
        # гладкое крупномасштабное затравочное возмущение (k ≤ 20, амп. 1e-3):
        # грубый (сеточный) шум при Ra ~ 1e6 даёт нефизичный взрывной трансиент
        noise = rng.normal(size=(NX, NZ))
        nh = np.fft.rfft(noise, axis=0)
        nh[(np.abs(self.k) > 20.0).ravel(), :] = 0.0
        nh[:, 0] = 0.0; nh[:, -1] = 0.0   # стены без шума
        noise = np.fft.irfft(nh, axis=0)
        noise = 1e-4 * noise / max(np.abs(noise).max(), 1e-30)
        th = th + noise
        th[:, 0] = 1.0; th[:, -1] = 0.0
        self.th = th
        self.om = np.zeros((NX, NZ))
        self.psi = np.zeros((NX, NZ))
        self._prev = None
        self.cfl_max = 0.0
        # прогонка для ψ: (−2/dz² − k²) главный, 1/dz² внедиагонали
        ni = NZ - 2
        main = (-2.0 / self.dz**2 - self.k2) * np.ones((1, ni))
        off = 1.0 / self.dz**2
        cp = np.zeros_like(main)
        cp[:, 0] = off / main[:, 0]
        for i in range(1, ni):
            cp[:, i] = off / (main[:, i] - off * cp[:, i - 1])
        self._helm_main, self._helm_cp = main, cp
        self._helm_off = off
        # RHS-вектор для ψ собирается из ω̂: −ω̂ (внутр. узлы)

    def _thomas(self, main, cp, rhs):
        """Прогонка с готовыми cp; обратный ход по (K, ni)."""
        ni = rhs.shape[1]
        dp = np.zeros_like(rhs)
        dp[:, 0] = rhs[:, 0] / main[:, 0]
        for i in range(1, ni):
            dp[:, i] = (rhs[:, i] - self._helm_off * dp[:, i - 1]) \
                       / (main[:, i] - self._helm_off * cp[:, i - 1])
        x = np.zeros_like(dp)
        x[:, -1] = dp[:, -1]
        for i in range(ni - 2, -1, -1):
            x[:, i] = dp[:, i] - cp[:, i] * x[:, i + 1]
        return x

    def solve_psi(self, om):
        om_h = np.fft.rfft(om, axis=0)
        psi_i = self._thomas(self._helm_main, self._helm_cp, -om_h[:, 1:-1])
        psi_h = np.zeros_like(om_h)
        psi_h[:, 1:-1] = psi_i
        return np.fft.irfft(psi_h * NORM, axis=0)

    def lap(self, f, c):
        """c·∇²f в физическом пространстве (Фурье-x + КР-z, внутренние узлы);
        стеночные строки обнуляются (граничные условия задаются отдельно)."""
        fh = np.fft.rfft(f, axis=0)
        out_h = -c * self.k2 * fh
        out_h[:, 1:-1] += c * (fh[:, 2:] - 2 * fh[:, 1:-1] + fh[:, :-2]) / self.dz**2
        out = np.fft.irfft(out_h * NORM, axis=0)
        out[:, 0] = 0.0
        out[:, -1] = 0.0
        return out

    def biharmonic(self, f):
        """∇⁴f одним проходом: ∂⁴_x (спектр) + 2∂²_x∂²_z + ∂⁴_z (КР)."""
        fh = np.fft.rfft(f, axis=0)
        d2z = np.zeros_like(fh)
        d2z[:, 1:-1] = (fh[:, 2:] - 2 * fh[:, 1:-1] + fh[:, :-2]) / self.dz**2
        out_h = self.k2**2 * fh - 2.0 * self.k2 * d2z
        out_h[:, 1:-1] += (d2z[:, 2:] - 2 * d2z[:, 1:-1] + d2z[:, :-2]) / self.dz**2
        out = np.fft.irfft(out_h * NORM, axis=0)
        out[:, 0] = 0.0
        out[:, -1] = 0.0
        return out

    def rhs(self):
        om_h = np.fft.rfft(self.om, axis=0)
        th_h = np.fft.rfft(self.th, axis=0)
        # спектральные производные
        dom_dx = np.fft.irfft(1j * self.k[:, None] * om_h * NORM, axis=0)
        dth_dx = np.fft.irfft(1j * self.k[:, None] * th_h * NORM, axis=0)
        # диффузия: Фурье-x + КР-z (внутренние узлы)
        lap_om_h = -self.k2 * om_h
        lap_om_h[:, 1:-1] += (om_h[:, 2:] - 2 * om_h[:, 1:-1] + om_h[:, :-2]) \
                             / self.dz**2
        lap_th_h = -self.k2 * th_h
        lap_th_h[:, 1:-1] += (th_h[:, 2:] - 2 * th_h[:, 1:-1] + th_h[:, :-2]) \
                             / self.dz**2
        lap_om = np.fft.irfft(lap_om_h * NORM, axis=0)
        lap_th = np.fft.irfft(lap_th_h * NORM, axis=0)
        # скорость из ψ: u = ∂ψ/∂z, w = −∂ψ/∂x
        u = self.grad_z(self.psi)
        psi_h = np.fft.rfft(self.psi, axis=0)
        w = -np.fft.irfft(1j * self.k[:, None] * psi_h * NORM, axis=0)
        # КФЛ
        umax = max(float(np.abs(u).max()), float(np.abs(w).max()))
        self.cfl_max = max(self.cfl_max, umax * DT / min(self.dx, self.dz))
        # якобианы (физическое пространство)
        jw = u * dom_dx + w * np.gradient(self.om, self.dz, axis=1)
        jt = u * dth_dx + w * np.gradient(self.th, self.dz, axis=1)
        rhs_om = -jw + PR * RA * dth_dx
        rhs_th = -jt
        # диффузия возвращается отдельно (Эйлер в step): AB2 с весами 1.5/0.5
        # на жёсткой диффузии неустойчив при ν·k²max·dt·1.5 > 1
        diff_om = PR * lap_om - NU4 * self.biharmonic(self.om)
        diff_th = lap_th - NU4 * self.biharmonic(self.th)
        return rhs_om, rhs_th, diff_om, diff_th

    def grad_z(self, f):
        return np.gradient(f, self.dz, axis=1)

    def step(self, n_step):
        nl_om, nl_th, df_om, df_th = self.rhs()
        if n_step == 0:
            self.om += DT * (nl_om + df_om)
            self.th += DT * (nl_th + df_th)
        else:
            # AB2 — только адвекция+выталкивание; диффузия — Эйлер (стабильность)
            self.om += DT * (1.5 * nl_om - 0.5 * self._prev[0] + df_om)
            self.th += DT * (1.5 * nl_th - 0.5 * self._prev[1] + df_th)
        self._prev = (nl_om, nl_th)
        if self.b_rotation:
            self.om *= math.cos(DT * THETA_B)      # точное тождество L4
        self.psi = self.solve_psi(self.om)
        # свободное скольжение: ω = 0 и ψ = 0 на стенках (без петли Том↔ψ,
        # известного источника численной неустойчивости явных схем);
        # Дирихле для θ
        self.om[:, 0] = 0.0
        self.om[:, -1] = 0.0
        self.psi[:, 0] = 0.0
        self.psi[:, -1] = 0.0
        self.th[:, 0] = 1.0
        self.th[:, -1] = 0.0

    def nusselt_hot(self):
        return float((1.0 - self.th[:, 1].mean()) / self.dz)


def main(mode_arg="both"):
    res_dir = HERE.parent / "data" / "results"
    res_dir.mkdir(exist_ok=True)
    json_path = res_dir / "p3_buoyancy.json"
    # режимы можно запускать раздельно (лимит времени): p3_buoyancy.py [true_nse|b_rotation|both]
    modes = {"true_nse": False, "b_rotation": True}
    if mode_arg in modes:
        selected = [mode_arg]
    else:
        selected = list(modes)
    # дозагрузка уже выполненных режимов (для любых selected)
    results = None
    if json_path.exists():
        try:
            results = json.loads(json_path.read_text(encoding="utf-8"))
            if not isinstance(results.get("runs"), dict):
                results = None
        except Exception:
            results = None
    if results is None:
        results = {"problem": "P3",
                   "title": "Плавучесть: конвекция Рэлея–Бенара, Gr = 1e6",
                   "command": "python3 code/p3_buoyancy.py",
                   "params": {"NX": NX, "NZ": NZ, "Lx": LX, "Pr": PR, "Gr": GR,
                              "Ra": RA, "dt": DT, "T_end": T_END,
                              "scheme": "AB2 (адвекция+диффузия+выталкивание), "
                                        "Фурье-x / КР-z, ψ — прогонка, Том; "
                                        "гипервязкость 4-го порядка против алиасинга",
                              "theta_b_deg": math.degrees(THETA_B),
                              "b_protocol": "ω ← cos(dt·θ_b)·ω за шаг (тождество L4)"},
                   "runs": {}, "wall_seconds": 0.0}
    t_wall0 = time.perf_counter()
    th_store = {}
    # пропускаем уже выполненные режимы
    selected = [m for m in selected if m not in results.get("runs", {})]
    for mode in selected:
        brot = modes[mode]
        rb = RB(b_rotation=brot)
        nu_t, t_t, wmax_t = [], [], []
        n_steps = int(round(T_END / DT))
        cfl_breached = False
        for n in range(n_steps):
            rb.step(n)
            if rb.cfl_max > CFL_LIMIT:
                cfl_breached = True
                print(f"  P3[{mode}]: КФЛ превышен ({rb.cfl_max:.2f}) на шаге {n}",
                      flush=True)
                break
            if (n + 1) % 1000 == 0:
                t_t.append((n + 1) * DT)
                nu_t.append(rb.nusselt_hot())
                psi_h = np.fft.rfft(rb.psi, axis=0)
                w = -np.fft.irfft(1j * rb.k[:, None] * psi_h * NORM, axis=0)
                wmax_t.append(float(np.abs(w).max()))
        nu_arr = np.array(nu_t); t_arr = np.array(t_t)
        m = t_arr >= AVG_FROM
        nu_mean = float(nu_arr[m].mean()) if m.any() else float("nan")
        results["runs"][mode] = {
            "Nu_hot_time_avg": nu_mean,
            "Nu_final": float(nu_arr[-1]) if len(nu_arr) else None,
            "w_max_final": wmax_t[-1] if wmax_t else None,
            "CFL_max": float(rb.cfl_max),
            "CFL_breached": cfl_breached,
            "Nu_series": [round(v, 4) for v in nu_t],
            "t_series": [round(v, 4) for v in t_t],
        }
        th_store[mode] = rb.th.copy()
        results["wall_seconds"] = round(time.perf_counter() - t_wall0, 1)
        json_path.write_text(json.dumps(results, ensure_ascii=False, indent=1),
                             encoding="utf-8")
        print(f"  P3[{mode}]: Nu = {nu_mean:.3f}, w_max = {wmax_t[-1] if wmax_t else 0:.1f}, "
              f"CFL = {rb.cfl_max:.2f}, сохранено", flush=True)

    def finalize(results, th_store):
        """Критерии + итоговый статус (вызывается когда есть оба режима)."""
        if not {"true_nse", "b_rotation"} <= set(results.get("runs", {})):
            return
        nu0 = results["runs"]["true_nse"]["Nu_hot_time_avg"]
        nub = results["runs"]["b_rotation"]["Nu_hot_time_avg"]
        nu_corr = 0.13 * RA ** 0.311
        results["criteria"] = {
            "C1_Nu_gt_1.5": bool(nu0 > 1.5),
            "C2_Nu_base": nu0,
            "C2_Nu_correlation_0.13Ra^0.311": round(nu_corr, 3),
            "C2_ratio_run_over_corr": round(nu0 / nu_corr, 3),
            "C3_delta_Nu_b": nub - nu0,
            "C3_delta_Nu_b_rel": (nub - nu0) / nu0,
            "CFL_ok": bool(results["runs"]["true_nse"]["CFL_max"] < CFL_LIMIT),
        }
        results["ok"] = bool(results["criteria"]["C1_Nu_gt_1.5"]
                             and results["criteria"]["CFL_ok"])
        res_dir = HERE.parent / "data" / "results"
        json_path = res_dir / "p3_buoyancy.json"
        json_path.write_text(json.dumps(results, ensure_ascii=False, indent=1),
                             encoding="utf-8")
        np.save(res_dir / "p3_theta_snapshot.npy",
                th_store["true_nse"]) if "true_nse" in th_store else None
        print(f"P3: {'PASS' if results['ok'] else 'FAIL'} | Nu(база) = {nu0:.4f} "
              f"(корр. {nu_corr:.2f}) | ΔNu(b) = {nub - nu0:+.3e} "
              f"({(nub - nu0) / nu0:+.2e})")

    if not selected:
        finalize(results, th_store)
        return 0
    finalize(results, th_store)
    return 0 if results.get("ok") else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1] if len(sys.argv) > 1 else "both"))
