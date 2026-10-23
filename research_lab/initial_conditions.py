"""Initial conditions and b-rotation transforms for the laboratory flows.

All fields are periodic on [0, 2 pi]^3 and returned in physical space with
shape (3, N, N, N); helpers convert them to dealiased divergence-free
spectral states.

Flows:
    * taylor_green — the classic Brachet et al. (1983) vortex, the
      repository's reference field in section 2;
    * abc           — Arnold-Beltrami-Childress flow, an exact curl
      eigenfield (force-free); at small nu it stresses the BKM monitor;
    * hou_luo_tubes — periodic-box adaptation of the anti-parallel vortex
      tube scenario of Hou & Luo (two Gaussian tubes + symmetry-preserving
      perturbation), the strongest known near-singularity candidate setup;
    * random_field  — deterministic LCG-seeded field with a k^-3 spectrum.

The b-rotation of the repository is available in two mathematically distinct
forms (see README, "What the b-rotation can and cannot do"):
    * pointwise  u'(x) = R u(x)        — isometry, NOT incompressible;
    * full       u'(x) = R u(R^-1 x)   — exact NSE symmetry (grid-matching).
"""
import numpy as np

from research_lab.constants import b_rotation_matrix

_LCG_STATE = 20260916


def _lcg_randoms(shape: tuple[int, ...]) -> np.ndarray:
    """Deterministic uniform randoms in [-1, 1) (fixed seed, repo-style LCG)."""
    global _LCG_STATE
    out = np.empty(shape)
    total = int(np.prod(shape))
    flat = np.empty(total)
    for idx in range(total):
        _LCG_STATE = (_LCG_STATE * 6364136223846793005 + 1442695040888963407) \
            % (1 << 64)
        flat[idx] = _LCG_STATE / float(1 << 64) * 2.0 - 1.0
    out[:] = flat.reshape(shape)
    return out


def grid(n: int) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Physical-space coordinate arrays for [0, 2 pi)^3."""
    x = np.linspace(0.0, 2.0 * np.pi, n, endpoint=False)
    return np.meshgrid(x, x, x, indexing="ij")


def taylor_green(n: int) -> np.ndarray:
    """u = (sin x cos y cos z, -cos x sin y cos z, 0)."""
    x, y, z = grid(n)
    u = np.empty((3, n, n, n))
    u[0] = np.sin(x) * np.cos(y) * np.cos(z)
    u[1] = -np.cos(x) * np.sin(y) * np.cos(z)
    u[2] = 0.0
    return u


def abc(n: int, a: float = 1.0, b: float = 1.0, c: float = 1.0) -> np.ndarray:
    """Arnold-Beltrami-Childress flow, an exact curl eigenfield (lambda = 1)."""
    x, y, z = grid(n)
    u = np.empty((3, n, n, n))
    u[0] = a * np.sin(z) + c * np.cos(y)
    u[1] = b * np.sin(x) + a * np.cos(z)
    u[2] = c * np.sin(y) + b * np.cos(x)
    return u


def hou_luo_tubes(n: int, gamma: float = 1.0, delta: float = np.pi / 8.0,
                  sigma: float = np.pi / 16.0,
                  perturbation: float = 0.05) -> np.ndarray:
    """Two anti-parallel Gaussian vortex tubes along x (periodic-box variant
    of the Hou-Luo scenario), plus a symmetric small perturbation.

    Returns vorticity-shaped velocity via the caller; here the raw VELOCITY
    is produced by the solver's Biot-Savart helper, so this function returns
    the vorticity field instead: use velocity_from_vorticity() on its FFT.
    """
    _x, y, z = grid(n)
    w = np.zeros((3, n, n, n))

    def tube(y0: float, z0: float, sign: float) -> None:
        gauss = np.exp(-((y - y0) ** 2 + (z - z0) ** 2) / (2.0 * sigma**2))
        # symmetric small perturbation along the tube: (1 + eps*cos x)
        w[0] += sign * gamma * gauss * (1.0 + perturbation * np.cos(_x))

    tube(np.pi / 2.0, np.pi / 2.0, +1.0)
    tube(3.0 * np.pi / 2.0, np.pi / 2.0, -1.0)
    return w


def random_field(n: int, k_peak: int = 4) -> np.ndarray:
    """Deterministic random divergence-free field with an energy envelope
    peaked near k_peak (used for generic decay runs)."""
    u = _lcg_randoms((3, n, n, n))
    x, y, z = grid(n)
    # project onto a smooth subspace: convolve with trig kernels near k_peak
    for i in range(3):
        u[i] = (u[i]
                + np.sin(k_peak * x) * np.cos(k_peak * y + i)
                + np.cos(k_peak * z + 2 * i) * np.sin(k_peak * y)) / 2.0
    return u


def rotate_pointwise(u: np.ndarray,
                     rot: list[list[float]] | None = None) -> np.ndarray:
    """u'(x) = R u(x): energy-preserving, incompressibility-breaking."""
    rot = b_rotation_matrix() if rot is None else rot
    out = np.empty_like(u)
    for i in range(3):
        out[i] = rot[i][0] * u[0] + rot[i][1] * u[1] + rot[i][2] * u[2]
    return out
