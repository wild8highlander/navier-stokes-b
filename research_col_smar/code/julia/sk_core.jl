# sk_core.jl — shared core of the Julia verification track.
#
# Conventions (identical to code/python/sk_core.py):
#   * kinetic-energy spectrum E(k) = C_K eps^(2/3) k^(-5/3);
#   * textbook identities  eps = 2 nu int k^2 E dk,
#     <|Sbar|^2> = 2 int k^2 E G^2 dk;
#   * Smagorinsky closure  nu_t = (C_s Delta)^2 |Sbar|,
#     |Sbar| = (2 Sbar_ij Sbar_ij)^(1/2), eps_sgs = (C_s Delta)^2 <|Sbar|^3>.

module sk_core

export GAMMA23, CK_SREENIVASAN, CK_LHDIA, CK_DIA,
    lilly_cs_sharp, lilly_cs_gaussian, pao_beta,
    heisenberg_ck, heisenberg_alpha, heisenberg_spectrum, pao_spectrum

const GAMMA23 = 1.3541179394264005      # Gamma(2/3)
const CK_SREENIVASAN = 1.50             # Sreenivasan 1995
const CK_LHDIA = 1.52                   # Kraichnan 1965 (LhDIA)
const CK_DIA = 1.77                     # Kraichnan 1959 (DIA)

"Sharp-cutoff Lilly relation: C_s = 1 / (pi (3 C_K / 2)^(3/4))."
lilly_cs_sharp(ck::Float64) = 1.0 / (pi * (1.5 * ck)^0.75)

"Gaussian-filter Lilly relation: C_s = (C_K Gamma(2/3) 12^(2/3))^(-3/4)."
lilly_cs_gaussian(ck::Float64) = (ck * GAMMA23 * 12.0^(2.0 / 3.0))^(-0.75)

"Pao-type Gaussian cutoff exponent with exact dissipation normalization."
pao_beta(ck::Float64) = (ck * GAMMA23)^1.5

"Heisenberg closure: C_K(alpha) = (8/(9 alpha))^(2/3)."
heisenberg_ck(alpha::Float64) = (8.0 / (9.0 * alpha))^(2.0 / 3.0)

"Inverse Heisenberg calibration: alpha = 8/(9 C_K^(3/2))."
heisenberg_alpha(ck::Float64) = 8.0 / (9.0 * ck^1.5)

"Closed-form Heisenberg spectrum (chi = k eta)."
function heisenberg_spectrum(k::Float64, eps::Float64, nu::Float64,
                             alpha::Float64)
    eta = (nu^3 / eps)^0.25
    chi = k * eta
    chi <= 0.0 && return 0.0
    core = chi^(-7.0)
    bracket = 1.0 + 0.375 * alpha^2 * chi^(-4.0)
    return alpha^2 / 4.0 * eps^0.25 * nu^1.25 * core * bracket^(-4.0 / 3.0)
end

"Pao-type model spectrum with exact dissipation normalization."
function pao_spectrum(k::Float64, eps::Float64, nu::Float64, ck::Float64)
    k <= 0.0 && return 0.0
    eta = (nu^3 / eps)^0.25
    chi = k * eta
    return ck * eps^(2.0 / 3.0) * k^(-5.0 / 3.0) *
           exp(-pao_beta(ck) * chi^2)
end

end  # module
