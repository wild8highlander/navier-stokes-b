#!/usr/bin/env julia
# =============================================================================
# nsb_extra_research.jl — кросс-языковая проверка дополнительных исследований
# (L11 градиентная статистика + гипердиссипативное КдФ + L17 φ-аудит)
# на Julia 1.10+.
#
# Читает те же данные, что и Python-версия:
#   reference/p5_snapshot_u.f64        — снимок 48³ (t = 6, монография)
#   reference/ck96_state_t6.npz        — состояние 96³ (t = 6, прогон A96)
#   results/extra14_julia_ref.json     — эталон Python (nsb_extra_research.py --run jref)
#   results/extra17_julia_ref.json     — эталон L17 (nsb_extra_research.py --run 17)
# сравнивает величины и записывает отчёты:
#   results/extra14_julia_crosscheck.json
#   results/extra17_julia_crosscheck.json
#
# Запуск:  julia nsb_extra_research.jl [корень_пакета]           — режим L11/L13
#          julia nsb_extra_research.jl phi17 [корень_пакета]     — режим L17
# Зависимости: FFTW.jl, JSON.jl, ZipFile.jl (ставятся автоматически)
# =============================================================================
using Printf, Statistics, LinearAlgebra

const HERE = abspath(dirname(PROGRAM_FILE))
const MODE = length(ARGS) >= 1 && ARGS[1] == "phi17" ? :phi17 : :main
const _argoff = MODE == :phi17 ? 1 : 0
const PKG = length(ARGS) > _argoff ? abspath(ARGS[_argoff + 1]) : dirname(HERE)
const REF = joinpath(PKG, "reference")
const RES = joinpath(PKG, "results")

# --- зависимости -------------------------------------------------------------
for pkg in ("FFTW", "JSON", "ZipFile")
    try
        Base.eval(Main, Meta.parse("using $pkg"))
    catch
        @info "устанавливаю пакет $pkg ..."
        using Pkg
        Pkg.add(pkg)
        Base.eval(Main, Meta.parse("using $pkg"))
    end
end
using FFTW
import JSON
import ZipFile

# --- чтение данных -----------------------------------------------------------
"""Член .npy из несжатого npz-архива → Vector{UInt8} тела данных + dims."""
function read_npy_bytes(npz_path::String, member::String)
    z = ZipFile.Reader(npz_path)
    local bytes = UInt8[]
    found = false
    for f in z.files
        if f.name == member || f.name == member * ".npy"
            bytes = read(f)
            found = true
            break
        end
    end
    close(z)
    found || error("нет члена $member в $npz_path")
    @assert bytes[1:6] == UInt8[0x93, UInt8('N'), UInt8('U'), UInt8('M'),
                                UInt8('P'), UInt8('Y')] "не npy"
    @assert bytes[7] == 0x01 && bytes[8] == 0x00 "не npy v1.0"
    hlen = Int(bytes[9]) + 256 * Int(bytes[10])
    header = String(bytes[11:(10 + hlen)])
    m = match(r"'descr':\s*'([^']+)'", header)
    descr = m.captures[1]
    m = match(r"'fortran_order':\s*(True|False)", header)
    @assert m.captures[1] == "False" "fortran-порядок не поддержан"
    m = match(r"'shape':\s*\(([^)]*)\)", header)
    dims = [parse(Int, s) for s in split(m.captures[1], ",") if
            !isempty(strip(s))]
    body = bytes[(11 + hlen):end]
    return descr, dims, body
end

"""Состояние 96³ из npz: 'uh.npy' (3,96,96,49) complex128 → (3,96,96,49)."""
function load_uh96(npz_path::String)
    descr, dims, body = read_npy_bytes(npz_path, "uh.npy")
    @assert occursin("c16", descr) "ожидался complex128"
    data = reinterpret(ComplexF64, body)
    # numpy C-порядок (c, x, y, zh): последняя ось fastest → Julia (zh, y, x, c)
    V = reshape(data, (dims[4], dims[3], dims[2], dims[1]))
    return permutedims(V, (4, 3, 2, 1))   # (c, x, y, zh)
end

"""Снимок 48³ (3,48,48,48) float64 → (3,48,48,48)."""
function load_u48(path::String)
    raw = read(path)
    @assert length(raw) == 3 * 48 * 48 * 48 * 8 "размер снимка 48³"
    V = reshape(reinterpret(Float64, raw), (48, 48, 48, 3))
    return permutedims(V, (4, 3, 2, 1))   # (c, x, y, z)
end

# --- L11: изотропная градиентная статистика ----------------------------------
"""ζ_i = ∂u_i/∂x_i (полный FFT); моменты, усреднённые по 3 осям."""
function grad_stats_iso(U::Array{Float64,3})
    n = size(U, 2)
    kf = FFTW.fftfreq(n)                  # целые волновые числа (домен 2π)
    acc = Dict(p => 0.0 for p in (2, 3, 4, 6))
    for a in 1:3
        k = a == 1 ? reshape(kf, n, 1, 1) :
            a == 2 ? reshape(kf, 1, n, 1) : reshape(kf, 1, 1, n)
        Uh = FFTW.fft(U[a, :, :, :])
        z = real.(FFTW.ifft((1im .* k) .* Uh))
        for p in keys(acc)
            acc[p] += sum(z .^ p) / length(z)
        end
    end
    v2 = acc[2] / 3; v3 = acc[3] / 3; v4 = acc[4] / 3; v6 = acc[6] / 3
    return Dict("S3" => v3 / v2^1.5, "F4" => v4 / v2^2, "F6" => v6 / v2^3)
end

# --- КдФ: гипердиссипативный случай (IFRK4, 2/3-обезвреживание) --------------
"""u_t + 6uu_x + u_xxx = −ν(−∂²)^b u; возвращает A(T), P(T), M0, MT."""
function kdv_b_case(n::Int, l::Float64, dt::Float64, T::Float64,
                    nu::Float64, b::Float64, c::Float64, x0::Float64)
    k = FFTW.fftfreq(n) .* (2π / l)
    Lin = 1im .* k .^ 3 .- nu .* abs.(k) .^ (2b)
    Eop = exp.(Lin .* dt)
    Eop2 = exp.(Lin .* dt ./ 2)
    mask = abs.(k) .<= (n ÷ 3) * (2π / l)
    x = range(0.0, step = l / n, length = n)
    u0 = (c / 2) .* sech.(sqrt(c) ./ 2 .* (x .- x0)) .^ 2
    uh = FFTW.fft(u0) .* mask
    nl(u) = (-3im .* k) .* FFTW.fft(u .* u) .* mask
    nsteps = round(Int, T / dt)
    u_init = real.(FFTW.ifft(uh))
    M0 = mean(u_init)
    for _ in 1:nsteps
        a = nl(real.(FFTW.ifft(uh)))
        bh = nl(real.(FFTW.ifft(Eop2 .* (uh .+ dt ./ 2 .* a))))
        ch = nl(real.(FFTW.ifft(Eop2 .* uh .+ dt ./ 2 .* bh)))
        dh = nl(real.(FFTW.ifft(Eop .* uh .+ dt .* Eop2 .* ch)))
        uh .= Eop .* uh .+ dt ./ 6 .*
              (Eop .* a .+ 2 .* Eop2 .* (bh .+ ch) .+ dh)
        uh .*= mask
    end
    uf = real.(FFTW.ifft(uh))
    return Dict("A_T" => maximum(abs.(uf)), "P_T" => mean(abs2.(uf)) / 2,
                "M0" => M0, "MT" => mean(uf))
end

# --- сравнение ----------------------------------------------------------------
reldev(a::Float64, b::Float64) = abs(a - b) / max(abs(b), 1e-300)

function main()
    ref = JSON.parsefile(joinpath(RES, "extra14_julia_ref.json"))
    rows = Vector{Dict{String,Any}}()
    function push(lab, test, val, refv, tol, flr::Float64 = 0.0)
        d = abs(val - refv) / max(abs(refv), flr, 1e-300)
        v = d <= tol ? "PASS" : "FAIL"
        push!(rows, Dict("lab" => lab, "test" => test, "julia" => val,
                         "python" => refv, "rel_dev" => d, "tol" => tol,
                         "verdict" => v))
        @printf("  %-20s %-12s julia=%-24.14g python=%-24.14g отн=%-9.2e %s\n",
                lab, test, val, refv, d, v)
    end

    println("NSB EXTRA — кросс-языковая проверка Julia ↔ Python")
    println("=" * "^76")
    # ---- 48³ ---------------------------------------------------------------
    U48 = load_u48(joinpath(REF, "p5_snapshot_u.f64"))
    g48 = grad_stats_iso(U48)
    println("  [48³] снимок монографии загружен")
    for k in ("S3", "F4", "F6")
        push("L11/48³", k, g48[k], ref["grad48"][k], 1e-10)
    end
    # ---- 96³ ---------------------------------------------------------------
    uh96 = load_uh96(joinpath(REF, "ck96_state_t6.npz"))
    E96 = 2 * sum(abs2, uh96) / 96^6
    push("L11/96³", "E96", E96, ref["E96_check"], 1e-12)
    U96r = real.(FFTW.ifft(uh96, (2, 3, 4)))
    g96 = grad_stats_iso(U96r)
    for k in ("S3", "F4", "F6")
        push("L11/96³", k, g96[k], ref["grad96"][k], 1e-10)
    end
    # ---- КдФ b = 5/4 ---------------------------------------------------------
    kc = ref["kdv_case"]
    kd = kdv_b_case(Int(kc["n"]), Float64(kc["l"]), Float64(kc["dt"]),
                    Float64(kc["T"]), Float64(kc["nu"]), Float64(kc["b"]),
                    Float64(kc["c"]), Float64(kc["x0"]))
    push("L13/КдФ", "A_T", kd["A_T"], kc["A_T"], 1e-8)
    push("L13/КдФ", "P_T", kd["P_T"], kc["P_T"], 1e-8)
    push("L13/КдФ", "mass_drift", kd["mass_drift"], kc["mass_drift"], 1e-6)

    npass = count(r -> r["verdict"] == "PASS", rows)
    summary = Dict("program" => "NSB-96-UPGRADE / nsb_extra_research.jl",
                   "julia_version" => string(VERSION),
                   "checks" => rows,
                   "tally" => Dict("PASS" => npass,
                                   "FAIL" => length(rows) - npass))
    out = joinpath(RES, "extra14_julia_crosscheck.json")
    open(out, "w") do fh
        JSON.print(fh, summary, 2)
        println(fh)
    end
    @printf("\n  ИТОГ: PASS=%d FAIL=%d  →  %s\n", npass, length(rows) - npass,
            out)
end

# =============================================================================
# L17: φ-аудит — детерминированное ядро (без RNG и FFT)
# =============================================================================
const PHI = (1.0 + sqrt(5.0)) / 2.0
const DELTA2J = 0.05
const PHI_TABLE2 = ((89, 144, 144, 233), (55, 89, 89, 144), (89, 89, 144, 144),
                    (34, 55, 55, 89), (21, 34, 34, 55), (13, 21, 21, 34),
                    (34, 34, 55, 55), (8, 13, 13, 21), (21, 21, 34, 34),
                    (8, 8, 13, 13))

"""Скорости 4 вихрей двухслойного прямоугольника (как phi_vels в Python)."""
function phi_vels_jl(r1::Float64, r2::Float64, g4::NTuple{4,Float64})
    ga, gb, gc, gd = g4
    m1 = max(r1 * r1, DELTA2J); m2 = max(r2 * r2, DELTA2J)
    mm = max(r1 * r1 + r2 * r2, DELTA2J)
    k1 = 1.0 / (2π * m1); k2 = 1.0 / (2π * m2); km = 1.0 / (2π * mm)
    return ((gc * r2 * k2 + gd * r2 * km, -gb * r1 * k1 - gd * r1 * km),
            (gc * r2 * km + gd * r2 * k2, ga * r1 * k1 + gc * r1 * km))
end

"""Редуцированное условие нулевого дрейфа (теорема L17)."""
function phi_drift_reduced_jl(r1::Float64, r2::Float64, g4::NTuple{4,Float64})
    ga, gb, gc, gd = g4
    m1 = max(r1 * r1, DELTA2J); m2 = max(r2 * r2, DELTA2J)
    mm = max(r1 * r1 + r2 * r2, DELTA2J)
    return (gb * gc - ga * gd) * m2 + (gb * gd - ga * gc) * mm +
           (gd * gd - gc * gc) * m1
end

"""RG-отображение μₙ₊₁ = 1 + 1/μₙ: наклон МНК и асимптотический множитель."""
function phi_rg_jl()
    starts = [0.4 * k for k in 1:12]
    trajs = Vector{Vector{Float64}}()
    for mu0 in starts
        seq = Float64[mu0]
        for _ in 1:60
            mu = 1.0 + 1.0 / seq[end]
            push!(seq, mu)
            abs(mu - PHI) < 1e-15 && break
        end
        push!(trajs, seq)
    end
    xs = Float64[]; ys = Float64[]; ratios = Float64[]
    for seq in trajs
        for n in 1:(length(seq) - 1)
            d0 = abs(seq[n] - PHI); d1 = abs(seq[n + 1] - PHI)
            if 1e-14 < d0 < 1e-3 && d1 > 0
                push!(ratios, d1 / d0)
            end
        end
        for (n, mu) in enumerate(seq)
            d = abs(mu - PHI)
            if 1e-13 < d < 0.1
                push!(xs, Float64(n - 1)); push!(ys, log(d))
            end
        end
    end
    sx = sum(xs); sxx = sum(x -> x * x, xs); sy = sum(ys)
    sxy = sum(xs .* ys)
    det = length(xs) * sxx - sx * sx
    slope = (length(xs) * sxy - sx * sy) / det
    return slope, median(ratios)
end

"""Контрольное C_s (пара 80/120): полный пайплайн приложения B."""
function phi_cs_pair_jl()
    n = 64; box = 3.5; delta = 1.0
    h = 2 * box / n
    idx = [(i + 0.5) * h - box for i in 0:(n - 1)]
    u = zeros(n, n); v = zeros(n, n)
    for (px, py, g) in ((-0.5, 0.0, 80.0), (0.5, 0.1, 120.0))
        for j in 1:n, i in 1:n
            dx = idx[i] - px; dy = idx[j] - py
            r2e = max(dx * dx + dy * dy, DELTA2J)
            c = g / (2π * r2e)
            u[i, j] += -c * dy
            v[i, j] += c * dx
        end
    end
    sigma = delta / sqrt(12.0); sp = sigma / h
    krad = Int(ceil(3.0 * sp))
    ker = [exp(-0.5 * (k / sp)^2) for k in -krad:krad]
    ker ./= sum(ker)
    function f2d(f::Matrix{Float64})
        tmp = zeros(n, n)
        for i in 1:n
            acc = zeros(n)
            for kk in -krad:krad
                ii = i + kk
                if 1 <= ii <= n
                    acc .+= f[ii, :] .* ker[kk + krad + 1]
                end
            end
            tmp[i, :] = acc
        end
        res = zeros(n, n)
        for j in 1:n
            acc = zeros(n)
            for kk in -krad:krad
                jj = j + kk
                if 1 <= jj <= n
                    acc .+= tmp[:, jj] .* ker[kk + krad + 1]
                end
            end
            res[:, j] = acc
        end
        return res
    end
    ut, vt = f2d(u), f2d(v)
    uut, vvt, uvt = f2d(u .* u), f2d(v .* v), f2d(u .* v)
    num = 0.0; den = 0.0
    for j in 2:(n - 1), i in 2:(n - 1)
        dudx = (ut[i + 1, j] - ut[i - 1, j]) / (2h)
        dvdy = (vt[i, j + 1] - vt[i, j - 1]) / (2h)
        dudy = (ut[i, j + 1] - ut[i, j - 1]) / (2h)
        dvdx = (vt[i + 1, j] - vt[i - 1, j]) / (2h)
        sxx = dudx; syy = dvdy; sxy = 0.5 * (dudy + dvdx)
        ns = sqrt(2.0 * (dudx^2 + dvdy^2 + 2.0 * sxy^2))
        ns < 1e-10 && continue
        txx = uut[i, j] - ut[i, j]^2
        tyy = vvt[i, j] - vt[i, j]^2
        txy = uvt[i, j] - ut[i, j] * vt[i, j]
        num += -(txx * sxx + 2.0 * txy * sxy + tyy * syy)
        den += 2.0 * delta * delta * ns^3
    end
    return den > 0 && num > 0 ? num / den : NaN
end

"""Кросс-проверка ядра L17 против эталона Python."""
function phi17_main()
    ref = JSON.parsefile(joinpath(RES, "extra17_julia_ref.json"))
    rows = Vector{Dict{String,Any}}()
    function push(lab, test, val, refv, tol, flr::Float64 = 0.0)
        d = abs(val - refv) / max(abs(refv), flr, 1e-300)
        v = d <= tol ? "PASS" : "FAIL"
        push!(rows, Dict("lab" => lab, "test" => String(test), "julia" => val,
                         "python" => refv, "rel_dev" => d, "tol" => tol,
                         "verdict" => v))
        @printf("  %-12s %-22s julia=%-22.14g python=%-22.14g rel=%-9.2e %s\n",
                lab, String(test), val, refv, d, v)
    end

    println("NSB EXTRA L17 — кросс-языковая проверка Julia ↔ Python (φ-ядро)")
    push("L17/алгебра", "phi", PHI, Float64(ref["phi"]), 1e-15)
    for (i, g) in enumerate(PHI_TABLE2)
        mu = (g[3] + g[4]) / (g[1] + g[2])
        push("L17/спектр", "mu[$i]", mu, Float64(ref["fib_mu"][i]), 1e-12)
    end
    slope, ratio = phi_rg_jl()
    push("L17/RG", "slope", slope, Float64(ref["rg_slope"]), 1e-7)
    push("L17/RG", "ratio", ratio, Float64(ref["rg_ratio"]), 1e-12)
    push("L17/RG", "slope_theory", log(1.0 / PHI^2),
         Float64(ref["rg_slope_theory"]), 1e-15)
    let j = 0
        for g in PHI_TABLE2
            g[1] == g[2] && continue   # a·a·b·b — не в asym-списке
            j += 1
            push("L17/дрейф", "cassini[$j]",
                 Float64(g[2] * g[3] - g[1] * g[4]),
                 Float64(ref["zd_cassini"][j]), 0.5)
        end
    end
    tgrid = (0.3, 0.8, 1.5)
    worst = 0.0
    for g4 in ((55.0, 89.0, 89.0, 144.0), (89.0, 144.0, 144.0, 233.0))
        for t in tgrid, fr in (0.3, 0.8, 1.2, 2.5)
            r1 = 2.0 * t; r2 = fr * r1
            vA, vB = phi_vels_jl(r1, r2, g4)
            direct = vA[2] * vB[1] + vB[2] * vA[1]
            red = phi_drift_reduced_jl(r1, r2, g4)
            expected = -r1 * r2 * red /
                       ((2π)^2 * max(r1^2, DELTA2J) * max(r2^2, DELTA2J) *
                        max(r1^2 + r2^2, DELTA2J))
            denom = abs(vA[2] * vB[1]) + abs(vB[2] * vA[1]) + abs(expected)
            denom > 0 || continue
            worst = max(worst, abs(direct - expected) / denom)
        end
    end
    push("L17/дрейф", "identity_mismatch", worst,
         Float64(ref["zd_identity_mismatch"]), 1e-12, 1.0)   # абсолютное сравнение
    worst_f = 0.0
    for g4 in ((89.0, 89.0, 144.0, 144.0), (34.0, 34.0, 55.0, 55.0))
        for t in tgrid
            r1 = 2.0 * t; r2 = r1 / PHI
            vA, vB = phi_vels_jl(r1, r2, g4)
            s = vB[2] / vB[1]
            fb = vB[2] - s * vB[1]
            fa = vA[2] + s * vA[1]
            worst_f = max(worst_f, max(abs(fb), abs(fa)) / max(1.0, abs(vB[2])))
        end
    end
    push("L17/дрейф", "sym_family", worst_f,
         Float64(ref["zd_sym_family_residual"]), 1e-12, 1.0) # абсолютное сравнение
    let g4 = (55.0, 89.0, 89.0, 144.0), t = 0.8
        r1 = 2.0 * t
        gfun = (x::Float64) -> begin
            vA, vB = phi_vels_jl(r1, x, g4)
            vA[2] + (vB[2] / vB[1]) * vA[1]
        end
        lo = 0.10 * r1; hi = 5.0 * r1; nscan = 4000
        grid = [lo * (hi / lo)^(i / (nscan - 1)) for i in 0:(nscan - 1)]
        vals = [gfun(x) for x in grid]
        roots = 0
        for i in 1:(nscan - 1)
            (isfinite(vals[i]) && isfinite(vals[i + 1]) &&
             vals[i] * vals[i + 1] <= 0) || continue
            x0, x1, y0 = grid[i], grid[i + 1], vals[i]
            ok = true
            for _ in 1:80
                xm = 0.5 * (x0 + x1)
                ym = gfun(xm)
                if !isfinite(ym)
                    ok = false; break
                end
                if y0 * ym <= 0
                    x1 = xm
                else
                    x0, y0 = xm, ym
                end
            end
            ok && (roots += 1)
        end
        push("L17/дрейф", "roots(55-89-89-144)", Float64(roots),
             Float64(ref["zd_scan_case"]["roots"]), 0.5)
    end
    cs2 = phi_cs_pair_jl()
    push("L17/C_s", "cs2_pair", cs2, Float64(ref["cs_pair_cs2"]), 1e-6)

    npass = count(r -> r["verdict"] == "PASS", rows)
    summary = Dict("program" => "NSB-96-UPGRADE / nsb_extra_research.jl (L17)",
                   "julia_version" => string(VERSION),
                   "checks" => rows,
                   "tally" => Dict("PASS" => npass,
                                   "FAIL" => length(rows) - npass))
    out = joinpath(RES, "extra17_julia_crosscheck.json")
    open(out, "w") do fh
        JSON.print(fh, summary, 2)
        println(fh)
    end
    @printf("\n  ИТОГ L17: PASS=%d FAIL=%d  →  %s\n", npass,
            length(rows) - npass, out)
end

# =============================================================================
# ДИСПЕТЧЕР: julia nsb_extra_research.jl [phi17] [корень_пакета]
# =============================================================================
if MODE == :phi17
    phi17_main()
else
    main()
end
