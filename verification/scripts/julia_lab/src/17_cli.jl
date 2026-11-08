# 17_cli.jl — разбор аргументов командной строки и batch-режим.

function nsb_cli_help()
    nsb_println("""
    " NSB Julia Lab v" * $NSB_LAB_VERSION * " — самодостаточная лаборатория Навье–Стокса
    Использование:
      julia -t auto navier_stokes_lab.jl [опции]
    Опции:
      --quick                  быстрый прогон (мини-сьют + финальный PDF)
      --suite normal|hard      полная сьют в выбранном режиме
      --experiment tg|abc|houluo|baudit|scan
      --flow <id|all|list>     лаборатория течений (katrina, haiyan, ... all)
      --roadmap                бенчмарк и оценки роадмапа
      --report                 финальный отчёт (PDF+MD+HTML+JSON+CSV) по сессии
      --n N --nu ν --dt DT --t T   параметры эксперимента
      --ic tg|abc|houluo       начальное поле для scan
      --lang ru|en             язык (по умолчанию ru; NSB_LAB_LANG)
      --dpi N                  DPI графиков (по умолчанию 600)
      --out DIR                папка результатов (nsb_lab_results)
      --seed N                 зерно случайности
      --help                   эта справка
    Примеры:
      julia -t auto navier_stokes_lab.jl --quick --lang ru
      julia -t auto navier_stokes_lab.jl --experiment tg --n 64 --t 4
      julia -t auto navier_stokes_lab.jl --flow katrina
      julia -t auto navier_stokes_lab.jl --flow all --mode hard""")
    return nothing
end

function nsb_cli_parse!(args::Vector{String})
    cfg = NSB_CFG[]
    lang = get(ENV, "NSB_LAB_LANG", "ru")
    action = "menu"
    opts = Dict{String,Any}()
    i = 1
    while i <= length(args)
        a = args[i]
        if a == "--quick"
            action = "quick"
        elseif a == "--suite"
            action = "suite"; opts["mode"] = get(args, i + 1, "normal"); i += 1
        elseif a == "--experiment"
            action = "experiment"; opts["exp"] = get(args, i + 1, "tg"); i += 1
        elseif a == "--flow"
            action = "flow"; opts["flow"] = get(args, i + 1, "list"); i += 1
        elseif a == "--mode"
            opts["mode"] = get(args, i + 1, "normal"); i += 1
        elseif a == "--roadmap"
            action = "roadmap"
        elseif a == "--report"
            action = "report"
        elseif a == "--n"
            opts["n"] = parse(Int, args[i+1]); i += 1
        elseif a == "--nu"
            opts["nu"] = parse(Float64, replace(args[i+1], "," => ".")); i += 1
        elseif a == "--dt"
            opts["dt"] = parse(Float64, replace(args[i+1], "," => ".")); i += 1
        elseif a == "--t"
            opts["t"] = parse(Float64, replace(args[i+1], "," => ".")); i += 1
        elseif a == "--ic"
            opts["ic"] = Symbol(get(args, i + 1, "abc")); i += 1
        elseif a == "--lang"
            lang = get(args, i + 1, "ru"); i += 1
        elseif a == "--dpi"
            cfg.dpi = parse(Int, args[i+1]); i += 1
        elseif a == "--out"
            cfg.out_dir = args[i+1]; i += 1
        elseif a == "--seed"
            cfg.seed = parse(Int, args[i+1]); i += 1
        elseif a == "--help" || a == "-h"
            action = "help"
        else
            nsb_println(nsb_warn("неизвестный аргумент: $a"))
        end
        i += 1
    end
    nsb_setlang!(Symbol(lang))
    cfg.batch = action != "menu"
    cfg.quick = action == "quick"
    return (action = action, opts = opts)
end

function nsb_cli_dispatch(action::String, opts::Dict{String,Any})
    if action == "help"
        nsb_cli_help()
        return 0
    elseif action == "quick"
        nsb_run_suite("normal"; quick = true)
        nsb_export_session()
        nsb_generate_final_article()
        return 0
    elseif action == "suite"
        mode = get(opts, "mode", "normal") == "hard" ? "hard" : "normal"
        nsb_run_suite(mode)
        nsb_export_session()
        nsb_generate_final_article()
        return 0
    elseif action == "experiment"
        exp = get(opts, "exp", "tg")
        n = get(opts, "n", 0); nu = get(opts, "nu", NaN)
        dt = get(opts, "dt", NaN); t = get(opts, "t", NaN)
        mode = get(opts, "mode", "normal") == "hard" ? "hard" : "normal"
        v = exp == "abc" ? nsb_exp_abc(mode; n = n, dt = dt, t_hor = t) :
            exp == "houluo" ? nsb_exp_houluo(mode; n = n, dt = dt, t_hor = t) :
            exp == "baudit" ? nsb_exp_baudit(mode; n = n, dt = dt, t_hor = t, nu = nu) :
            exp == "scan" ? nsb_exp_scan(mode; ic = get(opts, "ic", :abc), n = n,
                                        dt = dt, t_hor = t) :
            nsb_exp_taylor_green(mode; n = n, nu = nu, dt = dt, t_hor = t)
        nsb_register!(v)
        nsb_export_session()
        nsb_generate_final_article()
        return v.ok ? 0 : 1
    elseif action == "flow"
        what = get(opts, "flow", "list")
        mode = get(opts, "mode", "normal") == "hard" ? "hard" : "normal"
        if what == "list"
            for ln in nsb_flows_table_text()
                nsb_println(ln)
            end
            return 0
        end
        flows = what == "all" ? NSB_FLOWS :
            [f for f in NSB_FLOWS if f.id == lowercase(what)]
        isempty(flows) && (nsb_println(nsb_warn("нет течения: $what")); return 1)
        for f in flows
            nsb_register!(nsb_flow_run(f, mode))
        end
        nsb_export_session()
        nsb_generate_final_article()
        return 0
    elseif action == "roadmap"
        nsb_roadmap_report()
        return 0
    elseif action == "report"
        nsb_export_session()
        nsb_generate_final_article()
        return 0
    end
    return 2
end
