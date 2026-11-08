# 06_fft.jl — собственный radix-2 FFT (Кули–Тьюки, на месте, потокобезопасно).
# Конвенции как в numpy.fft (солвер репозитория): forward без нормировки,
# inverse с множителем 1/n на каждую ось (итого 1/N³ для 3D).

struct NsbFFTPlan
    n::Int
    tw::Vector{ComplexF64}
    bitrev::Vector{Int}
end

function nsb_fft_plan(n::Int)
    (n ≥ 2 && (n & (n - 1)) == 0) || error("FFT: n должно быть степенью двойки, получено $n")
    tw = Vector{ComplexF64}(undef, n ÷ 2)
    for k in 0:(n ÷ 2 - 1)
        tw[k+1] = exp(-2im * π * k / n)
    end
    logn = round(Int, log2(n))
    bitrev = Vector{Int}(undef, n)
    for i in 0:n-1
        r = 0
        x = i
        for _ in 1:logn
            r = (r << 1) | (x & 1)
            x >>= 1
        end
        bitrev[i+1] = r + 1
    end
    return NsbFFTPlan(n, tw, bitrev)
end

@inline function nsb_fft1d!(a::AbstractVector{ComplexF64}, p::NsbFFTPlan,
                            inverse::Bool = false)
    n = p.n
    br = p.bitrev
    @inbounds for i in 1:n
        j = br[i]
        if i < j
            a[i], a[j] = a[j], a[i]
        end
    end
    tw = p.tw
    len = 2
    while len <= n
        half = len >> 1
        step = n ÷ len
        @inbounds for start in 1:len:n
            k = 0
            @inbounds for j in 0:half-1
                w = inverse ? conj(tw[k+1]) : tw[k+1]
                i1 = start + j
                i2 = i1 + half
                u = a[i1]
                v = a[i2] * w
                a[i1] = u + v
                a[i2] = u - v
                k += step
            end
        end
        len <<= 1
    end
    if inverse
        s = 1.0 / n
        @inbounds @simd for i in 1:n
            a[i] *= s
        end
    end
    return a
end

"3D-FFT на месте по всем осям (A: (n,n,n) ComplexF64)."
function nsb_fftn!(A::Array{ComplexF64,3}, p::NsbFFTPlan, inverse::Bool = false)
    n = p.n
    # ось 1 — непрерывные линии
    Threads.@threads for jk in 1:(n*n)
        j = (jk - 1) ÷ n + 1
        k = (jk - 1) % n + 1
        nsb_fft1d!(@view(A[:, j, k]), p, inverse)
    end
    # ось 2
    bufs = [Vector{ComplexF64}(undef, n) for _ in 1:Threads.nthreads()]
    Threads.@threads for k in 1:n
        buf = bufs[Threads.threadid()]
        for i in 1:n
            @inbounds for j in 1:n
                buf[j] = A[i, j, k]
            end
            nsb_fft1d!(buf, p, inverse)
            @inbounds for j in 1:n
                A[i, j, k] = buf[j]
            end
        end
    end
    # ось 3
    Threads.@threads for i in 1:n
        buf = bufs[Threads.threadid()]
        for j in 1:n
            @inbounds for k in 1:n
                buf[k] = A[i, j, k]
            end
            nsb_fft1d!(buf, p, inverse)
            @inbounds for k in 1:n
                A[i, j, k] = buf[k]
            end
        end
    end
    return A
end

"2D-FFT на месте (M: (n,n) ComplexF64)."
function nsb_fft2d!(M::Matrix{ComplexF64}, p::NsbFFTPlan, inverse::Bool = false)
    n = p.n
    Threads.@threads for j in 1:n
        nsb_fft1d!(@view(M[:, j]), p, inverse)
    end
    buf = Vector{ComplexF64}(undef, n)
    for i in 1:n
        @inbounds for j in 1:n
            buf[j] = M[i, j]
        end
        nsb_fft1d!(buf, p, inverse)
        @inbounds for j in 1:n
            M[i, j] = buf[j]
        end
    end
    return M
end

"Самотест FFT: раундтрип и сравнение с наивным ДПФ."
function nsb_fft_selftest(; n::Int = 16, seed::Int = 42)
    rng = MersenneTwister(seed)
    a0 = [ComplexF64(randn(rng), randn(rng)) for _ in 1:n]
    p = nsb_fft_plan(n)
    a = copy(a0)
    nsb_fft1d!(a, p)
    # наивное ДПФ
    ref = [sum(a0[m+1] * exp(-2im * π * m * k / n) for m in 0:n-1) for k in 0:n-1]
    err_fwd = maximum(abs.(a .- ref)) / maximum(abs.(ref))
    nsb_fft1d!(a, p, true)
    err_rt = maximum(abs.(a .- a0))
    # 3D раундтрип
    A0 = randn(rng, ComplexF64, 4, 4, 4)
    p4 = nsb_fft_plan(4)
    A = copy(A0)
    nsb_fftn!(A, p4)
    nsb_fftn!(A, p4, true)
    err_3d = maximum(abs.(A .- A0))
    return (forward = err_fwd, roundtrip = err_rt, roundtrip3d = err_3d)
end
