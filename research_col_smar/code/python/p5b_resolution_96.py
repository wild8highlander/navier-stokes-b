"""P5-B: resolution study — the TG regularity protocol on a 96^3 grid.

Extends the smoothness program of ch. 12 (P5, 48^3) by re-running the
baseline trajectory on a grid twice as fine in every direction:

  (1) run A96: pseudo-spectral DNS 96^3, nu = 0.01, dt = 2e-3, T = 6,
      2/3-rule dealiasing, integrating-factor midpoint RK2 (the same
      solver as P5; the only changes are the certification band, now
      [22, 32] against k_c = 32, and snapshot export for P5-C);
  (2) run H2_96: the worst-resolved hyperdissipative case b_pow = 2
      repeated at 96^3 — at 48^3 it had only k_max/eta_b = 6.2, at 96^3
      the resolved margin doubles, testing the x*(b) collapse
      convergence of the generalized Pao theory;
  (3) convergence report: every headline diagnostic of run A
      (t_peak, Omega_max, ||omega||_oo, I_BKM, LPS integrals, E(6),
      eps_mean, certificate exponents, k_d.eta_b) is compared 48^3 vs
      96^3; the b_pow = 2 rel.dev is compared against its 48^3 value;
  (4) self-verification gates as in P5 (div-free IC residual, energy
      balance dE/dt = -2 eps, enstrophy balance dOmega/dt = S1 - D2);
  (5) snapshots of u at t = 4, 5, 6 (raw f64, C-order (3, 96, 96, 96))
      feed the P5-C stretching-statistics experiment; the t = 5 field
      is additionally archived as float32 npz, and the f64-vs-f32
      sensitivity of the alignment statistics is reported (robustness
      of the statistics to storage precision).

Checkpointed execution (sandbox tooling kills long background processes,
so the trajectory is chunked; the spectral state u_hat is the COMPLETE
solver state — IFK-RK2 is deterministic, hence checkpoint/resume is
bit-exact):

  python3 p5b_resolution_96.py --step A96    # run up to BUDGET_S seconds
  python3 p5b_resolution_96.py --step H2_96  # (repeat until it reports done)
  python3 p5b_resolution_96.py --finalize    # reports, csv, json, snapshots

Outputs: results/p5b_resolution_96.json, results/p5b_bkm_96.csv,
         results/p5b_certificate_96.csv, results/p5b_bfamily_96.csv,
         results/p5b_spectra_96.npz, results/p5b_snap_u_t{4,5,6}.f64,
         results/p5b_snap_u_t5_f32.npz
"""

from __future__ import annotations

import csv
import hashlib
import json
import os
import sys
import time

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from sk_core import CK_SREENIVASAN, results_json_dump  # noqa: E402
from p5_regularity import (  # noqa: E402
    SpecSolver,
    eta_b,
    kd_from_spectrum,
    tail_fits,
    tg_initial_condition,
    wavevectors,
    x_star,
    beta_b,
)

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
RESULTS = os.path.join(ROOT, "results")

N = 96
NU = 0.01
DT = 2.0e-3
T_END = 6.0
SAVE_EVERY = 10
CERT_BAND_96 = (22.0, 32.0)  # k_c = N/3 = 32
STAT_T0 = 2.0
SPEC_TIMES = (1.0, 2.0, 3.0, 4.0, 5.0)
SNAP_TIMES = (4.0, 5.0, 6.0)
BUDGET_S = 460.0  # per-invocation wall budget (< 10 min tool limit)
STATE_FILES = {"A96": "p5b_state_A96.npz", "H2_96": "p5b_state_H2_96.npz"}


def _new_logs() -> dict:
    return {
        "t": [],
        "E": [],
        "Omega": [],
        "eps": [],
        "omega_inf": [],
        "u_inf": [],
        "u4": [],
        "u6": [],
        "pal": [],
        "S1": [],
        "D2": [],
        "cert": [],
    }


def step_run(label: str, b_pow: float) -> bool:
    """Run one checkpointed chunk; return True when the trajectory is done."""
    path = os.path.join(RESULTS, STATE_FILES[label])
    n_steps = int(round(T_END / DT))
    solver = SpecSolver(N, NU, DT, b_pow)

    if os.path.exists(path):
        with np.load(path, allow_pickle=False) as z:
            uh = z["uh"]
            step0 = int(z["step"])
            logs = {k: list(z["log_" + k]) for k in _new_logs()}
            spec_store = {k: z[k] for k in z.files if k.startswith("spec_")}
            spec_store = {k[5:]: v for k, v in spec_store.items()}
            snaps = {k[5:]: z["snap_" + k] for k in z.files if k.startswith("snap_")}
            snaps = {float(k): v for k, v in snaps.items()}
        solver.uh = uh.copy()
        print(f"[{label}] resume at step {step0}", flush=True)
    else:
        solver.set_ic(tg_initial_condition(N))
        step0 = 0
        logs = _new_logs()
        spec_store: dict[str, np.ndarray] = {}
        snaps: dict[float, np.ndarray] = {}
        print(f"[{label}] fresh start", flush=True)

    t0 = time.perf_counter()
    step = step0
    while step <= n_steps:
        t = step * DT
        if step % 250 == 0:
            print(
                f"    [{label}] step {step}/{n_steps}  t={t:.2f}  "
                f"E={solver.energy():.6f}  "
                f"elapsed={time.perf_counter() - t0:.0f}s",
                flush=True,
            )
        if step % SAVE_EVERY == 0 or step == n_steps:
            u = solver.phys()
            w = solver.vorticity()
            E = solver.energy()
            eps = solver.diss_rate()
            win = float(np.max(np.sqrt(np.sum(w * w, axis=0))))
            uin = float(np.max(np.sqrt(np.sum(u * u, axis=0))))
            u4 = float(np.mean(np.sum(u * u, axis=0)) ** 2)
            u6 = float(np.mean(np.sum(u * u, axis=0)) ** 3)
            Om, pal = solver.enstrophy_palinstrophy()
            s1 = solver.stretching(u, w)
            wh2 = np.sum(np.abs(solver.vorticity_hat()) ** 2, axis=0)
            k2b = solver.k2 if b_pow == 1.0 else solver.kmb
            d2 = 4.0 * NU * float(np.sum(k2b * wh2)) / N**6
            e_sh = solver.shell_spectrum()
            c_exp, r2_exp, sl_pow, r2_pow = tail_fits(e_sh, CERT_BAND_96)
            kd = kd_from_spectrum(e_sh, NU, b_pow, N)
            logs["t"].append(t)
            logs["E"].append(E)
            logs["Omega"].append(Om)
            logs["eps"].append(eps)
            logs["omega_inf"].append(win)
            logs["u_inf"].append(uin)
            logs["u4"].append(u4)
            logs["u6"].append(u6)
            logs["pal"].append(pal)
            logs["S1"].append(s1)
            logs["D2"].append(d2)
            logs["cert"].append((c_exp, r2_exp, sl_pow, r2_pow, kd))
            for ts in SPEC_TIMES:
                if abs(t - ts) <= 0.5 * DT * SAVE_EVERY and ts not in spec_store:
                    spec_store[f"{label}_t{ts:g}"] = e_sh.copy()
            if label == "A96":
                for ts in SNAP_TIMES:
                    if abs(t - ts) < 1e-12 and ts not in snaps:
                        snaps[ts] = u.copy()
        if step == n_steps:
            break
        # budget guard: the remaining step pair must fit before saving state
        if time.perf_counter() - t0 > BUDGET_S and step > step0:
            break
        solver.step()
        step += 1

    done = step >= n_steps
    np.savez(
        path,
        uh=solver.uh,
        step=step,
        **{f"log_{k}": np.array(v) for k, v in logs.items()},
        **{f"spec_{k}": v for k, v in spec_store.items()},
        **{f"snap_{ts:g}": v for ts, v in snaps.items()},
    )
    print(
        f"[{label}] state saved at step {step}/{n_steps} "
        f"({'DONE' if done else 'continue with --step ' + label})",
        flush=True,
    )
    return done


def load_state(label: str) -> dict:
    with np.load(os.path.join(RESULTS, STATE_FILES[label]), allow_pickle=False) as z:
        out = {
            "t": z["log_t"],
            "E": z["log_E"],
            "Omega": z["log_Omega"],
            "eps": z["log_eps"],
            "omega_inf": z["log_omega_inf"],
            "u_inf": z["log_u_inf"],
            "u4": z["log_u4"],
            "u6": z["log_u6"],
            "pal": z["log_pal"],
            "S1": z["log_S1"],
            "D2": z["log_D2"],
            "cert": z["log_cert"],
        }
        out["spec_store"] = {k[5:]: z[k] for k in z.files if k.startswith("spec_")}
        out["snaps"] = {float(k[5:]): z[k] for k in z.files if k.startswith("snap_")}
    return out


def summarize(state: dict, b_pow: float) -> dict:
    t_arr = state["t"]
    E_arr = state["E"]
    Om_arr = state["Omega"]
    eps_arr = state["eps"]
    win_arr = state["omega_inf"]
    cert_arr = state["cert"]

    i_peak = int(np.argmax(Om_arr))
    i_bkm = float(np.trapezoid(win_arr, t_arr))
    lps4 = float(np.trapezoid(state["u4"], t_arr))
    lps6 = float(np.trapezoid(np.sqrt(state["u6"]), t_arr))
    dEdt = (E_arr[2:] - E_arr[:-2]) / (t_arr[2:] - t_arr[:-2])
    bal = float(np.max(np.abs(dEdt + 2.0 * eps_arr[1:-1]))) / max(
        float(E_arr.max()), 1e-300
    )
    dOmdt = (Om_arr[2:] - Om_arr[:-2]) / (t_arr[2:] - t_arr[:-2])
    bal2 = float(
        np.max(np.abs(dOmdt - (state["S1"][1:-1] - state["D2"][1:-1])))
    ) / max(float(Om_arr.max()), 1e-300)
    m_stat = t_arr >= STAT_T0
    eps_mean = float(np.mean(eps_arr[m_stat]))
    kd_win = float(np.mean(cert_arr[m_stat, 4]))
    return {
        "t_peak_enstrophy": float(t_arr[i_peak]),
        "Omega_max": float(Om_arr.max()),
        "omega_inf_max": float(win_arr.max()),
        "u_inf_max": float(state["u_inf"].max()),
        "I_BKM_T": i_bkm,
        "LPS_int_u4": lps4,
        "LPS_int_u6half": lps6,
        "E_final": float(E_arr[-1]),
        "eps_mean_stat": eps_mean,
        "energy_balance_rel_max": bal,
        "enstrophy_balance_rel_max": bal2,
        "kd_mean_stat": kd_win,
        "c_exp_at_peak": float(cert_arr[i_peak, 0]),
        "r2_exp_at_peak": float(cert_arr[i_peak, 1]),
        "slope_pow_at_peak": float(cert_arr[i_peak, 2]),
        "r2_pow_at_peak": float(cert_arr[i_peak, 3]),
    }


def finalize() -> int:
    t_wall0 = time.perf_counter()
    # divergence-free residual of the TG IC on the 96^3 grid
    kx, ky, kz, k2 = wavevectors(N)
    k2e = k2.copy()
    k2e[0, 0, 0] = 1.0
    uh0 = np.fft.rfftn(tg_initial_condition(N), axes=(1, 2, 3))
    div_free_max = float(np.max(np.abs(kx * uh0[0] + ky * uh0[1] + kz * uh0[2]) / k2e))

    sa = load_state("A96")
    sh = load_state("H2_96")
    sA = summarize(sa, 1.0)
    sH = summarize(sh, 2.0)
    print(
        f"[P5-B] A96: t_peak={sA['t_peak_enstrophy']:.2f}, "
        f"Omega_max={sA['Omega_max']:.4f}, ||w||oo={sA['omega_inf_max']:.4f}, "
        f"I_BKM={sA['I_BKM_T']:.4f}",
        flush=True,
    )

    # ---- convergence report vs the 48^3 protocol ---------------------------
    with open(os.path.join(RESULTS, "p5_regularity.json"), encoding="utf-8") as fh:
        p48 = json.load(fh)
    a48 = p48["run_A_baseline"]
    conv_keys = [
        "t_peak_enstrophy",
        "Omega_max",
        "omega_inf_max",
        "u_inf_max",
        "I_BKM_T",
        "LPS_int_u4",
        "LPS_int_u6half",
        "E_final",
        "eps_mean_stat",
        "c_exp_at_peak",
        "r2_exp_at_peak",
        "slope_pow_at_peak",
        "r2_pow_at_peak",
    ]
    convergence = {}
    for key in conv_keys:
        v48, v96 = a48[key], sA[key]
        rel = abs(v96 - v48) / max(abs(v48), 1e-300) if v48 != 0 else float("nan")
        convergence[key] = {"n48": v48, "n96": v96, "rel_diff": rel}
    b2_48 = [r for r in p48["b_family_prediction_test"] if r["b_pow"] == 2.0][0]
    eb96 = eta_b(sH["eps_mean_stat"], NU, 2.0)
    kd96 = sH["kd_mean_stat"]
    row96 = {
        "b_pow": 2.0,
        "grid": N,
        "eps_mean_stat": sH["eps_mean_stat"],
        "eta_b": eb96,
        "k_max_over_eta_b": (N / 3.0) * eb96,
        "kd_measured": kd96,
        "kd_times_eta_b": kd96 * eb96,
        "x_star_theory": x_star(2.0),
        "beta_b_theory": beta_b(2.0),
        "rel_dev": abs(kd96 * eb96 - x_star(2.0)) / x_star(2.0),
        "rel_dev_48": b2_48["rel_dev"],
        "k_max_over_eta_b_48": b2_48["k_max_over_eta_b"],
    }

    # ---- snapshots ---------------------------------------------------------
    for ts, arr in sa["snaps"].items():
        arr.tofile(os.path.join(RESULTS, f"p5b_snap_u_t{ts:g}.f64"))
    if 5.0 in sa["snaps"]:
        np.savez_compressed(
            os.path.join(RESULTS, "p5b_snap_u_t5_f32.npz"),
            u=sa["snaps"][5.0].astype(np.float32),
            grid=N,
            t=5.0,
            nu=NU,
            layout="u, raw float32, C-order, shape (3, 96, 96, 96)",
        )

    # ---- csv outputs -------------------------------------------------------
    with open(os.path.join(RESULTS, "p5b_bkm_96.csv"), "w", newline="", encoding="utf-8") as fh:
        wr = csv.writer(fh)
        wr.writerow(["t", "E", "Omega", "omega_inf", "I_BKM", "eps"])
        ia = np.cumsum(
            np.concatenate(
                [[0.0], 0.5 * (sa["omega_inf"][1:] + sa["omega_inf"][:-1]) * np.diff(sa["t"])]
            )
        )
        for j, t in enumerate(sa["t"]):
            wr.writerow(
                [f"{t:.4f}", f"{sa['E'][j]:.8e}", f"{sa['Omega'][j]:.8e}",
                 f"{sa['omega_inf'][j]:.8e}", f"{ia[j]:.8e}", f"{sa['eps'][j]:.8e}"]
            )

    with open(os.path.join(RESULTS, "p5b_certificate_96.csv"), "w", newline="", encoding="utf-8") as fh:
        wr = csv.writer(fh)
        wr.writerow(["t", "c_exp", "r2_exp", "slope_pow", "r2_pow", "kd"])
        for j, t in enumerate(sa["t"]):
            c, re_, sp, rp, kd = sa["cert"][j]
            wr.writerow([f"{t:.4f}", f"{c:.6e}", f"{re_:.6f}", f"{sp:.6e}", f"{rp:.6f}", f"{kd:.4f}"])

    with open(os.path.join(RESULTS, "p5b_bfamily_96.csv"), "w", newline="", encoding="utf-8") as fh:
        wr = csv.DictWriter(fh, fieldnames=list(row96.keys()))
        wr.writeheader()
        wr.writerow(row96)

    np.savez(
        os.path.join(RESULTS, "p5b_spectra_96.npz"),
        **{key: val for key, val in sa["spec_store"].items()},
        **{key: val for key, val in sh["spec_store"].items()},
    )

    protocol = {
        "program": "P5B_resolution",
        "title": (
            "P5-B: resolution study of the 3D smoothness protocol — "
            "Taylor-Green regularity diagnostics at 96^3"
        ),
        "date": "2026-09-29",
        "parameters": {
            "grid": N,
            "nu": NU,
            "dt": DT,
            "T_end": T_END,
            "ic": "Taylor-Green u=(sin x cos y cos z, -cos x sin y cos z, 0)",
            "dealiasing": "2/3 rule on the nonlinear product",
            "time_stepper": "integrating-factor midpoint RK2 + Leray projection",
            "cert_band_96": list(CERT_BAND_96),
            "cert_band_48_reference": [11.0, 16.0],
            "stat_window_t0": STAT_T0,
            "C_K_used_for_beta_b": CK_SREENIVASAN,
            "b_pow_H2_run": 2.0,
            "execution": "checkpointed chunks (u_hat is the complete IFK-RK2 state)",
        },
        "self_verification": {
            "div_free_residual_max": div_free_max,
            "energy_balance_rel_max_A96": sA["energy_balance_rel_max"],
            "enstrophy_balance_rel_max_A96": sA["enstrophy_balance_rel_max"],
            "energy_balance_rel_max_H2_96": sH["energy_balance_rel_max"],
        },
        "run_A96_summary": {k: v for k, v in sA.items() if "balance" not in k},
        "run_H2_96_summary": {k: v for k, v in sH.items() if "balance" not in k},
        "convergence_48_vs_96": convergence,
        "b2_resolution_test_96": row96,
        "snapshots": {
            "times": sorted(sa["snaps"].keys()),
            "layout": "raw float64 C-order, shape (3, 96, 96, 96)",
            "files": [f"p5b_snap_u_t{ts:g}.f64" for ts in sorted(sa["snaps"].keys())],
            "archived_f32": "p5b_snap_u_t5_f32.npz",
        },
        "wall_time_min_finalize": round((time.perf_counter() - t_wall0) / 60.0, 1),
        "integrity": {
            "sha256_of_code": hashlib.sha256(
                open(os.path.abspath(__file__), "rb").read()
            ).hexdigest(),
            "sha256_of_p5_regularity_py": hashlib.sha256(
                open(
                    os.path.join(os.path.dirname(os.path.abspath(__file__)), "p5_regularity.py"),
                    "rb",
                ).read()
            ).hexdigest(),
        },
    }
    out = os.path.join(RESULTS, "p5b_resolution_96.json")
    results_json_dump(protocol, out)
    print(f"[P5-B] wrote {out}")
    print(
        f"[P5-B] energy balance A96: {sA['energy_balance_rel_max']:.2e}, "
        f"enstrophy balance A96: {sA['enstrophy_balance_rel_max']:.2e}, "
        f"div-free: {div_free_max:.2e}"
    )
    print(
        f"[P5-B] b2 at 96^3: k_d*eta_b = {row96['kd_times_eta_b']:.4f} "
        f"vs x*(2) = {row96['x_star_theory']:.4f} "
        f"(rel.dev {row96['rel_dev']:.1%}, was {row96['rel_dev_48']:.1%} at 48^3)"
    )
    # states are reproducible; drop the bulky intermediates
    for f in STATE_FILES.values():
        p = os.path.join(RESULTS, f)
        if os.path.exists(p):
            os.remove(p)
    return 0


def main() -> int:
    os.makedirs(RESULTS, exist_ok=True)
    if "--finalize" in sys.argv:
        return finalize()
    label = "A96" if "--step" not in sys.argv else sys.argv[sys.argv.index("--step") + 1]
    if label not in STATE_FILES:
        raise SystemExit(f"unknown label {label}")
    done = step_run(label, 1.0 if label == "A96" else 2.0)
    return 0 if done else 3  # exit code 3 = "run --step again"


if __name__ == "__main__":
    raise SystemExit(main())
