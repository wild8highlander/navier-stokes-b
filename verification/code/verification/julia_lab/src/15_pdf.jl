# 15_pdf.jl — генератор PDF 1.4 внутри кода: векторный текст (Type0/Identity-H
# с встроенными сабсетами DejaVu и ToUnicode), таблицы, векторные графики,
# растровые XObject-теплокарты, колонтитулы. Никаких внешних библиотек.

const NSB_PDF_W = 595.276      # A4, pt
const NSB_PDF_H = 841.89
const NSB_PDF_MARGIN = 54.0

mutable struct NsbPdf
    objs::Vector{Vector{UInt8}}           # сериализованные объекты
    page_ops::Vector{Vector{UInt8}}       # содержимое страниц (ops)
    page_objs::Vector{Int}                # номера объектов страниц
    font_reg::Int
    font_bold::Int
    fnt_reg_metrics::NsbFont
    fnt_bold_metrics::NsbFont
    images::Dict{String,Int}              # имя → obj номер XObject
    cury::Float64
end

_pdf_esc(s::AbstractString) = replace(String(s), "\\" => "\\\\", "(" => "\\(",
                                      ")" => "\\)")

function NsbPdf()
    objs = Vector{Vector{UInt8}}()
    # 1 Catalog, 2 Pages — заглушки, заполним при сохранении
    push!(objs, UInt8[])   # 1
    push!(objs, UInt8[])   # 2
    d = NsbPdf(objs, Vector{Vector{UInt8}}(), Int[], 0, 0,
               NSB_FONT_REG, NSB_FONT_BOLD, Dict{String,Int}(), 0.0)
    d.font_reg = nsb_pdf_add_font!(d, NSB_FONT_REG_BYTES, NSB_FONT_REG, "F1")
    d.font_bold = nsb_pdf_add_font!(d, NSB_FONT_BOLD_BYTES, NSB_FONT_BOLD, "F2")
    nsb_pdf_newpage!(d)
    return d
end

_pdf_add_obj!(d::NsbPdf, body::Vector{UInt8}) = (push!(d.objs, body); length(d.objs))

"Встроить Type0-шрифт: FontFile2 + CIDFontType2 + ToUnicode."
function nsb_pdf_add_font!(d::NsbPdf, ttfbytes::Vector{UInt8}, f::NsbFont, name::String)
    ng = f.num_glyphs
    # W array: ширины всех глифов (В ЕДИНИЦАХ 1/1000 em — как требует PDF!)
    wio = IOBuffer()
    write(wio, "[")
    for g in 0:ng-1
        adv1000 = round(Int, nsb_advance(f, g) * 1000 / f.units_per_em)
        write(wio, "$g[$adv1000]")
    end
    write(wio, "]")
    warr = String(take!(wio))
    # FontFile2
    ff_data = nsb_zlib_compress(ttfbytes)
    ff_head = "<<" * "/Filter /FlateDecode" * "/Length $(length(ff_data))" *
              "/Length1 $(length(ttfbytes))" * ">>\nstream\n"
    ff_obj = _pdf_add_obj!(d, vcat(Vector{UInt8}(codeunits(ff_head)), ff_data,
                                  Vector{UInt8}(codeunits("\nendstream"))))
    asc = round(Int, f.ascender * 1000 / f.units_per_em)
    dsc = round(Int, f.descender * 1000 / f.units_per_em)
    cap = round(Int, 0.72 * f.units_per_em * 1000 / f.units_per_em)
    bbox = "-8 -$(1000 + dsc) $(1000 + asc) $asc"
    fd = _pdf_add_obj!(d, Vector{UInt8}(codeunits(
        "<< /Type /FontDescriptor /FontName /DejaVuSans /Flags 32" *
        " /FontBBox [$bbox] /ItalicAngle 0 /Ascent $asc /Descent $dsc" *
        " /CapHeight $cap /StemV 80 /FontFile2 $ff_obj 0 R >>")))
    # ToUnicode
    tuio = IOBuffer()
    write(tuio, "/CIDInit /ProcSet findresource begin\n12 dict begin\nbegincmap\n")
    entries = collect(f.cmap)
    write(tuio, "/CMapName /Custom-$(name) def\n/CMapType 2 def\n")
    for chunk_start in 1:100:length(entries)
        chunk = entries[chunk_start:min(end, chunk_start + 99)]
        write(tuio, "$(length(chunk)) beginbfchar\n")
        for (cp, gid) in chunk
            write(tuio, @sprintf("<%04X> <%04X>\n", gid, cp))
        end
        write(tuio, "endbfchar\n")
    end
    write(tuio, "endcmap\nCMapName currentdict /CMap defineresource pop\nend end\n")
    tu_data = nsb_zlib_compress(take!(tuio))
    tu_obj = _pdf_add_obj!(d, vcat(
        Vector{UInt8}(codeunits("<< /Filter /FlateDecode /Length $(length(tu_data)) >>\nstream\n")),
        tu_data, Vector{UInt8}(codeunits("\nendstream"))))
    cidfont = _pdf_add_obj!(d, Vector{UInt8}(codeunits(
        "<< /Type /Font /Subtype /CIDFontType2 /BaseFont /DejaVuSans" *
        " /CIDSystemInfo << /Registry (Adobe) /Ordering (Identity) /Supplement 0 >>" *
        " /FontDescriptor $fd 0 R /CIDToGIDMap /Identity /DW 600 /W $warr >>")))
    type0 = _pdf_add_obj!(d, Vector{UInt8}(codeunits(
        "<< /Type /Font /Subtype /Type0 /BaseFont /DejaVuSans" *
        " /Encoding /Identity-H /DescendantFonts [$cidfont 0 R] /ToUnicode $tu_obj 0 R >>")))
    return type0
end

# --------------------------------------------------------------- примитивы
function nsb_pdf_newpage!(d::NsbPdf)
    push!(d.page_ops, Vector{UInt8}())
    d.cury = NSB_PDF_H - NSB_PDF_MARGIN
    return nothing
end

_pdf_ops(d::NsbPdf) = d.page_ops[end]
append_op!(d::NsbPdf, s::AbstractString) =
    (append!(d.page_ops[end], Vector{UInt8}(codeunits(s * "\n"))); nothing)

function nsb_pdf_ensure!(d::NsbPdf, h::Float64)
    if d.cury - h < NSB_PDF_MARGIN + 30
        nsb_pdf_newpage!(d)
    end
    return nothing
end

"Ширина строки в pt при размере size."
function nsb_pdf_width(d::NsbPdf, fnt::Int, s::AbstractString, size::Real)
    f = fnt == d.font_bold ? d.fnt_bold_metrics : d.fnt_reg_metrics
    return nsb_text_width(f, s, size)
end

"Текст в точке (x, y_baseline)."
function nsb_pdf_text!(d::NsbPdf, x::Float64, y::Float64, s::AbstractString,
                       size::Real; fnt::Union{Nothing,Int} = nothing,
                       color::Tuple{Float64,Float64,Float64} = (0.10, 0.13, 0.22))
    f = fnt === nothing ? d.font_reg : fnt
    metrics = f == d.font_bold ? d.fnt_bold_metrics : d.fnt_reg_metrics
    hex = IOBuffer()
    for ch in String(s)
        gid = nsb_gid(metrics, Int(ch))
        write(hex, @sprintf("%04X", gid))
    end
    append_op!(d, @sprintf("%.3f %.3f %.3f rg BT /F%d %.2f Tf 1 0 0 1 %.2f %.2f Tm <%s> Tj ET",
                           color[1], color[2], color[3],
                           f == d.font_bold ? 2 : 1, Float64(size), x, y,
                           String(take!(hex))))
    return nothing
end

"Перенос слов по ширине; возвращает строки."
function nsb_pdf_wrap(d::NsbPdf, s::AbstractString, size::Real, maxw::Real;
                      fnt::Union{Nothing,Int} = nothing)
    f = fnt === nothing ? d.font_reg : fnt
    words = split(String(s), (' ',); keepempty = false)
    lines = String[]
    cur = ""
    for w in words
        trial = isempty(cur) ? String(w) : cur * " " * String(w)
        if nsb_pdf_width(d, f, trial, size) <= maxw
            cur = trial
        else
            isempty(cur) || push!(lines, cur)
            # сверхдлинное слово — режем
            if nsb_pdf_width(d, f, String(w), size) > maxw
                part = ""
                for ch in String(w)
                    if nsb_pdf_width(d, f, part * string(ch), size) > maxw
                        push!(lines, part)
                        part = string(ch)
                    else
                        part *= string(ch)
                    end
                end
                cur = part
            else
                cur = String(w)
            end
        end
    end
    isempty(cur) || push!(lines, cur)
    return lines
end

# --------------------------------------------------------------- блоки
const NSB_PDF_TEAL = (0.055, 0.455, 0.565)
const NSB_PDF_INK = (0.10, 0.13, 0.22)
const NSB_PDF_MUT = (0.36, 0.42, 0.52)

function nsb_pdf_heading!(d::NsbPdf, text::AbstractString; level::Int = 1)
    size = level == 1 ? 15.0 : (level == 2 ? 12.5 : 11.0)
    nsb_pdf_ensure!(d, size * 2.4)
    d.cury -= size * 1.3
    nsb_pdf_text!(d, NSB_PDF_MARGIN, d.cury, text, size; fnt = d.font_bold,
                  color = level == 1 ? NSB_PDF_TEAL : NSB_PDF_INK)
    if level == 1
        d.cury -= 5
        append_op!(d, @sprintf("%.3f %.3f %.3f RG 0.8 w %.2f %.2f m %.2f %.2f l S",
                               NSB_PDF_TEAL..., NSB_PDF_MARGIN, d.cury,
                               NSB_PDF_W - NSB_PDF_MARGIN, d.cury))
    end
    d.cury -= size * 0.9
    return nothing
end

function nsb_pdf_para!(d::NsbPdf, text::AbstractString; size::Real = 9.8,
                       bold::Bool = false, color = NSB_PDF_INK, lead::Real = 1.42)
    f = bold ? d.font_bold : d.font_reg
    lines = nsb_pdf_wrap(d, text, size, NSB_PDF_W - 2 * NSB_PDF_MARGIN; fnt = f)
    for ln in lines
        nsb_pdf_ensure!(d, size * lead)
        d.cury -= size * lead
        nsb_pdf_text!(d, NSB_PDF_MARGIN, d.cury, ln, size; fnt = f, color = color)
    end
    d.cury -= size * 0.45
    return nothing
end

function nsb_pdf_bullets!(d::NsbPdf, items::Vector{String}; size::Real = 9.6)
    for it in items
        lines = nsb_pdf_wrap(d, it, size, NSB_PDF_W - 2 * NSB_PDF_MARGIN - 14)
        for (i, ln) in enumerate(lines)
            nsb_pdf_ensure!(d, size * 1.45)
            d.cury -= size * 1.45
            if i == 1
                nsb_pdf_text!(d, NSB_PDF_MARGIN + 2, d.cury, "•", size;
                              color = NSB_PDF_TEAL)
            end
            nsb_pdf_text!(d, NSB_PDF_MARGIN + 14, d.cury, ln, size)
        end
    end
    d.cury -= 4
    return nothing
end

"Таблица с авто-шириной колонок (или заданной долей)."
function nsb_pdf_table!(d::NsbPdf, headers::Vector{String},
                        rows::Vector{Vector{String}};
                        size::Real = 8.6, fracs::Union{Nothing,Vector{Float64}} = nothing)
    ncols = length(headers)
    avail = NSB_PDF_W - 2 * NSB_PDF_MARGIN
    fr = fracs === nothing ? fill(1.0 / ncols, ncols) : fracs
    widths = [avail * fr[i] for i in 1:ncols]
    rh = size * 1.62
    function draw_row(cells, bold::Bool, header::Bool)
        f = bold ? d.font_bold : d.font_reg
        # высота строки по числу перенесённых строк
        nlines = 1
        cell_lines = Vector{Vector{String}}()
        for (i, c) in enumerate(cells)
            ls = nsb_pdf_wrap(d, c, size, widths[i] - 6; fnt = f)
            push!(cell_lines, ls)
            nlines = max(nlines, length(ls))
        end
        hh = rh * nlines
        nsb_pdf_ensure!(d, hh + 4)
        if header
            y0 = d.cury - hh
            append_op!(d, @sprintf("%.3f %.3f %.3f rg %.2f %.2f %.2f %.2f re f",
                                   0.90, 0.95, 0.97, NSB_PDF_MARGIN, y0, avail, hh))
        end
        y0 = d.cury - hh
        color = header ? NSB_PDF_TEAL : NSB_PDF_INK
        for (i, c) in enumerate(cell_lines)
            yy = d.cury - rh * 0.78
            for ln in c
                nsb_pdf_text!(d, NSB_PDF_MARGIN + 3 + sum(widths[1:i-1]), yy, ln,
                              size; fnt = f, color = color)
                yy -= rh
            end
        end
        d.cury = y0 - 1.2
        # сетка
        append_op!(d, @sprintf("0.82 0.86 0.91 RG 0.4 w %.2f %.2f m %.2f %.2f l S",
                               NSB_PDF_MARGIN, y0, NSB_PDF_W - NSB_PDF_MARGIN, y0))
    end
    draw_row(headers, true, true)
    for r in rows
        draw_row(r, false, false)
    end
    d.cury -= 6
    return nothing
end

function nsb_pdf_hrule!(d::NsbPdf)
    nsb_pdf_ensure!(d, 12)
    d.cury -= 7
    append_op!(d, @sprintf("0.8 0.85 0.9 RG 0.5 w %.2f %.2f m %.2f %.2f l S",
                           NSB_PDF_MARGIN, d.cury, NSB_PDF_W - NSB_PDF_MARGIN, d.cury))
    d.cury -= 8
    return nothing
end

# --------------------------------------------------------------- векторные графики
"Векторный линейный график NsbPlot в прямоугольник (x, y, w, h) на странице."
function nsb_pdf_draw_plot!(d::NsbPdf, x::Float64, y::Float64, w::Float64, h::Float64,
                            p::NsbPlot)
    pad_l, pad_r, pad_t, pad_b = 46.0, 10.0, (isempty(p.title) ? 8.0 : 22.0), 34.0
    ax_x, ax_y = x + pad_l, y + pad_b
    ax_w, ax_h = w - pad_l - pad_r, h - pad_t - pad_b
    allx = Float64[]; ally = Float64[]
    for s in p.series; append!(allx, s.xs); append!(ally, s.ys); end
    isempty(allx) && return nothing
    xmin, xmax = extrema(allx); ymin, ymax = extrema(ally)
    xmin == xmax && (xmax += 1)
    if p.logy
        ally_f = filter(>(0.0), ally)
        isempty(ally_f) && return nothing
        ymin = 10.0^floor(log10(minimum(ally_f)))
        ymax = 10.0^ceil(log10(max(maximum(ally_f), ymin * 10)))
    else
        ymin -= 0.06 * (ymax - ymin) + 1e-15
        ymax += 0.06 * (ymax - ymin) + 1e-15
    end
    topx(v) = ax_x + (v - xmin) / (xmax - xmin) * ax_w
    topy(v) = p.logy ?
        ax_y + ax_h - (log10(max(v, 1e-300)) - log10(ymin)) / (log10(ymax) - log10(ymin)) * ax_h :
        ax_y + ax_h - (v - ymin) / (ymax - ymin) * ax_h
    # сетка
    stx = nsb_nice_step(xmax - xmin, 6)
    sty = p.logy ? 1.0 : nsb_nice_step(ymax - ymin, 5)
    for t in xmin:stx:xmax
        X = topx(t)
        append_op!(d, @sprintf("0.90 0.92 0.96 RG 0.4 w %.2f %.2f m %.2f %.2f l S", X, ax_y, X, ax_y + ax_h))
    end
    if p.logy
        for e in floor(Int, log10(ymin)):ceil(Int, log10(ymax))
            Y = topy(10.0^e)
            (ax_y - 1 <= Y <= ax_y + ax_h + 1) && append_op!(d,
                @sprintf("0.90 0.92 0.96 RG 0.4 w %.2f %.2f m %.2f %.2f l S", ax_x, Y, ax_x + ax_w, Y))
        end
    else
        for t in ymin:sty:ymax
            Y = topy(t)
            (ax_y - 1 <= Y <= ax_y + ax_h + 1) && append_op!(d,
                @sprintf("0.90 0.92 0.96 RG 0.4 w %.2f %.2f m %.2f %.2f l S", ax_x, Y, ax_x + ax_w, Y))
        end
    end
    # рамка
    append_op!(d, @sprintf("0.45 0.50 0.60 RG 0.8 w %.2f %.2f %.2f %.2f re S", ax_x, ax_y, ax_w, ax_h))
    fs = 7.4
    # тики
    for t in xmin:stx:xmax
        X = topx(t)
        nsb_pdf_text!(d, X - nsb_pdf_width(d, d.font_reg, nsb_fmt_tick(t, stx), fs) / 2,
                      ax_y - 11, nsb_fmt_tick(t, stx), fs; color = NSB_PDF_MUT)
    end
    if p.logy
        for e in floor(Int, log10(ymin)):ceil(Int, log10(ymax))
            Y = topy(10.0^e)
            (ax_y <= Y <= ax_y + ax_h) && nsb_pdf_text!(d, ax_x - 6 - nsb_pdf_width(d, d.font_reg, "1e$e", fs),
                                                        Y - 2.5, "1e$e", fs; color = NSB_PDF_MUT)
        end
    else
        for t in ymin:sty:ymax
            Y = topy(t)
            (ax_y <= Y <= ax_y + ax_h) && nsb_pdf_text!(d, ax_x - 6 - nsb_pdf_width(d, d.font_reg, nsb_fmt_tick(t, sty), fs),
                                                        Y - 2.5, nsb_fmt_tick(t, sty), fs; color = NSB_PDF_MUT)
        end
    end
    # серии
    for s in p.series
        n = length(s.xs)
        n < 2 && continue
        col = @sprintf("%.3f %.3f %.3f RG %.2f w", s.color[1] / 255, s.color[2] / 255,
                       s.color[3] / 255, s.lw * 0.8)
        append_op!(d, col)
        s.dashed && append_op!(d, "[3 2.4] 0 d")
        path = ""
        started = false
        for i in 1:n
            isfinite(s.ys[i]) || continue
            path *= @sprintf("%.2f %.2f %s ", topx(s.xs[i]), topy(s.ys[i]),
                             started ? "l" : "m")
            started = true
        end
        append_op!(d, path * "S")
        append_op!(d, "[] 0 d")
    end
    # легенда
    items = [s for s in p.series if !isempty(s.label)]
    if !isempty(items)
        lx = ax_x + ax_w - 118; ly = ax_y + ax_h - 14 * length(items) - 6
        for (i, s) in enumerate(items)
            yy = ly + (length(items) - i) * 14
            append_op!(d, @sprintf("%.3f %.3f %.3f RG 1.4 w %.2f %.2f m %.2f %.2f l S",
                                   s.color[1] / 255, s.color[2] / 255, s.color[3] / 255,
                                   lx, yy, lx + 16, yy))
            nsb_pdf_text!(d, lx + 20, yy - 2.6, s.label, fs; color = NSB_PDF_INK)
        end
    end
    # заголовок и подписи
    if !isempty(p.title)
        nsb_pdf_text!(d, x + w / 2 - nsb_pdf_width(d, d.font_bold, p.title, 10) / 2,
                      y + h - 12, p.title, 10; fnt = d.font_bold, color = NSB_PDF_INK)
    end
    if !isempty(p.xlabel)
        nsb_pdf_text!(d, ax_x + ax_w / 2 - nsb_pdf_width(d, d.font_reg, p.xlabel, fs + 0.6) / 2,
                      y + 8, p.xlabel, fs + 0.6; color = NSB_PDF_MUT)
    end
    if !isempty(p.ylabel)
        nsb_pdf_text!(d, x + 4, ax_y + ax_h / 2 - 4, p.ylabel, fs; color = NSB_PDF_MUT)
    end
    return nothing
end

"Векторный график с подписью, с гарантированным местом."
function nsb_pdf_figure!(d::NsbPdf, p::NsbPlot; w::Float64 = NSB_PDF_W - 2 * NSB_PDF_MARGIN,
                         h::Float64 = 190.0, caption::AbstractString = "")
    nsb_pdf_ensure!(d, h + (isempty(caption) ? 8 : 18))
    d.cury -= h + 6
    nsb_pdf_draw_plot!(d, NSB_PDF_MARGIN, d.cury, w, h, p)
    if !isempty(caption)
        d.cury -= 12
        nsb_pdf_text!(d, NSB_PDF_W / 2 - nsb_pdf_width(d, d.font_reg, caption, 8) / 2,
                      d.cury, caption, 8; color = NSB_PDF_MUT)
    end
    d.cury -= 12
    return nothing
end

"Растровая тепловая карта: XObject из канваса."
function nsb_pdf_heat_image!(d::NsbPdf, c::NsbCanvas, name::String)::String
    if haskey(d.images, name)
        return name
    end
    data = nsb_zlib_compress(c.px)
    head = "<<" * "/Type /XObject /Subtype /Image /Width $(c.w) /Height $(c.h)" *
           "/ColorSpace /DeviceRGB /BitsPerComponent 8 /Filter /FlateDecode" *
           "/Length $(length(data)) >>\nstream\n"
    obj = _pdf_add_obj!(d, vcat(Vector{UInt8}(codeunits(head)), data,
                                Vector{UInt8}(codeunits("\nendstream"))))
    d.images[name] = obj
    return name
end

function nsb_pdf_figure_heat!(d::NsbPdf, q::NsbHeat;
                              w::Float64 = NSB_PDF_W - 2 * NSB_PDF_MARGIN - 90,
                              h::Float64 = 240.0,
                              caption::AbstractString = "")
    nsb_pdf_ensure!(d, h + 30)
    # отрисовка тепловой карты во временный канвас низкого разрешения (страница ~ 3x)
    cw = 640; ch = round(Int, 640 * h / w)
    c = NsbCanvas(cw, ch)
    nsb_draw_heat!(c, (0, 0, cw, ch), q)
    name = nsb_pdf_heat_image!(d, c, "im" * string(length(d.images) + 1))
    x = NSB_PDF_MARGIN + 36
    y = d.cury - h
    append_op!(d, @sprintf("q %.2f 0 0 %.2f %.2f %.2f cm /%s Do Q", w, h, x, y, name))
    d.cury = y - 6
    if !isempty(caption)
        nsb_pdf_text!(d, NSB_PDF_W / 2 - nsb_pdf_width(d, d.font_reg, caption, 8) / 2,
                      d.cury, caption, 8; color = NSB_PDF_MUT)
        d.cury -= 12
    end
    return nothing
end

# --------------------------------------------------------------- сохранение
function nsb_pdf_save(d::NsbPdf, path::AbstractString)
    npages = length(d.page_ops)
    # 1 Catalog
    d.objs[1] = Vector{UInt8}(codeunits("<< /Type /Catalog /Pages 2 0 R >>"))
    # страницы и содержимое
    page_objs = Int[]
    content_objs = Int[]
    footer_txt = "NSB Julia Lab v" * NSB_LAB_VERSION
    for i in 1:npages
        ftr_hex = prod(@sprintf("%04X", nsb_gid(d.fnt_reg_metrics, Int(c)))
                       for c in footer_txt)
        footer = @sprintf("0.45 0.50 0.60 rg BT /F1 8 Tf 1 0 0 1 %.1f %.1f Tm <%s> Tj ET",
                          NSB_PDF_MARGIN, 30.0, ftr_hex)
        digits_hex = prod(@sprintf("%04X", nsb_gid(d.fnt_reg_metrics, Int(c)))
                          for c in "$(i) / $npages")
        pn = @sprintf("0.45 0.50 0.60 rg BT /F1 8 Tf 1 0 0 1 %.1f %.1f Tm <%s> Tj ET",
                      NSB_PDF_W - NSB_PDF_MARGIN - 60, 30.0, digits_hex)
        ops = vcat(d.page_ops[i], Vector{UInt8}(codeunits(footer * "\n" * pn * "\n")))
        zops = nsb_zlib_compress(ops)
        cobj = _pdf_add_obj!(d, vcat(
            Vector{UInt8}(codeunits("<< /Filter /FlateDecode /Length $(length(zops)) >>\nstream\n")),
            zops, Vector{UInt8}(codeunits("\nendstream"))))
        img_names = collect(keys(d.images))
        xobjs = isempty(d.images) ? "" :
            "/XObject << " * join(("/$(nm) $(d.images[nm]) 0 R" for nm in img_names), " ") * " >>"
        fonts = "/Font << /F1 $(d.font_reg) 0 R /F2 $(d.font_bold) 0 R >>"
        pobj = _pdf_add_obj!(d, Vector{UInt8}(codeunits(
            "<< /Type /Page /Parent 2 0 R /MediaBox [0 0 $(NSB_PDF_W) $(NSB_PDF_H)]" *
            " /Resources << $fonts $xobjs /ProcSet [/PDF /Text /ImageC] >>" *
            " /Contents $cobj 0 R >>")))
        push!(page_objs, pobj)
        push!(content_objs, cobj)
    end
    d.page_objs = page_objs
    kids = join(["$(page_objs[i]) 0 R" for i in 1:npages], " ")
    d.objs[2] = Vector{UInt8}(codeunits(
        "<< /Type /Pages /Kids [$kids] /Count $npages >>"))
    # сериализация с xref
    io = IOBuffer()
    write(io, "%PDF-1.4\n%\xE2\xE3\xCF\xD3\n")
    offsets = Int[]
    for (i, body) in enumerate(d.objs)
        push!(offsets, position(io))
        write(io, "$i 0 obj\n")
        write(io, body)
        write(io, "\nendobj\n")
    end
    xref_pos = position(io)
    n_objs = length(d.objs)
    write(io, "xref\n0 $(n_objs + 1)\n0000000000 65535 f \n")
    for off in offsets
        write(io, @sprintf("%010d 00000 n \n", off))
    end
    write(io, "trailer\n<< /Size $(n_objs + 1) /Root 1 0 R >>\nstartxref\n$xref_pos\n%%EOF\n")
    open(path, "w") do f
        write(f, take!(io))
    end
    return path
end
