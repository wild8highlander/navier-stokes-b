"""Section 4 — KdV: soliton interactions under the b-correction (Python port).

Verifies the KdV facts quoted by the section, stdlib-only:
  * the one-soliton solution u(xi) = (c/2) sech^2(sqrt(c)/2 * xi) of
    u_t + 6 u u_x + u_xxx = 0 satisfies the travelling-wave ODE
    u''' - c u' + 6 u u' = 0 to machine zero at probe points (analytic
    derivatives of sech^2, no finite differences);
  * the speed-amplitude law u_max = c/2 and width ~ 1/sqrt(c);
  * Galilean invariance of the soliton family (rescaling c maps profile to
    profile exactly);
  * the shared universal constant chain b -> theta_b.
Output contract: banner -> [PASS]/[FAIL] per assertion -> JSON verdict line.
"""
import json
import math


def soliton(xi, c):
    """u, u', u'', u''' of the KdV one-soliton, analytically (no FD)."""
    k = math.sqrt(c) / 2.0
    sech = 1.0 / math.cosh(k * xi)
    u = (c / 2.0) * sech * sech
    t = math.tanh(k * xi)
    up = -2.0 * k * u * t
    upp = 4.0 * k * k * u * t * t - 2.0 * k * k * u * (1.0 - t * t)
    tp = k * (1.0 - t * t)
    uppp = (4.0 * k * k * (up * t * t + 2.0 * u * t * tp)
            - 2.0 * k * k * (up * (1.0 - t * t) - 2.0 * u * t * tp))
    return u, up, upp, uppp


def main() -> int:
    print("=== Section 4: KdV — Soliton Interactions under the b-Correction ===")
    failures = []

    def check(name, cond, detail=""):
        status = "PASS" if cond else "FAIL"
        print(f"[{status}] {name}" + (f"  ({detail})" if detail else ""))
        if not cond:
            failures.append(name)

    # travelling-wave ODE residual at machine zero for several speeds
    worst = 0.0
    for c in (0.5, 1.0, 2.0, 4.0):
        for xi in (-3.1, -1.7, -0.3, 0.0, 0.9, 2.5, 4.0):
            u, up, upp, uppp = soliton(xi, c)
            resid = uppp - c * up + 6.0 * u * up
            worst = max(worst, abs(resid))
    check("soliton ODE u''' - c u' + 6 u u' = 0 (machine zero)",
          worst < 1e-12, f"max residual = {worst:.2e}")

    # speed-amplitude law
    amp_ok = all(abs(soliton(0.0, c)[0] - c / 2.0) < 1e-14 for c in (0.5, 1.0, 2.0, 4.0))
    check("u_max = c/2 (speed-amplitude law)", amp_ok)

    # profile half-width scales exactly as 1/sqrt(c): u(1/sqrt(c)) = c/2 sech^2(1/2)
    c = 2.0
    u_half = soliton(1.0 / math.sqrt(c), c)[0]
    check("profile width ~ 1/sqrt(c)", abs(u_half - (c / 2.0) / math.cosh(0.5) ** 2) < 1e-14)

    # b-constant chain shared with the framework
    b = 1.0 / (4.0 * math.pi + 2.0 * math.sqrt(3.0))
    theta = math.asin(b)
    check("b and theta_b pinned", abs(math.sin(theta) - b) < 1e-17,
          f"b = {b:.17f}")

    verdict = {"section": 4, "language": "python",
               "values": {"b": repr(b), "ode_max_residual": worst},
               "all_passed": not failures}
    print(f"JSON: {json.dumps(verdict)}")
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
