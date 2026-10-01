#!/usr/bin/env julia
# ============================================================================
#  NSB LAB 96 — Julia edition
#  Интерактивная лаборатория программы b-коррекции (navier-stokes-b)
#  Interactive laboratory for the b-correction program — ONE FILE, Julia 1.10+
#
#  Запуск / run:
#    julia nsb_lab.jl                     # интерактивное меню
#    julia nsb_lab.jl --lang en           # English UI
#    julia nsb_lab.jl --run main96        # главный тест P5 на 96^3
#    julia nsb_lab.jl --run all           # все лаборатории
#    julia nsb_lab.jl --run matrix --yes  # матрицы 112x112, без меню
#
#  Зависимости / deps: FFTW.jl (авто-установка при первом запуске).
#  Всё остальное — стандартная библиотека Julia (LinearAlgebra, Serialization,
#  Printf, Random, Dates). Отчёты: JSON / TXT / CSV. Логи: logs/.
#
#  Лаборатории / labs:
#   L1 matrix    — операторы программы на матрицах 112x112 + FFT 112^3
#   L2 kdv       — улучшенный KdV-комплекс (IFRK4, механизм b, инварианты)
#   L3 smoke     — смоук-тест решателя 48^3
#   L4 main96    — ГЛАВНЫЙ ТЕСТ: протокол P5 на 96^3 (чекпоинты)
#   L5 dns112    — DNS 112^3
#   L6 bfamily   — гипердиссипативное семейство b на 96^3
#   L7 bprotocol — b-протокол на 96^3 (прогон B)
#   L8 match     — матч Победа/Ничья/Поражение
#   L10 report   — сводный отчёт
#  Графики 600 dpi строит tools/nsb_lab.py --run figures (см. README).
#
#  (c) 2026 — пакет NSB-96-UPGRADE для wild8highlander/navier-stokes-b
# ============================================================================
using LinearAlgebra
using Printf
using Random
using Serialization
using Dates
using Statistics

const B_UNIV = 1.0 / (4.0 * pi + 2.0 * sqrt(3.0))
const THETA_B = asin(B_UNIV)

# ---------------------------------------------------------------------------
# FFTW: единственная внешняя зависимость — авто-установка при старте
# ---------------------------------------------------------------------------
function _ensure_fftw()
    try
        Base.eval(Main, :(import FFTW))
        return getfield(Main, :FFTW)
    catch
        @info "FFTW.jl не найден — устанавливаю (однократно)..."
        Base.eval(Main, :(import Pkg))
        Base.eval(Main, :(Pkg.add(String["FFTW"])))
        Base.eval(Main, :(import FFTW))
        return getfield(Main, :FFTW)
    end
end
const FFTW = _ensure_fftw()

# ---------------------------------------------------------------------------
# I18N
# ---------------------------------------------------------------------------
const I18N = Dict{String,Dict{String,String}}(
    "ru" => Dict{String,String}(
        "title" => "NSB LAB 96 — ЛАБОРАТОРИЯ ПРОГРАММЫ b-КОРРЕКЦИИ (Julia)",
        "menu_hdr" => "ГЛАВНОЕ МЕНЮ — ВЫБЕРИТЕ ЛАБОРАТОРИЮ",
        "lab1" => "L1  Матрицы 112×112 (ортогональность, Лерай, FFT 112³)",
        "lab2" => "L2  Улучшенный KdV-комплекс (IFRK4, инварианты)",
        "lab3" => "L3  Смоук-тест решателя 48³ (T = 0.2)",
        "lab4" => "L4  ГЛАВНЫЙ ТЕСТ: P5 на 96³ (T = 6, чекпоинты)",
        "lab5" => "L5  DNS на больших матрицах 112³",
        "lab6" => "L6  Гипердиссипативное семейство b на 96³",
        "lab7" => "L7  b-протокол на 96³ (прогон B, поворот θ_b)",
        "lab8" => "L8  Матч Победа / Ничья / Поражение",
        "lab10" => "L10 Сводный отчёт (JSON/TXT/CSV)",
        "lab_all" => "A   ЗАПУСТИТЬ ВСЁ (L1→L10)",
        "lab_quit" => "Q   Выход",
        "choose" => "Ваш выбор: ",
        "back" => "Enter — в меню",
        "eta" => "осталось", "resume" => "чекпоинт: продолжаю с шага",
        "fresh" => "чистый старт", "win" => "ПОБЕДА", "draw" => "НИЧЬЯ",
        "loss" => "ПОРАЖЕНИЕ", "score" => "ТАБЛО",
    ),
    "en" => Dict{String,String}(
        "title" => "NSB LAB 96 — b-CORRECTION PROGRAM LABORATORY (Julia)",
        "menu_hdr" => "MAIN MENU — CHOOSE A LABORATORY",
        "lab1" => "L1  112×112 matrix checks (orthogonality, Leray, FFT 112³)",
        "lab2" => "L2  Improved KdV suite (IFRK4, invariants)",
        "lab3" => "L3  48³ solver smoke test (T = 0.2)",
        "lab4" => "L4  MAIN TEST: P5 on 96³ (T = 6, checkpoints)",
        "lab5" => "L5  Large-matrix DNS at 112³",
        "lab6" => "L6  Hyperdissipative b-family on 96³",
        "lab7" => "L7  b-protocol on 96³ (run B, θ_b rotation)",
        "lab8" => "L8  Win / Draw / Loss match",
        "lab10" => "L10 Aggregate report (JSON/TXT/CSV)",
        "lab_all" => "A   RUN EVERYTHING (L1→L10)",
        "lab_quit" => "Q   Quit",
        "choose" => "Your choice: ",
        "back" => "Enter — menu",
        "eta" => "ETA", "resume" => "checkpoint: resuming from step",
        "fresh" => "fresh start", "win" => "WIN", "draw" => "DRAW",
        "loss" => "LOSS", "score" => "SCOREBOARD",
    ),
)

# ANSI-арт
const ART = r"""
   ███╗   ██╗███████╗██████╗     ██╗      █████╗ ██████╗  ██████╗  ██████╗
   ████╗  ██║██╔════╝██╔══██╗    ██║     ██╔══██╗██╔══██╗██╔════╝ ██╔═══██╗
   ██╔██╗ ██║█████╗  ██████╔╝    ██║     ███████║██████╔╝██║  ███╗██║   ██║
   ██║╚██╗██║██╔══╝  ██╔══██╗    ██║     ██╔══██║██╔══██╗██║   ██║██║   ██║
   ██║ ╚████║███████╗██████╔╝    ███████╗██║  ██║██████╔╝╚██████╔╝╚██████╔╝
   ╚═╝  ╚═══╝╚══════╝╚═════╝     ╚══════╝╚═╝  ╚═╝╚═════╝  ╚═════╝  ╚═════╝"""

const COL_C = "\033[1;36m"; const COL_G = "\033[1;32m"
const COL_Y = "\033[1;33m"; const COL_R = "\033[1;31m"
const COL_M = "\033[1;35m"; const COL_D = "\033[2m"; const COL_0 = "\033[0m"

function banner(lang::String)
    t = I18N[lang]
    println(COL_C * ART * COL_0)
    println(COL_Y * "="^78 * COL_0)
    println(COL_C * center(t["title"], 78) * COL_0)
    bstr = @sprintf("b = 1/(4π+2√3) = %.9f   θ_b = %.6f°", B_UNIV, rad2deg(THETA_B))
    println(COL_M * center(bstr, 78) * COL_0)
    println(COL_Y * "="^78 * COL_0)
end

center(s::String, w::Int) = begin
    n = length(s)
    pad = max(w - n, 0)
    l = pad ÷ 2
    " "^l * s * " "^(pad - l)
end

# ---------------------------------------------------------------------------
# Простейший JSON-сериализатор (без внешних зависимостей)
# ---------------------------------------------------------------------------
json_escape(s::String) = replace(replace(replace(s, "\\" => "\\\\"),
                                          "\"" => "\\\""), "\n" => "\\n")

function json_dump(io::IO, x; indent::Int = 0)
    pad = " "^indent
    if x isa Dict
        println(io, "{")
        ks = collect(keys(x))
        for (i, k) in enumerate(ks)
            print(io, pad * "  " * "\"" * json_escape(string(k)) * "\": ")
            json_dump(io, x[k]; indent = indent + 2)
            i < length(ks) && println(io, ",")
        end
        println(io)
        print(io, pad * "}")
    elseif x isa AbstractVector && !isempty(x) && !(x[1] isa Dict) &&
           !(x[1] isa AbstractVector)
        # компактные числовые векторы
        print(io, "[")
        for (i, v) in enumerate(x)
            i > 1 && print(io, ", ")
            json_dump(io, v; indent = indent)
        end
        print(io, "]")
    elseif x isa AbstractVector
        println(io, "[")
        for (i, v) in enumerate(x)
            print(io, pad * "  ")
            json_dump(io, v; indent = indent + 2)
            i < length(x) && println(io, ",")
        end
        println(io)
        print(io, pad * "]")
    elseif x isa AbstractFloat
        isnan(x) ? print(io, "null") : @printf(io, "%.12g", x)
    elseif x isa Integer
        print(io, x)
    elseif x isa Bool
        print(io, x ? "true" : "false")
    elseif x isa Nothing
        print(io, "null")
    else
        print(io, "\"" * json_escape(string(x)) * "\"")
    end
end

function save_json(path::String, x)
    open(path, "w") do io
        json_dump(io, x)
        println(io)
    end
end

# ---------------------------------------------------------------------------
# Однострочный прогресс-бар
# ---------------------------------------------------------------------------
function progress!(frac::Float64, label::String; width::Int = 36)
    frac = clamp(frac, 0.0, 1.0)
    filled = round(Int, frac * width)
    blocks = "█"^filled * "░"^(width - filled)
    line = @sprintf("|%s| %5.1f%%  %s", blocks, frac * 100, label)
    print("\r", length(line) > 110 ? line[1:110] : line, " "^4)
    frac >= 1.0 ? println() : flush(stdout)
end

fmt_sec(s::Int) = begin
    h, rem = divrem(s, 3600)
    m, sec = divrem(rem, 60)
    h > 0 ? @sprintf("%d:%02d:%02d", h, m, sec) : @sprintf("%d:%02d", m, sec)
end

# ---------------------------------------------------------------------------
# Конфигурация (настраиваемые параметры прогонов)
# ---------------------------------------------------------------------------
function default_cfg()
    Dict{String,Any}(
        "lang" => "ru", "n_main" => 96, "n_matrix" => 112, "n_smoke" => 48,
        "nu" => 0.01, "dt" => 0.002, "t_end_main" => 6.0, "t_end_112" => 1.0,
        "t_end_smoke" => 0.2, "save_every" => 10, "stat_t0" => 2.0,
        "b_powers" => [1.25, 1.5, 2.0], "seed" => 20260930,
        "budget_s" => 600.0,
        "thr_divfree" => [1e-10, 1e-8],
        "thr_energy_balance" => [0.01, 0.05],
        "thr_enstrophy_balance" => [0.02, 0.10],
        "thr_conv_headline" => [0.02, 0.05],
        "thr_matrix_orth" => [1e-13, 1e-10],
        "thr_kdv_invariants" => [1e-6, 1e-4],
        "kdv_n" => 512, "kdv_l" => 100.0, "kdv_dt" => 0.0005,
        "kdv_t_end" => 20.0, "kdv_c1" => 4.0, "kdv_c2" => 1.0,
        "kdv_x0_1" => 30.0, "kdv_x0_2" => 60.0, "kdv_collision_t" => 14.0,
        "match_t" => 1.0, "match_n_under" => 32,
    )
end

const PKG_ROOT = normpath(dirname(@__FILE__), "..")
const OUT_RESULTS = joinpath(PKG_ROOT, "results")
const OUT_REPORTS = joinpath(PKG_ROOT, "reports")
const OUT_LOGS = joinpath(PKG_ROOT, "logs")
for d in (OUT_RESULTS, OUT_REPORTS, OUT_LOGS)
    isdir(d) || mkpath(d)
end

LOG_IO = Ref{Union{IOStream,Nothing}}(nothing)

function logline(msg::String)
    if LOG_IO[] !== nothing
        println(LOG_IO[], "[", Dates.format(Dates.now(), "yyyy-mm-dd HH:MM:SS"),
                "] ", msg)
        flush(LOG_IO[])
    end
end

function say(msg::String = "")
    println(msg)
    logline(replace(msg, COL_C => "", COL_G => "", COL_Y => "", COL_R => "",
                    COL_M => "", COL_D => "", COL_0 => ""))
end

# ============================================================================
# ЯДРО: псевдоспектральный решатель семейства гипердиссипативных НСЭ
# (совместим с research_col_smar/code/python/p5_regularity.py и nsb_lab.py)
# Julia-компоновка (отличие от NumPy!): rfft укорачивает ПЕРВУЮ ось,
# поэтому: u :: (3,n,n,n); uh :: (3,nh,n,n), nh = n÷2+1;
# к-векторы :: (nh,n,n): x-ось — укороченная.
# ============================================================================
function wavevectors(n::Int)
    kf = FFTW.fftfreq(n) .* n            # безразмерные k (как в репозитории)
    nh = n ÷ 2 + 1
    kfh = FFTW.rfftfreq(n) .* n          # nh значений для укороченной x-оси
    kx = zeros(nh, n, n); ky = zeros(nh, n, n); kz = zeros(nh, n, n)
    kx .= reshape(kfh, nh, 1, 1)         # x-ось укорочена (Julia rfft)
    ky .= reshape(kf, 1, n, 1)
    kz .= reshape(kf, 1, 1, n)
    k2 = kx.^2 .+ ky.^2 .+ kz.^2
    return kx, ky, kz, k2
end

function dealias_mask(n::Int)
    kx, ky, kz, _ = wavevectors(n)
    crit = n ÷ 3
    return (abs.(kx) .<= crit) .& (abs.(ky) .<= crit) .& (abs.(kz) .<= crit)
end

function tg_initial_condition(n::Int)
    v = ((0:n-1) .+ 0.5) .* (2π / n)
    u = zeros(3, n, n, n)
    xv = reshape(v, n, 1, 1); yv = reshape(v, 1, n, 1); zv = reshape(v, 1, 1, n)
    u[1, :, :, :] .= sin.(xv) .* cos.(yv) .* cos.(zv)
    u[2, :, :, :] .= -cos.(xv) .* sin.(yv) .* cos.(zv)
    return u
end

function rotate_z!(u::Array{Float64,4}, theta::Float64)
    c, s = cos(theta), sin(theta)
    u1 = copy(u[1, :, :, :]); u2 = copy(u[2, :, :, :])
    u[1, :, :, :] .= c .* u1 .- s .* u2
    u[2, :, :, :] .= s .* u1 .+ c .* u2
    return u
end

mutable struct SpecSolver
    n::Int; nu::Float64; dt::Float64; bpow::Float64
    kx::Array{Float64,3}; ky::Array{Float64,3}; kz::Array{Float64,3}
    k2::Array{Float64,3}; k2e::Array{Float64,3}
    kmag::Array{Float64,3}; kmb::Array{Float64,3}
    mask::Array{Bool,4}; crit::Int
    uh::Array{ComplexF64,4}
    _D::Array{Float64,4}; _Dm::Array{Float64,4}
end

function SpecSolver(n::Int, nu::Float64, dt::Float64, bpow::Float64)
    kx, ky, kz, k2 = wavevectors(n)
    k2e = copy(k2); k2e[1, 1, 1] = 1.0
    kmag = sqrt.(k2)
    kmb = kmag .^ (2.0 * bpow)
    # ВАЖНО (Julia vs NumPy): broadcast в Julia выравнивает оси НАЧАЛА,
    # а не конца! Поэтому маску и диссипационные коэффициенты храним
    # как 4D (1,nh,n,n) — тогда (3,nh,n,n) .* (1,nh,n,n) расширяется верно.
    nh = n ÷ 2 + 1
    mask = reshape(Array{Bool,3}(dealias_mask(n)), 1, nh, n, n)
    uh = zeros(ComplexF64, 3, nh, n, n)
    lam = bpow == 1.0 ? nu .* k2 : nu .* kmb
    D = reshape(exp.(-lam .* dt), 1, nh, n, n)
    Dm = reshape(sqrt.(exp.(-lam .* dt)), 1, nh, n, n)
    return SpecSolver(n, nu, dt, bpow, kx, ky, kz, k2, k2e, kmag, kmb,
                      mask, n ÷ 3, uh, D, Dm)
end

function project(sv::SpecSolver, fh::Array{ComplexF64,4})
    nh, n = size(sv.kx, 1), sv.n
    div = (sv.kx .* fh[1, :, :, :] .+ sv.ky .* fh[2, :, :, :] .+
           sv.kz .* fh[3, :, :, :]) ./ sv.k2e
    p1 = reshape(fh[1, :, :, :] .- sv.kx .* div, 1, nh, n, n)
    p2 = reshape(fh[2, :, :, :] .- sv.ky .* div, 1, nh, n, n)
    p3 = reshape(fh[3, :, :, :] .- sv.kz .* div, 1, nh, n, n)
    return cat(p1, p2, p3; dims = 1)
end

function set_ic!(sv::SpecSolver, u::Array{Float64,4})
    uh = FFTW.rfft(u, (2, 3, 4))          # (3, nh, n, n)
    sv.uh = project(sv, uh) .* sv.mask
    sv.uh[:, 1, 1, 1] .= 0.0
    return sv
end

phys(sv::SpecSolver) = FFTW.irfft(sv.uh, sv.n, (2, 3, 4))

function vorticity_hat(sv::SpecSolver)
    kx, ky, kz = sv.kx, sv.ky, sv.kz
    nh, n = size(sv.kx, 1), sv.n
    u1, u2, u3 = sv.uh[1, :, :, :], sv.uh[2, :, :, :], sv.uh[3, :, :, :]
    w1 = im .* (ky .* u3 .- kz .* u2)
    w2 = im .* (kz .* u1 .- kx .* u3)
    w3 = im .* (kx .* u2 .- ky .* u1)
    # reshape до 4D перед склейкой по компонентной оси
    w1 = reshape(w1, 1, nh, n, n)
    w2 = reshape(w2, 1, nh, n, n)
    w3 = reshape(w3, 1, nh, n, n)
    return cat(w1, w2, w3; dims = 1)
end

vorticity(sv::SpecSolver) = FFTW.irfft(vorticity_hat(sv), sv.n, (2, 3, 4))

function rhs!(sv::SpecSolver, out::Array{ComplexF64,4})
    u = phys(sv)
    w = vorticity(sv)
    n = sv.n
    c1 = u[2, :, :, :] .* w[3, :, :, :] .- u[3, :, :, :] .* w[2, :, :, :]
    c2 = u[3, :, :, :] .* w[1, :, :, :] .- u[1, :, :, :] .* w[3, :, :, :]
    c3 = u[1, :, :, :] .* w[2, :, :, :] .- u[2, :, :, :] .* w[1, :, :, :]
    # reshape до 4D перед склейкой по компонентной оси
    cr = cat(reshape(c1, 1, n, n, n), reshape(c2, 1, n, n, n),
             reshape(c3, 1, n, n, n); dims = 1)
    ch = FFTW.rfft(cr, (2, 3, 4))
    ch = project(sv, ch)
    ch[:, 1, 1, 1] .= 0.0
    out .= ch
    return out
end

function step!(sv::SpecSolver)
    dt = sv.dt
    k1 = rhs!(sv, similar(sv.uh))
    uh_save = copy(sv.uh)
    sv.uh .= sv._Dm .* (uh_save .+ 0.5 .* dt .* k1)
    k2v = rhs!(sv, k1)
    sv.uh .= sv._D .* uh_save .+ dt .* sv._Dm .* k2v
    sv.uh .*= sv.mask
    sv.uh[1, 1, 1, :] .= 0.0
    return sv
end

energy(sv::SpecSolver) = 2.0 * sum(abs2, sv.uh) / sv.n^6

function shell_spectrum(sv::SpecSolver)
    e = zeros(sv.n ÷ 2 + 1)
    uh2 = dropdims(sum(abs2, sv.uh; dims = 1); dims = 1)   # (nh,n,n)
    kb = round.(Int, sv.kmag)
    n6 = sv.n^6
    for kk in 1:(length(e) - 1)
        m = kb .== kk
        if any(m)
            e[kk+1] = 2.0 * sum(uh2[m]) / n6
        end
    end
    return e
end

diss_rate(sv::SpecSolver) = begin
    w = sv.bpow == 1.0 ? sv.k2 : sv.kmb
    uh2 = dropdims(sum(abs2, sv.uh; dims = 1); dims = 1)
    sv.nu * 2.0 * sum(w .* uh2) / sv.n^6
end

function enstrophy_palinstrophy(sv::SpecSolver)
    wh = vorticity_hat(sv)
    wh2 = dropdims(sum(abs2, wh; dims = 1); dims = 1)
    om2 = 2.0 * sum(wh2) / sv.n^6
    pal = 2.0 * sum(sv.k2 .^ 2 .* wh2) / sv.n^6
    return om2, pal
end

# Честная реализация S1 = 2<ω_i S_ij ω_j>: девять производных d_b u_a.
# rfft 3D-поля (n,n,n) по (1,2,3) даёт (nh,n,n) — согласовано с k-массивами.
function stretching(sv::SpecSolver, u::Array{Float64,4}, w::Array{Float64,4})
    n = sv.n
    grad = Dict{Tuple{Int,Int},Array{Float64,3}}()
    for a in 1:3
        gh = FFTW.rfft(u[a, :, :, :], (1, 2, 3))
        for b in 1:3
            kb = b == 1 ? sv.kx : b == 2 ? sv.ky : sv.kz
            grad[(a, b)] = FFTW.irfft(im .* kb .* gh, n, (1, 2, 3))
        end
    end
    s1 = 0.0
    for a in 1:3, b in 1:3
        sab = 0.5 .* (grad[(a, b)] .+ grad[(b, a)])
        s1 += mean3(w[a, :, :, :] .* w[b, :, :, :] .* sab)
    end
    return 2.0 * s1
end

mean3(x::Array{Float64,3}) = sum(x) / length(x)

# --- производные функции монографии ----------------------------------------
beta_b(bpow::Float64; ck::Float64 = 1.5) = begin
    a = 2.0 * bpow - 2.0 / 3.0
    (ck * gamma(a / (2.0 * bpow)) / bpow)^(2.0 * bpow / a)
end
x_star(bpow::Float64; ck::Float64 = 1.5) = begin
    bb = beta_b(bpow; ck = ck)
    ((2.0 * bpow - 5.0 / 3.0) / (2.0 * bpow * bb))^(1.0 / (2.0 * bpow))
end
eta_b(eps::Float64, nu::Float64, bpow::Float64) =
    (nu^3 / eps)^(1.0 / (6.0 * bpow - 2.0))

function tail_fits(e::Vector{Float64}, band::Tuple{Float64,Float64})
    kk = collect(0.0:(length(e) - 1.0))
    m = (kk .>= band[1]) .& (kk .<= band[2]) .& (e .> 0)
    if count(m) < 4
        return (NaN, NaN, NaN, NaN)
    end
    xk = kk[m]; le = log.(e[m])
    c_exp = sum(xk .* (le .- mean(le))) / sum((xk .- mean(xk)) .^ 2)
    i_exp = mean(le) .- c_exp * mean(xk)
    ss = sum((le .- mean(le)) .^ 2)
    r2e = ss > 0 ? 1.0 - sum((le .- (c_exp .* xk .+ i_exp)) .^ 2) / ss : NaN
    lxk = log.(xk)
    sl = sum(lxk .* (le .- mean(le))) / sum((lxk .- mean(lxk)) .^ 2)
    ii = mean(le) .- sl * mean(lxk)
    r2p = ss > 0 ? 1.0 - sum((le .- (sl .* lxk .+ ii)) .^ 2) / ss : NaN
    return (c_exp, r2e, sl, r2p)
end

function kd_from_spectrum(e::Vector{Float64}, bpow::Float64)
    kk = collect(0.0:(length(e) - 1.0))
    d = kk .^ (2.0 * bpow) .* e
    kk = kk[2:end]; d = d[2:end]
    maximum(d) <= 0 && return NaN
    i = argmax(d)
    if 2 <= i <= length(d) - 1
        y0, y1, y2 = d[i-1], d[i], d[i+1]
        denom = y0 - 2y1 + y2
        delta = abs(denom) > 1e-300 ? 0.5 * (y0 - y2) / denom : 0.0
        return kk[i] + clamp(delta, -1.0, 1.0)
    end
    return kk[i]
end

# ============================================================================
# ВЕРДИКТЫ WIN / DRAW / LOSS
# ============================================================================
mutable struct Verdicts
    rows::Vector{Dict{String,Any}}
    thr::Dict{String,Any}
end
Verdicts(cfg::Dict{String,Any}) = Verdicts(Dict{String,Any}[], cfg)

function judge!(V::Verdicts, lab::String, test::String, value::Real;
                thrkey::Union{String,Nothing} = nothing, note::String = "")
    v = "WIN"
    if isnan(value)
        v = "DRAW"
    elseif thrkey !== nothing
        tw, td = V.thr[thrkey]
        v = value < tw ? "WIN" : (value < td ? "DRAW" : "LOSS")
    end
    push!(V.rows, Dict{String,Any}("lab" => lab, "test" => test,
                                   "value" => Float64(value), "verdict" => v,
                                   "note" => note))
    return v
end

tally(V::Verdicts) = begin
    w = count(r -> r["verdict"] == "WIN", V.rows)
    d = count(r -> r["verdict"] == "DRAW", V.rows)
    l = count(r -> r["verdict"] == "LOSS", V.rows)
    Dict("WIN" => w, "DRAW" => d, "LOSS" => l, "total" => length(V.rows))
end

function print_verdicts(ui_lang::String, V::Verdicts)
    t = I18N[ui_lang]
    say(COL_Y * "  " * "─"^74 * COL_0)
    for r in V.rows
        val = @sprintf("%.3e", r["value"])
        icon, col = r["verdict"] == "WIN" ? ("✔", COL_G) :
                    r["verdict"] == "DRAW" ? ("◆", COL_Y) : ("✘", COL_R)
        nm = rpad(icon * " " * (r["verdict"] == "WIN" ? t["win"] :
                                r["verdict"] == "DRAW" ? t["draw"] : t["loss"]), 30)
        say("  " * col * nm * COL_0 * rpad(r["test"][1:min(end, 44)], 46) * val)
    end
    sc = tally(V)
    say(COL_Y * "  " * "─"^74 * COL_0)
    say("  " * t["score"] * ": " * COL_G * "WIN=$(sc["WIN"])" * COL_0 *
        "  " * COL_Y * "DRAW=$(sc["DRAW"])" * COL_0 *
        "  " * COL_R * "LOSS=$(sc["LOSS"])" * COL_0)
end

# ============================================================================
# ЧЕКПОИНТ-РАННЕР ТРАЕКТОРИЙ
# ============================================================================
function run_trajectory(label::String, n::Int, nu::Float64, dt::Float64,
                        t_end::Float64, save_every::Int; bpow = 1.0,
                        rotate = false, lang = "ru", cfg = default_cfg(),
                        checkpoint::Bool = true, show_bar::Bool = true)
    state_path = joinpath(OUT_RESULTS, "ckpt_$label.jlser")
    sv = SpecSolver(n, nu, dt, Float64(bpow))
    n_steps = round(Int, t_end / dt)
    names = ("t", "E", "Omega", "eps", "omega_inf", "u_inf", "u4", "u6",
             "pal", "S1", "D2")
    logs = Dict{String,Vector{Float64}}(n => Float64[] for n in names)
    cert = Vector{NTuple{5,Float64}}()
    step0 = 0
    spec_store = Dict{String,Vector{Float64}}()
    if checkpoint && isfile(state_path)
        st = deserialize(state_path)
        sv.uh = st["uh"]
        step0 = st["step"]
        logs = st["logs"]
        cert = st["cert"]
        spec_store = st["spec"]
        say(COL_D * "  [$label] $(I18N[lang]["resume"]) $step0" * COL_0)
    else
        ic = tg_initial_condition(n)
        rotate && rotate_z!(ic, THETA_B)
        set_ic!(sv, ic)
        say(COL_D * "  [$label] $(I18N[lang]["fresh"]): N=$n, b=$bpow, " *
            "dt=$dt, T=$t_end" * COL_0)
    end
    band = (0.7 * sv.crit, Float64(sv.crit))
    t0c = time()
    step = step0
    while step <= n_steps
        t = step * dt
        if step % save_every == 0 || step == n_steps
            u = phys(sv)
            w = vorticity(sv)
            E = energy(sv)
            eps = diss_rate(sv)
            win_ = maximum(sqrt.(dropdims(sum(abs2, w; dims = 1); dims = 1)))
            uin = maximum(sqrt.(dropdims(sum(abs2, u; dims = 1); dims = 1)))
            u2m = dropdims(sum(abs2, u; dims = 1); dims = 1)
            # конвенция репозитория (p5_regularity.py): u4 = <u^2>^2, u6 = <u^2>^3
            u4 = mean(u2m)^2
            u6 = mean(u2m)^3
            Om, pal = enstrophy_palinstrophy(sv)
            s1 = stretching(sv, u, w)
            wh2 = dropdims(sum(abs2, vorticity_hat(sv); dims = 1); dims = 1)
            k2b = bpow == 1.0 ? sv.k2 : sv.kmb
            d2 = 4.0 * nu * sum(k2b .* wh2) / n^6
            e_sh = shell_spectrum(sv)
            cf = tail_fits(e_sh, band)
            kd = kd_from_spectrum(e_sh, Float64(bpow))
            push!(logs["t"], t); push!(logs["E"], E)
            push!(logs["Omega"], Om); push!(logs["eps"], eps)
            push!(logs["omega_inf"], win_); push!(logs["u_inf"], uin)
            push!(logs["u4"], u4); push!(logs["u6"], u6)
            push!(logs["pal"], pal); push!(logs["S1"], s1)
            push!(logs["D2"], d2)
            push!(cert, (cf[1], cf[2], cf[3], cf[4], kd))
        end
        step == n_steps && break
        if show_bar && step % 5 == 0
            frac = step / n_steps
            el = time() - t0c
            eta = el / max(frac - step0 / n_steps, 1e-9) * (1 - frac)
            progress!(frac, @sprintf("[%s] t=%5.2f/%g E=%.5f %s %s",
                                     label, t, t_end, energy(sv),
                                     I18N[lang]["eta"],
                                     fmt_sec(round(Int, eta))))
        end
        if checkpoint && step > step0 && time() - t0c > cfg["budget_s"]
            break
        end
        step!(sv)
        step += 1
    end
    show_bar && progress!(1.0, @sprintf("[%s] t=%g/%g E=%.5f",
                                        label, t_end, t_end, energy(sv)))
    done = step >= n_steps
    if checkpoint
        serialize(state_path, Dict("uh" => sv.uh, "step" => step,
                                   "logs" => logs, "cert" => cert,
                                   "spec" => spec_store))
    end
    # сводка
    t_arr = logs["t"]; E_arr = logs["E"]; Om_arr = logs["Omega"]
    eps_arr = logs["eps"]; win_arr = logs["omega_inf"]
    i_peak = argmax(Om_arr)
    trapezoid(x, y) = sum((x[i+1] - x[i]) * 0.5 * (y[i+1] + y[i])
                          for i in 1:(length(x) - 1))
    i_bkm = trapezoid(t_arr, win_arr)
    lps4 = trapezoid(t_arr, logs["u4"])
    lps6 = trapezoid(t_arr, sqrt.(logs["u6"]))
    bal = 0.0; bal2 = 0.0
    if length(t_arr) > 2
        dEdt = [(E_arr[i+1] - E_arr[i-1]) / (t_arr[i+1] - t_arr[i-1])
                for i in 2:(length(t_arr) - 1)]
        bal = maximum(abs.(dEdt .+ 2.0 .* eps_arr[2:(end - 1)])) /
              maximum(E_arr)
        dOmdt = [(Om_arr[i+1] - Om_arr[i-1]) / (t_arr[i+1] - t_arr[i-1])
                 for i in 2:(length(t_arr) - 1)]
        res = [logs["S1"][i] - logs["D2"][i] for i in 2:(length(t_arr) - 1)]
        bal2 = maximum(abs.(dOmdt .- res)) / maximum(Om_arr)
    end
    m_stat = t_arr .>= Float64(cfg["stat_t0"])
    eps_mean = count(m_stat) > 0 ? mean(eps_arr[m_stat]) : eps_arr[end]
    kd_win = count(m_stat) > 0 ? mean(x[5] for x in cert[m_stat]) : cert[end][5]
    summary = Dict{String,Any}(
        "label" => label, "grid" => n, "b_pow" => bpow, "nu" => nu,
        "dt" => dt, "t_end" => t_end, "rotated" => rotate,
        "t_peak_enstrophy" => t_arr[i_peak], "Omega_max" => maximum(Om_arr),
        "omega_inf_max" => maximum(win_arr), "u_inf_max" => maximum(logs["u_inf"]),
        "I_BKM_T" => i_bkm, "LPS_int_u4" => lps4, "LPS_int_u6half" => lps6,
        "E_final" => E_arr[end], "eps_mean_stat" => eps_mean,
        "energy_balance_rel_max" => bal, "enstrophy_balance_rel_max" => bal2,
        "kd_mean_stat" => kd_win,
        "c_exp_at_peak" => cert[i_peak][1], "r2_exp_at_peak" => cert[i_peak][2],
        "slope_pow_at_peak" => cert[i_peak][3], "r2_pow_at_peak" => cert[i_peak][4],
        "steps" => step, "done" => done,
    )
    return Dict("summary" => summary, "logs" => logs, "cert" => cert,
                "spec" => spec_store, "done" => done)
end

# ============================================================================
# ЛАБОРАТОРИИ
# ============================================================================
function lab_matrix112(lang::String, cfg::Dict{String,Any})
    t = I18N[lang]
    n = cfg["n_matrix"]
    say(COL_C * "\n┌─[ L1 ]─ " * t["lab1"] * COL_0)
    rng = MersenneTwister(cfg["seed"])
    V = Verdicts(cfg)
    out = Dict{String,Any}("lab" => "L1_matrix112", "n" => n,
                           "tests" => Dict{String,Any}())
    # 1) блочно-диагональная ортогональная матрица поворотов 112x112
    th = THETA_B
    R = zeros(n, n)
    for i in 1:2:(n - 1)
        c, s = cos(th), sin(th)
        R[i, i] = c; R[i, i+1] = -s
        R[i+1, i] = s; R[i+1, i+1] = c
    end
    orth = maximum(abs.(R' * R .- I(n)))
    judge!(V, "L1", "R(theta_b) block-diag orthogonality (112x112)", orth;
           thrkey = "thr_matrix_orth")
    out["tests"]["R_orth_residual"] = orth
    # 2) Родригес 3D на случайных векторах
    u = randn(rng, 3, 200_000)
    ax = randn(rng, 3, 200_000)
    ax ./= reshape(sqrt.(sum(abs2, ax; dims = 1)), 1, :)
    upar = reshape(vec(sum(u .* ax; dims = 1)), 1, :) .* ax
    uperp = u .- upar
    cross = hcat(ax[2,:] .* uperp[3,:] .- ax[3,:] .* uperp[2,:],
                 ax[3,:] .* uperp[1,:] .- ax[1,:] .* uperp[3,:],
                 ax[1,:] .* uperp[2,:] .- ax[2,:] .* uperp[1,:])'
    v = upar .+ cos(th) .* uperp .+ sin(th) .* cross
    nd = maximum(abs.(vec(sum(v .^ 2; dims = 1)) ./ vec(sum(u .^ 2; dims = 1)) .- 1))
    judge!(V, "L1", "Rodrigues 3D norm preservation (200k vectors)", nd;
           thrkey = "thr_matrix_orth")
    out["tests"]["rodrigues_norm_dev"] = nd
    # 3) проектор Лерея через ортонормированное вложение
    Q, _ = qr(randn(rng, n, 3))
    U = Matrix(Q)'                      # 3 x n, ортонорм. строки
    k0 = randn(rng, 3); k0 ./= norm(k0)
    Pf = I(3) .- k0 * k0'
    P = U' * (Pf * U)
    idem = maximum(abs.(P * P .- P))
    judge!(V, "L1", "Leray projector block idempotence (112x112)", idem;
           thrkey = "thr_matrix_orth")
    out["tests"]["leray_idempotence_112"] = idem
    # 4) унитарность линейного потока KdV exp(i k^3 t) как 112x112
    kv = FFTW.fftfreq(n) .* n .* (2π / 100.0)
    Ukd = Diagonal(exp.(im .* kv .^ 3 .* 0.7))
    unit = maximum(abs.(Ukd' * Ukd .- I(n)))
    judge!(V, "L1", "KdV linear flow unitarity exp(i k^3 t) (112x112)", unit;
           thrkey = "thr_matrix_orth")
    out["tests"]["kdv_unitarity_112"] = unit
    # 5) FFT 112^3: обратимость + Парсеваль (укороченная ось — dim 1)
    f = randn(rng, n, n, n)
    fh = FFTW.rfft(f, (1, 2, 3))                # (nh, n, n)
    f2 = FFTW.irfft(fh, n, (1, 2, 3))
    rt = maximum(abs.(f2 .- f)) / maximum(abs.(f))
    judge!(V, "L1", "FFT $(n)^3 roundtrip", rt; thrkey = "thr_matrix_orth")
    par1 = sum(abs2, f)
    fh2 = abs2.(fh)
    par2 = (2 * sum(fh2) - sum(fh2[1, :, :]) - sum(fh2[end, :, :])) / n^3
    judge!(V, "L1", "Parseval identity $(n)^3", abs(par1 - par2) / par1;
           thrkey = "thr_matrix_orth")
    out["tests"]["fft_roundtrip"] = rt
    out["tests"]["fft_parseval_err"] = abs(par1 - par2) / par1
    # 6) дивергентно-свободный остаток TG на 112^3
    kx, ky, kz, k2 = wavevectors(n)
    k2e = copy(k2); k2e[1, 1, 1] = 1.0
    uh0 = FFTW.rfft(tg_initial_condition(n), (2, 3, 4))   # (3,nh,n,n)
    div0 = maximum(abs.(kx .* uh0[1, :, :, :] .+ ky .* uh0[2, :, :, :] .+
                        kz .* uh0[3, :, :, :]) ./ k2e)
    judge!(V, "L1", "TG IC divergence-free residual ($(n)^3)", div0;
           thrkey = "thr_divfree")
    out["tests"]["tg_divfree_residual"] = div0
    out["verdicts"] = V.rows
    out["tally"] = tally(V)
    print_verdicts(lang, V)
    return out
end

function lab_smoke48(lang::String, cfg::Dict{String,Any})
    t = I18N[lang]
    say(COL_C * "\n┌─[ L3 ]─ " * t["lab3"] * COL_0)
    res = run_trajectory("SMOKE48", cfg["n_smoke"], cfg["nu"], cfg["dt"],
                         cfg["t_end_smoke"], cfg["save_every"]; lang = lang,
                         cfg = cfg, checkpoint = false)
    V = Verdicts(cfg)
    judge!(V, "L3", "energy balance (SMOKE48)",
           res["summary"]["energy_balance_rel_max"];
           thrkey = "thr_energy_balance")
    judge!(V, "L3", "enstrophy balance (SMOKE48)",
           res["summary"]["enstrophy_balance_rel_max"];
           thrkey = "thr_enstrophy_balance")
    print_verdicts(lang, V)
    return Dict("lab" => "L3_smoke48", "summary" => res["summary"],
                "verdicts" => V.rows, "tally" => tally(V))
end

function lab_main96(lang::String, cfg::Dict{String,Any})
    t = I18N[lang]
    say(COL_C * "\n┌─[ L4 ]─ " * t["lab4"] * COL_0)
    res = run_trajectory("A96JL", cfg["n_main"], cfg["nu"], cfg["dt"],
                         cfg["t_end_main"], cfg["save_every"]; lang = lang,
                         cfg = cfg)
    sA = res["summary"]
    out = Dict{String,Any}("lab" => "L4_main96_julia", "params" =>
        Dict("grid" => cfg["n_main"], "nu" => cfg["nu"], "dt" => cfg["dt"],
             "T" => cfg["t_end_main"], "ic" => "Taylor-Green",
             "impl" => "Julia FFTW IFK-RK2 + Leray + 2/3 dealias"),
        "run_A96_summary" => sA)
    # сравнение с эталоном 48^3
    ref = joinpath(PKG_ROOT, "reference", "p5_regularity.json")
    V = Verdicts(cfg)
    conv = Dict{String,Any}()
    if isfile(ref)
        a48 = parse48(ref)
        for key in ("t_peak_enstrophy", "Omega_max", "omega_inf_max",
                    "I_BKM_T", "LPS_int_u4", "LPS_int_u6half", "E_final",
                    "eps_mean_stat")
            v48 = a48[key]
            v96 = sA[key]
            rel = v48 != 0 ? abs(v96 - v48) / abs(v48) : NaN
            conv[key] = Dict("n48" => v48, "n96" => v96, "rel_diff" => rel)
            key == "t_peak_enstrophy" && continue
            judge!(V, "L4", "48→96 $key (Julia impl)", rel;
                   thrkey = "thr_conv_headline")
        end
    else
        say(COL_Y * "  ⚠ эталон 48³ не найден" * COL_0)
    end
    out["convergence_48_vs_96"] = conv
    out["verdicts"] = V.rows
    out["tally"] = tally(V)
    print_verdicts(lang, V)
    stamp = Dates.format(Dates.now(), "yyyymmdd_HHMMSS")
    save_json(joinpath(OUT_RESULTS, "julia_main96_$stamp.json"), out)
    # CSV траектории
    open(joinpath(OUT_RESULTS, "julia_A96_trajectory.csv"), "w") do io
        println(io, "t,E,Omega,omega_inf,eps")
        for i in eachindex(res["logs"]["t"])
            println(io, @sprintf("%.4f,%.8e,%.8e,%.8e,%.8e",
                                 res["logs"]["t"][i], res["logs"]["E"][i],
                                 res["logs"]["Omega"][i],
                                 res["logs"]["omega_inf"][i],
                                 res["logs"]["eps"][i]))
        end
    end
    return out
end

function lab_bfamily96(lang::String, cfg::Dict{String,Any})
    t = I18N[lang]
    say(COL_C * "\n┌─[ L6 ]─ " * t["lab6"] * COL_0)
    rows = []
    for bp in cfg["b_powers"]
        lab = "H$(replace(string(bp), "." => "p"))_96JL"
        say(COL_D * "  --- b_pow = $bp ($lab) ---" * COL_0)
        res = run_trajectory(lab, cfg["n_main"], cfg["nu"], cfg["dt"],
                             cfg["t_end_main"], cfg["save_every"]; bpow = bp,
                             lang = lang, cfg = cfg)
        s = res["summary"]
        eb = eta_b(s["eps_mean_stat"], cfg["nu"], Float64(bp))
        kd = s["kd_mean_stat"]
        push!(rows, Dict{String,Any}(
            "b_pow" => bp, "label" => lab, "eps_mean_stat" => s["eps_mean_stat"],
            "eta_b" => eb, "k_max_over_eta_b" => (cfg["n_main"] / 3.0) * eb,
            "kd_measured" => kd, "kd_times_eta_b" => kd * eb,
            "x_star_theory" => x_star(Float64(bp)),
            "beta_b_theory" => beta_b(Float64(bp)),
            "rel_dev" => abs(kd * eb - x_star(Float64(bp))) /
                         x_star(Float64(bp))))
        say(@sprintf("  [%s] k_d*eta_b = %.4f vs x* = %.4f", lab, kd * eb,
                     x_star(Float64(bp))))
    end
    out = Dict{String,Any}("lab" => "L6_bfamily96_julia", "rows" => rows)
    stamp = Dates.format(Dates.now(), "yyyymmdd_HHMMSS")
    save_json(joinpath(OUT_RESULTS, "julia_bfamily96_$stamp.json"), out)
    return out
end

function lab_bprotocol96(lang::String, cfg::Dict{String,Any})
    t = I18N[lang]
    say(COL_C * "\n┌─[ L7 ]─ " * t["lab7"] * COL_0)
    res_b = run_trajectory("B96JL", cfg["n_main"], cfg["nu"], cfg["dt"],
                           cfg["t_end_main"], cfg["save_every"]; rotate = true,
                           lang = lang, cfg = cfg)
    sB = res_b["summary"]
    sA = nothing
    ckA = joinpath(OUT_RESULTS, "ckpt_A96JL.jlser")
    if isfile(ckA)
        st = deserialize(ckA)
        t_arr = st["logs"]["t"]
        ia = sum((t_arr[i+1] - t_arr[i]) * 0.5 *
                 (st["logs"]["omega_inf"][i+1] + st["logs"]["omega_inf"][i])
                 for i in 1:(length(t_arr) - 1))
        sA = Dict("I_BKM_T" => ia)
    else
        ra = run_trajectory("A96JL", cfg["n_main"], cfg["nu"], cfg["dt"],
                            cfg["t_end_main"], cfg["save_every"]; lang = lang,
                            cfg = cfg)
        sA = Dict("I_BKM_T" => ra["summary"]["I_BKM_T"])
    end
    V = Verdicts(cfg)
    f_bkm = sB["I_BKM_T"] / max(sA["I_BKM_T"], 1e-300)
    judge!(V, "L7", "I_BKM(B)/I_BKM(A) - 1 (Julia impl)", abs(f_bkm - 1.0);
           thrkey = "thr_conv_headline", note = "factor = $(round(f_bkm, digits = 4))")
    out = Dict{String,Any}("lab" => "L7_bprotocol96_julia",
                           "run_B96_summary" => sB, "I_BKM_A" => sA["I_BKM_T"],
                           "verdicts" => V.rows, "tally" => tally(V))
    print_verdicts(lang, V)
    stamp = Dates.format(Dates.now(), "yyyymmdd_HHMMSS")
    save_json(joinpath(OUT_RESULTS, "julia_bprotocol96_$stamp.json"), out)
    return out
end

function lab_dns112(lang::String, cfg::Dict{String,Any})
    t = I18N[lang]
    n = cfg["n_matrix"]
    say(COL_C * "\n┌─[ L5 ]─ " * t["lab5"] * COL_0)
    res = run_trajectory("A$(n)JL", n, cfg["nu"], cfg["dt"],
                         cfg["t_end_112"], cfg["save_every"]; lang = lang,
                         cfg = cfg)
    sA = res["summary"]
    V = Verdicts(cfg)
    judge!(V, "L5", "energy balance ($(n)^3, Julia)",
           sA["energy_balance_rel_max"]; thrkey = "thr_energy_balance")
    judge!(V, "L5", "enstrophy balance ($(n)^3, Julia)",
           sA["enstrophy_balance_rel_max"];
           thrkey = "thr_enstrophy_balance")
    print_verdicts(lang, V)
    out = Dict{String,Any}("lab" => "L5_dns$(n)_julia",
                           "run_summary" => sA, "verdicts" => V.rows,
                           "tally" => tally(V))
    stamp = Dates.format(Dates.now(), "yyyymmdd_HHMMSS")
    save_json(joinpath(OUT_RESULTS, "julia_dns$(n)_$stamp.json"), out)
    return out
end

# --- KdV (IFRK4 + 2/3 dealias + инварианты) ---------------------------------
kdv_wavenumbers(n::Int, l::Float64) = FFTW.fftfreq(n) .* (n / l) .* (2π)

function kdv_ifrk4(n::Int, l::Float64, dt::Float64, t_end::Float64,
                   u0::Vector{Float64}; mech::String = "none",
                   theta::Float64 = 0.0, dealias::Bool = true)
    k = kdv_wavenumbers(n, l)
    Eop = exp.(im .* (k .^ 3) .* dt)
    Eop2 = exp.(im .* (k .^ 3) .* dt / 2)
    mask = nothing
    if dealias
        crit = n ÷ 3
        kf = FFTW.fftfreq(n) .* (n / l)
        mask = abs.(kf) .<= crit * (2π / l)
    end
    uh = FFTW.fft(u0)
    mask !== nothing && (uh .*= mask)
    nsteps = round(Int, t_end / dt)
    nl(u) = begin
        mech == "M3" && (u = cos(theta) .* u)
        -3.0im .* k .* FFTW.fft(u .^ 2)
    end
    applymask(x) = mask === nothing ? x : x .* mask
    M = Float64[mean(u0)]; P = Float64[mean(u0 .^ 2) / 2]
    ux0 = FFTW.ifft(im .* k .* uh)
    E0 = mean(u0 .^ 3) - real(mean(ux0 .^ 2)) / 2
    Ev = Float64[E0]
    uhat = copy(uh)
    for step in 1:nsteps
        a = applymask(nl(FFTW.ifft(uhat)))
        b_ = applymask(nl(FFTW.ifft(Eop2 .* (uhat .+ dt / 2 .* a))))
        c_ = applymask(nl(FFTW.ifft(Eop2 .* uhat .+ dt / 2 .* b_)))
        d_ = applymask(nl(FFTW.ifft(Eop .* uhat .+ dt .* Eop2 .* c_)))
        uhat = applymask(Eop .* uhat .+
                         dt / 6 .* (Eop .* a .+ 2 .* Eop2 .* (b_ .+ c_) .+ d_))
        if step == nsteps
            u_f = FFTW.ifft(uhat)
            push!(M, mean(real.(u_f)))
            push!(P, mean(abs2.(u_f)) / 2)
            uxx = FFTW.ifft(im .* k .* uhat)
            push!(Ev, mean(real.(u_f) .^ 3) - real(mean(uxx .^ 2)) / 2)
        end
    end
    drift = Dict("M" => abs(M[end] - M[1]) / max(abs(M[1]), 1e-300),
                 "P" => abs(P[end] - P[1]) / max(abs(P[1]), 1e-300),
                 "E" => abs(Ev[end] - Ev[1]) /
                        max(abs(Ev[1]), real(mean(abs.(ux0 .^ 2))) / 2, 1e-300))
    return Dict("drift" => drift, "M" => M, "P" => P, "E" => Ev)
end

kdv_soliton(x, c, x0) = (c / 2) ./ cosh.(sqrt(c) / 2 .* (x .- x0)) .^ 2

function lab_kdv(lang::String, cfg::Dict{String,Any})
    t = I18N[lang]
    say(COL_C * "\n┌─[ L2 ]─ " * t["lab2"] * COL_0)
    n = cfg["kdv_n"]; l = Float64(cfg["kdv_l"]); dt = Float64(cfg["kdv_dt"])
    Tend = Float64(cfg["kdv_t_end"])
    x = collect(0.0:(l / n):(l - l / n))
    V = Verdicts(cfg)
    u0 = kdv_soliton(x, Float64(cfg["kdv_c1"]), Float64(cfg["kdv_x0_1"]))
    r1 = kdv_ifrk4(n, l, dt, Tend, u0)
    worst1 = maximum(values(r1["drift"]))
    judge!(V, "L2", "E1 soliton invariant drift", worst1;
           thrkey = "thr_kdv_invariants")
    th = THETA_B
    ux0 = real.(FFTW.ifft(im .* kdv_wavenumbers(n, l) .* FFTW.fft(u0)))
    u_m2 = cos(th) .* u0 .+ sin(th) .* ux0
    rm2 = kdv_ifrk4(n, l, dt, Tend, u_m2)
    judge!(V, "L2", "M2 rodrigues IC invariant drift",
           maximum(values(rm2["drift"])); thrkey = "thr_kdv_invariants")
    rm3 = kdv_ifrk4(n, l, dt, Tend, u0; mech = "M3", theta = th)
    judge!(V, "L2", "M3 modified nonlinearity drift",
           maximum(values(rm3["drift"])); thrkey = "thr_kdv_invariants")
    out = Dict{String,Any}("lab" => "L2_kdv_julia",
                           "E1_drift" => r1["drift"],
                           "M2_drift" => rm2["drift"],
                           "M3_drift" => rm3["drift"],
                           "verdicts" => V.rows, "tally" => tally(V))
    print_verdicts(lang, V)
    stamp = Dates.format(Dates.now(), "yyyymmdd_HHMMSS")
    save_json(joinpath(OUT_RESULTS, "julia_kdv_$stamp.json"), out)
    return out
end

function lab_match(lang::String, cfg::Dict{String,Any})
    t = I18N[lang]
    say(COL_C * "\n┌─[ L8 ]─ " * t["lab8"] * COL_0)
    Tm = Float64(cfg["match_t"])
    quick(label, n; bpow = 1.0, rotate = false) =
        run_trajectory(label, n, cfg["nu"], cfg["dt"], Tm, cfg["save_every"];
                       bpow = bpow, rotate = rotate, lang = lang, cfg = cfg,
                       checkpoint = false, show_bar = false)["summary"]
    say(COL_D * "  Матч 1: A vs B — ожидание НИЧЬЯ" * COL_0)
    sA = quick("M1_AJL", cfg["n_smoke"])
    sB = quick("M1_BJL", cfg["n_smoke"]; rotate = true)
    dI = abs(sA["I_BKM_T"] - sB["I_BKM_T"]) / max(sA["I_BKM_T"], 1e-300)
    say(COL_D * "  Матч 2: A vs H2 — ожидание ПОБЕДА H2" * COL_0)
    sH = quick("M2_H2JL", cfg["n_smoke"]; bpow = 2.0)
    say(COL_D * "  Матч 3: A vs U — ожидание ПОРАЖЕНИЕ U" * COL_0)
    sU = quick("M3_UJL", cfg["match_n_under"])
    V = Verdicts(cfg)
    judge!(V, "L8", "MATCH1 A vs B |dI|/I", dI;
           thrkey = "thr_conv_headline", note = "expect DRAW (isometry)")
    judge!(V, "L8", "MATCH3 U/A balance ratio",
           sU["energy_balance_rel_max"] /
           max(sA["energy_balance_rel_max"], 1e-300);
           note = "expect U LOSS")
    out = Dict{String,Any}("lab" => "L8_match_julia",
                           "I_A" => sA["I_BKM_T"], "I_B" => sB["I_BKM_T"],
                           "I_H2" => sH["I_BKM_T"],
                           "bal_U" => sU["energy_balance_rel_max"],
                           "verdicts" => V.rows, "tally" => tally(V))
    print_verdicts(lang, V)
    stamp = Dates.format(Dates.now(), "yyyymmdd_HHMMSS")
    save_json(joinpath(OUT_RESULTS, "julia_match_$stamp.json"), out)
    return out
end

# --- парсер эталона 48^3 (минимальный JSON-ридер для плоских чисел) --------
function parse48(path::String)
    txt = read(path, String)
    m = match(r"\"run_A_baseline\"\s*:\s*\{([^}]*)\}", txt)
    out = Dict{String,Float64}()
    m === nothing && return out
    for fm in eachmatch(r"\"(\w+)\"\s*:\s*(-?[\d.eE+]+)", m.captures[1])
        out[fm.captures[1]] = parse(Float64, fm.captures[2])
    end
    return out
end

# ============================================================================
# СВОДНЫЙ ОТЧЁТ
# ============================================================================
function lab_report(lang::String)
    lines = ["# NSB LAB 96 (Julia) — aggregate report", "",
             "*$(Dates.format(Dates.now(), "yyyy-mm-dd HH:MM:SS"))*", ""]
    for f in sort(readdir(OUT_RESULTS))
        (endswith(f, ".json") && startswith(f, "julia_")) || continue
        lines *= ["## $f", "", "```json"]
        push!(lines, readline(joinpath(OUT_RESULTS, f)))
        lines *= ["```", ""]
    end
    open(joinpath(OUT_REPORTS, "NSB_LAB_REPORT_JULIA.md"), "w") do io
        println.(Ref(io), lines)
    end
    say(COL_D * "  отчёт: reports/NSB_LAB_REPORT_JULIA.md" * COL_0)
end

# ============================================================================
# МЕНЮ + CLI
# ============================================================================
function run_lab(key::String, lang::String, cfg::Dict{String,Any})
    if key == "1"
        return lab_matrix112(lang, cfg)
    elseif key == "2"
        return lab_kdv(lang, cfg)
    elseif key == "3"
        return lab_smoke48(lang, cfg)
    elseif key == "4"
        return lab_main96(lang, cfg)
    elseif key == "5"
        return lab_dns112(lang, cfg)
    elseif key == "6"
        return lab_bfamily96(lang, cfg)
    elseif key == "7"
        return lab_bprotocol96(lang, cfg)
    elseif key == "8"
        return lab_match(lang, cfg)
    elseif key == "10"
        return lab_report(lang)
    end
end

function menu_loop(lang::String, cfg::Dict{String,Any})
    while true
        println("\n"^2)
        banner(lang)
        t = I18N[lang]
        say(COL_C * "  ╔" * "═"^74 * "╗" * COL_0)
        say(COL_C * "  ║ " * center(t["menu_hdr"], 72) * " ║" * COL_0)
        say(COL_C * "  ╚" * "═"^74 * "╝" * COL_0)
        for (k, key) in (("1", "lab1"), ("2", "lab2"), ("3", "lab3"),
                         ("4", "lab4"), ("5", "lab5"), ("6", "lab6"),
                         ("7", "lab7"), ("8", "lab8"), ("10", "lab10"))
            col = key == "lab4" ? COL_G : COL_C
            say("   " * col * lpad(k, 2) * COL_0 * " │ " * t[key])
        end
        say(COL_Y * "   " * "─"^72 * COL_0)
        say("   " * COL_G * " A" * COL_0 * " │ " * t["lab_all"])
        say("   " * COL_M * " L" * COL_0 * " │ язык / language (ru↔en)")
        say("   " * COL_R * " Q" * COL_0 * " │ " * t["lab_quit"])
        print(t["choose"])
        choice = strip(readline())
        if choice == "" || uppercase(choice) == "Q"
            say(COL_D * "bye ✦" * COL_0)
            break
        elseif uppercase(choice) == "L"
            lang = lang == "ru" ? "en" : "ru"
        elseif uppercase(choice) == "A"
            for k in ("1", "2", "3", "4", "5", "6", "7", "8", "10")
                run_lab(k, lang, cfg)
            end
        elseif choice in ("1", "2", "3", "4", "5", "6", "7", "8", "10")
            run_lab(choice, lang, cfg)
        end
    end
end

function main(args::Vector{String})
    lang = "ru"
    run = nothing
    yes = "--yes" in args
    cfg = default_cfg()
    i = 1
    while i <= length(args)
        a = args[i]
        if a == "--lang" && i < length(args)
            lang = args[i+1]; i += 2
        elseif a == "--run" && i < length(args)
            run = args[i+1]; i += 2
        elseif a == "--set" && i + 1 < length(args)
            cfg[args[i+1]] = args[i+2]; i += 3
        else
            i += 1
        end
    end
    isdir(OUT_LOGS) || mkpath(OUT_LOGS)
    logpath = joinpath(OUT_LOGS, "nsb_lab_jl_" *
                       Dates.format(Dates.now(), "yyyymmdd_HHMMSS") * ".log")
    LOG_IO[] = open(logpath, "a")
    banner(lang)
    say(COL_D * "  лог: $logpath" * COL_0)
    say(COL_D * "  Julia $(VERSION), FFTW потоки: $(Sys.CPU_THREADS)" * COL_0)
    alias = Dict("matrix" => "1", "kdv" => "2", "smoke" => "3",
                 "main96" => "4", "dns112" => "5", "bfamily" => "6",
                 "bprotocol" => "7", "match" => "8", "report" => "10")
    if run !== nothing
        keys = run == "all" ? ["1", "2", "3", "4", "5", "6", "7", "8", "10"] :
               [get(alias, run, run)]
        for k in keys
            run_lab(k, lang, cfg)
        end
        say(COL_G * "\n  ✔ ГОТОВО / DONE" * COL_0)
        close(LOG_IO[])
        return 0
    end
    menu_loop(lang, cfg)
    close(LOG_IO[])
    return 0
end

(abspath(PROGRAM_FILE) == @__FILE__) && exit(main(ARGS))
