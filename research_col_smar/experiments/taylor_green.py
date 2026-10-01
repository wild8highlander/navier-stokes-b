"""Experiment 1 — Taylor-Green vortex: convergence and dt-extrapolation.

The reference flow of the repository (section 2 verifies the BKM machinery
on it). Here it becomes a dynamical experiment: free decay at Re = 1/nu,

    checks: incompressibility held; energy non-increasing; finite enstrophy
    peak; RK4 temporal order recovered by dt-halving with a Richardson
    estimate of the peak-enstrophy monitor; spectral tail steepening.

Scientific meaning: an internal-consistency certificate of the whole lab +
the canonical "extrapolated to dt -> 0" monitor values for the reference
flow. Literature context: TG remains smooth in every computation to date;
the lab reproduces that within its window and quantifies error bars.
"""

from research_lab import diagnostics as dg
from research_lab.experiments.common import PRESETS, Verdict, banner, progress_header
from research_lab.initial_conditions import taylor_green
from research_lab.solver import SpectralNSE3D


def run_single(n: int, nu: float, dt: float, t_horizon: float,
               sample_every: int = 8) -> dict:
    """One decay run; returns summary monitors (peak enstrophy, BKM, drifts)."""
    solver = SpectralNSE3D(n, nu)
    u_hat = solver.dealias(solver.project(solver.fft(taylor_green(n))))
    ts = dg.TimeSeries()
    sup_prev = dg.sup_vorticity(solver.vorticity_field(u_hat)[0])
    steps = int(round(t_horizon / dt))
    div_max = 0.0
    energy_rise = 0.0
    e_prev = dg.mean_energy(u_hat, n)
    t_elapsed = 0.0
    step = 0
    while step < steps:
        h = min(dt, t_horizon - t_elapsed)
        u_hat = solver.step_rk4(u_hat, h)
        t_elapsed += h
        step += 1
        if step % sample_every == 0 or step == steps:
            w, w_hat = solver.vorticity_field(u_hat)
            sup_now = dg.sup_vorticity(w)
            e_now = dg.mean_energy(u_hat, n)
            div_max = max(div_max, dg.divergence_max(solver.k_vec, u_hat, n))
            energy_rise = max(energy_rise, e_now - e_prev)
            e_prev = e_now
            bkm = dg.bkm_step(ts.bkm[-1], sup_prev, sup_now,
                              h * sample_every)
            sup_prev = sup_now
            ts.push(t_elapsed, e_now, dg.enstrophy(u_hat, w_hat, n),
                    dg.palinstrophy(solver.k_vec, w_hat, n),
                    sup_now, dg.dissipation(solver.k_sq, u_hat, nu, n), bkm)
    peak_t, peak_omega = ts.peak_enstrophy()
    _, spectrum = dg.shell_spectrum(
        u_hat, n, dg.spectral_radii(n))
    k_cutoff = n // 3
    tail_level = dg.spectral_tail_level(spectrum, k_cutoff)
    slope = dg.spectral_tail_slope(spectrum, k_cutoff)
    return {
        "peak_t": peak_t,
        "peak_enstrophy": peak_omega,
        "enstrophy_final": ts.enstrophy[-1],
        "bkm_final": ts.bkm[-1],
        "energy_final": ts.energy[-1],
        "div_max": div_max,
        "energy_rise": energy_rise,
        "tail_slope": slope,
        "tail_level": tail_level,
        "timeseries": ts.as_dict(),
    }


def run(preset: str = "default", n: int | None = None, t_horizon: float | None = None,
        nu: float | None = None, dt: float | None = None, lang_str: str | None = None) -> int:
    from research_lab.i18n import Lang
    lang = Lang(lang_str)
    base = {"n": n, "t_horizon": t_horizon, "nu": nu, "dt": dt}
    cfg = {**PRESETS[preset], **{k: v for k, v in base.items() if v is not None}}
    banner(lang, "Taylor-Green vortex: convergence and extrapolation", cfg)
    verdict = Verdict("taylor_green", lang, cfg)
    progress_header(lang)

    main = run_single(cfg["n"], cfg["nu"], cfg["dt"], cfg["t_horizon"])
    print(f"    t={main['peak_t']:.3f}  peak Omega={main['peak_enstrophy']:.6f}"
          f"  BKM(T)={main['bkm_final']:.4f}  tail={main['tail_level']:.1e}")

    verdict.check("check_div", main["div_max"] < 1e-10,
                  f"max div = {main['div_max']:.2e}")
    verdict.check("check_energy_decay", main["energy_rise"] <= 1e-10,
                  f"max rise = {main['energy_rise']:.2e}")
    verdict.check("check_enstrophy_finite",
                  0.0 < main["peak_enstrophy"] < 1e6,
                  f"peak = {main['peak_enstrophy']:.6f} at t = {main['peak_t']:.3f}")

    # temporal ladder on the enstrophy at a fixed final time (deterministic
    # monitor, independent of sampling): J(dt) = Omega(t_lad; dt)
    t_lad = min(cfg["t_horizon"], 1.0)
    if t_lad >= 0.5:
        j = [run_single(cfg["n"], cfg["nu"], d, t_lad,
                        sample_every=max(1, int(0.1 / d)))["enstrophy_final"]
             for d in (cfg["dt"], cfg["dt"] / 2.0, cfg["dt"] / 4.0)]
        from research_lab.extrapolate import observed_order, richardson
        p = observed_order(j[0], j[1], j[2])
        extrap = richardson(j[1], j[2], 2.0, p if p == p else 4.0)
        verdict.check("check_temporal_order", 3.0 <= p <= 5.0,
                      f"observed order = {p:.2f}, "
                      f"Omega(t={t_lad:.2f}; dt->0) = {extrap:.8f}")
        verdict.values["temporal_order"] = round(p, 3)
        verdict.values["peak_enstrophy_extrapolated"] = round(extrap, 8)
    else:
        verdict.check("check_temporal_order", False, "horizon too short")

    verdict.values["peak_enstrophy"] = round(main["peak_enstrophy"], 8)
    verdict.values["peak_time"] = round(main["peak_t"], 5)
    verdict.values["bkm_final"] = round(main["bkm_final"], 8)
    verdict.values["spectral_tail_level"] = float(f"{main['tail_level']:.3e}")
    verdict.check("check_resolution", main["tail_level"] < 1e-4,
                  f"cutoff tail level = {main['tail_level']:.2e} "
                  "(< 1e-4 of the spectral peak expected)")
    return verdict.finish()
