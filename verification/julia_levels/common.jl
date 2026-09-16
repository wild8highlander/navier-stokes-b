# common.jl — общие утилиты: JSON-писатель, radix-2 FFT с самотестом, RK4

using LinearAlgebra
using Random

# ------------------------- минимальный JSON-писатель -------------------------

json_escape(s::AbstractString) = replace(s, "\\" => "\\\\", "\"" => "\\\"",
    "\n" => "\\n", "\t" => "\\t", "\r" => "\\r")

json(x::AbstractString) = "\"" * json_escape(x) * "\""
json(x::Union{Bool,Nothing}) = x === nothing ? "null" : (x ? "true" : "false")
json(x::Integer) = string(x)
json(x::AbstractFloat) = isfinite(x) ? string(round(x; digits = 15)) : "null"
json(x::BigFloat) = "\"" * string(x) * "\""
json(v::Vector) = "[" * join(json.(v), ",") * "]"
json(d::Dict) = "{" * join(["$(json(string(k))):$(json(v))" for (k, v) in d], ",") * "}"
json(p::Pair) = json(Dict(p))

function write_json(path::AbstractString, d::Dict)
    open(path, "w") do io
        write(io, json(d))
    end
end

# ------------------------- собственный radix-2 FFT -------------------------

"""
    fft!(a, inverse=false) — итеративный radix-2 Кули–Тьюки на месте, по последней оси.
a — комплексный массив (…, n), n — степень двойки.
"""
function fft1d!(a::AbstractVector{ComplexF64}, inverse::Bool)
    n = length(a)
    (n & (n - 1)) == 0 || error("radix-2: длина должна быть степенью двойки")
    # bit-reversal permutation
    j = 1
    for i in 1:n-1
        if i < j
            a[i], a[j] = a[j], a[i]
        end
        m = n >> 1
        while m >= 1 && j > m
            j -= m
            m >>= 1
        end
        j += m
    end
    len = 2
    while len <= n
        ang = (inverse ? 2 : -2) * pi / len
        wl = ComplexF64(cos(ang), sin(ang))
        half = len >> 1
        i = 1
        while i <= n
            w = ComplexF64(1.0, 0.0)
            for k in 1:half
                u = a[i + k - 1]
                v = a[i + k - 1 + half] * w
                a[i + k - 1] = u + v
                a[i + k - 1 + half] = u - v
                w *= wl
            end
            i += len
        end
        len <<= 1
    end
    if inverse
        a ./= n
    end
    return a
end

"""
    myfft(a; inverse=false) — FFT по последней оси для массива (…, n).
"""
function myfft(a::AbstractArray{ComplexF64}; inverse::Bool = false)
    b = copy(a)
    n = size(b, ndims(b))
    tails = CartesianIndices(size(b)[1:end-1])
    buf = Vector{ComplexF64}(undef, n)
    for idx in tails
        for k in 1:n
            buf[k] = b[CartesianIndex(idx, k)]
        end
        fft1d!(buf, inverse)
        for k in 1:n
            b[CartesianIndex(idx, k)] = buf[k]
        end
    end
    return b
end

"""Самотест: FFT против прямого DFT O(n²) на случайных данных; возвращает макс. невязку."""
function fft_selftest(n::Int = 64)
    Random.seed!(1234)
    a = ComplexF64.(randn(n), randn(n))
    f = myfft(reshape(a, n, 1))[:, 1]
    dft = [sum(a[m] * exp(-2im * pi * (m - 1) * (k - 1) / n)) for k in 1:n, m in 1:n][:, 1]
    err_fwd = maximum(abs.(f .- dft))
    back = myfft(reshape(f, n, 1); inverse = true)[:, 1]
    err_inv = maximum(abs.(back .- a))
    return max(err_fwd, err_inv)
end

# ------------------------- RK4 -------------------------

function rk4_step(f, y, dt)
    k1 = f(y)
    k2 = f(y .+ 0.5 * dt .* k1)
    k3 = f(y .+ 0.5 * dt .* k2)
    k4 = f(y .+ dt .* k3)
    return y .+ (dt / 6) .* (k1 .+ 2k2 .+ 2k3 .+ k4)
end

const B = 1 / (4 * pi + 2 * sqrt(3))
const THETA = asin(B)
