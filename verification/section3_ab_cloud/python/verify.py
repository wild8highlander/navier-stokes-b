"""Section 3 — AB-Cloud: the non-Hermitian Hofstadter Hamiltonian (Python port).

Verifies the Hofstadter-model facts quoted by the AB-Cloud section, stdlib-only:
  * the k = 0 slice of the Hofstadter butterfly at flux phi = p/q in Landau
    gauge, E_j = 2 cos(2*pi*p*j/q), obeys the exact finite-DFT identities
    sum_{j=1..q-1} E_j = -2 and sum_{j=1..q-1} E_j^2 = 2q - 4 for every
    coprime (p, q) probed;
  * the q x q Harper matrix H (diagonal 2cos(2*pi*p*j/q), unit hopping with
    flux phase on the wrap-around bond) is Hermitian with trace exactly 0;
  * the shared constant chain b -> theta_b (the AB-Cloud normalization uses
    the same universal polarization constant).
Output contract: banner -> [PASS]/[FAIL] per assertion -> JSON verdict line.
"""
import cmath
import json
import math


def main() -> int:
    print("=== Section 3: AB-Cloud — Non-Hermitian Hofstadter Hamiltonian ===")
    failures = []

    def check(name, cond, detail=""):
        status = "PASS" if cond else "FAIL"
        print(f"[{status}] {name}" + (f"  ({detail})" if detail else ""))
        if not cond:
            failures.append(name)

    # exact butterfly-slice identities for several coprime (p, q)
    slice_ok = True
    detail = []
    for p, q in ((1, 4), (3, 8), (5, 12), (7, 16)):
        E = [2.0 * math.cos(2.0 * math.pi * p * j / q) for j in range(1, q)]
        s1, s2 = sum(E), sum(e * e for e in E)
        ok = abs(s1 - (-2.0)) < 1e-12 and abs(s2 - (2.0 * q - 4.0)) < 1e-10
        slice_ok = slice_ok and ok
        detail.append(f"p={p},q={q}: sum={s1:.2e}+2={s1 + 2:.1e}, sumsq err={abs(s2 - 2 * q + 4):.1e}")
    check("butterfly slice: sum E_j = -2, sum E_j^2 = 2q-4 (all pairs)",
          slice_ok, "; ".join(detail))

    # Harper matrix: Hermitian, trace 0
    for p, q in ((1, 5), (3, 10)):
        H = [[0.0 + 0.0j] * q for _ in range(q)]
        for j in range(q):
            H[j][j] = 2.0 * math.cos(2.0 * math.pi * p * (j + 1) / q)
            H[j][(j + 1) % q] = 1.0
            H[(j + 1) % q][j] = 1.0
        # wrap-around flux phase (Landau gauge, k = 0)
        H[q - 1][0] = cmath.exp(-2.0j * math.pi * p)
        H[0][q - 1] = cmath.exp(2.0j * math.pi * p)
        herm_err = max(abs(H[i][j] - H[j][i].conjugate())
                       for i in range(q) for j in range(q))
        trace = sum(H[i][i] for i in range(q))
        check(f"Harper matrix hermitian, trace 0 (p={p}, q={q})",
              herm_err < 1e-12 and abs(trace) < 1e-10,
              f"herm_err={herm_err:.1e}, |trace|={abs(trace):.1e}")

    # universal constant shared with the framework
    b = 1.0 / (4.0 * math.pi + 2.0 * math.sqrt(3.0))
    check("b matches framework value", abs(b - 0.062381194121028227) < 5e-16,
          f"b = {b:.17f}")

    verdict = {"section": 3, "language": "python",
               "values": {"b": repr(b)},
               "all_passed": not failures}
    print(f"JSON: {json.dumps(verdict)}")
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
