# l3_kirchhoff_vortices.jl — гамильтоновость, порядок RK4 = 4, изометрия вращения
include(joinpath(@__DIR__, "common.jl"))

H(q) = 0.5 * (q[1]^2 + q[2]^2) + 0.25 * sin(q[1]) * sin(q[2])
grad_H(q) = [q[1] + 0.25 * cos(q[1]) * sin(q[2]); q[2] + 0.25 * sin(q[1]) * cos(q[2])]
grad_H_harm(q) = [q[1]; q[2]]

vel(q, grad) = [grad(q)[2]; -grad(q)[1]]

function integrate(q0, T, dt, grad)
    q = Float64.(q0)
    for _ in 1:Int(round(T / dt))
        q = rk4_step(y -> vel(y, grad), q, dt)
    end
    return q
end

function run_l3()
    rng = MersenneTwister(42)
    q0 = [0.7; -1.1]; T = 10.0
    H0 = H(q0)
    drifts = Dict(dt => abs(H(integrate(q0, T, dt, grad_H)) - H0) for dt in (0.1, 0.05, 0.025))
    fine = integrate(q0, T, 0.00125, grad_H)
    e1 = norm(integrate(q0, T, 0.05, grad_H) - fine)
    e2 = norm(integrate(q0, T, 0.025, grad_H) - fine)
    order = log2(e1 / e2)

    pts = [randn(rng, 2) for _ in 1:50]
    ptsT = [integrate(p, T, 0.01, grad_H_harm) for p in pts]
    iso_err = 0.0
    for i in 1:50, j in 1:50
        iso_err = max(iso_err, abs(norm(ptsT[i] - ptsT[j]) - norm(pts[i] - pts[j])))
    end
    area(q1, q2, q3) = abs((q2[1]-q1[1])*(q3[2]-q1[2]) - (q2[2]-q1[2])*(q3[1]-q1[1]))
    base = randn(rng, 2); eps = 1e-4
    tri = [base, base .+ [eps, 0], base .+ [0, eps]]
    triT = [integrate(p, T, 0.01, grad_H) for p in tri]
    area_err = abs(area(triT...) - area(tri...)) / area(tri...)

    qh_T = integrate([1.0; 0.0], 2pi, 2pi / 2000, grad_H_harm)
    circle_err = norm(qh_T - [1.0; 0.0])

    ok = drifts[0.025] < drifts[0.05] < drifts[0.1] && 3.7 < order < 4.3 &&
         iso_err < 1e-9 && area_err < 1e-4 && circle_err < 1e-3
    out = Dict("level" => "L3",
        "checks" => Dict(
            "дрейф H, dt=0.1" => drifts[0.1], "дрейф H, dt=0.05" => drifts[0.05],
            "дрейф H, dt=0.025" => drifts[0.025],
            "измеренный порядок RK4 (ожидаeтся ≈4)" => order,
            "изометрия жёсткого вращения, макс. |Δd|" => iso_err,
            "сохранение площади, отн. ошибка" => area_err,
            "замыкание окружности за 2π" => circle_err,
        ), "ok" => ok)
    write_json(joinpath(RESULTS_DIR, "l3_kirchhoff_vortices.json"), out)
    println("L3: ", ok ? "PASS" : "FAIL", " | порядок RK4 = ", round(order; digits = 2))
    return ok
end
