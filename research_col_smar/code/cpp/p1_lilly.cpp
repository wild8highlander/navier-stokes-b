// p1_lilly.cpp — analytical determination of C_s from C_K (C++ track).
//
// Mirrors code/python/p1_lilly.py in long double precision:
//   * master curve C_s(C_K) for sharp / Gaussian / box filters;
//   * numerical quadrature check of the sharp-cutoff strain integral;
//   * reference point C_K = 1.5 versus Lilly (1966) = 0.17326.
// Output: results/p1_cpp.json
#include <cmath>
#include <cstdio>
#include <fstream>
#include <iomanip>
#include <sstream>

#include "sk_core.hpp"

namespace {

long double strain_integral_sharp(long double ck, long double kc) {
    // <|Sbar|^2> = 2 C_K eps^(2/3) int_0^kc k^(1/3) dk
    // (eps = 1, Delta = 1 -> kc = pi); returns eps^(2/3) kc^(4/3) factor.
    const long double n_steps = 2000000.0L;
    const long double h = kc / n_steps;
    long double acc = 0.0L;
    for (long double i = 0; i < n_steps; ++i) {
        const long double k = (i + 0.5L) * h;
        acc += std::pow(k, 1.0L / 3.0L);
    }
    return 2.0L * ck * acc * h;
}

long double strain_factor_box(long double ck) {
    // val = 2 C_K int_0^200 chi^(1/3) sinc^2(chi/2) dchi
    const long double n_steps = 400000.0L;
    const long double h = 200.0L / n_steps;
    long double acc = 0.0L;
    for (long double i = 0; i < n_steps; ++i) {
        const long double chi = (i + 0.5L) * h;
        const long double s = chi / 2.0L;
        const long double sinc = (std::fabs(s) < 1e-12L)
                                     ? 1.0L
                                     : std::sin(s) / s;
        acc += std::pow(chi, 1.0L / 3.0L) * sinc * sinc;
    }
    return 2.0L * ck * acc * h;
}

}  // namespace

int main() {
    const long double ck_ref = sk::kCkSreenivasan;

    // master curve
    std::ostringstream table;
    table << std::setprecision(10);
    table << "  [\n";
    for (int i = 0; i <= 22; ++i) {
        const long double ck = 1.30L + 0.025L * i;
        const long double cs_sharp = 1.0L / (M_PI * std::pow(1.5L * ck, 0.75L));
        const long double cs_gauss = std::pow(
            ck * sk::kGamma23 * std::pow(12.0L, 2.0L / 3.0L), -0.75L);
        const long double val = strain_factor_box(ck);
        const long double cs_box = std::pow(val, -0.75L);
        table << "    [ " << ck << ", " << cs_sharp << ", " << cs_gauss
              << ", " << cs_box << " ]";
        if (i < 22) {
            table << ",";
        }
        table << "\n";
    }
    table << "  ]";

    // quadrature check of the analytic sharp-cutoff strain factor
    const long double kc_pi = std::acos(-1.0L);
    const long double num = strain_integral_sharp(ck_ref, kc_pi);
    const long double exact = 1.5L * ck_ref * std::pow(kc_pi, 4.0L / 3.0L);
    const long double rel_err = std::fabs(num - exact) / exact;

    // box-filter reference at C_K = 1.5
    const long double val_box = strain_factor_box(ck_ref);
    const long double cs_box = std::pow(val_box, -0.75L);

    std::ostringstream json;
    json << std::setprecision(12);
    json << "{\n";
    json << "  \"program\": \"p1_cpp\",\n";
    json << "  \"title\": \"Analytical C_s(C_K) verification in C++ (long double)\",\n";
    json << "  \"date\": \"2026-09-29\",\n";
    json << "  \"reference_point\": {\n";
    json << "    \"C_K\": " << ck_ref << ",\n";
    json << "    \"C_s_sharp\": " << 1.0L / (M_PI * std::pow(1.5L * ck_ref, 0.75L)) << ",\n";
    json << "    \"C_s_gaussian\": " << std::pow(ck_ref * sk::kGamma23 * std::pow(12.0L, 2.0L / 3.0L), -0.75L) << ",\n";
    json << "    \"C_s_box\": " << cs_box << ",\n";
    json << "    \"C_s_lilly_1966\": 0.17326\n";
    json << "  },\n";
    json << "  \"verification\": {\n";
    json << "    \"quadrature_strain_value\": " << num << ",\n";
    json << "    \"quadrature_exact_value\": " << exact << ",\n";
    json << "    \"quadrature_rel_err\": " << rel_err << "\n";
    json << "  },\n";
    json << "  \"table_C_K__sharp__gaussian__box\": " << table.str() << "\n";
    json << "}\n";

    const std::string out_path = "results/p1_cpp.json";
    std::ofstream fh(out_path);
    fh << json.str();
    std::printf("[p1_cpp] C_s sharp = %.6Lf, gaussian = %.6Lf, box = %.6Lf\n",
                1.0L / (M_PI * std::pow(1.5L * ck_ref, 0.75L)),
                std::pow(ck_ref * sk::kGamma23 * std::pow(12.0L, 2.0L / 3.0L), -0.75L),
                cs_box);
    std::printf("[p1_cpp] quadrature rel err = %.3Le, wrote %s\n", rel_err,
                out_path.c_str());
    return 0;
}
