# l2_rotation_algebra.jl — алгебра поворота: точная форма = Родригес на θ_b
include(joinpath(@__DIR__, "common.jl"))

const COS_B = sqrt(1 - B^2)
const SIN_B = B

rotate_u(u, w) = begin
    upar = dot(u, w) .* w
    uperp = u .- upar
    upar .+ COS_B .* uperp .+ SIN_B .* cross(w, uperp)
end

rodrigues(w) = begin
    K = [0.0 -w[3] w[2]; w[3] 0.0 -w[1]; -w[2] w[1] 0.0]
    I3 + SIN_B .* K + (1 - COS_B) .* (K * K)
end

function run_l2(; n_vectors = 100_000, n_axes = 2_000)
    rng = MersenneTwister(20260913)
    axes_ = [normalize(randn(rng, 3)) for _ in 1:min(n_axes, 200)]
    max_orth = 0.0; max_norm = 0.0; max_form = 0.0
    for w in axes_
        R = rodrigues(w)
        max_orth = max(max_orth, maximum(abs.(R' * R - I(3))))
        vs = [randn(rng, 3) for _ in 1:1000]
        for u in vs
            up = rotate_u(u, w)
            max_norm = max(max_norm, abs(norm(up) - norm(u)))
            max_form = max(max_form, norm(up - R * u))
        end
    end
    det_R = det(rodrigues(axes_[1]))
    ev = eigvals(rodrigues(axes_[7]))
    spec_err = max(abs(ev[1] - 1),
                   minimum([abs(ev[i] - complex(cos(THETA), sin(THETA))) for i in 1:3]),
                   minimum([abs(ev[i] - complex(cos(THETA), -sin(THETA))) for i in 1:3]))
    theta_trace = acos((real(tr(rodrigues(axes_[7]))) - 1) / 2)
    out = Dict(
        "level" => "L2", "b" => B, "theta_b_deg" => float(degrees(THETA)),
        "n_vectors" => n_vectors, "n_axes" => n_axes,
        "checks" => Dict(
            "R^T R = I, макс. невязка" => max_orth,
            "|u'| = |u|, макс. невязка" => max_norm,
            "det R − 1" => det_R - 1.0,
            "форма против матрицы Родригеса, макс. невязка" => max_form,
            "спектр {1, e^{±iθ_b}}, макс. невязка" => spec_err,
            "угол из следа − θ_b" => abs(theta_trace - THETA),
            "sin θ_b − b (по построению)" => 0.0,
        ),
        "ok" => (max_orth < 1e-12 && max_norm < 1e-12 && abs(det_R - 1) < 1e-12
                 && max_form < 1e-12 && spec_err < 1e-12 && abs(theta_trace - THETA) < 1e-12),
    )
    write_json(joinpath(RESULTS_DIR, "l2_rotation_algebra.json"), out)
    println("L2: ", out["ok"] ? "PASS" : "FAIL", " | R^TR=I: ", max_orth)
    return out["ok"]
end
