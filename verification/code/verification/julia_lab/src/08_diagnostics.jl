# 08_diagnostics.jl — зеркало research_lab/diagnostics.py: BKM-монитор,
# энстрофия, палинстрофия, диссипация, sup|ω|, спектры по оболочкам, div.

"Времянная серия диагностик (зеркало TimeSeries)."
mutable struct NsbTimeSeries
    t::Vector{Float64}
    energy::Vector{Float64}
    enstrophy::Vector{Float64}
    palinstrophy::Vector{Float64}
    sup_omega::Vector{Float64}
    dissipation::Vector{Float64}
    bkm::Vector{Float64}          # со стартовым 0.0
end
NsbTimeSeries() = NsbTimeSeries(Float64[], Float64[], Float64[], Float64[],
                                Float64[], Float64[], [0.0])

function nsb_ts_push!(ts, t, e, om, pal, sup, eps_, bkm)
    push!(ts.t, t); push!(ts.energy, e); push!(ts.enstrophy, om)
    push!(ts.palinstrophy, pal); push!(ts.sup_omega, sup)
    push!(ts.dissipation, eps_); push!(ts.bkm, bkm)
    return ts
end

function nsb_ts_peak_enstrophy(ts)
    i = argmax(ts.enstrophy)
    return (ts.t[i], ts.enstrophy[i])
end

"E = <|u|²>/2 (Парсеваль: Σ|û|²/n⁶)."
function nsb_energy(uhat, n::Int)
    s = 0.0
    for c in 1:3, i in eachindex(uhat[c])
        s += abs2(uhat[c][i])
    end
    return 0.5 * s / n^6
end

"Ω = <|curl u|²>/2."
function nsb_enstrophy(what, n::Int)
    s = 0.0
    for c in 1:3, i in eachindex(what[c])
        s += abs2(what[c][i])
    end
    return 0.5 * s / n^6
end

"P = <|curl ω|²>/2 — счётчик усиления градиентов завихренности."
function nsb_palinstrophy(s::NsbNSE3D, what, n::Int)
    ssum = 0.0
    @inbounds for i in eachindex(what[1])
        kx, ky, kz = s.kx[i], s.ky[i], s.kz[i]
        w1, w2, w3 = what[1][i], what[2][i], what[3][i]
        a1 = ky * w3 - kz * w2
        a2 = kz * w1 - kx * w3
        a3 = kx * w2 - ky * w1
        ssum += abs2(a1) + abs2(a2) + abs2(a3)
    end
    return 0.5 * ssum / n^6
end

"ε = ν <|∇u|²>."
function nsb_dissipation(s::NsbNSE3D, uhat, nu::Float64)
    ssum = 0.0
    for c in 1:3, i in eachindex(uhat[c])
        ssum += s.ksq[i] * abs2(uhat[c][i])
    end
    return nu * ssum / s.n^6
end

"sup_x |ω| — коллокационный максимум (практ. прокси L∞)."
function nsb_sup_vorticity(w::NTuple{3,Array{Float64,3}})
    m = 0.0
    @inbounds for i in eachindex(w[1])
        v = sqrt(w[1][i]^2 + w[2][i]^2 + w[3][i]^2)
        v > m && (m = v)
    end
    return m
end

"Трапецеидальный прирост BKM-интеграла за шаг."
nsb_bkm_step(bkm, sup_prev, sup_now, dt) = bkm + 0.5 * (sup_prev + sup_now) * dt

"max |div u| (Парсеваль, на объём)."
function nsb_divergence_max(s::NsbNSE3D, uhat)
    ssum = 0.0
    @inbounds for i in eachindex(uhat[1])
        d = s.kx[i] * uhat[1][i] + s.ky[i] * uhat[2][i] + s.kz[i] * uhat[3][i]
        ssum += abs2(d)
    end
    return sqrt(ssum) / s.n^3
end

"|k| решётка."
function nsb_spectral_radii(s::NsbNSE3D)
    return sqrt.(Float64.(s.ksq))
end

"Усреднённый по оболочкам спектр E(k) (Σ E(k) = E)."
function nsb_shell_spectrum(s::NsbNSE3D, uhat)
    n = s.n
    kr = nsb_spectral_radii(s)
    kmax = Int(ceil(maximum(kr)))
    counts = zeros(Int, kmax + 1)
    sums = zeros(Float64, kmax + 1)
    for i in eachindex(uhat[1])
        e = 0.5 * (abs2(uhat[1][i]) + abs2(uhat[2][i]) + abs2(uhat[3][i])) / n^6
        ki = Int(round(kr[i])) + 1
        counts[ki] += 1
        sums[ki] += e
    end
    spectrum = [counts[k] > 0 ? sums[k] / counts[k] : 0.0 for k in 1:kmax+1]
    return (collect(0.0:kmax), spectrum)
end

"Монитор разрешения: max E(k) у порога деалиаса / пик спектра."
function nsb_spectral_tail_level(spectrum::Vector{Float64}, k_cutoff::Int;
                                 window::Int = 1)
    k_hi = min(k_cutoff + 1, length(spectrum))
    k_lo = max(2, k_hi - window)
    isempty(spectrum[2:end]) && return 0.0
    peak = maximum(spectrum[2:end])
    peak <= 0 && return 0.0
    tail = spectrum[k_lo:k_hi]
    return isempty(tail) ? 0.0 : maximum(tail) / peak
end

"МНК-наклон log E(k) по последней декаде мод."
function nsb_spectral_tail_slope(spectrum::Vector{Float64}, k_hi::Int)
    pts = Tuple{Float64,Float64}[]
    for k in 1:min(k_hi, length(spectrum) - 1)
        spectrum[k+1] > 0 && push!(pts, (Float64(k), log(spectrum[k+1])))
    end
    length(pts) < 3 && return NaN
    sx = sum(p[1] for p in pts); sy = sum(p[2] for p in pts)
    n = length(pts)
    sxx = sum(p[1]^2 for p in pts); sxy = sum(p[1] * p[2] for p in pts)
    den = n * sxx - sx^2
    return den == 0 ? NaN : (n * sxy - sx * sy) / den
end

"МНК-подгонка y = a·x + b, возвращает (a, b, R²)."
function nsb_linfit(xs::Vector{Float64}, ys::Vector{Float64})
    n = length(xs)
    n < 2 && return (NaN, NaN, NaN)
    sx = sum(xs); sy = sum(ys)
    sxx = sum(x * x for x in xs); sxy = sum(x * y for (x, y) in zip(xs, ys))
    den = n * sxx - sx^2
    den == 0 && return (NaN, NaN, NaN)
    a = (n * sxy - sx * sy) / den
    b = (sy - a * sx) / n
    ybar = sy / n
    ss_res = sum((y - (a * x + b))^2 for (x, y) in zip(xs, ys))
    ss_tot = sum((y - ybar)^2 for y in ys)
    r2 = ss_tot > 0 ? 1 - ss_res / ss_tot : NaN
    return (a, b, r2)
end
