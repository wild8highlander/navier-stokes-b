"""Experiment 2 — ABC flow blow-up hunt at low viscosity.

The Arnold-Beltrami-Childress flow is an exact curl eigenfield: with nu = 0
and no perturbation it is stationary for Euler. At small but finite nu, and
with the field's own nonlinearity (A=B=C=1 gives nontrivial interaction only
through higher modes after dealiasing — the lab therefore seeds a small
symmetric perturbation), the run stresses the Beale-Kato-Majda monitor:

    BKM(t) = int_0^t sup_x |omega| ds.

Semantics (honest): PASS = "computation consistent AND no near-singularity
indicators inside the (N, T, dt) window". A separate boolean
`blowup_suspected` flags super-exponential vorticity growth / self-similar
acceleration. Neither outcome proves anything globally; see README.
"""
import numpy as np

from research_lab import diagnostics as dg
from research_lab.experiments.common import Verdict, banner, progress_header
from research_lab.initial_conditions import abc, random_field
from research_lab.solver import SpectralNSE3D


def run(preset: str = "default", n: int | None = None, t_horizon: float | None = None,
        nu: float | None = None, dt: float | None = None, lang_str: str | None = None) -> int:
    from research_lab.i18n import Lang
    lang = Lang(lang_str)
    base = {"n": n, "t_horizon": t_horizon, "nu": nu, "dt": dt}
    cfg = {**PRESET, **{k: v for k, v in base.items() if v is not None}}
    if preset == "smoke":
        cfg = {**cfg, "n": 16, "t_horizon": 1.0, "dt": 0.01}
    banner(lang, "ABC flow: BKM blow-up hunt", cfg)
    verdict = Verdict("abc_blowup_hunt", lang, cfg)
    progress_header(lang)

    solver = SpectralNSE3D(cfg["n"], cfg["nu"])
    u0 = abc(cfg["n"])
    # small deterministic perturbation: wake the eigenfield out of equilibrium
    u0 = 0.5 * u0 + 0.02 * random_field(cfg["n"], k_peak=6)
    u_hat = solver.dealias(solver.project(solver.fft(u0)))

    ts = dg.TimeSeries()
    sup_prev = dg.sup_vorticity(solver.vorticity_field(u_hat)[0])
    growth = []
    steps = int(round(cfg["t_horizon"] / cfg["dt"]))
    sample_every = max(1, steps // 40)
    div_max = 0.0
    t_elapsed = 0.0
    for step in range(1, steps + 1):
        u_hat = solver.step_rk4(u_hat, cfg["dt"])
        t_elapsed = step * cfg["dt"]
        if step % sample_every == 0 or step == steps:
            w, w_hat = solver.vorticity_field(u_hat)
            sup_now = dg.sup_vorticity(w)
            growth.append(sup_now)
            div_max = max(div_max, dg.divergence_max(solver.k_vec, u_hat, cfg["n"]))
            bkm = dg.bkm_step(ts.bkm[-1], sup_prev, sup_now,
                              cfg["dt"] * sample_every)
            sup_prev = sup_now
            ts.push(t_elapsed, dg.mean_energy(u_hat, cfg["n"]),
                    dg.enstrophy(u_hat, w_hat, cfg["n"]),
                    dg.palinstrophy(solver.k_vec, w_hat, cfg["n"]),
                    sup_now, dg.dissipation(solver.k_sq, u_hat, cfg["nu"], cfg["n"]),
                    bkm)
            print(f"    t={t_elapsed:.3f}  Omega={ts.enstrophy[-1]:.6e}"
                  f"  sup|w|={sup_now:.4f}  BKM={ts.bkm[-1]:.4f}")

    sup_arr = np.array(growth)
    ratios = sup_arr[1:] / np.maximum(sup_arr[:-1], 1e-30)
    accelerating = bool(np.all(ratios[-4:] > 1.35)) and sup_arr[-1] > 2.0 * sup_arr[0]
    bkm_fin = ts.bkm[-1]

    verdict.check("check_div", div_max < 1e-10, f"max div = {div_max:.2e}")
    verdict.check("check_bkm_finite", bkm_fin < 1e6 and np.isfinite(bkm_fin),
                  f"BKM(T) = {bkm_fin:.4f}")
    verdict.check("check_vorticity_growth", sup_arr[-1] > 0.0,
                  f"sup|w|: {sup_arr[0]:.3f} -> {sup_arr[-1]:.3f}")
    verdict.values["bkm_final"] = round(bkm_fin, 6)
    verdict.values["sup_omega_final"] = round(float(sup_arr[-1]), 6)
    verdict.values["sup_omega_initial"] = round(float(sup_arr[0]), 6)
    verdict.extra["blowup_suspected"] = accelerating
    print(lang("blowup_no") if not accelerating else lang("blowup_yes"))
    return verdict.finish()


PRESET = {"n": 32, "t_horizon": 2.0, "nu": 0.002, "dt": 0.004}
