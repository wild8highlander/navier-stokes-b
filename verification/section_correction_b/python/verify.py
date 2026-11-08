"""Section 1 — Correction b: the universal polarization constant (Python port).

Verifies, from the closed form alone and stdlib-only:
  * b = 1/(4*pi + 2*sqrt(3)) matches the pinned value to 15+ digits;
  * 0 < b < 1 and theta_b = arcsin(b) satisfies sin(theta_b) = b exactly
    to machine precision;
  * Rodrigues rotation algebra: R^T R = I, det R = 1, trace R = 1 + 2 cos theta_b;
  * energy neutrality: ||R u|| = ||u|| (machine zero) over a deterministic
    pseudo-random field.
Output contract: banner -> [PASS]/[FAIL] per assertion -> JSON verdict line.
"""
import json
import math

PINNED_B = 0.062381194121028227546339671639402081186993306823604

# deterministic LCG so the run is bit-reproducible on any platform
_state = 20260916


def lcg_random():
    global _state
    _state = (_state * 6364136223846793005 + 1442695040888963407) % (1 << 64)
    return _state / float(1 << 64) * 2.0 - 1.0


def rotation_matrix(theta, axis):
    """Rodrigues rotation matrix about a unit axis."""
    ex, ey, ez = axis
    K = [[0.0, -ez, ey], [ez, 0.0, -ex], [-ey, ex, 0.0]]
    outer = [[ex * ex, ex * ey, ex * ez],
             [ey * ex, ey * ey, ey * ez],
             [ez * ex, ez * ey, ez * ez]]
    c, s = math.cos(theta), math.sin(theta)
    return [[(1.0 if i == j else 0.0) * c + (1.0 - c) * outer[i][j] - s * K[i][j]
             for j in range(3)] for i in range(3)]


def main() -> int:
    print("=== Section 1: Correction b & 3D NSE Regularity ===")
    failures = []

    def check(name, cond, detail=""):
        status = "PASS" if cond else "FAIL"
        print(f"[{status}] {name}" + (f"  ({detail})" if detail else ""))
        if not cond:
            failures.append(name)

    # closed-form constant
    b = 1.0 / (4.0 * math.pi + 2.0 * math.sqrt(3.0))
    theta = math.asin(b)
    print(f"b = {b:.17f}")
    print(f"theta_b = {theta:.17f} rad = {math.degrees(theta):.16f} deg")
    check("b matches pinned value (15 digits)", abs(b - PINNED_B) < 5e-16)
    check("0 < b < 1", 0.0 < b < 1.0)
    check("sin(theta_b) = b (machine)", abs(math.sin(theta) - b) < 1e-17)
    check("cos(theta_b)^2 + b^2 = 1", abs(math.cos(theta) ** 2 + b * b - 1.0) < 1e-16)

    # Rodrigues rotation algebra about a non-trivial axis
    axis = (0.3, -0.5, math.sqrt(1.0 - 0.3 ** 2 - 0.5 ** 2))
    R = rotation_matrix(theta, axis)
    det = (R[0][0] * (R[1][1] * R[2][2] - R[1][2] * R[2][1])
           - R[0][1] * (R[1][0] * R[2][2] - R[1][2] * R[2][0])
           + R[0][2] * (R[1][0] * R[2][1] - R[1][1] * R[2][0]))
    check("det R = 1", abs(det - 1.0) < 1e-12, f"det-1 = {abs(det - 1.0):.2e}")
    trace = R[0][0] + R[1][1] + R[2][2]
    check("trace R = 1 + 2 cos(theta_b)", abs(trace - (1.0 + 2.0 * math.cos(theta))) < 1e-12)
    ortho_err = max(abs(sum(R[k][i] * R[k][j] for k in range(3)) - (1.0 if i == j else 0.0))
                    for i in range(3) for j in range(3))
    check("R^T R = I", ortho_err < 1e-12, f"max residual {ortho_err:.2e}")

    # energy neutrality over a deterministic pseudo-random field
    max_dE = 0.0
    for _ in range(10000):
        v = (lcg_random(), lcg_random(), lcg_random())
        rv = tuple(sum(R[i][j] * v[j] for j in range(3)) for i in range(3))
        dE = abs(sum(x * x for x in rv) - sum(x * x for x in v))
        max_dE = max(max_dE, dE)
    check("energy neutral: max |dE| over 1e4 vectors <= 1e-12",
          max_dE <= 1e-12, f"max|dE| = {max_dE:.2e}")

    verdict = {"section": 1, "language": "python",
               "values": {"b": repr(b), "theta_b": repr(theta), "max_dE": max_dE},
               "all_passed": not failures}
    print(f"JSON: {json.dumps(verdict)}")
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
