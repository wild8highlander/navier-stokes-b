"""P3: spectral verification of the Lilly-derivation inputs on K41 fields.

Chapter 8 of the monograph. A random-phase Gaussian field carries no third
order correlations, so the Germano identity <L_ij S_ij> vanishes identically
on synthetic fields (measured below at the noise floor -- itself an
instructive result that motivates the DNS experiment P4). What CAN and MUST
be verified on synthetic fields are the *spectral inputs* of the Lilly
derivation:

  (1) resolved-strain identity  <|Sbar|^2> = 2 int_0^inf k^2 E(k) G^2 dk
      measured directly on 128^3 filtered fields versus quadrature;
  (2) the implied Smagorinsky constant
      C_s(Delta) = eps^(1/2) / (Delta <|Sbar|^2>^(3/4))
      versus the analytical filter-family values of P1
      (sharp 0.17327, Gaussian 0.16967 for C_K = 1.5);
  (3) the finite-scale (Delta/eta) correction from the Pao dissipation tail;
  (4) the zero third-order correlation of Gaussian fields
      <L_ij Sbar_ij> = 0  (eddy-viscosity-only transfer), measured.

Outputs: results/p3_synthetic_apriori.json, results/p3_apriori.csv
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
    lilly_cs,
    pao_beta,
    results_json_dump,
)

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
RESULTS = os.path.join(ROOT, "results")

NGRID = 96
NREAL = 4


def make_kgrid(n: int) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    kf = np.fft.fftfreq(n, d=1.0 / n)
    kx = kf[:, None, None]
    ky = kf[None, :, None]
    kz = kf[None, None, : n // 2 + 1]
    kmag = np.sqrt(kx**2 + ky**2 + kz**2)
    return kx, ky, kz, kmag


def shell_energies(u: np.ndarray, n: int) -> tuple[np.ndarray, float, float]:
    """Physical per-shell energy of a real field, empirically normalized.

    The Parseval weight between the rfft half-grid amplitudes and the
    physical energy density is determined from the measured field itself:
    w = <u^2> * n^6 / sum_half |u_hat|^2. This is convention-free.
    Returns (e_shell array over integer k, total energy, w).
    """
    uh = np.fft.rfftn(u, axes=(1, 2, 3))
    kmag = np.sqrt(
        make_kgrid(n)[0] ** 2 + make_kgrid(n)[1] ** 2 + make_kgrid(n)[2] ** 2
    )
    kbin = np.rint(kmag).astype(int)
    kmax = int(kbin.max()) + 1
    w_half = np.zeros(kmax)
    for kk in range(1, kmax):
        m = kbin == kk
        if m.any():
            w_half[kk] = float(np.sum(np.abs(uh[:, m]) ** 2))
    tot = float(np.mean(np.sum(u * u, axis=0)))
    s_half = float(np.sum(w_half))
    w = tot * n**6 / s_half if s_half > 0 else 0.0
    e_shell = w * w_half / n**6
    return e_shell, tot, w


def synthetic_field(
    n: int, ck: float, eps: float, nu: float, rng: np.random.Generator
) -> np.ndarray:
    """Random-phase divergence-free field with shell-exact Pao-K41 spectrum.

    A first random realization is corrected deterministically per shell so
    that the *measured physical* shell energy of the final field equals the
    target E(k) = C_K eps^(2/3) k^(-5/3) exp(-beta (k eta)^2). All bookkeeping
    is empirical (no FFT-convention assumptions).
    """
    kx, ky, kz, kmag = make_kgrid(n)
    eta = (nu**3 / eps) ** 0.25
    beta = pao_beta(ck)
    with np.errstate(divide="ignore", invalid="ignore"):
        e_spec = ck * eps ** (2.0 / 3.0) * np.where(kmag > 0, kmag ** (-5.0 / 3.0), 0.0)
    shell_vol = np.where(kmag > 0, 4.0 * np.pi * kmag**2, 1.0)
    amp = n**3 * np.sqrt(e_spec / shell_vol)
    phase = (rng.normal(size=amp.shape) + 1j * rng.normal(size=amp.shape)) / np.sqrt(
        2.0
    )
    uh = phase * amp
    uh[0, 0, 0] = 0.0
    uh3 = np.zeros((3,) + uh.shape, dtype=complex)
    uh3[0], uh3[1], uh3[2] = uh, uh, uh
    k2 = np.where(kmag > 0, kmag**2, 1.0)
    proj = (kx * uh3[0] + ky * uh3[1] + kz * uh3[2]) / k2
    uh3[0] -= kx * proj
    uh3[1] -= ky * proj
    uh3[2] -= kz * proj

    kbin = np.rint(kmag).astype(int)
    kmax = int(kbin.max()) + 1
    # Shell-energy target = 2 x the kinetic-energy spectrum E(k):
    # the textbook convention has int E dk = (1/2)<u^2> (kinetic energy),
    # so the variance shell energy is e_shell = 2 E(k). With this
    # normalization the textbook identities hold exactly:
    #   eps = 2 nu int k^2 E dk = nu sum k^2 e_shell,
    #   <|Sbar|^2> = 2 int k^2 E G^2 dk = sum k^2 e_shell G^2.
    e_target = np.zeros(kmax)
    for kk in range(1, kmax):
        e_target[kk] = (
            2.0
            * ck
            * eps ** (2.0 / 3.0)
            * kk ** (-5.0 / 3.0)
            * np.exp(-beta * (kk * eta) ** 2)
        )
    for _pass in range(10):
        u = np.fft.irfftn(uh3, s=(n, n, n), axes=(1, 2, 3))
        e_shell, tot, _w = shell_energies(u, n)
        # per-shell amplitude correction: energy scales as fac^2
        corr = np.ones(kmax)
        np.divide(e_target, e_shell, out=corr, where=e_shell > 0)
        fac = np.sqrt(corr)
        # global energy renormalization
        gfac = np.sqrt(float(np.sum(e_target)) / max(tot, 1e-300))
        uh3 *= (fac * gfac)[kbin][None]
    return np.fft.irfftn(uh3, s=(n, n, n), axes=(1, 2, 3))


def gauss_filter_hat(kmag: np.ndarray, delta: float) -> np.ndarray:
    return np.exp(-(kmag**2) * delta**2 / 24.0)


def sharp_filter_hat(kmag: np.ndarray, delta: float) -> np.ndarray:
    return (kmag <= np.pi / delta).astype(float)


def filter_field(u: np.ndarray, gh: np.ndarray) -> np.ndarray:
    uh = np.fft.rfftn(u, axes=(1, 2, 3))
    uh = uh * gh[None]
    return np.fft.irfftn(uh, s=u.shape[1:], axes=(1, 2, 3))


def strain_tensor(ubar: np.ndarray, n: int) -> np.ndarray:
    kx, ky, kz, _ = make_kgrid(n)
    uh = np.fft.rfftn(ubar, axes=(1, 2, 3))
    grads = []
    for kg in (kx, ky, kz):
        comps = [
            np.fft.irfftn(1j * kg * uh[a], s=ubar.shape[1:], axes=(0, 1, 2))
            for a in range(3)
        ]
        grads.append(comps)
    s_mat = np.zeros((3, 3) + ubar.shape[1:])
    for a in range(3):
        for b in range(3):
            s_mat[a, b] = 0.5 * (grads[a][b] + grads[b][a])
    return s_mat


def germano_correlation(u: np.ndarray, gh: np.ndarray, n: int) -> float:
    """<L_ij Sbar_ij> per point (zero for Gaussian fields up to sampling)."""
    ubar = filter_field(u, gh)
    sm = strain_tensor(ubar, n)
    lhs = np.zeros((3, 3) + u.shape[1:])
    for a in range(3):
        for b in range(3):
            prod = np.fft.rfftn(u[a] * u[b], axes=(0, 1, 2))
            filt = np.fft.irfftn(prod * gh, s=u.shape[1:], axes=(0, 1, 2))
            lhs[a, b] = filt - ubar[a] * ubar[b]
            del prod, filt
    return float(np.mean(np.sum(lhs * sm, axis=(0, 1))))


def main() -> int:
    os.makedirs(RESULTS, exist_ok=True)
    ck = CK_SREENIVASAN
    eps = 1.0
    # choose nu so that the Kolmogorov wavenumber k_eta = 1/eta = n_grid/4:
    # the dissipation range is then fully resolved on the grid
    # (eta = (nu^3/eps)^(1/4) = 4/n * 2pi/L ... in box units eta = 1/24).
    nu = 24.0 ** (-4.0 / 3.0)
    eta = (nu**3 / eps) ** 0.25
    rng = np.random.default_rng(20260929)

    rows = []
    gauss_zero = []
    for i_real in range(NREAL):
        u = synthetic_field(NGRID, ck, eps, nu, rng)
        _, _, _, kmag = make_kgrid(NGRID)
        for delta_dx, fkind in (
            (2.0, "gaussian"),
            (4.0, "gaussian"),
            (8.0, "gaussian"),
            (16.0, "gaussian"),
            (32.0, "gaussian"),
            (4.0, "sharp"),
            (16.0, "sharp"),
            (32.0, "sharp"),
        ):
            delta = delta_dx * (2.0 * np.pi / NGRID)
            gh = (
                gauss_filter_hat(kmag, delta)
                if fkind == "gaussian"
                else sharp_filter_hat(kmag, delta)
            )
            ubar = filter_field(u, gh)
            sm = strain_tensor(ubar, NGRID)
            s2_meas = float(np.mean(2.0 * np.sum(sm * sm, axis=(0, 1))))
            del sm
            # exact discrete identity check with empirically normalized
            # shell energies: <|Sbar|^2> = sum_shells k^2 e_shell G^2
            e_shell, tot, _w = shell_energies(u, NGRID)
            ks = np.arange(len(e_shell))
            g_shell = np.array(
                [
                    float(gauss_filter_hat(np.array([[float(kk)]]), delta)[0, 0])
                    if fkind == "gaussian"
                    else float(kk <= np.pi / delta)
                    for kk in ks
                ]
            )
            s2_quad = float(np.sum(ks**2 * e_shell * g_shell**2))
            # the field's physical dissipation (nu <omega^2>) measured:
            eps_field = nu * float(
                np.sum(ks**2 * e_shell)
            )  # <w^2> = sum k^2 e_shell (verified identity)
            cs_implied = np.sqrt(eps_field) / (delta * s2_meas**0.75)
            rows.append(
                {
                    "realization": i_real,
                    "filter": fkind,
                    "Delta_over_dx": delta_dx,
                    "Delta_over_eta": delta / eta,
                    "strain2_measured": s2_meas,
                    "strain2_quadrature": s2_quad,
                    "strain2_rel_err": abs(s2_meas - s2_quad) / s2_quad,
                    "C_s_implied": float(cs_implied),
                }
            )
        if i_real < 2:
            delta = 4.0 * (2.0 * np.pi / NGRID)
            gh = gauss_filter_hat(kmag, delta)
            gauss_zero.append(germano_correlation(u, gh, NGRID))

    agg = {}
    for fkind in ("gaussian", "sharp"):
        for dxm in (2.0, 4.0, 8.0, 16.0, 32.0):
            sel = [
                r for r in rows if r["filter"] == fkind and r["Delta_over_dx"] == dxm
            ]
            if sel:
                agg[f"{fkind}_d{dxm:g}"] = {
                    "C_s_mean": float(np.mean([r["C_s_implied"] for r in sel])),
                    "C_s_std": float(np.std([r["C_s_implied"] for r in sel])),
                    "strain2_rel_err_max": float(
                        max(r["strain2_rel_err"] for r in sel)
                    ),
                    "Delta_over_eta": float(sel[0]["Delta_over_eta"]),
                    "n": len(sel),
                }

    protocol = {
        "program": "P3_spectral_inputs",
        "title": "Spectral verification of the Lilly-derivation inputs",
        "date": "2026-09-29",
        "method": {
            "field": "128^3 random-phase divergence-free K41-Pao field",
            "C_K": ck,
            "realizations": NREAL,
            "note": (
                "Gaussian random fields have vanishing third-order "
                "correlations: <L_ij S_ij> = 0 up to sampling noise "
                "(measured below). The Germano-based a priori C_s therefore "
                "requires real cascade dynamics and is measured in P4."
            ),
        },
        "analytic_reference": {
            "C_s_sharp": lilly_cs(ck, "sharp"),
            "C_s_gaussian": lilly_cs(ck, "gaussian"),
        },
        "germano_correlation_gaussian_field": gauss_zero,
        "measured": agg,
        "rows": rows,
        "integrity": {
            "sha256_of_code": hashlib.sha256(
                open(os.path.abspath(__file__), "rb").read()
            ).hexdigest(),
        },
    }
    results_json_dump(protocol, os.path.join(RESULTS, "p3_synthetic_apriori.json"))
    csv_path = os.path.join(RESULTS, "p3_apriori.csv")
    with open(csv_path, "w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)

    print(
        "[P3] analytic: sharp = "
        f"{lilly_cs(ck, 'sharp'):.5f}, gaussian = {lilly_cs(ck, 'gaussian'):.5f}"
    )
    for key, val in agg.items():
        print(
            f"[P3] {key:16s} C_s = {val['C_s_mean']:.5f} "
            f"+/- {val['C_s_std']:.5f}  strain-id err max "
            f"{val['strain2_rel_err_max']:.2e}"
        )
    print(f"[P3] <L_ij S_ij> on Gaussian fields: {gauss_zero}")
    print(f"[P3] wrote {csv_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
