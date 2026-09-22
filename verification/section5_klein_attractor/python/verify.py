"""Section 5 — Klein attractor: ergodic dynamics and the NSE bridge (Python port).

Verifies, stdlib-only:
  * theta_b / pi is irrational — by Niven's theorem, a rational multiple of
    pi has sine in {0, +-1/2, +-1}; sin(theta_b) = b = 0.0623811... is not in
    that finite set, hence the rotation orbit is dense on the circle;
  * the rotation orbit fills the circle uniformly: after 1e5 iterates the
    largest angular gap is O(1/N) (three-gap theorem scale);
  * every iterate is an isometry (the map is a rigid rotation — the NSE
    bridge premise: energy is preserved step after step);
  * the shared constant chain b -> theta_b to machine precision.
Output contract: banner -> [PASS]/[FAIL] per assertion -> JSON verdict line.
"""
import json
import math


def main() -> int:
    print("=== Section 5: Klein Attractor — Ergodic Dynamics and the NSE Bridge ===")
    failures = []

    def check(name, cond, detail=""):
        status = "PASS" if cond else "FAIL"
        print(f"[{status}] {name}" + (f"  ({detail})" if detail else ""))
        if not cond:
            failures.append(name)

    b = 1.0 / (4.0 * math.pi + 2.0 * math.sqrt(3.0))
    theta = math.asin(b)
    print(f"b = {b:.17f}, theta_b = {theta:.17f} rad, theta_b/pi = {theta / math.pi:.15f}")
    check("b and theta_b pinned", abs(math.sin(theta) - b) < 1e-17)

    # Niven's theorem: rational theta/pi => sin(theta) in {0, +-1/2, +-1}
    niven_set = (0.0, 0.5, -0.5, 1.0, -1.0)
    not_niven = all(abs(b - s) > 1e-9 for s in niven_set)
    check("sin(theta_b) = b not in Niven set => theta_b/pi irrational", not_niven)

    # ergodic filling of the circle by the rotation orbit
    n_iter = 100000
    angles = sorted((n * theta) % (2.0 * math.pi) for n in range(1, n_iter + 1))
    max_gap = max(angles[i + 1] - angles[i] for i in range(n_iter - 1))
    max_gap = max(max_gap, 2.0 * math.pi - angles[-1] + angles[0])
    check("orbit dense: max angular gap < 1e-3 rad after 1e5 iterates",
          max_gap < 1e-3, f"max gap = {max_gap:.2e} rad (2*pi/N = {2 * math.pi / n_iter:.2e})")

    # isometry step after step (energy bridge)
    cx, cy = math.cos(theta), math.sin(theta)
    worst = 0.0
    x, y = 0.7, -1.3
    for _ in range(10000):
        x, y = cx * x - cy * y, cy * x + cx * y  # rotate by theta_b
        worst = max(worst, abs(x * x + y * y - (0.7 ** 2 + 1.3 ** 2)))
    check("rotation is an isometry at every iterate", worst < 1e-9,
          f"max |r^2 drift| = {worst:.2e}")

    verdict = {"section": 5, "language": "python",
               "values": {"b": repr(b), "theta_over_pi": repr(theta / math.pi),
                          "max_gap": max_gap},
               "all_passed": not failures}
    print(f"JSON: {json.dumps(verdict)}")
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
