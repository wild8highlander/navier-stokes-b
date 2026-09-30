"""P5-D cross-language check: Python (f64, LAPACK eigh) vs C++ (long double,
Jacobi) vs Julia (Float64, GenericLinAlg/eigen) on the SAME artifact.

Artifact: results/p5d_tensors_dns.f64 — the (S, omega) point-tensor dump of
the primary 64^3 ensemble run (nu = 0.01, seed 20261101, t = 5), layout
point-major (n, n, n, 9) with channels [Sxx,Syy,Szz,Sxy,Sxz,Syz,wx,wy,wz].

Python recomputes the P5-C scalar block (s_rms, mean strain eigenvalues,
beta_S, <cos^2 theta_i>, alpha mean/std) and the P5-D Q-R block
(q = Q/<S:S>, r = R/<S:S>^{3/2}, D_S = (r/2)^2 + (q/3)^3, masses, tail
proximity with the q < -0.5 restriction) directly from the dumped tensors —
the same quantities as code/cpp/p5d_qr.cpp (results/p5d_cpp.json) and
code/julia/p5d_qr.jl (results/p5d_julia.json).

Agreement target: relative deviation <= 1e-10 on every scalar.
Output: results/p5d_cross_language.json (status PASS/FAIL).
"""
from __future__ import annotations

import json
import os
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
RESULTS = os.path.join(ROOT, "results")

N = 64
CHANNELS = 9


ABS_FLOOR = 1e-12  # absolute floor for near-zero quantities (q_mean ~ 1e-18)


def rel(a: float, b: float) -> float:
    """Relative deviation with an absolute floor.

    The mean invariants <q*> and <r*> vanish identically for any
    divergence-free field (they are ~1e-18 here), so a pure relative
    metric is degenerate on them; the floor makes the deviation
    meaningful for both O(1) and near-zero scalars.
    """
    return abs(a - b) / max(abs(a), abs(b), ABS_FLOOR)


def stats_from_tensors(T: np.ndarray) -> dict:
    """All P5-C + P5-D scalars from the (9, n, n, n) tensor block."""
    sxx, syy, szz = T[0], T[1], T[2]
    sxy, sxz, syz = T[3], T[4], T[5]
    wx, wy, wz = T[6], T[7], T[8]
    ss = sxx**2 + syy**2 + szz**2 + 2.0 * (sxy**2 + sxz**2 + syz**2)
    s2m = float(np.mean(ss))
    s_rms = float(np.sqrt(s2m))
    s2m_15 = s2m * np.sqrt(s2m)
    npt = ss.size
    S = np.empty((npt, 3, 3), dtype=np.float64)
    S[:, 0, 0] = sxx.ravel()
    S[:, 1, 1] = syy.ravel()
    S[:, 2, 2] = szz.ravel()
    S[:, 0, 1] = S[:, 1, 0] = sxy.ravel()
    S[:, 0, 2] = S[:, 2, 0] = sxz.ravel()
    S[:, 1, 2] = S[:, 2, 1] = syz.ravel()
    eigvals, eigvecs = np.linalg.eigh(S)  # ascending
    lam = eigvals[:, ::-1] / s_rms        # descending, normalized
    vec = np.moveaxis(eigvecs[:, :, ::-1], -1, 0).copy()  # (3, npt, 3)
    wr = np.stack([wx.ravel(), wy.ravel(), wz.ravel()], axis=1)
    wn = np.linalg.norm(wr, axis=1)
    wh = wr / np.maximum(wn[:, None], 1e-300)
    cos = np.empty((3, npt))
    for a in range(3):
        cos[a] = np.einsum("nj,nj->n", wh, vec[a])
    cos2 = [float(np.mean(cos[a] ** 2)) for a in range(3)]
    wSw = np.einsum("ni,nij,nj->n", wr, S, wr)
    alpha = wSw / np.maximum(wn**2, 1e-300) / s_rms
    mean_lam = [float(np.mean(lam[:, a])) for a in range(3)]
    beta_s = mean_lam[1] / (mean_lam[0] - mean_lam[2])
    # ---- Q-R block from the SAME (S, omega) tensors ----
    w2 = wx**2 + wy**2 + wz**2
    q = (0.25 * w2 - 0.5 * ss) / s2m
    A12 = sxy - 0.5 * wz
    A13 = sxz + 0.5 * wy
    A21 = sxy + 0.5 * wz
    A23 = syz - 0.5 * wx
    A31 = sxz - 0.5 * wy
    A32 = syz + 0.5 * wx
    det = (
        sxx * (syy * szz - A23 * A32)
        - A12 * (A21 * szz - A23 * A31)
        + A13 * (A21 * A32 - syy * A31)
    )
    r = -det / s2m_15
    d_s = (r / 2.0) ** 2 + (q / 3.0) ** 3
    m_tail = q < -0.5
    x_tail = np.zeros_like(q)
    x_tail[m_tail] = 27.0 * r[m_tail] ** 2 / (-4.0 * q[m_tail] ** 3)
    qr = {
        "q_mean_norm": float(np.mean(q)),
        "r_mean_norm": float(np.mean(r)),
        "r_std_norm": float(np.std(r)),
        "p_q_pos": float(np.mean(q > 0.0)),
        "p_qneg_node": float(np.mean((q < 0.0) & (d_s >= 0.0))),
        "p_qneg_focal": float(np.mean((q < 0.0) & (d_s < 0.0))),
        "p_qp_rn": float(np.mean((q > 0.0) & (r < 0.0))),
        "p_qp_rp": float(np.mean((q > 0.0) & (r > 0.0))),
        "p_qn_rn": float(np.mean((q < 0.0) & (r < 0.0))),
        "p_qn_rp": float(np.mean((q < 0.0) & (r > 0.0))),
        "tail_rel_mean": float(np.mean(x_tail[m_tail])),
        "tail_pop_frac": float(np.mean(x_tail[m_tail] >= 0.9)),
    }
    return {
        "s_rms": s_rms,
        "mean_lam": mean_lam,
        "beta_S": float(beta_s),
        "cos2": cos2,
        "alpha_mean": float(np.mean(alpha)),
        "alpha_std": float(np.std(alpha)),
        "qr": qr,
    }


def flatten(st: dict) -> dict:
    out = {
        "s_rms": st["s_rms"],
        "beta_S": st["beta_S"],
        "alpha_mean": st["alpha_mean"],
        "alpha_std": st["alpha_std"],
    }
    for a in range(3):
        out[f"mean_lam_{a}"] = st["mean_lam"][a]
        out[f"cos2_{a}"] = st["cos2"][a]
    for k, v in st["qr"].items():
        out[f"qr.{k}"] = v
    return out


def main() -> int:
    path = os.path.join(RESULTS, "p5d_tensors_dns.f64")
    raw = np.fromfile(path, dtype=np.float64)
    assert raw.size == CHANNELS * N**3, f"bad tensor file: {path}"
    # the dump is POINT-major (n, n, n, 9) C-order (offset = channel + 9*point):
    # decode with the channel axis LAST, then move it to the front — the
    # same layout convention the C++ reader (raw[p*9+c]) and the Julia
    # reader (column-major reshape(9, N, N, N)) implement.
    T = np.ascontiguousarray(raw.reshape(N, N, N, CHANNELS).transpose(3, 0, 1, 2))
    py = flatten(stats_from_tensors(T))

    with open(os.path.join(RESULTS, "p5d_cpp.json"), encoding="utf-8") as fh:
        cpp_j = json.load(fh)
    with open(os.path.join(RESULTS, "p5d_julia.json"), encoding="utf-8") as fh:
        jul_j = json.load(fh)

    def lang_flat(d: dict) -> dict:
        out = {
            "s_rms": d["s_rms"],
            "beta_S": d["beta_S"],
            "alpha_mean": d["alpha_mean"],
            "alpha_std": d["alpha_std"],
        }
        for a in range(3):
            out[f"mean_lam_{a}"] = d["mean_lam"][a]
            out[f"cos2_{a}"] = d["cos2"][a]
        for k, v in d["qr"].items():
            out[f"qr.{k}"] = v
        return out

    cpp = lang_flat(cpp_j)
    jul = lang_flat(jul_j)
    tol = 1e-10
    # <q*> and <r*> are identically zero for every divergence-free field
    # (exact algebraic identity); each is a sum of ~2.6e5 mutually
    # canceling terms, so its computed value is pure rounding noise at
    # the f64 accumulation level (~3e-12). They are verified as
    # IDENTITY CHECKS (absolute bound + pairwise agreement), not
    # compared at the strict relative tolerance.
    identity_keys = ("qr.q_mean_norm", "qr.r_mean_norm")
    strict_keys = [k for k in py if k not in identity_keys]
    dev = {"cpp": {}, "julia": {}}
    worst = {"cpp": 0.0, "julia": 0.0}
    for name, other in (("cpp", cpp), ("julia", jul)):
        for k in strict_keys:
            d = rel(py[k], other[k])
            dev[name][k] = d
            worst[name] = max(worst[name], d)
    ident = {}
    ident_ok = True
    for k in identity_keys:
        vals = {"python": py[k], "cpp": cpp[k], "julia": jul[k]}
        max_abs = max(abs(v) for v in vals.values())
        pair = max(
            abs(vals[a] - vals[b])
            for a in vals for b in vals
        )
        ok = max_abs <= 1e-11 and pair <= 1e-11
        ident_ok = ident_ok and ok
        ident[k] = {"values": vals, "max_abs": max_abs, "max_pairwise": pair,
                    "ok": ok}
    out = {
        "program": "P5D cross-language verification (Python/C++/Julia)",
        "date": "2026-09-30",
        "artifact": "p5d_tensors_dns.f64",
        "artifact_note": (
            "(S, omega) point-tensor dump of run n064_nu0p010_s20261101 at "
            "t=5; the C++/Julia tracks recompute every scalar from this "
            "file in their own arithmetic (long double / Float64)"
        ),
        "nScalars": len(strict_keys),
        "tolerance": tol,
        "metric": "rel(a,b) = |a-b| / max(|a|, |b|, 1e-12); the absolute floor only affects near-zero scalars",
        "max_rel_dev": worst,
        "deviations": dev,
        "identity_checks": {
            "note": (
                "<q*> and <r*> vanish identically for divergence-free "
                "fields; the computed values are f64 accumulation noise "
                "(bounded by 1e-11 absolute) and verify the exact "
                "cancellation in all three arithmetic environments"
            ),
            "tolerance_abs": 1e-11,
            "entries": ident,
            "status": "PASS" if ident_ok else "FAIL",
        },
        "status": (
            "PASS"
            if (max(worst.values()) <= tol and ident_ok)
            else "FAIL"
        ),
    }
    dst = os.path.join(RESULTS, "p5d_cross_language.json")
    with open(dst, "w", encoding="utf-8") as fh:
        json.dump(out, fh, indent=2, sort_keys=True)
        fh.write("\n")
    print(f"[P5-x] status = {out['status']} -> {dst}")
    return 0 if out["status"] == "PASS" else 1


if __name__ == "__main__":
    sys.exit(main())
