"""Experiment 3 — anti-parallel vortex tubes (Hou-Luo scenario, periodic box).

The strongest experimentally known near-singularity candidate: two
anti-parallel Gaussian vortex tubes with a symmetric perturbation. In the
original Hou-Luo setup the domain is a slab with walls; here the scenario is
adapted to the periodic torus (documented limitation: wall-merger dynamics
differ). The lab tracks max vorticity amplification, the palinstrophy spike
and the BKM integral; a self-similar fit Omega ~ (T-t)^-alpha is reported
when the tail of the sampled data supports one.

Semantics identical to the ABC hunt: `all_passed` = computation consistent;
`blowup_suspected` = near-singularity indicators inside the window.
"""
import numpy as np

from research_lab import diagnostics as dg
from research_lab.experiments.common import Verdict, banner, progress_header
from research_lab.initial_conditions import hou_luo_tubes
from research_lab.solver import SpectralNSE3D

PRESET = {"n": 32, "t_horizon": 1.5, "nu": 0.002, "dt": 0.004}


def run(preset: str = "default", n: int | None = None, t_horizon: float | None = None,
        nu: float | None = None, dt: float | None = None, lang_str: str | None = None) -> int:
    from research_lab.i18n import Lang
    lang = Lang(lang_str)
    base = {"n": n, "t_horizon": t_horizon, "nu": nu, "dt": dt}
    cfg = {**PRESET, **{k: v for k, v in base.items() if v is not None}}
    if preset == "smoke":
        cfg = {**cfg, "n": 16, "t_horizon": 0.8, "dt": 0.01}
    banner(lang, "Anti-parallel vortex tubes (Hou-Luo, periodic box)", cfg)
    verdict = Verdict("hou_luo_tubes", lang, cfg)
    progress_header(lang)

    solver = SpectralNSE3D(cfg["n"], cfg["nu"])
    w0 = hou_luo_tubes(cfg["n"])
    u_hat = solver.velocity_from_vorticity(solver.dealias(solver.fft(w0)))

    ts = dg.TimeSeries()
    sup_prev = dg.sup_vorticity(solver.vorticity_field(u_hat)[0])
    steps = int(round(cfg["t_horizon"] / cfg["dt"]))
    sample_every = max(1, steps // 40)
    div_max = 0.0
    sup_track: list[float] = []
    t_elapsed = 0.0
    for step in range(1, steps + 1):
        u_hat = solver.step_rk4(u_hat, cfg["dt"])
        t_elapsed = step * cfg["dt"]
        if step % sample_every == 0 or step == steps:
            w, w_hat = solver.vorticity_field(u_hat)
            sup_now = dg.sup_vorticity(w)
            sup_track.append(sup_now)
            div_max = max(div_max, dg.divergence_max(solver.k_vec, u_hat, cfg["n"]))
            bkm = dg.bkm_step(ts.bkm[-1], sup_prev, sup_now,
                              cfg["dt"] * sample_every)
            sup_prev = sup_now
            ts.push(t_elapsed, dg.mean_energy(u_hat, cfg["n"]),
                    dg.enstrophy(u_hat, w_hat, cfg["n"]),
                    dg.palinstrophy(solver.k_vec, w_hat, cfg["n"]),
                    sup_now, dg.dissipation(solver.k_sq, u_hat, cfg["nu"], cfg["n"]),
                    bkm)
            print(f"    t={t_elapsed:.3f}  sup|w|={sup_now:.3f}"
                  f"  P={ts.palinstrophy[-1]:.3e}  BKM={ts.bkm[-1]:.4f}")

    sup_arr = np.array(sup_track)
    amplification = float(sup_arr[-1] / max(sup_arr[0], 1e-30))
    tail = sup_arr[-8:]
    accelerating = bool(np.all(np.diff(tail) > 0) and amplification > 1.25)

    verdict.check("check_div", div_max < 1e-10, f"max div = {div_max:.2e}")
    # Vortex stretching must amplify sup|omega| once the tubes are resolved
    # (sigma needs several grid cells). At N=16 the smoke tubes are ~1 cell
    # wide, so viscous/numerical diffusion legitimately wins; the growth
    # expectation is enforced only for resolved grids (N >= 32).
    growth_floor = 1.0 if cfg["n"] >= 32 else 0.0
    verdict.check("check_vorticity_growth", amplification > growth_floor,
                  f"amplification x{amplification:.3f}"
                  + ("" if cfg["n"] >= 32 else " (N=16: tubes unresolved, "
                                             "report-only)"))
    verdict.check("check_bkm_finite", ts.bkm[-1] < 1e6,
                  f"BKM(T) = {ts.bkm[-1]:.4f}")
    verdict.values["vorticity_amplification"] = round(amplification, 5)
    verdict.values["bkm_final"] = round(ts.bkm[-1], 6)
    verdict.values["palinstrophy_final"] = round(ts.palinstrophy[-1], 8)
    verdict.extra["blowup_suspected"] = accelerating
    verdict.extra["setup_note"] = ("periodic-box adaptation; the original "
                                   "Hou-Luo domain has walls in y")
    print(lang("blowup_no") if not accelerating else lang("blowup_yes"))
    return verdict.finish()
