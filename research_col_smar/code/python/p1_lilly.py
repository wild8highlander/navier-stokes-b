"""P1: analytical determination of C_s from C_K (the Lilly relation).

Executes the derivation chain of monograph ch. 4:
  (1) matched SGS dissipation  eps_sgs = (C_s Delta)^2 <|Sbar|^3> = eps;
  (2) resolved-strain integral for sharp / Gaussian / box filters;
  (3) the master curve C_s(C_K) and the reference point C_K = 1.5;
  (4) sensitivity: filter family and Pao versus bare K41 spectrum.

Outputs:
  results/p1_lilly.json       pinned protocol with all numbers
  results/p1_lilly_table.csv  C_s(C_K) for the three filters
"""

from __future__ import annotations

import csv
import hashlib
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from sk_core import (  # noqa: E402
    CK_SREENIVASAN,
    CS_LILLY,
    GAMMA_23,
    fit_kolmogorov_constant,
    lilly_cs,
    pao_beta,
    results_json_dump,
)

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
RESULTS = os.path.join(ROOT, "results")


def strain_factor_sharp(ck: float) -> float:
    """<|Sbar|^2> = (3/2) C_K eps^(2/3) kc^(4/3) for a sharp cutoff (ch. 4.2)."""
    return 1.5 * ck


def main() -> int:
    os.makedirs(RESULTS, exist_ok=True)

    # --- (3) master curve C_s(C_K) for the three filter families ----------
    ck_grid = np.round(np.arange(1.30, 1.851, 0.025), 4)
    rows = []
    for ck in ck_grid:
        rows.append(
            {
                "C_K": float(ck),
                "C_s_sharp": lilly_cs(float(ck), "sharp"),
                "C_s_gaussian": lilly_cs(float(ck), "gaussian"),
                "C_s_box": lilly_cs(float(ck), "box"),
            }
        )

    ck_ref = CK_SREENIVASAN
    cs_ref = {
        "sharp": lilly_cs(ck_ref, "sharp"),
        "gaussian": lilly_cs(ck_ref, "gaussian"),
        "box": lilly_cs(ck_ref, "box"),
    }

    # --- (4) sensitivity to the spectral model (sharp cutoff) -------------
    # Bare K41 integrated to kc vs Pao spectrum integrated to kc: the
    # dissipation-range tail removes a small fraction of <|Sbar|^2>,
    # raising the implied C_s by the factor f = (1 - loss)^(-3/4).
    eps, nu = 1.0, 1.0e-4
    eta = (nu**3 / eps) ** 0.25
    delta_over_eta = np.logspace(np.log10(2.0), np.log10(200.0), 40)
    sens = []

    for ratio in delta_over_eta:
        delta = ratio * eta
        kc = np.pi / delta
        chi_c = kc * eta  # = pi / ratio
        k_grid = np.linspace(1e-9, chi_c, 4000)
        full = (
            2.0 * ck_ref * np.trapezoid(k_grid ** (1.0 / 3.0), k_grid)
        )  # bare K41, chi-units (eps absorbed: E=CK chi^-5/3 in chi units)
        # Pao spectrum in chi units: E_chi = CK chi^(-5/3) exp(-beta chi^2)
        beta = pao_beta(ck_ref)
        e_pao = ck_ref * k_grid ** (-5.0 / 3.0) * np.exp(-beta * k_grid**2)
        pao_val = 2.0 * np.trapezoid(
            k_grid ** (1.0 / 3.0) * e_pao / ck_ref * ck_ref, k_grid
        )
        loss = 1.0 - pao_val / full
        cs_bare = lilly_cs(ck_ref, "sharp")
        cs_pao = cs_bare * (1.0 - loss) ** -0.75
        sens.append(
            {
                "Delta_over_eta": float(ratio),
                "chi_c": float(chi_c),
                "strain_loss_frac": float(loss),
                "C_s_K41": float(cs_bare),
                "C_s_Pao": float(cs_pao),
            }
        )

    # --- consistency probe: the analytic factor for the Gaussian filter ---
    gauss_analytic = (ck_ref * GAMMA_23 * 12.0 ** (2.0 / 3.0)) ** -0.75

    # --- verification: numerical quadrature of the sharp-cutoff relation ---
    # <|Sbar|^2> = 2 CK eps^(2/3) int_0^(pi/Delta) k^(1/3) dk = (3/2) CK eps^(2/3) kc^(4/3)
    k_num = np.linspace(0.0, np.pi, 2_000_001)
    strain_num = 2.0 * ck_ref * np.trapezoid(k_num ** (1.0 / 3.0), k_num)
    strain_exact = 1.5 * ck_ref * np.pi ** (4.0 / 3.0)
    quad_err = abs(strain_num - strain_exact) / strain_exact

    # --- free-slope diagnostic on a synthetic K41 spectrum ----------------
    k_syn = np.logspace(0.0, 3.0, 200)
    e_syn = ck_ref * k_syn ** (-5.0 / 3.0)
    ck_fit, slope_fit, rms = fit_kolmogorov_constant(k_syn, e_syn, 2.0, 500.0)

    protocol = {
        "program": "P1_lilly",
        "title": "Analytical determination of C_s from C_K (Lilly relation)",
        "date": "2026-09-29",
        "conventions": {
            "spectrum": "E(k) = C_K eps^(2/3) k^(-5/3)",
            "strain_norm": "|Sbar| = (2 Sbar_ij Sbar_ij)^(1/2)",
            "sgs_dissipation": "eps_sgs = (C_s Delta)^2 <|Sbar|^3>",
            "sharp_cutoff": "k_c = pi / Delta",
        },
        "master_relation": {
            "sharp": "C_s = 1 / (pi (3 C_K / 2)^(3/4))",
            "gaussian": "C_s = (C_K Gamma(2/3) 12^(2/3))^(-3/4)",
            "box": "C_s = val^(-3/4), val = 2 C_K int chi^(1/3) sinc^2(chi/2) dchi",
        },
        "reference_point": {
            "C_K": ck_ref,
            "C_s_sharp": cs_ref["sharp"],
            "C_s_gaussian": cs_ref["gaussian"],
            "C_s_box": cs_ref["box"],
            "C_s_lilly_1966": CS_LILLY,
            "abs_diff_vs_lilly": abs(cs_ref["sharp"] - CS_LILLY),
        },
        "verification": {
            "quadrature_relative_error": quad_err,
            "gaussian_analytic_value": gauss_analytic,
            "synthetic_fit_C_K": ck_fit,
            "synthetic_fit_free_slope": slope_fit,
            "synthetic_fit_residual_rms": rms,
        },
        "sensitivity_pao_vs_k41": sens,
        "table": rows,
        "integrity": {
            "sha256_of_code": hashlib.sha256(
                open(os.path.abspath(__file__), "rb").read()
            ).hexdigest(),
        },
    }
    results_json_dump(protocol, os.path.join(RESULTS, "p1_lilly.json"))

    csv_path = os.path.join(RESULTS, "p1_lilly_table.csv")
    with open(csv_path, "w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)

    print(
        f"[P1] C_K = {ck_ref}: C_s sharp = {cs_ref['sharp']:.5f}, "
        f"gaussian = {cs_ref['gaussian']:.5f}, box = {cs_ref['box']:.5f}"
    )
    print(
        f"[P1] |C_s - Lilly| = {abs(cs_ref['sharp'] - CS_LILLY):.2e}, "
        f"quadrature err = {quad_err:.2e}"
    )
    print(f"[P1] wrote {csv_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
