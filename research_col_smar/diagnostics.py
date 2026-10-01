"""Singularity diagnostics for the spectral Navier-Stokes laboratory.

Every diagnostic is computed directly from the spectral coefficient array
u_hat of shape (3, N, N, N) using Parseval identities, so no redundant FFTs
are needed. The Beale-Kato-Majda (BKM) running integral

    BKM(t) = int_0^t sup_x |omega(x, s)| ds

is the repository's central blow-up monitor: by Beale-Kato-Majda (1984) a
finite BKM integral at the maximal existence time implies the solution stays
smooth. Tracking it (and the enstrophy Omega = < |omega|^2 > / 2) is how the
lab hunts for, or rules out, near-singular behaviour inside a computed
window.
"""
import numpy as np


def mean_energy(u_hat: np.ndarray, n: int) -> float:
    """E = < |u|^2 > / 2 on the torus of volume (2*pi)^3, per unit volume."""
    return 0.5 * float(np.sum(np.abs(u_hat) ** 2)) / n**6


def enstrophy(u_hat: np.ndarray, w_hat: np.ndarray, n: int) -> float:
    """Omega = < |curl u|^2 > / 2 = < |omega|^2 > / 2 (Parseval)."""
    del u_hat
    return 0.5 * float(np.sum(np.abs(w_hat) ** 2)) / n**6


def palinstrophy(k_vec: np.ndarray, w_hat: np.ndarray, n: int) -> float:
    """P = < |curl omega|^2 > / 2 — the vorticity-gradient amplification meter."""
    kw_hat = np.cross(k_vec, w_hat, axis=0)
    return 0.5 * float(np.sum(np.abs(kw_hat) ** 2)) / n**6


def dissipation(k_sq: np.ndarray, u_hat: np.ndarray, nu: float, n: int) -> float:
    """epsilon = nu * < |grad u|^2 > (equals 2 nu < S:S > for div-free fields)."""
    return nu * float(np.sum(k_sq * np.abs(u_hat) ** 2)) / n**6


def sup_vorticity(w: np.ndarray) -> float:
    """sup_x |omega| approximated by the grid maximum (pseudospectral norm).

    Note: this is a collocation-point maximum, the standard practical proxy
    for the L-infinity norm in spectral codes; a rigorous bound needs the
    aliasing correction discussed in the README.
    """
    return float(np.max(np.sqrt(np.sum(w * w, axis=0))))


def bkm_step(bkm: float, sup_prev: float, sup_now: float, dt: float) -> float:
    """Trapezoid advance of the BKM integral by one time step."""
    return bkm + 0.5 * (sup_prev + sup_now) * dt


def shell_spectrum(u_hat: np.ndarray, n: int, k_mod: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """Angle-averaged energy spectrum E(k), normalized so that sum E(k) = E."""
    energy_per_mode = 0.5 * np.sum(np.abs(u_hat) ** 2, axis=0) / n**6
    k_int = np.rint(k_mod).astype(int)
    kmax = int(k_int.max())
    counts = np.bincount(k_int.ravel(), minlength=kmax + 1)
    sums = np.bincount(k_int.ravel(), weights=energy_per_mode.ravel(),
                       minlength=kmax + 1)
    with np.errstate(invalid="ignore", divide="ignore"):
        spectrum = np.where(counts > 0, sums / np.maximum(counts, 1), 0.0)
    return np.arange(kmax + 1), spectrum


def spectral_radii(n: int) -> np.ndarray:
    """|k| array for the integer Fourier lattice produced by fftfreq(n)*n."""
    k = np.fft.fftfreq(n) * n
    kx = k.reshape(n, 1, 1)
    ky = k.reshape(1, n, 1)
    kz = k.reshape(1, 1, n)
    return np.sqrt(kx * kx + ky * ky + kz * kz)


def spectral_tail_level(spectrum: np.ndarray, k_cutoff: int,
                        window: int = 1) -> float:
    """Resolution monitor: max E(k) in the top shells just below the dealiasing
    cutoff, relative to the spectral peak.

    For a resolved run this ratio is many orders below one (spectral methods
    leave the cutoff empty); pile-up towards O(1) signals under-resolution.
    A plain log-slope fit is meaningless when the physical tail sits at
    machine zero (laminar/early phase), hence this level-based check.
    """
    k_hi = min(k_cutoff, len(spectrum) - 1)
    k_lo = max(1, k_hi - window)
    tail = spectrum[k_lo:k_hi + 1]
    peak = float(np.max(spectrum[1:]))
    if peak <= 0.0:
        return 0.0
    return float(np.max(tail) / peak) if tail.size else 0.0


def spectral_tail_slope(spectrum: np.ndarray, k_hi: int) -> float:
    """Least-squares slope of log E(k) over the last fitted decade of modes.

    A resolved decaying turbulence field steepens at high k; a slope close to
    zero or a noisy plateau indicates an unresolved or under-dealiased run.
    """
    ks = np.arange(1, min(k_hi, len(spectrum) - 1) + 1)
    vals = []
    good_ks = []
    for k in ks:
        if spectrum[k] > 0.0:
            good_ks.append(k)
            vals.append(np.log(spectrum[k]))
    if len(good_ks) < 3:
        return float("nan")
    slope = np.polyfit(np.array(good_ks, dtype=float), np.array(vals), 1)[0]
    return float(slope)


def divergence_max(k_vec: np.ndarray, u_hat: np.ndarray, n: int) -> float:
    """max |div u| in physical space computed via the divergence theorem form:
    sqrt(< (div u)^2 >) — Parseval-exact, per unit volume."""
    kx, ky, kz = k_vec[0], k_vec[1], k_vec[2]
    div_hat = 1j * (kx * u_hat[0] + ky * u_hat[1] + kz * u_hat[2])
    return float(np.sqrt(np.sum(np.abs(div_hat) ** 2)) / n**3)


class TimeSeries:
    """Records diagnostics along a run and advances the BKM integral."""

    def __init__(self) -> None:
        self.t: list[float] = []
        self.energy: list[float] = []
        self.enstrophy: list[float] = []
        self.palinstrophy: list[float] = []
        self.sup_omega: list[float] = []
        self.dissipation: list[float] = []
        self.bkm: list[float] = [0.0]

    def push(self, t: float, energy: float, omega: float, palin: float,
             sup: float, eps: float, bkm: float) -> None:
        self.t.append(t)
        self.energy.append(energy)
        self.enstrophy.append(omega)
        self.palinstrophy.append(palin)
        self.sup_omega.append(sup)
        self.dissipation.append(eps)
        self.bkm.append(bkm)

    def peak_enstrophy(self) -> tuple[float, float]:
        idx = int(np.argmax(self.enstrophy))
        return self.t[idx], self.enstrophy[idx]

    def as_dict(self) -> dict:
        return {
            "t": self.t,
            "energy": self.energy,
            "enstrophy": self.enstrophy,
            "palinstrophy": self.palinstrophy,
            "sup_omega": self.sup_omega,
            "dissipation": self.dissipation,
            "bkm": self.bkm[1:],
        }
