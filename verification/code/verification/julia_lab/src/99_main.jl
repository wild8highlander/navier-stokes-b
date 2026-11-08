# 99_main.jl — точка входа: init, banner, CLI-диспетчер или интерактивное меню.

function nsb_main(args::Vector{String})
    NSB_CFG[] = nsb_default_config()
    nsb_detect_terminal!()
    nsb_init_i18n!()
    act = nsb_cli_parse!(args)
    nsb_ensure_outdirs!()
    logpath = nsb_logfile_open!()
    try
        if act.action == "menu"
            nsb_banner()
            nsb_menu_loop()
        else
            nsb_banner()
            code = nsb_cli_dispatch(act.action, act.opts)
            nsb_println(nsb_rgb(NSB_C_TITLE..., Lf("quit_bye", NSB_CFG[].out_dir)))
            return code
        end
        return 0
    catch err
        if isa(err, InterruptException)
            nsb_println(nsb_warn(L("interrupted")))
            return 130
        else
            rethrow(err)
        end
    finally
        nsb_log_close!()
    end
end

