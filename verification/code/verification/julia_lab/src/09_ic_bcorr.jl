# 09_ic_bcorr.jl — начальные условия (Тейлор–Грин, ABC, Хоу–Ло, случайное)
# и константы b-коррекции: b = 1/(4π + 2√3), θ_b = arcsin(b), R = Rodrigues.
# Зеркало research_lab/initial_conditions.py + constants.py.

const NSB_B = 1.0 / (4.0 * π + 2.0 * sqrt(3.0))
const NSB_THETA_B = asin(NSB_B)
const NSB_AXIS = (0.3, -0.5, sqrt(1.0 - 0.3^2 - 0.5^2))

"Матрица поворота Родрига вокруг единичной оси."
function nsb_rodrigues(theta::Float64, axis::Tuple{Float64,Float64,Float64})
    ex, ey, ez = axis
    cmat = [0.0 -ez ey; ez 0.0 -ex; -ey ex 0.0]
    outer = [ex*ex ex*ey ex*ez; ey*ex ey*ey ey*ez; ez*ex ez*ey ez*ez]
    c, s = cos(theta), sin(theta)
    I3 = [1.0 0.0 0.0; 0.0 1.0 0.0; 0.0 0.0 1.0]
    M = c * I3 + (1 - c) * outer - s * cmat
    return [[M[i, j] for j in 1:3] for i in 1:3]
end

nsb_b_rotation_matrix() = nsb_rodrigues(NSB_THETA_B, NSB_AXIS)
nsb_quarter_rotation_matrix() = nsb_rodrigues(π / 2, (0.0, 0.0, 1.0))

# --------------------------------------------------------------- сетки/IC
"Координаты сетки [0, 2π)³."
function nsb_grid(n::Int)
    x = [2π * (i - 1) / n for i in 1:n]
    return x
end

"u = (sin x cos y cos z, −cos x sin y cos z, 0)."
function nsb_ic_taylor_green(n::Int)
    x = nsb_grid(n)
    u1 = zeros(n, n, n); u2 = zeros(n, n, n); u3 = zeros(n, n, n)
    sx = [sin(v) for v in x]; cx = [cos(v) for v in x]
    Threads.@threads for k in 1:n
        for j in 1:n, i in 1:n
            u1[i, j, k] = sx[i] * cx[j] * cx[k]
            u2[i, j, k] = -cx[i] * sx[j] * cx[k]
        end
    end
    return (u1, u2, u3)
end

"ABC-поток: точное собственное поле curl (λ = 1)."
function nsb_ic_abc(n::Int; a = 1.0, b = 1.0, c = 1.0)
    x = nsb_grid(n)
    sx = [sin(v) for v in x]; cx = [cos(v) for v in x]
    u1 = zeros(n, n, n); u2 = zeros(n, n, n); u3 = zeros(n, n, n)
    Threads.@threads for k in 1:n
        for j in 1:n, i in 1:n
            u1[i, j, k] = a * sx[k] + c * cx[j]
            u2[i, j, k] = b * sx[i] + a * cx[k]
            u3[i, j, k] = c * sx[j] + b * cx[i]
        end
    end
    return (u1, u2, u3)
end

"Хоу–Ло: две антипараллельные гауссовы трубки вдоль x + симметричное
возмущение (1 + ε cos x). Возвращает ЗАВИХРЕННОСТЬ; скорость — Био–Саваром."
function nsb_ic_hou_luo(n::Int; gamma = 1.0, delta = π / 8, sigma = π / 16,
                        perturbation = 0.05)
    x = nsb_grid(n)
    w1 = zeros(n, n, n); w2 = zeros(n, n, n); w3 = zeros(n, n, n)
    inv2s2 = 1.0 / (2.0 * sigma^2)
    y0, z0a, z0b = π / 2, π / 2, 3π / 2
    Threads.@threads for k in 1:n
        zk = x[k]
        for j in 1:n, i in 1:n
            yj = x[j]
            g1 = exp(-((yj - y0)^2 + (zk - z0a)^2) * inv2s2)
            g2 = exp(-((yj - 3π/2)^2 + (zk - z0b)^2) * inv2s2)
            w1[i, j, k] = gamma * (g1 * (1 + perturbation * cos(x[i])) -
                                   g2 * (1 + perturbation * cos(x[i])))
        end
    end
    return (w1, w2, w3)
end

"Случайное дивергентно-чистое поле с пиком энергии у k_peak (детерминированное)."
function nsb_ic_random(n::Int; k_peak::Int = 4, seed::Int = NSB_CFG[].seed)
    rng = MersenneTwister(UInt64(seed))
    x = nsb_grid(n)
    u1 = randn(rng, n, n, n); u2 = randn(rng, n, n, n); u3 = randn(rng, n, n, n)
    sk = [sin(k_peak * v) for v in x]; ck = [cos(k_peak * v) for v in x]
    for i in 1:n
        u1[i, :, :] .+= (sk[i] .* ck') .* 0.5
    end
    Threads.@threads for k in 1:n
        for j in 1:n, i in 1:n
            u1[i, j, k] += 0.5 * sk[i] * ck[j]
            u2[i, j, k] += 0.5 * sk[i] * (0.5 * sk[j] + 0.5)
            u3[i, j, k] += 0.5 * ck[k] * sk[j]
        end
    end
    return (u1, u2, u3)
end

"IC → деалиасированное дивергентно-чистое спектральное состояние."
function nsb_prepare_state(ic, s::NsbNSE3D, W::NsbWork3D)
    uhat = nsb_zerofield(s.n)
    nsb_fft_field!(uhat, ic, W, s)
    nsb_project!(uhat, uhat, s, W)
    for c in 1:3
        nsb_maskmul!(uhat[c], s.mask)
    end
    return uhat
end

function nsb_maskmul!(arr, m)
    @inbounds @simd for i in eachindex(arr)
        arr[i] = m[i] ? arr[i] : zero(eltype(arr))
    end
    return arr
end
