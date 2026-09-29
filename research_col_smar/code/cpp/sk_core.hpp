// sk_core.hpp — shared core of the C++ verification track.
//
// Conventions (identical to code/python/sk_core.py):
//   * kinetic-energy spectrum  E(k) = C_K eps^(2/3) k^(-5/3) in the
//     inertial range; the textbook identities
//         eps = 2 nu int k^2 E dk,   <|Sbar|^2> = 2 int k^2 E G^2 dk
//     hold when the shell (variance) energy is e_shell = 2 E(k).
//   * Smagorinsky closure  nu_t = (C_s Delta)^2 |Sbar|,
//     |Sbar| = (2 Sbar_ij Sbar_ij)^(1/2),
//     eps_sgs = (C_s Delta)^2 <|Sbar|^3>.
#ifndef SK_CORE_HPP
#define SK_CORE_HPP

#include <cmath>
#include <string>
#include <vector>

namespace sk {

constexpr double kGamma23 = 1.3541179394264005;  // Gamma(2/3)
constexpr double kCkSreenivasan = 1.50;          // Sreenivasan 1995
constexpr double kCkLhDia = 1.52;                // Kraichnan 1965
constexpr double kCkDia = 1.77;                  // Kraichnan 1959

// Lilly relation, sharp spectral cutoff kc = pi/Delta:
//   C_s = 1 / (pi (3 C_K / 2)^(3/4))
inline double lilly_cs_sharp(double ck) {
    return 1.0 / (M_PI * std::pow(1.5 * ck, 0.75));
}

// Gaussian filter G(k) = exp(-k^2 Delta^2 / 24):
//   C_s = (C_K Gamma(2/3) 12^(2/3))^(-3/4)
inline double lilly_cs_gaussian(double ck) {
    return std::pow(ck * kGamma23 * std::pow(12.0, 2.0 / 3.0), -0.75);
}

// Pao-type Gaussian dissipation-range model with exact normalization:
//   E(k) = C_K eps^(2/3) k^(-5/3) exp(-beta (k eta)^2),
//   beta = (C_K Gamma(2/3))^(3/2)
inline double pao_beta(double ck) {
    return std::pow(ck * kGamma23, 1.5);
}

// Heisenberg closure: C_K(alpha) = (8 / (9 alpha))^(2/3), inverse
// alpha = 8 / (9 C_K^(3/2)).
inline double heisenberg_ck(double alpha) {
    return std::pow(8.0 / (9.0 * alpha), 2.0 / 3.0);
}
inline double heisenberg_alpha(double ck) {
    return 8.0 / (9.0 * std::pow(ck, 1.5));
}

// Closed-form Heisenberg spectrum (chi = k eta):
//   E(k) = (a^2/4) eps^(1/4) nu^(5/4) chi^-7 [1 + (3 a^2/8) chi^-4]^(-4/3)
inline double heisenberg_spectrum(double k, double eps, double nu,
                                  double alpha) {
    const double eta = std::pow(nu * nu * nu / eps, 0.25);
    const double chi = k * eta;
    if (chi <= 0.0) {
        return 0.0;
    }
    const double core = std::pow(chi, -7.0);
    const double bracket = 1.0 + 0.375 * alpha * alpha * std::pow(chi, -4.0);
    return std::pow(alpha, 2) / 4.0 * std::pow(eps, 0.25) *
           std::pow(nu, 1.25) * core * std::pow(bracket, -4.0 / 3.0);
}

// Pao-type model spectrum.
inline double pao_spectrum(double k, double eps, double nu, double ck) {
    const double eta = std::pow(nu * nu * nu / eps, 0.25);
    const double chi = k * eta;
    if (k <= 0.0) {
        return 0.0;
    }
    return ck * std::pow(eps, 2.0 / 3.0) * std::pow(k, -5.0 / 3.0) *
           std::exp(-pao_beta(ck) * chi * chi);
}

// Simple JSON string escaping.
inline std::string jstr(const std::string& s) {
    std::string out;
    for (char c : s) {
        if (c == '"' || c == '\\') {
            out.push_back('\\');
        }
        out.push_back(c);
    }
    return out;
}

}  // namespace sk

#endif  // SK_CORE_HPP
