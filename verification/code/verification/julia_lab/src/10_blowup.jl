# 10_blowup.jl — анализ «сходимости в бесконечность»: λ(t) = d/dt ln sup|ω|,
# линейный тренд λ, подгонка sup|ω| ~ A(t*−t)^−α, экстраполяция t*.
# Плюс зеркало research_lab/extrapolate.py (лестницы Ричардсона).

"Мгновенная скорость роста λ(t) серии sup|ω| (центральная разность)."
function nsb_growth_rate(ts::NsbTimeSeries)
    n = length(ts.sup_omega)
    n < 3 && return (Float64[], Float64[])
    ts_ = Vector{Float64}(); lam = Vector{Float64}()
    for i in 2:n-1
        dt1 = ts.t[i] - ts.t[i-1]
        dt2 = ts.t[i+1] - ts.t[i]
        (dt1 <= 0 || dt2 <= 0) && continue
        s0, s1, s2 = ts.sup_omega[i-1], ts.sup_omega[i], ts.sup_omega[i+1]
        (s0 > 0 && s1 > 0 && s2 > 0) || continue
        push!(lam, (log(s2) - log(s0)) / (dt1 + dt2))
        push!(ts_, ts.t[i])
    end
    return (ts_, lam)
end

struct NsbBlowupReport
    lambda_trend::Float64          # наклон dλ/dt (МНК)
    lambda_r2::Float64
    lambda_max::Float64
    doubling_min::Float64          # мин время удвоения sup|ω|
    sustained::Bool         # λ растёт устойчиво (≥25% окна с dλ/dt>0 и R²>0.8)
    tstar::Union{Nothing,Float64}  # экстраполир. время сингулярности
    alpha::Float64                 # показатель (t*−t)^−α
    bkm_final::Float64
    verdict_key::String            # ключ вердикта для i18n
end

"Полный blow-up анализ временной серии."
function nsb_blowup_report(ts::NsbTimeSeries; window_frac::Float64 = 0.25)
    t_lam, lam = nsb_growth_rate(ts)
    bkm_final = isempty(ts.bkm) ? 0.0 : ts.bkm[end]
    if length(t_lam) < 4
        return NsbBlowupReport(NaN, NaN, isempty(lam) ? NaN : maximum(lam), NaN,
                               false, nothing, NaN, bkm_final,
                               "ck_lambda_fit")
    end
    a, b, r2 = nsb_linfit(t_lam, lam)
    lam_max = maximum(lam)
    # мин время удвоения
    doublings = Float64[]
    for i in 2:length(ts.sup_omega)
        s0, s1 = ts.sup_omega[i-1], ts.sup_omega[i]
        dt = ts.t[i] - ts.t[i-1]
        (s0 > 0 && s1 > s0 && dt > 0) && push!(doublings, dt * log(2) / (log(s1 / s0)))
    end
    doubl_min = isempty(doublings) ? Inf : minimum(doublings)
    # устойчивый рост: последние window_frac окна с положительным трендом
    nfit = max(4, round(Int, length(t_lam) * window_frac))
    tail_t = t_lam[end-nfit+1:end]
    tail_l = lam[end-nfit+1:end]
    at, bt, r2t = nsb_linfit(tail_t, tail_l)
    sustained = !isnan(at) && at > 0 && r2t > 0.5 && lam_max > 0
    tstar = nothing; alpha = NaN
    if sustained
        # подгонка sup|ω| = A (t*−t)^−α перебором α ∈ [0.5, 7]
        sup = ts.sup_omega; tt = ts.t
        best_err = Inf; best_tstar = NaN; best_alpha = NaN
        T_end = tt[end]
        for al in 0.5:0.25:7.0
            for frac in 1.02:0.02:2.5
                tst = T_end * frac
                ok = true
                xs = Float64[]; ys = Float64[]
                for (ti, si) in zip(tt, sup)
                    d = tst - ti
                    d <= 0 && (ok = false; break)
                    push!(xs, log(d)); push!(ys, log(max(si, 1e-300)))
                end
                ok || continue
                A, B, r2f = nsb_linfit(xs, ys)
                isnan(r2f) && continue
                err = -r2f
                if err < best_err
                    best_err = err; best_tstar = tst; best_alpha = -A
                end
            end
        end
        if best_err < -0.9        # R² > 0.9 по log-log
            tstar = best_tstar; alpha = best_alpha
        end
    end
    verdict_key = sustained ? "ck_lambda_fit" : "ck_no_blowup"
    return NsbBlowupReport(a, r2, lam_max, doubl_min, sustained, tstar, alpha,
                           bkm_final, verdict_key)
end

# ------------------------- зеркала extrapolate.py -------------------------
"Измеренный порядок по геометрической тройке значений."
function nsb_observed_order(j_c, j_f, j_ff; ratio = 2.0)
    denom = j_c - j_f
    numer = j_f - j_ff
    (abs(denom) < 1e-30 || abs(numer) < 1e-30) && return NaN
    return log(ratio, abs(denom / numer))   # log(base, x): порядок аргументов важен!
end

"Ричардсон-оценка J(0) по двум тонким уровням."
nsb_richardson(j_f, j_ff, ratio, order) =
    j_ff + (j_ff - j_f) / (ratio^order - 1.0)
