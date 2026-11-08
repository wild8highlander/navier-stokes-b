# 05_plots.jl — графический движок: линейные графики, тепловые карты, мультипанели.
# Два бэкенда: PNG 600 dpi (растеризация собственным шрифтом) и SVG (для HTML).

const NSB_PAL = NTuple{3,Int}[
    (37, 99, 235), (220, 38, 38), (5, 150, 105), (217, 119, 6),
    (126, 34, 206), (8, 145, 178), (190, 24, 93), (101, 163, 13)]

struct NsbSeries
    xs::Vector{Float64}
    ys::Vector{Float64}
    color::NTuple{3,Int}
    label::String
    lw::Float64
    dashed::Bool
end
NsbSeries(xs, ys, color, label = "", lw = 2.0, dashed = false) =
    NsbSeries(Float64.(xs), Float64.(ys), color, label, lw, dashed)

struct NsbPlot
    title::String
    xlabel::String
    ylabel::String
    series::Vector{NsbSeries}
    logy::Bool
    grid::Bool
    legend::Bool
end
function NsbPlot(title, xlabel, ylabel, series::Vector; logy = false, grid = true,
                 legend = true)
    conv = NsbSeries[]
    for s in series
        if s isa NsbSeries
            push!(conv, s)
        elseif s isa Tuple || s isa Vector
            push!(conv, NsbSeries(s[1], s[2], length(s) ≥ 3 ? s[3] : NSB_PAL[1],
                                  length(s) ≥ 4 ? String(s[4]) : ""))
        end
    end
    return NsbPlot(title, xlabel, ylabel, conv, logy, grid, legend)
end
NsbPlot(title, xlabel, ylabel, s::NsbSeries; kw...) = NsbPlot(title, xlabel, ylabel, [s]; kw...)

struct NsbHeat
    title::String
    field::Matrix{Float64}
    signed::Bool
    xlabel::String
    ylabel::String
    colorbar::Bool
end

# --------------------------------------------------------------- тики
function nsb_nice_step(span::Float64, target::Int)
    span <= 0 && return 1.0
    raw = span / max(target, 1)
    mag = 10.0^floor(log10(raw))
    for m in (1.0, 2.0, 2.5, 5.0, 10.0)
        raw <= m * mag && return m * mag
    end
    return 10 * mag
end

function nsb_fmt_tick(v::Float64, step::Float64)
    a = abs(v)
    if a >= 1e5 || (a < 1e-3 && a > 0)
        return @sprintf("%.0e", v)
    elseif step >= 1
        return @sprintf("%d", round(Int, v))
    elseif step >= 0.1
        return @sprintf("%.1f", v)
    else
        return @sprintf("%.2g", v)
    end
end

# --------------------------------------------------------------- внутренняя отрисовка
"Отрисовка линейного графика в прямоугольник канваса (px координаты)."
function nsb_draw_plot!(c::NsbCanvas, R::NTuple{4,Int}, p::NsbPlot)
    x0, y0, w, h = R          # y0 — верх
    m = max(10, round(Int, h * 0.10))
    pad_l = max(56, round(Int, w * 0.11))
    pad_r = 14
    pad_t = (isempty(p.title) ? 10 : max(26, round(Int, h * 0.09)))
    pad_b = max(40, round(Int, h * 0.15))
    ax_x, ax_y = x0 + pad_l, y0 + pad_t
    ax_w = max(20, w - pad_l - pad_r)
    ax_h = max(20, h - pad_t - pad_b)
    frame = (110, 116, 140)
    gridc = (225, 229, 240)
    # диапазоны
    allx = Float64[]; ally = Float64[]
    for s in p.series
        append!(allx, s.xs); append!(ally, s.ys)
    end
    isempty(allx) && return nothing
    filter!(isfinite, allx); filter!(isfinite, ally)
    xmin, xmax = extrema(allx); ymin, ymax = extrema(ally)
    xmin == xmax && (xmax = xmin + 1)
    if p.logy
        ally_f = filter(>(0.0), ally)
        isempty(ally_f) && return nothing
        ymin, ymax = extrema(ally_f)
        ymin = max(ymin, 1e-300)
        ymin = 10.0^floor(log10(ymin))
        ymax = 10.0^ceil(log10(max(ymax, ymin * 10)))
    else
        span = ymax - ymin
        ymin -= 0.06 * span + (span == 0 ? 0.5 : 0)
        ymax += 0.06 * span + (span == 0 ? 0.5 : 0)
    end
    topx(x) = ax_x + (x - xmin) / (xmax - xmin) * ax_w
    topy(y) = p.logy ? ax_y + ax_h - (log10(max(y, 1e-300)) - log10(ymin)) /
        (log10(ymax) - log10(ymin)) * ax_h :
        ax_y + ax_h - (y - ymin) / (ymax - ymin) * ax_h
    fs = max(9, round(Int, h * 0.045))          # размер шрифта меток
    # сетка и тики
    stx = nsb_nice_step(xmax - xmin, 6)
    sty = p.logy ? 1.0 : nsb_nice_step(ymax - ymin, 5)
    if p.grid
        tv = xmin:stx:xmax
        for t in tv
            X = round(Int, topx(t))
            0 <= X - ax_x <= ax_w && nsb_line!(c, X, ax_y, X, ax_y + ax_h, gridc; lw = 1.0)
        end
        if p.logy
            d = floor(Int, log10(ymin)):ceil(Int, log10(ymax))
            for e in d
                Y = round(Int, topy(10.0^e))
                ax_y <= Y <= ax_y + ax_h && nsb_line!(c, ax_x, Y, ax_x + ax_w, Y, gridc; lw = 1.0)
            end
        else
            for t in ymin:sty:ymax
                Y = round(Int, topy(t))
                ax_y <= Y <= ax_y + ax_h && nsb_line!(c, ax_x, Y, ax_x + ax_w, Y, gridc; lw = 1.0)
            end
        end
    end
    # оси
    nsb_line!(c, ax_x, ax_y + ax_h, ax_x + ax_w, ax_y + ax_h, frame; lw = 2.0)
    nsb_line!(c, ax_x, ax_y, ax_x, ax_y + ax_h, frame; lw = 2.0)
    # подписи тиков
    for t in xmin:stx:xmax
        X = topx(t); Yt = ax_y + ax_h
        nsb_line!(c, X, Yt, X, Yt + 4, frame; lw = 1.5)
        s = nsb_fmt_tick(t, stx)
        nsb_draw_text!(c, X - nsb_text_width(NSB_FONT_REG, s, fs) / 2,
                       Yt + 5 + fs, s, fs, (70, 74, 94))
    end
    if p.logy
        d = floor(Int, log10(ymin)):ceil(Int, log10(ymax))
        for e in d
            Y = topy(10.0^e); (ax_y <= Y <= ax_y + ax_h) || continue
            nsb_line!(c, ax_x - 4, Y, ax_x, Y, frame; lw = 1.5)
            s = "1e$e"
            nsb_draw_text!(c, ax_x - 6 - nsb_text_width(NSB_FONT_REG, s, fs),
                           Y + fs * 0.4, s, fs, (70, 74, 94))
        end
    else
        for t in ymin:sty:ymax
            Y = topy(t); (ax_y <= Y <= ax_y + ax_h) || continue
            nsb_line!(c, ax_x - 4, Y, ax_x, Y, frame; lw = 1.5)
            s = nsb_fmt_tick(t, sty)
            nsb_draw_text!(c, ax_x - 6 - nsb_text_width(NSB_FONT_REG, s, fs),
                           Y + fs * 0.4, s, fs, (70, 74, 94))
        end
    end
    # серии
    for s in p.series
        n = length(s.xs)
        n < 2 && continue
        prev = nothing
        for i in 1:n
            isfinite(s.ys[i]) || (prev = nothing; continue)
            X = topx(s.xs[i]); Y = topy(s.ys[i])
            if prev !== nothing
                if s.dashed
                    nsb_dashed_line!(c, prev[1], prev[2], X, Y, s.color; lw = s.lw)
                else
                    nsb_line!(c, prev[1], prev[2], X, Y, s.color; lw = s.lw)
                end
            end
            prev = (X, Y)
        end
    end
    # легенда
    if p.legend && any(!isempty(s.label) for s in p.series)
        lh = round(Int, fs * 1.6)
        items = [s for s in p.series if !isempty(s.label)]
        tw = maximum(nsb_text_width(NSB_FONT_REG, s.label, fs) for s in items)
        lw_ = round(Int, tw + fs * 5)
        lx = ax_x + ax_w - lw_ - 8
        ly = ax_y + 8
        nsb_rect!(c, lx, ly, lw_, length(items) * lh + 6, (255, 255, 255);
                  outline = (200, 205, 220))
        for (i, s) in enumerate(items)
            yy = ly + i * lh - lh ÷ 3
            nsb_line!(c, lx + 6, yy, lx + 6 + fs * 3, yy, s.color; lw = s.lw)
            nsb_draw_text!(c, lx + fs * 4, yy + fs * 0.45, s.label, fs, (50, 54, 74))
        end
    end
    # заголовки
    if !isempty(p.title)
        tfs = round(Int, fs * 1.35)
        nsb_draw_text!(c, x0 + w / 2 - nsb_text_width(NSB_FONT_REG, p.title, tfs) / 2,
                       y0 + pad_t - 8, p.title, tfs, (25, 28, 48); bold = true)
    end
    if !isempty(p.xlabel)
        nsb_draw_text!(c, ax_x + ax_w / 2 - nsb_text_width(NSB_FONT_REG, p.xlabel, fs) / 2,
                       y0 + h - 6, p.xlabel, fs, (40, 44, 66))
    end
    if !isempty(p.ylabel)
        s = p.ylabel
        for (i, ch) in enumerate(s)
            nsb_draw_text!(c, x0 + 12, ax_y + ax_h / 2 -
                nsb_text_width(NSB_FONT_REG, s, fs) / 2 + (i - 1) * fs * 1.15,
                string(ch), fs, (40, 44, 66))
        end
    end
    return nothing
end

function nsb_dashed_line!(c::NsbCanvas, x0, y0, x1, y1, col; lw = 1.5, dash = 5.0, gap = 4.0)
    dx, dy = x1 - x0, y1 - y0
    L = hypot(dx, dy)
    L < 1e-9 && return nothing
    ux, uy = dx / L, dy / L
    t = 0.0
    while t < L
        t2 = min(L, t + dash)
        nsb_line!(c, x0 + ux * t, y0 + uy * t, x0 + ux * t2, y0 + uy * t2, col; lw = lw)
        t = t2 + gap
    end
    return nothing
end

"Тепловая карта в прямоугольник канваса."
function nsb_draw_heat!(c::NsbCanvas, R::NTuple{4,Int}, q::NsbHeat)
    x0, y0, w, h = R
    pad_l = max(46, round(Int, w * 0.08))
    pad_r = q.colorbar ? 64 : 14
    pad_t = isempty(q.title) ? 8 : max(24, round(Int, h * 0.09))
    pad_b = 26
    ax_x, ax_y = x0 + pad_l, y0 + pad_t
    ax_w = max(10, w - pad_l - pad_r)
    ax_h = max(10, h - pad_t - pad_b)
    ny, nx = size(q.field)
    vmin, vmax = extrema(skipnan(q.field))
    m = q.signed ? max(abs(vmin), abs(vmax)) : 0.0
    for j in 1:ax_h, i in 1:ax_w
        fi = clamp(round(Int, (i - 1) / ax_w * nx) + 1, 1, nx)
        fj = clamp(round(Int, (j - 1) / ax_h * ny) + 1, 1, ny)
        v = q.field[fj, fi]
        col = q.signed ? nsb_coolwarm_signed(v, m) : nsb_viridis(v, vmin, vmax)
        nsb_setpx!(c, ax_x + i - 1, ax_y + j - 1, col)
    end
    frame = (110, 116, 140)
    for i in 0:ax_w
        (i == 0 || i == ax_w) && nsb_line!(c, ax_x + i, ax_y, ax_x + i, ax_y + ax_h, frame; lw = 1.0)
    end
    for j in 0:ax_h
        (j == 0 || j == ax_h) && nsb_line!(c, ax_x, ax_y + j, ax_x + ax_w, ax_y + j, frame; lw = 1.0)
    end
    fs = max(9, round(Int, h * 0.042))
    if q.colorbar
        cbx = ax_x + ax_w + 10
        cbw = 12
        for j in 1:ax_h
            t = 1 - (j - 1) / (ax_h - 1)
            col = q.signed ? nsb_coolwarm(t) : nsb_viridis(t)
            for i in 1:cbw
                nsb_setpx!(c, cbx + i - 1, ax_y + j - 1, col)
            end
        end
        nsb_rect!(c, cbx, ax_y, cbw, ax_h, (0, 0, 0))
        lo = q.signed ? -m : vmin
        hi = q.signed ? m : vmax
        for (t, s) in ((1.0, @sprintf("%.2g", hi)), (0.5, @sprintf("%.2g", (hi + lo) / 2)),
                       (0.0, @sprintf("%.2g", lo)))
            yy = round(Int, ax_y + (1 - t) * ax_h)
            nsb_draw_text!(c, cbx + cbw + 4, yy + fs * 0.35, s, fs, (50, 54, 74))
        end
    end
    if !isempty(q.title)
        tfs = round(Int, fs * 1.35)
        nsb_draw_text!(c, x0 + w / 2 - nsb_text_width(NSB_FONT_REG, q.title, tfs) / 2,
                       y0 + pad_t - 8, q.title, tfs, (25, 28, 48); bold = true)
    end
    return nothing
end

skipnan(v) = (x = collect(Iterators.filter(x -> !isnan(x), v)); isempty(x) ? [0.0] : x)

# --------------------------------------------------------------- сохранение
"Одиночный график → PNG с конфиг-DPI."
function nsb_save_plot_png(p::NsbPlot, path::AbstractString; dpi::Int = NSB_CFG[].dpi,
                           size_in::Tuple{Float64,Float64} = (6.4, 4.2))
    w = round(Int, size_in[1] * dpi)
    h = round(Int, size_in[2] * dpi)
    c = NsbCanvas(w, h)
    nsb_draw_plot!(c, (0, 0, w, h), p)
    return nsb_canvas_save_png(c, path)
end

function nsb_save_heat_png(q::NsbHeat, path::AbstractString; dpi::Int = NSB_CFG[].dpi,
                           size_in::Tuple{Float64,Float64} = (6.4, 4.6))
    w = round(Int, size_in[1] * dpi)
    h = round(Int, size_in[2] * dpi)
    c = NsbCanvas(w, h)
    nsb_draw_heat!(c, (0, 0, w, h), q)
    return nsb_canvas_save_png(c, path)
end

"Мультипанель: 2×2 и т.п. → один PNG."
function nsb_save_grid_png(items::Vector{Union{NsbPlot,NsbHeat}}, path::AbstractString;
                           dpi::Int = NSB_CFG[].dpi,
                           size_in::Tuple{Float64,Float64} = (9.6, 7.2),
                           rows::Int = 0, cols::Int = 0)
    n = length(items)
    n == 0 && return path
    rows = rows == 0 ? (n <= 2 ? 1 : 2) : rows
    cols = cols == 0 ? ceil(Int, n / rows) : cols
    w = round(Int, size_in[1] * dpi)
    h = round(Int, size_in[2] * dpi)
    c = NsbCanvas(w, h)
    gap = round(Int, dpi * 0.06)
    pw = (w - gap * (cols + 1)) ÷ cols
    ph = (h - gap * (rows + 1)) ÷ rows
    for (i, item) in enumerate(items)
        r = (i - 1) ÷ cols + 1
        cc = (i - 1) % cols + 1
        R = (gap + (cc - 1) * (pw + gap), gap + (r - 1) * (ph + gap), pw, ph)
        item isa NsbPlot ? nsb_draw_plot!(c, R, item) : nsb_draw_heat!(c, R, item)
    end
    return nsb_canvas_save_png(c, path)
end

# --------------------------------------------------------------- SVG бэкенд
_svg_esc(s) = replace(replace(replace(String(s), "&" => "&amp;"), "<" => "&lt;"), ">" => "&gt;")

"Линейный график → SVG-строка (для HTML-отчёта)."
function nsb_plot_svg(p::NsbPlot; width::Int = 640, height::Int = 420)
    io = IOBuffer()
    pad_l, pad_r, pad_t, pad_b = 56, 14, 40, 44
    ax_x, ax_y = pad_l, pad_t
    ax_w, ax_h = width - pad_l - pad_r, height - pad_t - pad_b
    allx = Float64[]; ally = Float64[]
    for s in p.series; append!(allx, s.xs); append!(ally, s.ys); end
    isempty(allx) && return ""
    xmin, xmax = extrema(allx); ymin, ymax = extrema(ally)
    xmin == xmax && (xmax += 1)
    ymin -= 0.06 * (ymax - ymin) + 1e-12; ymax += 0.06 * (ymax - ymin) + 1e-12
    topx(x) = ax_x + (x - xmin) / (xmax - xmin) * ax_w
    topy(y) = ax_y + ax_h - (y - ymin) / (ymax - ymin) * ax_h
    write(io, "<svg xmlns='http://www.w3.org/2000/svg' width='$width' height='$height' font-family='DejaVu Sans,Segoe UI,Arial,sans-serif'>")
    write(io, "<rect width='100%' height='100%' fill='white'/>")
    stx = nsb_nice_step(xmax - xmin, 6); sty = nsb_nice_step(ymax - ymin, 5)
    for t in xmin:stx:xmax
        write(io, "<line x1='$(topx(t))' y1='$ax_y' x2='$(topx(t))' y2='$(ax_y+ax_h)' stroke='#e5e9f2'/>")
    end
    for t in ymin:sty:ymax
        write(io, "<line x1='$ax_x' y1='$(topy(t))' x2='$(ax_x+ax_w)' y2='$(topy(t))' stroke='#e5e9f2'/>")
    end
    for t in xmin:stx:xmax
        write(io, "<text x='$(topx(t))' y='$(ax_y+ax_h+16)' font-size='11' text-anchor='middle' fill='#4a4f68'>$(_svg_esc(nsb_fmt_tick(t, stx)))</text>")
    end
    for t in ymin:sty:ymax
        write(io, "<text x='$(ax_x-6)' y='$(topy(t)+4)' font-size='11' text-anchor='end' fill='#4a4f68'>$(_svg_esc(nsb_fmt_tick(t, sty)))</text>")
    end
    for s in p.series
        n = length(s.xs)
        n < 2 && continue
        d = ""
        for i in 1:n
            isfinite(s.ys[i]) || continue
            d *= (isempty(d) ? "M" : "L") * @sprintf("%.1f,%.1f ", topx(s.xs[i]), topy(s.ys[i]))
        end
        col = @sprintf("#%02x%02x%02x", s.color...)
        dash = s.dashed ? " stroke-dasharray='6 4'" : ""
        write(io, "<path d='$d' fill='none' stroke='$col' stroke-width='$(s.lw)'$dash/>")
    end
    if p.legend && any(!isempty(s.label) for s in p.series)
        items = [s for s in p.series if !isempty(s.label)]
        yy = ax_y + 14
        for (i, s) in enumerate(items)
            col = @sprintf("#%02x%02x%02x", s.color...)
            ly = yy + (i - 1) * 16
            write(io, "<line x1='$(ax_x+ax_w-150)' y1='$ly' x2='$(ax_x+ax_w-130)' y2='$ly' stroke='$col' stroke-width='2'/>")
            write(io, "<text x='$(ax_x+ax_w-124)' y='$(ly+4)' font-size='11' fill='#33374a'>$(_svg_esc(s.label))</text>")
        end
    end
    write(io, "<text x='$(width/2)' y='20' font-size='15' font-weight='bold' text-anchor='middle' fill='#1a2c50'>$(_svg_esc(p.title))</text>")
    write(io, "<text x='$(ax_x+ax_w/2)' y='$(height-8)' font-size='12' text-anchor='middle' fill='#33374a'>$(_svg_esc(p.xlabel))</text>")
    write(io, "<text x='14' y='$(ax_y+ax_h/2)' font-size='12' text-anchor='middle' fill='#33374a' transform='rotate(-90 14 $(ax_y+ax_h/2))'>$(_svg_esc(p.ylabel))</text>")
    write(io, "</svg>")
    return String(take!(io))
end
