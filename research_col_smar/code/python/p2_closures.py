"""P2: two-point closures for the Kolmogorov constant (Heisenberg, Pao, DIA).

Executes monograph ch. 5:
  (1) Heisenberg spectral balance -> closed-form spectrum
      E_H(k) = (a^2/4) eps^(1/4) nu^(5/4) chi^-7 [1 + (3a^2/8) chi^-4]^(-4/3),
      inertial constant C_K(alpha) = (8 / (9 alpha))^(2/3);
  (2) calibration of alpha from C_K (experiment, LhDIA) and the inverse map;
  (3) Pao spectrum with exact dissipation normalization
      beta = (C_K Gamma(2/3))^(3/2);
  (4) numeric checks: dissipation integral, inertial-range constant,
      far-dissipation slope  k^-7.

Outputs:
  results/p2_closures.json
  results/p2_spectra.csv    (chi, E_H, E_Pao in Kolmogorov-scaled units)
"""

from __future__ import annotations

import hashlib
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from sk_core import (  # noqa: E402
    CK_DIA,
    CK_LHDIA,
    CK_SREENIVASAN,
    alpha_from_ck,
    ck_from_alpha,
    heisenberg_spectrum,
    pao_beta,
    pao_spectrum,
    results_json_dump,
)

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
RESULTS = os.path.join(ROOT, "results")


def main() -> int:
    os.makedirs(RESULTS, exist_ok=True)
    eps, nu = 1.0, 1.0e-4
    eta = (nu**3 / eps) ** 0.25

    checks = []
    for label, ck in (
        ("experiment", CK_SREENIVASAN),
        ("LhDIA", CK_LHDIA),
        ("DIA", CK_DIA),
    ):
        alpha = alpha_from_ck(ck)
        # round trip
        ck_rt = ck_from_alpha(alpha)
        # dissipation integral of the Heisenberg spectrum must equal eps/2 per
        # the balance eps = 2 nu I(inf) -> 2 nu int k^2 E dk = eps
        k = np.logspace(-3, 6, 400_000) / eta
        e_h = heisenberg_spectrum(k, eps, nu, alpha)
        diss = 2.0 * nu * np.trapezoid(k**2 * e_h, k)
        checks.append(
            {
                "source": label,
                "C_K_target": ck,
                "alpha": alpha,
                "C_K_roundtrip": ck_rt,
                "dissipation_integral": float(diss),
                "dissipation_rel_error": float(abs(diss - eps) / eps),
            }
        )

    # inertial-range constant recovered from the closed-form spectrum (alpha
    # calibrated on experiment): fit on 0.01 < chi < 0.2
    alpha = alpha_from_ck(CK_SREENIVASAN)
    k = np.logspace(-3, 6, 200_000) / eta
    e_h = heisenberg_spectrum(k, eps, nu, alpha)
    chi = k * eta
    m = (chi > 0.01) & (chi < 0.2)
    slope = float(np.polyfit(np.log(chi[m]), np.log(e_h[m]), 1)[0])
    # E = C_K eps^(2/3) k^(-5/3) = C_K eps^(2/3) eta^(5/3) chi^(-5/3):
    intercept = float(np.polyfit(np.log(chi[m]), np.log(e_h[m]), 1)[1])
    ck_measured = float(np.exp(intercept) / (eps ** (2.0 / 3.0) * eta ** (5.0 / 3.0)))

    # far-dissipation slope on 3 < chi < 20
    m2 = (chi > 3.0) & (chi < 20.0)
    slope_far = float(np.polyfit(np.log(chi[m2]), np.log(e_h[m2]), 1)[0])

    # Pao spectrum: dissipation integral check
    e_p = pao_spectrum(k, eps, nu, CK_SREENIVASAN)
    diss_pao = 2.0 * nu * np.trapezoid(k**2 * e_p, k)

    # CSV export in Kolmogorov-scaled units
    chi_c = np.logspace(-2, 1.5, 300)
    e_h_c = (
        heisenberg_spectrum(chi_c / eta, eps, nu, alpha)
        * eta ** (5.0 / 3.0)
        / eps ** (2.0 / 3.0)
    )
    e_p_c = (
        pao_spectrum(chi_c / eta, eps, nu, CK_SREENIVASAN)
        * eta ** (5.0 / 3.0)
        / eps ** (2.0 / 3.0)
    )
    csv_path = os.path.join(RESULTS, "p2_spectra.csv")
    with open(csv_path, "w", newline="", encoding="utf-8") as fh:
        fh.write("chi,E_heisenberg_scaled,E_pao_scaled\n")
        for a, b, c in zip(chi_c, e_h_c, e_p_c):
            fh.write(f"{a:.6e},{b:.6e},{c:.6e}\n")

    protocol = {
        "program": "P2_closures",
        "title": "Two-point closures for the Kolmogorov constant",
        "date": "2026-09-29",
        "heisenberg": {
            "closure": "nu_T(k) = alpha int_k^inf sqrt(E(q)/q^3) dq",
            "balance": "eps = 2 (nu + nu_T(k)) int_0^k q^2 E(q) dq",
            "closed_form_spectrum": (
                "E(k) = (alpha^2/4) eps^(1/4) nu^(5/4) chi^-7 "
                "[1 + (3 alpha^2 / 8) chi^-4]^(-4/3),  chi = k eta"
            ),
            "master_relation": "C_K(alpha) = (8 / (9 alpha))^(2/3),  alpha = 8 / (9 C_K^(3/2))",
            "calibration": checks,
            "inertial_slope_measured": slope,
            "inertial_C_K_measured": ck_measured,
            "far_dissipation_slope": slope_far,
        },
        "pao": {
            "spectrum": "E(k) = C_K eps^(2/3) k^(-5/3) exp(-beta chi^2)",
            "beta_rule": "beta = (C_K Gamma(2/3))^(3/2)",
            "beta_value": pao_beta(CK_SREENIVASAN),
            "dissipation_integral": float(diss_pao),
            "dissipation_rel_error": float(abs(diss_pao - eps) / eps),
        },
        "literature": {
            "Sreenivasan_1995_experiment": CK_SREENIVASAN,
            "Kraichnan_1965_LhDIA": CK_LHDIA,
            "Kraichnan_1959_DIA": CK_DIA,
        },
        "integrity": {
            "sha256_of_code": hashlib.sha256(
                open(os.path.abspath(__file__), "rb").read()
            ).hexdigest(),
        },
    }
    results_json_dump(protocol, os.path.join(RESULTS, "p2_closures.json"))
    print(
        f"[P2] Heisenberg: alpha = {alpha:.4f} -> C_K = {ck_measured:.4f} "
        f"(target {CK_SREENIVASAN}), slope = {slope:.4f}, far slope = {slope_far:.2f}"
    )
    print(
        f"[P2] dissipation checks: H = {checks[0]['dissipation_rel_error']:.1e}, "
        f"Pao = {abs(diss_pao - eps) / eps:.1e}"
    )
    print(f"[P2] wrote {csv_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
