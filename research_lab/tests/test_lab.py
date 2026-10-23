"""Fast, deterministic tests for the research lab (CI-safe: N = 16).

These are the laboratory's own verification layer: each test pins one
mathematical property of the solver, the diagnostics or the b-rotation
transforms. They run in seconds and are wired into CI as part of the
lab-smoke job.
"""
import numpy as np
import pytest

from research_lab import diagnostics as dg
from research_lab.constants import b_rotation_matrix, quarter_rotation_matrix
from research_lab.extrapolate import observed_order, richardson
from research_lab.initial_conditions import taylor_green
from research_lab.solver import SpectralNSE3D

N = 16
NU = 0.05


def _state(n: int = N, nu: float = NU):
    solver = SpectralNSE3D(n, nu)
    u_hat = solver.dealias(solver.project(solver.fft(taylor_green(n))))
    return solver, u_hat


def test_projection_makes_field_solenoidal():
    solver, _ = _state()
    rng = np.random.default_rng(7)
    u = rng.standard_normal((3, N, N, N))
    u_hat = solver.project(solver.fft(u))
    assert dg.divergence_max(solver.k_vec, u_hat, N) < 1e-13


def test_single_mode_exact_viscous_decay():
    """One Fourier mode must decay as exp(-nu k^2 t): pins RK4 + nu term."""
    solver = SpectralNSE3D(N, NU)
    u = np.zeros((3, N, N, N))
    x = np.linspace(0.0, 2.0 * np.pi, N, endpoint=False)
    xm, ym, _ = np.meshgrid(x, x, x, indexing="ij")
    u[0] = np.sin(ym)  # mode k = (0, 1, 0)
    u_hat = solver.dealias(solver.project(solver.fft(u)))
    e0 = dg.mean_energy(u_hat, N)
    dt, steps = 0.01, 25
    for _ in range(steps):
        u_hat = solver.step_rk4(u_hat, dt)
    e1 = dg.mean_energy(u_hat, N)
    expected = np.exp(-2.0 * NU * dt * steps)
    assert abs(e1 / e0 - expected) < 1e-12


def test_galerkin_energy_balance():
    """dE/dt = -2 nu Omega for the unforced torus: discrete balance to RK4 tol."""
    solver, u_hat = _state(nu=0.05)
    dt = 0.002
    e0 = dg.mean_energy(u_hat, N)
    om = dg.enstrophy(u_hat, solver.curl_hat(u_hat), N)
    for _ in range(5):
        u_hat = solver.step_rk4(u_hat, dt)
    e1 = dg.mean_energy(u_hat, N)
    # crude RK4-consistent bound: energy loss close to viscous prediction
    assert 0.0 < e0 - e1 < (2.0 * NU * om * 5 * dt) * 1.01 + 1e-14


def test_taylor_green_is_divergence_free():
    solver, u_hat = _state()
    assert dg.divergence_max(solver.k_vec, u_hat, N) < 1e-13


def test_full_rotation_symmetry_is_exact_relabeling():
    """Quarter-turn symmetry: identical energy, vorticity sup, div-free."""
    solver, u_hat = _state()
    u_sym = solver.rotate_full_symmetry(u_hat, quarter_rotation_matrix())
    u_sym = solver.dealias(u_sym)
    e0 = dg.mean_energy(u_hat, N)
    e1 = dg.mean_energy(u_sym, N)
    w0 = dg.sup_vorticity(solver.vorticity_field(u_hat)[0])
    w1 = dg.sup_vorticity(solver.vorticity_field(u_sym)[0])
    assert abs(e0 - e1) < 1e-12
    assert abs(w0 - w1) / max(w0, 1e-30) < 1e-10
    assert dg.divergence_max(solver.k_vec, u_sym, N) < 1e-12


def test_pointwise_b_rotation_breaks_incompressibility():
    """The scientific point: pointwise rotation is NOT incompressible."""
    solver, u_hat = _state()
    u_rot = solver.rotate_pointwise(u_hat, b_rotation_matrix())
    div = dg.divergence_max(solver.k_vec, u_rot, N)
    assert div > 1e-4  # documented effect (generic field, generic rotation)
    # ... but it IS an isometry: energy exactly preserved
    e0 = dg.mean_energy(u_hat, N)
    e1 = dg.mean_energy(u_rot, N)
    assert abs(e0 - e1) < 1e-12


def test_short_run_diagnostics_consistent():
    """10 steps: div stays roundoff, energy decreases, BKM accumulates."""
    solver, u_hat = _state()
    ts = dg.TimeSeries()
    sup_prev = dg.sup_vorticity(solver.vorticity_field(u_hat)[0])
    dt = 0.005
    for step in range(1, 11):
        u_hat = solver.step_rk4(u_hat, dt)
        w, w_hat = solver.vorticity_field(u_hat)
        sup_now = dg.sup_vorticity(w)
        ts.push(step * dt, dg.mean_energy(u_hat, N),
                dg.enstrophy(u_hat, w_hat, N),
                dg.palinstrophy(solver.k_vec, w_hat, N),
                sup_now, dg.dissipation(solver.k_sq, u_hat, NU, N),
                dg.bkm_step(ts.bkm[-1], sup_prev, sup_now, dt))
        sup_prev = sup_now
    assert dg.divergence_max(solver.k_vec, u_hat, N) < 1e-12
    assert ts.energy[-1] < ts.energy[0]
    assert 0.0 < ts.bkm[-1] < 10.0
    assert np.isfinite(ts.enstrophy).all()


def test_extrapolation_tools_recover_order_two_sequence():
    """Manufactured J(dt) = J0 + c dt^2: order 2 and Richardson hit J0."""
    j0, c = 1.234567, 0.5
    vals = [j0 + c * dt**2 for dt in (0.1, 0.05, 0.025)]
    p = observed_order(vals[0], vals[1], vals[2])
    assert abs(p - 2.0) < 1e-9
    extr = richardson(vals[1], vals[2], 2.0, p)
    assert abs(extr - j0) < 1e-9


def test_extrapolation_tools_recover_order_four_sequence():
    j0, c = -0.7, 2.0
    vals = [j0 + c * dt**4 for dt in (0.2, 0.1, 0.05)]
    p = observed_order(vals[0], vals[1], vals[2])
    assert abs(p - 4.0) < 1e-9
    extr = richardson(vals[1], vals[2], 2.0, p)
    assert abs(extr - j0) < 1e-9


@pytest.mark.parametrize("n", [12])
def test_spectral_radii_shapes(n):
    radii = dg.spectral_radii(n)
    assert radii.shape == (n, n, n)
    assert radii[0, 0, 0] == 0.0
    assert abs(radii[1, 0, 0] - 1.0) < 1e-12
