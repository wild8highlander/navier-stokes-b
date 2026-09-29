"""sk_core: shared library of the Smagorinsky-Kolmogorov research program.

Derives the closed-form relations that couple the Kolmogorov constant C_K and
the Smagorinsky constant C_s, and provides the spectral models (K41, Pao,
Heisenberg) used by the P1-P4 numerical programs.

Physical conventions (fixed once, used everywhere):

  * 3D isotropic turbulence, energy spectrum  E(k) = C_K eps^(2/3) k^(-5/3)
    in the inertial range, eps = dissipation rate [m^2/s^3].
  * Kolmogorov length scale  eta = (nu^3 / eps)^(1/4).
  * Filtered (resolved) strain norm  |Sbar| = (2 Sbar_ij Sbar_ij)^(1/2).
  * Smagorinsky closure  nu_t = (C_s Delta)^2 |Sbar|,
    SGS dissipation  eps_sgs = (C_s Delta)^2 <|Sbar|^3>  (quasi-Gaussian mean).
  * Sharp spectral cutoff  k_c = pi / Delta.
"""

from __future__ import annotations

import math

import numpy as np

# ---------------------------------------------------------------------------
# Reference values (literature anchors, see monograph ch. 10 for sources)
# ---------------------------------------------------------------------------
CK_SREENIVASAN = 1.50  # Sreenivasan 1995 review of the Kolmogorov constant
CK_LHDIA = 1.52  # Lagrangian-history DIA (Kraichnan 1965)
CK_DIA = 1.77  # Eulerian DIA (Kraichnan 1959)
CS_LILLY = 0.17326  # Lilly (1966/67) value for a sharp cutoff, C_K = 1.5
GAMMA_23 = 1.3541179394264005  # Gamma(2/3)


# ---------------------------------------------------------------------------
# Analytical core: the Lilly relation  C_s(C_K)
# ---------------------------------------------------------------------------
def lilly_cs(ck: float, filter_type: str = "sharp") -> float:
    """Smagorinsky constant implied by the K41 spectrum for a given filter.

    Monograph ch. 4: eps_sgs = (C_s Delta)^2 <|Sbar|^3> is matched to the
    resolved-strain integral  <|Sbar|^2> = 2 int_0^kc k^2 E(k) dk.

    sharp   : k_c = pi/Delta, G_hat = 1 for k < k_c
              -> C_s = 1 / (pi (3 C_K / 2)^(3/4))
    gaussian: G_hat = exp(-k^2 Delta^2 / 24) (Delta = standard deviation
              convention), k_c = infinity
              -> C_s = (C_K Gamma(2/3) 12^(2/3))^(-3/4)
    box     : G_hat = sinc(k Delta / 2), evaluated numerically (quadrature)
    """
    if filter_type == "sharp":
        return 1.0 / (math.pi * (1.5 * ck) ** 0.75)
    if filter_type == "gaussian":
        return (ck * GAMMA_23 * 12.0 ** (2.0 / 3.0)) ** -0.75
    if filter_type == "box":
        val = _strain_integral_box(ck)
        # eps = (C_s Delta)^2 <|Sbar|^2>^(3/2),  <|Sbar|^2> = val * eps^(2/3) D^-4/3
        # -> 1 = C_s^2 (val)^(3/2)  =>  C_s = val^(-3/4)
        return val**-0.75
    raise ValueError(f"unknown filter_type: {filter_type}")


def _strain_integral_box(ck: float, n: int = 200_000) -> float:
    """<|Sbar|^2> Delta^(4/3) eps^(-2/3) for the box (top-hat) filter.

    Returns the dimensionless factor  val  such that
    <|Sbar|^2> = val * eps^(2/3) Delta^(-4/3).
    """
    # k from 0 to 40/Delta captures the sinc^2 tail; substitute chi = k Delta
    chi = np.linspace(1e-9, 200.0, n)
    sinc = np.sinc(chi / (2.0 * np.pi))  # np.sinc(x) = sin(pi x)/(pi x)
    integrand = 2.0 * ck * chi ** (1.0 / 3.0) * sinc**2
    return float(np.trapezoid(integrand, chi))


def ck_from_alpha(alpha: float) -> float:
    """Heisenberg closure: Kolmogorov constant implied by transfer constant alpha.

    Monograph ch. 5: nu_T(k) = alpha int_k^inf sqrt(E(q)/q^3) dq together with
    the constant-flux balance  eps = 2 (nu + nu_T) int_0^k q^2 E dq  gives,
    in the inertial range,  C_K = (8 / (9 alpha))^(2/3).
    """
    return (8.0 / (9.0 * alpha)) ** (2.0 / 3.0)


def alpha_from_ck(ck: float) -> float:
    """Inverse Heisenberg calibration: alpha = 8 / (9 C_K^(3/2))."""
    return 8.0 / (9.0 * ck**1.5)


def heisenberg_spectrum(
    k: np.ndarray, eps: float, nu: float, alpha: float
) -> np.ndarray:
    """Closed-form Heisenberg spectrum (monograph ch. 5, eq. (5.14)).

    E(k) = (alpha^2 / 4) eps^(1/4) nu^(5/4) chi^-7 [1 + (3 alpha^2 / 8) chi^-4]^(-4/3),
    chi = k eta, eta = (nu^3/eps)^(1/4).
    Inertial range: E ~ C_K eps^(2/3) k^(-5/3) with C_K = (8/9 alpha)^(2/3).
    Far dissipation range: E ~ k^(-7) (classical Heisenberg falloff).
    """
    k = np.asarray(k, dtype=float)
    eta = (nu**3 / eps) ** 0.25
    chi = k * eta
    with np.errstate(divide="ignore", invalid="ignore"):
        core = np.where(chi > 0, chi**-7.0, 0.0)
        bracket = 1.0 + 0.375 * alpha**2 * chi**-4.0
        bracket = np.where(chi > 0, bracket, np.inf)
    return (alpha**2 / 4.0) * eps**0.25 * nu**1.25 * core * bracket ** (-4.0 / 3.0)


def pao_beta(ck: float) -> float:
    """Pao-type exponent with exact dissipation normalization (ch. 5, eq. (5.18)).

    Requiring int 2 nu k^2 E dk = eps for  E = C_K eps^(2/3) k^(-5/3) exp(-beta chi^2)
    fixes  beta = (C_K Gamma(2/3))^(3/2).
    """
    return (ck * GAMMA_23) ** 1.5


def pao_spectrum(k: np.ndarray, eps: float, nu: float, ck: float) -> np.ndarray:
    """Pao-type spectrum with exact dissipation normalization.

    E(k) = C_K eps^(2/3) k^(-5/3) exp(-beta (k eta)^2).
    """
    k = np.asarray(k, dtype=float)
    eta = (nu**3 / eps) ** 0.25
    chi = k * eta
    beta = pao_beta(ck)
    power = np.where(k > 0, k ** (-5.0 / 3.0), 0.0)
    return ck * eps ** (2.0 / 3.0) * power * np.exp(-beta * chi**2)


# ---------------------------------------------------------------------------
# Numerics helpers shared by P3 / P4
# ---------------------------------------------------------------------------
def fit_kolmogorov_constant(
    k: np.ndarray, energy: np.ndarray, k_lo: float, k_hi: float
) -> tuple[float, float, float]:
    """Fit  E(k) = C_K eps^(2/3) k^(-5/3)  on [k_lo, k_hi] with known eps.

    Returns (C_K, slope, log_residual_rms). The slope is forced to -5/3 for
    C_K; the free slope is reported separately for diagnostics.
    """
    mask = (k >= k_lo) & (k <= k_hi) & (energy > 0)
    if mask.sum() < 4:
        return float("nan"), float("nan"), float("nan")
    x = np.log(k[mask])
    y = np.log(energy[mask])
    # free fit for the slope diagnostic
    slope, intercept = np.polyfit(x, y, 1)
    # constrained fit with slope = -5/3
    c_fix = float(np.mean(y + (5.0 / 3.0) * x))
    ck = float(np.exp(c_fix))
    resid = y - (-(5.0 / 3.0) * x + c_fix)
    return ck, float(slope), float(np.sqrt(np.mean(resid**2)))


def golden_mean() -> float:
    """Shell-model spacing lambda = (1 + sqrt(5)) / 2."""
    return 0.5 * (1.0 + math.sqrt(5.0))


def results_json_dump(obj: dict, path: str) -> None:
    """Write UTF-8 JSON with a stable key order for reproducible diffs."""
    import json

    with open(path, "w", encoding="utf-8") as fh:
        json.dump(obj, fh, indent=2, ensure_ascii=False, sort_keys=True)
        fh.write("\n")
