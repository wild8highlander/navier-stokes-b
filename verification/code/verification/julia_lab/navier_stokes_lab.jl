# navier_stokes_lab.jl — точка входа NSB Julia Lab.
# Запуск:  julia -t auto navier_stokes_lab.jl [--quick] [--lang ru|en] [...]
# Только stdlib — никаких внешних пакетов.

const NSB_LAB_ROOT = @__DIR__

for f in ["00_boot.jl", "01_i18n.jl", "02_ui.jl", "04_fontdata.jl", "05_colormapdata.jl",
          "03_deflate_png.jl", "04_font.jl", "05_plots.jl",
          "06_fft.jl", "07_solver3d.jl", "08_diagnostics.jl", "09_ic_bcorr.jl",
          "10_blowup.jl", "11_experiments.jl", "12_flows.jl", "13_roadmap.jl",
          "14_reports.jl", "15_pdf.jl", "16_final_report.jl", "17_cli.jl",
          "18_menu.jl", "99_main.jl"]
    include(joinpath(NSB_LAB_ROOT, "src", f))
end

exit(nsb_main(ARGS))
