"""P5-C: stretching statistics — ensemble of random fields versus DNS.

Chapter 12 of the monograph, the third block of the P5 smoothness program
(user-requested extension: an ensemble of random fields for the vortex
stretching statistics). Three families of divergence-free fields on the
same 96^3 grid are compared with the SAME scale-free statistics:

  GAU  M=32 Gaussian random-phase fields with the shell-exact Pao-K41
       spectrum (the P3 generator algorithm, vectorized; eps from the
       96^3 DNS) — the parameter-free random baseline;
  DNS  Taylor-Green 96^3 snapshots (P5-B run A96) at t = 4, 5, 6 —
       real dynamics near and past the enstrophy peak;
  SUR  M=8 random-phase surrogates of the t = 5 DNS snapshot (|u_hat|
       preserved per mode, phases randomized, Leray-projected,
       energy-renormalized) — same spectral content, destroyed phase
       structure.

Statistics per field (all dimensionless, scale-free):
  (1) strain eigenvalues of S_ij at every grid point (ascending ->
      descending), normalized by s_rms = <S_ij S_ij>^(1/2):
      mean lambda_i / s_rms, the intermediate invariant
      beta_S = <lambda_2> / (<lambda_1> - <lambda_3>);
  (2) alignment of vorticity with the strain eigenvectors:
      cos(theta_i) = (omega_hat . e_i), PDFs on [-1, 1] and <cos^2>;
  (3) normalized stretching rate
      alpha = (omega_i S_ij omega_j) / (|omega|^2 s_rms), PDF on [-3, 3].

Additional verifications:
  * GAU ensemble-mean shell spectrum matches the Pao-K41 target
    (deviation = chi-square sampling noise of 32 realizations);
  * GAU alignment null check: an exactly Gaussian field has (omega, S)
    independent, hence <cos^2 theta_i> = 1/3 — a built-in unit test of
    the alignment pipeline (note: the shell-EXACT P3 generator, which
    conditions the ensemble on pinned shell energies, VIOLATES this
    null model and produces spurious alignment — the reason the
    one-shot generator is used here);
  * SUR spectrum matches the DNS spectrum shell-by-shell;
  * f64-vs-f32 storage robustness of every statistic on the t = 5 field;
  * cross-language reference block: scalar statistics of two 48^3
    artifacts (Gaussian reference field p5c_gauss_ref_u.f64 and the P5
    snapshot p5_snapshot_u.f64) recomputed by C++/Julia in
    p5c_crosscheck.py, plus the GOE Monte-Carlo of the Gaussian
    eigenvalue baseline.

Outputs: results/p5c_stretch_ensemble.json, results/p5c_pdfs.csv,
         results/p5c_summary.csv, results/p5c_gauss_ref_u.f64
"""

from __future__ import annotations

import csv
import hashlib
import json
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from sk_core import CK_SREENIVASAN, pao_beta, results_json_dump  # noqa: E402
from p5_regularity import wavevectors  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
RESULTS = os.path.join(ROOT, "results")

N = 96
NU = 0.01
M_GAU = 32
M_SUR = 8
EPS_FALLBACK = 0.011963943  # 48^3 P5 run A, used if the 96^3 JSON is absent
SEED_GAU = 20260930
SEED_SUR = 20261001
SEED_REF48 = 20260929
ALIGN_BINS = 21   # cos(theta_i) on [-1, 1]
ALPHA_BINS = 41   # alpha on [-3, 3]
SUR_SHELL_BAND = (1, 16)  # spectrum-match verification band


# ---------------------------------------------------------------------------
# fields
# ---------------------------------------------------------------------------
def make_kgrid(n: int) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    kf = np.fft.fftfreq(n, d=1.0 / n)
    kx = kf[:, None, None]
    ky = kf[None, :, None]
    kz = kf[None, None, : n // 2 + 1]
    kmag = np.sqrt(kx**2 + ky**2 + kz**2)
    return kx, ky, kz, kmag


def synthetic_field_vec(
    n: int, ck: float, eps: float, nu: float, rng: np.random.Generator
) -> np.ndarray:
    """P3's synthetic_field with the shell bookkeeping vectorized.

    Same algorithm and normalization: random-phase divergence-free field
    whose *measured physical* shell energy equals the Pao-K41 target
    e_shell = 2 C_K eps^(2/3) k^(-5/3) exp(-beta (k eta)^2); 10 passes of
    per-shell amplitude correction with an empirical Parseval weight
    (convention-free). The bincount replaces the per-shell boolean loop —
    bit-level rounding differs from P3's version, hence the equivalence
    check below compares measured spectra and the field correlation.
    """
    kx, ky, kz, kmag = make_kgrid(n)
    eta = (nu**3 / eps) ** 0.25
    beta = pao_beta(ck)
    with np.errstate(divide="ignore", invalid="ignore"):
        e_spec = ck * eps ** (2.0 / 3.0) * np.where(kmag > 0, kmag ** (-5.0 / 3.0), 0.0)
    shell_vol = np.where(kmag > 0, 4.0 * np.pi * kmag**2, 1.0)
    amp = n**3 * np.sqrt(e_spec / shell_vol)
    phase = (rng.normal(size=amp.shape) + 1j * rng.normal(size=amp.shape)) / np.sqrt(2.0)
    uh = phase * amp
    uh[0, 0, 0] = 0.0
    uh3 = np.empty((3,) + uh.shape, dtype=complex)
    uh3[0], uh3[1], uh3[2] = uh, uh, uh
    # Hermitian consistency on the self-paired kz = 0 and kz = n/2 planes:
    # a real field demands F(-k) = conj(F(k)); on these planes both partners
    # live on the half-grid, so independent phases break the symmetry — the
    # inverse transform silently symmetrizes them and both the div-free
    # residual and the measured spectrum degrade. Symmetrize BEFORE the
    # projection loop.
    # kz = 0 plane: enforce F(-k) = conj(F(k)) with the correct partner map
    # (n - i) mod n on the kx/ky axes only
    p = uh3[:, :, :, 0]
    partner = np.roll(p[:, ::-1, ::-1], 1, axis=(1, 2))
    uh3[:, :, :, 0] = 0.5 * (p + np.conj(partner))
    # kz = n/2 plane and the kx/ky Nyquist columns of the kz = 0 plane:
    # the Nyquist frequency n/2 is its own negation mod n, so the Leray
    # coefficient k_a/k^2 cannot be made consistent between a mode and its
    # conjugate partner (the kz-derivative flips sign). Their Pao-tail
    # energy is ~1e-10 relative — zeroed for exact consistency.
    nz = n // 2
    uh3[:, :, :, nz] = 0.0
    uh3[:, nz, :, 0] = 0.0
    uh3[:, :, nz, 0] = 0.0
    k2 = np.where(kmag > 0, kmag**2, 1.0)
    proj = (kx * uh3[0] + ky * uh3[1] + kz * uh3[2]) / k2
    for a in range(3):
        uh3[a] -= (kx, ky, kz)[a] * proj

    kbin2 = np.rint(kmag).astype(int)          # (n, n, n//2+1) for indexing
    kbin = kbin2.ravel()                       # flat for bincount
    kmax = int(kbin.max()) + 1
    kk_axis = np.arange(kmax, dtype=float)
    with np.errstate(divide="ignore"):
        e_target = 2.0 * ck * eps ** (2.0 / 3.0) * np.where(
            kk_axis > 0, kk_axis ** (-5.0 / 3.0), 0.0
        ) * np.exp(-beta * (kk_axis * eta) ** 2)
    e_target[0] = 0.0

    def shell_measured(uh_in: np.ndarray, u_phys: np.ndarray) -> np.ndarray:
        """Empirical per-shell physical energy of a real field."""
        amp2 = np.sum(np.abs(uh_in) ** 2, axis=0).ravel()
        w_half = np.bincount(kbin, weights=amp2, minlength=kmax)
        tot = float(np.mean(np.sum(u_phys * u_phys, axis=0)))
        s_half = float(np.sum(w_half))
        w = tot * n**6 / s_half if s_half > 0 else 0.0
        return w * w_half / n**6

    for _pass in range(10):
        u = np.fft.irfftn(uh3, s=(n, n, n), axes=(1, 2, 3))
        e_shell = shell_measured(uh3, u)
        corr = np.ones(kmax)
        np.divide(e_target, e_shell, out=corr, where=e_shell > 0)
        np.sqrt(corr, out=corr)  # amplitude = sqrt(energy ratio)
        # per-shell amplitude correction only: e_shell_new = e_target * tot_new/Σe_target,
        # the SHAPE converges in one pass; combining it with a global factor
        # inside the loop (as P3 did) creates a harmless 2-cycle in the
        # absolute normalization — irrelevant for P3's scale-free outputs,
        # so here the absolute level is fixed once, after the shape passes.
        uh3 *= corr[kbin2][None]
    # exact global energy normalization (uniform scaling, shape preserved)
    u = np.fft.irfftn(uh3, s=(n, n, n), axes=(1, 2, 3))
    e_shell = shell_measured(uh3, u)
    gfac = np.sqrt(float(np.sum(e_target)) / max(float(np.sum(e_shell)), 1e-300))
    uh3 *= gfac
    return np.fft.irfftn(uh3, s=(n, n, n), axes=(1, 2, 3))


def gaussian_field_oneshot(
    n: int, ck: float, eps: float, nu: float, rng: np.random.Generator
) -> np.ndarray:
    """Exactly Gaussian isotropic incompressible field, one-shot synthesis.

    Mode amplitudes follow the Pao-K41 shell target deterministically,
    coefficients are iid complex Gaussian; no realization-level constraint
    is imposed (per-shell energies fluctuate chi-square around the target —
    sampling noise, not bias). This matters: the shell-EXACT correction of
    the P3 generator conditions the ensemble on pinned shell energies, and
    a conditional Gaussian is no longer Gaussian in its omega-S cross
    structure — it produces SPURIOUS vorticity-strain alignment. The exact
    Gaussian baseline here is the null model: (omega, S) jointly Gaussian
    with zero cross-covariance (isotropy forbids a chiral second moment)
    hence independent, hence a FLAT alignment PDF P(cos theta_i) = 1/2 and
    <cos^2 theta_i> = 1/3 — a built-in unit test of the alignment pipeline.
    A single global rescale sets the measured total energy to the target
    sum (uniform scaling preserves Gaussianity exactly).
    """
    kx, ky, kz, kmag = make_kgrid(n)
    eta = (nu**3 / eps) ** 0.25
    beta = pao_beta(ck)
    kk_axis = np.arange(int(kmag.max()) + 2, dtype=float)
    with np.errstate(divide="ignore"):
        e_target = 2.0 * ck * eps ** (2.0 / 3.0) * np.where(
            kk_axis > 0, kk_axis ** (-5.0 / 3.0), 0.0
        ) * np.exp(-beta * (kk_axis * eta) ** 2)
    kbin2 = np.rint(kmag).astype(int)
    kbin = kbin2.ravel()
    n_half = np.bincount(kbin, minlength=len(kk_axis)).astype(float)
    n_half[0] = 1.0  # avoid div by zero; mean mode is zeroed anyway
    amp = n**3 * np.sqrt(e_target / (2.0 * n_half))[kbin2]
    # THREE INDEPENDENT complex-Gaussian draws per component. Sharing one
    # draw across components (as the P3 generator did) gives every mode the
    # fixed polarization P(k)(1,1,1) instead of a Haar-random one — the
    # ensemble stays shell-isotropic on average (trace P = 2) but is
    # anisotropic at fourth order, which fakes vorticity-strain alignment.
    uh3 = np.empty((3,) + amp.shape, dtype=complex)
    for a in range(3):
        ph_a = (rng.normal(size=amp.shape) + 1j * rng.normal(size=amp.shape)) / np.sqrt(2.0)
        uh3[a] = ph_a * amp
    uh3[:, 0, 0, 0] = 0.0
    # Hermitian consistency of the self-paired kz = 0 plane ...
    p = uh3[:, :, :, 0]
    partner = np.roll(p[:, ::-1, ::-1], 1, axis=(1, 2))
    uh3[:, :, :, 0] = 0.5 * (p + np.conj(partner))
    # ... and removal of the Nyquist-degenerate set (see below)
    nz = n // 2
    uh3[:, :, :, nz] = 0.0
    uh3[:, nz, :, 0] = 0.0
    uh3[:, :, nz, 0] = 0.0
    # the symmetrized kz=0 modes carry half the variance of interior modes
    # (0.5(p + conj(partner)) of two iid Gaussians) — compensate with sqrt(2)
    # so that every shell has the target expected energy
    uh3[:, :, :, 0] *= np.sqrt(2.0)
    k2 = np.where(kmag > 0, kmag**2, 1.0)
    proj = (kx * uh3[0] + ky * uh3[1] + kz * uh3[2]) / k2
    for a in range(3):
        uh3[a] -= (kx, ky, kz)[a] * proj
    u = np.fft.irfftn(uh3, s=(n, n, n), axes=(1, 2, 3))
    tot = float(np.mean(np.sum(u * u, axis=0)))
    u *= np.sqrt(float(np.sum(e_target)) / max(tot, 1e-300))
    return u


def phase_surrogate(u: np.ndarray, rng: np.random.Generator) -> np.ndarray:
    """Random-phase surrogate on the FULL grid, structure-preserving.

    u_hat'(k) = exp(i phi'(k)) u_hat(k) with a scalar, antisymmetric
    random phase phi'(-k) = -phi'(k) = (phi(k) - phi(-k))/2. A scalar
    phase preserves the polarization (div-freeness) and the magnitude of
    EVERY Fourier mode exactly; antisymmetry preserves Hermitian
    consistency, so the surrogate is a real, divergence-free field with
    the DNS energy spectrum reproduced bit-exactly. Self-paired modes
    (k = -k mod n) automatically get phi' = 0, as required for real
    coefficients. No projection needed.
    """
    n = u.shape[1]
    U = np.fft.fftn(u, axes=(1, 2, 3))
    ph = rng.uniform(0.0, 2.0 * np.pi, size=U.shape[1:])
    ph_anti = 0.5 * (
        ph - np.roll(ph[::-1, ::-1, ::-1], 1, axis=(0, 1, 2))
    )
    U2 = U * np.exp(1j * ph_anti)[None]
    U2[:, 0, 0, 0] = 0.0
    return np.fft.ifftn(U2, axes=(1, 2, 3)).real


# ---------------------------------------------------------------------------
# statistics
# ---------------------------------------------------------------------------
def strain_eig_and_stats(u: np.ndarray) -> dict:
    """All scale-free stretching statistics of one divergence-free field."""
    n = u.shape[1]
    kx, ky, kz, _ = make_kgrid(n)
    kv = (kx, ky, kz)
    uh = [np.fft.rfftn(u[a], axes=(0, 1, 2)) for a in range(3)]

    def phys(arr: np.ndarray) -> np.ndarray:
        return np.fft.irfftn(arr, s=(n, n, n), axes=(0, 1, 2))

    # velocity gradient G[a][b] = d_b u_a
    G = [[None] * 3 for _ in range(3)]
    for a in range(3):
        for b in range(3):
            G[a][b] = phys(1j * kv[b] * uh[a])
    # strain components
    S = [[None] * 3 for _ in range(3)]
    for a in range(3):
        for b in range(3):
            S[a][b] = 0.5 * (G[a][b] + G[b][a])
    # vorticity
    wh = np.stack(
        [
            1j * (ky * uh[2] - kz * uh[1]),
            1j * (kz * uh[0] - kx * uh[2]),
            1j * (kx * uh[1] - ky * uh[0]),
        ]
    )
    w = np.stack([phys(wh[a]) for a in range(3)])
    w2 = w[0] ** 2 + w[1] ** 2 + w[2] ** 2

    # assemble S as (n^3, 3, 3)
    npt = n**3
    Sfull = np.empty((3, 3, npt), dtype=np.float64)
    for a in range(3):
        for b in range(3):
            Sfull[a, b] = S[a][b].ravel()
    Sfull = np.moveaxis(Sfull, -1, 0)  # (npt, 3, 3)
    ss = np.einsum("nij,nij->n", Sfull, Sfull)
    s_rms = float(np.sqrt(np.mean(ss)))

    eigvals, eigvecs = np.linalg.eigh(Sfull)  # ascending
    lam = eigvals[:, ::-1] / s_rms  # descending, normalized
    vec = np.moveaxis(eigvecs[:, :, ::-1], -1, 0).copy()  # (3, npt, 3)

    wn = np.stack([w[a].ravel() for a in range(3)], axis=1)  # (npt, 3)
    wn_norm = np.linalg.norm(wn, axis=1)
    w_hat = wn / np.maximum(wn_norm[:, None], 1e-300)

    cos = np.empty((3, npt))
    for i in range(3):
        cos[i] = np.einsum("nj,nj->n", w_hat, vec[i])
    cos2 = [float(np.mean(cos[i] ** 2)) for i in range(3)]

    # stretching rate omega_i S_ij omega_j, normalized
    wSw = np.einsum("ni,nij,nj->n", wn, Sfull, wn)
    alpha = wSw / np.maximum(wn_norm**2, 1e-300) / s_rms

    edges_a = np.linspace(-1.0, 1.0, ALIGN_BINS + 1)
    pdf_cos = [np.histogram(cos[i], bins=edges_a, density=True)[0] for i in range(3)]
    centers_a = 0.5 * (edges_a[1:] + edges_a[:-1])
    edges_al = np.linspace(-3.0, 3.0, ALPHA_BINS + 1)
    pdf_alpha = np.histogram(np.clip(alpha, -2.999, 2.999), bins=edges_al, density=True)[0]
    centers_al = 0.5 * (edges_al[1:] + edges_al[:-1])

    mean_l = [float(np.mean(lam[:, i])) for i in range(3)]
    beta_s = mean_l[1] / (mean_l[0] - mean_l[2])
    return {
        "s_rms": s_rms,
        "mean_lam": mean_l,
        "ratio_lambda": [mean_l[0] / -mean_l[2], mean_l[1] / -mean_l[2], 1.0],
        "beta_S": float(beta_s),
        "cos2": cos2,
        "pdf_cos": pdf_cos,
        "pdf_cos_centers": centers_a,
        "alpha_mean": float(np.mean(alpha)),
        "alpha_std": float(np.std(alpha)),
        "pdf_alpha": pdf_alpha,
        "pdf_alpha_centers": centers_al,
        "pdf_alpha_peak": float(pdf_alpha.max()),
    }


def strain_and_vorticity(u: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """Spectral strain (6 independent comps) and vorticity of a real field.

    Returns T shape (9, n, n, n) ordered
    [Sxx, Syy, Szz, Sxy, Sxz, Syz, wx, wy, wz].
    """
    n = u.shape[1]
    kx, ky, kz, _ = make_kgrid(n)
    kv = (kx, ky, kz)
    uh = [np.fft.rfftn(u[a], axes=(0, 1, 2)) for a in range(3)]

    def phys(arr):
        return np.fft.irfftn(arr, s=(n, n, n), axes=(0, 1, 2))

    G = [[None] * 3 for _ in range(3)]
    for a in range(3):
        for b in range(3):
            G[a][b] = phys(1j * kv[b] * uh[a])
    T = np.empty((9, n, n, n), dtype=np.float64)
    T[0] = G[0][0]
    T[1] = G[1][1]
    T[2] = G[2][2]
    T[3] = 0.5 * (G[0][1] + G[1][0])
    T[4] = 0.5 * (G[0][2] + G[2][0])
    T[5] = 0.5 * (G[1][2] + G[2][1])
    T[6] = phys(1j * (ky * uh[2] - kz * uh[1]))
    T[7] = phys(1j * (kz * uh[0] - kx * uh[2]))
    T[8] = phys(1j * (kx * uh[1] - ky * uh[0]))
    return T


def export_tensors(u: np.ndarray, path: str) -> None:
    """Write (S, omega) point tensors for the C++/Julia statistics track.

    Layout on disk: POINT-major (n, n, n, 9) C-order, i.e. flat offset
    point*9 + channel — one point's nine numbers are contiguous, which is
    the natural layout for the row-major C++ reader and the column-major
    Julia reshape(n, n, n, 9) alike.
    """
    strain_and_vorticity(u).transpose(1, 2, 3, 0).tofile(path)


def scalar_subset(st: dict) -> dict:
    """Compact scalar block used for cross-language comparison."""
    return {
        "s_rms": st["s_rms"],
        "mean_lam": st["mean_lam"],
        "beta_S": st["beta_S"],
        "cos2": st["cos2"],
        "alpha_mean": st["alpha_mean"],
        "alpha_std": st["alpha_std"],
    }


def rel_dev_block(ref: dict, other: dict, keys: tuple = ("s_rms", "beta_S", "alpha_mean", "alpha_std")) -> dict:
    out = {}
    for k in keys:
        r, o = ref[k], other[k]
        out[k] = abs(o - r) / max(abs(r), 1e-300)
    for k in ("mean_lam", "cos2"):
        out[k] = max(
            abs(o - r) / max(abs(r), 1e-300) for r, o in zip(ref[k], other[k])
        )
    return out


# ---------------------------------------------------------------------------
# experiment driver
# ---------------------------------------------------------------------------
def load_eps_96() -> float:
    path = os.path.join(RESULTS, "p5b_resolution_96.json")
    if os.path.exists(path):
        with open(path, encoding="utf-8") as fh:
            d = json.load(fh)
        return float(d["run_A96_summary"]["eps_mean_stat"])
    return EPS_FALLBACK


def main() -> int:
    os.makedirs(RESULTS, exist_ok=True)
    if "--export-tensors" in sys.argv:
        for tag, fname in (
            ("gauss", "p5c_gauss_ref_u.f64"),
            ("dns", "p5_snapshot_u.f64"),
        ):
            src = os.path.join(RESULTS, fname)
            n = 48
            u = np.fromfile(src, dtype=np.float64).reshape(3, n, n, n)
            out = os.path.join(RESULTS, f"p5c_tensors_{tag}.f64")
            export_tensors(u, out)
            print(f"[P5-C] wrote {out}")
        return 0
    eps_dns = load_eps_96()

    fam: dict[str, list[dict]] = {}

    # ---- GAU ensemble ------------------------------------------------------
    print(f"[P5-C] GAU ensemble: {M_GAU} fields, 96^3, eps = {eps_dns:.6f}", flush=True)
    rng = np.random.default_rng(SEED_GAU)
    gau = []
    e_shell_acc = np.zeros(N + 1)
    for i in range(M_GAU):
        u = gaussian_field_oneshot(N, CK_SREENIVASAN, eps_dns, NU, rng)
        st = strain_eig_and_stats(u)
        gau.append(st)
        # ensemble-mean shell spectrum for the generator verification
        kxg, kyg, kzg, kmagg = make_kgrid(N)
        uhg = np.fft.rfftn(u, axes=(1, 2, 3))
        kbg = np.rint(kmagg).astype(int).ravel()
        w_h = np.bincount(
            kbg, weights=np.sum(np.abs(uhg) ** 2, axis=0).ravel(), minlength=N + 1
        )
        totg = float(np.mean(np.sum(u * u, axis=0)))
        e_shell_acc += w_h * totg * N**6 / np.sum(w_h) / N**6
        if (i + 1) % 8 == 0:
            print(f"    GAU {i + 1}/{M_GAU} done", flush=True)
    fam["GAU"] = gau
    e_shell_ens = e_shell_acc / M_GAU
    kk_ax = np.arange(N + 1, dtype=float)
    eta_dns = (NU**3 / eps_dns) ** 0.25
    with np.errstate(divide="ignore"):
        e_tgt_ens = 2.0 * CK_SREENIVASAN * eps_dns ** (2.0 / 3.0) * np.where(
            kk_ax > 0, kk_ax ** (-5.0 / 3.0), 0.0
        ) * np.exp(-pao_beta(CK_SREENIVASAN) * (kk_ax * eta_dns) ** 2)
    ens_dev = np.abs(e_shell_ens[1:17] - e_tgt_ens[1:17]) / e_tgt_ens[1:17]
    ens_spec_dev = float(np.max(ens_dev))
    print(f"[P5-C] GAU ensemble-mean spectrum max dev (1..16): {ens_spec_dev:.2e}", flush=True)

    # ---- DNS snapshots -----------------------------------------------------
    dns = []
    for ts in (4.0, 5.0, 6.0):
        path = os.path.join(RESULTS, f"p5b_snap_u_t{ts:g}.f64")
        u = np.fromfile(path, dtype=np.float64).reshape(3, N, N, N)
        st = strain_eig_and_stats(u)
        dns.append(st)
        print(f"    DNS t={ts:g} done", flush=True)
    fam["DNS_t4"], fam["DNS_t5"], fam["DNS_t6"] = [dns[0]], [dns[1]], [dns[2]]

    # ---- SUR ensemble ------------------------------------------------------
    print(f"[P5-C] SUR ensemble: {M_SUR} surrogates of DNS t=5", flush=True)
    u5 = np.fromfile(os.path.join(RESULTS, "p5b_snap_u_t5.f64"), dtype=np.float64).reshape(3, N, N, N)
    rng_s = np.random.default_rng(SEED_SUR)
    sur = []
    for i in range(M_SUR):
        u = phase_surrogate(u5, rng_s)
        st = strain_eig_and_stats(u)
        sur.append(st)
    fam["SUR"] = sur
    kb = np.rint(make_kgrid(N)[3]).astype(int).ravel()

    def shell_e(uu: np.ndarray) -> np.ndarray:
        uh2 = np.sum(np.abs(np.fft.rfftn(uu, axes=(1, 2, 3))) ** 2, axis=0).ravel()
        w_h = np.bincount(kb, weights=uh2, minlength=N)
        tot = float(np.mean(np.sum(uu * uu, axis=0)))
        return w_h * tot * N**6 / np.sum(w_h) / N**6

    e_dns, e_sur = shell_e(u5), shell_e(phase_surrogate(u5, np.random.default_rng(SEED_SUR)))
    kk_band = np.arange(N, dtype=float)
    dev_shell = np.abs(e_sur - e_dns) / np.maximum(e_dns, 1e-300)
    b_lo, b_hi = SUR_SHELL_BAND
    spec_match = float(np.max(dev_shell[b_lo + 1 : b_hi + 1]))
    spec_match_s1 = float(dev_shell[1])

    # ---- f64 vs f32 robustness --------------------------------------------
    z = np.load(os.path.join(RESULTS, "p5b_snap_u_t5_f32.npz"))
    st32 = strain_eig_and_stats(z["u"].astype(np.float64))
    robust32 = rel_dev_block(fam["DNS_t5"][0], st32)

    # ---- 48^3 reference artifacts for the cross-language track -------------
    eps48 = EPS_FALLBACK
    ref_path = os.path.join(RESULTS, "p5c_gauss_ref_u.f64")
    rng_r = np.random.default_rng(SEED_REF48)
    u_fast = gaussian_field_oneshot(48, CK_SREENIVASAN, eps48, NU, rng_r)
    u_fast.tofile(ref_path)
    ref_gauss = scalar_subset(strain_eig_and_stats(u_fast))
    u48 = np.fromfile(os.path.join(RESULTS, "p5_snapshot_u.f64"), dtype=np.float64).reshape(3, 48, 48, 48)
    ref_dns48 = scalar_subset(strain_eig_and_stats(u48))

    # ---- family aggregation -------------------------------------------------
    def agg(rows: list[dict]) -> dict:
        keys = ("beta_S", "alpha_mean", "alpha_std", "pdf_alpha_peak")
        out: dict = {}
        for k in keys:
            vals = [r[k] for r in rows]
            out[k] = {"mean": float(np.mean(vals)), "std": float(np.std(vals))}
        for k in ("mean_lam", "cos2", "ratio_lambda"):
            arr = np.array([r[k] for r in rows])
            out[k] = {
                "mean": [float(v) for v in arr.mean(axis=0)],
                "std": [float(v) for v in arr.std(axis=0)],
            }
        out["n_realizations"] = len(rows)
        return out

    summary = {name: agg(rows) for name, rows in fam.items() if rows}
    # family-averaged PDFs for the csv/figures
    pdf_avg = {}
    for name, rows in fam.items():
        if not rows:
            continue
        pdf_avg[name] = {
            "cos_centers": rows[0]["pdf_cos_centers"],
            "cos": [np.mean([r["pdf_cos"][i] for r in rows], axis=0) for i in range(3)],
            "alpha_centers": rows[0]["pdf_alpha_centers"],
            "alpha": np.mean([r["pdf_alpha"] for r in rows], axis=0),
        }

    # ---- csv: family-averaged PDFs -----------------------------------------
    with open(os.path.join(RESULTS, "p5c_pdfs.csv"), "w", newline="", encoding="utf-8") as fh:
        wr = csv.writer(fh)
        wr.writerow(["kind", "family", "x", "pdf"])
        for name, pa in pdf_avg.items():
            for j, x in enumerate(pa["cos_centers"]):
                for i in range(3):
                    wr.writerow([f"cos{i + 1}", name, f"{x:.4f}", f"{pa['cos'][i][j]:.6e}"])
            for j, x in enumerate(pa["alpha_centers"]):
                wr.writerow(["alpha", name, f"{x:.4f}", f"{pa['alpha'][j]:.6e}"])

    with open(os.path.join(RESULTS, "p5c_summary.csv"), "w", newline="", encoding="utf-8") as fh:
        wr = csv.writer(fh)
        wr.writerow(
            ["family", "n", "lam1", "lam2", "lam3", "beta_S", "beta_S_std",
             "cos2_1", "cos2_2", "cos2_3", "alpha_mean", "alpha_std", "pdf_alpha_peak"]
        )
        for name, s in summary.items():
            wr.writerow(
                [name, s["n_realizations"],
                 f"{s['mean_lam']['mean'][0]:.4f}", f"{s['mean_lam']['mean'][1]:.4f}",
                 f"{s['mean_lam']['mean'][2]:.4f}",
                 f"{s['beta_S']['mean']:.4f}", f"{s['beta_S']['std']:.4f}",
                 f"{s['cos2']['mean'][0]:.4f}", f"{s['cos2']['mean'][1]:.4f}",
                 f"{s['cos2']['mean'][2]:.4f}",
                 f"{s['alpha_mean']['mean']:.4f}", f"{s['alpha_std']['mean']:.4f}",
                 f"{s['pdf_alpha_peak']['mean']:.4f}"]
            )

    protocol = {
        "program": "P5C_stretch_ensemble",
        "title": (
            "P5-C: vortex stretching statistics — Gaussian ensemble, "
            "phase surrogates and DNS snapshots compared"
        ),
        "date": "2026-09-29",
        "parameters": {
            "grid": N,
            "nu": NU,
            "eps_dns_96": eps_dns,
            "C_K": CK_SREENIVASAN,
            "M_gaussian": M_GAU,
            "M_surrogates": M_SUR,
            "seed_gaussian": SEED_GAU,
            "seed_surrogate": SEED_SUR,
            "seed_ref48": SEED_REF48,
            "gauss_generator": "Pao-K41 shell-exact (P3 algorithm, vectorized)",
            "surrogate": "|u_hat| preserved, phases randomized, Leray-projected, energy-renormalized",
            "align_bins": ALIGN_BINS,
            "alpha_bins": ALPHA_BINS,
        },
        "statistics_definitions": {
            "s_rms": "sqrt(<S_ij S_ij>)",
            "lambda_i": "strain eigenvalues, descending, normalized by s_rms",
            "beta_S": "<lambda_2> / (<lambda_1> - <lambda_3>)",
            "cos_theta_i": "omega_hat . e_i (e_i: strain eigenvector, i=1 most extensive)",
            "alpha": "(omega_i S_ij omega_j) / (|omega|^2 s_rms)",
        },
        "families": summary,
        "verifications": {
            "gauss_ensemble_mean_spectrum_max_dev_1_16": ens_spec_dev,
            "gauss_alignment_null_check": {
                "theory": "exact Gaussian => (omega,S) independent => cos2 = 1/3",
                "cos2_measured": summary["GAU"]["cos2"]["mean"],
            },
            "surrogate_spectrum_max_rel_dev_band_2_16": spec_match,
            "surrogate_spectrum_rel_dev_shell1": spec_match_s1,
            "f64_vs_f32_max_rel_dev": robust32,
        },
        "cross_language_reference": {
            "gauss_ref48": ref_gauss,
            "dns_ref48": ref_dns48,
            "artifacts": {
                "gauss": "p5c_gauss_ref_u.f64 (48^3, seed 20260929)",
                "dns": "p5_snapshot_u.f64 (48^3, P5 run A, t = 6)",
            },
        },
        "integrity": {
            "sha256_of_code": hashlib.sha256(
                open(os.path.abspath(__file__), "rb").read()
            ).hexdigest(),
            "sha256_gauss_ref": hashlib.sha256(open(ref_path, "rb").read()).hexdigest(),
        },
    }
    out = os.path.join(RESULTS, "p5c_stretch_ensemble.json")
    results_json_dump(protocol, out)
    print(f"[P5-C] wrote {out}")
    print(f"[P5-C] SUR spectrum match (max rel dev, band 1-16): {spec_match:.2e}")
    print(f"[P5-C] f64-vs-f32 max rel dev: {max(robust32.values()):.2e}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
