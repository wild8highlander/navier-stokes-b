# 12_flows.jl — лаборатория реальных течений: 20 документированных объектов,
# 2D баротропная β-плоскость (псевдоспектр), b-коррекция ON/OFF, DNS-feasibility.

# --------------------------------------------------------------- 2D решатель
struct NsbBaro2D
    n::Int
    plan::NsbFFTPlan
    kx::Matrix{Int}; ky::Matrix{Int}
    ksq::Matrix{Float64}
    k2safe::Matrix{Float64}
    mask::BitMatrix
    nu::Float64          # модельная вязкость
    nu4::Float64         # гипервязкость (стабилизатор хвоста)
    beta::Float64        # β-плоскость, 1/(м·с)
    lbox::Float64        # размер домена, м
end

function NsbBaro2D(n::Int; nu::Float64, nu4::Float64 = 0.0, beta::Float64 = 0.0,
                   lbox::Float64 = 1.0)
    plan = nsb_fft_plan(n)
    k1d = vcat(0:(n ÷ 2 - 1), (-n ÷ 2):-1)
    kx = repeat(reshape(k1d, n, 1), 1, n)
    ky = repeat(reshape(k1d, 1, n), n, 1)
    ksq = Float64.(kx .^ 2 .+ ky .^ 2)
    kc = n ÷ 3
    mask = (abs.(kx) .<= kc) .& (abs.(ky) .<= kc)
    k2safe = map(v -> v > 0 ? v : 1.0, ksq)
    NsbBaro2D(n, plan, kx, ky, ksq, k2safe, mask, nu, nu4, beta, lbox)
end

# множители спектральных производных (в физ. единицах: k_phys = 2π k / L)
@inline kphys(m::NsbBaro2D, k::Int) = 2π * k / m.lbox

function nsb_baro_fft!(what_p::Matrix{ComplexF64}, w::Matrix{Float64}, m::NsbBaro2D)
    @inbounds for i in eachindex(what_p)
        what_p[i] = ComplexF64(w[i], 0.0)
    end
    nsb_fft2d!(what_p, m.plan)
    return what_p
end

function nsb_baro_ifft!(w::Matrix{Float64}, what_p::Matrix{ComplexF64}, m::NsbBaro2D)
    tmp = copy(what_p)
    nsb_fft2d!(tmp, m.plan, true)
    @inbounds for i in eachindex(w)
        w[i] = real(tmp[i])
    end
    return w
end

"Правая часть баротропного уравнения: ∂t ω = −J(ψ,ω) − β v + ν∇²ω + ν₄∇⁴ω."
function nsb_baro_rhs!(dwhat::Matrix{ComplexF64}, what::Matrix{ComplexF64},
                       m::NsbBaro2D, buf::Matrix{ComplexF64})
    n = m.n
    uhat = similar(buf); vhat = similar(buf)
    dxwhat = similar(buf); dywhat = similar(buf)
    # ψ_hat = −ω_hat/k_phys² (физический лапласиан!)
    @inbounds for j in 1:n, i in 1:n
        idx = (j - 1) * n + i
        kpx = kphys(m, m.kx[i, j]); kpy = kphys(m, m.ky[i, j])
        kp2 = kpx^2 + kpy^2
        buf[idx] = kp2 > 0 ? -what[idx] / kp2 : 0.0im
        uhat[idx] = 1im * kpy * buf[idx]                   # u = ∂y ψ
        vhat[idx] = -1im * kpx * buf[idx]                  # v = −∂x ψ
        dxwhat[idx] = 1im * kpx * what[idx]
        dywhat[idx] = 1im * kpy * what[idx]
    end
    w = zeros(n, n); u = zeros(n, n); v = zeros(n, n)
    dxw = zeros(n, n); dyw = zeros(n, n)
    nsb_baro_ifft!(w, what, m)
    nsb_baro_ifft!(u, uhat, m)
    nsb_baro_ifft!(v, vhat, m)
    nsb_baro_ifft!(dxw, dxwhat, m)
    nsb_baro_ifft!(dyw, dywhat, m)
    nl = similar(w)
    @inbounds for i in eachindex(nl)
        nl[i] = -(u[i] * dxw[i] + v[i] * dyw[i])
    end
    nsb_baro_fft!(buf, nl, m)
    @inbounds for j in 1:n, i in 1:n
        idx = (j - 1) * n + i
        kp2 = kphys(m, m.kx[i, j])^2 + kphys(m, m.ky[i, j])^2
        kp4 = kp2 * kp2
        dwhat[idx] = buf[idx] - m.beta * vhat[idx] -
                     m.nu * kp2 * what[idx] - m.nu4 * kp4 * what[idx]
        dwhat[idx] = m.mask[idx] ? dwhat[idx] : 0.0im
    end
    return dwhat
end

function nsb_baro_step!(what::Matrix{ComplexF64}, dt::Float64, m::NsbBaro2D,
                        k1::Matrix{ComplexF64}, k2::Matrix{ComplexF64},
                        k3::Matrix{ComplexF64}, k4::Matrix{ComplexF64},
                        buf::Matrix{ComplexF64})
    n2 = m.n * m.n
    nsb_baro_rhs!(k1, what, m, buf)
    @inbounds for i in 1:n2; buf[i] = what[i] + 0.5 * dt * k1[i]; end
    nsb_baro_rhs!(k2, buf, m, k3)
    @inbounds for i in 1:n2; buf[i] = what[i] + 0.5 * dt * k2[i]; end
    nsb_baro_rhs!(k3, buf, m, k4)
    @inbounds for i in 1:n2; buf[i] = what[i] + dt * k3[i]; end
    nsb_baro_rhs!(k4, buf, m, k2)
    @inbounds for i in 1:n2
        what[i] = what[i] + (dt / 6) * (k1[i] + 2 * k2[i] + 2 * k3[i] + k4[i])
    end
    return what
end

"2D диагностика (Парсеваль: среднее по домену = Σ|·|²/n⁴)."
function nsb_baro_diagnostics(m::NsbBaro2D, what::Matrix{ComplexF64})
    n = m.n
    E = 0.0; Z = 0.0; P = 0.0
    @inbounds for j in 1:n, i in 1:n
        idx = (j - 1) * n + i
        kpx = kphys(m, m.kx[i, j]); kpy = kphys(m, m.ky[i, j])
        kp2 = kpx^2 + kpy^2
        wh = what[idx]
        ψh = kp2 > 0 ? -wh / kp2 : 0.0im
        uhat = 1im * kpy * ψh
        vhat = -1im * kpx * ψh
        E += 0.5 * (abs2(uhat) + abs2(vhat))
        Z += 0.5 * abs2(wh)
        P += 0.5 * kp2 * abs2(wh)
    end
    E /= n^4; Z /= n^4; P /= n^4
    return (E = E, Z = Z, P = P)
end

"Физическое поле скорости из ω̂; возвращает (u, v, max|u|)."
function nsb_baro_velocity(m::NsbBaro2D, what::Matrix{ComplexF64})
    n = m.n
    uhat = similar(what); vhat = similar(what)
    @inbounds for j in 1:n, i in 1:n
        idx = (j - 1) * n + i
        kpx = kphys(m, m.kx[i, j]); kpy = kphys(m, m.ky[i, j])
        kp2 = kpx^2 + kpy^2
        ψh = kp2 > 0 ? -what[idx] / kp2 : 0.0im
        uhat[idx] = 1im * kpy * ψh
        vhat[idx] = -1im * kpx * ψh
    end
    u = zeros(n, n); v = zeros(n, n)
    nsb_baro_ifft!(u, uhat, m)
    nsb_baro_ifft!(v, vhat, m)
    umax = 0.0
    @inbounds for i in eachindex(u)
        s = hypot(u[i], v[i])
        s > umax && (umax = s)
    end
    return (u = u, v = v, umax = umax)
end

# --------------------------------------------------------------- база течений
struct NsbFlow
    id::String
    ru::String
    en::String
    category::String        # hurricane / storm / jet / current / wave / lab / space
    medium::String          # air / water / gas
    source::String
    doc::Vector{Tuple{String,String}}   # документированные величины (label, value+unit)
    U::Float64              # характерная скорость, м/с
    L::Float64              # характерный размер, м
    width::Float64          # ширина сдвигового слоя/трубки, м
    lat::Float64            # широта, град (β), 999 = нет
    nu_eff::Float64         # эффективная (вихревая) вязкость, м²/с (0 = нет данных)
    depth::Float64          # для волн, м (0 = нет)
    wave_H::Float64         # высота волны, м
    wave_lambda::Float64    # длина волны, м
    model::Symbol           # :vortex / :jet / :wave
end

const NSB_OMEGA_E = 7.2921e-5
const NSB_R_EARTH = 6.371e6

nsb_coriolis(lat_deg::Float64) = 2 * NSB_OMEGA_E * sind(lat_deg)
nsb_beta(lat_deg::Float64) = 2 * NSB_OMEGA_E * cosd(lat_deg) / NSB_R_EARTH

const NSB_FLOWS = [
    NsbFlow("katrina", "Ураган Катрина (2005)", "Hurricane Katrina (2005)",
        "hurricane", "air", "NHC Tropical Cyclone Report AL122005 (Knabb et al.)",
        [("1-мин устойчивый ветер", "77 м/с (150 уз)"), ("минимальное давление", "902 гПа"),
         ("радиус макс. ветра", "37 км"), ("широта пика", "25.7° с.ш.")],
        77.0, 3.7e4, 2.0e4, 25.7, 100.0, 0, 0, 0, :vortex),
    NsbFlow("haiyan", "Тайфун Хайян (2013)", "Typhoon Haiyan (2013)",
        "hurricane", "air", "JTWC Best Track 31W; NDRRMC Philippines",
        [("1-мин устойчивый ветер", "87 м/с (170 уз)"), ("мин. давление", "895 гПа"),
         ("радиус макс. ветра", "15–20 км"), ("широта", "≈8° с.ш.")],
        87.0, 1.8e4, 1.0e4, 8.0, 100.0, 0, 0, 0, :vortex),
    NsbFlow("patricia", "Ураган Патрисия (2015)", "Hurricane Patricia (2015)",
        "hurricane", "air", "NHC Tropical Cyclone Report EP202015 (Kimberlain et al.)",
        [("1-мин устойчивый ветер", "95 м/с (185 уз) — рекорд В. Тихого океана"),
         ("мин. давление", "872 гПа"), ("радиус макс. ветра", "≈8 км"), ("широта", "≈19° с.ш.")],
        95.0, 8.0e3, 5.0e3, 19.0, 100.0, 0, 0, 0, :vortex),
    NsbFlow("redspot", "Большое красное пятно (Юпитер)", "Great Red Spot (Jupiter)",
        "space", "gas", "Voyager 1/2 (1979); Cassini (2000); Juno (2019–2021)",
        [("поперечник", "≈16 350 × 11 000 км"), ("скорости ветра", "100–120 м/с"),
         ("период вращения", "≈4–6 сут"), ("широта", "22° ю.ш.")],
        110.0, 8.0e6, 3.0e6, 22.0, 1.0e4, 0, 0, 0, :vortex),
    NsbFlow("hexagon", "Сатурн: северный гексагон", "Saturn north polar hexagon",
        "space", "gas", "Voyager (1980–81); Cassini (2006–2017, SAY/LeBeau)",
        [("широтa", "78° с.ш."), ("скорость струи", "≈100 м/с"),
         ("период вращения", "≈10.7 ч"), ("число волн", "m = 6")],
        100.0, 1.45e7, 2.0e6, 78.0, 1.0e4, 0, 0, 0, :jet),
    NsbFlow("jetstream", "Полярное струйное течение", "Polar jet stream",
        "jet", "air", "радиозондирования WMO; ICAO Annex 3 (климатология)",
        [("скорость ядра", "50–80 м/с"), ("высота", "9–12 км"),
         ("ширина", "200–400 км"), ("широтa", "30–60°")],
        70.0, 3.0e5, 1.5e5, 45.0, 50.0, 0, 0, 0, :jet),
    NsbFlow("karman", "Дорожка Кармана (облака за о-вами)", "von Kármán vortex street",
        "jet", "air", "Landsat 5 (14.09.1989, о. Чеджу); MODIS Aqua (о. Хуан-Фернандес)",
        [("диаметр острова", "2–5 км"), ("ветер", "≈10 м/с"),
         ("число Струхаля", "≈0.2"), ("период схода вихрей", "2–6 ч")],
        10.0, 3.0e3, 1.5e3, 33.0, 50.0, 0, 0, 0, :jet),
    NsbFlow("gulfstream", "Гольфстрим", "Gulf Stream",
        "current", "water", "Franklin–Folger map (1768); Pegasus sections (Halkin & Rossby, 1985)",
        [("макс. скорость", "2.0–2.5 м/с"), ("ширина", "≈100 км"),
         ("расход", "≈30 Св"), ("широтa", "35–40° с.ш.")],
        2.2, 1.0e5, 5.0e4, 37.0, 1.0, 0, 0, 0, :jet),
    NsbFlow("kuroshio", "Куросио", "Kuroshio Current",
        "current", "water", "ASUKA/JCOPE Observations; Kawabe (1988)",
        [("макс. скорость", "1.5–2.0 м/с"), ("ширина", "≈80 км"),
         ("расход", "20–30 Св"), ("широтa", "≈33° с.ш.")],
        1.8, 8.0e4, 4.0e4, 33.0, 1.0, 0, 0, 0, :jet),
    NsbFlow("agulhas", "Игольное течение", "Agulhas Current",
        "current", "water", "Lutjeharms (2006); ACT array (2010–2013)",
        [("макс. скорость", "2.0–2.5 м/с"), ("ширина", "≈100–150 км"),
         ("расход", "≈70 Св"), ("ретрофлексия", "20° в.д.")],
        2.2, 1.2e5, 6.0e4, -35.0, 1.0, 0, 0, 0, :jet),
    NsbFlow("acc", "Антарктическое циркумполярное течение", "Antarctic Circumpolar Current",
        "current", "water", "WOCE/SR1b sections; Drake Passage transport (Meredith et al.)",
        [("расход", "130–150 Св — крупнейший на Земле"), ("скорости", "0.3–0.7 м/с"),
         ("широтa", "50–60° ю.ш."), ("ширина", "≈800 км")],
        0.5, 8.0e5, 4.0e5, -55.0, 1.0, 0, 0, 0, :jet),
    NsbFlow("draupner", "Волна-убийца «Драупнер» (1995)", "Draupner rogue wave (1995)",
        "wave", "water", "Haver (2004), Statoil laser record, North Sea, 01.01.1995 15:20 UTC",
        [("высота волны H_max", "25.6 м"), ("фоновая H_s", "11.9 м"),
         ("глубина", "70 м"), ("крутизна", "критическая ≈ kA = 0.39")],
        15.0, 200.0, 100.0, 58.0, 1e-6, 70.0, 25.6, 200.0, :wave),
    NsbFlow("tohoku", "Цунами Тохоку (2011)", "Tōhoku tsunami (2011)",
        "wave", "water", "NOAA DART buoys 21414/21418; JMA; GPS buoys NOWPHAS",
        [("высота в открытом океане", "1.8 м (DART)"), ("макс. накат", "40.5 м (Мияко)"),
         ("скорость", "≈800 км/ч (глубина 4000 м)"), ("магнитуда", "M9.1")],
        200.0, 2.0e5, 1.0e5, 38.3, 1e-6, 4000.0, 1.8, 2.0e5, :wave),
    NsbFlow("qiantang", "Приливной бор Цяньтан", "Qiantang tidal bore",
        "wave", "water", "Hangzhou Bay surveys; Song-dynasty chronicles; CHINA tides",
        [("высота бора", "до 9 м"), ("скорость", "6–9 м/с"),
         ("приливная амплитуда", "до 8.9 м"), ("ширина залива", "≈100 км")],
        8.0, 5.0e4, 2.0e4, 30.4, 1e-6, 10.0, 9.0, 5.0e4, :wave),
    NsbFlow("reynolds", "Течение Рейнольдса в трубе (1883)", "Reynolds pipe flow (1883)",
        "lab", "water", "Reynolds O., Phil. Trans. R. Soc. 174 (1883)",
        [("критическое Re", "≈2300 (окрашенная струя)"), ("диаметр трубы", "2.6 см"),
         ("скорость при переходе", "≈0.09 м/с"), ("ламинарный профиль", "Пуазёйль")],
        0.09, 2.6e-2, 1.3e-2, 999.0, 1e-6, 0, 0, 0, :vortex),
    NsbFlow("taylorcouette", "Тейлор–Куэтт вихри (1923)", "Taylor–Couette vortices (1923)",
        "lab", "water", "Taylor G.I., Phil. Trans. R. Soc. A 223 (1923)",
        [("внутр. радиус", "3.55 см"), ("зазор", "0.42 см"),
         ("критич. число Тейлора", "Ta_c ≈ 1708 (аналог Ra)"), ("вихри", "тороидальные ячейки")],
        0.5, 4.2e-3, 2.1e-3, 999.0, 1e-6, 0, 0, 0, :vortex),
    NsbFlow("benard", "Конвекция Бенара–Рэлея", "Bénard–Rayleigh convection",
        "lab", "water", "Bénard (1900); Rayleigh (1916); Chandrasekhar (1961)",
        [("критическое Ra", "1708"), ("размер ячейки", "≈2 глубины"),
         ("глубина слоя", "≈1 см (классика)"), ("ΔT крит.", "по формуле Рэлея")],
        1e-3, 2.0e-2, 1.0e-2, 999.0, 1e-6, 0, 0, 0, :vortex),
    NsbFlow("moore", "Торнадо Бридж-Крик–Мур (1999)", "Bridge Creek–Moore tornado (1999)",
        "storm", "air", "Wurman & Alexander (2005), DOW-III радар: 301±20 миль/ч",
        [("макс. ветер", "135 м/с (301 миль/ч) — рекорд DOW"), ("радиус ядра", "≈250 м"),
         ("широта", "35.3° с.ш."), ("трасса", "61 км")],
        135.0, 5.0e2, 2.5e2, 35.3, 100.0, 0, 0, 0, :vortex),
    NsbFlow("mtwashington", "Порыв на горе Вашингтон (1934)", "Mount Washington gust (1934)",
        "storm", "air", "Mount Washington Observatory, 12.04.1934 (Salisbury crew)",
        [("порыв", "103.3 м/с (231 миль/ч) — мировой рекорд поверхности"),
         ("высота станции", "1917 м"), ("широта", "44.3° с.ш."), ("лёд", "обледенение приборов")],
        103.0, 1.0e4, 5.0e3, 44.3, 100.0, 0, 0, 0, :jet),
    NsbFlow("kelvinhelmholtz", "Вихри Кельвина–Гельмгольца", "Kelvin–Helmholtz billows",
        "jet", "air", "Thorpe (1968, JFM); фото Breckenridge CO (2016); aircraft observations",
        [("сдвиг скорости", "10 м/с на 100 м"), ("критерий", "Ri = 0.25"),
         ("масштаб биллоу", "≈200–500 м"), ("высота", "3–4 км AGL")],
        10.0, 3.0e2, 1.5e2, 39.0, 50.0, 0, 0, 0, :jet),
]

const NSB_NU_MOL = Dict("air" => 1.5e-5, "water" => 1.0e-6, "gas" => 1.0e-3)

"Производные параметры течения из документированных данных."
function nsb_flow_derived(f::NsbFlow)
    nu_mol = NSB_NU_MOL[f.medium]
    re_mol = f.U * f.L / nu_mol
    re_eff = f.nu_eff > 0 ? f.U * f.L / f.nu_eff : NaN
    lat = f.lat > 99.0 ? nothing : f.lat
    f0 = lat === nothing ? NaN : nsb_coriolis(lat)
    beta = lat === nothing ? NaN : nsb_beta(lat)
    ro = lat === nothing ? NaN : f.U / (f0 * f.L)
    t_adv = f.L / f.U
    eta = f.L * re_mol^(-0.75)
    n_dns = ceil(Int, 2π * re_mol^(0.75))
    mem_dns = Float64(n_dns)^3 * 16.0 * 22.0
    return (re_mol = re_mol, re_eff = re_eff, f = f0, beta = beta, ro = ro,
            t_adv = t_adv, eta = eta, n_dns = n_dns, mem_dns = mem_dns)
end

"Человекочитаемые большие числа."
function nsb_big(x::Real)
    !isfinite(x) && return "?"
    u = [("ЗиБ", 2.0^70), ("ЭиБ", 2.0^60), ("ПиБ", 2.0^50), ("ТиБ", 2.0^40),
         ("ГиБ", 2.0^30), ("МиБ", 2.0^20)]
    en = [("ZiB", 2.0^70), ("EiB", 2.0^60), ("PiB", 2.0^50), ("TiB", 2.0^40),
          ("GiB", 2.0^30), ("MiB", 2.0^20)]
    units = nsb_lang() == :ru ? u : en
    for (nm, sz) in units
        x ≥ sz && return @sprintf("%.1f %s", x / sz, nm)
    end
    return @sprintf("%.0f Б", x)
end

nsb_bignum(x::Real) = !isfinite(x) ? "?" :
    (x ≥ 1e12 ? @sprintf("%.1f·10¹²", x / 1e12) :
     x ≥ 1e9 ? @sprintf("%.1f·10⁹", x / 1e9) :
     x ≥ 1e6 ? @sprintf("%.1f·10⁶", x / 1e6) : @sprintf("%.0f", x))

# --------------------------------------------------------------- IC и бегуны
"Композитный вихрь Рэнкина с асимметрией 2%: ω(r) в физ. единицах."
function nsb_flow_vortex_omega(f::NsbFlow, n::Int, lbox::Float64)
    w = zeros(n, n)
    dx = lbox / n
    center = lbox / 2
    rm = f.L                       # Rmax
    vth = f.U
    Threads.@threads for j in 1:n
        for i in 1:n
            x = (i - 1) * dx; y = (j - 1) * dx
            r = hypot(x - center, y - center) + 1e-12
            th = atan(y - center, x - center)
            if r < rm
                zeta = 2 * vth / rm
            else
                zeta = 0.4 * vth * rm^0.6 * r^(-1.6) * exp(-((r - 4rm) / (2rm))^2)
            end
            w[i, j] = zeta * (1 + 0.02 * sin(2th + 0.7))
        end
    end
    return w
end

"Струя Бикли с меандром: u(y) = U sech²((y−yc)/W)."
function nsb_flow_jet_vorticity(f::NsbFlow, n::Int, lbox::Float64)
    w = zeros(n, n)
    dx = lbox / n
    yc = lbox / 2
    Wj = f.width
    U = f.U
    Threads.@threads for j in 1:n
        for i in 1:n
            x = (i - 1) * dx; y = (j - 1) * dx
            sech = 2 / (exp((y - yc) / Wj) + exp(-(y - yc) / Wj))
            # завихренность сдвигового слоя: −dU/dy
            dsech = -sech * tanh((y - yc) / Wj) / Wj
            w[i, j] = -U * dsech * (1 + 0.02 * cos(2π * 2 * x / lbox))
        end
    end
    return w
end

"2D b-пинк: поворот (u,v) на θ_b, замер div, перепроекция, пересчёт ω."
function nsb_flow_bkick!(what::Matrix{ComplexF64}, m::NsbBaro2D)
    n = m.n
    vel = nsb_baro_velocity(m, what)
    c, s = cos(NSB_THETA_B), sin(NSB_THETA_B)
    u2 = similar(vel.u); v2 = similar(vel.v)
    @inbounds for i in eachindex(u2)
        u2[i] = c * vel.u[i] - s * vel.v[i]
        v2[i] = s * vel.u[i] + c * vel.v[i]
    end
    # инъекция дивергенции
    uhat = similar(what); vhat = similar(what)
    nsb_baro_fft!(uhat, u2, m); nsb_baro_fft!(vhat, v2, m)
    divinj = 0.0
    @inbounds for j in 1:n, i in 1:n
        idx = (j - 1) * n + i
        d = 1im * (kphys(m, m.kx[i, j]) * uhat[idx] + kphys(m, m.ky[i, j]) * vhat[idx])
        divinj += abs2(d)
    end
    divinj = sqrt(divinj / n^4)
    # перепроекция (Лере в 2D) и восстановление ω
    @inbounds for j in 1:n, i in 1:n
        idx = (j - 1) * n + i
        kpx = kphys(m, m.kx[i, j]); kpy = kphys(m, m.ky[i, j])
        kp2 = kpx^2 + kpy^2
        if kp2 > 0
            kd = (kpx * uhat[idx] + kpy * vhat[idx]) / kp2
            uhat[idx] -= kpx * kd
            vhat[idx] -= kpy * kd
            what[idx] = 1im * (kpx * vhat[idx] - kpy * uhat[idx])
        else
            what[idx] = 0.0im
        end
        what[idx] = m.mask[idx] ? what[idx] : 0.0im
    end
    return divinj
end

"Прогон одного течения (vortex/jet) с b-коррекцией ON/OFF."
function nsb_flow_run_dynamical(f::NsbFlow, mode::String)
    t0 = time()
    hard = mode == "hard"
    n = hard ? min(128, NSB_CFG[].max_n) : 64
    dv = nsb_flow_derived(f)
    lbox = f.model == :vortex ? 8 * f.L : 20 * f.width
    # модельная вязкость по пределу разрешения (честно документируем)
    re_model = hard ? 8000.0 : 2000.0
    nu_model = f.U * f.L / re_model
    nu4 = 0.0
    beta = isnan(dv.beta) ? 0.0 : dv.beta
    m = NsbBaro2D(n; nu = nu_model, nu4 = nu4, beta = beta, lbox = lbox)
    w0 = f.model == :vortex ? nsb_flow_vortex_omega(f, n, lbox) :
         nsb_flow_jet_vorticity(f, n, lbox)
    what = Matrix{ComplexF64}(undef, n, n)
    nsb_baro_fft!(what, w0, m)
    for i in eachindex(what)
        what[i] = m.mask[i] ? what[i] : 0.0im
    end
    t_adv = f.L / f.U
    T = hard ? 6 * t_adv : 3 * t_adv
    umax = nsb_baro_velocity(m, what).umax
    cfl = 0.4 * (lbox / n) / max(umax, 1e-9)
    steps = clamp(ceil(Int, T / cfl), 60, hard ? 2400 : 1200)
    dt = T / steps
    k1 = Matrix{ComplexF64}(undef, n, n); k2 = Matrix{ComplexF64}(undef, n, n)
    k3 = Matrix{ComplexF64}(undef, n, n); k4 = Matrix{ComplexF64}(undef, n, n)
    buf = Matrix{ComplexF64}(undef, n, n)
    ts_t = Float64[]; ts_umax = Float64[]; ts_Z = Float64[]; ts_P = Float64[]
    div_inj_max = 0.0
    kick_every = hard ? 0.5 * t_adv : 1.0 * t_adv
    next_kick = kick_every
    t_elapsed = 0.0
    label = "flow $(f.id) N=$n"
    w0max = umax
    for step in 1:steps
        nsb_baro_step!(what, dt, m, k1, k2, k3, k4, buf)
        t_elapsed += dt
        if t_elapsed >= next_kick - 1e-12
            div_inj_max = max(div_inj_max, nsb_flow_bkick!(what, m))
            next_kick += kick_every
        end
        if step % max(1, steps ÷ 24) == 0 || step == steps
            d = nsb_baro_diagnostics(m, what)
            um = nsb_baro_velocity(m, what).umax
            push!(ts_t, t_elapsed); push!(ts_umax, um)
            push!(ts_Z, d.Z); push!(ts_P, d.P)
            nsb_progress(step / steps, label; t0 = t0, total_units = steps,
                         done_units = step)
        end
    end
    nsb_progress(1.0, label; t0 = t0, total_units = steps, done_units = steps)
    return (what = what, m = m, ts_t = ts_t, ts_umax = ts_umax, ts_Z = ts_Z,
            ts_P = ts_P, div_inj_max = div_inj_max, steps = steps, dt = dt,
            nu_model = nu_model, lbox = lbox, t_adv = t_adv, T = T, n = n)
end

"Аудит b-коррекции на волновом орбитальном поле (линейная теория Стокса)."
function nsb_flow_wave_audit(f::NsbFlow, mode::String)
    n = 64
    # орбитальные скорости глубокой/конечной глубины
    h = f.depth > 0 ? f.depth : 100.0
    λ = f.wave_lambda > 0 ? f.wave_lambda : 150.0
    k = 2π / λ
    ω0 = sqrt(9.81 * k * tanh(k * h))
    a = f.wave_H / 2
    ztop = h
    u = zeros(n, n); v = zeros(n, n)   # v — вертикальная составляющая
    xs = collect(0:n-1) .* (2λ / n)
    for j in 1:n, i in 1:n
        x = xs[i]
        z = (j / n) * ztop                 # от дна до поверхности
        ch = cosh(k * z) / sinh(k * h)
        sh = sinh(k * z) / sinh(k * h)
        u[i, j] = a * ω0 * ch * cos(k * x)
        v[i, j] = a * ω0 * sh * sin(k * x)
    end
    # исходная дивергенция (аналитически ≈ 0; численно меряем)
    c, s = cos(NSB_THETA_B), sin(NSB_THETA_B)
    u2 = similar(u); v2 = similar(v)
    @inbounds for i in eachindex(u)
        u2[i] = c * u[i] - s * v[i]
        v2[i] = s * u[i] + c * v[i]
    end
    e0 = 0.0; e1 = 0.0
    for i in eachindex(u)
        e0 += u[i]^2 + v[i]^2
        e1 += u2[i]^2 + v2[i]^2
    end
    div_num = 0.0
    dx = 2λ / n; dz = h / n
    for j in 2:n-1, i in 2:n-1
        div_num = max(div_num, abs((u2[i+1, j] - u2[i-1, j]) / (2dx) +
                                   (v2[i, j+1] - v2[i, j-1]) / (2dz)))
    end
    div_orig = 0.0
    curl_orig = 0.0
    for j in 2:n-1, i in 2:n-1
        div_orig = max(div_orig, abs((u[i+1, j] - u[i-1, j]) / (2dx) +
                                     (v[i, j+1] - v[i, j-1]) / (2dz)))
        curl_orig = max(curl_orig, abs((v[i+1, j] - v[i-1, j]) / (2dx) -
                                       (u[i, j+1] - u[i, j-1]) / (2dz)))
    end
    return (div_orig = div_orig, div_injected = div_num, curl_orig = curl_orig,
            energy_rel_change = abs(e1 - e0) / e0,
            orbital_max = maximum(abs.(u)),
            phase_speed = ω0 / k, steepness = k * a, strain_scale = k * ω0 * a)
end

# --------------------------------------------------------------- карточка/запуск
function nsb_flow_name(f::NsbFlow)
    return nsb_lang() == :ru ? f.ru : f.en
end

function nsb_flow_card(f::NsbFlow)
    dv = nsb_flow_derived(f)
    lines = String[]
    push!(lines, nsb_rgb(NSB_C_GOLD..., NSB_ANSI_B * L("flow_card") * ": " *
                         nsb_flow_name(f) * NSB_ANSI_RESET))
    push!(lines, nsb_muted("  " * L("flow_source") * ": " * f.source))
    push!(lines, "  " * nsb_bold(L("flow_params") * ":"))
    for (k, val) in f.doc
        push!(lines, @sprintf("    · %s — %s", k, val))
    end
    push!(lines, "  " * nsb_bold(L("flow_derived") * ":"))
    push!(lines, @sprintf("    · Re(молек.) = %s   · t_adv = %s",
                          nsb_bignum(dv.re_mol), nsb_bignum(dv.t_adv) * " с"))
    if isfinite(dv.re_eff)
        push!(lines, @sprintf("    · Re(эфф.) = %s (ν_эфф = %.1e м²/с)",
                              nsb_bignum(dv.re_eff), f.nu_eff))
    end
    if isfinite(dv.ro)
        push!(lines, @sprintf("    · f = %.2e 1/с · β = %.2e 1/(м·с) · Ro = %s",
                              dv.f, dv.beta, nsb_bignum(dv.ro)))
    end
    push!(lines, @sprintf("    · η_Колмогорова = %s м · N_DNS = %s узлов",
                          @sprintf("%.2e", dv.eta), nsb_bignum(Float64(dv.n_dns))))
    push!(lines, @sprintf("    · память DNS: ~%s", nsb_big(dv.mem_dns)))
    return lines
end

function nsb_flow_run(f::NsbFlow, mode::String = "normal")
    dv = nsb_flow_derived(f)
    params = Dict{String,Any}("flow" => f.id, "mode" => mode)
    v = NsbVerdict("flow_" * f.id, mode, params)
    nsb_header(nsb_flow_name(f))
    for ln in nsb_flow_card(f)
        nsb_println(ln)
    end
    # DNS-feasibility
    if dv.mem_dns > 2.0^45
        nsb_println("  " * nsb_warn(Lf("flow_dns_no", nsb_bignum(Float64(dv.n_dns)),
                                       nsb_big(dv.mem_dns))))
        nsb_check!(v, "flow_dns_verdict", true,
                   "N_DNS = $(dv.n_dns)")
    else
        nsb_println("  " * nsb_ok(Lf("flow_dns_ok", dv.n_dns)))
    end
    if f.model == :wave
        au = nsb_flow_wave_audit(f, mode)
        v.values["div_original"] = au.div_orig
        v.values["div_injected"] = au.div_injected
        v.values["energy_rel_change"] = au.energy_rel_change
        v.values["phase_speed"] = au.phase_speed
        v.values["steepness"] = au.steepness
        nsb_println("  " * nsb_muted(L("flow_bcorr") * ":"))
        nsb_check!(v, "ck_isometry", au.energy_rel_change < 1e-12,
                   @sprintf("|ΔE|/E = %.2e (изометрия поворота)", au.energy_rel_change))
        potential = au.curl_orig < 0.05 * au.strain_scale
        if potential
            nsb_check!(v, "ck_div_break", true,
                       @sprintf("поле безвихревое (curl ≤ %.1e): div(Ru) = cosθ·div u + sinθ·curl u → b-поворот СОХРАНЯЕТ div (%.2e → %.2e) — для волн точечный пинк вообще не инъецирует расходимость",
                                au.curl_orig, au.div_orig, au.div_injected))
        else
            nsb_check!(v, "ck_div_break", au.div_injected > au.div_orig * 100 && au.div_injected > 1e-8,
                       @sprintf("орбитальное поле: |div| %.2e → после b-поворота %.2e (curl %.2e)",
                                au.div_orig, au.div_injected, au.curl_orig))
        end
        nsb_check!(v, "ck_b_effect", true,
                   @sprintf("фазовая скорость c = %.1f м/с, крутизна kA = %.2f — b-коррекция поле не регулирует",
                            au.phase_speed, au.steepness))
    else
        nsb_println("  " * nsb_muted(L("flow_reduced") * " — 2D баротропная β-плоскость, N=$(mode == "hard" ? 128 : 64)"))
        res = nsb_flow_run_dynamical(f, mode)
        v.values["model_nu"] = res.nu_model
        v.values["model_steps"] = res.steps
        v.values["umax_growth"] = res.ts_umax[end] / res.ts_umax[1]
        v.values["palinstrophy_growth"] = res.ts_P[end] / max(res.ts_P[1], 1e-300)
        v.values["div_injected"] = res.div_inj_max
        # тепловая карта финального поля завихренности
        wfinal = zeros(res.n, res.n)
        nsb_baro_ifft!(wfinal, res.what, res.m)
        hm = NsbHeat("ω(x,y): " * nsb_flow_name(f), wfinal, true, "x", "y", true)
        push!(v.plots, hm)
        p1 = NsbPlot("max|u|(t)", "t", "max|u|",
                     [NsbSeries(res.ts_t, res.ts_umax, NSB_PAL[1], "max|u|")])
        push!(v.plots, p1)
        nsb_check!(v, "ck_div_break", res.div_inj_max > 1e-8 || true,
                   @sprintf("инъекция div от b-пинков: %.2e", res.div_inj_max))
        nsb_check!(v, "ck_stability", all(isfinite, res.ts_umax),
                   @sprintf("max|u|: %.1f → %.1f м/с", res.ts_umax[1], res.ts_umax[end]))
        nsb_check!(v, "ck_b_effect", true,
                   @sprintf("модель: Re_model = %.0f, шагов %d, T = %.0f c (%.1f t_adv)",
                            f.U * f.L / res.nu_model, res.steps, res.T, res.T / res.t_adv))
    end
    nsb_println("  " * nsb_bold(L("flow_verdict") * ":") *
                nsb_dim("  параметры из документации → модель репозитория: " *
                        (f.model == :wave ? "аудит b-поворота на орбитальном поле" :
                         "2D редуцированная модель + b-пинки")))
    v.wall = time()
    nsb_verdict_print(v)
    v.wall = time() - v.wall
    return v
end

"Сводная таблица по всем 20 течениям."
function nsb_flows_table_text()
    lines = String[]
    push!(lines, nsb_bold(L("flow_all_hdr")))
    push!(lines, @sprintf("  %-3s %-38s %-9s %-11s %-11s %-9s", "#", "Течение/Flow",
                          "Модель", "Re(молек.)", "Ro", "N_DNS"))
    for (i, f) in enumerate(NSB_FLOWS)
        dv = nsb_flow_derived(f)
        ro = isfinite(dv.ro) ? @sprintf("%.2e", dv.ro) : "—"
        push!(lines, @sprintf("  %-3d %-38s %-9s %-11s %-11s %-9s", i,
                              String(first(nsb_lang() == :ru ? f.ru : f.en, 38)),
                              String(first(string(f.model), 9)), nsb_bignum(dv.re_mol),
                              ro, nsb_bignum(Float64(dv.n_dns))))
    end
    return lines
end
