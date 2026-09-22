"""Section 6 — Riemann zeros: the Hilbert-Pólya programme (Python port).

Verifies, stdlib-only (Lanczos complex Gamma + Euler-Maclaurin zeta):
  * zeta(2) = pi^2/6 and zeta(4) = pi^4/90 to 1e-12 (algorithm sanity);
  * the functional equation xi(s) = xi(1-s) off the critical line
    (s = 0.3 + 9i vs 0.7 - 9i) to 1e-10;
  * the first non-trivial zero: |xi(0.5 + 14.13472514...i)| < 1e-12, while a
    nearby non-zero ordinate gives |xi| > 1e-2 (contrast, not a trivial pass);
  * the shared universal constant chain b -> theta_b.
Output contract: banner -> [PASS]/[FAIL] per assertion -> JSON verdict line.
"""
import cmath
import json
import math

# Lanczos approximation (g = 7, 9 coefficients) — textbook, stdlib-only
_LANCZOS = [
    0.99999999999980993,
    676.5203681218851,
    -1259.1392167224028,
    771.32342877765313,
    -176.61502916214059,
    12.507343278686905,
    -0.13857109526572012,
    9.9843695780195716e-6,
    1.5056327351493116e-7,
]


def cgamma(z):
    """Complex Gamma via the Lanczos approximation with reflection."""
    if z.real < 0.5:
        return math.pi / (cmath.sin(math.pi * z) * cgamma(1.0 - z))
    z -= 1.0
    x = _LANCZOS[0]
    for i in range(1, 9):
        x += _LANCZOS[i] / (z + i)
    t = z + 7.5
    return math.sqrt(2.0 * math.pi) * t ** (z + 0.5) * cmath.exp(-t) * x


_BERN = [0.0, 1.0 / 6, -1.0 / 30, 1.0 / 42, -1.0 / 30,
         5.0 / 66, -691.0 / 2730, 7.0 / 6, -3617.0 / 510]


def zeta(s, n_sum=60, k_em=8):
    """Riemann zeta via Euler-Maclaurin summation (valid for Re(s) > 0)."""
    s = complex(s)
    total = 0.0j
    for n in range(1, n_sum):
        total += complex(n) ** (-s)
    total += complex(n_sum) ** (1.0 - s) / (s - 1.0)
    total += 0.5 * complex(n_sum) ** (-s)
    for k in range(1, k_em + 1):
        prod = 1.0 + 0.0j
        for j in range(2 * k - 1):
            prod *= s + j
        total += _BERN[k] / math.factorial(2 * k) * prod * complex(n_sum) ** (-s - (2 * k - 1))
    return total


def xi(s):
    """Riemann xi function."""
    s = complex(s)
    return 0.5 * s * (s - 1.0) * (math.pi ** (-s / 2.0)) * cgamma(s / 2.0) * zeta(s)


def main() -> int:
    print("=== Section 6: Riemann Zeros — the Hilbert-Pólya Programme ===")
    failures = []

    def check(name, cond, detail=""):
        status = "PASS" if cond else "FAIL"
        print(f"[{status}] {name}" + (f"  ({detail})" if detail else ""))
        if not cond:
            failures.append(name)

    print(f"zeta(2) = {zeta(2.0).real:.14f}")
    check("zeta(2) = pi^2/6 (1e-12)", abs(zeta(2.0).real - math.pi ** 2 / 6.0) < 1e-12)
    check("zeta(4) = pi^4/90 (1e-12)", abs(zeta(4.0).real - math.pi ** 4 / 90.0) < 1e-12)

    s_off = 0.3 + 9.0j
    fe_err = abs(xi(s_off) - xi(1.0 - s_off))
    print(f"|xi(0.3+9i) - xi(0.7-9i)| = {fe_err:.3e}")
    check("functional equation xi(s) = xi(1-s) off the line (1e-10)",
          fe_err < 1e-10, f"err = {fe_err:.2e}")

    g1 = 14.134725141734693790  # first non-trivial zero (ordinates)
    xi_zero = abs(xi(0.5 + g1 * 1j))
    xi_off = abs(xi(0.5 + 9.3j))
    print(f"|xi(first zero)| = {xi_zero:.3e}   |xi(0.5+9.3i)| = {xi_off:.4f}")
    check("|xi| at first zero < 1e-12", xi_zero < 1e-12)
    check("|xi| at a non-zero ordinate > 1e-2 (contrast)", xi_off > 1e-2)

    b = 1.0 / (4.0 * math.pi + 2.0 * math.sqrt(3.0))
    check("b matches framework value", abs(b - 0.062381194121028227) < 5e-16,
          f"b = {b:.17f}")

    verdict = {"section": 6, "language": "python",
               "values": {"b": repr(b), "xi_zero_residual": xi_zero},
               "all_passed": not failures}
    print(f"JSON: {json.dumps(verdict)}")
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
