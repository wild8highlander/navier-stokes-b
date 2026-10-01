# 04_font.jl — парсер TTF (cmap/hmtx/loca/glyf) и растеризатор глифов
# (ненулевое обходное число, суперсэмплинг, кэш битмапов). Кириллица+математика.
# ВСЕ смещения внутри парсера — 0-базные (как в спецификации TTF).

struct NsbFont
    units_per_em::Int
    num_glyphs::Int
    cmap::Dict{Int,Int}
    hmetrics::Vector{Int}
    num_hmetrics::Int
    loca::Vector{Int}
    glyf_off::Int
    glyf_len::Int
    ascender::Int
    descender::Int
    contours_cache::Dict{Int,Vector{Vector{Tuple{Bool,Float64,Float64}}}}
end

@inline _u8(b::Vector{UInt8}, o::Int) = Int(b[o+1])
@inline _u16(b::Vector{UInt8}, o::Int) = Int(b[o+1]) << 8 | Int(b[o+2])
@inline _s16(b::Vector{UInt8}, o::Int) = (v = _u16(b, o); v ≥ 0x8000 ? v - 0x10000 : v)
@inline _u32(b::Vector{UInt8}, o::Int) = (Int(b[o+1]) << 24) | (Int(b[o+2]) << 16) |
    (Int(b[o+3]) << 8) | Int(b[o+4])

function nsb_font_parse(bytes::Vector{UInt8})::NsbFont
    num_tables = _u16(bytes, 4)
    tables = Dict{String,Tuple{Int,Int}}()
    for t in 0:num_tables-1
        rec = 12 + 16 * t
        tag = String(bytes[rec+1:rec+4])
        tables[tag] = (_u32(bytes, rec + 8), _u32(bytes, rec + 12))
    end
    head_off, = tables["head"]
    units_per_em = _u16(bytes, head_off + 18)
    index_to_loc_format = _s16(bytes, head_off + 50)
    hhea_off, = tables["hhea"]
    ascender = _s16(bytes, hhea_off + 4)
    descender = _s16(bytes, hhea_off + 6)
    num_hmetrics = _u16(bytes, hhea_off + 34)
    maxp_off, = tables["maxp"]
    num_glyphs = _u16(bytes, maxp_off + 4)
    hmtx_off, = tables["hmtx"]
    hmetrics = [ _u16(bytes, hmtx_off + 4 * (i - 1)) for i in 1:num_hmetrics ]
    cmap_off, = tables["cmap"]
    n_sub = _u16(bytes, cmap_off + 2)
    best = 0
    for s in 0:n_sub-1
        po = cmap_off + 4 + 8 * s
        pid, eid = _u16(bytes, po), _u16(bytes, po + 2)
        sub = cmap_off + _u32(bytes, po + 4)
        if (pid == 3 && (eid == 1 || eid == 10)) || (pid == 0 && best == 0)
            best = sub
            (pid == 3 && eid == 1) && break
        end
    end
    best > 0 || error("cmap: подходящая субтаблица не найдена")
    cmap = Dict{Int,Int}()
    fmt = _u16(bytes, best)
    if fmt == 4
        segX2 = _u16(bytes, best + 6)
        seg = segX2 ÷ 2
        endo = best + 14
        starto = endo + segX2 + 2
        deltao = starto + segX2
        rangeo = deltao + segX2
        for s in 1:seg
            stop = _u16(bytes, endo + 2 * (s - 1))
            start = _u16(bytes, starto + 2 * (s - 1))
            delta = _s16(bytes, deltao + 2 * (s - 1))
            ro = _u16(bytes, rangeo + 2 * (s - 1))
            for cp in start:stop
                if ro == 0
                    g = (cp + delta) & 0xFFFF
                else
                    gi = rangeo + 2 * (s - 1) + ro + 2 * (cp - start)
                    g = _u16(bytes, best + gi)
                    g = (g == 0) ? 0 : (g + delta) & 0xFFFF
                end
                g != 0 && (cmap[cp] = g)
            end
        end
    elseif fmt == 12
        n_groups = _u32(bytes, best + 12)
        for gI in 0:n_groups-1
            go = best + 16 + 12 * gI
            sC, eC, gS = _u32(bytes, go), _u32(bytes, go + 4), _u32(bytes, go + 8)
            for cp in sC:eC
                cmap[cp] = gS + cp - sC
            end
        end
    else
        error("cmap format $fmt не поддержан")
    end
    loca_off, = tables["loca"]
    loca = Vector{Int}(undef, num_glyphs + 1)
    if index_to_loc_format == 0
        for i in 0:num_glyphs
            loca[i+1] = 2 * _u16(bytes, loca_off + 2 * i)
        end
    else
        for i in 0:num_glyphs
            loca[i+1] = _u32(bytes, loca_off + 4 * i)
        end
    end
    glyf_off, glyf_len = tables["glyf"]
    return NsbFont(units_per_em, num_glyphs, cmap, hmetrics, num_hmetrics,
                   loca, glyf_off, glyf_len, ascender, descender,
                   Dict{Int,Vector{Vector{Tuple{Bool,Float64,Float64}}}}())
end

nsb_font_regular() = nsb_font_parse_and_register(NSB_FONT_REG_BYTES)
nsb_font_bold() = nsb_font_parse_and_register(NSB_FONT_BOLD_BYTES)

nsb_gid(f::NsbFont, cp::Int) = get(f.cmap, cp, 0)
nsb_gid(f::NsbFont, c::Char) = nsb_gid(f, Int(c))

"Ширина символа в единицах шрифта."
@inline nsb_advance(f::NsbFont, gid::Int) =
    gid < f.num_hmetrics ? f.hmetrics[gid+1] : f.hmetrics[end]

"Ширина строки в пикселях при размере px (em = px)."
function nsb_text_width(f::NsbFont, s::AbstractString, px::Real)::Float64
    w = 0.0
    for ch in s
        w += nsb_advance(f, nsb_gid(f, Int(ch)))
    end
    return w / f.units_per_em * px
end

"Контур глифа: вектор контуров из точек (on_curve, x, y) в единицах шрифта."
function nsb_glyph_contours(f::NsbFont, gid::Int)
    haskey(f.contours_cache, gid) && return f.contours_cache[gid]
    res = Vector{Vector{Tuple{Bool,Float64,Float64}}}()
    if 0 ≤ gid < f.num_glyphs
        off = f.glyf_off + f.loca[gid+1]
        endoff = f.glyf_off + f.loca[gid+2]
        if off < endoff
            res = nsb_glyph_contours_raw(f, off, endoff)
        end
    end
    f.contours_cache[gid] = res
    return res
end

# байты: храним рядом по objectid шрифта
const NSB_FONT_BYTES_MAP = Dict{UInt64,Vector{UInt8}}()
_nsb_font_bytes(f::NsbFont) = NSB_FONT_BYTES_MAP[objectid(f)]

function nsb_font_register!(f::NsbFont, bytes::Vector{UInt8})
    NSB_FONT_BYTES_MAP[objectid(f)] = bytes
    return f
end

function nsb_font_parse_and_register(bytes::Vector{UInt8})
    return nsb_font_register!(nsb_font_parse(bytes), bytes)
end

function nsb_glyph_contours_raw(f::NsbFont, off::Int, endoff::Int)
    b = _nsb_font_bytes(f)
    res = Vector{Vector{Tuple{Bool,Float64,Float64}}}()
    ncont = _s16(b, off)
    if ncont < 0
        # составной глиф: рекурсивно собираем компоненты со сдвигами
        p = off + 10
        while true
            flags = _u16(b, p); gidx = _u16(b, p + 2)
            p += 4
            arg1 = (flags & 0x01 != 0) ? _s16(b, p) : Int(Int8(_u8(b, p)))
            arg2 = (flags & 0x01 != 0) ? _s16(b, p + 2) : Int(Int8(_u8(b, p + 1)))
            p += (flags & 0x01 != 0) ? 4 : 2
            dx = 0.0; dy = 0.0
            if flags & 0x02 != 0          # ARGS_ARE_XY_VALUES
                dx = Float64(arg1); dy = Float64(arg2)
            end
            scale = 1.0
            if flags & 0x08 != 0          # WE_HAVE_A_SCALE (F2Dot14)
                scale = _s16(b, p) / 16384.0; p += 2
            elseif flags & 0x40 != 0      # X_AND_Y_SCALE
                p += 4
            elseif flags & 0x80 != 0      # TWO_BY_TWO
                p += 8
            end
            c1 = f.glyf_off + f.loca[gidx+1]
            c2 = f.glyf_off + f.loca[gidx+2]
            if c1 < c2
                for cont in nsb_glyph_contours_raw(f, c1, c2)
                    push!(res, [(on, x * scale + dx, y * scale + dy)
                                for (on, x, y) in cont])
                end
            end
            flags & 0x20 == 0 && break    # MORE_COMPONENTS
        end
        return res
    end
    ncont == 0 && return res
    endpts = [ _u16(b, off + 10 + 2 * (i - 1)) for i in 1:ncont ]
    instr_len = _u16(b, off + 10 + 2 * ncont)
    p = off + 12 + 2 * ncont + instr_len
    npts = endpts[end] + 1
    flags = Vector{UInt8}(undef, npts)
    i = 1
    while i <= npts
        fl = _u8(b, p); p += 1
        flags[i] = fl
        i += 1
        if fl & 0x08 != 0
            rep = _u8(b, p); p += 1
            for _ in 1:rep
                flags[i] = fl
                i += 1
            end
        end
    end
    xs = Vector{Float64}(undef, npts)
    x = 0.0
    for i in 1:npts
        fl = flags[i]
        if fl & 0x02 != 0
            dx = _u8(b, p); p += 1
            dx = (fl & 0x10 != 0) ? dx : -dx
        elseif fl & 0x10 != 0
            dx = 0
        else
            dx = _s16(b, p); p += 2
        end
        x += dx
        xs[i] = x
    end
    ys = Vector{Float64}(undef, npts)
    y = 0.0
    for i in 1:npts
        fl = flags[i]
        if fl & 0x04 != 0
            dy = _u8(b, p); p += 1
            dy = (fl & 0x20 != 0) ? dy : -dy
        elseif fl & 0x20 != 0
            dy = 0
        else
            dy = _s16(b, p); p += 2
        end
        y += dy
        ys[i] = y
    end
    pts = [ (flags[i] & 0x01 != 0, xs[i], ys[i]) for i in 1:npts ]
    for c in 1:ncont
        lo = (c == 1) ? 1 : endpts[c-1] + 1
        hi = endpts[c]
        contour = pts[lo:hi]
        push!(res, nsb_implied_points(contour))
    end
    return res
end

"Циклическая вставка мнимых on-curve точек между парами off-curve."
function nsb_implied_points(contour::Vector{Tuple{Bool,Float64,Float64}})
    n = length(contour)
    n == 0 && return contour
    out = Vector{Tuple{Bool,Float64,Float64}}()
    for i in 1:n
        cur = contour[i]
        nxt = contour[mod1(i + 1, n)]
        push!(out, cur)
        if !cur[1] && !nxt[1]
            push!(out, (true, (cur[2] + nxt[2]) / 2, (cur[3] + nxt[3]) / 2))
        end
    end
    return out
end

# --------------------------------------------------------------- растеризатор
const NSB_GLYPH_CACHE = Dict{Tuple{Int,Int},Tuple{Int,Int,Vector{Float32}}}()

"Альфа-битмап глифа при размере px. Возвращает (w, h, alpha-буфер)."
function nsb_glyph_bitmap(f::NsbFont, gid::Int, px::Int)
    key = (objectid(f) >>> 8, gid * 4096 + px)
    haskey(NSB_GLYPH_CACHE, key) && return NSB_GLYPH_CACHE[key]
    contours = nsb_glyph_contours(f, gid)
    if isempty(contours)
        NSB_GLYPH_CACHE[key] = (0, 0, Float32[])
        return NSB_GLYPH_CACHE[key]
    end
    S = 3                       # суперсэмплинг
    upm = f.units_per_em
    scale = px / upm
    # bbox
    xmin = Inf; xmax = -Inf; ymin = Inf; ymax = -Inf
    for c in contours, (_, x, y) in c
        xmin = min(xmin, x); xmax = max(xmax, x)
        ymin = min(ymin, y); ymax = max(ymax, y)
    end
    bw = ceil(Int, (xmax - xmin) * scale) + 2
    bh = ceil(Int, (ymax - ymin) * scale) + 2
    bw = max(bw, 1); bh = max(bh, 1)
    cov = zeros(Float32, bw * S, bh * S)
    # ЕДИНЫЙ список рёбер всех контуров (дырки вычитаются обходным числом)
    edges = Tuple{Float64,Float64,Float64,Float64}[]   # (x1,y1,x2,y2) в пикселях
    for cont in contours
        np = length(cont)
        np < 2 && continue
        poly = Tuple{Float64,Float64}[]
        for i in 1:np
            p0 = cont[i]
            p1 = cont[mod1(i + 1, np)]
            if p0[1] && p1[1]                       # on -> on: отрезок
                push!(poly, (p0[2], p0[3]))
            elseif !p0[1]                           # off: квадратика от prev-on
                pp = cont[mod1(i - 1, np)]
                c0 = (pp[2], pp[3]); c1 = (p0[2], p0[3]); c2 = (p1[2], p1[3])
                if !p1[1]
                    c2 = ((p0[2] + p1[2]) / 2, (p0[3] + p1[3]) / 2)
                end
                for k in 1:8
                    t = k / 8
                    mt = 1 - t
                    x = mt^2 * c0[1] + 2 * mt * t * c1[1] + t^2 * c2[1]
                    y = mt^2 * c0[2] + 2 * mt * t * c1[2] + t^2 * c2[2]
                    push!(poly, (x, y))
                end
            end
        end
        m = length(poly)
        m < 3 && continue
        for i in 1:m
            a1 = poly[i]; b1 = poly[mod1(i + 1, m)]
            push!(edges, ((a1[1] - xmin) * scale + 1.0, (a1[2] - ymin) * scale + 1.0,
                          (b1[1] - xmin) * scale + 1.0, (b1[2] - ymin) * scale + 1.0))
        end
    end
    # скан-заливка с ненулевым числом обхода по ВСЕМ рёбрам
    ne = length(edges)
    for sy in 1:bh * S
        ys = sy - 0.5
        xsI = Float64[]; dirI = Int[]
        for e in edges
            x1, y1, x2, y2 = e
            if (y1 <= ys && y2 > ys) || (y2 <= ys && y1 > ys)
                t = (ys - y1) / (y2 - y1)
                push!(xsI, x1 + t * (x2 - x1))
                push!(dirI, y2 > y1 ? 1 : -1)
            end
        end
        isempty(xsI) && continue
        ord = sortperm(xsI)
        wind = 0
        for k in 1:length(ord)-1
            wind += dirI[ord[k]]
            wind == 0 && continue
            a = ceil(Int, xsI[ord[k]] * S)
            b = floor(Int, xsI[ord[k+1]] * S)
            a = max(a, 1); b = min(b, bw * S)
            for sx in a:b
                cov[sx, sy] = 1.0f0
            end
        end
    end
    alpha = Vector{Float32}(undef, bw * bh)
    for yy in 1:bh, xx in 1:bw
        s = 0.0f0
        for sj in 1:S, si in 1:S
            s += cov[(xx - 1) * S + si, (yy - 1) * S + sj]
        end
        alpha[(yy - 1) * bw + xx] = s / S^2
    end
    NSB_GLYPH_CACHE[key] = (bw, bh, alpha)
    return NSB_GLYPH_CACHE[key]
end

"Текст на канвас: (x, y_baseline), px = размер em в пикселях."
function nsb_draw_text!(c::NsbCanvas, f::NsbFont, x::Real, y::Real,
                        s::AbstractString, px::Real, col::NTuple{3,Int};
                        bold::Bool = false)
    x = Float64(x); y = Float64(y); px = Float64(px)
    g = bold ? NSB_FONT_BOLD : f
    scale = px / g.units_per_em
    pen = x
    for ch in s
        gid = nsb_gid(g, Int(ch))
        adv = nsb_advance(g, gid) * scale
        ch == ' ' && (pen += adv; continue)
        gid == 0 && (pen += adv; continue)
        bw, bh, alpha = nsb_glyph_bitmap(g, gid, max(6, round(Int, px)))
        # позиция глифа: baseline в y, левый край в pen
        gx = round(Int, pen)
        gy = round(Int, y)
        for yy in 1:bh, xx in 1:bw
            a = alpha[(yy - 1) * bw + xx]
            a <= 0.003 && continue
            # битмап: строка 1 = низ глифа (фонт-y растёт вверх) → на канвасе вверх = y минус
            nsb_blend!(c, gx + xx - 1, gy - (yy - 1), col, a)
        end
        pen += adv
    end
    return pen
end

nsb_draw_text!(c::NsbCanvas, x::Real, y::Real, s::AbstractString, px::Real,
               col::NTuple{3,Int}; bold::Bool = false) =
    nsb_draw_text!(c, NSB_FONT_REG, x, y, s, px, col; bold = bold)

# --------------------------------------------------------------- глобальные шрифты
const NSB_FONT_REG = nsb_font_regular()
const NSB_FONT_BOLD = nsb_font_bold()
