// p2_closures.cpp — Heisenberg and Pao closures (C++ track).
//
// Mirrors code/python/p2_closures.py:
//   * calibration alpha = 8/(9 C_K^(3/2)) for experiment / LhDIA / DIA;
//   * closed-form Heisenberg spectrum: inertial slope and constant,
//     far-dissipation slope, dissipation integral;
//   * Pao model spectrum: dissipation integral with beta = (C_K Gamma(2/3))^(3/2).
// Output: results/p2_cpp.json
#include <cmath>
#include <cstdio>
#include <fstream>
#include <iomanip>
#include <sstream>
#include <string>
#include <vector>

#include "sk_core.hpp"

namespace {

struct Check {
    std::string source;
    double ck_target;
    double alpha;
    double ck_roundtrip;
    double diss_rel_err;
};

}  // namespace

int main() {
    const double eps = 1.0;
    const double nu = 1.0e-4;
    const double eta = std::pow(nu * nu * nu / eps, 0.25);

    std::vector<Check> checks;
    const std::vector<std::string> labels = {"experiment", "LhDIA", "DIA"};
    const std::vector<double> cks = {sk::kCkSreenivasan, sk::kCkLhDia,
                                     sk::kCkDia};
    for (size_t i = 0; i < cks.size(); ++i) {
        const double alpha = sk::heisenberg_alpha(cks[i]);
        const double ck_rt = sk::heisenberg_ck(alpha);
        // dissipation integral of the Heisenberg spectrum must equal eps
        // (log-spaced trapezoid: int f dk = int (f k) d(ln k))
        const int n = 400000;
        const double lmin = std::log(1e-3 / eta);
        const double lmax = std::log(1e6 / eta);
        double acc = 0.0;
        double prev = 0.0;
        for (int j = 0; j <= n; ++j) {
            const double k = std::exp(lmin + (lmax - lmin) * j / n);
            const double f = k * k * sk::heisenberg_spectrum(k, eps, nu, alpha) * k;
            if (j > 0) {
                acc += 0.5 * (f + prev) * ((lmax - lmin) / n);
            }
            prev = f;
        }
        const double diss = 2.0 * nu * acc;
        checks.push_back({labels[i], cks[i], alpha, ck_rt,
                          std::fabs(diss - eps) / eps});
    }

    // inertial-range constant and slopes from the closed-form spectrum
    const double alpha = sk::heisenberg_alpha(sk::kCkSreenivasan);
    const int n = 200000;
    std::vector<double> chi(n), le(n);
    for (int j = 0; j < n; ++j) {
        chi[j] = std::exp(std::log(1e-3) +
                          (std::log(1e6) - std::log(1e-3)) * j / (n - 1.0));
        le[j] = std::log(sk::heisenberg_spectrum(chi[j] / eta, eps, nu, alpha));
    }
    auto linfit = [](const std::vector<double>& x,
                     const std::vector<double>& y, double xlo, double xhi) {
        double sx = 0, sy = 0, sxx = 0, sxy = 0;
        int m = 0;
        for (size_t i = 0; i < x.size(); ++i) {
            if (x[i] >= xlo && x[i] <= xhi) {
                sx += x[i];
                sy += y[i];
                sxx += x[i] * x[i];
                sxy += x[i] * y[i];
                ++m;
            }
        }
        const double slope = (m * sxy - sx * sy) / (m * sxx - sx * sx);
        const double intercept = (sy - slope * sx) / m;
        return std::make_pair(slope, intercept);
    };
    std::vector<double> lchi(n);
    for (int j = 0; j < n; ++j) {
        lchi[j] = std::log(chi[j]);
    }
    const auto inert = linfit(lchi, le, std::log(0.01), std::log(0.2));
    const double slope_inert = inert.first;
    // C_K from intercept: E = C_K eps^(2/3) eta^(5/3) chi^(-5/3)
    const double ck_meas = std::exp(inert.second) /
                           (std::pow(eps, 2.0 / 3.0) * std::pow(eta, 5.0 / 3.0));
    const auto far = linfit(lchi, le, std::log(3.0), std::log(20.0));

    // Pao dissipation check
    double acc = 0.0;
    {
        const double lmin = std::log(1e-3 / eta);
        const double lmax = std::log(1e6 / eta);
        double prev = 0.0;
        for (int j = 0; j <= n; ++j) {
            const double k = std::exp(lmin + (lmax - lmin) * j / n);
            const double f = k * k * sk::pao_spectrum(k, eps, nu, sk::kCkSreenivasan) * k;
            if (j > 0) {
                acc += 0.5 * (f + prev) * ((lmax - lmin) / n);
            }
            prev = f;
        }
    }
    const double diss_pao = 2.0 * nu * acc;

    std::ostringstream json;
    json << std::setprecision(10);
    json << "{\n";
    json << "  \"program\": \"p2_cpp\",\n";
    json << "  \"title\": \"Heisenberg and Pao closures in C++\",\n";
    json << "  \"date\": \"2026-09-29\",\n";
    json << "  \"calibration\": [\n";
    for (size_t i = 0; i < checks.size(); ++i) {
        json << "    {\"source\": \"" << checks[i].source
             << "\", \"C_K_target\": " << checks[i].ck_target
             << ", \"alpha\": " << checks[i].alpha
             << ", \"C_K_roundtrip\": " << checks[i].ck_roundtrip
             << ", \"dissipation_rel_err\": " << checks[i].diss_rel_err
             << "}";
        if (i + 1 < checks.size()) {
            json << ",";
        }
        json << "\n";
    }
    json << "  ],\n";
    json << "  \"inertial_slope\": " << slope_inert << ",\n";
    json << "  \"inertial_C_K_measured\": " << ck_meas << ",\n";
    json << "  \"far_dissipation_slope\": " << far.first << ",\n";
    json << "  \"pao_dissipation_rel_err\": "
         << std::fabs(diss_pao - eps) / eps << "\n";
    json << "}\n";

    std::ofstream fh("results/p2_cpp.json");
    fh << json.str();
    std::printf("[p2_cpp] alpha = %.4f -> C_K = %.4f, slopes %.3f / %.2f, "
                "Pao err %.1e\n",
                alpha, ck_meas, slope_inert, far.first,
                std::fabs(diss_pao - eps) / eps);
    std::printf("[p2_cpp] wrote results/p2_cpp.json\n");
    return 0;
}
