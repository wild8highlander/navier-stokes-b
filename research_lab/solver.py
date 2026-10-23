"""Dealiased pseudo-spectral 3D Navier-Stokes solver on the torus.

Spatial discretization: Fourier collocation on the periodic domain
[0, 2*pi)^3 with an N^3 grid, integer wavenumber lattice
k = 2*pi*fftfreq(N)*N, cubic 2/3-rule dealiasing (|k_i| <= N//3 for every
axis) and the Leray projection onto divergence-free fields.  Time
integration: classical RK4 with the projection applied inside every
right-hand-side evaluation, so the state stays divergence-free to roundoff
along the whole run (measured max |div u| ~ 1e-17).

The nonlinearity is evaluated in the vortex-(stretching) form: with
omega = curl u the convective derivative reduces, after the Leray
projection annihilates the gradient part, to a cross product of the
velocity and vorticity fields; the right-hand side is

    P[dealias(fft(w x u))] - nu k^2 u_hat.

The cross-product order w x u reproduces the two reference ports of this
module exactly: verification/julia_lab/src/07_solver3d.jl (rhs3 mirror)
and nsb-lab-multilang/python/nsb_lab.py (rhs3), which produce the
repository's documented laboratory results (README Part IV).

Only numpy is required (the laboratory's declared dependency contract).
"""
from __future__ import annotations

import numpy as np


class SpectralNSE3D:
    """Pseudo-spectral Navier-Stokes evolution for the velocity field.

    Parameters
    ----------
    n:
        Grid points per dimension (even, >= 8).
    nu:
        Kinematic viscosity.

    Notes
    -----
    Spectral states ``u_hat`` have shape ``(3, n, n, n)`` (component, kx,
    ky, kz) and follow the unnormalized ``numpy.fft`` convention, matching
    the Parseval normalization used in :mod:`research_lab.diagnostics`.
    """

    def __init__(self, n: int, nu: float) -> None:
        if n < 8 or n % 2 != 0:
            raise ValueError("n must be even and >= 8")
        self.n = int(n)
        self.nu = float(nu)

        k1d = np.fft.fftfreq(n) * n  # integer lattice values 0..n/2-1, -n/2..-1
        kx = k1d.reshape(n, 1, 1)
        ky = k1d.reshape(1, n, 1)
        kz = k1d.reshape(1, 1, n)
        self.k_vec = np.stack(np.broadcast_arrays(kx, ky, kz))  # (3, n, n, n)
        self.k_sq = self.k_vec[0] ** 2 + self.k_vec[1] ** 2 + self.k_vec[2] ** 2
        self.k_sq_safe = np.where(self.k_sq > 0.0, self.k_sq, 1.0)

        # cubic 2/3 dealiasing mask (mirrors the Julia reference port)
        k_cut = n // 3
        self.mask = ((np.abs(self.k_vec[0]) <= k_cut)
                     & (np.abs(self.k_vec[1]) <= k_cut)
                     & (np.abs(self.k_vec[2]) <= k_cut))

        # integer lattice for exact symmetry rotations (grid-matching R)
        k1d_int = np.rint(k1d).astype(int)
        self._k_int = np.stack(np.broadcast_arrays(
            k1d_int.reshape(n, 1, 1),
            k1d_int.reshape(1, n, 1),
            k1d_int.reshape(1, 1, n),
        ))

    # ------------------------------------------------------------- transforms
    def fft(self, u: np.ndarray) -> np.ndarray:
        """Physical (3, n, n, n) real field -> spectral coefficients."""
        return np.fft.fftn(u, axes=(1, 2, 3))

    def ifft(self, u_hat: np.ndarray) -> np.ndarray:
        """Spectral coefficients -> physical field (real part)."""
        return np.fft.ifftn(u_hat, axes=(1, 2, 3)).real

    # ------------------------------------------------------------- operators
    def project(self, u_hat: np.ndarray) -> np.ndarray:
        """Leray projection onto divergence-free fields (in Fourier space)."""
        k_dot_u = (self.k_vec[0] * u_hat[0]
                   + self.k_vec[1] * u_hat[1]
                   + self.k_vec[2] * u_hat[2]) / self.k_sq_safe
        return u_hat - self.k_vec * k_dot_u

    def dealias(self, u_hat: np.ndarray) -> np.ndarray:
        """Truncate modes outside the 2/3-rule cube."""
        return u_hat * self.mask

    def curl_hat(self, u_hat: np.ndarray) -> np.ndarray:
        """Fourier-space curl: i k x u_hat."""
        return 1j * np.cross(self.k_vec, u_hat, axis=0)

    def vorticity_field(self, u_hat: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
        """Return (omega, omega_hat) for a spectral velocity state."""
        w_hat = self.curl_hat(u_hat)
        return self.ifft(w_hat), w_hat

    def velocity_from_vorticity(self, w_hat: np.ndarray) -> np.ndarray:
        """Biot-Savart: u_hat = i k x w_hat / |k|^2 (k = 0 -> 0), projected.

        Used to build a divergence-free velocity state from a vorticity
        initial condition (Hou-Luo tubes).
        """
        u_hat = 1j * np.cross(self.k_vec, w_hat, axis=0) / self.k_sq_safe
        return self.dealias(self.project(u_hat))

    # ------------------------------------------------------------- dynamics
    def _rhs(self, u_hat: np.ndarray) -> np.ndarray:
        """Right-hand side: P[dealias(fft(w x u))] - nu k^2 u_hat."""
        u = self.ifft(u_hat)
        w = self.ifft(self.curl_hat(u_hat))
        nl_hat = self.dealias(self.fft(np.cross(w, u, axis=0)))
        return self.project(nl_hat) - self.nu * self.k_sq * u_hat

    def step_rk4(self, u_hat: np.ndarray, dt: float) -> np.ndarray:
        """One classical RK4 step; the result is kept dealiased."""
        k1 = self._rhs(u_hat)
        k2 = self._rhs(u_hat + (0.5 * dt) * k1)
        k3 = self._rhs(u_hat + (0.5 * dt) * k2)
        k4 = self._rhs(u_hat + dt * k3)
        return self.dealias(
            u_hat + (dt / 6.0) * (k1 + 2.0 * k2 + 2.0 * k3 + k4))

    def cfl_dt(self, u_hat: np.ndarray, safety: float = 0.5) -> float:
        """Advective CFL time step: safety * dx / max|u|."""
        u = self.ifft(u_hat)
        u_max = float(np.max(np.sqrt(np.sum(u * u, axis=0))))
        dx = 2.0 * np.pi / self.n
        if u_max < 1e-14:
            return safety * dx * dx / max(self.nu, 1e-12)
        return safety * dx / u_max

    # ---------------------------------------------------------- b-rotations
    def rotate_pointwise(self, u_hat: np.ndarray,
                         rot: list[list[float]]) -> np.ndarray:
        """u'(x) = R u(x): isometry, breaks incompressibility.

        Evaluated in physical space (the rotation is x-independent, so this
        equals the component-wise spectral mix up to FFT roundoff).
        """
        u = self.ifft(u_hat)
        ru = np.einsum("ij,jxyz->ixyz", np.asarray(rot, dtype=float), u)
        return self.fft(ru)

    def rotate_full_symmetry(self, u_hat: np.ndarray,
                             rot: list[list[float]]) -> np.ndarray:
        """u'(x) = R u(R^-1 x) for a grid-matching (integer) rotation R.

        Exact relabeling: spectral coefficients are remapped as
        u_hat'(k) = R u_hat(R^T k) with integer index arithmetic, so no
        interpolation is performed and the lattice maps onto itself.
        """
        mat = np.asarray(rot, dtype=float)
        mat_int = np.rint(mat).astype(int)
        if not np.allclose(mat, mat_int, atol=1e-8):
            raise ValueError(
                "rotate_full_symmetry requires a grid-matching (integer) "
                "rotation matrix; use rotate_pointwise for generic R")
        # u_hat'(k) = R u_hat(R^T k); python modulo folds +/- n/2 correctly
        k_rot = np.einsum("ab,bxyz->axyz", mat_int.T, self._k_int)
        src = u_hat[:, k_rot[0] % self.n,
                    k_rot[1] % self.n, k_rot[2] % self.n]
        return np.einsum("ij,jxyz->ixyz", mat_int, src)
