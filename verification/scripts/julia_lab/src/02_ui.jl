# 02_ui.jl — ANSI-оформление: цвета, баннеры, меню, пейджер (скроллинг),
# прогресс-бары, спарклайны, терминальные картинки полей.

# --------------------------------------------------------------- стили
const NSB_ANSI_RESET = "\e[0m"
const NSB_ANSI_B = "\e[1m"      # bold
const NSB_ANSI_DIM = "\e[2m"
const NSB_ANSI_ITAL = "\e[3m"

_nsb_c(code::String, s::AbstractString) = NSB_COLOR[] ? code * s * NSB_ANSI_RESET : String(s)
nsb_bold(s) = _nsb_c(NSB_ANSI_B, s)
nsb_dim(s) = _nsb_c(NSB_ANSI_DIM, s)
nsb_ital(s) = _nsb_c(NSB_ANSI_ITAL, s)

"24-битный цвет, деградирует до 256/16 при необходимости."
function nsb_rgb(r::Int, g::Int, b::Int, s::AbstractString)
    if !NSB_COLOR[]
        return String(s)
    elseif NSB_TRUECOLOR[]
        return "\e[38;2;$(r);$(g);$(b)m" * s * NSB_ANSI_RESET
    else
        # деградация: ближайший из 6x6x6 куба
        q = (x) -> (x > 127 ? 5 : round(Int, x / 43))
        c = 16 + 36 * q(r) + 6 * q(g) + q(b)
        return "\e[38;5;$(c)m" * s * NSB_ANSI_RESET
    end
end

const NSB_C_TITLE = (64, 190, 255)   # ледяной голубой
const NSB_C_ACCENT = (0, 229, 255)
const NSB_C_OK = (80, 250, 123)
const NSB_C_BAD = (255, 85, 85)
const NSB_C_WARN = (255, 184, 108)
const NSB_C_MUT = (98, 114, 164)
const NSB_C_GOLD = (241, 191, 80)

nsb_ok(s) = nsb_rgb(NSB_C_OK..., "✓ " * s)
nsb_bad(s) = nsb_rgb(NSB_C_BAD..., "✗ " * s)
nsb_warn(s) = nsb_rgb(NSB_C_WARN..., "⚠ " * s)
nsb_muted(s) = nsb_rgb(NSB_C_MUT..., s)

# --------------------------------------------------------------- баннер
const NSB_ART = [
    raw"  _   _  ___    _  _____  _____ ____      _    ____  _  _______ _____ ",
    raw" | \ | |/ _ \  / \|_   _|/ ____|  _ \    / \  |  _ \| |/ / ____|_   _|",
    raw" |  \| | | | | / _ \ | | | (___ | |_) |  / _ \ | |_) | ' /|  _|   | |  ",
    raw" | |\  | |_| |/ ___ \| |  \___ \|  _ <  / ___ \|  _ <| . \| |___  | |  ",
    raw" |_| \_|\___/_/   \_\_|  ____) |_| \_\/_/  \_\_| \_\_|\_\_____| |_|  ",
]

function nsb_banner()
    nsb_println()
    for (i, ln) in enumerate(NSB_ART)
        t = 1.0 - i / (length(NSB_ART) + 1)
        r = round(Int, NSB_C_TITLE[1] + t * 40)
        g = round(Int, NSB_C_TITLE[2] + t * 30)
        b = round(Int, NSB_C_TITLE[3] + t * 120)
        nsb_println(nsb_rgb(r, g, b, ln))
    end
    nsb_println(nsb_rgb(NSB_C_ACCENT..., NSB_ANSI_B * "  ▸ " * L("title") * NSB_ANSI_RESET))
    nsb_println(nsb_muted("    v" * NSB_LAB_VERSION * " · " * L("subtitle")))
    m = nsb_machine()
    nsb_println(nsb_muted(Lf("config_line", NSB_CFG[].out_dir, NSB_CFG[].dpi,
        NSB_CFG[].seed, NSB_CFG[].max_n, m.threads)))
    nsb_println()
    return nothing
end

"Горизонтальная линия-разделитель."
function nsb_rule(ch::Char = '─'; width::Int = 78)
    nsb_println(nsb_muted(string(ch)^width))
end

"Заголовок секции."
function nsb_header(s::AbstractString)
    nsb_println()
    nsb_rule('━')
    nsb_println(nsb_rgb(NSB_C_ACCENT..., NSB_ANSI_B * "  " * s * NSB_ANSI_RESET))
    nsb_rule('━')
    return nothing
end

# --------------------------------------------------------------- ввод
"Читаем строку; в batch-режиме берём из готового списка ответов."
const NSB_STDIN_ANSWERS = Ref{Vector{String}}(String[])
const NSB_STDIN_IDX = Ref(0)

function nsb_readline(prompt::AbstractString = "")
    nsb_print(nsb_rgb(NSB_C_ACCENT..., prompt))
    if !isempty(NSB_STDIN_ANSWERS[]) && NSB_STDIN_IDX[] <= length(NSB_STDIN_ANSWERS[])
        ans = NSB_STDIN_ANSWERS[][NSB_STDIN_IDX[]]
        NSB_STDIN_IDX[] += 1
        nsb_println(ans)   # эхо в лог
        return strip(ans)
    end
    if !NSB_TTY_STDOUT[] && !isa(stdin, Base.TTY)
        # piped stdin
        line = readline(stdin)
        nsb_println(line)
        return strip(line)
    end
    line = readline(stdin)
    nsb_println("")   # в лог (эхо уже выведено)
    return strip(line)
end

function nsb_ask_int(prompt::AbstractString, default::Int, lo::Int, hi::Int)
    while true
        s = nsb_readline(prompt * " ")
        if isempty(s)
            return default
        end
        v = tryparse(Int, s)
        if v === nothing || v < lo || v > hi
            nsb_println(nsb_warn(L("bad_number") * " [$lo..$hi]"))
            continue
        end
        return v
    end
end

function nsb_ask_float(prompt::AbstractString, default::Float64)
    while true
        s = nsb_readline(prompt * " ")
        isempty(s) && return default
        v = tryparse(Float64, replace(s, "," => "."))
        v === nothing || isnan(v) && (v = nothing)
        if v === nothing
            nsb_println(nsb_warn(L("bad_number")))
            continue
        end
        return v
    end
end

# --------------------------------------------------------------- пейджер
"Скроллинг длинного текста: страницы по высоте терминала, q/b/Enter."
function nsb_page(text::AbstractString)
    lines = split(text, '\n')
    if !NSB_TTY_STDOUT[]
        nsb_println(text)
        return nothing
    end
    h = Base.termheight()
    page_h = max(6, h - 3)
    i = 1
    n = length(lines)
    while i <= n
        j = min(n, i + page_h - 1)
        for k in i:j
            nsb_println(lines[k])
        end
        if j >= n
            nsb_println(nsb_muted(Lf("pager_end", n)))
            break
        end
        nsb_print(nsb_dim(L("pager_hint")))
        ans = NSB_TTY_STDOUT[] ? readline(stdin) : ""
        nsb_println("")
        c = strip(ans)
        (c == "q" || c == "Q" || c == "й" || c == "Й") && break
        if (c == "b" || c == "B" || c == "и" || c == "И")
            i = max(1, i - page_h)
            continue
        end
        i = j + 1
    end
    return nothing
end

# --------------------------------------------------------------- прогресс
const NSB_PROG_LAST = Ref(0.0)

"Прогресс-бар: TTY — перерисовка \r, иначе строка каждые 10%."
function nsb_progress(frac::Real, label::AbstractString = ""; t0::Float64 = time(),
                     total_units::Int = 0, done_units::Int = 0)
    frac = clamp(Float64(frac), 0.0, 1.0)
    if !NSB_TTY_STDOUT[]
        if frac - NSB_PROG_LAST[] >= 0.1 || frac >= 1.0
            NSB_PROG_LAST[] = frac
            nsb_println(@sprintf("  [%3d%%] %s", round(Int, frac * 100), label))
        end
        return nothing
    end
    W = 34
    fill = round(Int, frac * W)
    el = time() - t0
    eta = frac > 0.005 ? el / frac - el : NaN
    fmt_t(t) = (isnan(t) ? " --:--" :
        @sprintf("%02d:%02d", floor(Int, t / 60), floor(Int, t) % 60))
    bar = ""
    for i in 1:W
        if i <= fill
            r = round(Int, 40 + 180 * (i / W)); g = round(Int, 80 + 170 * (i / W)); b = 255
            bar *= nsb_rgb(r, g, b, "█")
        else
            bar *= nsb_rgb(NSB_C_MUT..., "░")
        end
    end
    info = @sprintf(" %5.1f%%", frac * 100)
    tail = ""
    if total_units > 0
        tail = @sprintf(" · %s %d/%d · %.1f %s · %s %s",
            L("prog_step"), done_units, total_units,
            done_units / max(el, 1e-9), L("prog_rate"),
            L("prog_eta"), fmt_t(eta))
    else
        tail = @sprintf(" · %s %s", L("prog_elapsed"), fmt_t(el))
    end
    print("\r" * " "^(min(160, displaysize(stdout)[2] - 1)) * "\r")
    print(nsb_rgb(NSB_C_ACCENT..., " ▸ ") * label * " ▕" * bar * "▏" * info * nsb_muted(tail))
    flush(stdout)
    frac >= 1.0 && print("\n")
    return nothing
end

# --------------------------------------------------------------- спарклайн
const NSB_SPARK = "▁▂▃▄▅▆▇█"

"Мини-график в одну строку."
function nsb_sparkline(v::Vector{Float64}; width::Int = 40)
    isempty(v) && return ""
    n = length(v)
    idx = round.(Int, range(1, n; length = min(width, n)))
    vals = [max(v[i], 0.0) for i in idx]
    lo, hi = minimum(vals), maximum(vals)
    rng = hi > lo ? hi - lo : 1.0
    s = IOBuffer()
    for x in vals
        k = clamp(round(Int, (x - lo) / rng * (length(NSB_SPARK) - 1)) + 1, 1, length(NSB_SPARK))
        print(s, NSB_SPARK[k])
    end
    return String(take!(s))
end

# --------------------------------------------------------------- терминал-картинка
"Поле → цветные полублоки в терминале (truecolor/256). В batch — подпись."
function nsb_term_image(field::AbstractMatrix{Float64}, caption::AbstractString;
                        w::Int = 56, h::Int = 22)
    if !NSB_TTY_STDOUT[] || !NSB_COLOR[]
        nsb_println(nsb_muted("  [🖼 " * caption * " → plots/*.png " *
                              @sprintf("%d dpi", NSB_CFG[].dpi) * "]"))
        return nothing
    end
    ny, nx = size(field)
    img = Matrix{NTuple{3,UInt8}}(undef, h, w)
    for j in 1:h, i in 1:w
        x0 = round(Int, (i - 1) / w * nx) + 1
        x1 = max(x0, round(Int, i / w * nx))
        y0 = round(Int, (j - 1) / h * ny) + 1
        y1 = max(y0, round(Int, j / h * ny))
        # усредняем блок; нижний полублок — нижняя половина ячейки
        top = field[max(y0, 1):(y0 + y1) ÷ 2, x0:min(x1, nx)]
        bot = field[((y0 + y1) ÷ 2 + 1):max(y1, (y0 + y1) ÷ 2 + 1), x0:min(x1, nx)]
        ctop = nsb_viridis(mean(isempty(top) ? [0.0] : vec(top)), minimum(field), maximum(field))
        cbot = nsb_viridis(mean(isempty(bot) ? [0.0] : vec(bot)), minimum(field), maximum(field))
        img[j, i] = (ctop, cbot)
    end
    nsb_println()
    for j in 1:h
        row = IOBuffer()
        for i in 1:w
            ct, cb = img[j, i]
            if NSB_TRUECOLOR[]
                print(row, "\e[38;2;$(ct[1]);$(ct[2]);$(ct[3]);48;2;$(cb[1]);$(cb[2]);$(cb[3])m▀")
            else
                print(row, "\e[38;5;$(nsb_256(ct))m▀")
            end
        end
        nsb_println(String(take!(row)) * NSB_ANSI_RESET)
    end
    nsb_println(nsb_muted("  " * caption))
    return nothing
end

function nsb_256(c::NTuple{3,UInt8})
    q = (x) -> (x > 127 ? 5 : round(Int, x / 43))
    return 16 + 36 * q(c[1]) + 6 * q(c[2]) + q(c[3])
end

# --------------------------------------------------------------- рамки
function nsb_box(lines::Vector{String}; color = NSB_C_ACCENT, pad::Int = 1)
    w = maximum(length(replace(l, r"\e\[[0-9;]*m" => "")) for l in lines) + 2 * pad
    top = "╔" * "═"^w * "╗"
    mid = ["║" * " "^pad * l * " "^pad * "║" for l in lines]
    bot = "╚" * "═"^w * "╝"
    for ln in (top, mid..., bot)
        nsb_println(nsb_rgb(color..., ln))
    end
    return nothing
end

"Пометка verdict: ok/fail/warn цветом."
function nsb_verdict_line(ok::Bool, text::AbstractString, detail::AbstractString = "")
    line = (ok ? nsb_ok(L(text)) : nsb_bad(L(text)))
    isempty(detail) || (line *= nsb_muted("  (" * detail * ")"))
    nsb_println("  " * line)
    return nothing
end
