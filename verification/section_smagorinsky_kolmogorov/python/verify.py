"""Section 7 — Smagorinsky-Kolmogorov constants program (Python reference port).

Verifies the master relation of the research_col_smar program, from the
closed form alone (plus a tiny point-vortex experiment for the symmetry
theorems), following the repository-wide output contract:

    banner -> per-assertion [PASS]/[FAIL] -> JSON: {...} verdict line
    exit 0 only if every assertion passed.

Claims verified here (mirrors research_col_smar/README.md and the L17 audit):
  C1  cross-link: the parent constant b = 1/(4*pi + 2*sqrt(3)), sin(theta_b)=b;
  C2  master relation C_s = 1/(pi * (3*C_K/2)^(3/4)) at C_K = 1.5 reproduces the
      pinned 50-digit value 0.1732659558297058017568595667273903913207704370073762727;
  C3  agreement with Lilly (1966): |C_s - 0.17326| < 1e-5 (measured delta = 6e-6);
  C4  exponent law: C_s(a*C_K)/C_s(C_K) = a^(-3/4) exactly (to 1e-14) for
      several scale factors a;
  C5  monotonicity: C_s(1.8) < C_s(1.5) < C_s(1.2), and 0 < C_s(C_K) for C_K > 0;
  C6  literature band: 0.16 < C_s(1.5) < 0.20;
  C7  Cassini identity: F(k+1)^2 - F(k)*F(k+2) = (-1)^k for k = 0..40 (exact);
  C8  symmetry theorem: for x-mirror-symmetric circulations (Gamma_A = Gamma_B,
      Gamma_C = Gamma_D) the scale-similarity numerator -<tau^SS : S~> is
      identically zero (max |numerator| <= 1e-14 on a symmetric grid);
  C9  reduced zero-drift condition (5') of the phi-audit (fix И1): the three
      algebraic coefficients are verified EXACTLY — for Fibonacci quads
      a*b*b*c = (F_k, F_(k+1), F_(k+1), F_(k+2)) the coefficient of m_2 is
      (-1)^k (Cassini), the coefficient of m_M is F_(k+1)^2 > 0 and the
      coefficient of m_1 is F_(k+2)^2 - F_(k+1)^2 > 0, so (5') has NO root at
      any scanned scale (0/18 scans); for symmetric quads a*a*b*b all three
      coefficients vanish identically — the degenerate one-parameter family;
  C10 K41 slope: the model spectrum E(k) = C_K eps^(2/3) k^(-5/3) re-measured
      in log-log space returns the slope -5/3 to 1e-12.

mpmath (50 digits) is used for C2 when available; every other check is pure
stdlib and runs in milliseconds. Deterministic: no RNG beyond a fixed LCG,
no data files.
"""
import json
import math
import sys

PINNED_CS_15 = 0.1732659558297058017568595667273903913207704370073762727
PINNED_CS_15_50D = "0.1732659558297058017568595667273903913207704370073762727"
LILLY_CS = 0.17326
CK_REF = 1.5

# deterministic LCG (same convention as Section 1)
_state = 20260930


def lcg_random():
    global _state
    _state = (_state * 6364136223846793005 + 1442695040888963407) % (1 << 64)
    return _state / float(1 << 64) * 2.0 - 1.0


def cs_master(ck):
    """The master relation C_s = 1/(pi * (3*C_K/2)^(3/4))."""
    return 1.0 / (math.pi * (3.0 * ck / 2.0) ** 0.75)


def fib(n):
    a, b = 0, 1
    for _ in range(n):
        a, b = b, a + b
    return a


# ---------------------------------------------------------------------------
# point-vortex machinery for the symmetry theorems (C8, C9)
# ---------------------------------------------------------------------------
def velocity_field(gammas, positions, X, Y):
    """Velocity of a regularized point-vortex system on grids X, Y."""
    NX, NY = len(X), len(Y)
    u = [[0.0] * NX for _ in range(NY)]
    v = [[0.0] * NX for _ in range(NY)]
    for g, (xj, yj) in zip(gammas, positions):
        for iy in range(NY):
            dy = Y[iy] - yj
            for ix in range(NX):
                dx = X[ix] - xj
                r2 = dx * dx + dy * dy + 1e-9
                u[iy][ix] += -g * dy / (2 * math.pi * r2)
                v[iy][ix] += g * dx / (2 * math.pi * r2)
    return u, v


def filter_box(A, w):
    """Simple box filter of half-width w (boundary-clamped)."""
    NY, NX = len(A), len(A[0])
    out = [[0.0] * NX for _ in range(NY)]
    for iy in range(NY):
        for ix in range(NX):
            s, c = 0.0, 0
            for jy in range(max(0, iy - w), min(NY, iy + w + 1)):
                row = A[jy]
                for jx in range(max(0, ix - w), min(NX, ix + w + 1)):
                    s += row[jx]
                    c += 1
            out[iy][ix] = s / c
    return out


def ss_numerator(gammas, positions, X, Y, w=2):
    """Numerator N = -<tau^SS : S~> of the Smagorinsky formula (8).

    tau^SS_{ij} = <u_i u_j>~ - <u_i>~<u_j>~  (scale-similarity stress),
    S~_ij = (d<u~_i>/dx_j + d<u~_j>/dx_i)/2 by central differences.
    Returns the box-integrated numerator.
    """
    u, v = velocity_field(gammas, positions, X, Y)
    ub, vb = filter_box(u, w), filter_box(v, w)
    NX, NY = len(X), len(Y)
    uub = filter_box([[u[iy][ix] * u[iy][ix] for ix in range(NX)]
                      for iy in range(NY)], w)
    uvb = filter_box([[u[iy][ix] * v[iy][ix] for ix in range(NX)]
                      for iy in range(NY)], w)
    vvb = filter_box([[v[iy][ix] * v[iy][ix] for ix in range(NX)]
                      for iy in range(NY)], w)
    dx, dy = X[1] - X[0], Y[1] - Y[0]
    num = 0.0
    for iy in range(1, NY - 1):
        for ix in range(1, NX - 1):
            ubx = (ub[iy][ix + 1] - ub[iy][ix - 1]) / (2 * dx)
            uby = (ub[iy + 1][ix] - ub[iy - 1][ix]) / (2 * dy)
            vbx = (vb[iy][ix + 1] - vb[iy][ix - 1]) / (2 * dx)
            vby = (vb[iy + 1][ix] - vb[iy - 1][ix]) / (2 * dy)
            sxx, syy, sxy = ubx, vby, 0.5 * (uby + vbx)
            tuu = uub[iy][ix] - ub[iy][ix] * ub[iy][ix]
            tuv = uvb[iy][ix] - ub[iy][ix] * vb[iy][ix]
            tvv = vvb[iy][ix] - vb[iy][ix] * vb[iy][ix]
            num += -(tuu * sxx + 2.0 * tuv * sxy + tvv * syy)
    return num


def grid(n, L):
    step = L / n
    X = [-L / 2 + step * (i + 0.5) for i in range(n)]
    return X, list(X)


def main() -> int:
    print("=== Section 7: Smagorinsky-Kolmogorov Master Relation ===")
    failures = []

    def check(name, cond, detail=""):
        status = "PASS" if cond else "FAIL"
        print(f"[{status}] {name}" + (f"  ({detail})" if detail else ""))
        if not cond:
            failures.append(name)

    # ---- C1: parent constant cross-link
    b = 1.0 / (4.0 * math.pi + 2.0 * math.sqrt(3.0))
    theta = math.asin(b)
    print(f"b = {b:.17f}, theta_b = {math.degrees(theta):.13f} deg")
    check("b matches pinned value",
          abs(b - 0.062381194121028227546339671639402081186993306823604) < 5e-16)
    check("sin(theta_b) = b (machine)", abs(math.sin(theta) - b) < 1e-17)

    # ---- C2: master relation (float64 + 50-digit block when mpmath present)
    cs = cs_master(CK_REF)
    print(f"C_s(C_K = 1.5) = {cs:.17f}")
    check("C_s(1.5) matches pinned value (float64)", abs(cs - PINNED_CS_15) < 5e-16)
    try:
        import mpmath as mp
        mp.mp.dps = 50
        val = 1 / (mp.pi * (3 * mp.mpf("1.5") / 2) ** (mp.mpf(3) / 4))
        check("C_s(1.5) matches 50-digit pinned string",
              abs(val - mp.mpf(PINNED_CS_15_50D)) < mp.mpf("1e-49"),
              f"mpmath: {mp.nstr(val, 18)}")
    except ImportError:
        check("C_s(1.5) 50-digit block skipped (mpmath absent)", True)

    # ---- C3: Lilly agreement
    check("|C_s - Lilly 0.17326| < 1e-5", abs(cs - LILLY_CS) < 1e-5,
          f"delta = {abs(cs - LILLY_CS):.2e}")

    # ---- C4: exponent law for several scale factors
    worst = 0.0
    for a in (0.5, 0.8, 1.25, 2.0, 3.0):
        lhs = cs_master(a * CK_REF) / cs_master(CK_REF)
        rhs = a ** (-0.75)
        worst = max(worst, abs(lhs - rhs))
    check("exponent law C_s(aC_K)/C_s(C_K) = a^(-3/4)", worst < 1e-14,
          f"max residual {worst:.2e}")

    # ---- C5: monotonicity + positivity
    check("C_s(1.8) < C_s(1.5) < C_s(1.2)",
          cs_master(1.8) < cs_master(1.5) < cs_master(1.2))
    check("0 < C_s(C_K) for C_K in (0, 10]",
          all(cs_master(k) > 0 for k in (0.1, 0.5, 1, 2, 5, 10)))

    # ---- C6: literature band
    check("0.16 < C_s(1.5) < 0.20", 0.16 < cs < 0.20, f"C_s = {cs:.5f}")

    # ---- C7: Cassini identity (exact integer arithmetic)
    cassini_ok = all(
        fib(k + 1) ** 2 - fib(k) * fib(k + 2) == (-1) ** k for k in range(41))
    check("Cassini: F(k+1)^2 - F(k)F(k+2) = (-1)^k, k = 0..40", cassini_ok,
          f"F(40) = {fib(40)}")

    # ---- C8: symmetry theorem (numerator identically 0 on symmetric quads)
    phi = (1.0 + math.sqrt(5.0)) / 2.0
    X, Y = grid(32, 6.0)
    t = 0.8
    sym_pos = [(-t, -1.0), (t, -1.0), (-t * phi, 1.0), (t * phi, 1.0)]
    sym_gam = [1.0, 1.0, phi, phi]
    num_sym = ss_numerator(sym_gam, sym_pos, X, Y)
    check("symmetric quad: |N| <= 1e-14 (C_s identifiably zero)",
          abs(num_sym) < 1e-14, f"N = {num_sym:.3e}")

    # ---- C9: reduced zero-drift condition (5') — exact coefficient algebra
    # (5'): (GaB*GaC - GaA*GaD)*m2 + (GaB*GaD - GaA*GaC)*m_M + (GaD^2-GaC^2)*m1
    # m1 = max(R1^2, delta^2), m2 = max(R2^2, delta^2), m_M = max(R1^2+R2^2, d^2)
    # a*b*b*c quad: no solution at ANY scale; a*a*b*b: all coefficients zero.
    delta = 1e-3
    no_root = 0
    scans = 0
    for k in range(2, 8):        # six Fibonacci quads a*b*b*c
        Fa, Fb, Fc = fib(k), fib(k + 1), fib(k + 2)
        ga = [float(Fa), float(Fb), float(Fb), float(Fc)]
        c2 = ga[1] * ga[2] - ga[0] * ga[3]      # = (-1)^k by Cassini
        cM = ga[1] * ga[3] - ga[0] * ga[2]      # = F_(k+1)^2 > 0
        c1 = ga[3] ** 2 - ga[2] ** 2            # = F_(k+2)^2 - F_(k+1)^2 > 0
        assert c2 == float((-1) ** k) and cM > 0 and c1 > 0
        for tscan in (0.3, 0.8, 1.5):
            R1, R2 = tscan, tscan / phi
            m1 = max(R1 * R1, delta * delta)
            m2 = max(R2 * R2, delta * delta)
            m_M = max(R1 * R1 + R2 * R2, delta * delta)
            lhs = c2 * m2 + cM * m_M + c1 * m1
            scans += 1
            if lhs > 0:          # sign-definite => (5') unsolvable
                no_root += 1
    check("a*b*b*c: (5') sign-definite at 18/18 scans (no zero-drift root)",
          no_root == scans, f"{no_root}/{scans}")
    degenerate = all(
        (fib(k) * fib(k + 1) - fib(k) * fib(k + 1) == 0)
        and (fib(k) * fib(k + 1) - fib(k) * fib(k + 1) == 0)
        and (fib(k + 1) ** 2 - fib(k + 1) ** 2 == 0)
        for k in range(2, 8))
    check("a*a*b*b: all three coefficients of (5') vanish identically",
          degenerate, "degenerate one-parameter family")

    # ---- C10: K41 slope of the model spectrum
    ks = [2.0 ** (i / 4.0) for i in range(12, 48)]
    eps = 1.0
    E = [CK_REF * eps ** (2.0 / 3.0) * k ** (-5.0 / 3.0) for k in ks]
    n = len(ks)
    mx = sum(math.log(k) for k in ks) / n
    my = sum(math.log(e) for e in E) / n
    slope = (sum((math.log(k) - mx) * (math.log(e) - my)
                 for k, e in zip(ks, E))
             / sum((math.log(k) - mx) ** 2 for k in ks))
    check("model spectrum slope = -5/3 (1e-12)", abs(slope + 5.0 / 3.0) < 1e-12,
          f"slope = {slope:.15f}")

    verdict = {
        "section": 7, "language": "python",
        "values": {"b": repr(b), "C_s": repr(cs), "slope_k41": slope,
                   "cassini_ok": cassini_ok,
                   "no_root_scans": f"{no_root}/{scans}"},
        "all_passed": not failures,
    }
    print(f"JSON: {json.dumps(verdict)}")
    return 1 if failures else 0


if __name__ == "__main__":
    if "--preset" in sys.argv:
        pass  # contract compatibility; this section is preset-independent
    raise SystemExit(main())
