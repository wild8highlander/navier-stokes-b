# 07_solver3d.jl — псевдоспектральный 3D Навье–Стокс/Эйлер на торе.
# Точное зеркало research_lab/solver.py: RK4 + Лере-проекция на каждом
# подэтапе, 2/3-деалиасинг, форма нелинейности P[curl u × u].

struct NsbNSE3D
    n::Int
    nu::Float64
    plan::NsbFFTPlan
    k1d::Vector{Int}
    ksq::Array{Float64,3}
    kx::Array{Int,3}; ky::Array{Int,3}; kz::Array{Int,3}
    mask::BitArray{3}
    k2safe::Array{Float64,3}
    dx::Float64
end

function NsbNSE3D(n::Int, nu::Real)
    n ≥ 8 && iseven(n) || error("n должно быть чётным ≥ 8")
    plan = nsb_fft_plan(n)
    k1d = vcat(0:(n ÷ 2 - 1), (-n ÷ 2):-1)
    kx = repeat(reshape(k1d, n, 1, 1), 1, n, n)
    ky = repeat(reshape(k1d, 1, n, 1), n, 1, n)
    kz = repeat(reshape(k1d, 1, 1, n), n, n, 1)
    ksq = kx .^ 2 .+ ky .^ 2 .+ kz .^ 2
    kc = n ÷ 3
    mask = (abs.(kx) .<= kc) .& (abs.(ky) .<= kc) .& (abs.(kz) .<= kc)
    k2safe = map(v -> v > 0 ? Float64(v) : 1.0, ksq)
    return NsbNSE3D(n, Float64(nu), plan, k1d, ksq, kx, ky, kz, mask, k2safe,
                    2.0 * π / n)
end

# --------------------------------------------------------------- рабочие буферы
struct NsbWork3D
    u::NTuple{3,Array{Float64,3}}
    w::NTuple{3,Array{Float64,3}}
    wh::NTuple{3,Array{ComplexF64,3}}
    nlhat::NTuple{3,Array{ComplexF64,3}}
    tmp::NTuple{3,Array{ComplexF64,3}}
    kd::Array{ComplexF64,3}
end

function NsbWork3D(n::Int)
    sh = (n, n, n)
    NsbWork3D(
        (zeros(sh), zeros(sh), zeros(sh)),
        (zeros(sh), zeros(sh), zeros(sh)),
        (zeros(ComplexF64, sh), zeros(ComplexF64, sh), zeros(ComplexF64, sh)),
        (zeros(ComplexF64, sh), zeros(ComplexF64, sh), zeros(ComplexF64, sh)),
        (zeros(ComplexF64, sh), zeros(ComplexF64, sh), zeros(ComplexF64, sh)),
        zeros(ComplexF64, sh))
end

@inline _maskmul!(out, inp, m) = (@inbounds @simd for i in eachindex(out)
    out[i] = m[i] ? inp[i] : zero(eltype(out))
end; out)

# --------------------------------------------------------------- трансформы
function nsb_fft_field!(uhat, u, W, s::NsbNSE3D)
    for c in 1:3
        @inbounds @simd for i in eachindex(uhat[c])
            W.tmp[c][i] = ComplexF64(u[c][i], 0.0)
        end
        nsb_fftn!(W.tmp[c], s.plan, false)
        copyto!(uhat[c], W.tmp[c])
    end
    return uhat
end

function nsb_ifft_field!(u, uhat, W, s::NsbNSE3D)
    for c in 1:3
        copyto!(W.tmp[c], uhat[c])
        nsb_fftn!(W.tmp[c], s.plan, true)
        @inbounds @simd for i in eachindex(u[c])
            u[c][i] = real(W.tmp[c][i])
        end
    end
    return u
end

"Лере-проекция на месте (out === in допустимо)."
function nsb_project!(out, in_, s::NsbNSE3D, W::NsbWork3D)
    kd = W.kd
    @inbounds for i in eachindex(kd)
        kd[i] = (s.kx[i] * in_[1][i] + s.ky[i] * in_[2][i] + s.kz[i] * in_[3][i]) /
                s.k2safe[i]
        s.ksq[i] == 0 && (kd[i] = 0.0)
    end
    for c in 1:3
        kc = c == 1 ? s.kx : (c == 2 ? s.ky : s.kz)
        @inbounds @simd for i in eachindex(out[c])
            out[c][i] = in_[c][i] - kc[i] * kd[i]
        end
    end
    return out
end

"curl_hat = i k × u_hat."
function nsb_curl_hat!(out, uhat, s::NsbNSE3D)
    @inbounds for i in eachindex(out[1])
        kx, ky, kz = s.kx[i], s.ky[i], s.kz[i]
        a1, a2, a3 = uhat[1][i], uhat[2][i], uhat[3][i]
        out[1][i] = 1im * (ky * a3 - kz * a2)
        out[2][i] = 1im * (kz * a1 - kx * a3)
        out[3][i] = 1im * (kx * a2 - ky * a1)
    end
    return out
end

"Правая часть: −P[curl u × u] − ν k² u (деалиас)."
function nsb_rhs!(du, uhat, s::NsbNSE3D, W::NsbWork3D)
    nsb_curl_hat!(W.wh, uhat, s)
    nsb_ifft_field!(W.u, uhat, W, s)
    nsb_ifft_field!(W.w, W.wh, W, s)
    # nl = w × u в физическом пространстве
    n = s.n
    for k in 1:n^3
        w1, w2, w3 = W.w[1][k], W.w[2][k], W.w[3][k]
        u1, u2, u3 = W.u[1][k], W.u[2][k], W.u[3][k]
        W.u[1][k] = w2 * u3 - w3 * u2
        W.u[2][k] = w3 * u1 - w1 * u3
        W.u[3][k] = w1 * u2 - w2 * u1
    end
    nsb_fft_field!(W.nlhat, W.u, W, s)
    for c in 1:3
        _maskmul!(W.nlhat[c], W.nlhat[c], s.mask)
    end
    nsb_project!(du, W.nlhat, s, W)
    @inbounds for c in 1:3
        kc = c == 1 ? s.kx : (c == 2 ? s.ky : s.kz)
        @inbounds @simd for i in eachindex(du[c])
            du[c][i] -= s.nu * s.ksq[i] * uhat[c][i]
        end
    end
    return du
end

"Один шаг RK4; возвращает деалиасированное новое состояние (в out)."
function nsb_step_rk4!(out, uhat, dt::Float64, s::NsbNSE3D, W::NsbWork3D,
                       K1, K2, K3, K4, T1, T2)
    nsb_rhs!(K1, uhat, s, W)
    for c in 1:3
        @inbounds @simd for i in eachindex(T1[c])
            T1[c][i] = uhat[c][i] + (0.5 * dt) * K1[c][i]
        end
    end
    nsb_rhs!(K2, T1, s, W)
    for c in 1:3
        @inbounds @simd for i in eachindex(T1[c])
            T1[c][i] = uhat[c][i] + (0.5 * dt) * K2[c][i]
        end
    end
    nsb_rhs!(K3, T1, s, W)
    for c in 1:3
        @inbounds @simd for i in eachindex(T1[c])
            T1[c][i] = uhat[c][i] + dt * K3[c][i]
        end
    end
    nsb_rhs!(K4, T1, s, W)
    for c in 1:3
        @inbounds @simd for i in eachindex(out[c])
            out[c][i] = uhat[c][i] +
                        (dt / 6.0) * (K1[c][i] + 2.0 * K2[c][i] + 2.0 * K3[c][i] + K4[c][i])
            out[c][i] = s.mask[i] ? out[c][i] : zero(ComplexF64)
        end
    end
    return out
end

"Копия поля (кортеж 3 массивов)."
nsb_copyfield(f) = (copy(f[1]), copy(f[2]), copy(f[3]))
nsb_zerofield(n) = (zeros(ComplexF64, n, n, n), zeros(ComplexF64, n, n, n),
                    zeros(ComplexF64, n, n, n))

# --------------------------------------------------------------- b-повороты
"Точечный поворот u'(x) = R u(x): изометрия, ломает несжимаемость."
function nsb_rotate_pointwise!(out, uhat, R, s::NsbNSE3D, W::NsbWork3D)
    nsb_ifft_field!(W.u, uhat, W, s)
    n = s.n
    ru = (zeros(n, n, n), zeros(n, n, n), zeros(n, n, n))
    for k in 1:n^3
        x, y, z = W.u[1][k], W.u[2][k], W.u[3][k]
        ru[1][k] = R[1][1] * x + R[1][2] * y + R[1][3] * z
        ru[2][k] = R[2][1] * x + R[2][2] * y + R[2][3] * z
        ru[3][k] = R[3][1] * x + R[3][2] * y + R[3][3] * z
    end
    nsb_fft_field!(out, ru, W, s)
    return out
end

"Полная симметрия u'(x) = R u(R⁻¹x) — ТОЧНЫЙ четверть-поворот вокруг z
(циркулярный сдвиг индексов, интерполяции нет; решётка переходит в себя)."
function nsb_rotate_full_symmetry!(out, uhat, R, s::NsbNSE3D, W::NsbWork3D)
    n = s.n
    nsb_ifft_field!(W.u, uhat, W, s)
    ru = (zeros(n, n, n), zeros(n, n, n), zeros(n, n, n))
    # R(x,y,z) = (-y, x, z)  =>  R⁻¹(x,y,z) = (y, -x, z)
    # sampled(x_i, y_j, z_k) = u(y_j, -x_i, z_k): индексы (j, mod1(-i), k)
    Threads.@threads for k in 1:n
        for j in 1:n, i in 1:n
            ii = (i == 1) ? 1 : n - i + 2   # mod1(1 - (i-1), n)
            x = W.u[1][j, ii, k]
            y = W.u[2][j, ii, k]
            z = W.u[3][j, ii, k]
            # R(a,b,c) = (-b, a, c)
            ru[1][i, j, k] = -y
            ru[2][i, j, k] = x
            ru[3][i, j, k] = z
        end
    end
    nsb_fft_field!(out, ru, W, s)
    return out
end

"CFL-шаг: 0.5·dx/max|u|."
function nsb_cfl_dt(uhat, s::NsbNSE3D, W::NsbWork3D; safety::Float64 = 0.5)
    nsb_ifft_field!(W.u, uhat, W, s)
    umax = 0.0
    @inbounds for k in eachindex(W.u[1])
        v = sqrt(W.u[1][k]^2 + W.u[2][k]^2 + W.u[3][k]^2)
        v > umax && (umax = v)
    end
    umax < 1e-14 && return safety * s.dx^2 / max(s.nu, 1e-12)
    return safety * s.dx / umax
end

"Поле скорости по завихренности (Био–Савар) — для IC Хоу–Ло."
function nsb_velocity_from_vorticity!(out, what, s::NsbNSE3D, W::NsbWork3D)
    @inbounds for i in eachindex(out[1])
        kx, ky, kz = s.kx[i], s.ky[i], s.kz[i]
        w1, w2, w3 = what[1][i], what[2][i], what[3][i]
        if s.ksq[i] == 0
            out[1][i] = 0.0im; out[2][i] = 0.0im; out[3][i] = 0.0im
        else
            inv2 = 1im / s.ksq[i]
            out[1][i] = inv2 * (ky * w3 - kz * w2)
            out[2][i] = inv2 * (kz * w1 - kx * w3)
            out[3][i] = inv2 * (kx * w2 - ky * w1)
        end
    end
    nsb_project!(out, out, s, W)
    for c in 1:3
        _maskmul!(out[c], out[c], s.mask)
    end
    return out
end
