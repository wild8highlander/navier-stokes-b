# 18_menu.jl — интерактивное TUI-меню: скроллинг, прогресс, переключение
# языка цифрой 9, быстрый прогон, лаборатория течений, настройки.

function nsb_menu_loop()
    cfg = NSB_CFG[]
    while true
        nsb_banner()
        nsb_println("  " * nsb_bold(L("menu_quick")))
        nsb_println("  " * L("menu_suite_normal"))
        nsb_println("  " * L("menu_suite_hard"))
        nsb_println("  " * L("menu_custom"))
        nsb_println("  " * L("menu_flows"))
        nsb_println("  " * L("menu_roadmap"))
        nsb_println("  " * L("menu_reports"))
        nsb_println("  " * L("menu_settings"))
        nsb_println("  " * nsb_rgb(NSB_C_GOLD..., L("lang_toggle")))
        nsb_println("  " * L("menu_exit"))
        nsb_println()
        choice = nsb_readline("  ➜ [0–9] ")
        if choice == "0" || choice == "q" || choice == "Q" || choice == "й" || choice == "Й"
            nsb_println(nsb_rgb(NSB_C_TITLE..., Lf("quit_bye", cfg.out_dir)))
            return nothing
        elseif choice == "9"
            nsb_togglelang!()
            continue
        elseif choice == "1"
            nsb_run_suite("normal"; quick = true)
            nsb_export_session()
            nsb_generate_final_article()
            nsb_pause()
        elseif choice == "2"
            nsb_run_suite("normal")
            nsb_export_session()
            nsb_generate_final_article()
            nsb_pause()
        elseif choice == "3"
            nsb_println(nsb_warn("⚠ HARD: больше критериев и выше N — дольше по времени"))
            nsb_run_suite("hard")
            nsb_export_session()
            nsb_generate_final_article()
            nsb_pause()
        elseif choice == "4"
            nsb_menu_custom()
        elseif choice == "5"
            nsb_menu_flows()
        elseif choice == "6"
            nsb_roadmap_report()
            nsb_pause()
        elseif choice == "7"
            nsb_menu_reports()
        elseif choice == "8"
            nsb_menu_settings()
        else
            nsb_println(nsb_warn(L("invalid_choice")))
        end
    end
end

nsb_pause() = (nsb_readline(nsb_dim("\n  " * L("press_enter") * " ")); nothing)

# --------------------------------------------------------------- свой эксперимент
function nsb_menu_custom()
    nsb_header(L("custom_hdr"))
    def_n = 32
    n = nsb_ask_int(Lf("custom_prompt_n", def_n) * " →", def_n, 16, NSB_CFG[].max_n)
    ispow2(n) || (n = prevpow(2, n); nsb_println(nsb_warn("→ N=$n (степень двойки)")))
    nu = nsb_ask_float(Lf("custom_prompt_nu", 0.01) * " →", 0.01)
    dt = nsb_ask_float(Lf("custom_prompt_dt", 0.005) * " →", 0.005)
    t = nsb_ask_float(Lf("custom_prompt_t", 2.0) * " →", 2.0)
    ic = nsb_ask_int(L("custom_prompt_ic") * " →", 1, 1, 4)
    bk = nsb_ask_int(L("custom_prompt_b") * " →", 0, 0, 2)
    euler = nsb_ask_int(L("custom_prompt_euler") * " →", 0, 0, 1)
    v = if ic == 2
        nsb_exp_scan("custom"; ic = :abc, n = n, dt = dt, t_hor = t)
    elseif ic == 3
        nsb_exp_scan("custom"; ic = :houluo, n = n, dt = dt, t_hor = t)
    else
        nsb_exp_taylor_green("custom"; n = n, nu = euler == 1 ? 0.0 : nu,
                             dt = dt, t_hor = t)
    end
    if bk == 1
        nsb_println(nsb_muted("  → полная симметрия применяется пинками каждые 0.5"))
        r = nsb_evolve_with_kicks(n, euler == 1 ? 0.0 : nu, dt, t, 0.5, :full)
        nsb_println("  sup|ω| = $(@sprintf("%.6f", r.sup_omega)), div = $(@sprintf("%.2e", r.div_post))")
    elseif bk == 2
        nsb_println(nsb_muted("  → точечный пинк каждые 0.5"))
        r = nsb_evolve_with_kicks(n, euler == 1 ? 0.0 : nu, dt, t, 0.5, :pointwise)
        nsb_println("  sup|ω| = $(@sprintf("%.6f", r.sup_omega)), инъекция div = $(@sprintf("%.2e", r.div_injected))")
    end
    nsb_register!(v)
    nsb_export_session()
    nsb_pause()
    return nothing
end

# --------------------------------------------------------------- течения
function nsb_menu_flows()
    while true
        nsb_header(L("flows_hdr"))
        for ln in nsb_flows_table_text()
            nsb_println(ln)
        end
        nsb_println()
        nsb_println("  " * nsb_dim(L("flows_menu_hint")) * "   " *
                    nsb_rgb(NSB_C_GOLD..., "9 — язык/language"))
        c = nsb_readline("  ➜ ")
        if c == "9"
            nsb_togglelang!(); continue
        elseif c == "q" || c == "Q" || c == "й" || c == "Й" || c == "0"
            return nothing
        elseif lowercase(c) == "a"
            for f in NSB_FLOWS
                nsb_register!(nsb_flow_run(f, "normal"))
            end
            nsb_export_session()
            nsb_pause()
            return nothing
        end
        num = tryparse(Int, c)
        if num === nothing || num < 1 || num > length(NSB_FLOWS)
            nsb_println(nsb_warn(L("invalid_choice")))
            continue
        end
        f = NSB_FLOWS[num]
        nsb_register!(nsb_flow_run(f, "normal"))
        # терминальный превью из последнего прогона
        if !isempty(NSB_RESULTS) && NSB_RESULTS[end].experiment == "flow_" * f.id
            v = NSB_RESULTS[end]
            for pl in v.plots
                if pl isa NsbHeat
                    nsb_term_image(pl.field, L("termimg_caption"))
                    break
                end
            end
        end
        nsb_export_session()
        nsb_pause()
    end
end

# --------------------------------------------------------------- отчёты
function nsb_menu_reports()
    nsb_header(L("rep_hdr"))
    nsb_println("  " * L("rep_formats"))
    nsb_ensure_outdirs!()
    rp = joinpath(NSB_CFG[].out_dir, "reports")
    files = sort(filter(endswith(".md"), readdir(rp; join = true)); by = f -> mtime(f))
    arts = sort(filter(endswith(".pdf"), readdir(joinpath(NSB_CFG[].out_dir, "articles"); join = true));
                by = f -> mtime(f))
    plots = sort(filter(endswith(".png"), readdir(joinpath(NSB_CFG[].out_dir, "plots"); join = true));
                 by = f -> mtime(f))
    if isempty(files) && isempty(arts)
        nsb_println("  " * nsb_warn(L("rep_none")))
        nsb_pause()
        return nothing
    end
    nsb_println("  " * nsb_bold(L("rep_saved") * ":"))
    for f in reverse(files)[1:min(6, end)]
        nsb_println("    📄 " * basename(f))
    end
    for f in reverse(arts)[1:min(4, end)]
        nsb_println("    📕 " * basename(f) * nsb_muted("  ← " * L("rep_final_pdf")))
    end
    nsb_println("    🖼 PNG $(length(plots)) шт @ $(NSB_CFG[].dpi) dpi · " *
                joinpath(NSB_CFG[].out_dir, "plots"))
    # показать последний markdown через пейджер
    if !isempty(files)
        nsb_println()
        c = nsb_readline("  " * L("press_enter") * " (m — Markdown, 9 — язык) ➜ ")
        c == "9" && nsb_togglelang!()
        if c == "m" || c == "ь"
            nsb_page(read(reverse(files)[1], String))
        end
    end
    return nothing
end

# --------------------------------------------------------------- настройки
function nsb_menu_settings()
    nsb_header(L("set_hdr"))
    cfg = NSB_CFG[]
    nsb_println("  " * L("set_dpi") * ": " * nsb_bold(string(cfg.dpi)))
    nsb_println("  " * L("set_out") * ": " * cfg.out_dir)
    m = nsb_machine()
    nsb_println("  CPU: " * m.cpu * " · threads: " * string(m.threads) *
                " · RAM: " * @sprintf("%.1f GiB", m.mem_gb) * " · N≤" * string(cfg.max_n))
    nsb_println()
    c = nsb_readline("  " * L("set_dpi_new") * " (Enter — оставить, 9 — язык) ➜ ")
    c == "9" && nsb_togglelang!()
    dv = tryparse(Int, c)
    if dv !== nothing && dv in (300, 600, 1200, 2400)
        cfg.dpi = dv
        nsb_println("  " * nsb_ok("DPI = $dv"))
    end
    nsb_println()
    nsb_header(L("set_about"))
    for ln in split(L("set_about_txt"), '\n')
        nsb_println("  " * nsb_dim(ln))
    end
    nsb_println("  " * nsb_dim("b = 1/(4π+2√3) = " * @sprintf("%.9f", NSB_B) *
                               " · θ_b = " * @sprintf("%.6f", NSB_THETA_B)))
    nsb_pause()
    return nothing
end
