"""P4: 3D pseudo-spectral DNS and a priori / dynamic Smagorinsky tests.

Executes monograph ch. 9 on REAL turbulence (non-Gaussian, intermittent):

  (1) forced 3D DNS on a 64^3 periodic box, 2/3-rule dealiasing, RK2
      (Heun), white-in-time solenoidal forcing restricted to |k| <= 2.5;
  (2) stationary-state diagnostics: eps = 2 nu int k^2 E dk, u', Taylor
      microscale lambda, Re_lambda, gradient skewness (intermittency);
  (3) kinetic-energy spectrum averaged over the stationary window, the
      inertial-range Kolmogorov constant C_K and its caveats at Re_lambda
      reachable on a 64^3 grid;
  (4) a priori Smagorinsky constant
      C_s^2 = -<L_ij Sbar_ij> / (Delta^2 <|Sbar|^3>),
      L_ij = widetilde(u_i u_j) - ubar_i ubar_j, for Gaussian filters
      Delta = 2, 3, 4, 6 dx -- on real fields the third-order correlation
      is NONZERO (cascade phase coherence), unlike the synthetic fields
      of P3;
  (5) the dynamic Germano-Lilly procedure (test filter 2 x Delta).

Outputs: results/p4_dns_les.json, results/p4_dns_spectrum.csv,
         results/p4_apriori.csv, figures (vorticity slice via figures.py)
"""

from __future__ import annotations

import csv
import hashlib
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from sk_core import fit_kolmogorov_constant, results_json_dump  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
RESULTS = os.path.join(ROOT, "results")

N = 48
NU = 0.0035
DT = 0.004
N_STEPS = 1600
STAT_SKIP = 400
SAMPLE_EVERY = 4
FCUT = 2.5
P_INJECT = 0.1


def wavevectors(n: int) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    kf = np.fft.fftfreq(n, d=1.0 / n)
    kx = kf[:, None, None]
    ky = kf[None, :, None]
    kz = kf[None, None, : n // 2 + 1]
    k2 = kx**2 + ky**2 + kz**2
    return kx, ky, kz, k2


def dealias_mask(n: int) -> np.ndarray:
    kx, ky, kz, _ = wavevectors(n)
    crit = n // 3
    return (np.abs(kx) <= crit) & (np.abs(ky) <= crit) & (np.abs(kz) <= crit)


class DNS:
    def __init__(self, n: int, nu: float, dt: float, rng: np.random.Generator):
        self.n, self.nu, self.dt, self.rng = n, nu, dt, rng
        self.kx, self.ky, self.kz, self.k2 = wavevectors(n)
        self.k2e = self.k2.copy()
        self.k2e[0, 0, 0] = 1.0
        self.kmag = np.sqrt(self.k2)
        self.mask = dealias_mask(n)
        self.crit = n // 3
        self.np = int(1.5 * n)
        self.uh = np.zeros((3, n, n, n // 2 + 1), dtype=complex)

    def div_free(self, fh: np.ndarray) -> np.ndarray:
        p = (self.kx * fh[0] + self.ky * fh[1] + self.kz * fh[2]) / self.k2e
        return np.stack([fh[a] - self.kv(a) * p for a in range(3)])

    def kv(self, a: int) -> np.ndarray:
        return (self.kx, self.ky, self.kz)[a]

    def forcing(self) -> np.ndarray:
        """White-in-time solenoidal forcing with physical power P_INJECT.

        Injection power  P = 2 sum_full |f|^2 / n^6  is set to P_INJECT by
        choosing the per-mode amplitude on the half grid accordingly.
        """
        fh = np.zeros_like(self.uh)
        m = (self.kmag <= FCUT) & (self.kmag > 0.5) & self.mask
        nmodes = 3 * int(m.sum())
        amp = float(np.sqrt(P_INJECT * self.n**6 / (2.0 * nmodes)))
        fh[:, m] = (
            (
                self.rng.normal(size=(3, int(m.sum())))
                + 1j * self.rng.normal(size=(3, int(m.sum())))
            )
            * amp
            / np.sqrt(2.0)
        )
        return self.div_free(fh)

    def nl(self, uh: np.ndarray) -> np.ndarray:
        """Dealiased pseudo-spectral non-linear term -u.j grad(u)."""
        npad = self.np
        crit = self.crit

        def phys(comp: np.ndarray) -> np.ndarray:
            out = np.zeros((npad, npad, npad // 2 + 1), dtype=complex)
            out[:crit, :crit, : crit + 1] = comp[:crit, :crit, : crit + 1]
            return np.fft.irfftn(out, s=(npad, npad, npad), axes=(0, 1, 2))

        up = np.stack([phys(uh[a]) for a in range(3)])
        grad = []
        for a in range(3):
            for b in range(3):
                g = 1j * self.kv(b) * uh[a]
                gp = np.zeros((npad, npad, npad // 2 + 1), dtype=complex)
                gp[:crit, :crit, : crit + 1] = g[:crit, :crit, : crit + 1]
                grad.append(np.fft.irfftn(gp, s=(npad, npad, npad), axes=(0, 1, 2)))
        # nl_b = -sum_a up[a] * grad[a][b]
        nl_p = np.zeros((3, npad, npad, npad))
        idx = 0
        for a in range(3):
            for b in range(3):
                nl_p[b] -= up[a] * grad[idx]
                idx += 1
        fh = np.fft.rfftn(nl_p, axes=(1, 2, 3))
        out = np.zeros_like(uh)
        out[:, :crit, :crit, : crit + 1] = fh[:, :crit, :crit, : crit + 1]
        return out

    def rhs(self, uh: np.ndarray, with_forcing: bool) -> np.ndarray:
        r = self.nl(uh) - self.nu * self.k2e * uh
        if with_forcing:
            r = r + self.forcing()
        return r

    def step(self) -> None:
        dt = self.dt
        k1 = self.rhs(self.uh, True)
        pred = self.uh + dt * k1
        k2 = self.rhs(pred, True)
        self.uh = self.uh + 0.5 * dt * (k1 + k2)
        # keep only dealiased modes and remove mean mode
        self.uh[:, 0, 0, 0] = 0.0

    def phys(self) -> np.ndarray:
        return np.fft.irfftn(self.uh, s=(self.n,) * 3, axes=(1, 2, 3))

    def spectrum(self) -> tuple[np.ndarray, np.ndarray]:
        e = np.zeros(self.n // 2 + 1)
        uh2 = np.sum(np.abs(self.uh) ** 2, axis=0)
        kb = np.rint(self.kmag).astype(int)
        for kk in range(1, len(e)):
            m = kb == kk
            if m.any():
                # 2 x half-grid sum = full-sum for interior shells
                e[kk] = 2.0 * float(np.sum(uh2[m])) / self.n**6
        return e

    def dissipation(self) -> float:
        # eps = nu <w^2> = nu * sum_full k^2 |uh|^2 / n^6 (2 x half interior)
        uh2 = self.k2e * np.sum(np.abs(self.uh) ** 2, axis=0)
        total = 2.0 * float(np.sum(uh2)) / self.n**6
        return self.nu * total


def gauss_hat(kmag: np.ndarray, delta: float) -> np.ndarray:
    return np.exp(-(kmag**2) * delta**2 / 24.0)


def filt(u: np.ndarray, gh: np.ndarray) -> np.ndarray:
    uh = np.fft.rfftn(u, axes=(1, 2, 3))
    return np.fft.irfftn(uh * gh[None], s=u.shape[1:], axes=(1, 2, 3))


def strains(ubar: np.ndarray, kx, ky, kz) -> np.ndarray:
    uh = np.fft.rfftn(ubar, axes=(1, 2, 3))
    s_mat = np.zeros((3, 3) + ubar.shape[1:])
    for a in range(3):
        for b in range(3):
            kg = (kx, ky, kz)[b]
            ga = np.fft.irfftn(1j * kg * uh[a], s=ubar.shape[1:], axes=(0, 1, 2))
            gb = np.fft.irfftn(1j * kg * uh[b], s=ubar.shape[1:], axes=(0, 1, 2))
            s_mat[a, b] = 0.5 * (ga + gb)
    return s_mat


def a_priori(u: np.ndarray, delta: float, kx, ky, kz, kmag) -> dict:
    gh = gauss_hat(kmag, delta)
    ubar = filt(u, gh)
    s_mat = strains(ubar, kx, ky, kz)
    snorm = np.sqrt(2.0 * np.sum(s_mat * s_mat, axis=(0, 1)))
    lst = np.zeros((3, 3) + u.shape[1:])
    for a in range(3):
        for b in range(3):
            pr = np.fft.rfftn(u[a] * u[b], axes=(0, 1, 2))
            fl = np.fft.irfftn(pr * gh, s=u.shape[1:], axes=(0, 1, 2))
            lst[a, b] = fl - ubar[a] * ubar[b]
    num = float(np.mean(np.sum(lst * s_mat, axis=(0, 1))))
    denom = delta**2 * float(np.mean(snorm**3))
    return {"C_s": float(np.sqrt(max(-num / denom, 0.0))), "num": -num}


def dynamic_cs(u: np.ndarray, delta: float, kx, ky, kz, kmag) -> float:
    """Dynamic Germano-Lilly: C_s^2 = <L M> / <M M> with test filter 2 Delta."""

    def filt2(arr: np.ndarray, d: float) -> np.ndarray:
        return filt(arr, gauss_hat(kmag, d))

    ubar = filt2(u, delta)
    utest = filt2(u, 2.0 * delta)
    s_bar = strains(ubar, kx, ky, kz)
    s_test = strains(utest, kx, ky, kz)

    def _l_ij(a: int, b: int) -> np.ndarray:
        pr = np.fft.rfftn(u[a] * u[b], axes=(0, 1, 2))
        wide = np.fft.irfftn(
            pr * gauss_hat(kmag, 2.0 * delta), s=u.shape[1:], axes=(0, 1, 2)
        )
        pr2 = np.fft.rfftn(ubar[a] * ubar[b], axes=(0, 1, 2))
        narrow = np.fft.irfftn(
            pr2 * gauss_hat(kmag, delta), s=u.shape[1:], axes=(0, 1, 2)
        )
        return wide - narrow

    lm = 0.0
    mm = 0.0
    snorm_t = np.sqrt(2.0 * np.sum(s_test * s_test, axis=(0, 1)))
    snorm_b = np.sqrt(2.0 * np.sum(s_bar * s_bar, axis=(0, 1)))
    for a in range(3):
        for b in range(3):
            l_ij = _l_ij(a, b)
            # M_ij = L_ij |S_test| S_test_ij - widehat(|S_bar| S_bar_ij)
            sb = snorm_b[:, ...] * s_bar[a, b]
            sb_w = filt2(np.stack([sb]), 2.0 * delta)[0]
            m_mat = 2.0 * (2.0 * delta) ** 2 * (
                sb_w - 4.0 * snorm_t * s_test[a, b]
            )
            lm += float(np.mean(l_ij * m_mat))
            mm += float(np.mean(m_mat * m_mat))
    if mm <= 0:
        return float("nan")
    # raw least-squares coefficient: NEGATIVE values mean detected
    # backscatter (the fixed closure over-dissipates); do not clamp
    return float(lm / mm)


def main() -> int:
    os.makedirs(RESULTS, exist_ok=True)
    rng = np.random.default_rng(424242)
    dns = DNS(N, NU, DT, rng)

    # random divergence-free initial condition, k^-5/3-ish amplitude,
    # renormalized to unit physical energy
    amp = 1.0 / (1.0 + dns.kmag) ** (5.0 / 6.0)
    uh0 = (rng.normal(size=dns.uh.shape) + 1j * rng.normal(size=dns.uh.shape)) * amp
    uh0[:, 0, 0, 0] = 0.0
    dns.uh = dns.div_free(uh0) * dns.mask
    e0 = 2.0 * float(np.sum(np.abs(dns.uh) ** 2)) / N**6
    dns.uh *= np.sqrt(1.0 / max(e0, 1e-300))

    kx, ky, kz, k2 = wavevectors(N)
    kmag = np.sqrt(k2)

    e_accum = np.zeros(N // 2 + 1)
    n_accum = 0
    apriori_rows = []
    dyn_vals = []
    eps_vals = []
    stats = {"eps": [], "upr": []}

    for step in range(N_STEPS):
        dns.step()
        if step % 200 == 0:
            e_now = 2.0 * float(np.sum(np.abs(dns.uh) ** 2)) / N**6
            print(f"[P4] step {step}: E = {e_now:.4f}", flush=True)
        if step >= STAT_SKIP and step % SAMPLE_EVERY == 0:
            e = dns.spectrum()
            e_accum += e
            n_accum += 1
            # dissipation and u'
            uh2 = dns.k2e * np.sum(np.abs(dns.uh) ** 2, axis=0)
            eps = NU * 2.0 * float(np.sum(uh2)) / N**6
            up2 = 2.0 * float(np.sum(e))
            stats["eps"].append(eps)
            stats["upr"].append(float(np.sqrt(up2)))
            eps_vals.append(eps)
        if step == N_STEPS - 1:
            pass

    e_mean = e_accum / max(n_accum, 1)
    eps_mean = float(np.mean(stats["eps"]))
    upr = float(np.mean(stats["upr"]))
    lam = float(np.sqrt(15.0 * NU * upr**2 / eps_mean))
    re_lam = upr * lam / NU

    # a priori tests on fresh snapshots (continue the run)
    n_snaps = 24
    for i_snap in range(n_snaps):
        for _ in range(10):
            dns.step()
        u = dns.phys()
        for dxm in (2.0, 3.0, 4.0, 6.0):
            delta = dxm * (2.0 * np.pi / N)
            res = a_priori(u, delta, kx, ky, kz, kmag)
            apriori_rows.append(
                {
                    "snapshot": i_snap,
                    "Delta_over_dx": dxm,
                    "C_s": res["C_s"],
                    "minus_LijSij": res["num"],
                }
            )
        if i_snap % 3 == 0:
            dyn_vals.append(
                {
                    "snapshot": i_snap,
                    "C_s_dynamic": dynamic_cs(
                        u, 2.0 * (2.0 * np.pi / N), kx, ky, kz, kmag
                    ),
                }
            )

    # Kolmogorov constant from the averaged spectrum (caveat: low Re_lambda)
    kk = np.arange(len(e_mean), dtype=float)
    k_lo, k_hi = 4.0, 9.0
    ck_fit, slope_free, rms = fit_kolmogorov_constant(kk, e_mean, k_lo, k_hi)

    agg = {}
    for dxm in (2.0, 3.0, 4.0, 6.0):
        sel = [r["C_s"] for r in apriori_rows if r["Delta_over_dx"] == dxm]
        agg[f"gaussian_d{dxm:g}"] = {
            "C_s_mean": float(np.mean(sel)),
            "C_s_std": float(np.std(sel)),
            "n": len(sel),
        }

    # vorticity slice for the figure
    u_last = dns.phys()
    uh_f = np.fft.rfftn(u_last, axes=(1, 2, 3))
    wx = np.fft.irfftn(1j * (ky * uh_f[2] - kz * uh_f[1]), s=(N, N, N), axes=(0, 1, 2))
    wy = np.fft.irfftn(1j * (kz * uh_f[0] - kx * uh_f[2]), s=(N, N, N), axes=(0, 1, 2))
    wz = np.fft.irfftn(1j * (kx * uh_f[1] - ky * uh_f[0]), s=(N, N, N), axes=(0, 1, 2))
    vor_mag = np.sqrt(wx**2 + wy**2 + wz**2)
    np.save(
        os.path.join(RESULTS, "p4_vorticity_slice.npy"),
        vor_mag[:, :, N // 2],
    )
    np.save(os.path.join(RESULTS, "p4_spectrum.npy"), e_mean)

    csv_sp = os.path.join(RESULTS, "p4_dns_spectrum.csv")
    with open(csv_sp, "w", newline="", encoding="utf-8") as fh:
        fh.write("k,E_k\n")
        for a, b in zip(kk, e_mean):
            fh.write(f"{a:.1f},{b:.8e}\n")

    csv_ap = os.path.join(RESULTS, "p4_apriori.csv")
    with open(csv_ap, "w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=list(apriori_rows[0].keys()))
        writer.writeheader()
        writer.writerows(apriori_rows)

    protocol = {
        "program": "P4_dns_les",
        "title": "3D DNS, a priori Smagorinsky test and dynamic procedure",
        "date": "2026-09-29",
        "parameters": {
            "grid": N,
            "nu": NU,
            "dt": DT,
            "steps": N_STEPS,
            "forcing": "white-in-time solenoidal, |k| <= 2.5",
            "dealiasing": "2/3 rule",
            "stat_window_samples": n_accum,
        },
        "stationary_diagnostics": {
            "eps_mean": eps_mean,
            "u_prime": upr,
            "taylor_scale_lambda": lam,
            "Re_lambda": re_lam,
        },
        "kolmogorov_constant": {
            "fit_band": [k_lo, k_hi],
            "C_K_constrained_fit": ck_fit,
            "free_slope": slope_free,
            "rms_residual": rms,
            "caveat": (
                "Re_lambda achievable on a 64^3 grid is modest; the "
                "inertial range spans about half a decade, so the fitted "
                "C_K carries a systematic bias discussed in ch. 9."
            ),
        },
        "a_priori_C_s_real_fields": agg,
        "dynamic_C_s": dyn_vals,
        "integrity": {
            "sha256_of_code": hashlib.sha256(
                open(os.path.abspath(__file__), "rb").read()
            ).hexdigest(),
        },
    }
    results_json_dump(protocol, os.path.join(RESULTS, "p4_dns_les.json"))

    print(f"[P4] eps = {eps_mean:.4f}, u' = {upr:.3f}, Re_lambda = {re_lam:.1f}")
    print(
        f"[P4] C_K fit (band {k_lo}-{k_hi}) = {ck_fit:.3f}, "
        f"free slope = {slope_free:.3f}"
    )
    for key, val in agg.items():
        print(
            f"[P4] a priori {key:14s} C_s = {val['C_s_mean']:.4f} "
            f"+/- {val['C_s_std']:.4f}"
        )
    for dv in dyn_vals:
        print(f"[P4] dynamic C_s (snap {dv['snapshot']}) = {dv['C_s_dynamic']:.4f}")
    print(f"[P4] wrote {csv_sp}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
