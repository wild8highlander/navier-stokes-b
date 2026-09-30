# p1_p2_julia.jl — Julia verification of the analytical core (P1 + P2).
#
# Mirrors code/python/p1_lilly.py and p2_closures.py:
#   * master curve C_s(C_K) for sharp / Gaussian / box filters;
#   * Heisenberg calibration alpha <-> C_K and the closed-form spectrum;
#   * Pao spectrum with exact dissipation normalization.
# Writes results/p1_p2_julia.json (hand-rolled JSON — zero dependencies).
#
# Run:  julia p1_p2_julia.jl <results_dir>   (default: ../../results)

include(joinpath(@__DIR__, "sk_core.jl"))
using .sk_core
using Statistics
using Dates

const OUT = length(ARGS) >= 1 ? ARGS[1] : "../../results"

# --- quadrature checks -------------------------------------------------

function strain_sharp_quadrature(ck::Float64, kc::Real; m::Int = 2_000_000)
    h = kc / m
    s = 0.0
    for i in 0:(m - 1)
        s += ((i + 0.5) * h)^(1.0 / 3.0)
    end
    return 2.0 * ck * s * h
end

function strain_factor_box(ck::Float64; m::Int = 400_000, chi_max = 200.0)
    h = chi_max / m
    s = 0.0
    for i in 0:(m - 1)
        chi = (i + 0.5) * h
        x = chi / 2.0
        sinc = abs(x) < 1e-12 ? 1.0 : sin(x) / x
        s += chi^(1.0 / 3.0) * sinc^2
    end
    return 2.0 * ck * s * h
end

ck_ref = CK_SREENIVASAN
num = strain_sharp_quadrature(ck_ref, Float64(pi))
exact = 1.5 * ck_ref * pi^(4.0 / 3.0)
rel_err = abs(num - exact) / exact
cs_sharp = lilly_cs_sharp(ck_ref)
cs_gauss = lilly_cs_gaussian(ck_ref)
cs_box = strain_factor_box(ck_ref)^(-0.75)

# master curve
table = [[round(ck, digits = 4),
          lilly_cs_sharp(ck),
          lilly_cs_gaussian(ck),
          strain_factor_box(ck)^(-0.75)] for ck in 1.30:0.025:1.80]

# --- P2: closures ------------------------------------------------------

nu = 1.0e-4
eta = (nu^3)^0.25

function log_dissipation(spec::Function)
    lmin, lmax = log(1e-3 / eta), log(1e6 / eta)
    n = 300_000
    acc = 0.0
    prev = 0.0
    for j in 0:n
        k = exp(lmin + (lmax - lmin) * j / n)
        f = k^2 * spec(k) * k
        if j > 0
            acc += 0.5 * (f + prev) * ((lmax - lmin) / n)
        end
        prev = f
    end
    return 2.0 * nu * acc
end

alpha = heisenberg_alpha(ck_ref)
ck_rt = heisenberg_ck(alpha)
diss_h = log_dissipation(k -> heisenberg_spectrum(k, 1.0, nu, alpha))
diss_p = log_dissipation(k -> pao_spectrum(k, 1.0, nu, ck_ref))

# inertial-range constant and slopes of the closed-form Heisenberg spectrum
n = 200_000
chis = exp.(range(log(1e-3), log(1e6); length = n))
les = log.(heisenberg_spectrum.(chis ./ eta, 1.0, nu, alpha))

function linfit(xs, ys)
    mx, my = mean(xs), mean(ys)
    slope = sum((xs .- mx) .* (ys .- my)) / sum((xs .- mx) .^ 2)
    return slope, my - slope * mx
end

band = (chis .>= 1e-2) .& (chis .<= 0.2)
slope_i, inter_i = linfit(log.(chis[band]), les[band])
ck_meas = exp(inter_i) / (eta^(5.0 / 3.0))

band2 = (chis .>= 3.0) .& (chis .<= 20.0)
slope_far, _ = linfit(log.(chis[band2]), les[band2])

result = Dict(
    "program" => "p1_p2_julia",
    "title" => "Julia verification of the analytical core (P1 + P2)",
    "date" => string(Dates.today()),
    "reference_point" => Dict(
        "C_K" => ck_ref,
        "C_s_sharp" => cs_sharp,
        "C_s_gaussian" => cs_gauss,
        "C_s_box" => cs_box,
        "C_s_lilly_1966" => 0.17326,
    ),
    "verification" => Dict(
        "quadrature_rel_err" => rel_err,
        "heisenberg_alpha" => alpha,
        "heisenberg_C_K_roundtrip" => ck_rt,
        "heisenberg_dissipation" => diss_h,
        "pao_dissipation" => diss_p,
        "inertial_C_K_measured" => ck_meas,
        "inertial_slope" => slope_i,
        "far_dissipation_slope" => slope_far,
    ),
    "table_C_K__sharp__gaussian__box" => table,
)

# --- hand-rolled JSON writer (no external dependencies) ----------------

json_num(x::Float64) = isinteger(x) ? string(round(Int, x)) : string(x)

json_val(v::String) = "\"" * replace(v, "\"" => "\\\"") * "\""
json_val(v::Int) = string(v)
json_val(v::Float64) = json_num(v)

json_val(v::Vector{Float64}) = "[" * join(json_val.(v), ", ") * "]"

function json_val(v::Vector{Vector{Float64}})
    inner = ["[" * join(json_val.(row), ", ") * "]" for row in v]
    return "[\n    " * join(inner, ",\n    ") * "\n  ]"
end

function json_val(v::Vector{Any})
    return "[" * join(json_val.(v), ",\n    ") * "]"
end

function json_val(d::Dict)
    parts = String[]
    for (key, val) in sort(collect(pairs(d)); by = x -> x[1])
        push!(parts, "\"" * key * "\": " * json_val(val))
    end
    return "{\n  " * join(parts, ",\n  ") * "\n}"
end

mkpath(OUT)
out_path = joinpath(OUT, "p1_p2_julia.json")
open(out_path, "w") do fh
    write(fh, json_val(result))
end

println("[julia] C_s sharp = $(round(cs_sharp, digits = 5)), ",
        "gaussian = $(round(cs_gauss, digits = 5)), box = ",
        "$(round(cs_box, digits = 5))")
println("[julia] quadrature err = ", rel_err,
        ", Heisenberg C_K = ", round(ck_meas, digits = 4),
        ", slopes ", round(slope_i, digits = 3), " / ",
        round(slope_far, digits = 2))
println("[julia] wrote $out_path")
