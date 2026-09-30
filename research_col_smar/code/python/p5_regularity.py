"""P5: 3D smoothness of solutions — regularity diagnostics, the b-protocol
and the hyperdissipative family.

Executes the smoothness program of monograph ch. 12 on the canonical
singularity-testing flow (3D Taylor-Green vortex):

  (1) pseudo-spectral DNS on a 48^3 periodic box, 2/3-rule dealiasing,
      explicit midpoint RK2, divergence-free projection each stage;
  (2) run A (baseline TG) vs run B (the SAME initial field rotated by
      theta_b = arcsin(b), b = 1/(4pi + 2 sqrt(3)) about z, energy
      identical by construction): full regularity diagnostics along
      both trajectories — E(t), enstrophy Omega(t), eps(t), ||omega||_oo,
      ||u||_oo, <u^4>, <u^6>, palinstrophy, stretching balance
      dOmega/dt = 2<omega.S.omega> - 2 nu <|grad omega|^2>, the BKM
      integral I(t) = int_0^t ||omega||_oo dt' and the Ladyzhenskaya-
      Prodi-Serrin integrals int <u^4> dt, int <u^6>^(1/2) dt;
  (3) hyperdissipative family nu(-Delta)^b_pow, b_pow in {1, 5/4, 3/2, 2}
      (the Colombo-Haffter global-regularity threshold is 5/4): the
      generalized dissipation scale eta_b = (nu^3/eps)^(1/(6b-2)), the
      closed-form generalized Pao normalization
      beta_b = (C_K Gamma(2b-2/3)/(2b))^(2b/(2b-2/3)) and the universal
      prediction k_d eta_b = x*(b) = [(2b-5/3)/(2b beta_b)]^(1/(2b))
      tested against the measured dissipation-spectrum peaks;
  (4) the spectral smoothness certificate: an exponentially decaying
      tail E ~ exp(-c k) on the top of the dealiased band certifies
      analytic regularity; c(t) and the exponential-vs-power-law fit
      quality are tracked in time (the most dangerous moment is the
      enstrophy peak);
  (5) self-verification: divergence-free residual of the IC, the energy
      balance dE/dt = -eps (no forcing) and the enstrophy balance
      dOmega/dt = S1 - D2 are checked by finite differences;
  (6) a snapshot of (u, omega) at T_end of run A is stored as raw f64
      for the C++/Julia diagnostic re-computation, and a miniature
      16^3 run (--mini) is written for the three-language dynamical
      cross-validation.

Outputs: results/p5_regularity.json, results/p5_bkm.csv,
         results/p5_certificate.csv, results/p5_bfamily.csv,
         results/p5_spectra.npz, results/p5_snapshot_u.f64,
         results/p5_snapshot_w.f64, results/p5_mini_python.json
"""

from __future__ import annotations

import csv
import hashlib
import json
import math
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from sk_core import CK_SREENIVASAN, results_json_dump  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
RESULTS = os.path.join(ROOT, "results")

# --- universal b-correction constants (repo convention) --------------------
B_UNIV = 1.0 / (4.0 * math.pi + 2.0 * math.sqrt(3))
THETA_B = math.asin(B_UNIV)

N = 48
NU = 0.01
DT = 2.0e-3
T_END = 6.0
SAVE_EVERY = 10           # steps -> diagnostic cadence 0.02
SPEC_TIMES = (1.0, 2.0, 3.0, 4.0, 5.0)
B_POWERS = (1.0, 1.25, 1.5, 2.0)
CERT_BAND = (11.0, 16.0)  # exponential-tail fit band, k_c = N/3 = 16
STAT_T0 = 2.0             # b-family averaging window [STAT_T0, T_END]

# miniature cross-language run
MINI = {"n": 16, "nu": 0.01, "dt": 5.0e-3, "t_end": 1.0, "save_every": 10}


# ---------------------------------------------------------------------------
# generalized Pao normalization (closed form, monograph ch. 12.5)
# ---------------------------------------------------------------------------
def beta_b(b_pow: float, ck: float = CK_SREENIVASAN) -> float:
    """beta_b = (C_K Gamma(2b-2/3)/(2b))^(2b/(2b-2/3)).

    Exact dissipation normalization of the generalized Pao spectrum
    E = C_K eps^(2/3) k^(-5/3) exp(-beta_b (k eta_b)^(2b)) with
    eta_b = (nu^3/eps)^(1/(6b-2)): int 2 nu k^(2b) E dk = eps.
    For b_pow = 1 this reduces to the ch. 5 value (C_K Gamma(2/3))^(3/2).
    """
    a = 2.0 * b_pow - 2.0 / 3.0
    return (ck * math.gamma(a / (2.0 * b_pow)) / b_pow) ** (2.0 * b_pow / a)


def x_star(b_pow: float, ck: float = CK_SREENIVASAN) -> float:
    """Universal peak of the shell-dissipation spectrum D = 2 nu k^(2b) E.

    x*(b) = [(2b - 5/3) / (2 b beta_b)]^(1/(2b)); prediction: the measured
    argmax k_d satisfies k_d eta_b -> x*(b) for every b_pow.
    """
    bb = beta_b(b_pow, ck)
    return ((2.0 * b_pow - 5.0 / 3.0) / (2.0 * b_pow * bb)) ** (1.0 / (2.0 * b_pow))


def eta_b(eps: float, nu: float, b_pow: float) -> float:
    return (nu**3 / eps) ** (1.0 / (6.0 * b_pow - 2.0))


# ---------------------------------------------------------------------------
# spectral solver
# ---------------------------------------------------------------------------
def wavevectors(n: int) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    kf = np.fft.fftfreq(n, d=1.0 / n)
    kx = kf[:, None, None]
    ky = kf[None, :, None]
    kz = kf[None, None, : n // 2 + 1]
    k2 = kx**2 + ky**2 + kz**2
    return kx, ky, kz, k2


def dealias_mask(n: int) -> np.ndarray:
    """2/3 rule applied to the nonlinear product (repo P6 convention)."""
    kx, ky, kz, _ = wavevectors(n)
    crit = n // 3
    return (np.abs(kx) <= crit) & (np.abs(ky) <= crit) & (np.abs(kz) <= crit)


def tg_initial_condition(n: int) -> np.ndarray:
    x = y = z = (np.arange(n) + 0.5) * (2.0 * math.pi / n)
    X, Y, Z = np.meshgrid(x, y, z, indexing="ij")
    return np.stack(
        [
            np.sin(X) * np.cos(Y) * np.cos(Z),
            -np.cos(X) * np.sin(Y) * np.cos(Z),
            np.zeros_like(X),
        ]
    )


def rotate_z(u: np.ndarray, theta: float) -> np.ndarray:
    c, s = math.cos(theta), math.sin(theta)
    out = np.empty_like(u)
    out[0] = c * u[0] - s * u[1]
    out[1] = s * u[0] + c * u[1]
    out[2] = u[2]
    return out


class SpecSolver:
    """Pseudo-spectral solver of the hyperdissipative NSE family.

    Dissipation operator -nu (-Delta)^b_pow, i.e. -nu k^(2 b_pow) in
    Fourier space; b_pow = 1 is the classical Navier-Stokes case.
    """

    def __init__(self, n: int, nu: float, dt: float, b_pow: float = 1.0):
        self.n, self.nu, self.dt, self.b_pow = n, nu, dt, b_pow
        self.kx, self.ky, self.kz, self.k2 = wavevectors(n)
        self.k2e = self.k2.copy()
        self.k2e[0, 0, 0] = 1.0
        self.kmag = np.sqrt(self.k2)
        self.kmb = self.kmag ** (2.0 * b_pow)  # k^(2b), zero at k = 0
        self.mask = dealias_mask(n)
        self.crit = n // 3
        self.uh = np.zeros((3, n, n, n // 2 + 1), dtype=complex)
        # integrating-factor coefficients: exact dissipation, RK2 nonlinearity
        lam = nu * self.kmb if b_pow != 1.0 else nu * self.k2
        self._D = np.exp(-lam * dt)
        self._Dm = np.sqrt(self._D)
        self._sD = self._Dm.copy()

    # -- basic operators ----------------------------------------------------
    def kv(self, a: int) -> np.ndarray:
        return (self.kx, self.ky, self.kz)[a]

    def project(self, fh: np.ndarray) -> np.ndarray:
        div = (self.kx * fh[0] + self.ky * fh[1] + self.kz * fh[2]) / self.k2e
        return np.stack([fh[a] - self.kv(a) * div for a in range(3)])

    def set_ic(self, u_phys: np.ndarray) -> None:
        self.uh = np.fft.rfftn(u_phys, axes=(1, 2, 3))
        self.uh = self.project(self.uh) * self.mask
        self.uh[:, 0, 0, 0] = 0.0

    def phys(self) -> np.ndarray:
        return np.fft.irfftn(self.uh, s=(self.n,) * 3, axes=(1, 2, 3))

    def vorticity_hat(self) -> np.ndarray:
        kx, ky, kz = self.kx, self.ky, self.kz
        return np.stack(
            [
                1j * (ky * self.uh[2] - kz * self.uh[1]),
                1j * (kz * self.uh[0] - kx * self.uh[2]),
                1j * (kx * self.uh[1] - ky * self.uh[0]),
            ]
        )

    def vorticity(self) -> np.ndarray:
        return np.fft.irfftn(
            self.vorticity_hat(), s=(self.n,) * 3, axes=(1, 2, 3)
        )

    # -- right-hand side ----------------------------------------------------
    def rhs(self) -> np.ndarray:
        """Nonlinear part  P[u x omega]  of the IFK right-hand side.

        Incompressible identity (u.grad)u = grad(u^2/2) - u x omega; the
        Leray projection removes the gradient part. Dissipation is applied
        exactly through the integrating factor (see step()).
        """
        u = self.phys()
        w = self.vorticity()
        cross = np.stack(
            [
                u[1] * w[2] - u[2] * w[1],
                u[2] * w[0] - u[0] * w[2],
                u[0] * w[1] - u[1] * w[0],
            ]
        )
        ch = np.fft.rfftn(cross, axes=(1, 2, 3))
        ch = self.project(ch)
        ch[:, 0, 0, 0] = 0.0
        return ch

    def step(self) -> None:
        """Integrating-factor midpoint RK2 (2nd order, dissipation exact).

        u_next = D uh + dt sqrt(D) N(u_mid),
        u_mid  = sqrt(D) (uh + dt/2 N(uh)),
        where D = exp(-nu k^(2b) dt) — unconditionally stable in the
        dissipation, mandatory for b_pow >= 2 at practical dt.
        """
        dt = self.dt
        k1 = self.rhs()
        uh_save = self.uh
        self.uh = self._Dm * (uh_save + 0.5 * dt * k1)
        k2 = self.rhs()
        self.uh = self._D * uh_save + dt * self._sD * k2
        self.uh *= self.mask
        self.uh[:, 0, 0, 0] = 0.0

    # -- diagnostics ---------------------------------------------------------
    def energy(self) -> float:
        return 2.0 * float(np.sum(np.abs(self.uh) ** 2)) / self.n**6

    def shell_spectrum(self) -> np.ndarray:
        e = np.zeros(self.n // 2 + 1)
        uh2 = np.sum(np.abs(self.uh) ** 2, axis=0)
        kb = np.rint(self.kmag).astype(int)
        for kk in range(1, len(e)):
            m = kb == kk
            if m.any():
                e[kk] = 2.0 * float(np.sum(uh2[m])) / self.n**6
        return e

    def diss_rate(self) -> float:
        w = self.kmb if self.b_pow != 1.0 else self.k2
        tot = 2.0 * float(np.sum(w * np.sum(np.abs(self.uh) ** 2, axis=0)))
        return self.nu * tot / self.n**6

    def enstrophy_palinstrophy(self) -> tuple[float, float]:
        wh = self.vorticity_hat()
        wh2 = np.sum(np.abs(wh) ** 2, axis=0)
        om2 = 2.0 * float(np.sum(wh2)) / self.n**6
        pal = 2.0 * float(np.sum(self.k2**2 * wh2)) / self.n**6
        return om2, pal

    def stretching(self, u: np.ndarray, w: np.ndarray) -> float:
        """S1 = 2 <omega_i S_ij omega_j> with S_ij = (d_i u_j + d_j u_i)/2."""
        gh = [
            np.fft.rfftn(u[a], axes=(0, 1, 2)) for a in range(3)
        ]
        grad = {}
        for a in range(3):
            for b in range(3):
                grad[(a, b)] = np.fft.irfftn(
                    1j * self.kv(b) * gh[a], s=(self.n,) * 3, axes=(0, 1, 2)
                )
        s1 = 0.0
        for a in range(3):
            for b in range(3):
                sab = 0.5 * (grad[(a, b)] + grad[(b, a)])
                s1 += float(np.mean(w[a] * w[b] * sab))
        return 2.0 * s1


def tail_fits(
    e: np.ndarray, kband: tuple[float, float]
) -> tuple[float, float, float, float]:
    """Exponential vs power-law tail fit on the certification band.

    Returns (c_exp, r2_exp, slope_pow, r2_pow); larger r2_exp relative to
    r2_pow certifies the analytic (exponential) tail.
    """
    kk = np.arange(len(e), dtype=float)
    m = (kk >= kband[0]) & (kk <= kband[1]) & (e > 0)
    if int(m.sum()) < 4:
        return float("nan"), float("nan"), float("nan"), float("nan")
    xk = kk[m]
    le = np.log(e[m])
    c_exp, i_exp = np.polyfit(xk, le, 1)
    pred = c_exp * xk + i_exp
    ss = float(np.sum((le - le.mean()) ** 2))
    r2_exp = 1.0 - float(np.sum((le - pred) ** 2)) / ss if ss > 0 else float("nan")
    sl_pow, i_pow = np.polyfit(np.log(xk), le, 1)
    pred2 = sl_pow * np.log(xk) + i_pow
    r2_pow = 1.0 - float(np.sum((le - pred2) ** 2)) / ss if ss > 0 else float("nan")
    return float(c_exp), r2_exp, float(sl_pow), r2_pow


def kd_from_spectrum(
    e: np.ndarray, nu: float, b_pow: float, n: int
) -> float:
    """Measured peak k_d of the shell-dissipation spectrum 2 nu k^(2b) E(k)."""
    kk = np.arange(len(e), dtype=float)
    d = kk ** (2.0 * b_pow) * e
    kk = kk[1:]
    d = d[1:]
    if d.max() <= 0:
        return float("nan")
    # parabolic interpolation around the discrete argmax
    i = int(np.argmax(d))
    if 1 <= i < len(d) - 1:
        y0, y1, y2 = d[i - 1], d[i], d[i + 1]
        denom = y0 - 2.0 * y1 + y2
        delta = 0.5 * (y0 - y2) / denom if abs(denom) > 1e-300 else 0.0
        delta = float(np.clip(delta, -1.0, 1.0))
        return float(kk[i] + delta)
    return float(kk[i])


# ---------------------------------------------------------------------------
# experiment driver
# ---------------------------------------------------------------------------
def run_case(
    label: str,
    rotate: bool,
    b_pow: float,
    n: int,
    nu: float,
    dt: float,
    t_end: float,
    save_every: int,
    snap_u: np.ndarray | None = None,
) -> dict:
    solver = SpecSolver(n, nu, dt, b_pow)
    ic = snap_u if snap_u is not None else tg_initial_condition(n)
    if rotate:
        ic = rotate_z(ic, THETA_B)
    solver.set_ic(ic)

    n_steps = int(round(t_end / dt))
    t_log, E_log, Om_log, eps_log = [], [], [], []
    win_log, uin_log, u4_log, u6_log = [], [], [], []
    pal_log, s1_log, d2_log = [], [], []
    cert_log = []
    spec_store: dict[str, np.ndarray] = {}
    snapshots: dict[float, tuple[np.ndarray, np.ndarray]] = {}

    for step in range(n_steps + 1):
        t = step * dt
        if step % (save_every * 50) == 0:
            print(
                f"    [{label}] step {step}/{n_steps}  t={t:.2f}  "
                f"E={solver.energy():.6f}",
                flush=True,
            )
        if step % save_every == 0 or step == n_steps:
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
            # enstrophy dissipation D2 = 2 <omega . nu(-Delta)^b omega>
            #                                = 4 nu sum k^(2b) |wh|^2 / n^6
            wh2 = np.sum(np.abs(solver.vorticity_hat()) ** 2, axis=0)
            k2b = solver.k2 if b_pow == 1.0 else solver.kmb
            d2 = 4.0 * nu * float(np.sum(k2b * wh2)) / n**6
            e_sh = solver.shell_spectrum()
            c_exp, r2_exp, sl_pow, r2_pow = tail_fits(e_sh, CERT_BAND)
            kd = kd_from_spectrum(e_sh, nu, b_pow, n)
            t_log.append(t)
            E_log.append(E)
            Om_log.append(Om)
            eps_log.append(eps)
            win_log.append(win)
            uin_log.append(uin)
            u4_log.append(u4)
            u6_log.append(u6)
            pal_log.append(pal)
            s1_log.append(s1)
            d2_log.append(d2)
            cert_log.append((c_exp, r2_exp, sl_pow, r2_pow, kd))
            for ts in SPEC_TIMES:
                if abs(t - ts) <= 0.5 * dt * save_every and ts not in spec_store:
                    spec_store[f"{label}_t{ts:g}"] = e_sh.copy()
            if label == "A" and abs(t - t_end) < 1e-12:
                snapshots["u"] = u
                snapshots["w"] = w
        if step < n_steps:
            solver.step()

    t_arr = np.array(t_log)
    E_arr = np.array(E_log)
    Om_arr = np.array(Om_log)
    win_arr = np.array(win_log)
    eps_arr = np.array(eps_log)
    cert_arr = np.array(cert_log)

    i_peak = int(np.argmax(Om_arr))
    i_bkm = float(np.trapezoid(win_arr, t_arr))
    lps4 = float(np.trapezoid(np.array(u4_log), t_arr))
    lps6 = float(np.trapezoid(np.sqrt(np.array(u6_log)), t_arr))
    # energy balance dE/dt = -2 eps (no forcing; program convention
    # E = sum e_shell = <u^2> = 2 E_kin, see monograph Appendix B)
    dEdt = (E_arr[2:] - E_arr[:-2]) / (t_arr[2:] - t_arr[:-2])
    bal = float(np.max(np.abs(dEdt + 2.0 * eps_arr[1:-1]))) / max(float(E_arr.max()), 1e-300)
    # enstrophy balance dOm/dt = S1 - D2
    dOmdt = (Om_arr[2:] - Om_arr[:-2]) / (t_arr[2:] - t_arr[:-2])
    bal2 = float(
        np.max(np.abs(dOmdt - (np.array(s1_log)[1:-1] - np.array(d2_log)[1:-1])))
    ) / max(float(Om_arr.max()), 1e-300)

    m_stat = t_arr >= STAT_T0
    eps_mean = float(np.mean(eps_arr[m_stat])) if m_stat.any() else float(eps_arr[-1])
    kd_win = float(np.mean(cert_arr[m_stat, 4])) if m_stat.any() else float(cert_arr[-1, 4])

    return {
        "label": label,
        "b_pow": b_pow,
        "t": t_arr,
        "E": E_arr,
        "Omega": Om_arr,
        "eps": eps_arr,
        "omega_inf": win_arr,
        "u_inf": np.array(uin_log),
        "u4": np.array(u4_log),
        "u6": np.array(u6_log),
        "pal": np.array(pal_log),
        "S1": np.array(s1_log),
        "D2": np.array(d2_log),
        "cert": cert_arr,
        "spec_store": spec_store,
        "snapshots": snapshots,
        "summary": {
            "t_peak_enstrophy": float(t_arr[i_peak]),
            "Omega_max": float(Om_arr.max()),
            "omega_inf_max": float(win_arr.max()),
            "u_inf_max": float(np.array(uin_log).max()),
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
        },
    }


def mini_run() -> dict:
    n, nu, dt, t_end, se = (
        MINI["n"],
        MINI["nu"],
        MINI["dt"],
        MINI["t_end"],
        MINI["save_every"],
    )
    solver = SpecSolver(n, nu, dt, 1.0)
    solver.set_ic(tg_initial_condition(n))
    n_steps = int(round(t_end / dt))

    def bias_free(w2_h: np.ndarray) -> float:
        """Full-grid sum = 2*half-sum - kz=0 plane.

        The half-grid rfft representation double-counts the kz = 0 plane
        (the Nyquist plane is zeroed by the dealiasing mask); this makes
        the mini-run quantities directly comparable with a full-complex
        FFT implementation in C++/Julia.
        """
        full = 2.0 * float(np.sum(w2_h)) - float(np.sum(w2_h[:, :, 0]))
        return full / n**6

    out = {"t": [], "E": [], "Omega": [], "omega_inf": []}
    for step in range(n_steps + 1):
        if step % se == 0 or step == n_steps:
            w = solver.vorticity()
            wh2 = np.sum(np.abs(solver.vorticity_hat()) ** 2, axis=0)
            out["t"].append(step * dt)
            out["E"].append(bias_free(np.sum(np.abs(solver.uh) ** 2, axis=0)))
            out["Omega"].append(bias_free(wh2))
            out["omega_inf"].append(
                float(np.max(np.sqrt(np.sum(w * w, axis=0))))
            )
        if step < n_steps:
            solver.step()
    return out


def main() -> int:
    os.makedirs(RESULTS, exist_ok=True)
    mini_mode = "--mini" in sys.argv

    if mini_mode:
        res = mini_run()
        results_json_dump(
            {
                "program": "P5_mini",
                "params": MINI,
                "convention": (
                    "bias-free: the kz=0 plane is counted once "
                    "(full-grid DFT normalization)"
                ),
                "series": res,
            },
            os.path.join(RESULTS, "p5_mini_python.json"),
        )
        print(
            f"[P5-mini] E(1.0) = {res['E'][-1]:.12f}, "
            f"Omega(1.0) = {res['Omega'][-1]:.12f}, "
            f"||w||_inf(1.0) = {res['omega_inf'][-1]:.12f}"
        )
        return 0

    # divergence-free residual of the TG initial condition
    kx, ky, kz, k2 = wavevectors(N)
    k2e = k2.copy()
    k2e[0, 0, 0] = 1.0
    uh0 = np.fft.rfftn(tg_initial_condition(N), axes=(1, 2, 3))
    div0 = np.abs(
        kx * uh0[0] + ky * uh0[1] + kz * uh0[2]
    ) / k2e
    div_free_max = float(np.max(div0))

    print("=== P5 run A: baseline Taylor-Green, 48^3, nu = 0.01 ===", flush=True)
    run_a = run_case("A", False, 1.0, N, NU, DT, T_END, SAVE_EVERY)
    print(
        f"[P5] A: t_peak = {run_a['summary']['t_peak_enstrophy']:.2f}, "
        f"Omega_max = {run_a['summary']['Omega_max']:.4f}, "
        f"||w||_oo max = {run_a['summary']['omega_inf_max']:.4f}, "
        f"I_BKM = {run_a['summary']['I_BKM_T']:.4f}"
    )
    print("=== P5 run B: b-rotated IC (theta_b about z) ===", flush=True)
    run_b = run_case("B", True, 1.0, N, NU, DT, T_END, SAVE_EVERY)
    print(
        f"[P5] B: I_BKM = {run_b['summary']['I_BKM_T']:.4f}, "
        f"factor I_B/I_A = "
        f"{run_b['summary']['I_BKM_T'] / run_a['summary']['I_BKM_T']:.4f}"
    )

    bfamily = []
    for bp in B_POWERS:
        lab = "A" if bp == 1.0 else f"H{bp:g}"
        if bp == 1.0:
            summ = run_a["summary"]
            eps_mean = summ["eps_mean_stat"]
            kd = summ["kd_mean_stat"]
        else:
            print(f"=== P5 run {lab}: hyperdissipation b_pow = {bp} ===", flush=True)
            rr = run_case(lab, False, bp, N, NU, DT, T_END, SAVE_EVERY)
            summ = rr["summary"]
            eps_mean = summ["eps_mean_stat"]
            kd = summ["kd_mean_stat"]
            for key, arr in rr["spec_store"].items():
                run_a.setdefault("spec_store", {})[key] = arr
        eb = eta_b(eps_mean, NU, bp)
        row = {
            "b_pow": bp,
            "eps_mean_stat": eps_mean,
            "eta_b": eb,
            "k_max_over_eta_b": (N / 3.0) * eb,
            "kd_measured": kd,
            "kd_times_eta_b": kd * eb,
            "x_star_theory": x_star(bp),
            "beta_b_theory": beta_b(bp),
            "rel_dev": abs(kd * eb - x_star(bp)) / x_star(bp),
        }
        bfamily.append(row)
        print(
            f"[P5] b_pow={bp:g}: eta_b={eb:.4f}, k_d={kd:.3f}, "
            f"k_d*eta_b={row['kd_times_eta_b']:.4f}, x*(b)={row['x_star_theory']:.4f}, "
            f"rel.dev={row['rel_dev']:.1%}"
        )

    # snapshot of run A at T_end for C++/Julia recomputation
    u_snap = run_a["snapshots"]["u"]
    w_snap = run_a["snapshots"]["w"]
    u_snap.tofile(os.path.join(RESULTS, "p5_snapshot_u.f64"))
    w_snap.tofile(os.path.join(RESULTS, "p5_snapshot_w.f64"))

    # spectra archive for the figures
    np.savez(
        os.path.join(RESULTS, "p5_spectra.npz"),
        **{
            key: val
            for key, val in run_a["spec_store"].items()
        },
    )

    csv_bkm = os.path.join(RESULTS, "p5_bkm.csv")
    with open(csv_bkm, "w", newline="", encoding="utf-8") as fh:
        wr = csv.writer(fh)
        wr.writerow(
            ["t", "E_A", "Omega_A", "omega_inf_A", "I_BKM_A",
             "E_B", "Omega_B", "omega_inf_B", "I_BKM_B", "eps_A"]
        )
        ia = np.cumsum(
            np.concatenate(
                [[0.0], 0.5 * (run_a["omega_inf"][1:] + run_a["omega_inf"][:-1])
                 * np.diff(run_a["t"])]
            )
        )
        ib = np.cumsum(
            np.concatenate(
                [[0.0], 0.5 * (run_b["omega_inf"][1:] + run_b["omega_inf"][:-1])
                 * np.diff(run_b["t"])]
            )
        )
        for j, t in enumerate(run_a["t"]):
            wr.writerow(
                [
                    f"{t:.4f}",
                    f"{run_a['E'][j]:.8e}",
                    f"{run_a['Omega'][j]:.8e}",
                    f"{run_a['omega_inf'][j]:.8e}",
                    f"{ia[j]:.8e}",
                    f"{run_b['E'][j]:.8e}",
                    f"{run_b['Omega'][j]:.8e}",
                    f"{run_b['omega_inf'][j]:.8e}",
                    f"{ib[j]:.8e}",
                    f"{run_a['eps'][j]:.8e}",
                ]
            )

    csv_cert = os.path.join(RESULTS, "p5_certificate.csv")
    with open(csv_cert, "w", newline="", encoding="utf-8") as fh:
        wr = csv.writer(fh)
        wr.writerow(
            ["t", "c_exp", "r2_exp", "slope_pow", "r2_pow", "kd"]
        )
        for j, t in enumerate(run_a["t"]):
            c, re_, sp, rp, kd = run_a["cert"][j]
            wr.writerow(
                [f"{t:.4f}", f"{c:.6e}", f"{re_:.6f}", f"{sp:.6e}",
                 f"{rp:.6f}", f"{kd:.4f}"]
            )

    csv_bf = os.path.join(RESULTS, "p5_bfamily.csv")
    with open(csv_bf, "w", newline="", encoding="utf-8") as fh:
        wr = csv.DictWriter(fh, fieldnames=list(bfamily[0].keys()))
        wr.writeheader()
        wr.writerows(bfamily)

    sA, sB = run_a["summary"], run_b["summary"]
    protocol = {
        "program": "P5_regularity",
        "title": (
            "3D smoothness of solutions: BKM/LPS diagnostics, the b-protocol "
            "and the hyperdissipative family"
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
            "ifk_note": (
                "dissipation exp(-nu k^(2b) t) is applied exactly; the "
                "explicit part is the nonlinearity only"
            ),
            "run_B": "IC rotated by theta_b = arcsin(b) about z (energy identical)",
            "b_powers": list(B_POWERS),
            "cert_band": list(CERT_BAND),
            "stat_window_t0": STAT_T0,
            "C_K_used_for_beta_b": CK_SREENIVASAN,
            "theta_b_deg": math.degrees(THETA_B),
        },
        "self_verification": {
            "div_free_residual_max": div_free_max,
            "energy_balance_rel_max_A": sA["energy_balance_rel_max"],
            "energy_balance_rel_max_B": sB["energy_balance_rel_max"],
            "enstrophy_balance_rel_max_A": sA["enstrophy_balance_rel_max"],
        },
        "run_A_baseline": {k: v for k, v in sA.items() if "balance" not in k},
        "run_B_brotated": {k: v for k, v in sB.items() if "balance" not in k},
        "b_protocol_effect": {
            "factor_I_BKM_B_over_A": sB["I_BKM_T"] / sA["I_BKM_T"],
            "factor_omega_inf_B_over_A": sB["omega_inf_max"] / sA["omega_inf_max"],
            "factor_Omega_max_B_over_A": sB["Omega_max"] / sA["Omega_max"],
            "max_abs_dE": float(np.max(np.abs(run_b["E"] - run_a["E"]))),
        },
        "b_family_prediction_test": bfamily,
        "integrity": {
            "sha256_of_code": hashlib.sha256(
                open(os.path.abspath(__file__), "rb").read()
            ).hexdigest(),
            "snapshot_files": ["p5_snapshot_u.f64", "p5_snapshot_w.f64"],
            "snapshot_layout": "raw float64 C-order, shape (3, 48, 48, 48)",
        },
    }
    out = os.path.join(RESULTS, "p5_regularity.json")
    results_json_dump(protocol, out)
    print(f"[P5] wrote {out}")
    print(f"[P5] energy balance A: {sA['energy_balance_rel_max']:.2e}, "
          f"enstrophy balance A: {sA['enstrophy_balance_rel_max']:.2e}")
    print(f"[P5] div-free residual: {div_free_max:.2e}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
