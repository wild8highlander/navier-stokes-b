# l1_exact_constants.jl — константы: BigFloat-формулы против Float64, 50 знаков
include(joinpath(@__DIR__, "config.jl"))

function run_l1()
    b = b_form_poly()
    b2 = b_form_simp()
    tb = theta_b(b)
    vals = Dict{String,BigFloat}(
        "b" => b,
        "theta_b" => tb,
        "cos_theta_b" => cos(tb),
        "ln_1p_b" => log(1 + b),
        "Z_full_leading" => exp(b * BETA_K * L_MIN_KLEIN),
        "b_beta_L" => b * BETA_K * L_MIN_KLEIN,
        "Cs_lilly" => (1 / BigFloat(pi)) * (BigFloat(9) / BigFloat(4))^(BigFloat(-3) / BigFloat(4)),
        "phi" => (1 + sqrt(BigFloat(5))) / 2,
        "e_klein" => exp(BigFloat(1)),
        "alpha_klein" => ALPHA_KLEIN,
        "L_min_klein" => L_MIN_KLEIN,
    )
    all_ok = abs(b - b2) == 0
    res = Dict{String,Any}(
        "b: разность двух форм" => string(b - b2),
        "sin(theta_b) − b (невязка)" => string(sin(tb) - b),
    )
    all_ok &= (sin(tb) - b == 0)
    for (k, v) in vals
        sym = string(v)
        f64 = Float64(v)
        diff = abs(f64 - parse(Float64, EXPECTED[k]))
        ok = startswith(sym, EXPECTED[k][1:min(length(EXPECTED[k]), 30)]) && diff < 1e-13
        all_ok &= ok
        res[k] = Dict("symbolic" => sym, "float64" => string(f64),
                      "abs_diff" => string(diff), "ok" => ok)
    end
    out = Dict("level" => "L1", "ok" => all_ok, "digits" => MP_DIGITS, "results" => res)
    write_json(joinpath(RESULTS_DIR, "l1_exact_constants.json"), out)
    println("L1: ", all_ok ? "PASS" : "FAIL")
    return all_ok
end
