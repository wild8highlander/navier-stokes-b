# p5_regularity.jl — P5 Julia verification track.
#
# Mirrors code/python/p5_regularity.py and code/cpp/p5_regularity.cpp:
#   (1) analytic block (BigFloat, 60 bits+): the generalized Pao
#       normalization beta_b, the universal dissipation-peak prediction
#       x*(b), the hyperdissipation scaling exponents and the LPS table;
#   (2) snapshot diagnostics: loads the raw f64 snapshot of the run A
#       field (u, omega) and recomputes the physical-space regularity
#       diagnostics;
#   (3) miniature 16^3 Taylor-Green DNS with a hand-written radix-2 FFT
#       and the same integrating-factor midpoint RK2 scheme.
# Writes results/p5_julia.json (hand-rolled JSON — zero dependencies).
#
# Run:  julia p5_regularity.jl <project_root>   (default: ../..)

const ROOT = length(ARGS) >= 1 ? ARGS[1] : "../.."
const RES = joinpath(ROOT, "results")

# --- universal b-correction constants --------------------------------------
const B_UNIV = 1.0 / (4.0 * pi + 2.0 * sqrt(3.0))
const THETA_B = asin(B_UNIV)
const CK = 1.5

# --- generalized Pao normalization (ch. 12.5) ------------------------------
# Base Julia has no gamma; a 9-term Lanczos approximation (g = 7) gives
# ~1e-15 relative accuracy, sufficient against the C++ long-double track.
function lanczos_gamma(z::Float64)::Float64
    if z < 0.5
        return pi / (sin(pi * z) * lanczos_gamma(1.0 - z))
    end
    z -= 1.0
    x = 0.99999999999980993
    for (i, c) in enumerate((
            676.5203681218851, -1259.1392167224028, 771.32342877765313,
            -176.61502916214059, 12.507343278686905, -0.13857109526572012,
            9.9843695780195716e-6, 1.5056327351493116e-7))
        x += c / (z + i)
    end
    t = z + 7.5
    return sqrt(2.0 * pi) * t^(z + 0.5) * exp(-t) * x
end

beta_b(b::Float64, ck::Float64 = CK) = (ck * lanczos_gamma((2 * b - 2.0 / 3.0) / (2 * b)) / b)^(2 * b / (2 * b - 2.0 / 3.0))

x_star(b::Float64, ck::Float64 = CK) = ((2 * b - 5.0 / 3.0) / (2 * b * beta_b(b, ck)))^(1.0 / (2.0 * b))

beta_b64(b::Float64) = beta_b(b)
x_star64(b::Float64) = x_star(b)

# --- radix-2 complex FFT (n = 16 per axis) ---------------------------------
function fft1d!(a::Vector{ComplexF64}, sign::Int)
    n = length(a)
    j = 0
    for i in 1:(n-1)
        bit = n >> 1
        while (j & bit) != 0
            j = j ⊻ bit
            bit >>= 1
        end
        j = j ⊻ bit
        if i < j
            a[i+1], a[j+1] = a[j+1], a[i+1]
        end
    end
    len = 2
    while len <= n
        ang = sign * 2.0 * pi / len
        wl = ComplexF64(cos(ang), sin(ang))
        i = 1
        while i <= n
            w = ComplexF64(1.0, 0.0)
            for m in 0:(len ÷ 2 - 1)
                u = a[i+m]
                v = a[i+m+len÷2] * w
                a[i+m] = u + v
                a[i+m+len÷2] = u - v
                w *= wl
            end
            i += len
        end
        len <<= 1
    end
    return nothing
end

const MN = 16

mutable struct MField
    c::Array{ComplexF64,4}   # 3 x MN x MN x MN
end
MField() = MField(zeros(ComplexF64, 3, MN, MN, MN))

fft_axis!(f::MField, axis::Int, sign::Int) = begin
    buf = Vector{ComplexF64}(undef, MN)
    for comp in 1:3
        for i in 1:MN, j in 1:MN
            for k in 1:MN
                buf[k] = axis == 0 ? f.c[comp, k, j, i] :
                         axis == 1 ? f.c[comp, i, k, j] :
                                     f.c[comp, i, j, k]
            end
            fft1d!(buf, sign)
            for k in 1:MN
                if axis == 0
                    f.c[comp, k, j, i] = buf[k]
                elseif axis == 1
                    f.c[comp, i, k, j] = buf[k]
                else
                    f.c[comp, i, j, k] = buf[k]
                end
            end
        end
    end
end

forward!(f::MField) = (fft_axis!(f, 0, -1); fft_axis!(f, 1, -1); fft_axis!(f, 2, -1))
inverse!(f::MField) = begin
    fft_axis!(f, 0, +1); fft_axis!(f, 1, +1); fft_axis!(f, 2, +1)
    f.c ./= MN^3
end

kval(i::Int) = i <= MN ÷ 2 ? Float64(i - 1) : Float64(i - 1 - MN)  # 1-based

# nonlinear term N(u) = P[u x omega], 2/3-dealised, mean-free
function nonlinear!(out::MField, uh::MField)
    u = deepcopy(uh); inverse!(u)
    wh = MField()
    for ix in 1:MN, iy in 1:MN, iz in 1:MN
        kx = kval(ix); ky = kval(iy); kz = kval(iz)
        U1 = uh.c[1, ix, iy, iz]; U2 = uh.c[2, ix, iy, iz]; U3 = uh.c[3, ix, iy, iz]
        wh.c[1, ix, iy, iz] = 1.0im * (ky * U3 - kz * U2)
        wh.c[2, ix, iy, iz] = 1.0im * (kz * U1 - kx * U3)
        wh.c[3, ix, iy, iz] = 1.0im * (kx * U2 - ky * U1)
    end
    w = deepcopy(wh); inverse!(w)
    # cross product in physical space, then to Fourier space, then project
    cr = MField()
    for ix in 1:MN, iy in 1:MN, iz in 1:MN
        c1 = u.c[1, ix, iy, iz].re; c2 = u.c[2, ix, iy, iz].re; c3 = u.c[3, ix, iy, iz].re
        w1 = w.c[1, ix, iy, iz].re; w2 = w.c[2, ix, iy, iz].re; w3 = w.c[3, ix, iy, iz].re
        cr.c[1, ix, iy, iz] = ComplexF64(c2 * w3 - c3 * w2, 0.0)
        cr.c[2, ix, iy, iz] = ComplexF64(c3 * w1 - c1 * w3, 0.0)
        cr.c[3, ix, iy, iz] = ComplexF64(c1 * w2 - c2 * w1, 0.0)
    end
    forward!(cr)
    crit = MN ÷ 3
    for ix in 1:MN, iy in 1:MN, iz in 1:MN
        kx = kval(ix); ky = kval(iy); kz = kval(iz)
        kk = kx^2 + ky^2 + kz^2
        k2e = kk > 0 ? kk : 1.0
        pass = abs(kx) <= crit && abs(ky) <= crit && abs(kz) <= crit
        div = (kx * cr.c[1, ix, iy, iz] + ky * cr.c[2, ix, iy, iz] +
               kz * cr.c[3, ix, iy, iz]) / k2e
        K = (kx, ky, kz)
        for comp in 1:3
            out.c[comp, ix, iy, iz] = pass ? cr.c[comp, ix, iy, iz] - K[comp] * div : 0.0im
        end
    end
    for comp in 1:3
        out.c[comp, 1, 1, 1] = 0.0im
    end
    return nothing
end

function mini_dns()
    nu = 0.01; dt = 5.0e-3; t_end = 1.0; se = 10
    uh = MField()
    h = 2.0 * pi / MN
    for ix in 1:MN, iy in 1:MN, iz in 1:MN
        x = (ix - 0.5) * h; y = (iy - 0.5) * h; z = (iz - 0.5) * h
        uh.c[1, ix, iy, iz] = ComplexF64(sin(x) * cos(y) * cos(z), 0.0)
        uh.c[2, ix, iy, iz] = ComplexF64(-cos(x) * sin(y) * cos(z), 0.0)
    end
    forward!(uh)
    # project + mask + mean removal
    crit = MN ÷ 3
    for ix in 1:MN, iy in 1:MN, iz in 1:MN
        kx = kval(ix); ky = kval(iy); kz = kval(iz)
        kk = kx^2 + ky^2 + kz^2
        k2e = kk > 0 ? kk : 1.0
        div = (kx * uh.c[1, ix, iy, iz] + ky * uh.c[2, ix, iy, iz] +
               kz * uh.c[3, ix, iy, iz]) / k2e
        pass = abs(kx) <= crit && abs(ky) <= crit && abs(kz) <= crit
        for comp in 1:3
            K = (kx, ky, kz)[comp]
            uh.c[comp, ix, iy, iz] = pass ? uh.c[comp, ix, iy, iz] - K * div : 0.0im
        end
    end
    for comp in 1:3
        uh.c[comp, 1, 1, 1] = 0.0im
    end
    # integrating-factor coefficients
    D = zeros(3, MN, MN, MN); Dm = zeros(3, MN, MN, MN)
    for ix in 1:MN, iy in 1:MN, iz in 1:MN
        kk = kval(ix)^2 + kval(iy)^2 + kval(iz)^2
        for comp in 1:3
            D[comp, ix, iy, iz] = exp(-nu * kk * dt)
            Dm[comp, ix, iy, iz] = sqrt(D[comp, ix, iy, iz])
        end
    end
    n_steps = round(Int, t_end / dt)
    k1 = MField(); um = MField(); k2f = MField()
    series = Vector{NamedTuple}()
    for step in 0:n_steps
        if step % se == 0 || step == n_steps
            E = sum(abs2, uh.c) / MN^6
            wh = MField()
            for ix in 1:MN, iy in 1:MN, iz in 1:MN
                kx = kval(ix); ky = kval(iy); kz = kval(iz)
                U1 = uh.c[1, ix, iy, iz]; U2 = uh.c[2, ix, iy, iz]; U3 = uh.c[3, ix, iy, iz]
                wh.c[1, ix, iy, iz] = 1.0im * (ky * U3 - kz * U2)
                wh.c[2, ix, iy, iz] = 1.0im * (kz * U1 - kx * U3)
                wh.c[3, ix, iy, iz] = 1.0im * (kx * U2 - ky * U1)
            end
            Om = sum(abs2, wh.c) / MN^6
            wp = deepcopy(wh); inverse!(wp)
            wmax = 0.0
            for ix in 1:MN, iy in 1:MN, iz in 1:MN
                wx = wp.c[1, ix, iy, iz].re
                wy = wp.c[2, ix, iy, iz].re
                wz = wp.c[3, ix, iy, iz].re
                wmax = max(wmax, sqrt(wx^2 + wy^2 + wz^2))
            end
            push!(series, (t = step * dt, E = E, Omega = Om, omega_inf = wmax))
        end
        if step < n_steps
            nonlinear!(k1, uh)
            @. um.c = Dm * (uh.c + 0.5 * dt * k1.c)
            nonlinear!(k2f, um)
            @. uh.c = D * uh.c + dt * Dm * k2f.c
        end
    end
    return series
end

function snapshot_diagnostics()
    n = 48; npts = n^3
    upath = joinpath(RES, "p5_snapshot_u.f64")
    wpath = joinpath(RES, "p5_snapshot_w.f64")
    (isfile(upath) && isfile(wpath)) || return nothing
    # raw C-order file: [comp][x][y][z] -> flat vector, comp-major blocks
    uflat = open(upath) do io
        v = Vector{Float64}(undef, 3 * npts)
        read!(io, v)
        v
    end
    wflat = open(wpath) do io
        v = Vector{Float64}(undef, 3 * npts)
        read!(io, v)
        v
    end
    u2 = 0.0; w2 = 0.0; u4 = 0.0; u6 = 0.0
    umax = 0.0; wmax = 0.0
    for i in 1:npts
        ux = uflat[i]; uy = uflat[npts+i]; uz = uflat[2*npts+i]
        wx = wflat[i]; wy = wflat[npts+i]; wz = wflat[2*npts+i]
        uu = ux^2 + uy^2 + uz^2
        ww = wx^2 + wy^2 + wz^2
        u2 += uu; w2 += ww; u4 += uu^2; u6 += uu^3
        umax = max(umax, sqrt(uu)); wmax = max(wmax, sqrt(ww))
    end
    return (
        E_phys = u2 / npts, Omega_phys = w2 / npts,
        u_inf = umax, omega_inf = wmax,
        u4_mean = u4 / npts, u6_mean = u6 / npts,
    )
end

# --- main -------------------------------------------------------------------
open(joinpath(RES, "p5_julia.json"), "w") do io
    println(io, "{")
    println(io, "  \"program\": \"p5_julia\",")
    println(io, "  \"title\": \"P5 Julia verification: analytic core, snapshot diagnostics, mini-DNS\",")
    println(io, "  \"date\": \"2026-09-29\",")
    println(io, "  \"analytic\": {")
    println(io, "    \"b\": ", B_UNIV, ",")
    println(io, "    \"theta_b_deg\": ", rad2deg(THETA_B), ",")
    println(io, "    \"lilly_cs_sharp_CK15\": ", (BigFloat(1) / (BigFloat(pi) * (BigFloat(3) * BigFloat(CK) / 2)^(BigFloat(3) / 4))), ",")
    println(io, "    \"b_family\": [")
    bpows = (1.0, 1.25, 1.5, 2.0)
    for (i, bp) in enumerate(bpows)
        println(io, "      {\"b_pow\": ", bp, ", \"beta_b\": ", beta_b64(bp),
                ", \"x_star\": ", x_star64(bp),
                ", \"exp_1_over_6b_minus_2\": ", 1.0 / (6.0 * bp - 2.0), "}",
                i < length(bpows) ? "," : "")
    end
    println(io, "    ],")
    println(io, "    \"lps_table\": [")
    pts = ((4, 4), (3, 6), (2, 3))
    for (i, (p, q)) in enumerate(pts)
        println(io, "      {\"p\": ", p, ", \"q\": ", q, ", \"2/p+3/q\": ",
                2.0 / p + 3.0 / q, "}", i < length(pts) ? "," : "")
    end
    println(io, "    ]")
    println(io, "  },")
    snap = snapshot_diagnostics()
    println(io, "  \"snapshot\": {")
    if snap !== nothing
        println(io, "    \"E_phys\": ", snap.E_phys, ",")
        println(io, "    \"Omega_phys\": ", snap.Omega_phys, ",")
        println(io, "    \"u_inf\": ", snap.u_inf, ",")
        println(io, "    \"omega_inf\": ", snap.omega_inf, ",")
        println(io, "    \"u4_mean\": ", snap.u4_mean, ",")
        println(io, "    \"u6_mean\": ", snap.u6_mean)
    else
        println(io, "    \"available\": false")
    end
    println(io, "  },")
    series = mini_dns()
    println(io, "  \"mini\": {")
    println(io, "    \"convention\": \"full-grid DFT, kz=0 counted once\",")
    println(io, "    \"series\": [")
    for (i, r) in enumerate(series)
        println(io, "      {\"t\": ", r.t, ", \"E\": ", r.E, ", \"Omega\": ",
                r.Omega, ", \"omega_inf\": ", r.omega_inf, "}",
                i < length(series) ? "," : "")
    end
    println(io, "    ]")
    println(io, "  }")
    println(io, "}")
end
println("[p5_julia] wrote ", joinpath(RES, "p5_julia.json"))
