# 13_roadmap.jl — бенчмарк FFT на этом железе и калькулятор роадмапа v0.2–v0.5.

"Бенчмарк собственного 3D-FFT: GFLOP/с (5·N³·log₂(N³) на одно 3D-преобразование)."
function nsb_bench_fft(; n::Int = 32, reps::Int = 3)
    A = [ComplexF64(sin(i * 0.1), cos(j * 0.1)) for i in 1:n, j in 1:n, k in 1:n]
    p = nsb_fft_plan(n)
    nsb_fftn!(A, p)   # прогрев
    t0 = time()
    for _ in 1:reps
        nsb_fftn!(A, p)
    end
    dt = (time() - t0) / reps
    flops = 5.0 * n^3 * log2(n^3)
    return (gflops = flops / dt / 1e9, sec_per_fft = dt)
end

struct NsbRoadRow
    n::Int
    mem_gb::Float64
    sec_per_step::Float64
    tg_hours::Float64          # TG: T=4, dt=0.0025 → 1600 шагов
    abc_hours::Float64         # ABC: T=8, dt=0.002 → 4000 шагов
    kida_hours::Float64        # Кида–Пельц: T=2.5, dt=0.00125 → 2000 шагов
    verdict_key::String
end

function nsb_roadmap_rows(gflops::Float64, mem_total_gb::Float64)
    rows = NsbRoadRow[]
    for n in (64, 128, 192, 256)
        # память: ~26 комплексных полей (состояние + K-буферы + работа)
        mem_gb = n^3 * 16 * 26 / 2^30
        # стоимость шага: ~13 эквивалентов 3D-FFT (RK4 × (2 ifft + 1 fft)) с оверхедом 1.3
        f_n = 5.0 * n^3 * log2(n^3) / 1e9 / max(gflops, 0.1)
        sps = 13 * f_n * 1.3
        tg = sps * 1600 / 3600
        abc = sps * 4000 / 3600
        kida = sps * 2000 / 3600
        if mem_gb > mem_total_gb * 0.85
            verdict = "road_verdict_no"
        elseif mem_gb > mem_total_gb * 0.45 || sps * 1600 > 8 * 3600
            verdict = "road_verdict_hpc"
        elseif sps * 1600 > 1.5 * 3600
            verdict = "road_verdict_ws"
        else
            verdict = "road_verdict_laptop"
        end
        push!(rows, NsbRoadRow(n, mem_gb, sps, tg, abc, kida, verdict))
    end
    return rows
end

function nsb_roadmap_report()
    nsb_header(L("road_hdr"))
    m = nsb_machine()
    nsb_println(nsb_muted("  CPU: " * m.cpu * " · " * string(m.threads) * " поток(ов) · " *
                          @sprintf("%.1f GiB RAM · Julia %s", m.mem_gb, m.julia)))
    bench = nsb_bench_fft(n = 32)
    nsb_println("  " * nsb_bold(Lf("road_gflops", bench.gflops)) *
                nsb_muted(@sprintf("  (3D-FFT N=32: %.1f мс)", bench.sec_per_fft * 1000)))
    rows = nsb_roadmap_rows(bench.gflops, m.mem_gb)
    nsb_println()
    nsb_println("  " * nsb_bold(L("road_tbl_hdr")))
    hdr = @sprintf("  %-5s %-9s %-11s %-9s %-9s %-10s %s", "N", L("road_mem"),
                   L("road_per_step"), "TG v0.2", "ABC v0.3", "Kida v0.3", "верedict")
    hdr = replace(hdr, "верedict" => "вердикт")
    nsb_println(nsb_dim(hdr))
    for r in rows
        mem = r.mem_gb < 1 ? @sprintf("%.2f GiB", r.mem_gb) : @sprintf("%.1f GiB", r.mem_gb)
        nsb_println(@sprintf("  %-5d %-9s %-11s %-9s %-9s %-10s %s", r.n, mem,
                             @sprintf("%.2f c", r.sec_per_step),
                             @sprintf("%.1f ч", r.tg_hours),
                             @sprintf("%.1f ч", r.abc_hours),
                             @sprintf("%.1f ч", r.kida_hours),
                             L(r.verdict_key)))
    end
    nsb_println()
    nsb_println(nsb_dim("  " * L("road_github")))
    nsb_println()
    # текстовая часть роадмапа
    txt = nsb_lang() == :ru ? [
        "v0.2 — Тейлор–Грин N=128–256: окно T=4, ν=0.01; цель — стабилизация мониторов",
        "       BKM/энстрофии по лестнице N (здесь: колонки TG).",
        "v0.3 — ABC и Кида–Пельц на N=192–256: охота за λ(t)>0; Кида–Пельц требует",
        "       симметрий (½ домена) — экономия ×8 по памяти против полного бокса.",
        "v0.4 — перенос горячего ядра на Rust/C++ (FFT + RK4): ожидается ×3–8",
        "       против чистой Julia без FFTW; интерфейс — те же JSON-вердикты.",
        "v0.5 — интервальная арифметика (CAP): N≤32–64, из-за 4–10× замедления",
        "       интервальных операций; цель — машинно-проверяемые оценки сверху.",
    ] : [
        "v0.2 — Taylor–Green N=128–256: window T=4, ν=0.01; goal — BKM/enstrophy",
        "       monitor stabilization across the N ladder (see TG columns).",
        "v0.3 — ABC and Kida–Pelz at N=192–256: hunting λ(t)>0; Kida–Pelz symmetries",
        "       (½ domain) save ×8 memory versus the full box.",
        "v0.4 — port the hot core to Rust/C++ (FFT + RK4): expected ×3–8 over pure",
        "       Julia without FFTW; interface stays the same JSON verdicts.",
        "v0.5 — interval arithmetic (CAP): N≤32–64 due to 4–10× interval overhead;",
        "       goal — machine-checkable upper bounds.",
    ]
    for ln in txt
        nsb_println("  " * ln)
    end
    return bench
end
