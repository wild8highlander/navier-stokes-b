# 03_deflate_png.jl — собственный DEFLATE (fixed Huffman + LZ77), CRC32/Adler32,
# PNG-писатель (600 dpi по умолчанию), колормапы viridis/coolwarm, zlib-обёртка для PDF.

# --------------------------------------------------------------- CRC32
const NSB_CRC_TABLE = let t = Vector{UInt32}(undef, 256)
    for n in 0:255
        c = UInt32(n)
        for _ in 1:8
            c = (c & 1 == 1) ? (0xEDB88320 ⊻ (c >> 1)) : (c >> 1)
        end
        t[n+1] = c
    end
    t
end

function nsb_crc32(data::AbstractVector{UInt8})::UInt32
    c = 0xFFFFFFFF
    for b in data
        c = NSB_CRC_TABLE[((c ⊻ UInt32(b)) & 0xFF) + 1] ⊻ (c >> 8)
    end
    return c ⊻ 0xFFFFFFFF
end

function nsb_adler32(data::AbstractVector{UInt8})::UInt32
    a = UInt32(1); b = UInt32(0)
    for x in data
        a = (a + UInt32(x)) % 65521
        b = (b + a) % 65521
    end
    return (b << 16) | a
end

# --------------------------------------------------------------- bit writer
mutable struct NsbBitW
    buf::Vector{UInt8}
    cur::UInt8
    nbits::Int
end
NsbBitW() = NsbBitW(Vector{UInt8}(undef, 0), 0x00, 0)

function _bw_bit!(w::NsbBitW, b::Bool)
    (b ? (w.cur |= (0x01 << w.nbits)) : nothing)
    w.nbits += 1
    if w.nbits == 8
        push!(w.buf, w.cur)
        w.cur = 0x00
        w.nbits = 0
    end
    return nothing
end

"Пишем биты value (LSB первого)."
function bw_bits!(w::NsbBitW, value::Int, n::Int)
    for i in 0:n-1
        _bw_bit!(w, (value >> i) & 1 == 1)
    end
    return nothing
end

"Код Хаффмана пишется старшими битами вперёд (RFC 1951)."
function bw_huff!(w::NsbBitW, code::Int, n::Int)
    for i in n-1:-1:0
        _bw_bit!(w, (code >> i) & 1 == 1)
    end
    return nothing
end

function bw_flush!(w::NsbBitW)
    w.nbits > 0 && push!(w.buf, w.cur)
    w.cur = 0x00
    w.nbits = 0
    return nothing
end

# --------------------------------------------------------------- фиксированный Хаффман
"Код литерала/длины (0..285): (код, длина)."
function nsb_fixed_lit_code(sym::Int)::Tuple{Int,Int}
    if sym < 144
        return (0x30 + sym, 8)
    elseif sym < 256
        return (0x190 + (sym - 144), 9)
    elseif sym < 280
        return (sym - 256, 7)
    else
        return (0xC0 + (sym - 280), 8)
    end
end

const NSB_LEN_BASE = [3,4,5,6,7,8,9,10,11,13,15,17,19,23,27,31,35,43,51,59,67,83,99,115,131,163,195,227,258]
const NSB_LEN_EXTRA = [0,0,0,0,0,0,0,0,1,1,1,1,2,2,2,2,3,3,3,3,4,4,4,4,5,5,5,5,0]
const NSB_DIST_BASE = [1,2,3,4,5,7,9,13,17,25,33,49,65,97,129,193,257,385,513,769,1025,1537,2049,3073,4097,6145,8193,12289,16385,24577]
const NSB_DIST_EXTRA = [0,0,0,0,1,1,2,2,3,3,4,4,5,5,6,6,7,7,8,8,9,9,10,10,11,11,12,12,13,13]

function nsb_len_code(m::Int)::Tuple{Int,Int,Int}   # (code, extra_bits, extra_val)
    m = clamp(m, 3, 258)
    for c in length(NSB_LEN_BASE):-1:1
        if m >= NSB_LEN_BASE[c]
            return (c + 256, NSB_LEN_EXTRA[c], m - NSB_LEN_BASE[c])
        end
    end
    return (257, 0, 0)
end

function nsb_dist_code(d::Int)::Tuple{Int,Int,Int}
    for c in length(NSB_DIST_BASE):-1:1
        if d >= NSB_DIST_BASE[c]
            return (c - 1, NSB_DIST_EXTRA[c], d - NSB_DIST_BASE[c])
        end
    end
    return (0, 0, 0)
end

# --------------------------------------------------------------- LZ77
const NSB_HBITS = 15
const NSB_HSIZE = 1 << NSB_HBITS

"Сырой DEFLATE (fixed Huffman + LZ77, min match 4)."
function nsb_deflate(data::Vector{UInt8})::Vector{UInt8}
    n = length(data)
    n == 0 && return UInt8[0x03, 0x00]  # пустой fixed-блок
    w = NsbBitW()
    bw_bits!(w, 1, 1)   # BFINAL
    bw_bits!(w, 1, 2)   # BTYPE=01 fixed
    head = fill(0, NSB_HSIZE)      # 1-based: последняя позиция с данным хешем
    prev = fill(0, n)              # цепочка
    hashof(i) = ((Int(data[i]) << 10 ⊻ (Int(data[i+1]) << 5) ⊻ Int(data[i+2])) &
                 (NSB_HSIZE - 1)) + 1
    function emit_literal(b::Int)
        c, l = nsb_fixed_lit_code(b)
        bw_huff!(w, c, l)
    end
    function emit_match(len::Int, dist::Int)
        c, eb, ev = nsb_len_code(len)
        hc, hl = nsb_fixed_lit_code(c)
        bw_huff!(w, hc, hl)
        eb > 0 && bw_bits!(w, ev, eb)
        dc, db, dv = nsb_dist_code(dist)
        bw_huff!(w, dc, 5)
        db > 0 && bw_bits!(w, dv, db)
    end
    i = 1
    while i <= n
        best_len = 0
        best_dist = 0
        if i + 3 <= n
            h = hashof(i)
            cand = head[h]
            chain = 0
            while cand > 0 && i - cand < 32768 && chain < 64
                l = 0
                maxlen = min(258, n - i + 1)
                while l < maxlen && data[cand + l] == data[i + l]
                    l += 1
                end
                if l >= 4 && l > best_len
                    best_len = l
                    best_dist = i - cand
                    l >= 258 && break
                end
                cand = prev[cand]
                chain += 1
            end
            # вставляем позицию в цепочку
            prev[i] = head[h]
            head[h] = i
        end
        if best_len >= 4
            emit_match(best_len, best_dist)
            # вставляем промежуточные позиции хешей
            for k in (i+1):(i+best_len-1)
                if k + 3 <= n
                    h = hashof(k)
                    prev[k] = head[h]
                    head[h] = k
                end
            end
            i += best_len
        else
            emit_literal(Int(data[i]))
            i += 1
        end
    end
    c, l = nsb_fixed_lit_code(256)   # end of block
    bw_huff!(w, c, l)
    bw_flush!(w)
    out = w.buf
    # хвост: BFINAL-блок типа 00 (пустой) не нужен; сравниваем с stored-вариантом
    stored = nsb_deflate_stored(data)
    return length(out) <= length(stored) ? out : stored
end

"DEFLATE stored-блоками (без сжатия) — надёжный fallback."
function nsb_deflate_stored(data::Vector{UInt8})::Vector{UInt8}
    out = IOBuffer()
    n = length(data)
    pos = 1
    while pos <= n
        chunk = min(65535, n - pos + 1)
        last = (pos + chunk - 1 >= n) ? 1 : 0
        write(out, UInt8(last))
        write(out, UInt8(chunk & 0xFF))
        write(out, UInt8((chunk >> 8) & 0xFF))
        write(out, data[pos:pos+chunk-1])
        pos += chunk
    end
    if n == 0
        write(out, UInt8(1)); write(out, UInt8(0)); write(out, UInt8(0))
    end
    return take!(out)
end

"zlib-обёртка (для PDF FlateDecode): 0x78 0x01 + deflate + adler32."
function nsb_zlib_compress(data::Vector{UInt8})::Vector{UInt8}
    d = nsb_deflate(data)
    out = Vector{UInt8}(undef, 2 + length(d) + 4)
    out[1] = 0x78; out[2] = 0x01
    out[3:2+length(d)] = d
    ad = nsb_adler32(data)
    off = 2 + length(d)
    out[off+1] = UInt8((ad >> 24) & 0xFF)
    out[off+2] = UInt8((ad >> 16) & 0xFF)
    out[off+3] = UInt8((ad >> 8) & 0xFF)
    out[off+4] = UInt8(ad & 0xFF)
    return out
end

# --------------------------------------------------------------- PNG
"RGB-канвас: 0 = (0,0,0); координаты [x, y], y сверху."
mutable struct NsbCanvas
    w::Int
    h::Int
    px::Vector{UInt8}   # RGB, row-major: (y*w + x)*3
end
NsbCanvas(w::Int, h::Int; fill::NTuple{3,Int} = (255, 255, 255)) =
    NsbCanvas(w, h, begin
        v = Vector{UInt8}(undef, 3 * w * h)
        for i in 1:3:length(v)
            v[i] = UInt8(fill[1]); v[i+1] = UInt8(fill[2]); v[i+2] = UInt8(fill[3])
        end
        v
    end)

@inline function nsb_setpx!(c::NsbCanvas, x::Int, y::Int, col::NTuple{3,Int})
    (1 <= x <= c.w && 1 <= y <= c.h) || return nothing
    o = 3 * ((y - 1) * c.w + (x - 1)) + 1
    c.px[o] = UInt8(clamp(col[1], 0, 255))
    c.px[o+1] = UInt8(clamp(col[2], 0, 255))
    c.px[o+2] = UInt8(clamp(col[3], 0, 255))
    return nothing
end

@inline nsb_getpx(c::NsbCanvas, x::Int, y::Int) =
    (Int(c.px[3 * ((y - 1) * c.w + (x - 1)) + 1]),
     Int(c.px[3 * ((y - 1) * c.w + (x - 1)) + 2]),
     Int(c.px[3 * ((y - 1) * c.w + (x - 1)) + 3]))

"Смешивание цвета в пиксель с альфой a∈[0,1]."
function nsb_blend!(c::NsbCanvas, x::Int, y::Int, col::NTuple{3,Int}, a::Real)
    (1 <= x <= c.w && 1 <= y <= c.h) || return nothing
    r0, g0, b0 = nsb_getpx(c, x, y)
    nsb_setpx!(c, x, y, (round(Int, r0 + (col[1] - r0) * a),
                         round(Int, g0 + (col[2] - g0) * a),
                         round(Int, b0 + (col[3] - b0) * a)))
    return nothing
end

"Сглаженная линия (У-Сяолинь)."
function nsb_line!(c::NsbCanvas, x0::Real, y0::Real, x1::Real, y1::Real,
                   col::NTuple{3,Int}; lw::Real = 1.5)
    x0 = Float64(x0); y0 = Float64(y0); x1 = Float64(x1); y1 = Float64(y1)
    lw = Float64(lw)
    steep = abs(y1 - y0) > abs(x1 - x0)
    if steep
        x0, y0, x1, y1 = y0, x0, y1, x1
    end
    if x0 > x1
        x0, x1 = x1, x0
        y0, y1 = y1, y0
    end
    dx = x1 - x0
    dy = y1 - y0
    grad = dx == 0 ? 1.0 : dy / dx
    xend = floor(x0 + 0.5)
    yend = y0 + grad * (xend - x0)
    xgap = 0.5 + (x0 + 0.5 - xend)
    px = Int(floor(xend)); py = Int(floor(yend))
    f = lw >= 1.5 ? 1.0 : lw
    steep ? nsb_blend!(c, py, px, col, (1 - (yend - floor(yend))) * xgap * f) :
            nsb_blend!(c, px, py, col, (1 - (yend - floor(yend))) * xgap * f)
    steep ? nsb_blend!(c, py + 1, px, col, (yend - floor(yend)) * xgap * f) :
            nsb_blend!(c, px, py + 1, col, (yend - floor(yend)) * xgap * f)
    for xi in (Int(xend) + 1):(Int(floor(x1 + 0.5)) - 1)
        yf = y0 + grad * (xi - x0)
        xf = xi + 0.5
        yi = Int(floor(yf))
        steep ? (nsb_blend!(c, yi, xi, col, (1 - (yf - yi)) * f);
                 nsb_blend!(c, yi + 1, xi, col, (yf - yi) * f)) :
                (nsb_blend!(c, xi, yi, col, (1 - (yf - yi)) * f);
                 nsb_blend!(c, xi, yi + 1, col, (yf - yi) * f))
    end
    return nothing
end

"Заливка прямоугольника."
function nsb_rect!(c::NsbCanvas, x::Int, y::Int, w::Int, h::Int, col::NTuple{3,Int};
                   outline::Union{Nothing,NTuple{3,Int}} = nothing)
    for yy in y:min(y + h - 1, c.h), xx in x:min(x + w - 1, c.w)
        nsb_setpx!(c, xx, yy, col)
    end
    if outline !== nothing
        for xx in x:min(x + w - 1, c.w)
            nsb_setpx!(c, xx, y, outline)
            nsb_setpx!(c, xx, y + h - 1, outline)
        end
        for yy in y:min(y + h - 1, c.h)
            nsb_setpx!(c, x, yy, outline)
            nsb_setpx!(c, x + w - 1, yy, outline)
        end
    end
    return nothing
end

# --------------------------------------------------------------- колормапы
function _lerp_table(tbl::Vector{NTuple{3,Int}}, t::Float64)::NTuple{3,Int}
    t = clamp(t, 0.0, 1.0) * (length(tbl) - 1)
    i = min(floor(Int, t) + 1, length(tbl) - 1)
    f = t - (i - 1)
    a, b = tbl[i], tbl[i + 1]
    return (round(Int, a[1] + (b[1] - a[1]) * f),
            round(Int, a[2] + (b[2] - a[2]) * f),
            round(Int, a[3] + (b[3] - a[3]) * f))
end

const NSB_VIRIDIS_INT = [(Int(r), Int(g), Int(b)) for (r, g, b) in NSB_VIRIDIS_RGB]

nsb_viridis(t::Real) = _lerp_table(NSB_VIRIDIS_INT, Float64(t))
nsb_viridis(v::Real, vmin::Real, vmax::Real) =
    nsb_viridis(vmax > vmin ? (v - vmin) / (vmax - vmin) : 0.5)

const NSB_COOLWARM = NTuple{3,Int}[
    (40, 60, 180), (70, 120, 235), (125, 175, 250), (190, 215, 245),
    (235, 235, 235), (250, 205, 165), (245, 150, 110), (230, 90, 70), (180, 20, 30)]
nsb_coolwarm(t::Real) = _lerp_table(NSB_COOLWARM, Float64(t))
"Знаковое поле → coolwarm с симметричным диапазоном."
nsb_coolwarm_signed(v::Real, m::Real) =
    nsb_coolwarm(clamp(v / (m == 0 ? 1.0 : m), -1.0, 1.0) / 2 + 0.5)

# --------------------------------------------------------------- PNG writer
function nsb_png_chunk(out::IOBuffer, tag::Vector{UInt8}, payload::Vector{UInt8})
    len = UInt32(length(payload))
    write(out, UInt8((len >> 24) & 0xFF), UInt8((len >> 16) & 0xFF),
          UInt8((len >> 8) & 0xFF), UInt8(len & 0xFF))
    body = vcat(tag, payload)
    write(out, body)
    crc = nsb_crc32(body)
    write(out, UInt8((crc >> 24) & 0xFF), UInt8((crc >> 16) & 0xFF),
          UInt8((crc >> 8) & 0xFF), UInt8(crc & 0xFF))
    return nothing
end

"Канвас → PNG-файл."
function nsb_canvas_save_png(c::NsbCanvas, path::AbstractString)
    out = IOBuffer()
    write(out, UInt8.([137, 80, 78, 71, 13, 10, 26, 10]))
    ihdr = Vector{UInt8}(undef, 13)
    w32 = UInt32(c.w); h32 = UInt32(c.h)
    ihdr[1] = UInt8((w32 >> 24) & 0xFF); ihdr[2] = UInt8((w32 >> 16) & 0xFF)
    ihdr[3] = UInt8((w32 >> 8) & 0xFF); ihdr[4] = UInt8(w32 & 0xFF)
    ihdr[5] = UInt8((h32 >> 24) & 0xFF); ihdr[6] = UInt8((h32 >> 16) & 0xFF)
    ihdr[7] = UInt8((h32 >> 8) & 0xFF); ihdr[8] = UInt8(h32 & 0xFF)
    ihdr[9] = 0x08   # bit depth
    ihdr[10] = 0x02  # color type RGB
    ihdr[11] = 0x00; ihdr[12] = 0x00; ihdr[13] = 0x00
    nsb_png_chunk(out, UInt8.(collect("IHDR")), ihdr)
    # сканлайны с фильтром 0
    raw = Vector{UInt8}(undef, (c.w * 3 + 1) * c.h)
    rowlen = c.w * 3
    for y in 1:c.h
        base_out = (y - 1) * (rowlen + 1)
        raw[base_out + 1] = 0x00
        copyto!(raw, base_out + 2, c.px, (y - 1) * rowlen + 1, rowlen)
    end
    nsb_png_chunk(out, UInt8.(collect("IDAT")), nsb_zlib_compress(raw))
    nsb_png_chunk(out, UInt8.(collect("IEND")), UInt8[])
    open(path, "w") do io
        write(io, take!(out))
    end
    return path
end
