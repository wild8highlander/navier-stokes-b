#!/usr/bin/env julia
# -*- coding: utf-8 -*-
#=
verify_ns_full.jl — объёмный самодостаточный верификатор репозитория
Navier-Stokes-B: Julia-адаптер того же контракта §0–§26, что и у
verify_ns_full.py (см. Python-версию: та же математика, те же задачи
1–10, те же отчёты; отличия — только в адаптере языка, §24), плюс
Julia-специфичный блок §27: 3D-слоистая b-поправка (задачи 11–15).

Только стандартная библиотека Julia 1.6+ (zero external packages,
zero codegen, zero network). Режимы (§29): TUI-меню по умолчанию в TTY
(и по --menu) · прямой прогон (--ci, --task, pipe, include-в-pipe) ·
прежнее плоское меню --menu-legacy · CLI c --ci.

АДАПТЕР ЯЗЫКА (§24, Julia):
| Концепт            | Реализация здесь                                          |
|--------------------|-----------------------------------------------------------|
| Запуск             | julia verify_ns_full.jl                                   |
| Include guard      | `if !isdefined(@__MODULE__, :VFAUI)` — повторный include   |
|                    | пересоздаёт слои, не перезапуская сессию (§2 self-healing) |
| Точка входа        | `abspath(PROGRAM_FILE) == @__FILE__ || isinteractive()`   |
| GC между задачами  | GC.gc(true) ×2 + ccall(:malloc_trim) на Linux (§10.1)      |
| In-place eig       | задачам не требуется; не эмитится                          |
| /proc, /sys        | read(path, String) с try/catch («—» если нет, Termux-safe) |
| rlimit             | ccall(:setrlimit) best-effort; нет — ERR_UNSUPPORTED (§1.4)|
| Сжатие             | zlib в stdlib Julia НЕТ → PNG через собственный zlib-обёртку|
|                    | с DEFLATE stored-блоками + adler32 (валидный PNG, §1.4 WARN)|
| Config-file        | TOML (stdlib); JSON-парсера в stdlib нет → ERR_UNSUPPORTED |
| DOCX               | zip-writer в stdlib Julia нет → ERR_UNSUPPORTED (md/html/pdf)|
| Сигналы            | SIGINT → InterruptException (try/catch); SIGTERM/USR1 —    |
|                    | best-effort ccall(:signal); не удалось — ERR_UNSUPPORTED   |
| Completions        | print-heredoc bash/zsh/fish                               |

Кросс-языковая перепроверка: задачи 1–7 считают те же величины, что и
Python-монолит (b, θ_b, C_s, Кассини, KdV, Родриг, Кирхгоф), task 9 —
встречная сверка: Python вызывает Julia, Julia-версия при совместном
запуске может сверяться с results/run_*/results.json Python-прогона.
=#

module VFAUI
    export paint, badge, box_lines, bar_line, erase_line, state, detect!,
           sticker, aurora_sep, aurora_title, sparkline_verdict

    state = Dict(:color => true, :unicode => true, :theme => "aurora")

    THEMES = Dict(
        "aurora"  => ("\x1b[48;5;236m", "\x1b[38;5;252m", "\x1b[38;5;75m",
                      "\x1b[38;5;114m", "\x1b[38;5;179m", "\x1b[38;5;174m"),
        "ice"     => ("\x1b[48;5;235m", "\x1b[38;5;254m", "\x1b[38;5;117m",
                      "\x1b[38;5;122m", "\x1b[38;5;151m", "\x1b[38;5;210m"),
        "gold"    => ("\x1b[48;5;234m", "\x1b[38;5;229m", "\x1b[38;5;220m",
                      "\x1b[38;5;120m", "\x1b[38;5;214m", "\x1b[38;5;203m"),
        "emerald" => ("\x1b[48;5;233m", "\x1b[38;5;250m", "\x1b[38;5;85m",
                      "\x1b[38;5;84m", "\x1b[38;5;185m", "\x1b[38;5;167m"))
    RESET = "\x1b[0m"

    # §4.1 aurora-стикеры: плавающий декор для баннера, меню и вердиктов
    const STICKERS = ["✦", "❋", "✺", "❊", "✿", "✦", "✧", "❃"]

    function detect!()
        if haskey(ENV, "NO_COLOR") || get(ENV, "TERM", "") == "dumb"
            state[:color] = false
        end
        return state
    end

    function set_unicode!(mode::AbstractString)
        state[:unicode] = mode == "on" ? true :
                          mode == "off" ? false :
                          occursin("utf", lowercase(get(ENV, "LANG", "")))
        return state
    end

    ccolor(idx::Int) = state[:color] ? get(THEMES, state[:theme], THEMES["aurora"])[idx] : ""
    paint(text::AbstractString, idx::Int) = state[:color] ? ccolor(idx) * text * RESET : String(text)
    badge(v::AbstractString) = paint("[$v]", v in ("PASS", "DONE") ? 4 : v in ("FAIL", "ERROR") ? 6 : 5)

    "Aurora-стикер по индексу: символ из STICKERS + цвет темы (idx→mod1(i,6))"
    function sticker(i::Int)
        sym = STICKERS[mod1(i, length(STICKERS))]
        return state[:color] ? ccolor(mod1(i, 6)) * sym * RESET : sym
    end

    "Aurora-разделитель: ╭─╮ с бегущими точками и искрами (phase — фаза бега)"
    function aurora_sep(width::Int = 66; phase::Int = 0)
        state[:unicode] || return "+" * "-"^(width - 2) * "+"
        c = state[:color]
        spk = c ? ccolor(3) * "✦" * RESET : "✦"
        out = IOBuffer()
        print(out, c ? ccolor(3) * "╭" * RESET : "╭")
        for i in 1:width - 2
            if mod(i + phase, 8) == 0
                print(out, spk)
            elseif mod(i + phase, 4) == 0
                print(out, "·")
            else
                print(out, "─")
            end
        end
        print(out, c ? ccolor(3) * "╮" * RESET : "╮")
        return String(take!(out))
    end

    "Плавающий заголовок: буквы в aurora-градиенте, по стикеру с каждого края"
    function aurora_title(text::AbstractString; accent::Int = 3, deco::Bool = true)
        u = state[:unicode]
        col = state[:color]
        buf = IOBuffer()
        if deco && u
            print(buf, "  ", sticker(1), " ")
        end
        for (i, ch) in enumerate(text)
            if col
                print(buf, ccolor(accent + (i % 3)), ch)
            else
                print(buf, ch)
            end
        end
        col && print(buf, RESET)
        if deco && u
            print(buf, " ", sticker(5))
        end
        return String(take!(buf))
    end

    "Мини-вердикт со спарклайн-скобками (для CI-логов — ASCII при !unicode)"
    function sparkline_verdict(verdict::AbstractString)
        state[:unicode] || return "[$verdict]"
        return verdict in ("PASS", "DONE") ? "✦[" * verdict * "]✦" :
               verdict in ("FAIL", "ERROR") ? "❋[" * verdict * "]❋" :
               "✺[" * verdict * "]✺"
    end

    function box_lines(lines::Vector{<:AbstractString}, width::Int = 66)
        u = state[:unicode]
        c = state[:color]
        if !u
            top = "+" * "-"^(width - 2) * "+"
            out = [top]
            for ln in lines
                body = first(ln, min(length(ln), width - 4))
                push!(out, "| " * rpad(body, width - 4) * " |")
            end
            push!(out, "+" * "-"^(width - 2) * "+")
            return out
        end
        # aurora: скруглённые углы + бегущие искры по верхней кромке;
        # RESET только на концах строки — иначе ANSI-коды ломают ширину
        tl, tr, bl, br, hz, vt = "╭", "╮", "╰", "╯", "─", "│"
        spk = c ? ccolor(3) * "✦" * ccolor(2) : "✦"
        top = c ? ccolor(3) * tl * ccolor(2) : tl
        for i in 1:width - 2
            top *= (mod(i, 6) == 0 ? spk : hz)
        end
        top *= (c ? ccolor(3) * tr * RESET : tr)
        out = [top]
        for ln in lines
            body = first(ln, min(length(ln), width - 4))
            pad = rpad(body, width - 4)
            lbar = c ? ccolor(3) * vt * RESET : vt
            push!(out, lbar * " " * pad * " " * lbar)
        end
        bot = (c ? ccolor(3) * bl * ccolor(2) : bl) * hz^(width - 2) *
              (c ? ccolor(3) * br * RESET : br)
        push!(out, bot)
        return out
    end

    function bar_line(done::Int, total::Int, label::AbstractString = "",
                      monitor::AbstractString = "", t0::Float64 = 0.0)
        width = 72
        frac = total <= 0 ? 0.0 : min(1.0, done / total)
        # B1: длинный monitor уводил (width-20-len)*frac в минус → "█"^filln
        # бросал DomainError; клампим и ширину, и заполнение
        avail = max(4, width - 20 - length(monitor))
        filln = clamp(round(Int, avail * frac), 0, avail)
        remn = avail - filln
        u = state[:unicode]
        c = state[:color]
        fill_ch = u ? "█" : "#"
        empty_ch = u ? "·" : "-"
        if c
            # aurora-пульс: заполнение бежит тремя цветами темы
            buf = IOBuffer()
            stepn = max(1, filln ÷ 3)
            for i in 1:filln
                print(buf, ccolor(3 + ((i - 1) ÷ stepn) % 3), fill_ch)
            end
            print(buf, ccolor(2), empty_ch^remn, RESET)
            glyph = String(take!(buf))
        else
            glyph = fill_ch^filln * empty_ch^remn
        end
        eta = ""
        if frac > 0.02 && t0 > 0
            el = time() - t0
            eta = " eta $(round(max(0.0, el / frac - el); digits = 0))s"
        end
        tag = u && c ? ccolor(4) * "✦" * RESET : ">"
        return "\r$tag $glyph $done/$total $(first(label, 14))$monitor$eta   "
    end

    function erase_line()
        print(stderr, "\r", " "^72, "\r")
        flush(stderr)
    end
end

# ═══════════════════════════════════════════════════════════════════════════
# §28 ASCII-баннер: печатается первым в vfa_main, до help/version/справок.
# Подавляется --plain, --ci, --quiet, --banner=never, NO_COLOR/TERM=dumb.
# Модуль объявлен ДО VFAMon/VFAUI-доступа из других модулей → ссылки через
# Main.* (разрешение в момент вызова).
# ═══════════════════════════════════════════════════════════════════════════

module VFABanner
    export show_banner!, banner_lines

    const ART_UNICODE = [
        "██╗   ██╗███████╗ █████╗ ",
        "██║   ██║██╔════╝██╔══██╗",
        "██║   ██║█████╗  ███████║",
        "╚██╗ ██╔╝██╔══╝  ██╔══██║",
        " ╚████╔╝ ██║     ██║  ██║",
        "  ╚═══╝  ╚═╝     ╚═╝  ╚═╝",
    ]
    const ART_PLAIN = [
        "V   V FFFFF AAAAA",
        "V   V F     A   A",
        "V   V FFF   AAAAA",
        " V V  F     A   A",
        "  V   F     A   A",
    ]

    function banner_lines(; plain::Bool = false, subtitle::AbstractString = "")
        art = plain ? ART_PLAIN : ART_UNICODE
        sep = plain ? "|" : "·"      # plain → ASCII-only (проверяет самотест)
        lines = collect(art)
        push!(lines, "")
        push!(lines, "  Navier-Stokes-B " * sep * " full verification")
        isempty(subtitle) || push!(lines, "  " * subtitle)
        push!(lines, "  julia " * string(VERSION) * " " * sep * " " *
                     Main.VFAMon.platform_tag() * " " * sep * " v1.3.1")
        return lines
    end

    "Печать баннера; цвет — акцент темы (idx 3), без цвета — чистый текст."
    function show_banner!(; plain::Bool = false, color::Bool = true,
                          subtitle::AbstractString = "")
        for line in banner_lines(plain = plain, subtitle = subtitle)
            println(color ? Main.VFAUI.paint(line, 3) : line)
        end
        println()
        return nothing
    end
end


# §2/§23.9 self-healing: все слои — модули одного файла; повторный
# include("verify_ns_full.jl") в REPL пересоздаёт их определения тихо
# (идемпотентно), сессия не перезапускается.

module VFAMon
    export snapshot, inline_str, panel, platform_tag

    function readfile(path::AbstractString)
        try
            return read(path, String)
        catch
            return ""
        end
    end

    platform_tag() = Sys.islinux() ? (occursin("com.termux", lowercase(get(ENV, "PREFIX", ""))) ?
                                      "termux" : "linux") :
                     Sys.isapple() ? "macos" : Sys.iswindows() ? "windows" : "other"

    _cpu_prev = Ref{Tuple{Int, Int}}((0, 0))

    function snapshot()
        d = Dict{String, Any}("cpu_percent" => nothing, "ram_used_gb" => nothing,
                              "ram_total_gb" => nothing, "temp_c" => nothing,
                              "io_latency_us" => nothing, "uptime_s" => nothing)
        stat = readfile("/proc/stat")
        for line in split(stat, '\n')
            if startswith(line, "cpu ")
                f = split(line)
                length(f) >= 5 || continue   # урезанный /proc/stat (sandbox)
                p = parse.(Int, f[2:min(length(f), 9)])
                total, idle = sum(p), p[4] + p[5]
                prev = _cpu_prev[]
                _cpu_prev[] = (total, idle)
                if prev[1] > 0
                    dt, di = total - prev[1], idle - prev[2]
                    dt > 0 && (d["cpu_percent"] = 100.0 * (dt - di) / dt)
                end
                break
            end
        end
        mem = readfile("/proc/meminfo")
        if occursin("MemTotal", mem)
            vals = Dict{String, Int}()
            for line in split(mem, '\n')
                parts = split(line, ":"; limit = 2)
                length(parts) == 2 || continue
                key, rest = parts
                f = split(strip(rest))
                isempty(f) || (vals[strip(key)] = parse(Int, first(f)))
            end
            haskey(vals, "MemTotal") || (vals["MemTotal"] = 0)
            d["ram_total_gb"] = vals["MemTotal"] / 1048576.0
            d["ram_used_gb"] = (vals["MemTotal"] - get(vals, "MemAvailable", 0)) / 1048576.0
        end
        upt = readfile("/proc/uptime")
        if occursin(".", upt)
            d["uptime_s"] = parse(Float64, first(split(upt)))
        end
        t = time()
        readfile("/proc/self/io")
        d["io_latency_us"] = (time() - t) * 1e6
        return d
    end

    function cell(v, suffix::AbstractString)
        v === nothing && return "—"
        return "$(round(v; digits = 1))$suffix"
    end

    inline_str(s) = " [$(cell(s["cpu_percent"], "%")) cpu $(cell(s["ram_used_gb"], "G")) ram $(cell(s["temp_c"], "C"))]"

    function panel()
        s = snapshot()
        return ["MONITOR: cpu $(cell(s["cpu_percent"], "%")) | ram $(cell(s["ram_used_gb"], "G")) | " *
                "temp $(cell(s["temp_c"], "C")) | platform $(platform_tag())"]
    end
end

module VFALog
import ..VFAUI
    export init_run!, open_task!, close_task!, log_comp, log_result, finish!,
           tee_start, tee_stop, prog_heartbeat, G

    mutable struct Run
        run_dir::Union{String, Nothing}
        task_dir::Union{String, Nothing}
        comp::Vector{String}
        events::Vector{String}
        verdicts::Dict{Int, Dict}
        t0::Float64
        ci::Bool
        current_task::String
        heartbeat::Float64
        ctl_path::Union{String, Nothing}
        aborted::Bool
        paused::Bool
        snapshot_req::Bool
        quiet::Bool
    end

    G = Run(nothing, nothing, String[], String[], Dict{Int, Dict}(), time(),
            false, "idle", time(), nothing, false, false, false, false)

    log_comp(msg::AbstractString, level::AbstractString = "info") = begin
        now = Libc.strftime("%H:%M:%S", time())
        delta = time() - G.t0
        push!(G.comp, "[$now] [+$(round(delta; digits = 3))s] $msg")
        ev = """{"ts":"$(Libc.strftime("%Y-%m-%dT%H:%M:%S", time()))","level":"$level","task":"$(G.current_task)","msg":"$(json_escape(String(msg)))"}"""
        push!(G.events, ev)
        G.ci && (println(stdout, ev); flush(stdout))
        G.heartbeat = time()
        nothing
    end

    json_escape(s::AbstractString) = replace(s, "\\" => "\\\\", "\"" => "\\\"",
                                             "\n" => "\\n", "\t" => "\\t")

    function log_result(task_id::Int, slug::AbstractString, verdict::AbstractString,
                        reason::AbstractString = "", metrics::Dict = Dict{String, Any}(),
                        duration::Real = 0.0, artifacts::Vector{String} = String[])
        # G.quiet (§B3): внутренние прогоны task10 не перезаписывают вердикты
        if !G.quiet
            G.verdicts[task_id] = Dict("slug" => slug, "verdict" => verdict,
                                       "reason" => reason, "metrics" => metrics,
                                       "duration_s" => round(Float64(duration); digits = 3),
                                       "artifacts" => artifacts)
        end
        line = "task $(lpad(task_id, 2, '0')) [$slug] $verdict" *
               (isempty(reason) ? "" : " $reason")
        log_comp(line, "verdict")
        return get(G.verdicts, task_id, Dict{String, Any}())
    end

    function init_run!(run_dir::AbstractString; ci::Bool = false)
        G.run_dir = run_dir
        G.ci = ci
        mkpath(joinpath(run_dir, "logs"))
        empty!(G.comp); empty!(G.events); empty!(G.verdicts)
        G.t0 = time()
        G.heartbeat = time()
        G.aborted = false
        G.paused = false
        G.snapshot_req = false
        G.quiet = false
        log_comp("run opened: $run_dir")
        return G
    end

    open_task!(task_dir::AbstractString, slug::AbstractString) = begin
        G.task_dir = task_dir
        G.current_task = slug
        mkpath(joinpath(task_dir, "logs"))
        mkpath(joinpath(task_dir, "plots"))
        G.heartbeat = time()
    end

    close_task!() = (G.current_task = "idle"; G.task_dir = nothing)

    tee_start() = nothing      # §23.1: no-op заглушки в Julia-адаптере
    tee_stop() = nothing
    prog_heartbeat() = (G.heartbeat = time(); nothing)

    function finish!()
        G.run_dir === nothing && return nothing
        open(joinpath(G.run_dir, "logs", "events.jsonl"), "w") do fh
            for e in G.events
                println(fh, e)
            end
        end
        open(joinpath(G.run_dir, "logs", "computation_log.txt"), "w") do fh
            for l in G.comp
                println(fh, l)
            end
        end
        return nothing
    end
end

# §23.1: побайтовый tee-ридер stdout удалён — redirect_stdout глотает
# вывод задач и конфликтует с --ci; заглушки tee_start/tee_stop сохранены.

module VFAPlot
    export Canvas, RepPlot, save_png, save_gif, render_plot, draw_text, FONT3X5

    # 3×5 шрифт (15 бит/глиф, снизу вверх) — тот же, что в Python-версии
    FONT3X5 = Dict{Char, UInt16}(
        ' ' => 0b000000000000000, '!' => 0b010010010000010, '0' => 0b111100101101111,
        '1' => 0b010110010010111, '2' => 0b111001111100111, '3' => 0b111001111001111,
        '4' => 0b101101111001001, '5' => 0b111100111001111, '6' => 0b111100111101111,
        '7' => 0b111001001010010, '8' => 0b111101111101111, '9' => 0b111101111001111,
        'A' => 0b010101111101101, 'B' => 0b110101110101110, 'C' => 0b011100100100011,
        'D' => 0b110101101101110, 'E' => 0b111100110100111, 'F' => 0b111100110100100,
        'G' => 0b011100101101011, 'H' => 0b101101111101101, 'I' => 0b111010010010111,
        'J' => 0b001001001101010, 'K' => 0b101101110101101, 'L' => 0b100100100100111,
        'M' => 0b101111111101101, 'N' => 0b110101101101101, 'O' => 0b010101101101010,
        'P' => 0b110101110100100, 'Q' => 0b010101101110011, 'R' => 0b110101110101101,
        'S' => 0b011100010100110, 'T' => 0b111010010010010, 'U' => 0b101101101101111,
        'V' => 0b101101101101010, 'W' => 0b101101111111101, 'X' => 0b101101010101101,
        'Y' => 0b101101010010010, 'Z' => 0b111001010100111, '.' => 0b000000000000010,
        ',' => 0b000000000010010, '-' => 0b000000111000000, '+' => 0b000010111010000,
        '=' => 0b000111000111000, '(' => 0b001010010010001, ')' => 0b100010010010100,
        ':' => 0b000010000010000, '/' => 0b001001010100100, '%' => 0b101001001010001,
        '?' => 0b111001010000010, '_' => 0b000000000000111)

    mutable struct Canvas
        w::Int
        h::Int
        buf::Vector{UInt8}
        Canvas(w, h, bg::Tuple{Int, Int, Int}) = new(w, h, repeat(UInt8[bg...], w * h))
    end

    function px!(c::Canvas, x, y, col::Tuple{Int, Int, Int})
        0 <= x < c.w && 0 <= y < c.h || return nothing
        i = 3 * (y * c.w + x) + 1
        c.buf[i] = col[1]; c.buf[i + 1] = col[2]; c.buf[i + 2] = col[3]
        return nothing
    end

    function rect!(c::Canvas, x0, y0, x1, y1, col::Tuple{Int, Int, Int})
        for y in max(0, y0):min(c.h - 1, y1), x in max(0, x0):min(c.w - 1, x1)
            px!(c, x, y, col)
        end
        return nothing
    end

    function line!(c::Canvas, x0, y0, x1, y1, col::Tuple{Int, Int, Int}, thick = 1)
        dx, dy = abs(x1 - x0), -abs(y1 - y0)
        sx = x0 < x1 ? 1 : -1
        sy = y0 < y1 ? 1 : -1
        err = dx + dy
        while true
            px!(c, x0, y0, col)
            (x0 == x1 && y0 == y1) && break
            e2 = 2 * err
            if e2 >= dy
                err += dy; x0 += sx
            end
            if e2 <= dx
                err += dx; y0 += sy
            end
        end
        return nothing
    end

    function draw_text(c::Canvas, text::AbstractString, x0, y0,
                       col::Tuple{Int, Int, Int}, scale = 1)
        cx = x0
        for ch in text
            g = get(FONT3X5, uppercase(ch), FONT3X5['?'])
            ch == ' ' && (cx += 4 * scale; continue)
            for bit in 0:14
                (g >> bit) & 1 == 1 || continue
                gx, gy = bit % 3, 4 - div(bit, 3)
                rect!(c, cx + gx * scale, y0 + gy * scale,
                      cx + gx * scale + scale - 1, y0 + gy * scale + scale - 1, col)
            end
            cx += 4 * scale
        end
        return nothing
    end

    # собственный CRC32 (§9) — stdlib Julia не экспортирует zlib.crc32
    _CRC = let tbl = Vector{UInt32}(undef, 256)
        for n in 0:255
            c = UInt32(n)
            for _ in 1:8
                c = (c & 1 == 1) ? (0xEDB88320 ⊻ (c >> 1)) : (c >> 1)
            end
            tbl[n + 1] = c
        end
        tbl
    end
    crc32(data::Vector{UInt8}) = begin
        c = 0xFFFFFFFF
        for b in data
            c = _CRC[((c ⊻ b) & 0xFF) + 1] ⊻ (c >> 8)
        end
        c ⊻ 0xFFFFFFFF
    end
    crc32(s::AbstractString) = crc32(Vector{UInt8}(codeunits(s)))

    # zlib-обёртка с DEFLATE stored-блоками (§1.4: zlib API в stdlib Julia
    # недоступен → валидный несжатый PNG; WARN в лог при сохранении)
    function zlib_stored(data::Vector{UInt8})
        out = UInt8[0x78, 0x01]                      # zlib header
        n = length(data)
        i = 1
        while true
            chunk = min(65535, n - i + 1)
            last = i + chunk - 1 >= n ? 1 : 0
            push!(out, UInt8(last))
            push!(out, UInt8(chunk & 0xFF), UInt8((chunk >> 8) & 0xFF))
            push!(out, UInt8((~chunk) & 0xFF), UInt8(((~chunk) >> 8) & 0xFF))
            append!(out, data[i:i + chunk - 1])
            i += chunk
            i > n && break
        end
        a, b = UInt32(1), UInt32(0)
        for byte in data
            a = (a + byte) % 65521
            b = (b + a) % 65521
        end
        adler = (b << 16) | a
        append!(out, reinterpret(UInt8, [hton(adler)]))
        return out
    end

    function save_png(path::AbstractString, c::Canvas)
        w, h = c.w, c.h
        raw = UInt8[]
        for y in 0:h - 1
            push!(raw, UInt8(0))                     # фильтр 0 (None): stored-deflate
            # B2: @view вместо копии среза; B-NEW-7: база строки — явные
            # умножения (y*3w-конкатенация хрупка при рефакторинге)
            base = y * 3 * w
            append!(raw, @view c.buf[(base + 1):(base + 3 * w)])
        end
        ihdr = vcat(reinterpret(UInt8, [hton(UInt32(w))]),
                    reinterpret(UInt8, [hton(UInt32(h))]), UInt8[8, 2, 0, 0, 0])
        sig = UInt8[0x89, 0x50, 0x4E, 0x47, 0x0D, 0x0A, 0x1A, 0x0A]
        chunk(tag::Vector{UInt8}, body::Vector{UInt8}) =
            vcat(reinterpret(UInt8, [hton(UInt32(length(body)))]), tag, body,
                 reinterpret(UInt8, [hton(crc32(vcat(tag, body)))]))
        data = vcat(sig,
                    chunk(UInt8[0x49, 0x48, 0x44, 0x52], ihdr),
                    chunk(UInt8[0x49, 0x44, 0x41, 0x54], zlib_stored(raw)),
                    chunk(UInt8[0x49, 0x45, 0x4E, 0x44], UInt8[]))
        open(path, "w") do fh
            write(fh, data)
        end
        return path
    end

    # LZW для GIF89a — тот же алгоритм, что в Python-версии (LSB-first, 9→12).
    # v1.3.1: рост ширины кода — ПОСЛЕ добавления записи со значением 2^cs
    # (nxt == (1<<cs)+1): декодер добавляет записи на один код позже энкодера,
    # ранний bump рассинхронизировал поток (PIL: broken data stream).
    function lzw(indices::Vector{UInt8}, min_code_size::Int = 8)
        clear = 1 << min_code_size
        eoi = clear + 1
        dict = Dict{Vector{UInt8}, Int}(Vector{UInt8}([UInt8(i)]) => i for i in 0:clear - 1)
        nxt, cs = eoi + 1, min_code_size + 1
        bits = Tuple{Int, Int}[(clear, cs)]
        w = UInt8[]
        for ch in indices
            wc = vcat(w, UInt8[ch])
            if haskey(dict, wc)
                w = wc
                continue
            end
            push!(bits, (dict[w], cs))
            if nxt >= 4096
                push!(bits, (clear, cs))
                dict = Dict{Vector{UInt8}, Int}(Vector{UInt8}([UInt8(i)]) => i for i in 0:clear - 1)
                nxt, cs = eoi + 1, min_code_size + 1
            else
                dict[wc] = nxt
                nxt += 1
                if nxt == (1 << cs) + 1 && cs < 12
                    cs += 1
                end
            end
            w = UInt8[ch]
        end
        isempty(w) || push!(bits, (dict[w], cs))
        push!(bits, (eoi, cs))
        out = UInt8[]
        acc, nb = 0, 0
        for (code, width) in bits
            acc |= code << nb
            nb += width
            while nb >= 8
                push!(out, UInt8(acc & 0xFF))
                acc >>= 8
                nb -= 8
            end
        end
        nb > 0 && push!(out, UInt8(acc & 0xFF))
        return out
    end

    # Референсный GIF-LZW декодер, парный к lzw (selftest §9, v1.3.1):
    # запись добавляется при приёме каждого кода (кроме первого после CLEAR),
    # ширина растёт, когда next_code декодера достигает 1<<cs. Round-trip
    # в selftest ловит любой рассинхрон ширины без внешних декодеров.
    function lzw_decode_ref(data::Vector{UInt8}, min_code_size::Int,
                            n_expect::Int)
        clear = 1 << min_code_size
        eoi = clear + 1
        table = Dict{Int, Vector{UInt8}}(i => UInt8[i] for i in 0:clear - 1)
        cs, nxt = min_code_size + 1, eoi + 1
        out = UInt8[]
        prev = nothing
        acc, nb, pos = 0, 0, 1
        while true
            while nb < cs
                pos > length(data) && error("LZW: поток кончился до EOI")
                acc |= Int(data[pos]) << nb
                pos += 1
                nb += 8
            end
            code = acc & ((1 << cs) - 1)
            acc >>= cs
            nb -= cs
            if code == clear
                table = Dict{Int, Vector{UInt8}}(i => UInt8[i] for i in 0:clear - 1)
                nxt, cs = eoi + 1, min_code_size + 1
                prev = nothing
                continue
            elseif code == eoi
                break
            end
            if prev === nothing
                entry = table[code]
            else
                entry = haskey(table, code) ? table[code] : vcat(prev, prev[1:1])
                if nxt < 4096
                    table[nxt] = vcat(prev, entry[1:1])
                    nxt += 1
                    if nxt == (1 << cs) && cs < 12
                        cs += 1
                    end
                end
            end
            append!(out, entry)
            prev = entry
            length(out) > n_expect && break
        end
        return out
    end

    function save_gif(path::AbstractString, frames::Vector{Canvas}; delay_cs = 2)
        isempty(frames) && return path
        w, h = frames[1].w, frames[1].h
        # B7: палитра объявляет 256 цветов (0xF7), но была заполнена только
        # 12; квантование тёмных пикселей (bg 18,20,28) проваливалось в чёрный
        # (0,0,0). Расширяем: тёмный фон, промежуточные тона, белый.
        pal_rgb = [(12, 14, 22), (18, 20, 28), (26, 29, 40), (40, 44, 60),
                   (55, 60, 80), (90, 95, 115), (150, 160, 190),
                   (220, 225, 240), (255, 255, 255),
                   (80, 170, 255), (255, 140, 105), (110, 220, 150),
                   (200, 150, 255), (255, 210, 90), (90, 230, 220),
                   (160, 120, 200)]
        palette = UInt8[]
        for rgb in pal_rgb
            append!(palette, UInt8.(collect(rgb)))
        end
        append!(palette, zeros(UInt8, 768 - length(palette)))
        out = IOBuffer()
        write(out, "GIF89a")
        write(out, UInt8.(vcat(reinterpret(UInt8, [UInt16(w)]),
                               reinterpret(UInt8, [UInt16(h)]), [0xF7, 0x00, 0x00])))
        write(out, palette)
        write(out, UInt8[0x21, 0xFF, 0x0B]); write(out, "NETSCAPE2.0")
        write(out, UInt8[0x03, 0x01, 0x00, 0x00, 0x00])
        for fr in frames
            idx = zeros(UInt8, w * h)
            for p in 1:w * h
                r, g, b = Int(fr.buf[3p - 2]), Int(fr.buf[3p - 1]), Int(fr.buf[3p])
                best, bd = 0, typemax(Int)
                # B3: `pi` затенял Base.pi на всю область цикла — хрупко;
                # переименовали в cidx
                for (cidx, pr) in enumerate(pal_rgb)
                    d = (r - pr[1])^2 + (g - pr[2])^2 + (b - pr[3])^2
                    d < bd && (best, bd = cidx - 1, d)
                end
                idx[p] = UInt8(best)
            end
            write(out, UInt8[0x21, 0xF9, 0x04, 0x04, delay_cs & 0xFF,
                              (delay_cs >> 8) & 0xFF, 0x00, 0x00])
            write(out, UInt8[0x2C])
            write(out, UInt8.(vcat(reinterpret(UInt8, [UInt16(0), UInt16(0), UInt16(w), UInt16(h)]), [0x00])))
            lzwdata = lzw(idx, 8)
            write(out, UInt8(8))
            i = 1
            while i <= length(lzwdata)
                blk = lzwdata[i:min(i + 254, end)]
                write(out, UInt8(length(blk))); write(out, blk)
                i += 255
            end
            write(out, UInt8(0))
        end
        write(out, UInt8(0x3B))
        open(path, "w") do fh
            write(fh, take!(out))
        end
        return path
    end

    mutable struct RepPlot
        title::String
        xlabel::String
        ylabel::String
        series::Vector{Tuple{String, Vector{Float64}, Vector{Float64}, Char}}
        infobox::Vector{String}
    end
    RepPlot(title, xl = "", yl = "") = RepPlot(title, xl, yl,
        Tuple{String, Vector{Float64}, Vector{Float64}, Char}[], String[])
    add_series!(p::RepPlot, name, xs, ys, style = 'l') =
        (push!(p.series, (name, collect(Float64.(xs)), collect(Float64.(ys)), style)); p)

    const THEMES = Dict(
        "aurora" => Dict("bg" => (18, 20, 28), "panel" => (26, 29, 40),
                         "grid" => (55, 60, 80), "axis" => (150, 160, 190),
                         "text" => (220, 225, 240),
                         "series" => [(80, 170, 255), (255, 140, 105), (110, 220, 150),
                                      (200, 150, 255), (255, 210, 90), (90, 230, 220)]),
        "light"  => Dict("bg" => (250, 250, 247), "panel" => (255, 255, 255),
                         "grid" => (225, 225, 220), "axis" => (60, 60, 60),
                         "text" => (30, 30, 30),
                         "series" => [(31, 119, 180), (214, 39, 40), (44, 160, 44)]))

    function render_plot(p::RepPlot, theme = "aurora"; width = 760, height = 440, ss = 2)
        th = get(THEMES, theme, THEMES["aurora"])
        W, H = width * ss, height * ss
        cv = Canvas(W, H, th["bg"])
        rect!(cv, ss, ss, W - ss - 1, H - ss - 1, th["panel"])
        ml, mr, mt, mb = 64ss, 18ss, 40ss, 44ss
        x0, y0, x1, y1 = ml, mt, W - mr, H - mb
        xs_all = Float64[]; ys_all = Float64[]
        for (_, xs, ys, _) in p.series
            append!(xs_all, xs); append!(ys_all, ys)
        end
        (isempty(xs_all) || isempty(ys_all)) && (xs_all = [0.0, 1.0]; ys_all = [0.0, 1.0])
        xmin, xmax = minimum(xs_all), maximum(xs_all)
        ymin, ymax = minimum(ys_all), maximum(ys_all)
        xmax - xmin < 1e-300 && (xmax = xmin + 1.0)
        ymax - ymin < 1e-300 && (ymax = ymin + 1.0)
        dx, dy = xmax - xmin, ymax - ymin
        xmin -= 0.06dx; xmax += 0.06dx; ymin -= 0.08dy; ymax += 0.08dy
        dx, dy = xmax - xmin, ymax - ymin
        # round(Int, …): Int() от дробного пикселя (271.2) = InexactError —
        # рендер падал на любой реальной серии (Python тут использует int())
        sx(v) = x0 + round(Int, (v - xmin) / dx * (x1 - x0))
        sy(v) = y1 - round(Int, (v - ymin) / dy * (y1 - y0))
        for k in 0:5
            fx, fy = xmin + dx * k / 5, ymin + dy * k / 5
            line!(cv, sx(fx), y0, sx(fx), y1, th["grid"])
            line!(cv, x0, sy(fy), x1, sy(fy), th["grid"])
            draw_text(cv, "$(round(fx; sigdigits = 4))", sx(fx) - 16ss, y1 + 6ss, th["axis"], ss)
            draw_text(cv, "$(round(fy; sigdigits = 4))", x0 - 46ss, sy(fy) - 3ss, th["axis"], ss)
        end
        line!(cv, x0, y0, x1, y0, th["axis"], 2)
        line!(cv, x0, y0, x0, y1, th["axis"], 2)
        draw_text(cv, p.title, x0, 10ss, th["text"], ss + 1)
        draw_text(cv, p.xlabel, (x0 + x1) ÷ 2 - 30ss, H - 26ss, th["text"], ss)
        for (i, ch) in enumerate(p.ylabel)
            draw_text(cv, string(ch), 8ss, y0 + (i - 1) * 12ss, th["text"], ss)
        end
        for (si, (name, xs, ys, style)) in enumerate(p.series)
            col = th["series"][(si - 1) % length(th["series"]) + 1]
            if style in ('l', 'L')
                for a in 1:length(xs) - 1
                    line!(cv, sx(xs[a]), sy(ys[a]), sx(xs[a + 1]), sy(ys[a + 1]), col,
                          style == 'L' ? 2ss : ss)
                end
            end
            if style in ('s', 'L')
                for a in 1:length(xs)
                    rect!(cv, sx(xs[a]) - 2ss, sy(ys[a]) - 2ss,
                          sx(xs[a]) + 2ss, sy(ys[a]) + 2ss, col)
                end
            end
        end
        if !isempty(p.infobox)
            bw = maximum(length(s) for s in p.infobox) * 6ss + 12ss
            bh = length(p.infobox) * 12ss + 8ss
            rect!(cv, x1 - bw, y1 - bh, x1, y1, th["panel"])
            for (i, s) in enumerate(p.infobox)
                draw_text(cv, s, x1 - bw + 6ss, y1 - bh + 5ss + (i - 1) * 12ss, th["text"], ss)
            end
        end
        # даунсэмпл ss×ss
        out = Canvas(width, height, (0, 0, 0))
        for y in 0:height - 1, x in 0:width - 1
            r = g = b = 0
            for j in 0:ss - 1, i in 0:ss - 1
                p0 = 3 * ((y * ss + j) * W + x * ss + i) + 1
                r += cv.buf[p0]; g += cv.buf[p0 + 1]; b += cv.buf[p0 + 2]
            end
            n = ss * ss
            q0 = 3 * (y * width + x) + 1
            out.buf[q0] = UInt8(r ÷ n); out.buf[q0 + 1] = UInt8(g ÷ n); out.buf[q0 + 2] = UInt8(b ÷ n)
        end
        return out
    end
end

# ═══════════════════════════════════════════════════════════════════════════
# §27 3D layered b-correction: ствол вихря дискретизируется по z на N слоёв;
# слой i несёт (h_i — высота над рельефом, W_i — ширина ядра, Γ_i —
# циркуляция) и свою поправку b_i = b∞·(1−e^(−h/h0))·1/(1+(W/W0)²).
# Пределы: h→0 ⇒ b→0 (вязкое подавление у поверхности); h→∞, W→0 ⇒ b=b∞
# (свободный вихрь); W→∞ ⇒ b→0 (широкое ядро, много мод).
# Синхронизация Кирхгоф↔Родриг: sin θ_i = b_i на каждом слое.
# ═══════════════════════════════════════════════════════════════════════════

module VFALayer3D
    export b_base, b_layer, b_rodrigues_layer, sync_residual,
           total_braking, layered_evolution, default_profile,
           radial_profile, layer_rodrigues_apply

    # Объёмное 2D-значение (Кирхгоф, треугольник); Float64 по построению —
    # побитово совпадает с vfa_b_float() главного модуля
    b_base() = 1 / (4π + 2√3)

    # Слоистая поправка: высота h и ширина W
    function b_layer(h::Real, W::Real; h0::Real = 1.0, W0::Real = 1.0)
        hf = 1 - exp(-h / h0)
        Wf = 1 / (1 + (W / W0)^2)
        return b_base() * hf * Wf
    end

    # Родриг: sin θ = b (непрерывный поворот, воспроизводящий b)
    function b_rodrigues_layer(h::Real, W::Real; kw...)
        b = b_layer(h, W; kw...)
        return sin(asin(b))   # = b, но явно через угол Родрига
    end

    sync_residual(h, W; kw...) =
        abs(b_layer(h, W; kw...) - b_rodrigues_layer(h, W; kw...))

    # Полное торможение ствола: τ = −∑ b_i Γ_i
    function total_braking(hs, Ws, Γs; kw...)
        n = length(hs)
        @assert length(Ws) == n && length(Γs) == n "layer lengths must match"
        return -sum(b_layer(hs[i], Ws[i]; kw...) * Γs[i] for i in 1:n)
    end

    # Синхронизированная эволюция: dΓ_i/dt = −b_i Γ_i / T
    function layered_evolution(hs, Ws, Γs0, T, Nsteps; kw...)
        n = length(hs)
        dt = T / Nsteps
        Γs = copy(Γs0)
        hist = zeros(n, Nsteps + 1)
        hist[:, 1] = Γs
        bs = [b_layer(hs[i], Ws[i]; kw...) for i in 1:n]
        for s in 1:Nsteps
            for i in 1:n
                Γs[i] -= bs[i] * Γs[i] * dt / T
            end
            hist[:, s + 1] = Γs
        end
        return hist
    end

    # Профиль по умолчанию: h(z) = z, W(z) = W0·(1 + z/L)
    function default_profile(; L = 4.0, N = 20, W0 = 0.5)
        zs = [(i - 0.5) * L / N for i in 1:N]
        hs = copy(zs)
        Ws = [W0 * (1 + z / L) for z in zs]
        return zs, hs, Ws
    end

    # Радиальный профиль: сужение/расширение с синусом
    function radial_profile(; L = 4.0, N = 20, r0 = 0.3, taper = 0.1)
        zs = [(i - 0.5) * L / N for i in 1:N]
        hs = copy(zs)
        Ws = [2 * (r0 + taper * sin(π * z / L)) for z in zs]
        return zs, hs, Ws
    end

    # Поворот Родрига с углом θ_i на слое
    function layer_rodrigues_apply(u, w, θ)
        c, s = cos(θ), sin(θ)
        d = sum(u[k] * w[k] for k in 1:3)
        up = [d * w[k] for k in 1:3]
        uperp = [u[k] - up[k] for k in 1:3]
        cr = [w[2] * uperp[3] - w[3] * uperp[2],
              w[3] * uperp[1] - w[1] * uperp[3],
              w[1] * uperp[2] - w[2] * uperp[1]]
        return [up[k] + c * uperp[k] + s * cr[k] for k in 1:3]
    end
end


# ═══════════════════════════════════════════════════════════════════════════
# §27b 3D vortex field: рендер реального вихревого жгута, затухающего во
# времени под слоистой b-поправкой Γ(z,t) = Γ0(z)·e^(−b(z)·t), t = frac·T.
# Сетка N×N×N, N ∈ [24, 256] (clamp для защиты памяти); при N³ > 96³
# выборка децимируется вдвое по оси до ≤96³ точек на кадр.
# Рендер: изометрическая проекция, сортировка по глубине, цвет по |u|
# (aurora-палитра). Вывод: анимированный GIF через VFAPlot.save_gif
# (stdlib only). Текст на канве — ASCII (шрифт FONT3X5).
# ═══════════════════════════════════════════════════════════════════════════

module VFAVortex3D
    using ..VFAPlot: Canvas, save_gif, draw_text, rect!, px!
    import ..VFALayer3D

    export render_vortex_animation, render_frame, vortex_preset,
           analyze_evolution, sample_velocity, v_azimuthal

    # ── Aurora-палитра (совпадает с VFAPlot.THEMES["aurora"]["series"])
    const AURORA_SERIES = [
        ( 80, 170, 255),   # cobalt
        (255, 140, 105),   # coral
        (110, 220, 150),   # mint
        (200, 150, 255),   # lilac
        (255, 210,  90),   # amber
        ( 90, 230, 220)]   # cyan
    const BG_DARK = (12, 14, 22)
    const GRID_DIM = (55, 60, 80)

    # ── Lamb-Oseen: азимутальная скорость на радиусе r (циркуляция Γ, ядро rc)
    function v_azimuthal(r::Real, Γ::Real, rc::Real)
        r < 1e-12 && return 0.0
        return Γ / (2π * r) * (1 - exp(-(r / rc)^2))
    end

    # ── Скорость (ux, uy, uz) в точке 3D для слоистого вихря: ядро на x=y=0,
    # слой z_i несёт циркуляцию Γ_i и ширину W_i; линейная интерполяция по z,
    # затем азимутальная Lamb-Oseen. Единичный азимутальный вектор (-y/r, x/r, 0).
    function sample_velocity(x::Real, y::Real, z::Real,
                             Γs::AbstractVector{<:Real},
                             hs::AbstractVector{<:Real},
                             Ws::AbstractVector{<:Real}; L = 4.0)
        n = length(hs)
        n == 0 && return (0.0, 0.0, 0.0)
        zc = clamp(Float64(z), 0.0, Float64(L))
        idx = clamp(searchsortedfirst(hs, zc), 1, n)
        lo = clamp(idx - 1, 1, n)
        hi = clamp(idx, 1, n)
        Γloc, Wloc = if hi == lo
            (Float64(Γs[lo]), Float64(Ws[lo]))
        else
            t = (zc - hs[lo]) / (hs[hi] - hs[lo] + 1e-30)
            ((1 - t) * Γs[lo] + t * Γs[hi], (1 - t) * Ws[lo] + t * Ws[hi])
        end
        rc = max(Wloc, 0.05)
        r = sqrt(x^2 + y^2)
        r < 1e-12 && return (0.0, 0.0, 0.0)
        vθ = v_azimuthal(r, Γloc, rc)
        return (-vθ * y / r, vθ * x / r, 0.0)
    end

    # ── Изометрическая проекция с глубиной: (screenX, screenY, depth)
    function _iso(x::Float64, y::Float64, z::Float64, az::Float64, el::Float64)
        ca, sa = cos(az), sin(az)
        ce, se = cos(el), sin(el)
        X = ca * x - sa * y
        Y = sa * x + ca * y
        return (X, ce * Y - se * z, se * Y + ce * z)
    end

    # ── Aurora-цвет по модулю скорости: интерполяция по палитре
    function _colormap(v::Float64, vmax::Float64)
        vmax < 1e-12 && return AURORA_SERIES[1]
        t = clamp(v / vmax, 0.0, 1.0)
        k = 1 + t * (length(AURORA_SERIES) - 1)
        i0 = clamp(floor(Int, k), 1, length(AURORA_SERIES))
        i1 = clamp(i0 + 1, 1, length(AURORA_SERIES))
        f = k - i0
        c0, c1 = AURORA_SERIES[i0], AURORA_SERIES[i1]
        return (round(Int, (1 - f) * c0[1] + f * c1[1]),
                round(Int, (1 - f) * c0[2] + f * c1[2]),
                round(Int, (1 - f) * c0[3] + f * c1[3]))
    end

    # ── Рендер одного кадра (возвращает Canvas width×height).
    # Depth = se·Y + ce·z растёт от камеры → farther = больше depth.
    # Рисуем FAR FIRST (painter's algorithm), ближние ярче (fade), авто-фит
    # по bbox проекции — вихрь целиком в кадре при любом el/az. Сетки нет:
    # её цвет (55,60,80) совпадал с тусклыми ближними точками.
    function render_frame(N::Int, Γs::AbstractVector{<:Real},
                          hs::AbstractVector{<:Real},
                          Ws::AbstractVector{<:Real};
                          width = 900, height = 640,
                          az = 0.55, el = 0.42,
                          title = "3D VORTEX", sub = "",
                          overlay::Vector{String} = String[])
        W, H = width * 2, height * 2      # supersample ×2
        cv = Canvas(W, H, BG_DARK)
        # защита памяти: держим выборку ≤ 96³ точек, децимация вдвое по оси
        N_eff = N
        while N_eff^3 > 96^3 && N_eff > 24
            N_eff ÷= 2
        end
        L = 4.0
        x_r = 1.5    # радиальный размах
        vmax = 0.0
        raw = Tuple{Float64, Float64, Float64, Float64}[]   # (depth, sx, sy, m)
        ca, sa = cos(az), sin(az)
        ce, se = cos(el), sin(el)
        inv = 1.0 / max(1, N_eff - 1)
        # pass 1: выборка + проекция
        for i in 0:N_eff - 1
            x = -x_r + 2x_r * i * inv
            for j in 0:N_eff - 1
                y = -x_r + 2x_r * j * inv
                for k in 0:N_eff - 1
                    z = L * k * inv
                    ux, uy, _ = sample_velocity(x, y, z, Γs, hs, Ws; L = L)
                    m = sqrt(ux^2 + uy^2)
                    m > vmax && (vmax = m)
                    X = ca * x - sa * y
                    Y = sa * x + ca * y
                    push!(raw, (se * Y + ce * z, X, ce * Y - se * z, m))
                end
            end
        end
        # pass 2: отсечение слабых точек (~90% работы) ДО сортировки
        pts = filter(p -> p[4] >= vmax * 0.02, raw)
        isempty(pts) && (pts = raw)
        # pass 3: авто-фит по bbox проекции (раньше фикс. scale резал верх)
        sx_min = minimum(p[2] for p in pts); sx_max = maximum(p[2] for p in pts)
        sy_min = minimum(p[3] for p in pts); sy_max = maximum(p[3] for p in pts)
        sz_min = minimum(p[1] for p in pts); sz_max = maximum(p[1] for p in pts)
        span_x = max(sx_max - sx_min, 1e-6)
        span_y = max(sy_max - sy_min, 1e-6)
        span_z = max(sz_max - sz_min, 1e-9)
        margin = 60
        scale = 0.9 * min((W - 2margin) / span_x, (H - 2margin) / span_y)
        cx = W / 2 - (sx_min + sx_max) / 2 * scale
        cy = H / 2 - (sy_min + sy_max) / 2 * scale
        # pass 4: FAR FIRST (было наоборот — дальние перекрывали ближние)
        sort!(pts; by = p -> -p[1])
        inv_vmax = 1.0 / max(vmax, 1e-12)
        for (depth, sx, sy, m) in pts
            pxi = round(Int, cx + sx * scale)
            pyi = round(Int, cy + sy * scale)
            rr = 2 + round(Int, 3 * m * inv_vmax)
            base = _colormap(m, vmax)
            # near = BRIGHT (t_depth 0 → 1.0), far тусклее (→ 0.55)
            t_depth = (depth - sz_min) / span_z
            fade = 1.0 - 0.45 * t_depth
            col = (round(Int, base[1] * fade), round(Int, base[2] * fade),
                   round(Int, base[3] * fade))
            rect!(cv, pxi - rr, pyi - rr, pxi + rr, pyi + rr, col)
        end
        # заголовок и легенда (ASCII: шрифт FONT3X5 не знает Γ/·/—)
        draw_text(cv, title, 40, 24, (220, 225, 240), 4)
        isempty(sub) || draw_text(cv, sub, 40, 52, (150, 160, 190), 3)
        # overlay: метрики стабилизации (правый низ); шаг 20 при глифе 15
        for (idx, line) in enumerate(overlay)
            draw_text(cv, line, W - 760, H - 62 - (idx - 1) * 20,
                      (200, 215, 240), 3)
        end
        draw_text(cv, "|u|max = $(round(vmax; sigdigits = 3))", 40, H - 40,
                  (220, 225, 240), 3)
        # даунсэмпл ×2 (box filter)
        out = Canvas(width, height, BG_DARK)
        for yy in 0:height - 1, xx in 0:width - 1
            r = g = b = 0
            for j in 0:1, i in 0:1
                p0 = 3 * ((yy * 2 + j) * W + xx * 2 + i) + 1
                r += cv.buf[p0]; g += cv.buf[p0 + 1]; b += cv.buf[p0 + 2]
            end
            q0 = 3 * (yy * width + xx) + 1
            out.buf[q0] = UInt8(r ÷ 4)
            out.buf[q0 + 1] = UInt8(g ÷ 4)
            out.buf[q0 + 2] = UInt8(b ÷ 4)
        end
        return out
    end

    # ── Временная серия метрик затухания + milestones + verdict:
    # Γ_total(t), v_peak (пик на кромке ядра), %Γ(t), t50/t10/t01,
    # Γ-взвешенный mean_b. Имена полей ASCII — общие с Python-эталоном.
    function analyze_evolution(hs::AbstractVector{<:Real},
                               Ws::AbstractVector{<:Real},
                               Γs0::AbstractVector{<:Real},
                               T::Float64, nframes::Int;
                               h0::Float64 = 1.0, W0::Float64 = 1.0)
        n = length(hs)
        bs = [VFALayer3D.b_layer(hs[i], Ws[i]; h0 = h0, W0 = W0) for i in 1:n]
        halflife = [b > 1e-12 ? log(2.0) / b : Inf for b in bs]
        Γ0tot = sum(Γs0)
        frames = NamedTuple[]
        for fi in 0:nframes - 1
            frac = nframes == 1 ? 0.0 : fi / (nframes - 1)
            t = frac * T
            Γs = [Γs0[i] * exp(-bs[i] * t) for i in 1:n]
            Γtot = sum(Γs)
            v_peak = n == 0 ? 0.0 :
                     maximum(Γs[i] / (2π * max(Ws[i], 0.05)) * (1 - exp(-1.0))
                             for i in 1:n)
            push!(frames, (i = fi + 1, frac = frac, t = t,
                           G_total = Γtot, v_peak = v_peak,
                           G_frac = Γ0tot > 1e-12 ? Γtot / Γ0tot : 0.0))
        end
        find_cross(target_frac) = begin
            target = target_frac * Γ0tot
            for f in frames
                f.G_total <= target && return f.t
            end
            return nothing
        end
        mean_b = Γ0tot > 1e-12 ?
                 sum(Γs0[i] * bs[i] for i in 1:n) / Γ0tot : 0.0
        final_frac = isempty(frames) ? 1.0 : frames[end].G_frac
        verdict = final_frac < 0.01 ? "STABILIZED" :
                  final_frac < 0.10 ? "DAMPED" :
                  final_frac < 0.50 ? "DECAYING" : "PERSISTENT"
        return (n = n, T = T, nframes = nframes,
                layers = [(i = i, h = Float64(hs[i]), W = Float64(Ws[i]),
                           b = bs[i], halflife = halflife[i], G0 = Float64(Γs0[i]),
                           G_end = Float64(Γs0[i]) * exp(-bs[i] * T)) for i in 1:n],
                frames = frames,
                milestones = (t50 = find_cross(0.50),
                              t10 = find_cross(0.10),
                              t01 = find_cross(0.01)),
                mean_b = mean_b, final_frac = final_frac, verdict = verdict)
    end

    # ── Пресет: слоистый профиль по умолчанию с красивым затуханием;
    # Γ_i(z) = Γ0·(1 − 0.5·z/L)·(W_i²/0.25) — ядро сильнее у поверхности
    function vortex_preset(; nlayers = 20, Γ0 = 2.0, L = 4.0)
        zs, hs, Ws = VFALayer3D.default_profile(L = L, N = nlayers, W0 = 0.5)
        Γs0 = [Γ0 * (1 - 0.5 * z / L) * (W^2 / 0.25) for (z, W) in zip(zs, Ws)]
        return hs, Ws, Γs0
    end

    # ── Полная анимация: t = frac·T ∈ [0, T]; Γ_i(t) = Γ_i(0)·exp(−b_i·t) —
    # точное послойное затухание. Дефолт T=40: при b≈0.03–0.06 даёт видимое
    # затухание до ~31% (при T=4 оставалось ~88% — «вихрь не затухает»).
    # nframes клампится [2, 240] — B-NEW-2: TOML/env могли задать 0/1.
    # Аудит (v1.3.1): пиксели, отличные от BG_DARK (12,14,22); ~0 = пустой кадр.
    function frame_nonbg(cv::Canvas)
        n = 0
        b = cv.buf
        for i in 1:3:length(b) - 2
            if b[i] != 12 || b[i + 1] != 14 || b[i + 2] != 22
                n += 1
            end
        end
        return n
    end

    function render_vortex_animation(path::AbstractString;
                                     N::Int = 48,
                                     nframes::Int = 24,
                                     T::Float64 = 40.0,
                                     h0::Float64 = 1.0,
                                     W0::Float64 = 1.0,
                                     width::Int = 900,
                                     height::Int = 640,
                                     callback = nothing)
        N < 24 && error("N must be >= 24 (got $N)")
        N > 256 && (N = 256)       # защита памяти
        nframes = max(2, min(240, nframes))
        hs, Ws, Γs0 = vortex_preset()
        analysis = analyze_evolution(hs, Ws, Γs0, T, nframes;
                                     h0 = h0, W0 = W0)
        frames = Canvas[]
        min_nonbg = -1
        t0 = time()
        for (fi, fmeta) in enumerate(analysis.frames)
            Γs = [Γs0[i] * exp(-analysis.layers[i].b * fmeta.t)
                  for i in 1:length(hs)]
            overlay = ["t=$(round(fmeta.t; digits = 2))  " *
                       "G=$(round(fmeta.G_total; digits = 2))  " *
                       "($(round(100 * fmeta.G_frac; digits = 1))%)",
                       "vmax=$(round(fmeta.v_peak; digits = 3))  " *
                       "$(analysis.verdict)"]
            cv = render_frame(N, Γs, hs, Ws;
                              width = width, height = height,
                              az = 0.55 + 0.15 * sin(fmeta.frac * pi),
                              el = 0.42,
                              title = "3D VORTEX - LAYERED B-CORRECTION",
                              sub = "t/T = $(round(fmeta.frac; digits = 2))  N = $N",
                              overlay = overlay)
            nonbg = frame_nonbg(cv)
            if nonbg * 200 < cv.w * cv.h   # < 0.5% не-фона — кадр пуст
                error("vortex: кадр $fi/$nframes пуст (non-bg $nonbg/" *
                      "$(cv.w * cv.h)) — render_frame/lzw?")
            end
            min_nonbg = min_nonbg < 0 ? nonbg : min(min_nonbg, nonbg)
            push!(frames, cv)
            callback !== nothing && callback(fi, nframes)
        end
        save_gif(path, frames; delay_cs = 6)
        return (path = String(path), frames = nframes,
                sec = round(time() - t0; digits = 2), min_nonbg = min_nonbg,
                analysis = analysis)
    end
end


# ═══════════════════════════════════════════════════════════════════════════
# Конфигурация §3, платформа, CLI
# ═══════════════════════════════════════════════════════════════════════════

import TOML
using LinearAlgebra: norm, det, I
using Random: MersenneTwister, rand!, randn

Base.@kwdef mutable struct VfaConfig
    repo_root::String = isdir("verification") ? "verification" :
                         isdir(joinpath(@__DIR__, "verification")) ?
                         joinpath(@__DIR__, "verification") : pwd()
    tasks::Vector{Int} = Int[]
    two_pass::Bool = true
    seed::Int = 20260913
    size::Int = 1
    preset::String = "full"
    theme::String = "aurora"
    no_report::Bool = false
    report_dir::Union{String, Nothing} = nothing
    no_gif::Bool = false
    plot_formats::Vector{String} = ["png", "gif", "svg"]
    report_formats::Vector{String} = ["md", "html", "pdf"]   # docx → ERR_UNSUPPORTED §1.4
    monitor::String = "on"
    monitor_interval::Float64 = 1.0
    task_timeout::Float64 = 600.0
    global_timeout::Float64 = 0.0
    selftest::Bool = false
    selftest_props::Bool = false
    selftest_contract::Bool = false
    ci::Bool = false
    junit::Union{String, Nothing} = nothing
    lang::String = "ru"
    unicode_mode::String = "auto"
    plain::Bool = false
    no_color::Bool = false
    strict::Bool = false
    list_tasks::Bool = false
    print_config::Bool = false
    help::Bool = false
    menu::Bool = false                  # --menu: интерактивное меню вместо прогона
    menu_legacy::Bool = false           # §29: прежнее плоское меню (--menu-legacy)
    banner::String = "auto"             # §28: auto|always|never
    quiet::Bool = false                 # §28: --quiet подавляет баннер/болтовню
    version::Bool = false
    completions::String = ""
    config_file::Union{String, Nothing} = nothing
    # §27: слоистая 3D-модель
    layers::Int = 20                    # --layers N
    layer_model::String = "default"     # --layer-model default|radial
    layer_h0::Float64 = 1.0             # --layer-h0
    layer_W0::Float64 = 1.0             # --layer-W0
    # §27b: 3D-вихрь (анимация затухания под b-поправкой)
    vortex_N::Int = 0                   # --vortex N (0 = выключено; ≥24 = рендер)
    vortex_frames::Int = 24             # --vortex-frames K
    vortex_T::Float64 = 40.0            # --vortex-T (горизонт времени)
    vortex_quick::Bool = false          # --vortex-quick (превью 640×440)
    fuzz::Int = 0                       # --fuzz N (0 = использовать preset)
    sweep::String = ""                  # --sweep KEY=V1,V2,...
    cross_check::String = ""            # --cross-check ПУТЬ (§32: сверка с results.json)
    rlimit::String = ""                 # --rlimit kind=v[,kind=v...]
end

# §2-локализация: расширенный словарь ru/en для всех пользовательских строк;
# отсутствующий ключ возвращает сам ключ (никаких KeyError в меню)
const VFA_MSG = Dict(
    "ru" => Dict(
        "title"        => "VFA · полная перепроверка Navier-Stokes-B (Julia)",
        "menu_header"  => "VFA · главное меню",
        "menu_core"    => "ЯДРО (контракт Python):",
        "menu_layers"  => "СЛОИ 3D (§27):",
        "menu_keys"    => "[a] все   [1..{n}] задача   [r] последняя   [p] пресет   [2] two-pass   [th] тема   [v] вихрь 3D",
        "menu_keys2"   => "[l] последние результаты   [c] конфиг   [t] самотест   [?] помощь   [q] выход",
        "run_dir"      => "каталог прогона: {d}",
        "select"       => "выберите пункт #: ",
        "back"         => "возврат в меню",
        "quit"         => "выход",
        "no_runs"      => "прогонов нет",
        "no_last"      => "последней задачи нет",
        "last_run"     => "последний прогон",
        "vortex_title" => "3D-вихрь: затухание под b-поправкой",
        "vortex_busy"  => "рендер кадров… {k}/{n}",
        "vortex_done"  => "готово: {path} ({frames} кадров, {sec}s)",
        "vortex_n"     => "размер матрицы N (≥24): ",
        "vortex_bad"   => "N должно быть ≥ 24",
        "vortex_clamp" => "N ограничено до 256 (защита памяти)",
        "vortex_frames_prompt" => "кадров (по умолчанию 24): "),
    "en" => Dict(
        "title"        => "VFA · full Navier-Stokes-B verification (Julia)",
        "menu_header"  => "VFA · main menu",
        "menu_core"    => "CORE (Python contract):",
        "menu_layers"  => "3D LAYERS (§27):",
        "menu_keys"    => "[a] all   [1..{n}] task   [r] rerun last   [p] preset   [2] two-pass   [th] theme   [v] 3D vortex",
        "menu_keys2"   => "[l] last results   [c] config   [t] selftest   [?] help   [q] quit",
        "run_dir"      => "run directory: {d}",
        "select"       => "select #: ",
        "back"         => "returning to menu",
        "quit"         => "quit",
        "no_runs"      => "no runs yet",
        "no_last"      => "no last task",
        "last_run"     => "last run",
        "vortex_title" => "3D vortex: decay under b-correction",
        "vortex_busy"  => "rendering frames… {k}/{n}",
        "vortex_done"  => "done: {path} ({frames} frames, {sec}s)",
        "vortex_n"     => "matrix size N (≥24): ",
        "vortex_bad"   => "N must be ≥ 24",
        "vortex_clamp" => "N clamped to 256 (memory guard)",
        "vortex_frames_prompt" => "frames (default 24): "))

fmt(cfg, key; kw...) = begin
    lang = get(VFA_MSG, cfg.lang, VFA_MSG["ru"])
    s = get(lang, key, key)
    for (k, v) in kw
        s = replace(s, "{$k}" => string(v))
    end
    return s
end

"Локализованная строка с подстановкой {k}→v (алиас fmt, §2)"
vfa_tr(cfg::VfaConfig, key::AbstractString; kw...) = fmt(cfg, key; kw...)

"§10.1/§23.6: GC ×2 + malloc_trim (Linux)"
function vfa_gc_full()
    GC.gc(true)
    GC.gc(true)
    if Sys.islinux()
        try
            ccall(:malloc_trim, Cint, (Csize_t,), 0)
        catch
        end
    end
    return nothing
end

"§10.6 rlimit best-effort; не удалось — ERR_UNSUPPORTED (§1.4)"
function vfa_set_rlimit(kind::AbstractString, value::Integer)
    res = kind == "as" ? Cint(9) : kind == "cpu" ? Cint(2) :
          kind == "fsize" ? Cint(7) : Cint(-1)
    res < 0 && return "ERR_UNSUPPORTED rlimit-$kind: неизвестный ресурс"
    try
        r = Clong[value, value]
        ret = ccall(:setrlimit, Cint, (Cint, Ptr{Clong}), res, r)
        return ret == 0 ? "OK rlimit-$kind=$value" : "ERR_UNSUPPORTED rlimit-$kind: errno"
    catch e
        return "ERR_UNSUPPORTED rlimit-$kind: $e"
    end
end

function vfa_load_config_file!(cfg::VfaConfig, path::AbstractString)
    # §24: JSON-парсера в stdlib Julia нет; TOML — есть
    try
        data = TOML.parsefile(path)
        for (k, v) in data
            sk = Symbol(k)
            sk in fieldnames(VfaConfig) || continue
            setproperty!(cfg, sk, v)
        end
    catch e
        error("config-file: не удалось прочитать $path: $e")
    end
    return cfg
end

function vfa_parse_env!(cfg::VfaConfig)
    for (k, v) in ENV
        startswith(k, "VFA_") || continue
        sk = Symbol(lowercase(k[5:end]))
        sk in fieldnames(VfaConfig) || continue
        cur = getfield(cfg, sk)
        try
            val = cur isa Bool ? lowercase(v) in ("1", "true", "yes", "on") :
                  cur isa Int ? parse(Int, v) :
                  cur isa Float64 ? parse(Float64, v) :
                  cur isa Vector{Int} ?
                      parse.(Int, filter(!isempty, split(v, ','))) :
                  cur isa Vector{String} ?
                      String.(filter(!isempty, split(v, ','))) :
                  String(v)
            setproperty!(cfg, sk, val)
        catch
            println(stderr, "WARNING: env $k: не приводится к типу")
        end
    end
    return cfg
end

vfa_parse_task_ids(val::AbstractString) =
    lowercase(val) in ("all", "все") ? collect(1:VFA_N_TASKS) :
    parse.(Int, filter(!isempty, split(val, ",")))

"разбор --sweep KEY=V1,V2,... → Vector{Pair{Symbol,Float64}}; KEY ограничен"
# §30: разбор --sweep переехал в VFALab.lab_parse_sweeps — многомерные свипы,
# строковые значения по типу поля, декартово произведение. Делегат для совместимости.
function vfa_parse_sweep(s::AbstractString)
    return VFALab.lab_parse_sweeps(s).sweeps
end

function vfa_parse_args!(cfg::VfaConfig, argv::Vector{String})
    i = 1
    while i <= length(argv)
        tok = argv[i]
        if !startswith(tok, "--")
            i += 1
            continue
        end
        flag = tok[3:end]
        if flag == "task"
            i += 1
            i <= length(argv) || error("--task expects значение")
            cfg.tasks = vfa_parse_task_ids(argv[i])
        elseif flag == "no-two-pass"
            cfg.two_pass = false
        elseif flag == "preset"
            i += 1; cfg.preset = argv[i]
        elseif flag == "seed"
            i += 1; cfg.seed = parse(Int, argv[i])
        elseif flag == "size"
            i += 1; cfg.size = parse(Int, argv[i])
        elseif flag == "theme"
            i += 1; cfg.theme = argv[i]
        elseif flag == "monitor"
            i += 1; cfg.monitor = argv[i]
        elseif flag == "monitor-interval"
            i += 1; cfg.monitor_interval = parse(Float64, argv[i])
        elseif flag == "no-report"
            cfg.no_report = true
        elseif flag == "report-dir"
            i += 1; cfg.report_dir = argv[i]
        elseif flag == "no-gif"
            cfg.no_gif = true
        elseif flag == "ci"
            cfg.ci = true
        elseif flag == "junit"
            i += 1; cfg.junit = argv[i]
        elseif flag == "lang"
            i += 1; cfg.lang = argv[i]
        elseif flag == "unicode"
            i += 1; cfg.unicode_mode = argv[i]
        elseif flag == "plain"
            cfg.plain = true
        elseif flag == "no-color"
            cfg.no_color = true
        elseif flag == "strict"
            cfg.strict = true
        elseif flag == "list-tasks"
            cfg.list_tasks = true
        elseif flag == "print-config"
            cfg.print_config = true
        elseif flag == "self-test"
            cfg.selftest = true
        elseif flag == "self-test-props"
            cfg.selftest = true; cfg.selftest_props = true
        elseif flag == "self-test-contract"
            cfg.selftest = true; cfg.selftest_contract = true
        elseif flag == "task-timeout"
            i += 1; cfg.task_timeout = parse(Float64, argv[i])
        elseif flag == "global-timeout"
            i += 1; cfg.global_timeout = parse(Float64, argv[i])
        elseif flag == "rlimit"
            i += 1; cfg.rlimit = argv[i]
        elseif flag == "layers"
            i += 1; cfg.layers = parse(Int, argv[i])
            cfg.layers > 0 || error("--layers: ожидается N > 0")
        elseif flag == "layer-model"
            i += 1; cfg.layer_model = argv[i]
            cfg.layer_model in ("default", "radial") ||
                error("--layer-model: ожидается default|radial")
        elseif flag == "layer-h0"
            i += 1; cfg.layer_h0 = parse(Float64, argv[i])
            cfg.layer_h0 > 0 || error("--layer-h0: ожидается x > 0")
        elseif flag == "layer-W0"
            i += 1; cfg.layer_W0 = parse(Float64, argv[i])
            cfg.layer_W0 > 0 || error("--layer-W0: ожидается y > 0")
        elseif flag == "vortex"
            # §27b: точное сравнение (flag == "vortex") — --vortex-frames
            # сюда не попадает; рендер вихря по N ≥ 24
            i += 1
            i <= length(argv) || error("--vortex ожидает N")
            cfg.vortex_N = parse(Int, argv[i])
            cfg.vortex_N >= 24 || error("--vortex: ожидается N ≥ 24")
        elseif flag == "vortex-frames"
            i += 1
            i <= length(argv) || error("--vortex-frames ожидает K")
            cfg.vortex_frames = parse(Int, argv[i])
            cfg.vortex_frames >= 2 || error("--vortex-frames: ожидается ≥ 2")
        elseif flag == "vortex-T"
            i += 1
            i <= length(argv) || error("--vortex-T ожидает T")
            cfg.vortex_T = parse(Float64, argv[i])
            cfg.vortex_T > 0 || error("--vortex-T: ожидается T > 0")
        elseif flag == "vortex-quick"
            cfg.vortex_quick = true
        elseif flag == "fuzz"
            i += 1; cfg.fuzz = parse(Int, argv[i])
            cfg.fuzz >= 0 || error("--fuzz: ожидается N ≥ 0")
        elseif flag == "sweep"
            i += 1
            # §30: повторные --sweep склеиваются — многомерная матрица
            cfg.sweep = isempty(cfg.sweep) ? argv[i] : cfg.sweep * ";" * argv[i]
        elseif flag == "cross-check"
            i += 1
            i <= length(argv) || error("--cross-check ожидает путь")
            cfg.cross_check = argv[i]
        elseif flag == "config-file"
            # F: --config-file читается до env/args (vfa_main); повторная
            # установка из argv перезаписала бы redirect из TOML
            i += 1
            cfg.config_file === nothing && (cfg.config_file = argv[i])
        elseif flag == "help"
            cfg.help = true
        elseif flag == "menu"
            cfg.menu = true
        elseif flag == "banner"
            i += 1
            cfg.banner = argv[i]
            cfg.banner in ("auto", "always", "never") ||
                error("--banner: ожидается auto|always|never")
        elseif flag == "quiet"
            cfg.quiet = true
        elseif flag == "menu-legacy"
            cfg.menu_legacy = true
        elseif flag == "version"
            cfg.version = true
        elseif flag == "generate-completions"
            i += 1; cfg.completions = argv[i]
        else
            msg = "WARNING: unrecognized CLI argument --$flag"
            cfg.strict && error("--$flag: неизвестный флаг (--strict)")
            println(stderr, msg)
        end
        i += 1
    end
    return cfg
end

function vfa_print_config(cfg::VfaConfig)
    for name in fieldnames(VfaConfig)
        println(rpad(name, 20), " ", rpad(string(getfield(cfg, name)), 40), " default")
    end
    return nothing
end
"§28: интерактивен ли TTY (для автовыбора баннера). Без isinteractive():
баннер должен появляться и у скрипта, запущенного из терминала, а не только
в REPL; в pipe/CI оба stdout и stdin не TTY → подавлен."
vfa_detect_tty() = stdin isa Base.TTY && stdout isa Base.TTY

"§28: найти последний прогон в results/ и вернуть его вердикты (Dict{Int,String})"
function vfa_last_run_info(rd_root::AbstractString = "results")
    isdir(rd_root) || return (nothing, Dict{Int, String}())
    cands = String[]
    for d in readdir(rd_root; join = true)
        isdir(d) || continue
        (startswith(basename(d), "jrun_") || startswith(basename(d), "run_")) || continue
        isfile(joinpath(d, "results.json")) || continue
        push!(cands, d)
    end
    isempty(cands) && return (nothing, Dict{Int, String}())
    sort!(cands; by = x -> stat(x).mtime, rev = true)
    lastrun = cands[1]
    verdicts = Dict{Int, String}()
    try
        txt = read(joinpath(lastrun, "results.json"), String)
        # минимальный regex-парсер: \"tid\":{\"slug\":\"...\",\"verdict\":\"...\""
        for m in eachmatch(r"\"(\d+)\"\s*:\s*\{[^}]*\"verdict\"\s*:\s*\"([A-Z]+)\"", txt)
            verdicts[parse(Int, m.captures[1])] = m.captures[2]
        end
    catch
    end
    return (lastrun, verdicts)
end


# ═══════════════════════════════════════════════════════════════════════════
# Численные задачи §4 (те же, что в Python; pass1 BigFloat 140, pass2 300 бит)
# ═══════════════════════════════════════════════════════════════════════════

# A2: строковый литерал несёт только 64 знака — при setprecision(300) (~90
# знаков) он ограничивал точность «300-битных» вычислений. vfa_pi()
# конвертирует Irrational π в BigFloat текущей точности — всегда полная
# точность. VFA_PI оставлен для совместимости, задачами не используется.
VFA_PI = BigFloat("3.1415926535897932384626433832795028841971693993751058209749445923")
vfa_pi() = BigFloat(π)
VFA_L_MIN_KLEIN = BigFloat("2.898149445355172670064346286515453564939")
VFA_LILLY = 0.17326
VFA_PINNED_CS = "0.1732659558297058017568595667273903913207704370073762727"
VFA_EXPECTED = Dict(
    "b" => "0.06238119412102822754633967163940208118699",
    "theta_b" => "0.06242172363615543448214131247202984079931",
    "cos_theta_b" => "0.9980523967307701392298638666131157346569",
    "ln_1p_b" => "0.06051279826655894651750676908625666676176",
    "Z_full_leading" => "1.351637344385124182138824478390398386857")

vfa_b_float() = 1 / (4pi + 2 * sqrt(3))

function vfa_arcsin_series(x::T; terms = 40) where {T <: Real}
    total, term = zero(T), x
    x2 = x * x
    for n in 1:terms
        total += term
        term *= x2 * (2n - 1)^2 / (2n * (2n + 1))
        abs(term) < eps(T) * 100 && break
    end
    return total
end

"полный ряд sin(x): усечённая в θ⁷ форма давала остаток θ⁹/9! ≈ 4e-17"
function vfa_sin_series(x::T; terms = 40) where {T <: Real}
    total, term = zero(T), x
    x2 = x * x
    for n in 1:terms
        total += term
        term *= -x2 / ((2n) * (2n + 1))
        abs(term) < eps(T) * 100 && break
    end
    return total
end

mutable struct VfaTaskCtx
    id::Int
    slug::String
    failures::Vector{String}
    metrics::Dict{String, Any}
    plots::Vector{VFAPlot.RepPlot}
    artifacts::Vector{String}
    cfg::VfaConfig
end
VfaTaskCtx(id, slug, cfg) = VfaTaskCtx(id, slug, String[], Dict{String, Any}(),
                                       VFAPlot.RepPlot[], String[], cfg)

function vfa_check(ctx::VfaTaskCtx, name::AbstractString, cond::Bool, detail = "")
    status = cond ? "PASS" : "FAIL"
    # бейдж VFAUI используется в человекочитаемом режиме; в --ci — plain
    prefix = ctx.cfg.ci ? "[$status]" : VFAUI.badge(status)
    println(prefix, " ", name, isempty(detail) ? "" : "  ($detail)")
    VFALog.log_comp("task$(lpad(ctx.id, 2, '0')) [$status] $name")
    cond || push!(ctx.failures, name)
    return cond
end

function vfa_skip(ctx::VfaTaskCtx, name::AbstractString, reason::AbstractString)
    println("[SKIP] $name — $reason")
    VFALog.log_comp("task$(lpad(ctx.id, 2, '0')) [SKIP] $name — $reason")
    return true
end

"§27: профиль слоёв из cfg (--layer-model default|radial) + масштабы поправки"
function vfa_layer_profile(cfg::VfaConfig)
    cfg.layer_model == "radial" && return VFALayer3D.radial_profile(N = cfg.layers)
    cfg.layer_model == "default" && return VFALayer3D.default_profile(N = cfg.layers)
    error("layer-model: неизвестная модель '$(cfg.layer_model)' (default|radial)")
end

vfa_layer_kw(cfg::VfaConfig) = (h0 = cfg.layer_h0, W0 = cfg.layer_W0)

function vfa_save_plot!(ctx::VfaTaskCtx, p::VFAPlot.RepPlot, idx::Int)
    push!(ctx.plots, p)
    VFALog.G.task_dir === nothing && return String[]
    out = String[]
    pdir = joinpath(VFALog.G.task_dir, "plots")
    stem = "plot_$(lpad(ctx.id, 2, '0'))_$idx"
    fmt = ctx.cfg.plot_formats
    if "png" in fmt || "gif" in fmt
        canvas = VFAPlot.render_plot(p, ctx.cfg.theme)
        if "png" in fmt
            VFAPlot.save_png(joinpath(pdir, "$stem.png"), canvas)
            push!(out, "plots/$stem.png")
        end
        # B4: gif теперь реально пишется (однокадровый), no_gif действует
        if "gif" in fmt && !ctx.cfg.no_gif
            VFAPlot.save_gif(joinpath(pdir, "$stem.gif"), [canvas])
            push!(out, "plots/$stem.gif")
        end
    end
    if "svg" in fmt
        VFALog.log_comp("WARN plots: svg не реализован в Julia-адаптере (§1.4) — пропущен",
                        "warn")
    end
    append!(ctx.artifacts, out)
    return out
end

# ── задача 01: константная цепочка b → θ_b → Клейн

function task01_constants(cfg::VfaConfig)
    ctx = VfaTaskCtx(1, "constants", cfg)
    # A3: setprecision(f, ...) восстанавливает точность после выхода —
    # глобальная утечка 140 бит портила порядок-зависимые задачи
    return setprecision(BigFloat, 140) do
        pi = vfa_pi()
        b1 = pi / (4pi^2 + 2pi * sqrt(BigFloat(3)))
        b2 = 1 / (4pi + 2 * sqrt(BigFloat(3)))
        # 140 бит ≈ 42 знака; расхождение двух форм — чистый шум округления
        # ≈ 1e-43; sin∘arcsin даёт до ~1.1e-40 (ранний break ряда на n=16),
        # поэтому допуск 1e-38 — 3 порядка запаса, а не 1e-50 ниже шума
        vfa_check(ctx, "b: две формы совпадают (шум ≤ 1e-38)",
                  abs(b1 - b2) < BigFloat(10)^-38,
                  "Δ = $(Float64(abs(b1 - b2)))")
        b = b2
        theta = vfa_arcsin_series(b)
        vfa_check(ctx, "sin θ_b = b (полный ряд, шум ≤ 1e-38)",
                  abs(vfa_sin_series(theta) - b) < BigFloat(10)^-38)
        cos_t = sqrt(1 - b^2)
        ln1p = log(1 + b)
        beta_k = BigFloat(5) / 3
        z = exp(b * beta_k * VFA_L_MIN_KLEIN)
        for (name, val, key) in (("b", b, "b"), ("theta_b", theta, "theta_b"),
                                 ("cos", cos_t, "cos_theta_b"), ("ln(1+b)", ln1p, "ln_1p_b"),
                                 ("exp(b·β_K·L_min)", z, "Z_full_leading"))
            s = string(val)
            ok = startswith(s, VFA_EXPECTED[key][1:min(34, length(VFA_EXPECTED[key]))])
            vfa_check(ctx, "$name ≡ pinned-эталон", ok, first(s, 30) * "…")
            ctx.metrics[name] = first(s, 40)
        end
        p = VFAPlot.RepPlot("Константная цепочка (Julia) — task 01", "x", "y")
        VFAPlot.add_series!(p, "b", [0.0, 1.0], [Float64(b), Float64(b)], 'l')
        vfa_save_plot!(ctx, p, 1)
        ok = isempty(ctx.failures)
        VFALog.log_result(1, "constants", ok ? "PASS" : "FAIL", "", ctx.metrics)
        return ok
    end
end

function task01b_constants_hardcore(cfg::VfaConfig)
    ctx = VfaTaskCtx(1, "constants_hardcore", cfg)
    return setprecision(BigFloat, 300) do
        b = 1 / (4vfa_pi() + 2 * sqrt(BigFloat(3)))
        vfa_check(ctx, "300-битная точность: b ≡ эталон до 40 знаков",
                  startswith(string(b), VFA_EXPECTED["b"][1:40]))
        ok = isempty(ctx.failures)
        VFALog.log_result(1, "constants_hardcore", ok ? "PASS" : "FAIL", "", ctx.metrics)
        return ok
    end
end

# ── задача 02: Смагоринский–Колмогоров

vfa_cs_master(ck::Real) = 1 / (BigFloat(pi) * (3 * BigFloat(ck) / 2)^BigFloat(0.75))

function task02_smagorinsky(cfg::VfaConfig)
    ctx = VfaTaskCtx(2, "smagorinsky", cfg)
    cs15 = vfa_cs_master(1.5)
    vfa_check(ctx, "C2: C_s(1.5) ≡ pinned (BigFloat 1e-35)",
              abs(cs15 - parse(BigFloat, VFA_PINNED_CS)) < BigFloat(10)^-35)
    vfa_check(ctx, "C3: Лилли |C_s−0.17326|<1e-5", abs(Float64(cs15) - VFA_LILLY) < 1e-5)
    worst = 0.0
    for a in (0.8, 1.2, 2.0, 3.0)
        worst = max(worst, abs(Float64(vfa_cs_master(1.5 * a) / cs15) - a^(-0.75)))
    end
    vfa_check(ctx, "C4: закон показателя (1e-14)", worst < 1e-14, "max Δ = $worst")
    vfa_check(ctx, "C5: монотонность", vfa_cs_master(1.8) < cs15 < vfa_cs_master(1.2))
    vfa_check(ctx, "C6: коридор 0.16<C_s<0.20", 0.16 < Float64(cs15) < 0.20)
    ks = [2.0^(i / 4) for i in 8:23]
    lys = log.(1.5 .* ks .^ (-5 / 3))
    lxs = log.(ks)
    n = length(ks)
    slope = (n * sum(lxs .* lys) - sum(lxs) * sum(lys)) /
            (n * sum(lxs .^ 2) - sum(lxs)^2)
    vfa_check(ctx, "C10: K41-наклон = −5/3", abs(slope + 5 / 3) < 1e-12, "slope = $slope")
    p = VFAPlot.RepPlot("C_s(C_K) Julia — task 02", "C_K", "C_s")
    grid = [0.5 + 0.05 * i for i in 0:50]
    VFAPlot.add_series!(p, "C_s", grid, [Float64(vfa_cs_master(k)) for k in grid], 'l')
    vfa_save_plot!(ctx, p, 1)
    ok = isempty(ctx.failures)
    VFALog.log_result(2, "smagorinsky", ok ? "PASS" : "FAIL", "", ctx.metrics)
    return ok
end

# ── задача 03: Кассини (BigInt)

vfa_fib(n::Int) = begin
    a, b = BigInt(0), BigInt(1)
    for _ in 1:n
        a, b = b, a + b
    end
    return a
end

function task03_cassini(cfg::VfaConfig)
    ctx = VfaTaskCtx(3, "cassini", cfg)
    worst = 0
    vals = Int[]
    for k in 0:40
        r = vfa_fib(k + 1)^2 - vfa_fib(k) * vfa_fib(k + 2) - (-1)^k
        worst = max(worst, abs(r))
        push!(vals, vfa_fib(k + 1)^2 - vfa_fib(k) * vfa_fib(k + 2))
    end
    vfa_check(ctx, "Кассини k=0..40 (BigInt)", worst == 0)
    ok_m1 = all(vfa_fib(k + 2)^2 - vfa_fib(k + 1)^2 > 0 for k in 1:40)
    vfa_check(ctx, "коэффициент m_1 > 0 (k ≥ 1)", ok_m1)
    p = VFAPlot.RepPlot("Кассини Julia — task 03", "k", "residual")
    VFAPlot.add_series!(p, "res", collect(0.0:40.0), Float64.(vals), 's')
    vfa_save_plot!(ctx, p, 1)
    ok = isempty(ctx.failures)
    VFALog.log_result(3, "cassini", ok ? "PASS" : "FAIL", "", ctx.metrics)
    return ok
end

# ── задача 04: KdV-солитон

function vfa_soliton(xi::Real, c::Real)
    k = sqrt(c) / 2
    sech = 1 / cosh(k * xi)
    u = (c / 2) * sech^2
    t = tanh(k * xi)
    up = -2k * u * t
    upp = 4k^2 * u * t^2 - 2k^2 * u * (1 - t^2)
    tp = k * (1 - t^2)
    uppp = 4k^2 * (up * t^2 + 2u * t * tp) - 2k^2 * (up * (1 - t^2) - 2u * t * tp)
    return u, up, upp, uppp
end

function task04_kdv(cfg::VfaConfig)
    ctx = VfaTaskCtx(4, "kdv", cfg)
    worst = 0.0
    for c in (0.5, 1.0, 2.0, 4.0), xi in (-3.1, -1.7, -0.3, 0.0, 0.9, 2.5, 4.0)
        u, up, upp, uppp = vfa_soliton(xi, c)
        worst = max(worst, abs(uppp - c * up + 6 * u * up))
    end
    vfa_check(ctx, "ODE бегущей волны u′′′ − c u′ + 6 u u′ = 0 (machine zero)",
              worst < 1e-12, "max = $worst")
    vfa_check(ctx, "u_max = c/2",
              all(abs(vfa_soliton(0.0, c)[1] - c / 2) < 1e-14
                  for c in (0.5, 1.0, 2.0, 4.0)))
    b = vfa_b_float()
    vfa_check(ctx, "b → θ_b", abs(sin(asin(b)) - b) < 1e-17)
    p = VFAPlot.RepPlot("KdV-солитон Julia — task 04", "x", "u")
    xg = [-4.0 + 0.1 * i for i in 0:80]
    for c in (0.5, 1.0, 2.0, 4.0)
        VFAPlot.add_series!(p, "c=$c", xg, [Float64(vfa_soliton(x, c)[1]) for x in xg], 'l')
    end
    vfa_save_plot!(ctx, p, 1)
    ok = isempty(ctx.failures)
    VFALog.log_result(4, "kdv", ok ? "PASS" : "FAIL", "", ctx.metrics)
    return ok
end

# ── задача 05: мост Клейна

function task05_klein_bridge(cfg::VfaConfig)
    ctx = VfaTaskCtx(5, "klein_bridge", cfg)
    b = vfa_b_float()
    theta = asin(b)
    # Баг 2: проверяем именно θ_b/π против нивеновских рациональных кратных,
    # а не само b (старая проверка проходила тривиально)
    niven = (0.0, 0.5, -0.5, 1.0, -1.0)
    theta_over_pi = theta / pi
    vfa_check(ctx, "θ_b/π далеко от {0, ±1/2, ±1} (Нивен)",
              all(abs(theta_over_pi - s) > 1e-9 for s in niven),
              "θ_b/π = $(round(theta_over_pi; sigdigits = 6))")
    n_iter = (cfg.preset == "quick" ? 20000 :
              cfg.preset == "deep" ? 400000 : 100000) * cfg.size
    # A1: θ_b/(2π) ≈ 1/100.66 — последовательность i·θ_b почти периодична
    # с периодом ~101, поэтому max gap ≈ 0.04 рад, а не O(1/N): старая
    # проверка гарантированно падала. Для θ_b проверяем структуру three-gap
    # (теорема о трёх промежутках: ≤ 3 различных длин), для качества
    # equidistribution — эталонный «хороший» угол (золотое сечение).
    ang = sort([mod(i * theta, 2 * pi) for i in 1:n_iter])
    gaps = Float64[ang[i + 1] - ang[i] for i in 1:n_iter - 1]
    push!(gaps, 2 * pi - ang[end] + ang[1])
    uniq = unique(round.(gaps; digits = 9))
    vfa_check(ctx, "three-gap θ_b: ≤ 3 различных длин интервалов",
              length(uniq) <= 3,
              "N=$n_iter uniq=$(length(uniq)) gmax=$(round(maximum(gaps); sigdigits = 3))")
    disc = 0.0
    for (j, x) in enumerate(ang)
        disc = max(disc, abs(j / n_iter - x / (2 * pi)),
                   abs((j - 1) / n_iter - x / (2 * pi)))
    end
    vfa_check(ctx, "star-discrepancy θ_b = O(√(log N / N))",
              disc < 3 * sqrt(log(2 * n_iter) / n_iter),
              "D=$(round(disc; sigdigits = 3)) bound=$(round(3 * sqrt(log(2 * n_iter) / n_iter); sigdigits = 3))")
    θ_test = pi * (sqrt(5.0) - 1) / 2
    ang2 = sort([mod(i * θ_test, 2 * pi) for i in 1:n_iter])
    gaps2 = Float64[ang2[i + 1] - ang2[i] for i in 1:n_iter - 1]
    push!(gaps2, 2 * pi - ang2[end] + ang2[1])
    gmax = maximum(gaps2)
    bound = 10 * log2(n_iter) * 2 * pi / n_iter
    vfa_check(ctx, "equidistribution φ: max gap = O(log N / N)", gmax < bound,
              "N=$n_iter gap=$(round(gmax; sigdigits = 3)) bound=$(round(bound; sigdigits = 3))")
    p = VFAPlot.RepPlot("Эргодика Julia — task 05", "N", "gap")
    VFAPlot.add_series!(p, "gap φ", [Float64(n_iter)], [gmax], 's')
    VFAPlot.add_series!(p, "bound", [Float64(n_iter)], [bound], 's')
    VFAPlot.add_series!(p, "gap θ_b", [Float64(n_iter)], [maximum(gaps)], 's')
    vfa_save_plot!(ctx, p, 1)
    ok = isempty(ctx.failures)
    VFALog.log_result(5, "klein_bridge", ok ? "PASS" : "FAIL", "", ctx.metrics)
    return ok
end

# ── задача 06: Родриг

function vfa_rodrigues_apply(u, w, c, s)
    dotuw = sum(u[i] * w[i] for i in 1:3)
    upar = [dotuw * w[i] for i in 1:3]
    uperp = [u[i] - upar[i] for i in 1:3]
    cr = [w[2] * uperp[3] - w[3] * uperp[2], w[3] * uperp[1] - w[1] * uperp[3],
          w[1] * uperp[2] - w[2] * uperp[1]]
    return [upar[i] + c * uperp[i] + s * cr[i] for i in 1:3]
end

function vfa_rodrigues_matrix(w, c, s)
    K = [0.0 -w[3] w[2]; w[3] 0.0 -w[1]; -w[2] w[1] 0.0]
    return Matrix{Float64}(I, 3, 3) + s .* K + (1 - c) .* (K * K)
end

function task06_rodrigues(cfg::VfaConfig)
    ctx = VfaTaskCtx(6, "rodrigues", cfg)
    b = vfa_b_float()
    cphi, sphi = sqrt(1 - b^2), b
    rng = MersenneTwister(cfg.seed)
    n_vec = (cfg.preset == "quick" ? 2000 : 20000) * cfg.size
    worst = 0.0
    for _ in 1:n_vec
        u = 2 .* rand(rng, 3) .- 1
        w = randn(rng, 3)
        # C1: защита от вырожденного направления (norm ≈ 0 → NaN)
        while norm(w) < 1e-10
            w = randn(rng, 3)
        end
        w ./= norm(w)
        M = vfa_rodrigues_matrix(w, cphi, sphi)
        r = vfa_rodrigues_apply(u, w, cphi, sphi)
        r2 = M * u
        worst = max(worst, maximum(abs.(r .- r2)), abs(norm(r) - norm(u)),
                    maximum(abs.(M' * M - Matrix{Float64}(I, 3, 3))))
    end
    vfa_check(ctx, "RᵀR=I, |u′|=|u|, форма≡матрица (1e-12)", worst < 1e-12, "max = $worst")
    wz = [0.3, -0.8, 0.5] ./ norm([0.3, -0.8, 0.5])
    vfa_check(ctx, "det R = 1", abs(det(vfa_rodrigues_matrix(wz, cphi, sphi)) - 1) < 1e-12)
    ok = isempty(ctx.failures)
    VFALog.log_result(6, "rodrigues", ok ? "PASS" : "FAIL", "", ctx.metrics)
    return ok
end

# ── задача 07: Кирхгоф (RK4)

vfa_H(x, y) = 0.5 * (x^2 + y^2) + 0.25 * sin(x) * sin(y)
vfa_v(q) = (q[2] + 0.25 * sin(q[1]) * cos(q[2]),
            -(q[1] + 0.25 * cos(q[1]) * sin(q[2])))

function vfa_rk4(q, dt)
    k1 = vfa_v(q)
    k2 = vfa_v((q[1] + 0.5 * dt * k1[1], q[2] + 0.5 * dt * k1[2]))
    k3 = vfa_v((q[1] + 0.5 * dt * k2[1], q[2] + 0.5 * dt * k2[2]))
    k4 = vfa_v((q[1] + dt * k3[1], q[2] + dt * k3[2]))
    return (q[1] + dt / 6 * (k1[1] + 2k2[1] + 2k3[1] + k4[1]),
            q[2] + dt / 6 * (k1[2] + 2k2[2] + 2k3[2] + k4[2]))
end

function task07_kirchhoff(cfg::VfaConfig)
    ctx = VfaTaskCtx(7, "kirchhoff", cfg)
    q0 = (0.7, -0.4)
    T = 4.0
    drifts = Float64[]
    for dt in (0.2, 0.1, 0.05, 0.025)
        q = q0
        for _ in 1:round(Int, T / dt)
            q = vfa_rk4(q, dt)
        end
        push!(drifts, abs(vfa_H(q[1], q[2]) - vfa_H(q0[1], q0[2])))
    end
    vfa_check(ctx, "инвариант H (dt=0.025, <1e-6)", drifts[end] < 1e-6)
    ratios = [drifts[i] / drifts[i + 1] for i in 1:3]
    # C3: при мелком dt ошибка упирается в машинный ноль и последнее
    # отношение схлопывается к ~1 — порядок берём по первым двум
    p_meas = log2(ratios[1])
    vfa_check(ctx, "высокий порядок RK4 (p ≥ 4 по первым отношениям)",
              ratios[1] > 13 && ratios[2] > 13, "ratios = $ratios")
    ok = isempty(ctx.failures)
    VFALog.log_result(7, "kirchhoff", ok ? "PASS" : "FAIL", "", ctx.metrics)
    return ok
end

"§32: разбор вердиктов из results.json (Python или Julia) → id → verdict"
function vfa_parse_verdicts(txt::AbstractString)
    pv = Dict{Int, String}()
    for m in eachmatch(r"\"(\d+)\":\s*\{[^{}]*?\"verdict\":\s*\"(\w+)\"", txt)
        pv[parse(Int, m.captures[1])] = String(m.captures[2])
    end
    return pv
end

"§32: кросс-языковая сверка вердиктов с чужим results.json (после прогона)"
function vfa_cross_check(cfg::VfaConfig, path::AbstractString)
    p = String(path)
    isdir(p) && (p = joinpath(p, "results.json"))
    if !isfile(p)
        println(stderr, "cross-check: нет файла: $p")
        return false
    end
    txt = read(p, String)
    pv = vfa_parse_verdicts(txt)
    ec = match(r"\"exit_code\"\s*:\s*(\d+)", txt)
    println(stderr, "cross-check: ", p)
    println(stderr, "  там: задач ", length(pv), ", exit_code ",
            ec === nothing ? "?" : ec.captures[1])
    mine = Dict{Int, String}(tid => rec["verdict"]
                             for (tid, rec) in VFALog.G.verdicts)
    ids = sort(collect(union(Set(keys(pv)), Set(keys(mine)))))
    ok = true
    nmatch = nmiss = 0
    println(stderr, "  task  этот прогон  чужой      статус")
    for tid in ids
        va = get(mine, tid, "—")
        vb = get(pv, tid, "—")
        st = va == vb ? "совпало" :
             (va == "—" || vb == "—" ? "нет пары" : "РАСХОЖДЕНИЕ")
        st == "РАСХОЖДЕНИЕ" && (ok = false)
        st == "совпало" && (nmatch += 1)
        st == "нет пары" && (nmiss += 1)
        println(stderr, "  ", lpad(tid, 4), "  ", rpad(va, 12),
                rpad(vb, 11), st)
    end
    println(stderr, "cross-check: совпало ", nmatch, ", без пары ", nmiss,
            ok ? " — СОВМЕСТИМО" : " — РАСХОЖДЕНИЕ")
    return ok
end

# ── задача 08: мост к Python-прогону (results.json) / SKIP с причиной

function task08_py_bridge(cfg::VfaConfig)
    ctx = VfaTaskCtx(8, "py_bridge", cfg)
    found = ""
    # repo_root теперь реально читается: ищем и в cwd, и в корне репозитория
    for res in ("results", joinpath(cfg.repo_root, "results"))
        isdir(res) || continue
        for d in sort(readdir(res; join = true); rev = true)
            if startswith(basename(d), "run_") && isfile(joinpath(d, "results.json"))
                found = d
                break
            end
        end
        isempty(found) || break
    end
    if isempty(found)
        vfa_skip(ctx, "python-прогон", "results/run_* не найден — SKIP с причиной")
        VFALog.log_result(8, "py_bridge", "SKIP", "нет результатов python-прогона")
        return true
    end
    txt = read(joinpath(found, "results.json"), String)
    ok10 = occursin(r"\"exit_code\"\s*:\s*0", txt)
    vfa_check(ctx, "python-прогон: exit_code = 0", ok10)
    pv = vfa_parse_verdicts(txt)               # §32: id → verdict
    # Баг 4: старый Python-прогон не знает о задачах 11–15 — отмечаем
    # неполноту как SKIP, а не молча пропускаем
    missing = [tid for tid in SUITE_IDS if !haskey(pv, tid)]
    isempty(missing) || vfa_skip(ctx, "py_bridge: нет задач $missing",
                                 "Python-прогон неполный (это не FAIL)")
    # §32: сверка вердиктов по уже выполненным задачам (пересечение ключей)
    done = sort(collect(intersect(Set(keys(pv)), Set(keys(VFALog.G.verdicts)))))
    if isempty(done)
        vfa_skip(ctx, "py_bridge: пересечение пусто",
                 "нет общих выполненных задач — сверять нечего")
    else
        mism = [tid for tid in done
                if pv[tid] != VFALog.G.verdicts[tid]["verdict"]]
        vfa_check(ctx, "вердикты совпадают (пересечение $(length(done)))",
                  isempty(mism),
                  isempty(mism) ? "" : "расхождение: $mism")
    end
    ctx.metrics["py_tasks"] = length(pv)
    ctx.metrics["matched"] = length(done)
    ok = isempty(ctx.failures)
    VFALog.log_result(8, "py_bridge", ok ? "PASS" : "FAIL", "", ctx.metrics)
    return ok
end

# ── задача 09: pinned-значения на Float64

function task09_pinned(cfg::VfaConfig)
    ctx = VfaTaskCtx(9, "pinned", cfg)
    b = vfa_b_float()
    diff_b = abs(b - parse(Float64, VFA_EXPECTED["b"]))
    vfa_check(ctx, "b float64 ≡ pinned (1e-15)", diff_b < 1e-15, "diff = $diff_b")
    cs = 1 / (pi * 2.25^0.75)
    # C2: ulp(0.173) ≈ 2.8e-17, порог 1e-15 = ~36 ulp — при другом пути
    # кодогенерации может выйти за край; 1e-14 устойчивее
    diff_cs = abs(cs - parse(Float64, VFA_PINNED_CS))
    vfa_check(ctx, "C_s(1.5) float64 ≡ pinned (1e-14)", diff_cs < 1e-14,
              "diff = $diff_cs")
    ok = isempty(ctx.failures)
    VFALog.log_result(9, "pinned", ok ? "PASS" : "FAIL", "", ctx.metrics)
    return ok
end

# ── задача 10: сводный численный прогон

function task10_suite(cfg::VfaConfig)
    ctx = VfaTaskCtx(10, "suite", cfg)
    ok = true
    missing_ids = Int[]
    # B3: задачи 1–4 не перезапускаются — читаем уже записанные вердикты,
    # иначе двойная работа и перезапись результатов в реестре
    for tid in (1, 2, 3, 4)
        rec = get(VFALog.G.verdicts, tid, nothing)
        if rec === nothing
            push!(missing_ids, tid)
        else
            v = rec["verdict"]
            vfa_check(ctx, "task $(lpad(tid, 2, '0')) [$(rec["slug"])] → $v (из реестра)",
                      v == "PASS")
            ok &= v == "PASS"
        end
    end
    if !isempty(missing_ids)
        # изолированный запуск (--task 10): считаем недостающие внутренне,
        # но вердикты 1–4 в реестр не пишем — только свой (id=10)
        vfa_check(ctx, "задачи $missing_ids не в реестре → тихий внутренний прогон", true)
        saved = VFALog.G.quiet
        VFALog.G.quiet = true
        try
            # B4: исключение задачи не должно ронять task10 целиком —
            # ловим и засчитываем провал
            for tid in missing_ids
                try
                    ok &= vfa_dispatch(tid, cfg)
                catch e
                    ok = false
                    VFALog.log_comp("task10: внутренний прогон $tid упал: $e", "warn")
                end
            end
        finally
            VFALog.G.quiet = saved
        end
    end
    vfa_check(ctx, "все численные задачи PASS", ok)
    ok = isempty(ctx.failures)
    VFALog.log_result(10, "suite", ok ? "PASS" : "FAIL", "", ctx.metrics)
    return ok
end

# ── задача 11: слоистая b-поправка (h, W-зависимость)

function task11_layered_b(cfg::VfaConfig)
    ctx = VfaTaskCtx(11, "layered_b", cfg)
    L = VFALayer3D
    kw = (h0 = cfg.layer_h0, W0 = cfg.layer_W0)
    b∞ = L.b_base()
    vfa_check(ctx, "b_base ≡ 2D константа", abs(b∞ - vfa_b_float()) < 1e-15)
    vfa_check(ctx, "b(h→0, W) → 0 (вязкое подавление у поверхности)",
              L.b_layer(1e-10 * cfg.layer_h0, cfg.layer_W0; kw...) < 1e-9)
    vfa_check(ctx, "b(h→∞, W→0) → b∞ (свободный вихрь)",
              L.b_layer(100 * cfg.layer_h0, 1e-10 * cfg.layer_W0; kw...) > 0.99 * b∞)
    hs = collect(0.1:0.1:2.0) .* cfg.layer_h0
    bs = [L.b_layer(h, cfg.layer_W0; kw...) for h in hs]
    vfa_check(ctx, "b монотонно растёт по h",
              all(bs[i] < bs[i + 1] for i in 1:length(bs) - 1))
    Ws = collect(0.1:0.1:2.0) .* cfg.layer_W0
    bsW = [L.b_layer(cfg.layer_h0, W; kw...) for W in Ws]
    vfa_check(ctx, "b монотонно убывает по W",
              all(bsW[i] > bsW[i + 1] for i in 1:length(bsW) - 1))
    vfa_check(ctx, "0 < b < b∞ для всех (h, W) > 0",
              all(0 < L.b_layer(h, W; kw...) < b∞ + 1e-15 for h in hs, W in Ws))
    p = VFAPlot.RepPlot("Layer b(h, W) — task 11", "h", "b")
    for W in (0.5, 1.0, 2.0)
        VFAPlot.add_series!(p, "W=$W", hs,
                            [Float64(L.b_layer(h, W * cfg.layer_W0; kw...)) for h in hs], 'l')
    end
    vfa_save_plot!(ctx, p, 1)
    ok = isempty(ctx.failures)
    VFALog.log_result(11, "layered_b", ok ? "PASS" : "FAIL", "", ctx.metrics)
    return ok
end

# ── задача 12: синхронизация Кирхгоф↔Родриг по слоям

function task12_layer_sync(cfg::VfaConfig)
    ctx = VfaTaskCtx(12, "layer_sync", cfg)
    L = VFALayer3D
    kw = (h0 = cfg.layer_h0, W0 = cfg.layer_W0)
    zs, hs, Ws = vfa_layer_profile(cfg)
    worst = maximum(L.sync_residual(h, W; kw...) for (h, W) in zip(hs, Ws))
    vfa_check(ctx, "sync |b_K − b_R| < 1e-15 для $(length(hs)) слоёв", worst < 1e-15,
              "max res = $worst")
    worst_E = 0.0
    rng = MersenneTwister(cfg.seed)
    for (h, W) in zip(hs, Ws)
        θ = asin(L.b_layer(h, W; kw...))
        u = randn(rng, 3)
        while norm(u) < 1e-10
            u = randn(rng, 3)
        end
        u ./= norm(u)
        w = randn(rng, 3)
        while norm(w) < 1e-10
            w = randn(rng, 3)
        end
        w ./= norm(w)
        r = L.layer_rodrigues_apply(u, w, θ)
        worst_E = max(worst_E, abs(norm(r) - norm(u)))
    end
    vfa_check(ctx, "Родриг сохраняет |u| на каждом слое", worst_E < 1e-12,
              "max = $worst_E")
    ok = isempty(ctx.failures)
    VFALog.log_result(12, "layer_sync", ok ? "PASS" : "FAIL", "", ctx.metrics)
    return ok
end

# ── задача 13: полное 3D-торможение (сумма по слоям)

function task13_total_braking(cfg::VfaConfig)
    ctx = VfaTaskCtx(13, "total_braking", cfg)
    L = VFALayer3D
    kw = (h0 = cfg.layer_h0, W0 = cfg.layer_W0)
    Ltr = 4.0
    zs, hs, Ws = L.default_profile(L = Ltr, N = cfg.layers, W0 = 0.5)
    # Γ_i отнесено к слою высоты dz: без веса Δz сумма растёт линейно по N
    # и «сходимость по N» невозможна; с Δz это средняя сумма → интеграл
    dz = Ltr / cfg.layers
    Γs = [1.0 * W^2 * dz for W in Ws]
    τ = L.total_braking(hs, Ws, Γs; kw...)
    vfa_check(ctx, "total braking τ < 0", τ < 0, "τ = $(round(τ; sigdigits = 6))")
    τ_2D = -L.b_base() * sum(Γs)
    vfa_check(ctx, "|τ3D| < |τ2D| (экран поверхности)", abs(τ) < abs(τ_2D),
              "|τ3D|=$(abs(τ)) < |τ2D|=$(abs(τ_2D))")
    τs = Float64[]
    for n in (5, 10, 20, 40, 80)
        _, hs_n, Ws_n = L.default_profile(L = Ltr, N = n, W0 = 0.5)
        Γs_n = [1.0 * W^2 * (Ltr / n) for W in Ws_n]
        push!(τs, L.total_braking(hs_n, Ws_n, Γs_n; kw...))
    end
    diffs = [abs(τs[i + 1] - τs[i]) for i in 1:length(τs) - 1]
    vfa_check(ctx, "сходимость по N (средние суммы → интеграл)",
              all(diffs[i + 1] < diffs[i] for i in 1:length(diffs) - 1),
              "diffs = $diffs")
    ctx.metrics["tau_3D"] = τ
    ctx.metrics["tau_2D"] = τ_2D
    ok = isempty(ctx.failures)
    VFALog.log_result(13, "total_braking", ok ? "PASS" : "FAIL", "", ctx.metrics)
    return ok
end

# ── задача 14: динамика 3D вихревого ствола

function task14_layered_evolution(cfg::VfaConfig)
    ctx = VfaTaskCtx(14, "layered_evolution", cfg)
    L = VFALayer3D
    kw = (h0 = cfg.layer_h0, W0 = cfg.layer_W0)
    zs, hs, Ws = L.default_profile(L = 4.0, N = cfg.layers, W0 = 0.5)
    Γs0 = [1.0 * W^2 for W in Ws]
    T, Nsteps = 10.0, 100
    hist = L.layered_evolution(hs, Ws, Γs0, T, Nsteps; kw...)
    n = length(hs)
    vfa_check(ctx, "каждый слой монотонно затухает",
              all(hist[i, end] < hist[i, 1] for i in 1:n))
    vfa_check(ctx, "Γ_i > 0 во все моменты", all(hist .> 0))
    totals = vec(sum(hist, dims = 1))
    vfa_check(ctx, "полная циркуляция убывает",
              all(totals[i + 1] < totals[i] for i in 1:length(totals) - 1))
    # за [0, T] слой затухает как e^{−b_i} (динамика dΓ/dt = −b Γ/T уже
    # включает интегрирование по времени) — лог-декремент БЕЗ деления на T;
    # сравниваем с Γ-взвешенным средним b (веса = Γ_0 = W²)
    total_rate = log(totals[1] / totals[end])
    w = [1.0 * Wi^2 for Wi in Ws]
    mean_b = sum(w[i] * L.b_layer(hs[i], Ws[i]; kw...) for i in 1:n) / sum(w)
    # Jensen: −ln⟨e^{−b}⟩ ≤ ⟨b⟩; зазор ≈ Var(b)/2 — на порядки меньше 0.1·mean_b
    vfa_check(ctx, "лог-декремент ≈ Γ-взвешенный mean(b) (Jensen-зазор мал)",
              abs(total_rate - mean_b) < 0.1 * mean_b,
              "rate=$(round(total_rate; sigdigits = 4)) mean_b=$(round(mean_b; sigdigits = 4))")
    ctx.metrics["mean_b"] = mean_b
    ctx.metrics["total_rate"] = total_rate
    p = VFAPlot.RepPlot("3D layered evolution — task 14", "t", "Γ_i")
    ts = collect(0:Nsteps) .* (T / Nsteps)
    for i in 1:min(5, n)
        VFAPlot.add_series!(p, "layer $i", ts, hist[i, :], 'l')
    end
    vfa_save_plot!(ctx, p, 1)
    ok = isempty(ctx.failures)
    VFALog.log_result(14, "layered_evolution", ok ? "PASS" : "FAIL", "", ctx.metrics)
    return ok
end

# ── задача 15: динамические тесты (fuzz + sweep + metamorphic)

function task15_dynamic(cfg::VfaConfig)
    ctx = VfaTaskCtx(15, "dynamic", cfg)
    L = VFALayer3D
    kw = (h0 = cfg.layer_h0, W0 = cfg.layer_W0)
    rng = MersenneTwister(cfg.seed)
    base_fuzz = cfg.preset == "quick" ? 100 : cfg.preset == "deep" ? 10000 : 1000
    n_fuzz = cfg.fuzz > 0 ? cfg.fuzz : base_fuzz * cfg.size
    b∞ = L.b_base()
    worst_sync = 0.0
    worst_bound = 0.0
    for _ in 1:n_fuzz
        h = exp(2 * randn(rng))
        W = exp(2 * randn(rng))
        bK = L.b_layer(h, W; kw...)
        bR = L.b_rodrigues_layer(h, W; kw...)
        worst_sync = max(worst_sync, abs(bK - bR))
        worst_bound = max(worst_bound, max(0.0, bK - b∞), max(0.0, -bK))
    end
    vfa_check(ctx, "fuzz ($n_fuzz): sync Кирхгоф↔Родриг", worst_sync < 1e-15)
    vfa_check(ctx, "fuzz: 0 ≤ b ≤ b∞", worst_bound < 1e-12)
    hs_sw = [10.0^(-2 + 0.15 * i) for i in 0:20]   # до 10^1: выше — сатурация
    bs_h = [L.b_layer(h, cfg.layer_W0; kw...) for h in hs_sw]
    vfa_check(ctx, "sweep по h (10^-2..10^1): монотонность",
              all(bs_h[i] < bs_h[i + 1] for i in 1:length(bs_h) - 1))
    Ws_sw = [10.0^(-2 + 0.15 * i) for i in 0:20]   # до 10^1: выше — вырожд. точность
    bs_W = [L.b_layer(cfg.layer_h0, W; kw...) for W in Ws_sw]
    vfa_check(ctx, "sweep по W (10^-2..10^1): монотонность",
              all(bs_W[i] > bs_W[i + 1] for i in 1:length(bs_W) - 1))
    b1 = L.b_layer(1.0, 1.0; h0 = 1.0)
    b2 = L.b_layer(2.0, 1.0; h0 = 2.0)
    vfa_check(ctx, "metamorphic: b(2h; 2h0) = b(h; h0)", abs(b1 - b2) < 1e-15)
    ok = isempty(ctx.failures)
    VFALog.log_result(15, "dynamic", ok ? "PASS" : "FAIL", "", ctx.metrics)
    return ok
end

VFA_N_TASKS = 15
TASKS = [
    Dict("id" => 1, "slug" => "constants", "title" => "Константная цепочка",
         "fn" => task01_constants, "pass2" => task01b_constants_hardcore),
    Dict("id" => 2, "slug" => "smagorinsky", "title" => "Мастер-соотношение C_s",
         "fn" => task02_smagorinsky, "pass2" => nothing),
    Dict("id" => 3, "slug" => "cassini", "title" => "Кассини (BigInt)",
         "fn" => task03_cassini, "pass2" => nothing),
    Dict("id" => 4, "slug" => "kdv", "title" => "KdV-солитон",
         "fn" => task04_kdv, "pass2" => nothing),
    Dict("id" => 5, "slug" => "klein_bridge", "title" => "Мост Клейна",
         "fn" => task05_klein_bridge, "pass2" => nothing),
    Dict("id" => 6, "slug" => "rodrigues", "title" => "Родриг",
         "fn" => task06_rodrigues, "pass2" => nothing),
    Dict("id" => 7, "slug" => "kirchhoff", "title" => "Кирхгоф RK4",
         "fn" => task07_kirchhoff, "pass2" => nothing),
    Dict("id" => 8, "slug" => "py_bridge", "title" => "Мост к Python-прогону",
         "fn" => task08_py_bridge, "pass2" => nothing),
    Dict("id" => 9, "slug" => "pinned", "title" => "Pinned-значения",
         "fn" => task09_pinned, "pass2" => nothing),
    Dict("id" => 10, "slug" => "suite", "title" => "Сводный численный прогон",
         "fn" => task10_suite, "pass2" => nothing),
    Dict("id" => 11, "slug" => "layered_b", "title" => "Слоистая b-поправка",
         "fn" => task11_layered_b, "pass2" => nothing),
    Dict("id" => 12, "slug" => "layer_sync", "title" => "Синхронизация К↔Р",
         "fn" => task12_layer_sync, "pass2" => nothing),
    Dict("id" => 13, "slug" => "total_braking", "title" => "Полное 3D-торможение",
         "fn" => task13_total_braking, "pass2" => nothing),
    Dict("id" => 14, "slug" => "layered_evolution", "title" => "Динамика 3D ствола",
         "fn" => task14_layered_evolution, "pass2" => nothing),
    Dict("id" => 15, "slug" => "dynamic", "title" => "Динамические тесты",
         "fn" => task15_dynamic, "pass2" => nothing)]
SUITE_IDS = [t["id"] for t in TASKS]

# ═══════════════════════════════════════════════════════════════════════════
# §31: бенчмарки точных решений (задачи 16–22) — аналитические решения
# уравнений Навье-Стокса/Эйлера/Бюргерса против дискретных операторов.
# Отдельный реестр: SUITE_IDS (1–15) не меняется (pinned, py_bridge, selftest).
# ═══════════════════════════════════════════════════════════════════════════

"периодический индекс 1..N (сетка [0,2π) с узлами (i-1)h)"
bench_pidx(i::Int, N::Int) = ((i - 1) % N + N) % N + 1

"точное поле Тейлора-Грина: u=sin x cos y, v=-cos x sin y · e^{-2νt}, p=…"
function bench_tg_fields(N::Int; nu = 1.0, t = 0.25)
    h = 2 * pi / N
    u = Array{Float64,2}(undef, N, N)
    v = Array{Float64,2}(undef, N, N)
    p = Array{Float64,2}(undef, N, N)
    e2 = exp(-2 * nu * t)
    e4 = exp(-4 * nu * t)
    for i in 1:N, j in 1:N
        x = (i - 1) * h
        y = (j - 1) * h
        u[i, j] = sin(x) * cos(y) * e2
        v[i, j] = -cos(x) * sin(y) * e2
        p[i, j] = (cos(2x) + cos(2y)) / 4 * e4
    end
    return u, v, p, h
end

"невязка дискретных НС на точном ТГ-поле (метод манифольда) + дивергенция"
function bench_tg_res(N::Int; nu = 1.0, t = 0.25)
    u, v, p, h = bench_tg_fields(N; nu = nu, t = t)
    res = 0.0
    div = 0.0
    hh = h * h
    for i in 1:N, j in 1:N
        ip = bench_pidx(i + 1, N); im = bench_pidx(i - 1, N)
        jp = bench_pidx(j + 1, N); jm = bench_pidx(j - 1, N)
        dxu = (u[ip, j] - u[im, j]) / (2h)
        dyu = (u[i, jp] - u[i, jm]) / (2h)
        dxv = (v[ip, j] - v[im, j]) / (2h)
        dyv = (v[i, jp] - v[i, jm]) / (2h)
        dxxu = (u[ip, j] - 2u[i, j] + u[im, j]) / hh
        dyyu = (u[i, jp] - 2u[i, j] + u[i, jm]) / hh
        dxxv = (v[ip, j] - 2v[i, j] + v[im, j]) / hh
        dyyv = (v[i, jp] - 2v[i, j] + v[i, jm]) / hh
        dxp = (p[ip, j] - p[im, j]) / (2h)
        dyp = (p[i, jp] - p[i, jm]) / (2h)
        ru = -2nu * u[i, j] + u[i, j] * dxu + v[i, j] * dyu + dxp -
             nu * (dxxu + dyyu)
        rv = -2nu * v[i, j] + u[i, j] * dxv + v[i, j] * dyv + dyp -
             nu * (dxxv + dyyv)
        res = max(res, abs(ru), abs(rv))
        div = max(div, abs(dxu + dyv))
    end
    return (res = res, div = div, h = h)
end

"точное поле Ковазная (Re): u=1-e^{λx}cos 2πy, v=(λ/2π)e^{λx}sin 2πy, p=(1-e^{2λx})/2"
function bench_kov_fields(N::Int; Re = 30.0)
    lam = Re / 2 - sqrt(Re^2 / 4 + 4 * pi^2)
    hx = 0.5 / N          # x ∈ [0, 0.5] (e^{λx} ≤ 1 — производные умеренные)
    hy = 1.0 / N          # y ∈ [0, 1]
    u = Array{Float64,2}(undef, N, N)
    v = Array{Float64,2}(undef, N, N)
    p = Array{Float64,2}(undef, N, N)
    for i in 1:N, j in 1:N
        x = (i - 1) * hx
        y = (j - 1) * hy
        E = exp(lam * x)
        u[i, j] = 1 - E * cos(2 * pi * y)
        v[i, j] = (lam / (2 * pi)) * E * sin(2 * pi * y)
        p[i, j] = (1 - exp(2 * lam * x)) / 2
    end
    return u, v, p, hx, hy, lam
end

"невязка стационарных НС на точном поле Ковазная; div — аналитически в узлах"
function bench_kov_res(N::Int; Re = 30.0)
    u, v, p, hx, hy, lam = bench_kov_fields(N; Re = Re)
    res = 0.0
    div = 0.0
    hxx = hx * hx
    hyy = hy * hy
    for i in 2:N-1, j in 1:N          # по x поле НЕпериодично (e^{λx}) — интерьер
        ip = i + 1; im = i - 1
        jp = bench_pidx(j + 1, N); jm = bench_pidx(j - 1, N)
        dxu = (u[ip, j] - u[im, j]) / (2hx)
        dyu = (u[i, jp] - u[i, jm]) / (2hy)
        dxv = (v[ip, j] - v[im, j]) / (2hx)
        dyv = (v[i, jp] - v[i, jm]) / (2hy)
        dxxu = (u[ip, j] - 2u[i, j] + u[im, j]) / hxx
        dyyu = (u[i, jp] - 2u[i, j] + u[i, jm]) / hyy
        dxxv = (v[ip, j] - 2v[i, j] + v[im, j]) / hxx
        dyyv = (v[i, jp] - 2v[i, j] + v[i, jm]) / hyy
        dxp = (p[ip, j] - p[im, j]) / (2hx)
        ru = u[i, j] * dxu + v[i, j] * dyu + dxp -
             (1 / Re) * (dxxu + dyyu)
        rv = u[i, j] * dxv + v[i, j] * dyv - (1 / Re) * (dxxv + dyyv)
        res = max(res, abs(ru), abs(rv))
        x = (i - 1) * hx
        y = (j - 1) * hy
        E = exp(lam * x)
        div = max(div, abs(-lam * E * cos(2 * pi * y) +
                           (lam / (2 * pi)) * E * 2 * pi * cos(2 * pi * y)))
    end
    return (res = res, div = div, hx = hx, hy = hy, lam = lam)
end

"осциллирующая стенка (Стокс II): FTCS до t_f=3T, профиль против точного"
function bench_stokes_run(N::Int)
    nu = 0.25; om = 1.0; U0 = 1.0
    k = sqrt(om / (2 * nu))
    L = 6.0 / k
    h = L / N
    dt = 0.4 * h * h / nu
    T = 2 * pi / om
    nsteps = ceil(Int, 3 * T / dt)
    tf = nsteps * dt
    u = zeros(N + 1)
    t = 0.0
    for n in 1:nsteps
        t = n * dt
        un = copy(u)
        u[1] = U0 * sin(om * t)
        for j in 2:N
            u[j] = un[j] + nu * dt / (h * h) * (un[j+1] - 2 * un[j] + un[j-1])
        end
        u[N+1] = 0.0
    end
    phi = om * tf
    uex(y) = U0 * exp(-k * y) * sin(phi - k * y)
    err = 0.0
    for j in 1:N+1
        err = max(err, abs(u[j] - uex((j - 1) * h)))
    end
    # периодичность: ещё один период — профиль должен повториться
    ub = copy(u)
    for n in 1:round(Int, T / dt)
        t = tf + n * dt
        un = copy(u)
        u[1] = U0 * sin(om * t)
        for j in 2:N
            u[j] = un[j] + nu * dt / (h * h) * (un[j+1] - 2 * un[j] + un[j-1])
        end
        u[N+1] = 0.0
    end
    err2 = maximum(abs.(u .- ub))
    deep = abs(u[round(Int, 3 / k / h) + 1] - U0 * exp(-3) * sin(phi - 3))
    return (err = err, err_period = err2, deep_err = deep,
            h = h, k = k, phi = phi, yg = [(j - 1) * h for j in 1:N+1],
            unum = copy(ub))
end

"энергетический инвариант Лере-Хопф на ТГ: E(t)=π²e^{-4νt}, dE/dt = -ν∫|∇u|²"
function bench_energy(N::Int; nu = 1.0, with_order = true)
    times = collect(0.0:0.002:0.25)   # мелкий шаг: dt²-ошибка трапеции ≪ h²-члена
    Es = Float64[]
    Zs = Float64[]
    for t in times
        u, v, _p, h = bench_tg_fields(N; nu = nu, t = t)
        area = (2 * pi)^2 / (N * N)
        E = 0.5 * area * (sum(abs2, u) + sum(abs2, v))
        Z = 0.0
        for i in 1:N, j in 1:N
            ip = bench_pidx(i + 1, N); im = bench_pidx(i - 1, N)
            jp = bench_pidx(j + 1, N); jm = bench_pidx(j - 1, N)
            dxu = (u[ip, j] - u[im, j]) / (2h)
            dyu = (u[i, jp] - u[i, jm]) / (2h)
            dxv = (v[ip, j] - v[im, j]) / (2h)
            dyv = (v[i, jp] - v[i, jm]) / (2h)
            Z += area * (dxu^2 + dyu^2 + dxv^2 + dyv^2)
        end
        push!(Es, E)
        push!(Zs, Z)
    end
    e_err = 0.0
    for (k, t) in enumerate(times)
        e_err = max(e_err, abs(Es[k] - pi^2 * exp(-4 * nu * t)))
    end
    integ = 0.0
    for k in 1:length(times)-1
        integ += (Zs[k] + Zs[k+1]) / 2 * (times[k+1] - times[k])
    end
    balance = abs(Es[end] - Es[1] + nu * integ)
    mono = true
    for k in 2:length(Es)
        Es[k] <= Es[k-1] + 1e-12 || (mono = false)
    end
    bal_order = 0.0
    if with_order
        # баланс на точном поле согласован с дискретной энстрофией лишь O(h²):
        # проверяем именно наблюдаемый порядок убывания невязки баланса
        b2 = bench_energy(2 * N; nu = nu, with_order = false).balance
        bal_order = log2(max(balance, 1e-300) / max(b2, 1e-300))
    end
    return (e_err = e_err, balance = balance, mono = mono,
            h = 2 * pi / N, bal_order = bal_order)
end

"ABC-поток (Бельтрами): дискретный rot, дивергенция, тождество Ламба"
function bench_abc_res(N::Int)
    h = 2 * pi / N
    u1 = Array{Float64,3}(undef, N, N, N)
    u2 = Array{Float64,3}(undef, N, N, N)
    u3 = Array{Float64,3}(undef, N, N, N)
    for i in 1:N, j in 1:N, k in 1:N
        x = (i - 1) * h; y = (j - 1) * h; z = (k - 1) * h
        u1[i, j, k] = sin(z) + cos(y)
        u2[i, j, k] = sin(x) + cos(z)
        u3[i, j, k] = sin(y) + cos(x)
    end
    curl = 0.0
    div = 0.0
    lamb = 0.0
    for i in 1:N, j in 1:N, k in 1:N
        ip = bench_pidx(i + 1, N); im = bench_pidx(i - 1, N)
        jp = bench_pidx(j + 1, N); jm = bench_pidx(j - 1, N)
        kp = bench_pidx(k + 1, N); km = bench_pidx(k - 1, N)
        dxu1 = (u1[ip, j, k] - u1[im, j, k]) / (2h)
        dyu1 = (u1[i, jp, k] - u1[i, jm, k]) / (2h)
        dzu1 = (u1[i, j, kp] - u1[i, j, km]) / (2h)
        dxu2 = (u2[ip, j, k] - u2[im, j, k]) / (2h)
        dyu2 = (u2[i, jp, k] - u2[i, jm, k]) / (2h)
        dzu2 = (u2[i, j, kp] - u2[i, j, km]) / (2h)
        dxu3 = (u3[ip, j, k] - u3[im, j, k]) / (2h)
        dyu3 = (u3[i, jp, k] - u3[i, jm, k]) / (2h)
        dzu3 = (u3[i, j, kp] - u3[i, j, km]) / (2h)
        curl = max(curl, abs((dyu3 - dzu2) - u1[i, j, k]),
                   abs((dzu1 - dxu3) - u2[i, j, k]),
                   abs((dxu2 - dyu1) - u3[i, j, k]))
        div = max(div, abs(dxu1 + dyu2 + dzu3))
        # тождество Ламба для Бельтрами: u·∇u = ∇(|u|²/2)
        qcp = (u1[i, j, k]^2 + u2[i, j, k]^2 + u3[i, j, k]^2) / 2
        qip = (u1[ip, j, k]^2 + u2[ip, j, k]^2 + u3[ip, j, k]^2) / 2
        qim = (u1[im, j, k]^2 + u2[im, j, k]^2 + u3[im, j, k]^2) / 2
        qjp = (u1[i, jp, k]^2 + u2[i, jp, k]^2 + u3[i, jp, k]^2) / 2
        qjm = (u1[i, jm, k]^2 + u2[i, jm, k]^2 + u3[i, jm, k]^2) / 2
        qkp = (u1[i, j, kp]^2 + u2[i, j, kp]^2 + u3[i, j, kp]^2) / 2
        qkm = (u1[i, j, km]^2 + u2[i, j, km]^2 + u3[i, j, km]^2) / 2
        dqpx = (qip - qim) / (2h)
        dqpy = (qjp - qjm) / (2h)
        dqpz = (qkp - qkm) / (2h)
        u1c = u1[i, j, k]; u2c = u2[i, j, k]; u3c = u3[i, j, k]
        lamb = max(lamb,
                   abs(u1c * dxu1 + u2c * dyu1 + u3c * dzu1 - dqpx),
                   abs(u1c * dxu2 + u2c * dyu2 + u3c * dzu2 - dqpy),
                   abs(u1c * dxu3 + u2c * dyu3 + u3c * dzu3 - dqpz))
    end
    return (curl = curl, div = div, lamb = lamb, h = h)
end

"стационарная вязкая ударная волна Бюргерса: прогон до установления"
function bench_burgers_run(N::Int)
    nu = 0.1; c = 1.0
    Lx = 4.0; h = Lx / N
    x = [-Lx / 2 + i * h for i in 0:N]
    uex(xv) = -c * tanh(c * xv / (2 * nu))
    u = [-tanh(c * xv / (2 * nu)) + 0.05 * sin(3 * xv) for xv in x]
    dt = 0.3 * h * h / nu
    nsteps = ceil(Int, 30.0 / dt)
    un = copy(u)
    resid = 0.0
    for n in 1:nsteps
        un = copy(u)
        for i in 2:N
            ux = un[i] > 0 ? (un[i] - un[i-1]) / h : (un[i+1] - un[i]) / h
            uxx = (un[i+1] - 2 * un[i] + un[i-1]) / (h * h)
            u[i] = un[i] - dt * un[i] * ux + dt * nu * uxx
        end
        u[1] = uex(-Lx / 2)
        u[N+1] = uex(Lx / 2)
        resid = maximum(abs.(u .- un)) / dt
    end
    err = maximum(abs.(u .- [uex(xv) for xv in x]))
    impulse = sum(u) * h - (u[1] + u[N+1]) * h / 2
    return (err = err, resid = resid, impulse = impulse, h = h,
            steps = nsteps)
end

"наблюдаемый порядок по Ричардсону: log2(res(N)/res(2N)) для ТГ и ABC"
function bench_richardson(N0::Int)
    r1 = bench_tg_res(N0).res; r2 = bench_tg_res(2 * N0).res
    r3 = bench_tg_res(4 * N0).res
    p_tg = (log2(r1 / r2), log2(r2 / r3))
    a1 = bench_abc_res(N0).curl; a2 = bench_abc_res(2 * N0).curl
    a3 = bench_abc_res(4 * N0).curl
    p_abc = (log2(a1 / a2), log2(a2 / a3))
    return (tg = p_tg, abc = p_abc, res_tg = (r1, r2, r3),
            res_abc = (a1, a2, a3), N0 = N0)
end

"задача 16: Тейлор-Грин — невязка дискретных НС на точном решении"
function task16_taylor_green(cfg::VfaConfig)
    ctx = VfaTaskCtx(16, "taylor_green", cfg)
    N = (cfg.preset == "quick" ? 16 : 32) * cfg.size
    N = clamp(N, 8, 128)
    r = bench_tg_res(N)
    r2 = bench_tg_res(max(4, div(N, 2)))
    order = log2(r2.res / r.res)
    vfa_check(ctx, "невязка дискретных НС < 3h² (2-й порядок)",
              r.res < 3 * r.h^2,
              "N=$N res=$(round(r.res; sigdigits = 3)) h²=$(round(r.h^2; sigdigits = 3))")
    vfa_check(ctx, "наблюдаемый порядок ≈ 2 (Ричардсон)",
              1.7 < order < 2.3, "p = $(round(order; sigdigits = 3))")
    vfa_check(ctx, "дискретная дивергенция < 1.5h²",
              r.div < 1.5 * r.h^2, "div = $(round(r.div; sigdigits = 3))")
    ctx.metrics["res_max"] = r.res
    ctx.metrics["order"] = order
    ctx.metrics["div_max"] = r.div
    p = VFAPlot.RepPlot("Тейлор-Грин: точные профили (Julia task 16)",
                        "x", "u, p")
    xg = [(i - 1) * r.h for i in 1:N]
    yy = pi / 3
    e2 = exp(-0.5); e4 = exp(-1.0)  # t=0.25, ν=1
    VFAPlot.add_series!(p, "u(x, y=π/3)",
                        xg, [sin(x) * cos(yy) * e2 for x in xg], 'l')
    VFAPlot.add_series!(p, "4p(x, y=π/3)",
                        xg, [(cos(2x) + cos(2yy)) * e4 for x in xg], 'l')
    vfa_save_plot!(ctx, p, 1)
    ok = isempty(ctx.failures)
    VFALog.log_result(16, "taylor_green", ok ? "PASS" : "FAIL", "", ctx.metrics)
    return ok
end

"задача 17: Ковазнай — стационарное точное решение НС"
function task17_kovasznay(cfg::VfaConfig)
    ctx = VfaTaskCtx(17, "kovasznay", cfg)
    N = (cfg.preset == "quick" ? 24 : 48) * cfg.size
    N = clamp(N, 12, 128)
    r = bench_kov_res(N)
    r2 = bench_kov_res(max(8, div(N, 2)))
    order = log2(max(r2.res, 1e-300) / max(r.res, 1e-300))
    vfa_check(ctx, "аналитическая дивергенция в узлах = 0 (machine)",
              r.div < 1e-12, "max = $(round(r.div; sigdigits = 3))")
    vfa_check(ctx, "невязка стационарных НС < 2000·max(hx,hy)²",
              r.res < 2000 * max(r.hx, r.hy)^2,
              "res = $(round(r.res; sigdigits = 3))")
    vfa_check(ctx, "наблюдаемый порядок ≈ 2 (Ричардсон)",
              1.7 < order < 2.5, "p = $(round(order; sigdigits = 3))")
    ctx.metrics["res_max"] = r.res
    ctx.metrics["order"] = order
    ctx.metrics["lambda"] = r.lam
    p = VFAPlot.RepPlot("Ковазнай Re=30: профили (Julia task 17)", "x", "u, v")
    xg = [(i - 1) * r.hx for i in 1:N]
    yy = 0.125
    E = [exp(r.lam * x) for x in xg]
    VFAPlot.add_series!(p, "u(x, y=0.125)",
                        xg, [1 - E[i] * cos(2 * pi * yy) for i in 1:N], 'l')
    VFAPlot.add_series!(p, "v(x, y=0.125)",
                        xg, [E[i] * (r.lam / (2 * pi)) * sin(2 * pi * yy)
                             for i in 1:N], 'l')
    vfa_save_plot!(ctx, p, 1)
    ok = isempty(ctx.failures)
    VFALog.log_result(17, "kovasznay", ok ? "PASS" : "FAIL", "", ctx.metrics)
    return ok
end

"задача 18: осциллирующая стенка (Стокс II) — FTCS против точного профиля"
function task18_stokes_wall(cfg::VfaConfig)
    ctx = VfaTaskCtx(18, "stokes_wall", cfg)
    N = (cfg.preset == "quick" ? 40 : 80) * cfg.size
    N = clamp(N, 20, 400)
    r = bench_stokes_run(N)
    vfa_check(ctx, "L∞ профиля против точного < 0.035",
              r.err < 0.035, "err = $(round(r.err; sigdigits = 3))")
    vfa_check(ctx, "периодичность: ещё T — профиль воспроизводится (< 0.005)",
              r.err_period < 0.005,
              "err_T = $(round(r.err_period; sigdigits = 3))")
    vfa_check(ctx, "глубина у=3/k: |u−e⁻³sin(φ−3)| < 0.02",
              r.deep_err < 0.02, "err = $(round(r.deep_err; sigdigits = 3))")
    ctx.metrics["err_linf"] = r.err
    ctx.metrics["k"] = r.k
    p = VFAPlot.RepPlot("Стокс II: профиль у стенки (Julia task 18)",
                        "y", "u")
    uex = [exp(-r.k * y) * sin(r.phi - r.k * y) for y in r.yg]
    VFAPlot.add_series!(p, "точный", r.yg, uex, 'l')
    VFAPlot.add_series!(p, "FTCS", r.yg, Float64.(r.unum), 'l')
    vfa_save_plot!(ctx, p, 1)
    ok = isempty(ctx.failures)
    VFALog.log_result(18, "stokes_wall", ok ? "PASS" : "FAIL", "", ctx.metrics)
    return ok
end

"задача 19: инвариант энергии Лере-Хопф на ТГ"
function task19_leray_energy(cfg::VfaConfig)
    ctx = VfaTaskCtx(19, "leray_energy", cfg)
    N = (cfg.preset == "quick" ? 16 : 24) * cfg.size
    N = clamp(N, 8, 64)
    r = bench_energy(N)
    vfa_check(ctx, "E(t) = π²e^{-4νt} (периодическая трапеция) < 1e-7",
              r.e_err < 1e-7, "err = $(round(r.e_err; sigdigits = 3))")
    vfa_check(ctx, "E монотонно не растёт (Лере-Хопф)", r.mono, "")
    vfa_check(ctx, "баланс E(t)-E(0)+ν∫|∇u|²: порядок убывания ≈ 2",
              1.7 < r.bal_order < 2.5,
              "p = $(round(r.bal_order; sigdigits = 3))")
    ctx.metrics["e_err"] = r.e_err
    ctx.metrics["balance"] = r.balance
    p = VFAPlot.RepPlot("Лере-Хопф: энергия ТГ (Julia task 19)", "t", "E")
    tg = [pi^2 * exp(-4 * t) for t in 0.0:0.05:0.25]
    VFAPlot.add_series!(p, "π²e^{-4νt}", collect(0.0:0.05:0.25), tg, 'l')
    vfa_save_plot!(ctx, p, 1)
    ok = isempty(ctx.failures)
    VFALog.log_result(19, "leray_energy", ok ? "PASS" : "FAIL", "", ctx.metrics)
    return ok
end

"задача 20: ABC-поток — Бельтрами, дивергенция, Ламба"
function task20_abc_beltrami(cfg::VfaConfig)
    ctx = VfaTaskCtx(20, "abc_beltrami", cfg)
    N = (cfg.preset == "quick" ? 10 : 16) * cfg.size
    N = clamp(N, 6, 40)
    r = bench_abc_res(N)
    r2 = bench_abc_res(max(4, div(N, 2)))
    order = log2(max(r2.curl, 1e-300) / max(r.curl, 1e-300))
    vfa_check(ctx, "rot_h u = u (Бельтрами) < 1.5h²",
              r.curl < 1.5 * r.h^2,
              "curl = $(round(r.curl; sigdigits = 3))")
    vfa_check(ctx, "наблюдаемый порядок ≈ 2", 1.7 < order < 2.3,
              "p = $(round(order; sigdigits = 3))")
    vfa_check(ctx, "div_h u < 1.5h²", r.div < 1.5 * r.h^2,
              "div = $(round(r.div; sigdigits = 3))")
    vfa_check(ctx, "тождество Ламба u·∇u = ∇(u²/2) < 12h²",
              r.lamb < 12 * r.h^2, "lamb = $(round(r.lamb; sigdigits = 3))")
    ctx.metrics["curl_max"] = r.curl
    ctx.metrics["lamb_max"] = r.lamb
    ctx.metrics["order"] = order
    p = VFAPlot.RepPlot("ABC: срез u₁(x, y=π/2, z=π/3) (Julia task 20)",
                        "x", "u₁")
    xg = [(i - 1) * r.h for i in 1:N]
    VFAPlot.add_series!(p, "sin z + cos y",
                        xg, [sin(pi / 3) + cos(pi / 2) for _ in xg], 'l')
    vfa_save_plot!(ctx, p, 1)
    ok = isempty(ctx.failures)
    VFALog.log_result(20, "abc_beltrami", ok ? "PASS" : "FAIL", "", ctx.metrics)
    return ok
end

"задача 21: ударная волна Бюргерса — прогон до установления"
function task21_burgers_shock(cfg::VfaConfig)
    ctx = VfaTaskCtx(21, "burgers_shock", cfg)
    N = (cfg.preset == "quick" ? 200 : 400) * cfg.size
    N = clamp(N, 100, 1600)
    r = bench_burgers_run(N)
    vfa_check(ctx, "установление: |Δu|/dt < 1e-6", r.resid < 1e-6,
              "resid = $(round(r.resid; sigdigits = 3))")
    vfa_check(ctx, "L∞ против точной волны < 0.06 (upwind O(h))",
              r.err < 0.06, "err = $(round(r.err; sigdigits = 3))")
    vfa_check(ctx, "импульс ∫u dx ≈ 0 (антисимметрия) < 1e-3",
              abs(r.impulse) < 1e-3, "I = $(round(r.impulse; sigdigits = 3))")
    ctx.metrics["err_linf"] = r.err
    ctx.metrics["steps"] = r.steps
    p = VFAPlot.RepPlot("Бюргерс: стационарная ударная волна (Julia task 21)",
                        "x", "u")
    xg = collect(-2.0:0.02:2.0)
    VFAPlot.add_series!(p, "точная: −tanh(x/0.2)",
                        xg, [-tanh(xv / 0.2) for xv in xg], 'l')
    vfa_save_plot!(ctx, p, 1)
    ok = isempty(ctx.failures)
    VFALog.log_result(21, "burgers_shock", ok ? "PASS" : "FAIL", "", ctx.metrics)
    return ok
end

"задача 22: сводный порядок сходимости (Ричардсон) для ТГ и ABC"
function task22_richardson(cfg::VfaConfig)
    ctx = VfaTaskCtx(22, "richardson", cfg)
    N0 = cfg.preset == "quick" ? 8 : 12
    r = bench_richardson(N0)
    vfa_check(ctx, "ТГ: обе пары порядков ∈ [1.7, 2.3]",
              all(1.7 < x < 2.3 for x in r.tg),
              "p = $(round.(collect(r.tg); sigdigits = 3))")
    vfa_check(ctx, "ABC: обе пары порядков ∈ [1.7, 2.3]",
              all(1.7 < x < 2.3 for x in r.abc),
              "p = $(round.(collect(r.abc); sigdigits = 3))")
    vfa_check(ctx, "невязки монотонно убывают (N, 2N, 4N)",
              r.res_tg[1] > r.res_tg[2] > r.res_tg[3] &&
              r.res_abc[1] > r.res_abc[2] > r.res_abc[3], "")
    ctx.metrics["p_tg"] = round.(collect(r.tg); digits = 3)
    ctx.metrics["p_abc"] = round.(collect(r.abc); digits = 3)
    ok = isempty(ctx.failures)
    VFALog.log_result(22, "richardson", ok ? "PASS" : "FAIL", "", ctx.metrics)
    return ok
end

VFA_BENCH = [
    Dict("id" => 16, "slug" => "taylor_green",
         "title" => "Тейлор-Грин: невязка дискретных НС",
         "fn" => task16_taylor_green, "pass2" => nothing),
    Dict("id" => 17, "slug" => "kovasznay",
         "title" => "Ковазнай: стационарное решение НС",
         "fn" => task17_kovasznay, "pass2" => nothing),
    Dict("id" => 18, "slug" => "stokes_wall",
         "title" => "Стокс II: осциллирующая стенка",
         "fn" => task18_stokes_wall, "pass2" => nothing),
    Dict("id" => 19, "slug" => "leray_energy",
         "title" => "Лере-Хопф: энергетический инвариант",
         "fn" => task19_leray_energy, "pass2" => nothing),
    Dict("id" => 20, "slug" => "abc_beltrami",
         "title" => "ABC: Бельтрами и тождество Ламба",
         "fn" => task20_abc_beltrami, "pass2" => nothing),
    Dict("id" => 21, "slug" => "burgers_shock",
         "title" => "Бюргерс: стационарная ударная волна",
         "fn" => task21_burgers_shock, "pass2" => nothing),
    Dict("id" => 22, "slug" => "richardson",
         "title" => "Ричардсон: сводный порядок сходимости",
         "fn" => task22_richardson, "pass2" => nothing),
]
BENCH_IDS = [t["id"] for t in VFA_BENCH]
VFA_ALL_IDS = vcat(SUITE_IDS, BENCH_IDS)

function vfa_find_task(id::Int)
    for t in TASKS
        t["id"] == id && return t
    end
    for t in VFA_BENCH
        t["id"] == id && return t
    end
    error("ERR_UNKNOWN_TASK $id")
end

"§5: двухпроходная обёртка с восстановлением cfg в finally"
function vfa_dispatch(id::Int, cfg::VfaConfig)
    t = vfa_find_task(id)
    # D: deepcopy — cfg.tasks/plot_formats/report_formats мутабельны;
    # shallow-копия хранила бы ссылки и «восстановление» не восстанавливало
    snapshot = Dict(f => deepcopy(getfield(cfg, f)) for f in fieldnames(VfaConfig))
    ok1 = try
        t["fn"](cfg)
    finally
        for f in fieldnames(VfaConfig)
            setfield!(cfg, f, snapshot[f])
        end
    end
    ok2 = true
    if t["pass2"] !== nothing && cfg.two_pass
        try
            ok2 = t["pass2"](cfg)
        finally
            for f in fieldnames(VfaConfig)
                setfield!(cfg, f, snapshot[f])
            end
        end
    end
    vfa_gc_full()
    return ok1 && ok2
end

# ═══════════════════════════════════════════════════════════════════════════
# Отчёты §8 (md/html/pdf; docx → ERR_UNSUPPORTED §1.4), манифест, JUnit
# ═══════════════════════════════════════════════════════════════════════════

function vfa_pdf_escape(s::AbstractString)
    out = IOBuffer()
    bad = 0
    for ch in s
        if 32 <= Int(ch) < 127
            print(out, ch)
        else
            bad += 1
            print(out, "?")
        end
    end
    bad > 0 && VFALog.log_comp("WARN pdf: $bad non-WinAnsi chars → '?'", "warn")
    return String(take!(out))
end

function vfa_write_pdf(path::AbstractString, lines::Vector{String})
    content = IOBuffer()
    y = 800
    for ln in lines
        y < 48 && break
        println(content, "BT /F1 9 Tf 40 $y Td ($(vfa_pdf_escape(first(ln, 105)))) Tj ET")
        y -= 11
    end
    body = String(take!(content))
    objs = String["<< /Type /Catalog /Pages 2 0 R >>",
                  "<< /Type /Pages /Kids [3 0 R] /Count 1 >>",
                  "<< /Type /Page /Parent 2 0 R /MediaBox [0 0 595 842] /Resources << /Font << /F1 5 0 R /F2 6 0 R >> >> /Contents 4 0 R >>",
                  "<< /Length $(length(body)) >>\nstream\n" * body * "endstream",
                  "<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica /Encoding /WinAnsiEncoding >>",
                  "<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica-Bold /Encoding /WinAnsiEncoding >>"]
    io = IOBuffer()
    write(io, "%PDF-1.4\n")
    offsets = Int[]
    for (i, objbody) in enumerate(objs)
        push!(offsets, position(io))
        println(io, "$i 0 obj")
        println(io, objbody)
        println(io, "endobj")
    end
    xref = position(io)
    println(io, "xref\n0 $(length(objs) + 1)\n0000000000 65535 f ")
    for off in offsets
        println(io, lpad(off, 10, "0") * " 00000 n ")
    end
    println(io, "trailer\n<< /Size $(length(objs) + 1) /Root 1 0 R >>\nstartxref\n$xref\n%%EOF")
    open(path, "w") do fh
        write(fh, take!(io))
    end
    return path
end

function vfa_write_reports(cfg::VfaConfig)
    VFALog.G.run_dir === nothing && return nothing
    rd = String(VFALog.G.run_dir)
    fr = joinpath(rd, "FINAL_REPORT")
    mkpath(fr)
    all_md = String["# VFA Julia · Итоговый отчёт", ""]
    for t in sort(TASKS; by = x -> x["id"])
        rec = get(VFALog.G.verdicts, t["id"], nothing)
        rec === nothing && continue
        push!(all_md, "---", "",
              "## task $(lpad(t["id"], 2, '0')) — $(t["title"])  `$(rec["verdict"])`",
              "", "- вердикт: **$(rec["verdict"])** $(rec["reason"])")
        for (k, v) in rec["metrics"]
            push!(all_md, "- `$k` = `$v`")
        end
    end
    if !isempty(VFA_RTM_ROWS)
        append!(all_md, ["", "## Трассировка требований (RTM)", "",
                         "| раздел | реализация | проверка |", "|---|---|---|"])
        for (sec, impl, chk) in VFA_RTM_ROWS
            push!(all_md, "| $sec | $impl | $chk |")
        end
    end
    md = join(all_md, "\n")
    # I: каждый формат пишется только если заявлен в --report-formats
    if "md" in cfg.report_formats
        open(joinpath(fr, "final_report.md"), "w") do fh
            write(fh, md)
        end
    end
    if "html" in cfg.report_formats
        open(joinpath(fr, "final_report.html"), "w") do fh
            write(fh, "<!doctype html><html><head><meta charset='utf-8'>" *
                      "<style>body{background:#12141c;color:#dce1f0;font-family:sans-serif}</style></head>" *
                      "<body><h1>VFA Julia Final Report</h1><pre>" *
                      replace(md, "<" => "&lt;") * "</pre></body></html>")
        end
    end
    if "pdf" in cfg.report_formats
        vfa_write_pdf(joinpath(fr, "final_report.pdf"), all_md)
    end
    if "docx" in cfg.report_formats
        println(stderr, "ERR_UNSUPPORTED docx: в stdlib Julia нет zip-writer — отчёт только md/html/pdf (§1.4)")
    end
    open(joinpath(fr, "full_run_log.txt"), "w") do fh
        for l in VFALog.G.comp
            println(fh, l)
        end
    end
    open(joinpath(rd, "MANIFEST.toml"), "w") do fh
        TOML.print(fh, Dict(
            "file" => Dict("path" => String(@__FILE__), "language" => "julia",
                           "lang_version" => string(VERSION)),
            "env" => Dict("platform" => VFAMon.platform_tag(),
                          "cpu_count" => Sys.CPU_THREADS),
            "seeds" => Dict("by_task" => Dict(string(t["id"]) =>
                                cfg.seed ⊻ (t["id"] * 0x9E3779B1) for t in TASKS)),
            "presets" => Dict("applied" => cfg.preset)))
    end
    fails = count(r -> r["verdict"] in ("FAIL", "ERROR"), values(VFALog.G.verdicts))
    open(joinpath(rd, "results.json"), "w") do fh
        write(fh, "{\"tasks\":{")
        firstv = true
        for (tid, rec) in sort(collect(VFALog.G.verdicts); by = first)
            firstv || write(fh, ",")
            # print с запятыми; slug/reason через vfa_json_str (кавычки, \n)
            print(fh, "\"", tid, "\":{\"slug\":", vfa_json_str(rec["slug"]), ",",
                  "\"verdict\":\"", rec["verdict"], "\",",
                  "\"reason\":", vfa_json_str(rec["reason"]), ",",
                  "\"duration_s\":", rec["duration_s"], "}")
            firstv = false
        end
        started = Libc.strftime("%Y-%m-%dT%H:%M:%S", VFALog.G.t0)
        finished = Libc.strftime("%Y-%m-%dT%H:%M:%S", time())
        write(fh, "},\"run\":{\"started_at\":\"", started,
              "\",\"finished_at\":\"", finished,
              "\",\"exit_code\":$(fails == 0 ? 0 : 1)",
              ",\"preset\":\"", cfg.preset,
              "\",\"two_pass\":", cfg.two_pass ? "true" : "false",
              ",\"platform\":\"", VFAMon.platform_tag(), "\"}}")
    end
    return nothing
end

"JSON-строка с экранированием (stdlib-JSON в Julia нет, §1.4)"
vfa_json_str(x::AbstractString) = "\"" *
    replace(replace(replace(replace(String(x), "\\" => "\\\\"),
                    "\"" => "\\\""), "\n" => "\\n"), "\t" => "\\t") * "\""

VFA_RTM_ROWS = [
    ("§0 режимы", "vfa_main: menu/library/CLI", "--self-test"),
    ("§2 слои", "модули VFAUI/VFAMon/VFAPlot/VFALog", "структура файла"),
    ("§5 two-pass", "vfa_dispatch + finally-restore", "--task 1"),
    ("§7 монитор", "VFAMon /proc", "--monitor panel"),
    ("§9 графика", "PNG stored-deflate (WARN §1.4), GIF LZW, 3×5 шрифт", "plots/*.png"),
    ("§10 память", "vfa_gc_full", "лог"),
    ("§11 CLI", "vfa_parse_args!", "--help"),
    ("§13 тайм-ауты", "кооперативный watchdog (между задачами / heartbeat)", "--task-timeout"),
    ("§16 вход", "include → автопрогон (VFA_AUTORUN); script → CLI; --menu → меню",
     "include / --menu / --ci"),
    ("§27 3D-слои", "VFALayer3D.b_layer(h,W), total_braking, layered_evolution",
     "--task 11 --task 15"),
    ("ЗАМЕНЫ §1.4", "zlib→stored-deflate; docx→ERR_UNSUPPORTED; JSON-cfg→TOML", "лог WARN")]

# ═══════════════════════════════════════════════════════════════════════════
# Прогон, меню, самотест, точка входа §16
# ═══════════════════════════════════════════════════════════════════════════

"уникальный каталог прогона (sweep может дать несколько прогонов в одну секунду)"
function vfa_new_run_dir(cfg::VfaConfig)
    base = joinpath(cfg.report_dir === nothing ? "results" : cfg.report_dir,
                    "jrun_$(Libc.strftime("%Y%m%d_%H%M%S", time()))")
    isdir(base) || return base
    for k in 2:1000
        isdir("$base-$k") || return "$base-$k"
    end
    return base * "-" * string(time_ns())
end

"§7: фоновый монитор; режим panel печатает строку VFAMon в stderr (B2)"
function vfa_monitor_start(cfg::VfaConfig, rd::AbstractString)
    interval = max(0.05, cfg.monitor_interval)
    if cfg.monitor == "on"
        @async begin
            try
                open(joinpath(rd, "logs", "monitor.csv"), "a") do fh
                    println(fh, "ts,cpu_percent,ram_used_gb")
                    while VFALog.G.run_dir !== nothing
                        s = VFAMon.snapshot()
                        cpu = s["cpu_percent"] === nothing ? "" :
                              string(round(s["cpu_percent"]; digits = 1))
                        ram = s["ram_used_gb"] === nothing ? "" :
                              string(round(s["ram_used_gb"]; digits = 3))
                        println(fh, "$(Libc.strftime("%H:%M:%S", time())),$cpu,$ram")
                        flush(fh)
                        sleep(interval)
                    end
                end
            catch e
                VFALog.log_comp("monitor: $e", "warn")
            end
        end
    elseif cfg.monitor == "panel"
        @async begin
            try
                while VFALog.G.run_dir !== nothing
                    line = join(VFAMon.panel(), " ")
                    print(stderr, "\r", rpad(first(line, 100), 100))
                    flush(stderr)
                    sleep(interval)
                end
                VFAUI.erase_line()
            catch e
                VFAUI.erase_line()
                VFALog.log_comp("monitor: $e", "warn")
            end
        end
    end
    return nothing
end

"§13: кооперативный watchdog — тайм-ауты между задачами и по heartbeat"
function vfa_watchdog_start(cfg::VfaConfig, t0::Float64)
    (cfg.task_timeout > 0 || cfg.global_timeout > 0) || return nothing
    interval = min(1.0, max(0.05, cfg.monitor_interval))
    @async begin
        try
            while VFALog.G.run_dir !== nothing && !VFALog.G.aborted
                if cfg.global_timeout > 0 && time() - t0 > cfg.global_timeout
                    VFALog.G.aborted = true
                    VFALog.log_comp("global-timeout $(cfg.global_timeout)s — прогон остановлен (кооперативно)",
                                    "warn")
                    break
                end
                if cfg.task_timeout > 0 && VFALog.G.current_task != "idle" &&
                   time() - VFALog.G.heartbeat > cfg.task_timeout
                    VFALog.G.aborted = true
                    VFALog.log_comp("task-timeout $(cfg.task_timeout)s — задача " *
                                    "'$(VFALog.G.current_task)' остановлена (кооперативно)",
                                    "warn")
                    break
                end
                sleep(interval)
            end
        catch
        end
    end
    return nothing
end

"один прогон: каталог, монитор, watchdog, цикл задач, отчёты"
function vfa_run_once(cfg::VfaConfig)
    ids = isempty(cfg.tasks) ? SUITE_IDS : filter(x -> x in VFA_ALL_IDS, cfg.tasks)
    rd = vfa_new_run_dir(cfg)
    VFALog.init_run!(rd; ci = cfg.ci)
    vfa_monitor_start(cfg, rd)
    vfa_watchdog_start(cfg, time())
    code = 1
    t00 = time()
    try
        done = 0
        for tid in ids
            t = vfa_find_task(tid)
            VFALog.open_task!(joinpath(rd, "task_$(lpad(tid, 2, '0'))_$(t["slug"])"),
                              t["slug"])
            tt = time()
            status, reason = "PASS", ""
            try
                ok = vfa_dispatch(tid, cfg)
                status = ok ? "PASS" : "FAIL"
            catch e
                status, reason = "ERROR", "EXCEPTION: $e"
                VFALog.log_comp("EXCEPTION: $e", "error")
            finally
                rec = get(VFALog.G.verdicts, tid, nothing)
                if rec !== nothing
                    rec["duration_s"] = round(time() - tt; digits = 3)
                    isempty(reason) || (rec["reason"] = reason)
                else
                    # задача упала до log_result — не даём ей исчезнуть из отчёта
                    VFALog.log_result(tid, t["slug"], status, reason,
                                      Dict{String, Any}(), time() - tt, String[])
                end
                VFALog.close_task!()
            end
            done += 1
            if cfg.monitor == "on" && !cfg.ci
                print(stderr, VFAUI.bar_line(done, length(ids), t["slug"], "", t00))
                flush(stderr)
            end
            VFALog.G.aborted && break
        end
        (cfg.monitor == "on" && !cfg.ci) && VFAUI.erase_line()
        fails = count(r -> r["verdict"] in ("FAIL", "ERROR"), values(VFALog.G.verdicts))
        code = (fails == 0 && !VFALog.G.aborted) ? 0 : 1
        VFALog.G.aborted &&
            VFALog.log_comp("run aborted: тайм-аут/прерывание, exit_code=$code", "warn")
        VFALog.log_comp("run finished: exit_code=$code")
        # B1: флаг --no-report наконец действует
        cfg.no_report || vfa_write_reports(cfg)
        cfg.junit !== nothing && vfa_write_junit(cfg, String(cfg.junit))
        # B-NEW-8: мёртвый vortex-хук удалён — vfa_main при vortex_N > 0
        # всегда уходит в vfa_vortex_cli раньше dispatch, сюда не доходит;
        # рендер в каталоге прогона больше не обещается (см. NOTE в --help)
    finally
        # баг 3: даже при исключении монитор и watchdog не остаются висеть
        VFALog.finish!()
        VFALog.G.run_dir = nothing        # останавливает монитор-таск (§7)
        vfa_gc_full()
    end
    return code
end

function vfa_run_all(cfg::VfaConfig)
    isempty(strip(cfg.sweep)) && return vfa_run_once(cfg)
    # §30: --sweep → многомерный эксперимент VFALab (декартово произведение,
    # изолированные комбинации в results/lab_*, индексы experiment.md/.toml)
    return VFALab.run_experiment(cfg, VFALab.lab_parse_sweeps(cfg.sweep; cfg = cfg))
end

function vfa_write_junit(cfg::VfaConfig, path::AbstractString)
    io = IOBuffer()
    println(io, "<?xml version=\"1.0\" encoding=\"UTF-8\"?>\n<testsuite name=\"vfa-jl\">")
    for (tid, rec) in sort(collect(VFALog.G.verdicts); by = first)
        failed = rec["verdict"] in ("FAIL", "ERROR")
        println(io, "<testcase classname=\"vfa.task$(lpad(tid, 2, '0'))\" " *
                "name=\"$(rec["slug"])\" time=\"$(rec["duration_s"])\"" *
                (failed ? "><failure/></testcase>" : "/>"))
    end
    println(io, "</testsuite>")
    open(path, "w") do fh
        write(fh, take!(io))
    end
    return path
end

function vfa_selftest(cfg::VfaConfig)
    results = Tuple{String, Bool}[]
    tmp = tempname()
    cv = VFAPlot.Canvas(16, 16, (1, 2, 3))
    VFAPlot.save_png(tmp * ".png", cv)
    pngmagic = UInt8[0x89, 0x50, 0x4E, 0x47, 0x0D, 0x0A, 0x1A, 0x0A]
    push!(results, ("png magic", read(tmp * ".png", 8) == pngmagic))
    fr = [VFAPlot.Canvas(8, 8, (0, 0, 0)) for _ in 1:2]
    VFAPlot.save_gif(tmp * ".gif", fr)
    push!(results, ("gif magic", startswith(String(read(tmp * ".gif", 6)), "GIF89a")))
    ok_arcsin = setprecision(BigFloat, 60) do
        abs(Float64(vfa_arcsin_series(BigFloat(vfa_b_float()))) -
            asin(vfa_b_float())) < 1e-14
    end
    push!(results, ("arcsin ≈ asin", ok_arcsin))
    # G: не хардкодить 10 — реестр растёт (§27 добавил 11–15)
    push!(results, ("реестр задач", length(TASKS) == VFA_N_TASKS &&
                                    SUITE_IDS == collect(1:VFA_N_TASKS)))
    if cfg.selftest_props
        rng = MersenneTwister(cfg.seed)
        worst = 0.0
        for _ in 1:1000
            w = randn(rng, 3)
            norm(w) < 1e-10 && continue
            w ./= norm(w)
            u = randn(rng, 3)
            r = vfa_rodrigues_apply(u, w, cos(0.7), sin(0.7))
            worst = max(worst, abs(norm(r) - norm(u)))
        end
        push!(results, ("props: Родриг |u′|=|u| ×1000", worst < 1e-12))
        worst_b = 0.0
        for _ in 1:1000
            h, W = exp(2 * randn(rng)), exp(2 * randn(rng))
            b = VFALayer3D.b_layer(h, W)
            worst_b = max(worst_b, max(0.0, b - VFALayer3D.b_base()), max(0.0, -b))
        end
        push!(results, ("props: 0 ≤ b ≤ b∞ ×1000", worst_b < 1e-12))
        push!(results, ("props: Кассини k=0..100",
                        all(vfa_fib(k + 1)^2 - vfa_fib(k) * vfa_fib(k + 2) == (-1)^k
                            for k in 0:100)))
    end
    if cfg.selftest_contract
        push!(results, ("contract: slugs уникальны",
                        length(unique(t["slug"] for t in TASKS)) == length(TASKS)))
        push!(results, ("contract: ids 1..N без пропусков",
                        SUITE_IDS == collect(1:length(TASKS))))
        push!(results, ("contract: completions bash/fish/zsh",
                        all(sh -> try
                                    occursin("verify_ns_full", vfa_completions(sh))
                                catch
                                    false
                                end, ("bash", "zsh", "fish"))))
        push!(results, ("contract: help описывает флаги §27/§27b",
                        occursin("--layers", VFA_HELP) && occursin("--fuzz", VFA_HELP) &&
                        occursin("--sweep", VFA_HELP) && occursin("--vortex", VFA_HELP)))
    end
    # §28: баннер и служебные поля (без stdin — не падают)
    push!(results, ("banner: непустой, содержит платформу/версию",
                    begin
                        ls = VFABanner.banner_lines(subtitle = "test")
                        !isempty(ls) && any(occursin("julia ", l) for l in ls) &&
                            any(occursin("Navier-Stokes-B", l) for l in ls)
                    end))
    push!(results, ("banner: plain → ASCII-only",
                    all(all(c -> Int(c) < 128, l) for l in
                        VFABanner.banner_lines(plain = true))))
    push!(results, ("banner: cfg.banner ∈ auto|always|never",
                    cfg.banner in ("auto", "always", "never")))
    push!(results, ("detect_tty: возвращает Bool", isa(vfa_detect_tty(), Bool)))
    push!(results, ("menu§29: дерево/навигация goto!/pop!",
                    begin
                        VFAMenu.build_tree!(cfg)
                        ok = haskey(VFAMenu.NODES, :root) &&
                             !isempty(VFAMenu.NODES[:root].items)
                        st = VFAMenu.MenuState(VFAMenu.NODES, :root, Symbol[:root],
                                               Symbol[], Dict{Symbol, Any}(), false)
                        ok = ok && VFAMenu.goto!(st, :root) && VFAMenu.pop!(st) &&
                                  st.current == :root
                        ok2 = haskey(VFAMenu.NODES, :settings) &&
                              haskey(VFAMenu.NODES, :results) &&
                              haskey(VFAMenu.NODES, :diag)
                        ok && ok2
                    end))
    push!(results, ("menu§29: настройки (set/цикл) + parse_results",
                    begin
                        specs = VFAMenu.settings_specs()
                        ok1 = length(specs) >= 12
                        c2 = deepcopy(cfg)
                        sp2 = only(filter(x -> x.field === :two_pass, specs))
                        ok1 &= VFAMenu.set_setting!(c2, sp2, "off") && c2.two_pass == false
                        ok1 &= VFAMenu.set_setting!(c2, sp2, "on") && c2.two_pass == true
                        sp3 = only(filter(x -> x.field === :theme, specs))
                        ok1 &= VFAMenu.set_setting!(c2, sp3, "ice") && c2.theme == "ice"
                        ok1 &= Main.VFAUI.state[:theme] == "ice"
                        Main.VFAUI.state[:theme] = cfg.theme   # вернуть как было
                        tmp = joinpath(tempdir(), "vfa_menu_selftest_results.json")
                        open(tmp, "w") do fh
                            write(fh, "{\"tasks\":{\"9\":{\"slug\":\"t9\",\"verdict\":\"PASS\"," *
                                   "\"reason\":\"ok\",\"duration_s\":1.5}}}")
                        end
                        ri = VFAMenu.parse_results(tmp)
                        rm(tmp; force = true)
                        ok1 && get(ri.verdicts, 9, "") == "PASS" &&
                            get(ri.durs, 9, 0.0) == 1.5
                    end))
    push!(results, ("lab§30: свипы/декартово/конвертация/TOML",
                    begin
                        exp = VFALab.lab_parse_sweeps("preset=quick,full;seed=1,2"; cfg = cfg)
                        ok1 = length(exp.sweeps) == 2 &&
                              exp.sweeps[2].values == ["1", "2"]
                        ok1 &= length(VFALab.lab_cartesian(exp.sweeps)) == 4
                        ok1 &= VFALab.lab_convert(cfg, :seed, "42") == 42
                        ok1 &= VFALab.lab_convert(cfg, :two_pass, "off") == false
                        ok1 &= VFALab.lab_convert(cfg, :task_timeout, "12.5") == 12.5
                        ok1 &= VFALab.lab_convert(cfg, :layers, "30") == 30
                        ok1 &= VFALab.lab_convert(cfg, :tasks, "2,9") == [2, 9]
                        ok1 &= VFALab.lab_convert(cfg, :theme, "ice") == "ice"
                        ok2 = try
                            VFALab.lab_convert(cfg, :report_dir, "x"); false
                        catch
                            true
                        end
                        tmp = joinpath(tempdir(), "vfa_selftest_exp.toml")
                        open(tmp, "w") do fh
                            write(fh, "[[sweep]]\nkey = \"preset\"\nvalues = [\"quick\", \"full\"]\n" *
                                      "[[sweep]]\nkey = \"seed\"\nvalues = [1, 2]\n" *
                                      "[base]\nseed = 42\ntasks = [2, 9]\n")
                        end
                        e2 = VFALab.lab_from_toml(tmp)
                        rm(tmp; force = true)
                        ok1 && ok2 && length(e2.sweeps) == 2 &&
                            e2.sweeps[2].values == ["1", "2"] &&
                            length(e2.base) == 2
                    end))
    push!(results, ("bench§31: точные решения 16–22",
                    begin
                        okb = true
                        rt = bench_tg_res(8)
                        okb &= rt.res < 3 * rt.h^2 && rt.div < 1.5 * rt.h^2
                        r8 = bench_tg_res(8).res; r16 = bench_tg_res(16).res
                        okb &= 1.7 < log2(r8 / r16) < 2.3
                        rk = bench_kov_res(16)
                        okb &= rk.div < 1e-12 && rk.res < 2000 * rk.hx^2
                        st = bench_stokes_run(40)
                        okb &= st.err < 0.05 && st.err_period < 0.005
                        en = bench_energy(8)
                        okb &= en.e_err < 1e-7 && en.mono &&
                               1.5 < en.bal_order < 2.6
                        ra = bench_abc_res(6)
                        okb &= ra.curl < 1.5 * ra.h^2 && ra.div < 1.5 * ra.h^2
                        bu = bench_burgers_run(80)
                        okb &= bu.resid < 1e-6 && bu.err < 0.08 &&
                               abs(bu.impulse) < 1e-3
                        rr = bench_richardson(6)
                        okb &= all(1.5 < x < 2.5 for x in rr.tg) &&
                               all(1.5 < x < 2.5 for x in rr.abc)
                        okb
                    end))
    push!(results, ("cross§32: вердикты/results.json-схема",
                    begin
                        tmp = joinpath(tempdir(), "vfa_xcheck.json")
                        open(tmp, "w") do fh
                            write(fh, "{\"tasks\": {\"1\": {\"task\": 1, \"slug\": \"constants\", " *
                                      "\"verdict\": \"PASS\", \"reason\": \"\", \"metrics\": {}, " *
                                      "\"duration_s\": 0.1, \"artifacts\": []}, \"4\": {\"task\": 4, " *
                                      "\"slug\": \"kdv\", \"verdict\": \"FAIL\", \"reason\": \"x\", " *
                                      "\"metrics\": {}, \"duration_s\": 0.2, \"artifacts\": []}}, " *
                                      "\"run\": {\"exit_code\": 1, \"preset\": \"full\"}}")
                        end
                        pv = vfa_parse_verdicts(read(tmp, String))
                        rm(tmp; force = true)
                        ok1 = length(pv) == 2 && pv[1] == "PASS" && pv[4] == "FAIL"
                        ok2 = vfa_json_str("a\"b\\c") == "\"a\\\"b\\\\c\""
                        ok1 && ok2
                    end))
    # §27b: изолированный рендер кадра вихря (маленькая сетка, быстро)
    push!(results, ("vortex§27b: изолированный рендер кадра",
                    begin
                        ok_v = try
                            hs_v, Ws_v, Γs_v = VFAVortex3D.vortex_preset(nlayers = 8)
                            cv_v = VFAVortex3D.render_frame(48, Γs_v, hs_v, Ws_v;
                                                            width = 320, height = 240,
                                                            title = "selftest", sub = "")
                            cv_v.w == 320 && cv_v.h == 240 &&
                                length(cv_v.buf) == 320 * 240 * 3
                        catch
                            false
                        end
                        ok_v
                    end))
    push!(results, ("vortex§27b: analyze_evolution даёт монотонное затухание",
                    begin
                        ok_a = try
                            hs_v, Ws_v, Γs_v = VFAVortex3D.vortex_preset(nlayers = 8)
                            an = VFAVortex3D.analyze_evolution(hs_v, Ws_v, Γs_v,
                                                               40.0, 12)
                            length(an.frames) == 12 &&
                                an.frames[end].G_total < an.frames[1].G_total &&
                                an.verdict in ("STABILIZED", "DAMPED",
                                               "DECAYING", "PERSISTENT") &&
                                (an.milestones.t50 === nothing ||
                                 0.0 < an.milestones.t50 <= 40.0)
                        catch
                            false
                        end
                        ok_a
                    end))
    push!(results, ("plot§9: GIF LZW encode→decode round-trip (рост 9→12, сброс 4096)",
                    begin
                        ok_l = try
                            rnd = UInt8.(rand(MersenneTwister(2026), 0:255, 60000))
                            dec = VFAPlot.lzw_decode_ref(VFAPlot.lzw(rnd, 8), 8,
                                                         length(rnd))
                            dec == rnd
                        catch
                            false
                        end
                        ok_l
                    end))
    push!(results, ("vortex§27b: frame_nonbg отличает пустой кадр от точки",
                    begin
                        blank_v = VFAPlot.Canvas(40, 30, VFAVortex3D.BG_DARK)
                        dotted_v = VFAPlot.Canvas(40, 30, VFAVortex3D.BG_DARK)
                        dotted_v.buf[(15 * 40 + 20) * 3 + 1] = 0xFF
                        dotted_v.buf[(15 * 40 + 20) * 3 + 2] = 0x8C
                        dotted_v.buf[(15 * 40 + 20) * 3 + 3] = 0x69
                        VFAVortex3D.frame_nonbg(blank_v) == 0 &&
                            VFAVortex3D.frame_nonbg(dotted_v) == 1
                    end))
    # §4.4: aurora-стиль отчёта самотеста (стикеры + спарклайн-вердикты)
    npass = count(r -> r[2], results)
    mode = (cfg.selftest_props ? "+props" : "") *
           (cfg.selftest_contract ? "+contract" : "")
    badge_str = npass == length(results) ?
                VFAUI.sticker(1) * " PASS " * VFAUI.sticker(3) :
                VFAUI.sticker(6) * " FAIL " * VFAUI.sticker(6)
    println(VFAUI.aurora_title("SELFTEST" * mode), " ", badge_str,
            "  $npass/", length(results))
    println("  ", VFAUI.aurora_sep())
    for (name, ok) in results
        println("  ", VFAUI.sparkline_verdict(ok ? "PASS" : "FAIL"), " ", name)
    end
    return npass == length(results) ? 0 : 1
end

VFA_RU = Dict('й' => 'q', 'ц' => 'w', 'у' => 'e', 'к' => 'r', 'е' => 't', 'н' => 'y',
              'г' => 'u', 'ш' => 'i', 'щ' => 'o', 'з' => 'p', 'ф' => 'a', 'ы' => 's',
              'в' => 'd', 'а' => 'f', 'п' => 'g', 'р' => 'h', 'о' => 'j', 'л' => 'k',
              'д' => 'l', 'я' => 'z', 'ч' => 'x', 'с' => 'c', 'м' => 'v', 'и' => 'b',
              'т' => 'n', 'ь' => 'm',
              'ё' => '`', 'х' => '[', 'ъ' => ']', 'ж' => ';', 'э' => '\'',
              'б' => ',', 'ю' => '.')

VFA_HELP_KEYS = Dict(
    "ru" => "Клавиши: [a] все задачи  [N] задача N  [r] повтор последней  [p] пресет\n" *
            "  [2] two-pass вкл/выкл  [th] тема  [v] 3D-вихрь (GIF, N ≥ 24)\n" *
            "  [l] последние результаты  [c] конфиг  [t] самотест  [?] эта справка  [q] выход",
    "en" => "Keys: [a] all tasks  [N] task N  [r] rerun last  [p] preset\n" *
            "  [2] toggle two-pass  [th] theme  [v] 3D vortex (GIF, N ≥ 24)\n" *
            "  [l] last run results  [c] config  [t] self-test  [?] this help  [q] quit")

"§28: выбор значения из списка (меню [p]); Ctrl+C уходит в меню"
function vfa_choose(cfg::VfaConfig, what::AbstractString, options)
    while true
        println(join(options, ", ") * ":")
        print("  > ")
        line = ""
        try
            line = lowercase(strip(readline(stdin)))
        catch
            continue
        end
        line in options && return String(line)
        println("  ? ", line)
    end
end

"§27b: каталог вывода вихря (report_dir/vortex или results/vortex)"
vfa_vortex_dir(cfg::VfaConfig) = joinpath(
    cfg.report_dir === nothing ? "results" : String(cfg.report_dir), "vortex")

# Число в JSON: inf/nan → null (строгий JSON); round до 6 знаков
_vfa_jfm(x::Nothing) = "null"
function _vfa_jfm(x::Real)
    v = Float64(x)
    (isnan(v) || isinf(v)) && return "null"
    return string(round(v; digits = 6))
end

"§27b: companion-отчёт (MD + JSON) рядом с GIF: per-layer таблица,
milestones, временная серия, вердикт. JSON — вручную (в stdlib нет JSON)."
function vfa_vortex_write_report(analysis, gif_path::AbstractString)
    base = splitext(String(gif_path))[1]
    md_path = base * ".md"
    json_path = base * ".json"
    ms = analysis.milestones
    lines = String[
        "# 3D Vortex — Stabilization Report",
        "",
        "- layers: $(analysis.n), frames: $(analysis.nframes), T: $(round(analysis.T; digits = 1))",
        "- mean_b (Γ-weighted): $(round(analysis.mean_b; digits = 6))",
        "- final Γ/Γ₀: $(round(100 * analysis.final_frac; digits = 2))%",
        "- **verdict: $(analysis.verdict)**",
        "",
        "## Milestones",
        "",
        "| threshold | t |",
        "|---|---|",
    ]
    for (label, v) in (("50% Γ (half-life)", ms.t50), ("10% Γ", ms.t10),
                       ("1% Γ", ms.t01))
        push!(lines, "| $label | " *
                     (v === nothing ? "> T = $(round(analysis.T; digits = 1))" :
                      string(round(v; digits = 3))) * " |")
    end
    push!(lines, "")
    push!(lines, "## Per-layer")
    push!(lines, "")
    push!(lines, "| i | h | W | b_i | half-life | Γ₀ | Γ_T |")
    push!(lines, "|---|---|---|---|---|---|---|")
    for L in analysis.layers
        hl = L.halflife == Inf ? "∞" : string(round(L.halflife; digits = 2))
        push!(lines, "| $(L.i) | $(round(L.h; digits = 3)) | " *
                     "$(round(L.W; digits = 3)) | $(round(L.b; digits = 5)) | " *
                     "$hl | $(round(L.G0; digits = 3)) | " *
                     "$(round(L.G_end; digits = 4)) |")
    end
    push!(lines, "")
    push!(lines, "## Time series")
    push!(lines, "")
    push!(lines, "| t | Γ_total | % of Γ₀ | v_peak |")
    push!(lines, "|---|---|---|---|")
    for f in analysis.frames
        push!(lines, "| $(round(f.t; digits = 3)) | " *
                     "$(round(f.G_total; digits = 4)) | " *
                     "$(round(100 * f.G_frac; digits = 2))% | " *
                     "$(round(f.v_peak; digits = 4)) |")
    end
    open(md_path, "w") do fh
        foreach(ln -> println(fh, ln), lines)
    end
    jio = IOBuffer()
    println(jio, "{")
    println(jio, "  \"n\": $(analysis.n),")
    println(jio, "  \"T\": $(_vfa_jfm(analysis.T)),")
    println(jio, "  \"nframes\": $(analysis.nframes),")
    println(jio, "  \"mean_b\": $(_vfa_jfm(analysis.mean_b)),")
    println(jio, "  \"final_frac\": $(_vfa_jfm(analysis.final_frac)),")
    println(jio, "  \"verdict\": \"$(analysis.verdict)\",")
    println(jio, "  \"milestones\": {\"t50\": $(_vfa_jfm(ms.t50)), " *
                 "\"t10\": $(_vfa_jfm(ms.t10)), \"t01\": $(_vfa_jfm(ms.t01))},")
    println(jio, "  \"layers\": [")
    for (k, L) in enumerate(analysis.layers)
        comma = k < length(analysis.layers) ? "," : ""
        println(jio, "    {\"i\": $(L.i), \"h\": $(_vfa_jfm(L.h)), " *
                     "\"W\": $(_vfa_jfm(L.W)), \"b\": $(_vfa_jfm(L.b)), " *
                     "\"halflife\": $(_vfa_jfm(L.halflife)), " *
                     "\"G0\": $(_vfa_jfm(L.G0)), \"G_end\": $(_vfa_jfm(L.G_end))}$comma")
    end
    println(jio, "  ],")
    println(jio, "  \"frames\": [")
    for (k, f) in enumerate(analysis.frames)
        comma = k < length(analysis.frames) ? "," : ""
        println(jio, "    {\"i\": $(f.i), \"frac\": $(_vfa_jfm(f.frac)), " *
                     "\"t\": $(_vfa_jfm(f.t)), \"G_total\": $(_vfa_jfm(f.G_total)), " *
                     "\"v_peak\": $(_vfa_jfm(f.v_peak)), " *
                     "\"G_frac\": $(_vfa_jfm(f.G_frac))}$comma")
    end
    println(jio, "  ]")
    println(jio, "}")
    open(json_path, "w") do fh
        write(fh, take!(jio))
    end
    return md_path, json_path
end

"§27b: короткая числовая сводка стабилизации (stderr)."
function vfa_vortex_print_summary(analysis; io = stderr)
    frames, ms = analysis.frames, analysis.milestones
    println(io, "\n  ── stabilization summary ──")
    println(io, "  Γ_total: $(round(frames[1].G_total; digits = 3)) → ",
            "$(round(frames[end].G_total; digits = 4)) ",
            "($(round(100 * analysis.final_frac; digits = 2))%)")
    println(io, "  mean_b: $(round(analysis.mean_b; digits = 6))")
    for (label, v) in (("t50 (half-life)", ms.t50),
                       ("t10 (90% decayed)", ms.t10),
                       ("t01 (99% decayed)", ms.t01))
        println(io, "  $label: " *
                (v === nothing ? "> T = $(round(analysis.T; digits = 1))" :
                 "t = $(round(v; digits = 3))"))
    end
    println(io, "  verdict: ", analysis.verdict)
    println(io, "    i       h       W         b   halflife      G_end")
    for L in analysis.layers
        hl = L.halflife == Inf ? "∞" : string(round(L.halflife; digits = 2))
        println(io, "  $(lpad(L.i, 3)) $(lpad(round(L.h; digits = 3), 7)) ",
                "$(lpad(round(L.W; digits = 3), 7)) ",
                "$(lpad(round(L.b; digits = 5), 9)) ",
                "$(lpad(hl, 9)) ",
                "$(lpad(round(L.G_end; digits = 4), 9))")
    end
    println(io)
end

"§27b: интерактивный рендер 3D-вихря (пункт [v] меню, legacy и TUI);
N ∈ [24, ∞), clamp до 256 — защита памяти; после рендера — отчёт и сводка"
function vfa_menu_vortex(cfg::VfaConfig, _s = nothing)
    println(VFAUI.aurora_title(fmt(cfg, "vortex_title")))
    print("  ", fmt(cfg, "vortex_n"))
    line = try
        strip(readline(stdin))
    catch
        ""
    end
    N = try
        parse(Int, line)
    catch
        48
    end
    if N < 24
        println("  ? ", fmt(cfg, "vortex_bad"))
        return
    end
    if N > 256
        println("  ", fmt(cfg, "vortex_clamp"))
        N = 256
    end
    print("  ", fmt(cfg, "vortex_frames_prompt"))
    fline = try
        strip(readline(stdin))
    catch
        ""
    end
    nframes = try
        max(2, min(240, parse(Int, fline)))
    catch
        24
    end
    mkpath(vfa_vortex_dir(cfg))
    path = joinpath(vfa_vortex_dir(cfg),
                    "vortex_N$(N)_$(Libc.strftime("%Y%m%d_%H%M%S", time())).gif")
    t_bar = time()
    print(stderr, VFAUI.bar_line(0, nframes, "vortex", "  N=$N", t_bar))
    flush(stderr)
    res = VFAVortex3D.render_vortex_animation(path;
                                              N = N, nframes = nframes,
                                              T = cfg.vortex_T,
                                              h0 = cfg.layer_h0, W0 = cfg.layer_W0,
                                              callback = (k, n) -> begin
                                                  (k % 2 == 0 || k == n) || return
                                                  print(stderr,
                                                        VFAUI.bar_line(k, n,
                                                                       "vortex",
                                                                       "  N=$N",
                                                                       t_bar))
                                                  flush(stderr)
                                              end)
    println(stderr, "\r  ", fmt(cfg, "vortex_done"; path = res.path,
                                frames = res.frames, sec = res.sec))
    md_path, json_path = vfa_vortex_write_report(res.analysis, path)
    println(stderr, "  report: $md_path")
    println(stderr, "  json:   $json_path")
    vfa_vortex_print_summary(res.analysis)
    return
end

"§27b: неконфликтный CLI-рендер --vortex N (stdout/CI-safe, без stdin);
--vortex-quick → превью 32/8/640×440; после рендера — отчёт и сводка"
function vfa_vortex_cli(cfg::VfaConfig)
    mkpath(vfa_vortex_dir(cfg))
    N, nframes = cfg.vortex_N, cfg.vortex_frames
    width, height = 900, 640
    if cfg.vortex_quick        # U-2: быстрое превью (CI-проверка вихря)
        N, nframes, width, height = 32, 8, 640, 440
    end
    path = joinpath(vfa_vortex_dir(cfg),
                    "vortex_N$(N)_$(Libc.strftime("%Y%m%d_%H%M%S", time())).gif")
    t_bar = time()
    print(stderr, VFAUI.bar_line(0, nframes, "vortex", "  N=$N", t_bar))
    flush(stderr)
    res = VFAVortex3D.render_vortex_animation(path;
                                              N = N, nframes = nframes,
                                              T = cfg.vortex_T,
                                              h0 = cfg.layer_h0, W0 = cfg.layer_W0,
                                              width = width, height = height,
                                              callback = (k, n) -> begin
                                                  (k % 2 == 0 || k == n) || return
                                                  print(stderr,
                                                        VFAUI.bar_line(k, n,
                                                                       "vortex",
                                                                       "  N=$N",
                                                                       t_bar))
                                                  flush(stderr)
                                              end)
    println(stderr, "\r  ", fmt(cfg, "vortex_done"; path = res.path,
                                frames = res.frames, sec = res.sec))
    md_path, json_path = vfa_vortex_write_report(res.analysis, path)
    println(stderr, "  report: $md_path")
    println(stderr, "  json:   $json_path")
    vfa_vortex_print_summary(res.analysis)
    return 0
end

"§28: главное меню с группировкой, последним прогоном и быстрыми клавишами"
function vfa_menu(cfg::VfaConfig)
    eof_streak = 0
    last_task = 0
    th_cycle = ["aurora", "ice", "gold", "emerald"]   # ключи VFAUI.THEMES
    while true
        # ── шапка
        println(join(VFAUI.box_lines([
            fmt(cfg, "menu_header"),
            "preset=$(cfg.preset) · two-pass=$(cfg.two_pass ? "ON" : "OFF") · " *
            "seed=$(cfg.seed) · theme=$(cfg.theme) · lang=$(cfg.lang)",
        ]), "\n"))
        # ── последний прогон (если есть)
        last_run, last_verdicts = vfa_last_run_info(
            cfg.report_dir === nothing ? "results" : String(cfg.report_dir))
        if last_run !== nothing
            nP = count(v -> v == "PASS", values(last_verdicts))
            nF = count(v -> v in ("FAIL", "ERROR"), values(last_verdicts))
            nS = count(v -> v == "SKIP", values(last_verdicts))
            println("  ⤷ ", fmt(cfg, "last_run"), ": ", basename(last_run),
                    "  [", nP, " PASS · ", nF, " FAIL · ", nS, " SKIP]")
        end
        # ── группы задач
        core_t = [t for t in TASKS if t["id"] <= 10]
        lay_t = [t for t in TASKS if t["id"] > 10]
        println("  ", fmt(cfg, "menu_core"))
        for t in core_t
            mark = t["id"] == last_task ? " ←" : ""
            v = get(last_verdicts, t["id"], "—")
            println("    [", lpad(t["id"], 2, '0'), "] ",
                    rpad(t["slug"], 22), rpad(v, 6), mark)
        end
        if !isempty(lay_t)
            println("  ", fmt(cfg, "menu_layers"))
            for t in lay_t
                mark = t["id"] == last_task ? " ←" : ""
                v = get(last_verdicts, t["id"], "—")
                println("    [", lpad(t["id"], 2, '0'), "] ",
                        rpad(t["slug"], 22), rpad(v, 6), mark)
            end
        end
        println()
        println("  ", fmt(cfg, "menu_keys"; n = VFA_N_TASKS))
        println("  ", fmt(cfg, "menu_keys2"))
        print("  > ")
        line = ""
        eof_hit = false
        try
            line = readline(stdin)
        catch
            eof_hit = true
        end
        if eof_hit
            eof_streak += 1
        else
            eof_streak = isempty(strip(line)) ? eof_streak + 1 : 0
        end
        eof_streak >= 50 && (println("EOF guard: graceful exit"); return 0)
        raw = lowercase(strip(line))
        isempty(raw) && continue
        key = join(get(VFA_RU, c, c) for c in raw)     # §12 RU-раскладка
        try
            # J: слова «выход/выйти» сравниваются до транслитерации —
            # в VFA_RU нет однозначного маппинга слов
            if raw in ("выход", "выйти", "exit") || key in ("q", "quit", "exit")
                return 0
            elseif key == "?"
                println(VFA_HELP_KEYS[cfg.lang])
                continue
            elseif key == "a"
                cfg.tasks = copy(SUITE_IDS)
            elseif key == "r"
                last_task == 0 && (println("  (", fmt(cfg, "no_last"), ")"); continue)
                cfg.tasks = [last_task]
            elseif key == "v"
                # §27b: 3D-вихрь (интерактивный рендер GIF)
                vfa_menu_vortex(cfg)
                continue
            elseif key == "p"
                cfg.preset = vfa_choose(cfg, "preset", ("quick", "full", "deep"))
                continue
            elseif key == "2"
                cfg.two_pass = !cfg.two_pass
                continue
            elseif key == "th"
                idx = findfirst(==(cfg.theme), th_cycle)
                cfg.theme = th_cycle[(idx === nothing ? 0 : idx % length(th_cycle)) + 1]
                VFAUI.state[:theme] = cfg.theme
                continue
            elseif key == "l"
                last_run === nothing && (println("  (", fmt(cfg, "no_runs"), ")"); continue)
                println("  ── ", last_run)
                for (tid, v) in sort(collect(last_verdicts); by = first)
                    t = try vfa_find_task(tid) catch; nothing end
                    name = t === nothing ? "?" : t["slug"]
                    println("    task ", lpad(tid, 2, '0'), " ", rpad(name, 22), v)
                end
                continue
            elseif key == "c"
                vfa_print_config(cfg)
                continue
            elseif key == "t"
                return vfa_selftest(cfg)
            elseif occursin(r"^\d+$", key) && parse(Int, key) in SUITE_IDS
                cfg.tasks = [parse(Int, key)]
            else
                println("  ? неизвестная команда: ", raw)
                continue
            end
            last_task = isempty(cfg.tasks) ? 0 : cfg.tasks[end]
            code = vfa_run_all(cfg)
            if code != 0 && !isinteractive()
                return code
            end
        catch e
            isa(e, InterruptException) && (println("\n  ", fmt(cfg, "back")); continue)
            println("  ERROR: $e")
        end
    end
end

VFA_HELP = """verify_ns_full.jl — Julia-адаптер контракта §0–§27 (stdlib-only)
Режимы (§29): TUI-меню по умолчанию в TTY (и по --menu) · прямой прогон
(--ci/--task/pipe/include-в-pipe) · прежнее меню --menu-legacy · CLI.
Ключи: --menu --menu-legacy --task N|all --no-two-pass --preset quick|full|deep --seed N --size N
  --banner auto|always|never   показывать ASCII-баннер (default: auto — только в TTY)
  --quiet                      подавить баннер и болтовню (CI-friendly)
  --theme aurora|light --monitor on|off|panel --no-report --report-dir D --no-gif
  --ci --junit F --lang en|ru --plain --no-color --strict --list-tasks
  --print-config --config-file F(TOML) --self-test [--self-test-props|--self-test-contract]
  --task-timeout s --global-timeout s (кооперативно: между задачами и по heartbeat)
  --rlimit kind=v[,kind=v...] (as|cpu|fsize; best-effort)
  --layers N --layer-model default|radial --layer-h0 x --layer-W0 y
  --vortex N --vortex-frames K --vortex-T T   (§27b) GIF 3D-вихря, N ≥ 24
             (до 256, кадры ≥ 2; T — горизонт времени, по умолчанию 40);
             рендер в results/vortex/*.gif + отчёт *.md/*.json и выход
  --vortex-quick        быстрое превью (N=32, 8 кадров, 640×440); без
             --vortex N запускает превью само
             NOTE: vortex_N, заданный в --config-file/TOML или env, тоже
             запускает рендер вихря ВМЕСТО обычного прогона задач — для
             параллельного рендера и прогоняйте отдельными вызовами
  --fuzz N --sweep KEY=V1,V2,... (--sweep можно повторять; KEY — любое поле
             конфига кроме report_dir/sweep; декартово произведение свипов,
             бандлы в results/lab_*, индексы experiment.md/.toml)
  --cross-check ПУТЬ  сверка вердиктов с results.json другого монолита
             (Python↔Julia, §32; после прогона; расхождение → код 1)
  --generate-completions bash|zsh|fish --help --version
Задачи: 1–10 — контракт Python-версии; 11–15 — 3D-слоистая b-поправка (§27).
Коды выхода: 0 OK · 1 FAIL · 2 usage · 3 internal · 130 SIGINT. Замены §1.4:
  zlib→stored-PNG (WARN), docx→ERR_UNSUPPORTED, JSON-config→TOML. Подробности — шапка файла."""

function vfa_completions(shell::AbstractString)
    flags = ("--menu", "--menu-legacy", "--banner", "--quiet", "--task", "--no-two-pass", "--preset", "--seed", "--size", "--theme",
             "--monitor", "--no-report", "--report-dir", "--no-gif", "--ci", "--junit",
             "--lang", "--plain", "--no-color", "--strict", "--list-tasks",
             "--print-config", "--config-file", "--self-test", "--self-test-props",
             "--self-test-contract", "--task-timeout", "--global-timeout", "--rlimit",
             "--layers", "--layer-model", "--layer-h0", "--layer-W0", "--fuzz",
             "--vortex", "--vortex-frames", "--vortex-T", "--vortex-quick",
             "--sweep", "--cross-check", "--generate-completions",
             "--help", "--version")
    ids = join(SUITE_IDS, " ")
    shell == "bash" &&
        return "# bash completion (generated)\ncomplete -W \"$(join(flags, ' '))\" verify_ns_full.jl\n"
    shell == "fish" &&
        return join(["complete -c verify_ns_full.jl -l $(f[3:end])" for f in flags], '\n') *
               "\ncomplete -c verify_ns_full.jl -l task -a '$ids all'\n"
    shell == "zsh" &&
        return "#compdef verify_ns_full.jl\n_arguments " *
               join(["'$(f)[option]' " for f in flags]) * "\n"
    error("--generate-completions expects bash|zsh|fish")
end

# ═══════════════════════════════════════════════════════════════════════════
# §29 TUI-меню: state machine (узлы → действия → история). Модуль включается
# в Main ПОСЛЕ VFAUI/VFALog, поэтому их имена — через Main.* (как в §28);
# const NODES объявляется после определения MenuNode.
# Правило входа (§16, ред. 1.2, вариант «б»): TTY без машинных флагов →
# меню; --ci/--task/--list-tasks/--self-test и pipe → прямой прогон.
# ═══════════════════════════════════════════════════════════════════════════

# ═══════════════════════════════════════════════════════════════════════════
# §30: VFALab — свипы, декартовы произведения, experiment.toml
# ═══════════════════════════════════════════════════════════════════════════
module VFALab

import TOML

export LabSweep, LabExperiment, lab_parse_sweeps, lab_cartesian, lab_convert,
       lab_from_toml, run_experiment, lab_add!, lab_show!, lab_clear!,
       lab_toml!, lab_run!, lab_sweeps_of

"""Одно измерение эксперимента: ключ VfaConfig → значения-строки
(конвертация по типу поля — в lab_convert, fail-fast до прогонов)."""
struct LabSweep
    key::Symbol
    values::Vector{String}
end

struct LabExperiment
    name::String
    sweeps::Vector{LabSweep}
    base::Vector{Pair{Symbol, Any}}   # необязательная база (из [base] TOML)
end

const LAB_FORBIDDEN = (:report_dir, :sweep)   # изоляция бандлов / рекурсия §30

function lab_sweeps_of(s)
    return get!(s.last_values, :lab_sweeps, LabSweep[])::Vector{LabSweep}
end

function lab_check_key(cfg::Main.VfaConfig, key::Symbol)
    key in LAB_FORBIDDEN &&
        error("lab: ключ '$key' нельзя свипать (изоляция бандлов / рекурсия)")
    hasproperty(cfg, key) ||
        error("lab: поля '$key' нет в VfaConfig (см. --print-config)")
    return nothing
end

"""Многомерный парсер: 'KEY=V1,V2;KEY2=V3' (CLI склеивает повторные --sweep
через ';'). Ключ — любое поле VfaConfig, кроме запрещённых; значения — строки,
тип проверяется в lab_convert. cfg передаётся для fail-fast валидации ключей."""
function lab_parse_sweeps(s::AbstractString; cfg = nothing)
    sws = LabSweep[]
    for chunk in split(s, ';')
        chunk = strip(chunk)
        isempty(chunk) && continue
        m = match(r"^\s*([A-Za-z_][A-Za-z0-9_]*)\s*=\s*(.+?)\s*$", chunk)
        m === nothing && error("--sweep ожидает KEY=V1,V2,... (получено: '$chunk')")
        key = Symbol(lowercase(m.captures[1]))
        cfg === nothing || lab_check_key(cfg, key)
        vals = String[]
        for tok in split(m.captures[2], ',')
            isempty(strip(tok)) && continue
            push!(vals, String(strip(tok)))
        end
        isempty(vals) && error("--sweep: нет значений после '='")
        push!(sws, LabSweep(key, vals))
    end
    return LabExperiment("cli", sws, Pair{Symbol, Any}[])
end

"""Значение → тип поля cfg (Bool/Int/Float64/String/Vector{Int}/Vector{String})."""
function lab_convert(cfg::Main.VfaConfig, key::Symbol, v::Any)
    lab_check_key(cfg, key)
    cur = getproperty(cfg, key)
    if v isa AbstractString
        sval = strip(String(v))
        if cur isa Bool
            return lowercase(sval) in ("on", "true", "1", "да", "вкл")
        elseif cur isa Int
            n = tryparse(Int, sval)
            n === nothing && error("lab: '$sval' — не целое для '$key'")
            return n
        elseif cur isa Float64
            x = tryparse(Float64, sval)
            x === nothing && error("lab: '$sval' — не число для '$key'")
            return x
        elseif cur isa Vector{Int}
            return Int[parse(Int, t) for t in split(sval, (',', ' '); keepempty = false)]
        elseif cur isa Vector{String}
            return String[t for t in split(sval, (',', ' '); keepempty = false)]
        else
            return sval
        end
    end
    # уже типизировано (обычно из [base] experiment.toml)
    if cur isa Bool
        v isa Bool || error("lab: '$key' — Bool, получено $(typeof(v))")
        return v
    elseif cur isa Int
        v isa Integer || error("lab: '$key' — целое, получено $(typeof(v))")
        return Int(v)
    elseif cur isa Float64
        v isa Real || error("lab: '$key' — число, получено $(typeof(v))")
        return Float64(v)
    elseif cur isa Vector{Int}
        v isa AbstractVector || error("lab: '$key' — список целых")
        return Int[Int(x) for x in v]
    elseif cur isa Vector{String}
        v isa AbstractVector || error("lab: '$key' — список строк")
        return String[string(x) for x in v]
    else
        return string(v)
    end
end

"""Декартово произведение свипов → Vector{Vector{Pair{Symbol,Any}}}."""
function lab_cartesian(sweeps::Vector{LabSweep})
    combos = Vector{Vector{Pair{Symbol, Any}}}([Pair{Symbol, Any}[]])
    for sw in sweeps
        nxt = Vector{Vector{Pair{Symbol, Any}}}()
        for c in combos, v in sw.values
            push!(nxt, vcat(c, [Pair{Symbol, Any}(sw.key, v)]))
        end
        combos = nxt
    end
    return combos
end

lab_val_str(v::AbstractString) = String(v)
lab_val_str(v) = string(v)
lab_pair_str(p::Pair{Symbol, Any}) = string(first(p)) * "=" * lab_val_str(last(p))

"""experiment.toml (stdlib TOML): [[sweep]] key/values · [base] — база."""
function lab_from_toml(path::AbstractString)
    isfile(path) || error("lab: нет файла: $path")
    t = TOML.parsefile(path)
    sws = LabSweep[]
    for sw in get(t, "sweep", Any[])
        sw isa AbstractDict || error("lab: [[sweep]] — таблица")
        haskey(sw, "key") || error("lab: у свипа нет 'key'")
        vals = String[string(v) for v in get(sw, "values", Any[])]
        isempty(vals) && error("lab: свип '$(sw["key"])' без значений")
        push!(sws, LabSweep(Symbol(lowercase(string(sw["key"]))), vals))
    end
    base = Pair{Symbol, Any}[]
    for (k, v) in get(t, "base", Dict{String, Any}())
        push!(base, Pair{Symbol, Any}(Symbol(lowercase(k)), v))
    end
    isempty(sws) && isempty(base) && error("lab: в $path нет [[sweep]] и [base]")
    nm = get(t, "name", "experiment")
    return LabExperiment(nm isa AbstractString ? String(nm) : "experiment", sws, base)
end

"""Сборка перекрытий комбинации: base + combo (комбо сильнее), fail-fast."""
function lab_combo_overrides(cfg::Main.VfaConfig, exp::LabExperiment,
                             combo::Vector{Pair{Symbol, Any}})
    d = Dict{Symbol, Any}()
    for (k, v) in exp.base
        d[k] = lab_convert(cfg, k, v)
    end
    for (k, v) in combo
        d[k] = lab_convert(cfg, k, v)
    end
    return collect(d)
end

"""§30: эксперимент — N комбинаций × задачи; каждая комбинация — изолированный
прогон в results/lab_<ts>/combo_XX (свой report_dir). Индексы experiment.md/.toml."""
function run_experiment(cfg::Main.VfaConfig, exp::LabExperiment;
                        task_ids::Union{Nothing, Vector{Int}} = nothing,
                        quiet::Bool = false)
    isempty(exp.sweeps) && isempty(exp.base) && error("lab: матрица пуста")
    ids = task_ids === nothing ?
          (isempty(cfg.tasks) ? copy(Main.SUITE_IDS) : copy(cfg.tasks)) : copy(task_ids)
    isempty(ids) && error("lab: пустой список задач")
    overrides = [lab_combo_overrides(cfg, exp, c) for c in lab_cartesian(exp.sweeps)]
    n = length(overrides)
    root = joinpath(cfg.report_dir === nothing ? "results" : String(cfg.report_dir),
                    "lab_" * Libc.strftime("%Y%m%d_%H%M%S", time()))
    mkpath(root)
    quiet || println(stderr, "lab: «", exp.name, "» — ", n, " комбинаций × ",
                     length(ids), " задач → ", root)
    rows = Any[]
    for (i, ov) in enumerate(overrides)
        cdir = joinpath(root, "combo_" * lpad(i, 2, '0'))
        snap = deepcopy(cfg)
        code = 1
        try
            cfg.sweep = ""                      # грабли №2: без рекурсии в vfa_run_all
            cfg.tasks = ids
            cfg.report_dir = cdir
            for (k, v) in ov
                setproperty!(cfg, k, v)
            end
            code = Main.vfa_run_once(cfg)
        finally
            for f in fieldnames(Main.VfaConfig)
                setfield!(cfg, f, getfield(snap, f))
            end
        end
        nP, nF, dur = 0, 0, 0.0
        runs = sort([d for d in readdir(cdir; join = true)
                     if isdir(d) && startswith(basename(d), "jrun_")])
        if !isempty(runs)
            ri = Main.VFAMenu.parse_results(joinpath(runs[end], "results.json"))
            nP = count(v -> v == "PASS", values(ri.verdicts))
            nF = count(v -> v in ("FAIL", "ERROR"), values(ri.verdicts))
            dur = sum(values(ri.durs); init = 0.0)
        end
        ovstr = join([lab_pair_str(p) for p in ov], "  ")
        quiet || println(stderr, "lab: combo_", lpad(i, 2, '0'), "  ", ovstr,
                         "  → код $code, PASS=$nP FAIL=$nF")
        push!(rows, (n = i, ov = ovstr, code = code, dir = cdir,
                     nP = nP, nF = nF, dur = dur))
    end
    lab_write_index(root, exp, ids, rows)
    return maximum(r.code for r in rows)
end

function lab_write_index(root::AbstractString, exp::LabExperiment,
                         ids::Vector{Int}, rows::Vector{Any})
    matrix = join(["$(sw.key) ∈ {" * join(sw.values, ", ") * "}" for sw in exp.sweeps], " × ")
    open(joinpath(root, "experiment.md"), "w") do fh
        println(fh, "# VFA Lab · ", exp.name)
        println(fh, "")
        println(fh, "- матрица: ", isempty(matrix) ? "база без свипов" : matrix,
                " → ", length(rows), " комбинаций")
        println(fh, "- задачи: ", join(ids, ", "))
        println(fh, "")
        println(fh, "| # | перекрытия | PASS | FAIL | dur_s | код | каталог |")
        println(fh, "|---|---|---|---|---|---|---|")
        for r in rows
            println(fh, "| ", r.n, " | ", replace(r.ov, "|" => "\\|"), " | ",
                    r.nP, " | ", r.nF, " | ", round(r.dur; digits = 1), " | ",
                    r.code, " | `", basename(r.dir), "` |")
        end
    end
    open(joinpath(root, "experiment.toml"), "w") do fh
        println(fh, "[experiment]")
        println(fh, "name = \"", replace(exp.name, "\"" => ""), "\"")
        println(fh, "tasks = [", join(ids, ", "), "]")
        println(fh, "combos = ", length(rows))
        for r in rows
            println(fh, "")
            println(fh, "[[combo]]")
            println(fh, "n = ", r.n)
            println(fh, "dir = \"", basename(r.dir), "\"")
            println(fh, "code = ", r.code)
            println(fh, "pass = ", r.nP)
            println(fh, "fail = ", r.nF)
        end
    end
    return nothing
end

# ── действия меню §29 (узел :lab) ───────────────────────────────────────────
function lab_add!(cfg::Main.VfaConfig, s)
    print("  свип KEY=V1,V2[,V3] > ")
    line = ""
    try
        line = strip(readline(stdin))
    catch
        return
    end
    isempty(line) && (println("  (отмена)"); return)
    try
        exp = lab_parse_sweeps(line; cfg = cfg)
        append!(lab_sweeps_of(s), exp.sweeps)
        println("  + ", join(["$(sw.key) ∈ {" * join(sw.values, ",") * "}" for sw in exp.sweeps], " · "),
                "  (измерений: ", length(lab_sweeps_of(s)), ")")
    catch e
        println("  ? ", sprint(showerror, e))
    end
    return
end

function lab_show!(cfg::Main.VfaConfig, s)
    sws = lab_sweeps_of(s)
    isempty(sws) && (println("  матрица пуста — добавьте свип [s] или загрузите [t]"); return)
    try
        combos = lab_cartesian(sws)
        println("  измерений: ", length(sws), " · комбинаций: ", length(combos))
        for sw in sws
            println("   ", sw.key, " ∈ {", join(sw.values, ", "), "}")
        end
        println("  комбинации (перекрытия):")
        for (i, c) in enumerate(combos)
            i > 8 && (println("   …"); break)
            ov = try
                lab_combo_overrides(cfg, LabExperiment("show", sws, Pair{Symbol, Any}[]), c)
            catch e
                println("   ", i, ": ? ", sprint(showerror, e))
                continue
            end
            println("   ", i, ": ", join([lab_pair_str(p) for p in ov], "  "))
        end
    catch e
        println("  ? ", sprint(showerror, e))
    end
    return
end

function lab_clear!(s)
    empty!(lab_sweeps_of(s))
    delete!(s.last_values, :lab_base)
    delete!(s.last_values, :lab_name)
    println("  матрица очищена")
    return
end

function lab_toml!(cfg::Main.VfaConfig, s)
    print("  путь к experiment.toml (enter = experiment.toml) > ")
    line = ""
    try
        line = strip(readline(stdin))
    catch
        return
    end
    path = isempty(line) ? "experiment.toml" : line
    try
        exp = lab_from_toml(path)
        s.last_values[:lab_sweeps] = exp.sweeps
        s.last_values[:lab_base] = exp.base
        s.last_values[:lab_name] = exp.name
        println("  загружено: ", length(exp.sweeps), " измерений, ",
                length(exp.base), " базовых перекрытий — ", exp.name)
        lab_show!(cfg, s)
    catch e
        println("  ? ", sprint(showerror, e))
    end
    return
end

function lab_run!(cfg::Main.VfaConfig, s)
    sws = lab_sweeps_of(s)
    isempty(sws) && isempty(get(s.last_values, :lab_base, Pair{Symbol, Any}[])) &&
        (println("  матрица пуста — [s]/[t] сначала"); return)
    ids = isempty(cfg.tasks) ? copy(Main.SUITE_IDS) : copy(cfg.tasks)
    n = length(lab_cartesian(sws))
    println("  эксперимент: ", n, " комбинаций × ", length(ids), " задач = ",
            n * length(ids), " прогонов")
    print("  запускать? [y/N] > ")
    line = ""
    try
        line = lowercase(strip(readline(stdin)))
    catch
        return
    end
    line in ("y", "yes", "д", "да", "1") || (println("  (отмена)"); return)
    base = Pair{Symbol, Any}[p for p in get(s.last_values, :lab_base, Pair{Symbol, Any}[])]
    exp = LabExperiment(string(get(s.last_values, :lab_name, "menu")), sws, base)
    try
        code = run_experiment(cfg, exp)
        println("  итоговый код возврата: $code")
    catch e
        println("  ? ", sprint(showerror, e))
    end
    return
end

end # module VFALab

module VFAMenu
    export MenuState, MenuNode, MenuItem, MenuAction,
           ShowInfo, GotoMenu, InvokeTask, RunSuite, RunLab, QuitMenu,
           PopMenu, ActionFn, FormField, FormAction,
           run_menu!, build_tree!, register_node!, goto!, vfa_run_all_with, NODES

    # ── типы действий ──────────────────────────────────────────────────────
    abstract type MenuAction end
    struct ShowInfo   <: MenuAction; text::String;               end
    struct GotoMenu   <: MenuAction; id::Symbol;                 end
    struct RunSuite   <: MenuAction; ids::Vector{Int};           end
    struct InvokeTask <: MenuAction; id::Int; override::Dict{Symbol, Any}; end
    struct RunLab     <: MenuAction; spec::Symbol;               end
    struct QuitMenu   <: MenuAction;                             end
    struct PopMenu    <: MenuAction;                             end
    struct ActionFn   <: MenuAction; fn::Function; desc::String; end

    struct FormField
        name::String
        typ::DataType
        default::Any
        choices::Union{Nothing, Vector{Any}}   # ≠ nothing → селектор
        help::String
    end

    struct FormAction <: MenuAction
        title::String
        fields::Vector{FormField}
        on_submit::Function    # values::Dict{String,Any} → MenuAction
    end

    # ── узел и состояние ───────────────────────────────────────────────────
    struct MenuItem
        label::String
        key::String            # "1", "a", "th", ".."
        action::MenuAction
        help::String
    end

    struct MenuNode
        id::Symbol
        title::String
        items::Vector{MenuItem}
        header_fn::Union{Nothing, Function}    # (state) -> Vector{String}
        back_to::Union{Symbol, Nothing}
    end

    mutable struct MenuState
        nodes::Dict{Symbol, MenuNode}
        current::Symbol
        breadcrumb::Vector{Symbol}
        history::Vector{Symbol}
        last_values::Dict{Symbol, Any}         # кэш форм (этап 2)
        quit::Bool
    end

    const NODES = Dict{Symbol, MenuNode}()
    const STATE = Ref{Union{MenuState, Nothing}}(nothing)

    register_node!(n::MenuNode) = (NODES[n.id] = n; n)

    function goto!(s::MenuState, id::Symbol)
        haskey(s.nodes, id) || return false
        push!(s.history, s.current)
        s.current = id
        push!(s.breadcrumb, id)
        return true
    end

    function Base.pop!(s::MenuState)
        isempty(s.history) && return false
        s.current = pop!(s.history)
        length(s.breadcrumb) > 1 && pop!(s.breadcrumb)
        return true
    end

    function render_menu!(s::MenuState)
        node = s.nodes[s.current]
        println()
        println(join(Main.VFAUI.box_lines([
            "VFA · $(node.title)",
            "path: " * join(String.(s.breadcrumb), " › "),
        ]), "\n"))
        if node.header_fn !== nothing
            for line in node.header_fn(s)
                println("  ", line)
            end
            println()
        end
        for it in node.items
            println("  [", rpad(it.key, 3), "] ", rpad(it.label, 38), " ", it.help)
        end
        println()
        print("  > ")
    end

    function show_help(s::MenuState)
        println("  Глобальные клавиши: [q] выход · [..|b] назад · [?] эта справка")
        for it in s.nodes[s.current].items
            isempty(it.help) || println("    [", it.key, "] ", it.label, " — ", it.help)
        end
    end

    function collect_form(a::FormAction)
        values = Dict{String, Any}()
        for f in a.fields
            print("  ", f.name, " [", f.default, "] > ")
            line = strip(readline(stdin))
            if isempty(line)
                values[f.name] = f.default
            elseif f.choices !== nothing
                values[f.name] = line in string.(f.choices) ? line :
                                 (println("  ? из ", f.choices); f.default)
            else
                values[f.name] = try parse(f.typ, line) catch; f.default end
            end
        end
        return values
    end

    # ── §29.2 настройки: data-driven по реальным полям VfaConfig ───────────
    struct SettingSpec
        key::String             # хоткей (регистр значим: O/M/W)
        label::String
        field::Symbol
        kind::Symbol            # :cycle | :int | :float | :list | :theme
        choices::Vector{String}
        help::String
    end

    function settings_specs()
        return SettingSpec[
            SettingSpec("p", "preset",         :preset,         :cycle, ["quick", "full", "deep"], ""),
            SettingSpec("s", "seed",           :seed,           :int,   String[], ""),
            SettingSpec("z", "size",           :size,           :int,   String[], ""),
            SettingSpec("t", "theme",          :theme,          :theme, ["aurora", "ice", "gold", "emerald"], "сразу в VFAUI"),
            SettingSpec("2", "two-pass",       :two_pass,       :cycle, ["false", "true"], ""),
            SettingSpec("m", "monitor",        :monitor,        :cycle, ["on", "off", "panel"], ""),
            SettingSpec("f", "report-formats", :report_formats, :list,  ["md", "html", "pdf"], "через пробел/запятую"),
            SettingSpec("g", "no-gif",         :no_gif,         :cycle, ["false", "true"], ""),
            SettingSpec("o", "task-timeout",   :task_timeout,   :float, String[], "сек"),
            SettingSpec("O", "global-timeout", :global_timeout, :float, String[], "0 = без лимита"),
            SettingSpec("l", "layers",         :layers,         :int,   String[], "§27"),
            SettingSpec("M", "layer-model",    :layer_model,    :cycle, ["default", "radial"], "§27"),
            SettingSpec("h", "layer-h0",       :layer_h0,       :float, String[], "§27"),
            SettingSpec("W", "layer-W0",       :layer_W0,       :float, String[], "§27"),
        ]
    end

    setting_show(cfg::Main.VfaConfig, sp::SettingSpec) = begin
        v = getproperty(cfg, sp.field)
        v isa Bool ? (v ? "ON" : "OFF") :
        v isa AbstractVector ? join(v, ",") : string(v)
    end

    function set_setting!(cfg::Main.VfaConfig, sp::SettingSpec, sval::AbstractString)
        cur = getproperty(cfg, sp.field)
        ok = true
        if cur isa Bool
            setproperty!(cfg, sp.field, lowercase(sval) in ("on", "true", "1", "да", "вкл"))
        elseif cur isa Int
            n = tryparse(Int, sval)
            if n === nothing
                ok = false
            else
                setproperty!(cfg, sp.field, n)
            end
        elseif cur isa Float64
            x = tryparse(Float64, sval)
            if x === nothing
                ok = false
            else
                setproperty!(cfg, sp.field, x)
            end
        elseif cur isa AbstractVector
            vals = [c for c in sp.choices
                    if c in split(lowercase(sval), (',', ' '); keepempty = false)]
            if isempty(vals)
                ok = false
            else
                setproperty!(cfg, sp.field, vals)
            end
        else
            setproperty!(cfg, sp.field, String(sval))
        end
        if ok && sp.kind === :theme
            Main.VFAUI.state[:theme] = cfg.theme   # мгновенный эффект, как в баннере §28
        end
        return ok
    end

    function setting_cycle!(cfg::Main.VfaConfig, sp::SettingSpec)
        v = getproperty(cfg, sp.field)
        cur = v isa Bool ? (v ? "true" : "false") : lowercase(string(v))
        i = findfirst(==(cur), lowercase.(sp.choices))
        nxt = sp.choices[i === nothing ? 1 : mod1(i + 1, length(sp.choices))]
        ok = set_setting!(cfg, sp, nxt)
        println("  ", sp.label, " = ", setting_show(cfg, sp), ok ? "" : "  ? не применилось")
    end

    function setting_prompt!(cfg::Main.VfaConfig, sp::SettingSpec)
        print("  ", sp.label, " = ", setting_show(cfg, sp),
              isempty(sp.choices) ? "" : "  (из: " * join(sp.choices, "/") * ")", "  > ")
        line = ""
        try
            line = strip(readline(stdin))
        catch
            return
        end
        isempty(line) && (println("  (без изменений)"); return)
        ok = set_setting!(cfg, sp, line)
        println(ok ? "  = " * setting_show(cfg, sp) : "  ? не разобрал: " * line)
    end

    function settings_header(cfg::Main.VfaConfig)
        lines = String[]
        for chunk in Iterators.partition(settings_specs(), 5)
            push!(lines, join(["$(sp.key):$(sp.label)=$(setting_show(cfg, sp))" for sp in chunk], " · "))
        end
        return lines
    end

    # ── §29.3 результаты: чтение results/ (jrun_* и python run_*) ──────────
    vfa_results_root(cfg::Main.VfaConfig) =
        cfg.report_dir === nothing ? "results" : String(cfg.report_dir)

    function list_runs(cfg::Main.VfaConfig)
        root = vfa_results_root(cfg)
        isdir(root) || return String[]
        runs = [d for d in readdir(root; join = true)
                if isdir(d) && (startswith(basename(d), "jrun_") ||
                                startswith(basename(d), "run_")) &&
                       isfile(joinpath(d, "results.json"))]
        return sort!(runs; by = x -> stat(x).mtime)
    end

    struct RunInfo
        path::String
        verdicts::Dict{Int, String}
        slugs::Dict{Int, String}
        reasons::Dict{Int, String}
        durs::Dict{Int, Float64}
    end

    function parse_results(path::AbstractString)
        vd = Dict{Int, String}(); sl = Dict{Int, String}()
        rs = Dict{Int, String}(); du = Dict{Int, Float64}()
        txt = read(path, String)
        # формат записи — ровно как пишет VFALog.finish! (§7)
        for m in eachmatch(r"\"(\d+)\":[{]\"slug\":\"([^\"]*)\",\"verdict\":\"([A-Z]+)\",\"reason\":\"([^\"]*)\",\"duration_s\":([0-9.eE+-]+)", txt)
            tid = parse(Int, m.captures[1])
            sl[tid] = m.captures[2]; vd[tid] = m.captures[3]
            rs[tid] = m.captures[4]
            x = tryparse(Float64, m.captures[5]); du[tid] = x === nothing ? 0.0 : x
        end
        isempty(vd) && for m in eachmatch(r"\"(\d+)\"\s*:\s*[{][^}]*\"verdict\"\s*:\s*\"([A-Z]+)\"", txt)
            vd[parse(Int, m.captures[1])] = m.captures[2]
        end
        return RunInfo(String(path), vd, sl, rs, du)
    end

    function run_counts(ri::RunInfo)
        nP = count(v -> v == "PASS", values(ri.verdicts))
        nF = count(v -> v in ("FAIL", "ERROR"), values(ri.verdicts))
        nS = count(v -> v == "SKIP", values(ri.verdicts))
        return (nP, nF, nS, sum(values(ri.durs); init = 0.0))
    end

    function pick_run(runs::Vector{String}, prompt::String)
        print("  ", prompt, " (enter = последний) > ")
        line = ""
        try
            line = strip(readline(stdin))
        catch
            return runs[end]
        end
        isempty(line) && return runs[end]
        for tok in split(line, (' ', ','); keepempty = false)
            hit = findall(x -> occursin(tok, basename(x)), runs)
            if length(hit) == 1
                return runs[only(hit)]
            end
            println("  ? не однозначно: ", tok)
        end
        return runs[end]
    end

    function res_last!(_cfg::Main.VfaConfig, _s::MenuState)
        runs = list_runs(_cfg)
        isempty(runs) && (println("  (прогонов ещё не было)"); return)
        run = runs[end]
        ri = parse_results(joinpath(run, "results.json"))
        nP, nF, nS, dur = run_counts(ri)
        println("  ", Main.fmt(_cfg, "run_dir"; d = basename(run)),
                "  [$nP PASS · $nF FAIL · $nS SKIP · ", round(dur; digits = 1), " s]")
        for tid in sort(collect(keys(ri.verdicts)))
            println("   ", rpad(string(tid), 4), rpad(get(ri.slugs, tid, "?"), 24),
                    rpad(get(ri.verdicts, tid, "?"), 7), get(ri.reasons, tid, ""))
        end
        return
    end

    function res_history!(_cfg::Main.VfaConfig, _s::MenuState)
        runs = list_runs(_cfg)
        isempty(runs) && (println("  (прогонов ещё не было)"); return)
        rows = Tuple{String, Int, Int, Int, Float64}[]
        for r in runs
            nP, nF, nS, dur = run_counts(parse_results(joinpath(r, "results.json")))
            push!(rows, (r, nP, nF, nS, dur))
        end
        print("  сортировка: [n] время · [p] PASS↓ · [f] FAIL↓ (enter = n) > ")
        line = ""
        try
            line = lowercase(strip(readline(stdin)))
        catch
        end
        if startswith(line, "p")
            sort!(rows; by = x -> -x[2])
        elseif startswith(line, "f")
            sort!(rows; by = x -> -x[3])
        else
            sort!(rows; by = x -> stat(x[1]).mtime)
        end
        println("  ", rpad("прогон", 26), rpad("PASS", 6), rpad("FAIL", 6), rpad("SKIP", 6), "dur_s")
        for r in rows
            println("  ", rpad(basename(r[1]), 26), rpad(r[2], 6), rpad(r[3], 6),
                    rpad(r[4], 6), round(r[5]; digits = 1))
        end
        return
    end

    function res_diff!(_cfg::Main.VfaConfig, _s::MenuState)
        runs = list_runs(_cfg)
        length(runs) < 2 && (println("  нужно ≥2 прогона"); return)
        a, b = runs[end-1], runs[end]
        print("  два прогона через пробел (enter = два последних) > ")
        line = ""
        try
            line = strip(readline(stdin))
        catch
        end
        if !isempty(line)
            picked = String[]
            for tok in split(line, (' ', ','); keepempty = false)
                hit = findall(x -> occursin(tok, basename(x)), runs)
                if length(hit) == 1
                    push!(picked, runs[only(hit)])
                else
                    println("  ? не однозначно: ", tok)
                end
            end
            if length(picked) == 2
                a, b = picked[1], picked[2]
            else
                println("  (нужно ровно 2 — беру два последних)")
            end
        end
        ra = parse_results(joinpath(a, "results.json"))
        rb = parse_results(joinpath(b, "results.json"))
        println("  A = ", basename(a), "  ·  B = ", basename(b))
        ndiff = 0
        for tid in sort(collect(union(keys(ra.verdicts), keys(rb.verdicts))))
            va = get(ra.verdicts, tid, "—")
            vb = get(rb.verdicts, tid, "—")
            va == vb && continue
            ndiff += 1
            println("   ", rpad(string(tid), 4), rpad(get(ra.slugs, tid, "?"), 24), va, " → ", vb)
        end
        same = count(t -> get(ra.verdicts, t, "?") == get(rb.verdicts, t, "?"),
                     Set(keys(ra.verdicts)) ∩ Set(keys(rb.verdicts)))
        ndiff == 0 ? println("  вердикты идентичны (совпало $same задач)") :
                     println("  различий: $ndiff · совпало: $same")
        return
    end

    function res_open!(_cfg::Main.VfaConfig, _s::MenuState)
        runs = list_runs(_cfg)
        isempty(runs) && (println("  (прогонов ещё не было)"); return)
        run = pick_run(runs, "прогон")
        fr = joinpath(run, "FINAL_REPORT")
        files = isdir(fr) ? sort([f for f in readdir(fr) if startswith(f, "final_report.")]) : String[]
        isempty(files) && (println("  (в прогоне нет FINAL_REPORT/final_report.*)"); return)
        println("  доступны: ", join(files, ", "))
        print("  формат (enter = md) > ")
        line = ""
        try
            line = lowercase(strip(readline(stdin)))
        catch
        end
        fmtname = isempty(line) ? "md" : line
        path = joinpath(fr, "final_report." * fmtname)
        isfile(path) || (println("  ? нет файла: ", path); return)
        fmtname == "md" || (println("  бинарный/разметочный файл — путь: ", path); return)
        println("  ── ", path, " ──")
        lines = readlines(path)
        for (i, l) in enumerate(lines)
            if i > 240
                println("  … (обрезано, всего ", length(lines), " строк)")
                break
            end
            println(l)
        end
        return
    end

    function res_manifest!(_cfg::Main.VfaConfig, _s::MenuState)
        runs = list_runs(_cfg)
        isempty(runs) && (println("  (прогонов ещё не было)"); return)
        run = pick_run(runs, "прогон")
        println("  ", Main.fmt(_cfg, "run_dir"; d = run))
        for f in sort(readdir(run; join = true))
            if isdir(f)
                println("   ", rpad(basename(f) * "/", 30), "dir")
            else
                sz = stat(f).size
                println("   ", rpad(basename(f), 30),
                        sz < 1024 ? "$sz B" : "$(round(sz / 1024; digits = 1)) KiB")
            end
        end
        mf = joinpath(run, "MANIFEST.toml")
        if isfile(mf)
            println("  ── MANIFEST.toml ──")
            for l in eachline(mf)
                println("  ", l)
            end
        end
        return
    end

    # ── §29.4 диагностика ──────────────────────────────────────────────────
    function diag_selftest!(cfg::Main.VfaConfig; props::Bool = false, contract::Bool = false)
        snap = deepcopy(cfg)
        cfg.selftest = true
        cfg.selftest_props = props
        cfg.selftest_contract = contract
        try
            code = Main.vfa_selftest(cfg)
            println("  (код возврата: $code)")
        finally
            for f in fieldnames(Main.VfaConfig)
                setfield!(cfg, f, getfield(snap, f))
            end
        end
        return
    end

    function diag_sysinfo!(_cfg::Main.VfaConfig, _s::MenuState)
        println("  julia ", VERSION, " · threads=", Threads.nthreads(),
                " · cpu=", Sys.CPU_THREADS,
                " · ram_total=", round(Sys.total_memory() / 2^30; digits = 1), " GiB")
        println("  platform: ", Main.VFAMon.platform_tag())
        for l in Main.VFAMon.panel()
            println("  ", l)
        end
        return
    end

    """Прогон набора задач с перекрытием полей конфига; cfg восстанавливается
    из снапшота в finally (грабли №2: sweep не протекает в следующий прогон)."""
    function vfa_run_all_with(cfg::Main.VfaConfig, ids::Vector{Int},
                              override::Dict{Symbol, Any} = Dict{Symbol, Any}())
        snap = deepcopy(cfg)
        cfg.tasks = ids
        for (k, v) in override
            hasproperty(cfg, k) && setproperty!(cfg, k, v)
        end
        try
            return Main.vfa_run_all(cfg)
        finally
            for f in fieldnames(Main.VfaConfig)
                setfield!(cfg, f, getfield(snap, f))
            end
        end
    end

    function handle_action!(s::MenuState, a::MenuAction, cfg::Main.VfaConfig)
        if a isa QuitMenu
            s.quit = true
        elseif a isa PopMenu
            pop!(s)
        elseif a isa GotoMenu
            goto!(s, a.id) || println("  ? узел недоступен: ", a.id)
        elseif a isa ShowInfo
            println(a.text)
        elseif a isa RunSuite
            vfa_run_all_with(cfg, copy(a.ids))
        elseif a isa InvokeTask
            vfa_run_all_with(cfg, [a.id], a.override)
        elseif a isa RunLab
            if a.spec === :add
                Main.VFALab.lab_add!(cfg, s)
            elseif a.spec === :show
                Main.VFALab.lab_show!(cfg, s)
            elseif a.spec === :clear
                Main.VFALab.lab_clear!(s)
            elseif a.spec === :toml
                Main.VFALab.lab_toml!(cfg, s)
            elseif a.spec === :run
                Main.VFALab.lab_run!(cfg, s)
            else
                println("  ? неизвестный режим лаборатории: ", a.spec)
            end
        elseif a isa ActionFn
            a.fn(cfg, s)
        elseif a isa FormAction
            handle_action!(s, a.on_submit(collect_form(a)), cfg)
        end
        return nothing
    end

    "Минимальное дерево этапа 1: только :root (run / задачи / справка / выход)."
    function build_tree!(cfg::Main.VfaConfig)
        empty!(NODES)

        state_header = function (s::MenuState)
            lines = String[]
            push!(lines, "preset=$(cfg.preset) · two-pass=$(cfg.two_pass ? "ON" : "OFF") · " *
                         "seed=$(cfg.seed) · theme=$(cfg.theme) · lang=$(cfg.lang)")
            last_run, last_v = Main.vfa_last_run_info(
                cfg.report_dir === nothing ? "results" : String(cfg.report_dir))
            if last_run !== nothing
                nP = count(v -> v == "PASS", values(last_v))
                nF = count(v -> v in ("FAIL", "ERROR"), values(last_v))
                nS = count(v -> v == "SKIP", values(last_v))
                push!(lines, "последний прогон: $(basename(last_run))  " *
                             "[$nP PASS · $nF FAIL · $nS SKIP]")
            end
            return lines
        end

        select_tasks = function (c::Main.VfaConfig, s::MenuState)
            print("  номера задач (пробел/запятая; all — все) > ")
            line = ""
            try
                line = strip(readline(stdin))
            catch
                return nothing
            end
            ids = Int[]
            ok = true
            for tok in split(lowercase(line), (',', ' ', '\t'); keepempty = false)
                if tok == "all"
                    append!(ids, Main.SUITE_IDS)
                    continue
                end
                tid = tryparse(Int, tok)
                if tid === nothing || !(tid in Main.SUITE_IDS)
                    println("  ? не задача: ", tok)
                    ok = false
                    continue
                end
                push!(ids, tid)
            end
            if !(ok && !isempty(ids))
                println("  (ничего не выбрано)")
                return nothing
            end
            c.tasks = ids                     # §30: выбор остаётся в сессии — lab [r], настройки
            vfa_run_all_with(c, ids)
            return nothing
        end

        bench_one = function (c::Main.VfaConfig, s::MenuState)
            print("  номер бенчмарка (16..22) > ")
            line = ""
            try
                line = strip(readline(stdin))
            catch
                return nothing
            end
            tid = tryparse(Int, line)
            if tid === nothing || !(tid in Main.BENCH_IDS)
                println("  ? не бенчмарк: ", line)
                return nothing
            end
            vfa_run_all_with(c, [tid])
            return nothing
        end

        res_xcheck! = function (c::Main.VfaConfig, s::MenuState)
            print("  путь к results.json / каталогу прогона > ")
            line = ""
            try
                line = strip(readline(stdin))
            catch
                return nothing
            end
            isempty(line) && (println("  (отмена)"); return nothing)
            vfa_cross_check(c, line)
            return nothing
        end

        spec_items = MenuItem[
            MenuItem(sp.label, sp.key,
                     sp.kind === :cycle || sp.kind === :theme ?
                     ActionFn((c, s) -> setting_cycle!(c, sp), "цикл") :
                     ActionFn((c, s) -> setting_prompt!(c, sp), "ввод"),
                     isempty(sp.choices) ? sp.help : join(sp.choices, "/"))
            for sp in settings_specs()]

        register_node!(MenuNode(:root, "Главное меню", [
            MenuItem("Быстрый прогон (все задачи)", "1",
                     RunSuite(copy(Main.SUITE_IDS)),
                     "preset=$(cfg.preset), two-pass=$(cfg.two_pass)"),
            MenuItem("Выбрать задачи", "2",
                     ActionFn(select_tasks, "выбор номеров"),
                     "например: 3 7 11"),
            MenuItem("Лаборатория", "3", GotoMenu(:lab), "свипы и эксперименты"),
            MenuItem("Бенчмарки точных решений", "4", GotoMenu(:bench), "задачи 16–22"),
            MenuItem("3D-вихрь (затухание)", "v",
                     ActionFn((c, s) -> Main.vfa_menu_vortex(c, s), "рендер GIF"),
                     "N ≥ 24, до 256"),
            MenuItem("Результаты и отчёты", "5", GotoMenu(:results), ""),
            MenuItem("Настройки", "6", GotoMenu(:settings), ""),
            MenuItem("Самотест / диагностика", "7", GotoMenu(:diag), ""),
            MenuItem("Справка (ключи CLI)", "?", ShowInfo(Main.VFA_HELP), ""),
            MenuItem("Выход", "q", QuitMenu(), ""),
        ], state_header, nothing))

        register_node!(MenuNode(:settings, "Настройки",
                                vcat(spec_items, [MenuItem("назад", "..", PopMenu(), "")]),
                                s -> settings_header(cfg), :root))

        register_node!(MenuNode(:lab, "Лаборатория (свипы и эксперименты)", [
            MenuItem("Добавить свип", "s", RunLab(:add), "KEY=V1,V2;... — любое поле конфига"),
            MenuItem("Показать матрицу", "v", RunLab(:show), "измерения и комбинации"),
            MenuItem("Очистить матрицу", "x", RunLab(:clear), ""),
            MenuItem("Загрузить experiment.toml", "t", RunLab(:toml), "enter = experiment.toml"),
            MenuItem("Запустить эксперимент", "r", RunLab(:run), "N комбинаций × задачи"),
            MenuItem("назад", "..", PopMenu(), ""),
        ], nothing, :root))

        register_node!(MenuNode(:bench, "Бенчмарки точных решений (16–22)", [
            MenuItem("Все бенчмарки 16–22", "1", RunSuite(copy(Main.BENCH_IDS)), "сводный прогон"),
            MenuItem("Отдельный бенчмарк", "2", ActionFn(bench_one, "номер 16..22"), ""),
            MenuItem("Что это", "v",
                     ShowInfo("  Бенчмарки точных решений §31 (16–22):\n" *
                              "   16 Тейлор-Грин   — невязка дискретных НС на точном поле, порядок 2\n" *
                              "   17 Ковазнай      — стационарные НС, Re=30, λ=Re/2−√(Re²/4+4π²)\n" *
                              "   18 Стокс II      — осциллирующая стенка, FTCS против e^{-ky}sin(ωt−ky)\n" *
                              "   19 Лере-Хопф     — энергия π²e^{-4νt}, монотонность, баланс с энстрофией\n" *
                              "   20 ABC           — rot u = u (Бельтрами), тождество Ламба\n" *
                              "   21 Бюргерс       — стационарная волна −tanh(cx/2ν), прогон до установления\n" *
                              "   22 Ричардсон     — log₂(res(N)/res(2N)) ≈ 2 для ТГ и ABC"), ""),
            MenuItem("назад", "..", PopMenu(), ""),
        ], nothing, :root))

        register_node!(MenuNode(:results, "Результаты и отчёты", [
            MenuItem("Последний прогон (сводка)", "l", ActionFn(res_last!, "вердикты"), ""),
            MenuItem("История прогонов", "h", ActionFn(res_history!, "n/p/f — сортировка"), ""),
            MenuItem("Diff двух прогонов", "d", ActionFn(res_diff!, "A → B"), "enter = два последних"),
            MenuItem("Открыть отчёт", "o", ActionFn(res_open!, "final_report.md"), "html/pdf — путь"),
            MenuItem("Манифест прогона", "m", ActionFn(res_manifest!, "MANIFEST.toml + файлы"), ""),
            MenuItem("Сверка с Python-прогоном", "c", ActionFn(res_xcheck!, "путь"),
                     "results.json другого монолита (§32)"),
            MenuItem("назад", "..", PopMenu(), ""),
        ], nothing, :root))

        register_node!(MenuNode(:diag, "Самотест / диагностика", [
            MenuItem("self-test (проверки §14)", "t",
                     ActionFn((c, s) -> diag_selftest!(c), "vfa_selftest"), ""),
            MenuItem("self-test +props", "tp",
                     ActionFn((c, s) -> diag_selftest!(c; props = true), "свойства"), ""),
            MenuItem("self-test +contract", "tc",
                     ActionFn((c, s) -> diag_selftest!(c; contract = true), "контракт"), ""),
            MenuItem("Системная информация", "i", ActionFn(diag_sysinfo!, "VFAMon + /proc"), ""),
            MenuItem("Печать конфига", "c",
                     ActionFn((c, s) -> Main.vfa_print_config(c), "VfaConfig"), ""),
            MenuItem("назад", "..", PopMenu(), ""),
        ], nothing, :root))
        return NODES
    end

    function run_menu!(cfg::Main.VfaConfig)
        build_tree!(cfg)
        s = MenuState(NODES, :root, Symbol[:root], Symbol[], Dict{Symbol, Any}(), false)
        STATE[] = s
        eof_streak = 0
        while !s.quit
            render_menu!(s)
            raw = ""
            hit_eof = false
            try
                raw = readline(stdin)
            catch e
                if e isa InterruptException
                    println("\n  (Ctrl+C — остаёмся в меню)")
                    continue
                end
                hit_eof = true
            end
            if hit_eof
                eof_streak += 1
            else
                eof_streak = isempty(strip(raw)) ? eof_streak + 1 : 0
            end
            if eof_streak >= 50
                println("EOF guard: graceful exit")
                break
            end
            line = strip(raw)
            isempty(line) && continue
            low = lowercase(line)
            if low in ("q", "quit", "exit", "выход", "выйти")
                break
            elseif low in ("..", "b", "back", "назад")
                pop!(s) || println("  (вы в корне)")
                continue
            elseif low == "?"
                show_help(s)
                continue
            end
            # хоткеи узла чувствительны к регистру (O/M/W в §29.2);
            # RU-раскладка §12 применяется к вводу пунктов
            key = join(get(Main.VFA_RU, ch, ch) for ch in line)
            node = s.nodes[s.current]
            idx = findfirst(it -> it.key == key, node.items)
            if idx === nothing
                println("  ? неизвестно: ", line)
                continue
            end
            try
                handle_action!(s, node.items[idx].action, cfg)
            catch e
                if e isa InterruptException
                    println("\n  ", Main.fmt(cfg, "back"))
                    continue
                end
                println("  ERROR: ", e)
                try
                    Main.VFALog.log_comp("menu: " * sprint(showerror, e), "error")
                catch
                end
            end
        end
        STATE[] = nothing
        return 0
    end
end

function vfa_main(argv::Vector{String} = ARGS)
    VFAUI.detect!()
    cfg = VfaConfig()
    for i in 1:length(argv) - 1
        argv[i] == "--config-file" && (cfg.config_file = argv[i + 1])
    end
    try
        # F: TOML может перенаправить на другой config_file — читаем цепочку
        # (максимум 5, защита от циклов), а не один файл
        seen = String[]
        while cfg.config_file !== nothing && !(String(cfg.config_file) in seen) &&
              length(seen) < 5
            push!(seen, String(cfg.config_file))
            vfa_load_config_file!(cfg, String(cfg.config_file))
        end
        vfa_parse_env!(cfg)
        vfa_parse_args!(cfg, argv)
        VFALab.lab_parse_sweeps(cfg.sweep; cfg = cfg)  # fail-fast: кривой --sweep → usage error
    catch e
        println(stderr, "usage error: $e")
        return 2
    end
    cfg.no_color && (VFAUI.state[:color] = false)
    VFAUI.set_unicode!(cfg.unicode_mode)
    cfg.plain && (VFAUI.state[:color] = false; VFAUI.state[:unicode] = false)
    VFALog.G.ci = cfg.ci
    # §28: баннер первым — до help/version/list-tasks/print-config.
    # Технические команды (help/version/completions/list-tasks/print-config)
    # баннер не печатают: это машиночитаемые выходы. Самотест — тоже.
    cfg.selftest && (cfg.banner = "never")
    _is_meta = cfg.help || cfg.version || !isempty(cfg.completions) ||
               cfg.list_tasks || cfg.print_config
    if !_is_meta && !cfg.quiet && !cfg.ci && !cfg.plain
        _show = cfg.banner == "always" ||
                (cfg.banner == "auto" && vfa_detect_tty())
        if _show
            VFABanner.show_banner!(plain = cfg.plain,
                                   color = VFAUI.state[:color],
                                   subtitle = "preset=$(cfg.preset) · " *
                                              "two-pass=$(cfg.two_pass ? "ON" : "OFF") · " *
                                              "tasks=$(isempty(cfg.tasks) ? "all" : join(cfg.tasks, ","))")
            # §9: баннер в computation_log (воспроизводимость)
            try
                VFALog.log_comp("banner printed (banner=" * cfg.banner * ")")
            catch
            end
        end
    end
    if !isempty(cfg.rlimit)
        for spec in split(cfg.rlimit, ',')
            isempty(strip(spec)) && continue
            try
                k, v = split(spec, '='; limit = 2)
                println(stderr, "rlimit: ", vfa_set_rlimit(strip(k), parse(Int, strip(v))))
            catch e
                println(stderr, "rlimit: ERR некорректно '$spec' ($e)")
            end
        end
    end
    cfg.help && (println(VFA_HELP); return 0)
    cfg.version &&
        (println("vfa 1.3.0-jl (julia $VERSION, $(VFAMon.platform_tag()))"); return 0)
    !isempty(cfg.completions) && (print(vfa_completions(cfg.completions)); return 0)
    if cfg.list_tasks
        for t in vcat(TASKS, VFA_BENCH)
            println("$(t["id"])\t$(t["slug"])\t$(t["title"])\t$(t["pass2"] === nothing ? "no" : "yes")")
        end
        # U-4: --vortex — не задача, но пусть виден в списке возможностей
        println("-\t(vortex)\t3D vortex render (--vortex N, §27b)\tno")
        return 0
    end
    cfg.print_config && (vfa_print_config(cfg); return 0)
    if cfg.selftest
        return vfa_selftest(cfg)
    end
    if cfg.vortex_N > 0 || cfg.vortex_quick
        # §27b: неконфликтный рендер вихря (--vortex N / --vortex-quick,
        # в т.ч. из TOML) — рендерим и выходим; NOTE в --help про приоритет
        try
            cfg.vortex_quick && cfg.vortex_N == 0 && (cfg.vortex_N = 32)
            return vfa_vortex_cli(cfg)
        catch e
            println(stderr, "vortex: ERROR $e")
            return 3
        end
    end
    try
        # §29 (§16, ред. 1.2, вариант «б»): TUI-меню по умолчанию только для
        # интерактивного TTY без машинных флагов; --ci/--task/--list-tasks/
        # --self-test и pipe/CI → прямой прогон (обратная совместимость).
        cfg.menu && return VFAMenu.run_menu!(cfg)      # --menu: новое меню
        cfg.menu_legacy && return vfa_menu(cfg)        # --menu-legacy: прежнее
        if cfg.ci || !isempty(cfg.tasks) || cfg.list_tasks || cfg.selftest ||
           !vfa_detect_tty()
            code = vfa_run_all(cfg)
            # §32: сверка с results.json другого монолита — после прогона
            if !isempty(strip(cfg.cross_check))
                vfa_cross_check(cfg, cfg.cross_check) || (code = max(code, 1))
            end
            return code
        end
        return VFAMenu.run_menu!(cfg)                  # TTY без флагов → меню
    catch e
        isa(e, InterruptException) && return 130
        println(stderr, "INTERNAL ERROR: $e")
        return 3
    end
end

# §16/§29: TTY без машинных флагов → TUI-меню; --ci/--task/pipe → прогон.
# include в TTY тоже открывает меню; тихая загрузка — определите ДО include:
#   VFA_AUTORUN = Ref(false)
isdefined(@__MODULE__, :VFA_AUTORUN) || (VFA_AUTORUN = Ref{Bool}(true))

if abspath(PROGRAM_FILE) == @__FILE__
    exit(vfa_main())
elseif VFA_AUTORUN[]
    println(stderr, "[vfa] include: TTY → TUI-меню §29, иначе полный прогон " *
            "(VFA_AUTORUN[] = false перед include — тихая загрузка)")
    vfa_main(String[])
end

