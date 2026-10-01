"""Experiment 4 — what the b-rotation can and cannot do (both lab lines).

This experiment implements the scientific audit of the repository's central
mechanism. Three statements are tested on the evolving Taylor-Green field:

  A. FULL rotation symmetry (the mathematically correct form u' = R u(R^-1 x),
     with R a grid-matching quarter turn): this is an exact NSE symmetry, so
     the evolved diagnostics must be IDENTICAL to the unrotated control.
     Expected result: yes, to roundoff — a symmetry changes nothing, it is a
     relabeling, and therefore cannot by itself regularize anything.

  B. POINTWISE b-rotation (the form used across repository sections: rotate
     the velocity vectors without rotating space): energy is preserved
     (isometry, true for ANY rotation, not specific to b) but div u = 0 is
     BROKEN for a generic field. The lab measures the divergence injected
     and then reprojects; the perturbed run is compared against the control
     on BKM / enstrophy monitors.

  C. CONCLUSION (printed and stored in JSON): as a symmetry, the rotation is
     vacuous; as a pointwise kick, it is an uncontrolled perturbation whose
     effect is not regularizing — no detectable reduction of vorticity
     growth within tolerance. This is a falsification line: the mechanism,
     as currently stated in the repository, does not influence the blow-up
     question on the tested window. Any stronger claim requires a modified
     evolution law with a proof, not a relabeling.
"""

from research_lab import diagnostics as dg
from research_lab.constants import b_rotation_matrix, quarter_rotation_matrix
from research_lab.experiments.common import Verdict, banner, progress_header
from research_lab.experiments.taylor_green import run_single
from research_lab.initial_conditions import taylor_green
from research_lab.solver import SpectralNSE3D

PRESET = {"n": 32, "t_horizon": 1.0, "nu": 0.01, "dt": 0.005}


def _evolve_with_kicks(n: int, nu: float, dt: float, t_horizon: float,
                       kick_every: float, kick: str) -> dict:
    """Evolve TG; every kick_every time units apply the chosen rotation.

    Returns post-reprojection divergence (the quality metric) separately
    from the deliberately injected pre-projection divergence.
    """
    solver = SpectralNSE3D(n, nu)
    u_hat = solver.dealias(solver.project(solver.fft(taylor_green(n))))
    rot = quarter_rotation_matrix() if kick == "full" else b_rotation_matrix()
    t_elapsed = 0.0
    next_kick = kick_every
    div_post = dg.divergence_max(solver.k_vec, u_hat, n)
    div_injected = 0.0
    while t_elapsed < t_horizon - 1e-12:
        h = min(dt, t_horizon - t_elapsed, max(next_kick - t_elapsed, 0.0))
        if h > 1e-12:
            u_hat = solver.step_rk4(u_hat, h)
            t_elapsed += h
            div_post = max(div_post,
                           dg.divergence_max(solver.k_vec, u_hat, n))
        if abs(t_elapsed - next_kick) < 1e-9 and t_elapsed < t_horizon - 1e-12:
            if kick == "full":
                u_hat = solver.rotate_full_symmetry(u_hat, rot)
                u_hat = solver.dealias(u_hat)
            else:
                u_hat = solver.rotate_pointwise(u_hat, rot)
                div_injected = max(
                    div_injected, dg.divergence_max(solver.k_vec, u_hat, n))
                u_hat = solver.project(u_hat)
                u_hat = solver.dealias(u_hat)
                div_post = max(div_post,
                               dg.divergence_max(solver.k_vec, u_hat, n))
            next_kick += kick_every
    w, _ = solver.vorticity_field(u_hat)
    return {
        "energy": dg.mean_energy(u_hat, n),
        "sup_omega": dg.sup_vorticity(w),
        "div_post": div_post,
        "div_injected": div_injected,
    }


def run(preset: str = "default", n: int | None = None, t_horizon: float | None = None,
        nu: float | None = None, dt: float | None = None, lang_str: str | None = None) -> int:
    from research_lab.i18n import Lang
    lang = Lang(lang_str)
    base = {"n": n, "t_horizon": t_horizon, "nu": nu, "dt": dt}
    cfg = {**PRESET, **{k: v for k, v in base.items() if v is not None}}
    if preset == "smoke":
        cfg = {**cfg, "n": 16, "t_horizon": 0.5, "dt": 0.01}
    banner(lang, "b-rotation audit: symmetry vs pointwise kick", cfg)
    verdict = Verdict("bcorrection_stress", lang, cfg)
    progress_header(lang)

    # --- A: full symmetry relabeling ------------------------------------
    solver = SpectralNSE3D(cfg["n"], cfg["nu"])
    u_hat = solver.dealias(solver.project(solver.fft(taylor_green(cfg["n"]))))
    u_sym = solver.rotate_full_symmetry(u_hat, quarter_rotation_matrix())
    e0 = dg.mean_energy(u_hat, cfg["n"])
    e_sym = dg.mean_energy(u_sym, cfg["n"])
    div_sym = dg.divergence_max(solver.k_vec, solver.dealias(u_sym), cfg["n"])
    w0 = dg.sup_vorticity(solver.vorticity_field(u_hat)[0])
    ws0 = dg.sup_vorticity(solver.vorticity_field(u_sym)[0])
    verdict.check("check_symmetry",
                  abs(e0 - e_sym) < 1e-12 and div_sym < 1e-10
                  and abs(w0 - ws0) / max(w0, 1e-30) < 1e-10,
                  f"dE = {abs(e0 - e_sym):.2e}, div = {div_sym:.2e}, "
                  f"sup|w| rel diff = {abs(w0 - ws0) / max(w0, 1e-30):.2e}")

    # evolved comparison: control vs rotated (symmetry) after short horizon
    ctrl = run_single(cfg["n"], cfg["nu"], cfg["dt"], cfg["t_horizon"])
    u_hat_sym = solver.rotate_full_symmetry(u_hat, quarter_rotation_matrix())
    t_elapsed = 0.0
    while t_elapsed < cfg["t_horizon"] - 1e-12:
        h = min(cfg["dt"], cfg["t_horizon"] - t_elapsed)
        u_hat_sym = solver.step_rk4(u_hat_sym, h)
        t_elapsed += h
    w_sym = solver.vorticity_field(u_hat_sym)[0]
    sup_sym = dg.sup_vorticity(w_sym)
    rel = abs(ctrl["sup_omega"] if "sup_omega" in ctrl else 0.0)
    # run_single returns tail_slope etc; recompute control sup directly
    u_hat_ctrl = solver.dealias(solver.project(solver.fft(taylor_green(cfg["n"]))))
    t_elapsed = 0.0
    while t_elapsed < cfg["t_horizon"] - 1e-12:
        h = min(cfg["dt"], cfg["t_horizon"] - t_elapsed)
        u_hat_ctrl = solver.step_rk4(u_hat_ctrl, h)
        t_elapsed += h
    sup_ctrl = dg.sup_vorticity(solver.vorticity_field(u_hat_ctrl)[0])
    rel = abs(sup_sym - sup_ctrl) / max(sup_ctrl, 1e-30)
    verdict.check("check_symmetry", rel < 1e-8,
                  f"evolved sup|w| rel diff = {rel:.2e}")

    # --- B: pointwise kick ----------------------------------------------
    bmat = b_rotation_matrix()
    u_kick = solver.rotate_pointwise(u_hat, bmat)
    div_inj = dg.divergence_max(solver.k_vec, u_kick, cfg["n"])
    e_kick = dg.mean_energy(u_kick, cfg["n"])
    verdict.check("check_isometry", abs(e_kick - e0) < 1e-12,
                  f"dE = {abs(e_kick - e0):.2e}")
    verdict.check("check_incompressibility_break", div_inj > 1e-6,
                  f"injected |div| = {div_inj:.2e} (must be nonzero to "
                  "document the effect)")
    kicked = _evolve_with_kicks(cfg["n"], cfg["nu"], cfg["dt"],
                                cfg["t_horizon"], 0.25, "pointwise")
    verdict.check("check_div", kicked["div_post"] < 1e-10,
                  f"after reprojection max div = {kicked['div_post']:.2e}; "
                  f"injected (documented) = {kicked['div_injected']:.2e}")

    # --- C: effect on the monitors --------------------------------------
    rel_gain = (kicked["sup_omega"] - sup_ctrl) / max(sup_ctrl, 1e-30)
    verdict.values["control_sup_omega"] = round(sup_ctrl, 8)
    verdict.values["kicked_sup_omega"] = round(kicked["sup_omega"], 8)
    verdict.values["relative_effect"] = round(rel_gain, 8)
    verdict.extra["mechanism_effect"] = (
        "none within tolerance" if abs(rel_gain) < 0.05
        else ("reduces sup|omega|" if rel_gain < 0 else "increases sup|omega|"))
    print(f"    control sup|w| = {sup_ctrl:.6f}, "
          f"b-kicked sup|w| = {kicked['sup_omega']:.6f} "
          f"({rel_gain * 100:+.3f}%)")
    return verdict.finish()
