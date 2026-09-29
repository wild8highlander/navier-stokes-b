// p3_apriori_cpp.cpp — C_s(Delta/eta) convergence curves in C++.
//
// Mirrors the sensitivity analysis of code/python/p1_lilly.py and p3:
//   * implied Smagorinsky constant
//       C_s(Delta) = eps^(1/2) / (Delta <|Sbar(Delta)|^2>^(3/4)),
//       <|Sbar(Delta)|^2> = 2 int_0^infty k^2 E(k) G^2(k; Delta) dk;
//   * model spectrum E(k) = C_K eps^(2/3) k^(-5/3) exp(-beta (k eta)^2),
//     beta = (C_K Gamma(2/3))^(3/2);
//   * filters: sharp cutoff kc = pi/Delta and Gaussian exp(-k^2 D^2/24);
//   * convergence to the Lilly values as Delta/eta -> infinity.
// Output: results/p3_cpp.json
#include <cmath>
#include <cstdio>
#include <fstream>
#include <iomanip>
#include <vector>

#include "sk_core.hpp"

namespace {

double strain_filtered(double delta, double eps, double nu, double ck,
                       bool sharp) {
    // <|Sbar|^2> = 2 int_0^inf k^2 E(k) G^2(k) dk  (log-spaced quadrature)
    const double eta = std::pow(nu * nu * nu / eps, 0.25);
    const double lmin = std::log(1e-6 / eta);
    const double lmax = std::log(1e4 / eta);
    const int n = 300000;
    double acc = 0.0;
    double prev = 0.0;
    for (int j = 0; j <= n; ++j) {
        const double k = std::exp(lmin + (lmax - lmin) * j / n);
        double G2;
        if (sharp) {
            G2 = (k <= M_PI / delta) ? 1.0 : 0.0;
        } else {
            G2 = std::exp(-k * k * delta * delta / 12.0);
        }
        const double f =
            k * k * sk::pao_spectrum(k, eps, nu, ck) * G2 * k;
        if (j > 0) {
            acc += 0.5 * (f + prev) * ((lmax - lmin) / n);
        }
        prev = f;
    }
    return 2.0 * acc;
}

}  // namespace

int main() {
    const double eps = 1.0;
    const double nu = std::pow(24.0, -4.0 / 3.0);  // k_eta = 24
    const double eta = std::pow(nu * nu * nu / eps, 0.25);
    const double ck = sk::kCkSreenivasan;

    std::ostringstream rows;
    rows << std::setprecision(8);
    rows << "  [\n";
    bool first = true;
    for (double d_over_eta = 2.0; d_over_eta <= 65.0; d_over_eta *= 1.4) {
        const double delta = d_over_eta * eta;
        for (const bool sharp : {true, false}) {
            const double s2 = strain_filtered(delta, eps, nu, ck, sharp);
            const double cs = std::sqrt(eps) /
                              (delta * std::pow(s2, 0.75));
            if (!first) {
                rows << ",\n";
            }
            first = false;
            rows << "    {\"Delta_over_eta\": " << d_over_eta
                 << ", \"filter\": \"" << (sharp ? "sharp" : "gaussian")
                 << "\", \"strain2\": " << s2
                 << ", \"C_s\": " << cs << "}";
        }
    }
    rows << "\n  ]";

    std::ofstream fh("results/p3_cpp.json");
    fh << std::setprecision(10);
    fh << "{\n";
    fh << "  \"program\": \"p3_cpp\",\n";
    fh << "  \"title\": \"C_s(Delta/eta) convergence curves in C++\",\n";
    fh << "  \"date\": \"2026-09-29\",\n";
    fh << "  \"convention\": \"E(k) kinetic-energy spectrum, "
          "eps = 2 nu int k^2 E dk\",\n";
    fh << "  \"C_s_lilly_sharp\": " << sk::lilly_cs_sharp(ck) << ",\n";
    fh << "  \"C_s_lilly_gaussian\": " << sk::lilly_cs_gaussian(ck) << ",\n";
    fh << "  \"eta\": " << eta << ",\n";
    fh << "  \"rows\": " << rows.str() << "\n";
    fh << "}\n";

    // console summary at the largest Delta/eta (deepest inertial cutoff)
    const double delta_big = 50.0 * eta;
    const double s2s = strain_filtered(delta_big, eps, nu, ck, true);
    const double s2g = strain_filtered(delta_big, eps, nu, ck, false);
    std::printf("[p3_cpp] Delta/eta = 50: C_s sharp = %.5f, gaussian = %.5f\n",
                std::sqrt(eps) / (delta_big * std::pow(s2s, 0.75)),
                std::sqrt(eps) / (delta_big * std::pow(s2g, 0.75)));
    std::printf("[p3_cpp] Lilly references: %.5f / %.5f\n",
                sk::lilly_cs_sharp(ck), sk::lilly_cs_gaussian(ck));
    std::printf("[p3_cpp] wrote results/p3_cpp.json\n");
    return 0;
}
