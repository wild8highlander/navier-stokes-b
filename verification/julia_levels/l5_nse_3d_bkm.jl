# l5_nse_3d_bkm.jl — 3D Тейлор–Грин: BKM-интеграл, непрерывный b-поворот
# Собственный FFT radix-2 → N=32 (степень двойки), 2N-паддинг (64) без алиасинга.
include(joinpath(@__DIR__, "common.jl"))

const COSB = sqrt(1 - B^2)
const SINB = B

function fft3(A::Array{ComplexF64,4}; inverse::Bool = false)
    # последовательные 1D-FFT по осям 2,3,4 (x,y,z)
    T = myfft(A; inverse)                                   # по z
    T = myfft(permutedims(T, (1, 3, 2, 4)); inverse)        # по y
    T = permutedims(T, (1, 3, 2, 4))
    T = myfft(permutedims(T, (1, 4, 3, 2)); inverse)        # по x
    return permutedims(T, (1, 4, 3, 2))
end

function run_l5(; N = 32, nu = 0.01, T = 6.0, dt = 0.004)
    skip = get(ENV, "NSE3D_SMALL", "") == "1"
    if skip
        N = 24; dt = 0.01; T = 1.0   # контрольный режим не кратен 2 — только для тестов FFT не используем; здесь требуем степень 2
        N = 32
    end
    crit = N ÷ 3
    NP = 2N
    k = fftfreq_r2c(N)
    KX = [k[l] for i in 1:N, j in 1:N, l in 1:N]
    KY = [k[j] for i in 1:N, j in 1:N, l in 1:N]
    KZ = [k[i] for i in 1:N, j in 1:N, l in 1:N]
    K2 = KX.^2 .+ KY.^2 .+ KZ.^2; K2[1, 1, 1] = 1.0
    kP = fftfreq_r2c(NP)
    KXP = [kP[l] for i in 1:NP, j in 1:NP, l in 1:NP]
    KYP = [kP[j] for i in 1:NP, j in 1:NP, l in 1:NP]
    KZP = [kP[i] for i in 1:NP, j in 1:NP, l in 1:NP]
    K2P = KXP.^2 .+ KYP.^2 .+ KZP.^2; K2P[1, 1, 1] = 1.0
    cs = crit ÷ 2
    m_smooth = (abs.(KX) .<= cs) .& (abs.(KY) .<= cs) .& (abs.(KZ) .<= cs)

    x = range(0; length = N, step = 2pi / N)
    X = [Float64(x[l]) for i in 1:N, j in 1:N, l in 1:N]
    Y = [Float64(x[j]) for i in 1:N, j in 1:N, l in 1:N]
    Z = [Float64(x[i]) for i in 1:N, j in 1:N, l in 1:N]

    proj(f) = begin
        p = (KX .* f[1] .+ KY .* f[2] .+ KZ .* f[3]) ./ K2
        [f[1] .- KX .* p, f[2] .- KY .* p, f[3] .- KZ .* p]
    end
    to_spec(f) = fft3(reshape(ComplexF64.(f), 3, N, N, N))
    to_real(f) = real.(fft3(f; inverse = true))

    embed3(f) = begin
        out = zeros(ComplexF64, 3, NP, NP, NP)
        for (si, ti) in ((1, 1), (N - crit + 1, NP - crit + 1))
            for (sj, tj) in ((1, 1), (N - crit + 1, NP - crit + 1))
                for (sk, tk) in ((1, 1), (N - crit + 1, NP - crit + 1))
                    ni = crit + 1; nj = crit + 1; nk = crit + 1
                    out[:, ti:ti+ni-1, tj:tj+nj-1, tk:tk+nk-1] .=
                        f[:, si:si+ni-1, sj:sj+nj-1, sk:sk+nk-1]
                end
            end
        end
        out
    end
    cut3(f) = begin
        out = zeros(ComplexF64, 3, N, N, N)
        for (si, ti) in ((1, 1), (NP - crit + 1, N - crit + 1))
            for (sj, tj) in ((1, 1), (NP - crit + 1, N - crit + 1))
                for (sk, tk) in ((1, 1), (NP - crit + 1, N - crit + 1))
                    ni = crit + 1; nj = crit + 1; nk = crit + 1
                    out[:, ti:ti+ni-1, tj:tj+nj-1, tk:tk+nk-1] .=
                        f[:, si:si+ni-1, sj:sj+nj-1, sk:sk+nk-1]
                end
            end
        end
        out
    end

    function rhs(uh)
        uhp = cat([embed3(reshape(uh[c, :, :, :], N, N, N)) for c in 1:3]...; dims = 1)
        u = real.(fft3(uhp; inverse = true))
        gx = real.(fft3(1im .* KXP .* uhp; inverse = true))
        gy = real.(fft3(1im .* KYP .* uhp; inverse = true))
        gz = real.(fft3(1im .* KZP .* uhp; inverse = true))
        adv = cat([u[1] .* gx[c] .+ u[2] .* gy[c] .+ u[3] .* gz[c] for c in 1:3]...; dims = 1)
        nlp = fft3(adv)
        p = (KXP .* nlp[1, :, :, :] .+ KYP .* nlp[2, :, :, :] .+ KZP .* nlp[3, :, :, :]) ./ K2P
        for c in 1:3
            nlp[c, :, :, :] .= nlp[c, :, :, :] .- (c == 1 ? KXP : c == 2 ? KYP : KZP) .* p
        end
        out = cat([cut3(reshape(-nlp[c, :, :, :], 1, NP, NP, NP)) for c in 1:3]...; dims = 1)
        return out .- nu .* K2 .* uh
    end

    u_init = [sin.(X) .* cos.(Y) .* cos.(Z), -cos.(X) .* sin.(Y) .* cos.(Z), zeros(size(X))]
    uh0 = proj(to_spec(u_init))

    function case(rotate::Bool)
        phi = dt * THETA
        cph, sph = cos(phi), sin(phi)
        uh = copy(uh0)
        w0 = to_real(fft3_omega(uh))
        wmax_series = [maximum(sqrt.(w0[1].^2 .+ w0[2].^2 .+ w0[3].^2))]
        t_series = [0.0]
        E_series = [sum(abs2, to_real(uh)) / 2 / N^3]
        om_max_abs = wmax_series[1]
        max_dE = 0.0
        n_steps = Int(round(T / dt))
        wall0 = time()
        for n in 1:n_steps
            k1 = rhs(uh); k2 = rhs(uh .+ 0.5dt .* k1)
            k3 = rhs(uh .+ 0.5dt .* k2); k4 = rhs(uh .+ dt .* k3)
            uh = uh .+ (dt / 6) .* (k1 .+ 2k2 .+ 2k3 .+ k4)
            u = to_real(uh)
            w = to_real(fft3_omega(uh))
            if rotate
                ws = to_real(fft3_omega(uh .* repeat(reshape(m_smooth, 1, N, N, N); outer = 3)))
                wn = sqrt.(ws[1].^2 .+ ws[2].^2 .+ ws[3].^2)
                q = (wn ./ maximum(wn)).^2
                inv = 1.0 ./ max.(wn, 1e-30)
                what = cat([ws[c] .* inv for c in 1:3]...; dims = 1)
                upar = cat([(u[1] .* what[1] .+ u[2] .* what[2] .+ u[3] .* what[3]) .* what[c] for c in 1:3]...; dims = 1)
                uperp = [u[c] .- upar[c] for c in 1:3]
                cx = what[2] .* uperp[3] .- what[3] .* uperp[2]
                cy = what[3] .* uperp[1] .- what[1] .* uperp[3]
                cz = what[1] .* uperp[2] .- what[2] .* uperp[1]
                Epre = sum(abs2, u) / 2 / N^3
                un = [u[c] .+ q .* (upar[c] .+ cph .* uperp[c] .+ sph .* [cx, cy, cz][c] .- u[c]) for c in 1:3]
                uh = proj(to_spec(un))
                u = to_real(uh)
                Epost = sum(abs2, u) / 2 / N^3
                max_dE = max(max_dE, abs(Epost - Epre))
                w = to_real(fft3_omega(uh))
            end
            wmax = maximum(sqrt.(w[1].^2 .+ w[2].^2 .+ w[3].^2))
            push!(wmax_series, wmax); push!(t_series, n * dt)
            push!(E_series, sum(abs2, u) / 2 / N^3)
            om_max_abs = max(om_max_abs, wmax)
        end
        I_bkm = sum(0.5 * (wmax_series[i] + wmax_series[i+1]) * (t_series[i+1] - t_series[i])
                    for i in 1:length(wmax_series)-1)
        return Dict("mode" => rotate ? "b_rotation" : "true_nse",
                    "I_BKM" => I_bkm, "omega_max_abs" => om_max_abs,
                    "E_final" => E_series[end], "wall_seconds" => round(time() - wall0; digits = 1),
                    "max_dE_per_rotation" => rotate ? max_dE : nothing,
                    "n_points_saved" => length(wmax_series))
    end

    println("L5 (Julia): N=$N, ν=$nu, T=$T, dt=$dt — истинные NSE…")
    tn = case(false)
    println("    I_BKM=", round(tn["I_BKM"]; digits = 4), ", max‖ω‖∞=", round(tn["omega_max_abs"]; digits = 4))
    println("    NSE с непрерывным b-поворотом…")
    br = case(true)
    println("    I_BKM=", round(br["I_BKM"]; digits = 4), ", max‖ω‖∞=", round(br["omega_max_abs"]; digits = 4))

    ok = isfinite(tn["I_BKM"]) && isfinite(br["I_BKM"]) &&
         (br["max_dE_per_rotation"] === nothing || br["max_dE_per_rotation"] < 1e-4) &&
         tn["omega_max_abs"] < 10 && br["omega_max_abs"] < 10
    out = Dict("level" => "L5",
        "params" => Dict("N" => N, "nu" => nu, "T" => T, "dt" => dt,
                         "theta_b_deg" => float(rad2deg(THETA)),
                         "protocol" => "continuous dt·θ_b; Rodrigues form; smoothed axis (k ≤ N/6), "
                                       "quadratic weight; Leray; 2/3-правило, 2N-паддинг; собственный FFT"),
        "true_nse" => tn, "b_rotation" => br,
        "factor_BKM" => tn["I_BKM"] / br["I_BKM"],
        "factor_omega_max" => tn["omega_max_abs"] / br["omega_max_abs"],
        "note" => "исторический фактор 3,5× (N=24, глава 11) здесь не воспроизводится; ",
        "ok" => ok)
    write_json(joinpath(RESULTS_DIR, "l5_nse_3d_bkm.json"), out)
    println("L5: ", ok ? "PASS" : "FAIL", " | фактор BKM ", round(tn["I_BKM"] / br["I_BKM"]; digits = 4), "×")
    return ok
end

function fft3_omega(uh)
    cat([1im .* (KY .* uh[3] .- KZ .* uh[2]),
         1im .* (KZ .* uh[1] .- KX .* uh[3]),
         1im .* (KX .* uh[2] .- KY .* uh[1])]...; dims = 1)
end
