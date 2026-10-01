// Section 7 — Smagorinsky-Kolmogorov master relation (C++17 port).
//
// Verifies, from the closed form alone:
//   * the parent constant b = 1/(4*pi + 2*sqrt(3)) and sin(theta_b) = b;
//   * C_s(C_K) = 1/(pi * (3*C_K/2)^(3/4)) at C_K = 1.5 (long double);
//   * Lilly agreement |C_s - 0.17326| < 1e-5;
//   * exponent law C_s(a*C_K)/C_s(C_K) = a^(-3/4);
//   * monotonicity and the 0.16..0.20 literature band;
//   * Cassini identity F(k+1)^2 - F(k)F(k+2) = (-1)^k (uint64 exact to k=90);
//   * reduced zero-drift condition (5'): a*b*b*c sign-definite (no root),
//     a*a*b*b degenerate (all coefficients zero) — exact integer algebra.
//
// Output contract: banner -> [PASS]/[FAIL] -> JSON verdict -> exit code.
#include <cstdint>
#include <cstdio>
#include <cmath>
#include <string>

static bool g_ok = true;

static void check(const char* name, bool cond, const char* detail = "") {
    std::printf("[%s] %s%s%s\n", cond ? "PASS" : "FAIL", name,
                detail[0] ? "  (" : "", detail);
    if (!cond) g_ok = false;
}

static long double cs_master(long double ck) {
    return 1.0L / (M_PIl * std::pow(3.0L * ck / 2.0L, 0.75L));
}

// Fibonacci up to F(90) fits in uint64.
static uint64_t fib(int n) {
    uint64_t a = 0, b = 1;
    for (int i = 0; i < n; ++i) {
        uint64_t t = a + b;
        a = b;
        b = t;
    }
    return a;
}

int main() {
    std::printf("=== Section 7: Smagorinsky-Kolmogorov Master Relation (C++) ===\n");

    const long double b = 1.0L / (4.0L * M_PIl + 2.0L * std::sqrt(3.0L));
    const long double theta = std::asin(b);
    std::printf("b = %.18Lf, theta_b = %.13Lf deg\n", b, theta * 180.0L / M_PIl);
    check("b matches pinned value", std::fabs(b - 0.062381194121028227546339671639402081186993L) < 5e-16L);
    check("sin(theta_b) = b", std::fabs(std::sin(theta) - b) < 1e-17L);

    const long double cs = cs_master(1.5L);
    std::printf("C_s(1.5) = %.18Lf\n", cs);
    check("C_s(1.5) matches pinned value", std::fabs(cs - 0.1732659558297058017568595667273903913207704L) < 5e-16L);
    check("|C_s - Lilly| < 1e-5", std::fabs(cs - 0.17326L) < 1e-5L);

    long double worst = 0.0L;
    for (long double a : {0.5L, 0.8L, 1.25L, 2.0L, 3.0L})
        worst = std::max(worst, std::fabs(cs_master(a * 1.5L) / cs - std::pow(a, -0.75L)));
    check("exponent law a^(-3/4)", worst < 1e-14L);

    check("monotonic C_s", cs_master(1.8L) < cs && cs < cs_master(1.2L));
    check("literature band 0.16..0.20", cs > 0.16L && cs < 0.20L);

    bool cassini = true;
    for (int k = 0; k <= 40; ++k) {
        // F(k+1)^2 - F(k)F(k+2) = (-1)^k  (exact modular check on int64 diff)
        long long d = static_cast<long long>(fib(k + 1) * fib(k + 1)
                                             - fib(k) * fib(k + 2));
        if (d != ((k % 2 == 0) ? 1 : -1)) cassini = false;
    }
    check("Cassini identity k = 0..40", cassini);

    // (5') coefficient algebra, exact on integers (F up to F(12) — no overflow)
    bool no_root = true, degenerate = true;
    const long double phi = (1.0L + std::sqrt(5.0L)) / 2.0L;
    const long double delta = 1e-3L;
    for (int k = 2; k < 8; ++k) {
        long long Fa = static_cast<long long>(fib(k));
        long long Fb = static_cast<long long>(fib(k + 1));
        long long Fc = static_cast<long long>(fib(k + 2));
        // a*b*b*c
        long long c2 = Fb * Fb - Fa * Fc;              // = (-1)^k
        long long cM = Fb * Fc - Fa * Fb;              // = Fb^2 > 0
        long long c1 = Fc * Fc - Fb * Fb;              // > 0
        if (!((k % 2 == 0 ? c2 == 1 : c2 == -1) && cM > 0 && c1 > 0))
            no_root = false;
        for (long double t : {0.3L, 0.8L, 1.5L}) {
            long double R1 = t, R2 = t / phi;
            long double m1 = std::max(R1 * R1, delta * delta);
            long double m2 = std::max(R2 * R2, delta * delta);
            long double mM = std::max(R1 * R1 + R2 * R2, delta * delta);
            if (!((long double)c2 * m2 + (long double)cM * mM + (long double)c1 * m1 > 0.0L))
                no_root = false;
        }
        // a*a*b*b degenerate: (Fa, Fa, Fb, Fb) -> all three coefficients zero
        long long d2 = Fa * Fb - Fa * Fb;   // Gamma_B*Gamma_C - Gamma_A*Gamma_D
        long long dM = Fa * Fb - Fa * Fb;   // Gamma_B*Gamma_D - Gamma_A*Gamma_C
        long long d1 = Fb * Fb - Fb * Fb;   // Gamma_D^2 - Gamma_C^2
        if (!(d2 == 0 && dM == 0 && d1 == 0))
            degenerate = false;
    }
    check("a*b*b*c: (5') sign-definite (no zero-drift root)", no_root);
    check("a*a*b*b: (5') coefficients vanish identically", degenerate);

    std::printf("JSON: {\"section\": 7, \"language\": \"cpp\", \"values\": {\"C_s\": \"%.17Lf\", \"b\": \"%.17Lf\"}, \"all_passed\": %s}\n",
                cs, b, g_ok ? "true" : "false");
    return g_ok ? 0 : 1;
}
