# 00_boot.jl — версия, машина, конфиг сессии, детекция TTY/цвета.
# Часть NSB Julia Lab: самодостаточная лаборатория без внешних пакетов
# (только stdlib: Printf, LinearAlgebra, Random, Base64, Dates).

const NSB_LAB_VERSION = "1.0.0"
const NSB_LAB_NAME = "Navier–Stokes b-Lab (Julia, self-contained)"

const NSB_STDLIBS = ("Printf", "LinearAlgebra", "Random", "Base64", "Dates")
using Printf
using LinearAlgebra
using Random
using Dates

# --------------------------------------------------------------- цвет
const NSB_TTY_STDOUT = Ref(false)
const NSB_TTY_STDERR = Ref(false)
const NSB_COLOR = Ref(false)
const NSB_TRUECOLOR = Ref(false)

function nsb_detect_terminal!()
    NSB_TTY_STDOUT[] = isa(stdout, Base.TTY)
    NSB_TTY_STDERR[] = isa(stderr, Base.TTY)
    no_color = haskey(ENV, "NO_COLOR") && !isempty(ENV["NO_COLOR"])
    term_ok = haskey(ENV, "TERM") && ENV["TERM"] != "dumb"
    NSB_COLOR[] = NSB_TTY_STDOUT[] && term_ok && !no_color
    ct = get(ENV, "COLORTERM", "")
    NSB_TRUECOLOR[] = NSB_COLOR[] && (ct == "truecolor" || ct == "24bit" ||
        occursin("truecolor", ct))
    return nothing
end

# --------------------------------------------------------------- конфиг
mutable struct NsbConfig
    lang::Symbol                 # :ru | :en
    out_dir::String
    dpi::Int                     # разрешение графиков (по умолчанию 600)
    seed::Int
    color::Bool
    max_n::Int                   # верхняя граница N по памяти этой машины
    quick::Bool
    batch::Bool                  # non-interactive режим
    quiet::Bool
    log_io::Union{Nothing,IOStream}
    t_start::DateTime
end

const NSB_CFG = Ref{NsbConfig}()

function nsb_default_config()
    # запас по памяти: ~22 комплексных поля N^3 * 16 байт * 1.6 (рабочие)
    total_gb = Sys.total_memory() / 2^30
    max_n = 32
    for cand in (32, 64, 128, 256)
        mem_gb = cand^3 * 16 * 24 / 2^30
        if mem_gb < total_gb * 0.55
            max_n = cand
        end
    end
    NsbConfig(:ru, "nsb_lab_results", 600, 20260916, true, max_n, false, false, false,
              nothing, now())
end

function nsb_ensure_outdirs!()
    cfg = NSB_CFG[]
    for sub in ("", "/logs", "/data", "/plots", "/reports", "/articles")
        p = cfg.out_dir * sub
        isdir(p) || mkpath(p)
    end
    return nothing
end

function nsb_logfile_open!()
    cfg = NSB_CFG[]
    stamp = Dates.format(now(), "yyyymmdd_HHMMSS")
    path = joinpath(cfg.out_dir, "logs", "session_$stamp.log")
    cfg.log_io = open(path, "a")
    return path
end

"Двойной вывод: в stdout (если не quiet) и в лог-файл сессии."
function nsb_print(s::AbstractString)
    cfg = NSB_CFG[]
    if !cfg.quiet
        print(s)
        flush(stdout)
    end
    if cfg.log_io !== nothing
        write(cfg.log_io, replace(s, "\e" => "\\e"))
        flush(cfg.log_io)
    end
    return nothing
end
nsb_println(s::AbstractString = "") = nsb_print(s * "\n")

function nsb_log_close!()
    cfg = NSB_CFG[]
    if cfg.log_io !== nothing
        close(cfg.log_io)
        cfg.log_io = nothing
    end
    return nothing
end

# --------------------------------------------------------------- машина
struct NsbMachine
    cpu::String
    threads::Int
    mem_gb::Float64
    julia::String
end

function nsb_machine()
    cpu = try
        si = Sys.cpu_info()
        isempty(si) ? "CPU" : si[1].model
    catch
        "CPU"
    end
    NsbMachine(cpu, Threads.nthreads(), Sys.total_memory() / 2^30, string(VERSION))
end
