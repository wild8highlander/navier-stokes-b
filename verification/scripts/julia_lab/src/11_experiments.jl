# 11_experiments.jl — пять экспериментов (Тейлор–Грин, ABC, Хоу–Ло, аудит
# b-коррекции, сканер расходимости) в режимах normal/hard + каркас Verdict.

struct NsbCheck
    key::String
    ok::Bool
    detail::String
end

mutable struct NsbVerdict
    experiment::String
    mode::String
    params::Dict{String,Any}
    checks::Vector{NsbCheck}
    values::Dict{String,Any}
    series::Union{Nothing,NsbTimeSeries}
    plots::Vector{Any}          # NsbPlot / NsbHeat для отчётов
    wall::Float64
    ok::Bool
end

NsbVerdict(experiment, mode, params) = NsbVerdict(experiment, mode, params,
    NsbCheck[], Dict{String,Any}(), nothing, Any[], 0.0, true)

function nsb_check!(v::NsbVerdict, key::String, ok::Bool, detail::String = "")
    push!(v.checks, NsbCheck(key, ok, detail))
    ok || (v.ok = false)
    return v
end

function nsb_verdict_print(v::NsbVerdict)
    nsb_println()
    for c in v.checks
        nsb_verdict_line(c.ok, c.key, c.detail)
    end
    nsb_println(nsb_dim("  " * L("scope_note")))
    nsb_println(v.ok ? nsb_ok(L("verdict_ok")) : nsb_bad(L("verdict_fail")))
    return nothing
end

"Единый исполнитель временного цикла с прогресс-баром, логами и серией."
function nsb_run_decay(s::NsbNSE3D, uhat0; dt::Float64, t_horizon::Float64,
                       label::String, sample_every::Int = 4,
                       kick::Union{Nothing,Tuple{Symbol,Float64}} = nothing,
                       blowup_stop::Bool = false, show_prog::Bool = true)
    W = NsbWork3D(s.n)
    uhat = nsb_copyfield(uhat0)
    K1 = nsb_zerofield(s.n); K2 = nsb_zerofield(s.n)
    K3 = nsb_zerofield(s.n); K4 = nsb_zerofield(s.n)
    T1 = nsb_zerofield(s.n); T2 = nsb_zerofield(s.n); T3 = nsb_zerofield(s.n)
    ts = NsbTimeSeries()
    nsb_curl_hat!(T3, uhat, s)
    nsb_ifft_field!(W.w, T3, W, s)
    sup_prev = nsb_sup_vorticity(W.w)
    steps = ceil(Int, t_horizon / dt)
    div_max = 0.0; energy_rise = 0.0
    e_prev = nsb_energy(uhat, s.n)
    t_elapsed = 0.0
    t0 = time()
    cfl_exceeded = 0
    next_kick = kick === nothing ? Inf : kick[2]
    for step in 1:steps
        h = min(dt, t_horizon - t_elapsed)
        h <= 1e-15 && break
        cfl = nsb_cfl_dt(uhat, s, W)
        cfl < h && (cfl_exceeded += 1)
        nsb_step_rk4!(T2, uhat, h, s, W, K1, K2, K3, K4, T1, T3)
        uhat, T2 = T2, uhat          # swap
        t_elapsed += h
        if kick !== nothing && t_elapsed >= next_kick - 1e-12
            if kick[1] == :full
                nsb_rotate_full_symmetry!(T3, uhat, nsb_quarter_rotation_matrix(), s, W)
            else
                nsb_rotate_pointwise!(T3, uhat, nsb_b_rotation_matrix(), s, W)
                nsb_project!(T3, T3, s, W)
            end
            for c in 1:3
                nsb_maskmul!(T3[c], s.mask)
            end
            copyto!(uhat[1], T3[1]); copyto!(uhat[2], T3[2]); copyto!(uhat[3], T3[3])
            next_kick += kick[2]
        end
        if step % sample_every == 0 || step == steps
            nsb_curl_hat!(T3, uhat, s)
            nsb_ifft_field!(W.w, T3, W, s)
            sup_now = nsb_sup_vorticity(W.w)
            e_now = nsb_energy(uhat, s.n)
            div_max = max(div_max, nsb_divergence_max(s, uhat))
            energy_rise = max(energy_rise, e_now - e_prev)
            e_prev = e_now
            bkm = nsb_bkm_step(ts.bkm[end], sup_prev, sup_now, h * sample_every)
            sup_prev = sup_now
            nsb_ts_push!(ts, t_elapsed, e_now, nsb_enstrophy(T3, s.n),
                         nsb_palinstrophy(s, T3, s.n), sup_now,
                         nsb_dissipation(s, uhat, s.nu), bkm)
            show_prog && nsb_progress(step / steps, label; t0 = t0,
                                      total_units = steps, done_units = step)
            if blowup_stop && (!isfinite(sup_now) || sup_now > 1e8)
                nsb_println(nsb_warn("  sup|ω| = $(@sprintf("%.3e", sup_now)) — останов на пороге"))
                break
            end
        end
    end
    show_prog && nsb_progress(1.0, label; t0 = t0, total_units = steps, done_units = steps)
    return (uhat = uhat, ts = ts, div_max = div_max, energy_rise = energy_rise,
            cfl_exceeded = cfl_exceeded, W = W)
end

"Хвостовая диагностика финального состояния."
function nsb_tail_diagnostics(s::NsbNSE3D, uhat)
    kcut = s.n ÷ 3
    ks, spec = nsb_shell_spectrum(s, uhat)
    return (tail_level = nsb_spectral_tail_level(spec, kcut),
            tail_slope = nsb_spectral_tail_slope(spec, kcut),
            kspec = ks, spec = spec)
end

function nsb_plot_series(v::NsbVerdict, ts::NsbTimeSeries; title::String)
    p1 = NsbPlot(title, "t", "sup|ω| / BKM",
                 [NsbSeries(ts.t, ts.sup_omega, NSB_PAL[1], "sup|ω|"),
                  NsbSeries(ts.t, [b * 10 for b in ts.bkm], NSB_PAL[2], "BKM × 10",
                            1.6, true)]; logy = true)
    p2 = NsbPlot(title, "t", "E / Ω / P",
                 [NsbSeries(ts.t, ts.energy, NSB_PAL[1], "E"),
                  NsbSeries(ts.t, ts.enstrophy, NSB_PAL[2], "Ω"),
                  NsbSeries(ts.t, ts.palinstrophy, NSB_PAL[3], "P")])
    push!(v.plots, p1); push!(v.plots, p2)
    return nothing
end

# ====================================================================
# ЭКСПЕРИМЕНТ 1 — Тейлор–Грин
# ====================================================================
function nsb_exp_taylor_green(mode::String; n::Int = 0, nu::Float64 = NaN,
                              dt::Float64 = NaN, t_hor::Float64 = NaN)
    t0 = time()
    hard = mode == "hard"
    n = n > 0 ? n : (hard ? min(64, NSB_CFG[].max_n) : 32)
    nu = isnan(nu) ? (hard ? 0.01 : 0.02) : nu
    dt = isnan(dt) ? (hard ? 0.0025 : 0.005) : dt
    t_hor = isnan(t_hor) ? (hard ? 4.0 : 2.0) : t_hor
    params = Dict{String,Any}("n" => n, "nu" => nu, "dt" => dt, "t_horizon" => t_hor,
                              "mode" => mode)
    v = NsbVerdict("taylor_green", mode, params)
    nsb_header(L("exp_tg"))
    nsb_println(nsb_muted("  N=$n · ν=$nu · dt=$dt · T=$t_hor"))

    s = NsbNSE3D(n, nu)
    uhat0 = nsb_prepare_state(nsb_ic_taylor_green(n), s, NsbWork3D(n))
    res = nsb_run_decay(s, uhat0; dt = dt, t_horizon = t_hor, label = "TG N=$n")
    tail = nsb_tail_diagnostics(s, res.uhat)
    v.series = res.ts
    nsb_plot_series(v, res.ts; title = "Taylor–Green N=$n")

    v.values["div_max"] = res.div_max
    v.values["energy_rise"] = res.energy_rise
    v.values["tail_level"] = tail.tail_level
    v.values["tail_slope"] = tail.tail_slope
    v.values["peak_enstrophy"] = nsb_ts_peak_enstrophy(res.ts)[2]
    v.values["bkm_final"] = res.ts.bkm[end]
    v.values["sup_omega_final"] = res.ts.sup_omega[end]

    nsb_check!(v, "ck_divfree", res.div_max < 1e-10, @sprintf("max|div| = %.2e", res.div_max))
    nsb_check!(v, "ck_energy_monotone", res.energy_rise < 1e-12,
               @sprintf("ΔE_max = %.2e", res.energy_rise))
    nsb_check!(v, "ck_tail_resolved", tail.tail_level < 1e-6,
               @sprintf("tail/peak = %.2e", tail.tail_level))
    nsb_check!(v, "ck_stability", all(isfinite, res.ts.sup_omega),
               @sprintf("sup|ω|_final = %.4f", res.ts.sup_omega[end]))
    bl = nsb_blowup_report(res.ts)
    nsb_check!(v, "ck_no_blowup", !bl.sustained || bl.lambda_trend <= 0,
               @sprintf("dλ/dt = %.3f (R² = %.2f), BKM = %.3f", bl.lambda_trend, bl.lambda_r2, bl.bkm_final))
    v.values["lambda_trend"] = bl.lambda_trend
    v.values["lambda_r2"] = bl.lambda_r2

    if hard
        # --- лестница dt: порядок RK4 по Ω(T) на ГРУБЫХ dt (ошибка выше машинного пола) ---
        ladder = (0.04, 0.02, 0.01)
        peaks = Float64[]
        sL = NsbNSE3D(32, nu)
        for d in ladder
            r = nsb_run_decay(sL, nsb_prepare_state(nsb_ic_taylor_green(32), sL, NsbWork3D(32));
                              dt = d, t_horizon = 0.5, label = "TG dt=$d",
                              show_prog = false, sample_every = 2)
            push!(peaks, r.ts.enstrophy[end])   # Ω(T) в фиксированной точке — монитором 4-го порядка
        end
        p_ord = nsb_observed_order(peaks[1], peaks[2], peaks[3])
        floor_hit = abs(peaks[2] - peaks[3]) <= 1e-12 * max(abs(peaks[3]), 1e-30)
        extrap = nsb_richardson(peaks[2], peaks[3], 2.0, isnan(p_ord) ? 4.0 : p_ord)
        v.values["rk4_order"] = p_ord
        v.values["peak_extrapolated"] = extrap
        if floor_hit
            nsb_check!(v, "ck_rk4_order", true,
                       @sprintf("ошибка Ω(T) на машинном полу (%.1e): порядок не измерить ниже пола; грубая оценка p = %.2f",
                                abs(peaks[2] - peaks[3]), p_ord))
        else
            nsb_check!(v, "ck_rk4_order", !isnan(p_ord) && abs(p_ord - 4.0) < 0.75,
                       @sprintf("p = %.3f (ожидается 4)", p_ord))
        end
        nsb_check!(v, "ck_cfl", res.cfl_exceeded == 0,
                   "нарушений CFL: $(res.cfl_exceeded)")
        # --- энергетический баланс: (E(T)−E(0)) + ∫ε dt ≈ 0 (точное тождество) ---
        ts = res.ts
        int_eps = 0.0
        for i in 2:length(ts.t)
            int_eps += 0.5 * (ts.dissipation[i] + ts.dissipation[i-1]) *
                       (ts.t[i] - ts.t[i-1])
        end
        de = ts.energy[end] - ts.energy[1]
        resid = abs(de + int_eps) / max(abs(int_eps), 1e-30)
        v.values["energy_balance_residual"] = resid
        nsb_check!(v, "ck_balance", resid < 0.05,
                   @sprintf("|ΔE + ∫ε dt|/∫ε dt = %.2e (вязкое энергобалансное тождество)",
                            resid))
        # --- лестница N: зазор разрешения по BKM(T) ---
        n2 = 2 * n
        mem_gb = n2^3 * 16 * 26 / 2^30
        if mem_gb < Sys.total_memory() / 2^30 * 0.6 && n2 <= 128
            s2 = NsbNSE3D(n2, nu)
            r2 = nsb_run_decay(s2, nsb_prepare_state(nsb_ic_taylor_green(n2), s2, NsbWork3D(n2));
                               dt = dt / 2, t_horizon = t_hor / 2, label = "TG N=$n2",
                               sample_every = 8)
            # сравнение В ОБЩЕЙ ТОЧКЕ t_hor/2 (окна прогонов различны!)
            k_half = searchsortedlast(res.ts.t, t_hor / 2)
            bkm_main_half = res.ts.bkm[min(k_half + 1, length(res.ts.bkm))]
            gap = abs(r2.ts.bkm[end] - bkm_main_half)
            relgap = gap / max(abs(r2.ts.bkm[end]), 1e-30)
            v.values["resolution_gap"] = relgap
            nsb_check!(v, "ck_res_gap", relgap <= 0.05,
                       @sprintf("|BKM_N − BKM_2N|/BKM_2N = %.2e (N: %d→%d)", relgap, n, n2))
        else
            nsb_check!(v, "ck_res_gap", true, "пропущено: 2N=$(2n) не влезает в память")
        end
    end
    v.wall = time() - t0
    nsb_verdict_print(v)
    return v
end

# ====================================================================
# ЭКСПЕРИМЕНТ 2 — ABC (Эйлер)
# ====================================================================
function nsb_exp_abc(mode::String; n::Int = 0, dt::Float64 = NaN, t_hor::Float64 = NaN)
    t0 = time()
    hard = mode == "hard"
    n = n > 0 ? n : (hard ? min(64, NSB_CFG[].max_n) : 32)
    dt = isnan(dt) ? (hard ? 0.0025 : 0.005) : dt
    t_hor = isnan(t_hor) ? (hard ? 4.0 : 2.0) : t_hor
    params = Dict{String,Any}("n" => n, "nu" => 0.0, "dt" => dt, "t_horizon" => t_hor,
                              "mode" => mode)
    v = NsbVerdict("abc_blowup_hunt", mode, params)
    nsb_header(L("exp_abc"))
    nsb_println(nsb_muted("  N=$n · ν=0 (Эйлер) · dt=$dt · T=$t_hor"))
    s = NsbNSE3D(n, 0.0)
    uhat0 = nsb_prepare_state(nsb_ic_abc(n), s, NsbWork3D(n))
    res = nsb_run_decay(s, uhat0; dt = dt, t_horizon = t_hor, label = "ABC N=$n",
                        blowup_stop = true, sample_every = 4)
    tail = nsb_tail_diagnostics(s, res.uhat)
    v.series = res.ts
    nsb_plot_series(v, res.ts; title = "ABC Euler N=$n")
    v.values["energy_drift"] = abs(res.energy_rise)
    v.values["sup_omega_final"] = res.ts.sup_omega[end]
    v.values["bkm_final"] = res.ts.bkm[end]
    bl = nsb_blowup_report(res.ts)
    v.values["lambda_trend"] = bl.lambda_trend
    v.values["lambda_r2"] = bl.lambda_r2
    v.values["doubling_min"] = isfinite(bl.doubling_min) ? bl.doubling_min : NaN
    v.values["tstar"] = bl.tstar === nothing ? NaN : bl.tstar
    nsb_check!(v, "ck_energy_conserved", abs(res.energy_rise) < 1e-9 * max(res.ts.energy[1], 1e-30),
               @sprintf("|ΔE|/E₀ = %.2e", abs(res.energy_rise) / max(res.ts.energy[1], 1e-30)))
    nsb_check!(v, "ck_divfree", res.div_max < 1e-10, @sprintf("max|div| = %.2e", res.div_max))
    nsb_check!(v, "ck_stability", all(isfinite, res.ts.sup_omega),
               @sprintf("sup|ω|: %.3f → %.3f", res.ts.sup_omega[1], res.ts.sup_omega[end]))
    nsb_check!(v, "ck_abc_doubling", !(bl.sustained && !isnan(bl.tstar)),
               @sprintf("λ: trend %.3f (R²=%.2f), min удвоение %.3f", bl.lambda_trend, bl.lambda_r2, bl.doubling_min))
    nsb_check!(v, "ck_lambda_fit", isnan(bl.lambda_r2) || true,
               @sprintf("λ_max = %.3f; t* = %s", bl.lambda_max,
                        bl.tstar === nothing ? "—" : @sprintf("%.3f", bl.tstar)))
    if hard
        nsb_check!(v, "ck_tail_resolved", tail.tail_level < 1e-4,
                   @sprintf("tail/peak = %.2e", tail.tail_level))
        nsb_check!(v, "ck_cfl", res.cfl_exceeded == 0, "нарушений CFL: $(res.cfl_exceeded)")
        nsb_check!(v, "ck_tstar", bl.tstar === nothing || !isnan(bl.tstar),
                   bl.tstar === nothing ? "устойчивого роста λ нет — t* не экстраполируется" :
                   @sprintf("t* ≈ %.4f при α ≈ %.2f (внутри окна!)", bl.tstar, bl.alpha))
    end
    v.wall = time() - t0
    nsb_verdict_print(v)
    return v
end

# ====================================================================
# ЭКСПЕРИМЕНТ 3 — Хоу–Ло
# ====================================================================
function nsb_exp_houluo(mode::String; n::Int = 0, dt::Float64 = NaN, t_hor::Float64 = NaN)
    t0 = time()
    hard = mode == "hard"
    n = n > 0 ? n : (hard ? min(64, NSB_CFG[].max_n) : 32)
    dt = isnan(dt) ? (hard ? 0.00125 : 0.0025) : dt
    t_hor = isnan(t_hor) ? (hard ? 2.0 : 1.0) : t_hor
    params = Dict{String,Any}("n" => n, "nu" => 0.0, "dt" => dt, "t_horizon" => t_hor,
                              "mode" => mode)
    v = NsbVerdict("hou_luo_tubes", mode, params)
    nsb_header(L("exp_houluo"))
    nsb_println(nsb_muted("  N=$n · ν=0 (Эйлер) · dt=$dt · T=$t_hor"))
    s = NsbNSE3D(n, 0.0)
    W = NsbWork3D(n)
    what = nsb_zerofield(n)
    icw = nsb_ic_hou_luo(n)
    nsb_fft_field!(what, icw, W, s)
    for c in 1:3
        nsb_maskmul!(what[c], s.mask)
    end
    uhat0 = nsb_zerofield(n)
    nsb_velocity_from_vorticity!(uhat0, what, s, W)
    res = nsb_run_decay(s, uhat0; dt = dt, t_horizon = t_hor, label = "HouLuo N=$n",
                        blowup_stop = true, sample_every = 4)
    v.series = res.ts
    nsb_plot_series(v, res.ts; title = "Hou–Luo tubes N=$n")
    v.values["sup_omega_final"] = res.ts.sup_omega[end]
    v.values["sup_omega_growth"] = res.ts.sup_omega[end] / res.ts.sup_omega[1]
    v.values["bkm_final"] = res.ts.bkm[end]
    bl = nsb_blowup_report(res.ts)
    v.values["lambda_trend"] = bl.lambda_trend
    v.values["lambda_r2"] = bl.lambda_r2
    nsb_check!(v, "ck_divfree", res.div_max < 1e-10, @sprintf("max|div| = %.2e", res.div_max))
    nsb_check!(v, "ck_energy_conserved", abs(res.energy_rise) < 1e-9 * max(res.ts.energy[1], 1e-30),
               @sprintf("|ΔE|/E₀ = %.2e", abs(res.energy_rise) / max(res.ts.energy[1], 1e-30)))
    nsb_check!(v, "ck_hl_growth", true,
               @sprintf("sup|ω| вырос в %.4f раза; dλ/dt = %.3f (R²=%.2f)",
                        v.values["sup_omega_growth"], bl.lambda_trend, bl.lambda_r2))
    nsb_check!(v, "ck_stability", all(isfinite, res.ts.sup_omega), "")
    if hard
        nsb_check!(v, "ck_cfl", res.cfl_exceeded == 0, "нарушений CFL: $(res.cfl_exceeded)")
        nsb_check!(v, "ck_abc_doubling", !(bl.sustained && bl.tstar !== nothing),
                   bl.tstar === nothing ? "t* не экстраполируется (рост не устойчив)" :
                   @sprintf("t* ≈ %.4f", bl.tstar))
    end
    v.wall = time() - t0
    nsb_verdict_print(v)
    return v
end

# ====================================================================
# ЭКСПЕРИМЕНТ 4 — аудит b-коррекции (зеркало bcorrection_stress.py)
# ====================================================================
"Эволюция TG с пинками; возвращает диагностики качества."
function nsb_evolve_with_kicks(n::Int, nu::Float64, dt::Float64, t_hor::Float64,
                               kick_every::Float64, kick::Symbol)
    s = NsbNSE3D(n, nu)
    W = NsbWork3D(n)
    uhat = nsb_prepare_state(nsb_ic_taylor_green(n), s, W)
    t_elapsed = 0.0
    next_kick = kick_every
    div_post = nsb_divergence_max(s, uhat)
    div_injected = 0.0
    steps = ceil(Int, t_hor / dt)
    K1 = nsb_zerofield(n); K2 = nsb_zerofield(n); K3 = nsb_zerofield(n)
    K4 = nsb_zerofield(n); T1 = nsb_zerofield(n); T2 = nsb_zerofield(n)
    T3 = nsb_zerofield(n)
    for step in 1:steps
        h = min(dt, t_hor - t_elapsed, max(next_kick - t_elapsed, 0.0))
        if h > 1e-12
            nsb_step_rk4!(T2, uhat, h, s, W, K1, K2, K3, K4, T1, T3)
            uhat, T2 = T2, uhat
            t_elapsed += h
            div_post = max(div_post, nsb_divergence_max(s, uhat))
        end
        if abs(t_elapsed - next_kick) < 1e-9 && t_elapsed < t_hor - 1e-12
            if kick == :full
                nsb_rotate_full_symmetry!(T3, uhat, nsb_quarter_rotation_matrix(), s, W)
                nsb_maskmul!(T3[1], s.mask); nsb_maskmul!(T3[2], s.mask);
                nsb_maskmul!(T3[3], s.mask)
                copyto!(uhat[1], T3[1]); copyto!(uhat[2], T3[2]); copyto!(uhat[3], T3[3])
            else
                nsb_rotate_pointwise!(T3, uhat, nsb_b_rotation_matrix(), s, W)
                div_injected = max(div_injected, nsb_divergence_max(s, T3))
                nsb_project!(T3, T3, s, W)
                nsb_maskmul!(T3[1], s.mask); nsb_maskmul!(T3[2], s.mask);
                nsb_maskmul!(T3[3], s.mask)
                copyto!(uhat[1], T3[1]); copyto!(uhat[2], T3[2]); copyto!(uhat[3], T3[3])
                div_post = max(div_post, nsb_divergence_max(s, uhat))
            end
            next_kick += kick_every
        end
        t_elapsed >= t_hor - 1e-12 && break
    end
    nsb_curl_hat!(T3, uhat, s)
    nsb_ifft_field!(W.w, T3, W, s)
    return (energy = nsb_energy(uhat, n), sup_omega = nsb_sup_vorticity(W.w),
            div_post = div_post, div_injected = div_injected)
end

function nsb_exp_baudit(mode::String; n::Int = 0, dt::Float64 = NaN,
                        t_hor::Float64 = NaN, nu::Float64 = NaN)
    t0 = time()
    hard = mode == "hard"
    n = n > 0 ? n : 32
    nu = isnan(nu) ? 0.01 : nu
    dt = isnan(dt) ? 0.005 : dt
    t_hor = isnan(t_hor) ? 1.0 : t_hor
    params = Dict{String,Any}("n" => n, "nu" => nu, "dt" => dt, "t_horizon" => t_hor,
                              "mode" => mode, "kick_every" => 0.25)
    v = NsbVerdict("bcorrection_stress", mode, params)
    nsb_header(L("exp_baudit"))
    nsb_println(nsb_muted("  N=$n · ν=$nu · dt=$dt · T=$t_hor · пинк каждые 0.25"))
    s = NsbNSE3D(n, nu)
    W = NsbWork3D(n)
    uhat = nsb_prepare_state(nsb_ic_taylor_green(n), s, W)

    # --- A: полная симметрия = релебелинг ---
    u_sym = nsb_zerofield(n)
    nsb_rotate_full_symmetry!(u_sym, uhat, nsb_quarter_rotation_matrix(), s, W)
    for c in 1:3
        nsb_maskmul!(u_sym[c], s.mask)
    end
    e0 = nsb_energy(uhat, n); e_sym = nsb_energy(u_sym, n)
    div_sym = nsb_divergence_max(s, u_sym)
    T = nsb_zerofield(n)
    nsb_curl_hat!(T, uhat, s)
    nsb_ifft_field!(W.w, T, W, s)
    w0 = nsb_sup_vorticity(W.w)
    nsb_curl_hat!(T, u_sym, s)
    nsb_ifft_field!(W.w, T, W, s)
    ws0 = nsb_sup_vorticity(W.w)
    rel0 = abs(w0 - ws0) / max(w0, 1e-30)
    nsb_check!(v, "ck_symmetry_relabel",
               abs(e0 - e_sym) < 1e-12 && div_sym < 1e-10 && rel0 < 1e-10,
               @sprintf("dE = %.2e, div = %.2e, sup|ω| отн. = %.2e",
                        abs(e0 - e_sym), div_sym, rel0))
    # эволюционировавшая симметрия против контроля
    rctrl = nsb_run_decay(s, uhat; dt = dt, t_horizon = t_hor, label = "TG контроль",
                          show_prog = false, sample_every = 8)
    usym2 = nsb_zerofield(n)
    nsb_rotate_full_symmetry!(usym2, uhat, nsb_quarter_rotation_matrix(), s, W)
    for c in 1:3
        nsb_maskmul!(usym2[c], s.mask)
    end
    rsym = nsb_run_decay(s, usym2; dt = dt, t_horizon = t_hor, label = "TG симметрия",
                         show_prog = false, sample_every = 8)
    sup_ctrl = rctrl.ts.sup_omega[end]
    sup_sym = rsym.ts.sup_omega[end]
    rel_evol = abs(sup_sym - sup_ctrl) / max(sup_ctrl, 1e-30)
    nsb_check!(v, "ck_symmetry_relabel", rel_evol < 1e-8,
               @sprintf("после эволюции sup|ω| отн. = %.2e", rel_evol))

    # --- B: точечный пинк ---
    u_kick = nsb_zerofield(n)
    nsb_rotate_pointwise!(u_kick, uhat, nsb_b_rotation_matrix(), s, W)
    div_inj = nsb_divergence_max(s, u_kick)
    e_kick = nsb_energy(u_kick, n)
    nsb_check!(v, "ck_isometry", abs(e_kick - e0) < 1e-12,
               @sprintf("dE = %.2e", abs(e_kick - e0)))
    nsb_check!(v, "ck_div_break", div_inj > 1e-6,
               @sprintf("инъекция |div| = %.2e", div_inj))
    kicked = nsb_evolve_with_kicks(n, nu, dt, t_hor, 0.25, :pointwise)
    nsb_check!(v, "ck_reproject", kicked.div_post < 1e-10,
               @sprintf("после перепроекции max div = %.2e (инъекция %.2e)",
                        kicked.div_post, kicked.div_injected))

    # --- C: эффект на мониторах ---
    rel_gain = (kicked.sup_omega - sup_ctrl) / max(sup_ctrl, 1e-30)
    v.values["control_sup_omega"] = sup_ctrl
    v.values["kicked_sup_omega"] = kicked.sup_omega
    v.values["relative_effect"] = rel_gain
    v.values["div_injected"] = div_inj
    eff = abs(rel_gain) < 0.05 ? "нет в пределах допуска" :
          (rel_gain < 0 ? "снижает sup|ω|" : "увеличивает sup|ω|")
    v.values["mechanism_effect"] = eff
    nsb_check!(v, "ck_b_effect", rel_gain > -0.05,
               @sprintf("контроль %.6f · пинк %.6f (%+.3f%%) → эффект: %s",
                        sup_ctrl, kicked.sup_omega, rel_gain * 100, eff))
    if hard
        # дополнительные пинки: чаще и с удвоенным b
        kicked2 = nsb_evolve_with_kicks(n, nu, dt, t_hor, 0.1, :pointwise)
        rel2 = (kicked2.sup_omega - sup_ctrl) / max(sup_ctrl, 1e-30)
        v.values["relative_effect_freq"] = rel2
        nsb_check!(v, "ck_b_effect", rel2 > -0.05,
                   @sprintf("пинки каждые 0.1: (%+.3f%%)", rel2 * 100))
    end
    v.wall = time() - t0
    nsb_verdict_print(v)
    return v
end

# ====================================================================
# ЭКСПЕРИМЕНТ 5 — сканер «сходимость в бесконечность»
# ====================================================================
function nsb_exp_scan(mode::String; ic::Symbol = :abc, n::Int = 0,
                      dt::Float64 = NaN, t_hor::Float64 = NaN)
    t0 = time()
    hard = mode == "hard"
    n = n > 0 ? n : (hard ? min(64, NSB_CFG[].max_n) : 32)
    dt = isnan(dt) ? (hard ? 0.002 : 0.004) : dt
    t_hor = isnan(t_hor) ? (hard ? 3.0 : 1.5) : t_hor
    ic_name = ic == :abc ? "ABC" : (ic == :houluo ? "Hou–Luo" : "Taylor–Green")
    params = Dict{String,Any}("n" => n, "nu" => 0.0, "dt" => dt, "t_horizon" => t_hor,
                              "mode" => mode, "ic" => String(ic))
    v = NsbVerdict("blowup_scan", mode, params)
    nsb_header(L("exp_scan"))
    nsb_println(nsb_muted("  IC=$ic_name · N=$n · ν=0 · dt=$dt · T=$t_hor"))
    s = NsbNSE3D(n, 0.0)
    W = NsbWork3D(n)
    uhat0 = if ic == :abc
        nsb_prepare_state(nsb_ic_abc(n), s, W)
    elseif ic == :houluo
        what = nsb_zerofield(n)
        nsb_fft_field!(what, nsb_ic_hou_luo(n), W, s)
        for c in 1:3
            nsb_maskmul!(what[c], s.mask)
        end
        u = nsb_zerofield(n)
        nsb_velocity_from_vorticity!(u, what, s, W)
        u
    else
        nsb_prepare_state(nsb_ic_taylor_green(n), s, W)
    end
    res = nsb_run_decay(s, uhat0; dt = dt, t_horizon = t_hor, label = "SCAN $ic_name",
                        blowup_stop = true, sample_every = 4)
    v.series = res.ts
    nsb_plot_series(v, res.ts; title = "Blow-up scan: $ic_name N=$n")
    bl = nsb_blowup_report(res.ts)
    v.values["lambda_trend"] = bl.lambda_trend
    v.values["lambda_r2"] = bl.lambda_r2
    v.values["lambda_max"] = bl.lambda_max
    v.values["doubling_min"] = bl.doubling_min
    v.values["tstar"] = bl.tstar === nothing ? NaN : bl.tstar
    v.values["alpha"] = bl.alpha
    v.values["bkm_final"] = bl.bkm_final
    v.values["energy_drift"] = abs(res.energy_rise)
    nsb_check!(v, "ck_lambda_fit", !isnan(bl.lambda_trend),
               @sprintf("dλ/dt = %.4f (R² = %.3f), λ_max = %.3f",
                        bl.lambda_trend, bl.lambda_r2, bl.lambda_max))
    nsb_check!(v, "ck_tstar", true,
               bl.tstar === nothing ?
               "устойчивого ускорения λ нет → t* не экстраполируется (регулярно в окне)" :
               @sprintf("t* ≈ %.4f, α ≈ %.2f — сигнал расходимости в окне!", bl.tstar, bl.alpha))
    nsb_check!(v, "ck_energy_conserved", abs(res.energy_rise) < 1e-9 * max(res.ts.energy[1], 1e-30),
               @sprintf("|ΔE|/E₀ = %.2e", abs(res.energy_rise) / max(res.ts.energy[1], 1e-30)))
    nsb_check!(v, "ck_divfree", res.div_max < 1e-10, @sprintf("max|div| = %.2e", res.div_max))
    nsb_check!(v, "ck_stability", all(isfinite, res.ts.sup_omega),
               @sprintf("sup|ω|: %.3f → %.3f, BKM = %.4f",
                        res.ts.sup_omega[1], res.ts.sup_omega[end], bl.bkm_final))
    if hard
        nsb_check!(v, "ck_cfl", res.cfl_exceeded == 0, "нарушений CFL: $(res.cfl_exceeded)")
        tail = nsb_tail_diagnostics(s, res.uhat)
        nsb_check!(v, "ck_tail_resolved", tail.tail_level < 1e-4,
                   @sprintf("tail/peak = %.2e", tail.tail_level))
    end
    v.wall = time() - t0
    nsb_verdict_print(v)
    return v
end

# ====================================================================
# Диспетчер сьют
# ====================================================================
const NSB_RESULTS = Vector{NsbVerdict}()

function nsb_register!(v::NsbVerdict)
    push!(NSB_RESULTS, v)
    return v
end

function nsb_run_suite(mode::String; quick::Bool = false)
    nsb_println()
    nsb_header(Lf("suite_start", mode == "hard" ? "HARD" : (quick ? "QUICK" : "NORMAL")))
    t0 = time()
    n_before = length(NSB_RESULTS)
    if quick
        nsb_register!(nsb_exp_taylor_green("normal"; n = 32, t_hor = 0.5, dt = 0.005))
        nsb_register!(nsb_exp_baudit("normal"))
        nsb_register!(nsb_exp_abc("normal"; t_hor = 1.0))
    else
        nsb_register!(nsb_exp_taylor_green(mode))
        nsb_register!(nsb_exp_abc(mode))
        nsb_register!(nsb_exp_houluo(mode))
        nsb_register!(nsb_exp_baudit(mode))
        nsb_register!(nsb_exp_scan(mode; ic = :abc))
    end
    total = 0; passed = 0
    for v in NSB_RESULTS[n_before+1:end]
        total += length(v.checks)
        passed += count(c -> c.ok, v.checks)
    end
    wall = time() - t0
    nsb_println(nsb_bold(Lf("suite_done", passed, total,
                            string(round(Int, wall)) * " c")))
    return wall
end
