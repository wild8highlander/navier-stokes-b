# l4_nse_2d.jl — 2D NSE: тождества поворота + энергетика (собственный FFT radix-2)
include(joinpath(@__DIR__, "common.jl"))

const COSB = sqrt(1 - B^2)
const SINB = B

"""FFT2 (по обеим осям) для матрицы n×n через myfft (последняя ось + перестановка)."""
function fft2(A::Matrix{ComplexF64}; inverse::Bool = false)
    T = myfft(A; inverse)
    return Matrix{ComplexF64}(permutedims(myfft(permutedims(T, (2, 1)); inverse), (2, 1)))
end

function run_l4(; N = 64, nu = 0.001, T = 2.0, dt = 0.002)
    selftest = fft_selftest(64)
    crit = N ÷ 3
    NP = 128                     # степень двойки: 2N-паддинг — произведения без алиасинга
    k = fftfreq_r2c(N)           # целые волновые числа
    kP = fftfreq_r2c(NP)
    # сетки: kx по строкам (полная ось), ky по столбцам (rfft-половина не нужна — полный комплексный формат)
    KX = [k[j] for i in 1:N, j in 1:N]
    KY = [k[i] for i in 1:N, j in 1:N]
    K2 = KX.^2 .+ KY.^2; K2[1, 1] = 1.0
    KXP = [kP[j] for i in 1:NP, j in 1:NP]
    KYP = [kP[i] for i in 1:NP, j in 1:NP]
    K2P = KXP.^2 .+ KYP.^2; K2P[1, 1] = 1.0
    x = range(0; length = N, step = 2pi / N)
    X = [Float64(x[j]) for i in 1:N, j in 1:N]
    Y = [Float64(x[i]) for i in 1:N, j in 1:N]

    mask = (abs.(KX) .<= crit) .& (abs.(KY) .<= crit)
    proj(f) = begin
        p = (KX .* f[1] .+ KY .* f[2]) ./ K2
        [f[1] .- KX .* p, f[2] .- KY .* p]
    end
    to_spec(f) = fft2(ComplexF64.(f))
    to_real(f) = real.(fft2(f; inverse = true))

    u0 = sin.(X) .* cos.(Y)
    v0 = -cos.(X) .* sin.(Y)
    wh = proj(to_spec([u0, v0]))
    om0 = to_real([1im .* KY .* wh[2] .- 1im .* KX .* wh[0 + 1]])[1]

    # (i) тождество ω' = cos θ_b·ω на 200 div-free полях
    rng = MersenneTwister(7)
    max_id = 0.0
    for _ in 1:200
        f = proj(to_spec([randn(rng, N, N), randn(rng, N, N)]))
        om = to_real([1im .* KY .* f[2] .- 1im .* KX .* f[1]])[1]
        rot = [COSB .* f[1] .- SINB .* f[2], SINB .* f[1] .+ COSB .* f[2]]
        omr = to_real([1im .* KY .* rot[2] .- 1im .* KX .* rot[1]])[1]
        max_id = max(max_id, maximum(abs.(omr .- COSB .* om)))
    end
    w = [u0, v0]
    E = sum(abs2, w[1]) + sum(abs2, w[2])
    wrot = [COSB .* w[1] .- SINB .* w[2], SINB .* w[1] .+ COSB .* w[2]]
    energy_err = abs((sum(abs2, wrot[1]) + sum(abs2, wrot[2])) - E) / E

    # честная реализация rhs (вектор из 2 спектральных полей)
    function rhs2(uh)
        uh2 = [embed(f, crit, NP) for f in uh]
        u = [real.(fft2(f; inverse = true)) for f in uh2]
        dX = [real.(fft2(1im .* KXP .* f; inverse = true)) for f in uh2]
        dY = [real.(fft2(1im .* KYP .* f; inverse = true)) for f in uh2]
        adv = [u[1] .* dX[1] .+ u[2] .* dY[1], u[1] .* dX[2] .+ u[2] .* dY[2]]
        nlp = to_spec(adv)
        p = (KXP .* nlp[1] .+ KYP .* nlp[2]) ./ K2P
        nlp = [nlp[1] .- KXP .* p, nlp[2] .- KYP .* p]
        out = [cut(nlp[1], crit, N), cut(nlp[2], crit, N)]
        return [.-out[1] .- nu .* K2 .* uh[1], .-out[2] .- nu .* K2 .* uh[2]]
    end

    n_steps = Int(round(T / dt))
    om_max0 = maximum(abs.(om0))
    om_viol = 0.0
    phi = dt * THETA
    cph, sph = cos(phi), sin(phi)
    max_dE = 0.0
    E_prev = (sum(abs2, u0) + sum(abs2, v0)) / 2 / N^2
    diss = 0.0; Z_prev = nothing
    wh_run = wh
    for n in 1:n_steps
        k1 = rhs2(wh_run)
        k2 = rhs2(wh_run .+ 0.5dt .* k1)
        k3 = rhs2(wh_run .+ 0.5dt .* k2)
        k4 = rhs2(wh_run .+ dt .* k3)
        wh_run = wh_run .+ (dt / 6) .* (k1 .+ 2k2 .+ 2k3 .+ k4)
        om = to_real([1im .* KY .* wh_run[2] .- 1im .* KX .* wh_run[1]])[1]
        om_viol = max(om_viol, maximum(abs.(om)) - om_max0)
        Z = 0.5 * sum(abs2, om) / N^2
        if Z_prev !== nothing
            diss += nu * dt * (Z_prev + Z)
        end
        Z_prev = Z
        uu = to_real(wh_run)
        E_pre = (sum(abs2, uu[1]) + sum(abs2, uu[2])) / 2 / N^2
        wh_rot = proj([cph .* wh_run[1] .- sph .* wh_run[2], sph .* wh_run[1] .+ cph .* wh_run[2]])
        uu2 = to_real(wh_rot)
        E_post = (sum(abs2, uu2[1]) + sum(abs2, uu2[2])) / 2 / N^2
        max_dE = max(max_dE, abs(E_post - E_pre))
        wh_run = wh_rot
    end
    balance = abs((sum(abs2, to_real(wh_run)[1]) + sum(abs2, to_real(wh_run)[2])) / 2 / N^2 - E_prev + diss)

    ok = selftest < 1e-10 && max_id < 1e-10 && energy_err < 1e-12 && om_viol < 1e-9 &&
         max_dE < 1e-7 && balance < 1e-3
    out = Dict("level" => "L4",
        "params" => Dict("N" => N, "nu" => nu, "T" => T, "dt" => dt,
                         "theta_b_deg" => float(rad2deg(THETA)),
                         "protocol" => "continuous dt·θ_b; 2/3-правило; 2N-паддинг; собственный FFT"),
        "checks" => Dict(
            "FFT самотест против DFT" => selftest,
            "тождество ω' = cos θ_b·ω" => max_id,
            "энергия при повороте |E'−E|/E" => energy_err,
            "максимум-принцип ω (превышение)" => om_viol,
            "|ΔE| за один поворот" => max_dE,
            "энергетический баланс" => balance,
        ), "ok" => ok)
    write_json(joinpath(RESULTS_DIR, "l4_nse_2d.json"), out)
    println("L4: ", ok ? "PASS" : "FAIL", " | FFT:", selftest, " ω'-тожд.: ", max_id)
    return ok
end

# rfftfreq-аналог для степени двойки (целые волновые числа)
function fftfreq_r2c(n::Int)
    return [j - n * (j > n ÷ 2) for j in 0:n-1]
end

# врезка спектра n-сетки (моды ≤ crit) в np-сетку и обратно (полный комплексный формат)
function embed(f, crit, np)
    out = zeros(ComplexF64, np, np)
    out[1:crit+1, 1:crit+1] = f[1:crit+1, 1:crit+1]
    out[end-crit+1:end, 1:crit+1] = f[end-crit+1:end, 1:crit+1]
    out[1:crit+1, end-crit+1:end] = f[1:crit+1, end-crit+1:end]
    out[end-crit+1:end, end-crit+1:end] = f[end-crit+1:end, end-crit+1:end]
    return out
end
function cut(f, crit, n)
    out = zeros(ComplexF64, n, n)
    out[1:crit+1, 1:crit+1] = f[1:crit+1, 1:crit+1]
    out[end-crit+1:end, 1:crit+1] = f[end-crit+1:end, 1:crit+1]
    out[1:crit+1, end-crit+1:end] = f[1:crit+1, end-crit+1:end]
    out[end-crit+1:end, end-crit+1:end] = f[end-crit+1:end, end-crit+1:end]
    return out
end
