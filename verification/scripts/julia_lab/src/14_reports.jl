# 14_reports.jl — экспорт сессии: TXT (полный лог), CSV (временные серии),
# JSON (вердикты в контракте репо), Markdown, HTML+SVG.

nsb_json_escape(s::AbstractString) = replace(String(s),
    "\\" => "\\\\", "\"" => "\\\"", "\n" => "\\n", "\r" => "\\r", "\t" => "\\t")

nsb_json(x::AbstractString) = "\"" * nsb_json_escape(x) * "\""
nsb_json(x::Nothing) = "null"
nsb_json(x::Bool) = x ? "true" : "false"
nsb_json(x::Integer) = string(x)
nsb_json(x::AbstractFloat) = isfinite(x) ? (@sprintf("%.15g", x)) : "null"
nsb_json(x::Missing) = "null"
function nsb_json(v::Union{Vector,Tuple})
    return "[" * join((nsb_json(i) for i in v), ",") * "]"
end
function nsb_json(d::Dict)
    return "{" * join(("$(nsb_json(String(k))):$(nsb_json(val))" for (k, val) in d), ",") * "}"
end

"Вердикт в JSON-объект (контракт репозитория)."
function nsb_verdict_dict(v::NsbVerdict)
    d = Dict{String,Any}(
        "verifier" => "julia_lab",
        "experiment" => v.experiment,
        "mode" => v.mode,
        "language" => "julia",
        "params" => v.params,
        "all_passed" => v.ok,
        "wall_seconds" => round(v.wall; digits = 2),
        "checks" => [Dict{String,Any}("key" => c.key, "ok" => c.ok, "detail" => c.detail)
                     for c in v.checks],
        "values" => Dict{String,Any}((k => _jsonable(val) for (k, val) in v.values)),
    )
    return d
end

_jsonable(x::Union{Nothing,Missing}) = x === nothing ? nothing : missing
_jsonable(x::Union{Float64,Int,String,Bool}) = x
_jsonable(x) = try
    Float64(x)
catch
    string(x)
end

"CSV временных серий прогона."
function nsb_save_run_csv(v::NsbVerdict, path::AbstractString)
    ts = v.series
    ts === nothing && return nothing
    open(path, "w") do io
        write(io, "t,energy,enstrophy,palinstrophy,sup_omega,dissipation,bkm\n")
        n = length(ts.t)
        for i in 1:n
            write(io, @sprintf("%.8g,%.10g,%.10g,%.10g,%.10g,%.10g,%.10g\n",
                               ts.t[i], ts.energy[i], ts.enstrophy[i],
                               ts.palinstrophy[i], ts.sup_omega[i],
                               ts.dissipation[i], i < length(ts.bkm) ? ts.bkm[i+1] : ts.bkm[end]))
        end
    end
    return path
end

"Полный TXT-отчёт сессии."
function nsb_save_session_txt(path::AbstractString)
    open(path, "w") do io
        write(io, "NSB Julia Lab v" * NSB_LAB_VERSION * " — session report\n")
        write(io, "date: " * Dates.format(now(), "yyyy-mm-dd HH:MM:SS") * "\n")
        m = nsb_machine()
        write(io, "machine: " * m.cpu * ", " * string(m.threads) * " threads, " *
                  @sprintf("%.1f GiB", m.mem_gb) * ", Julia " * m.julia * "\n")
        write(io, "="^70 * "\n\n")
        for v in NSB_RESULTS
            write(io, "## " * v.experiment * " [" * v.mode * "]\n")
            write(io, "params: " * nsb_json(v.params) * "\n")
            for c in v.checks
                write(io, (@sprintf("  [%s] %s  %s\n", c.ok ? "PASS" : "FAIL",
                                    c.key, c.detail)))
            end
            write(io, "values: " * nsb_json(nsb_verdict_dict(v)["values"]) * "\n")
            write(io, "wall: " * string(round(v.wall; digits = 2)) * " s\n\n")
        end
    end
    return path
end

"Markdown-отчёт."
function nsb_save_session_md(path::AbstractString)
    m = nsb_machine()
    open(path, "w") do io
        write(io, "# NSB Julia Lab — отчёт сессии / session report\n\n")
        write(io, "- Дата/Date: " * Dates.format(now(), "yyyy-mm-dd HH:MM:SS") * "\n")
        write(io, "- Машина/Machine: " * m.cpu * ", " * string(m.threads) * " потоков, " *
                  @sprintf("%.1f GiB", m.mem_gb) * "\n")
        write(io, "- Прогонов/Runs: " * string(length(NSB_RESULTS)) * "\n\n")
        for v in NSB_RESULTS
            write(io, "## " * v.experiment * " (`" * v.mode * "`)\n\n")
            write(io, "| критерий/criterion | статус | деталь |\n|---|---|---|\n")
            for c in v.checks
                write(io, "| `" * c.key * "` | " * (c.ok ? "✅" : "❌") * " | " *
                          replace(c.detail, "|" => "\\|") * " |\n")
            end
            write(io, "\n**Вердикт/Verdict**: " * (v.ok ? "все проверки пройдены / all passed" : "есть провалы / failures") *
                      " · " * @sprintf("%.1f c\n\n", v.wall))
        end
    end
    return path
end

"HTML-отчёт с инлайн-SVG."
function nsb_save_session_html(path::AbstractString)
    io = IOBuffer()
    write(io, """<!DOCTYPE html><html><head><meta charset="utf-8">
    <title>NSB Julia Lab — session report</title><style>
    body{font-family:'DejaVu Sans',Segoe UI,Arial,sans-serif;max-width:960px;margin:2em auto;
         padding:0 1.5em;color:#1a2238;background:#fafbfd}
    h1{color:#0e7490;border-bottom:3px solid #0e7490;padding-bottom:.3em}
    h2{color:#155e75;margin-top:1.6em}
    table{border-collapse:collapse;width:100%;font-size:.92em}
    td,th{border:1px solid #d3dce8;padding:.35em .6em;text-align:left}
    th{background:#e8f2f8}
    .ok{color:#0a7d3b;font-weight:bold}.bad{color:#c02942;font-weight:bold}
    .meta{color:#5a6b85;font-size:.9em}
    .svgwrap{background:white;border:1px solid #e2e8f2;padding:.5em;margin:.6em 0}
    code{background:#eef3f9;padding:.1em .3em;border-radius:3px}
    </style></head><body>
    <h1>⚡ NSB Julia Lab v$(NSB_LAB_VERSION)</h1>""")
    m = nsb_machine()
    write(io, "<p class='meta'>$(Dates.format(now(), "yyyy-mm-dd HH:MM:SS")) · " *
              _html_esc(m.cpu) * " · $(m.threads) threads · " *
              @sprintf("%.1f GiB", m.mem_gb) * " · Julia $(m.julia)</p>")
    for v in NSB_RESULTS
        write(io, "<h2>" * _html_esc(v.experiment) *
                  " <code>" * v.mode * "</code></h2>")
        write(io, "<table><tr><th>criterion</th><th>status</th><th>detail</th></tr>")
        for c in v.checks
            write(io, "<tr><td><code>" * _html_esc(c.key) * "</code></td><td class='" *
                      (c.ok ? "ok" : "bad") * "'>" * (c.ok ? "PASS ✓" : "FAIL ✗") *
                      "</td><td>" * _html_esc(c.detail) * "</td></tr>")
        end
        write(io, "</table>")
        # SVG-графики из серий
        if v.series !== nothing && length(v.series.t) > 3
            p = NsbPlot(v.experiment, "t", "sup|ω|",
                        [NsbSeries(v.series.t, v.series.sup_omega, NSB_PAL[1], "sup|ω|")];
                        logy = true)
            svg = nsb_plot_svg(p)
            isempty(svg) || write(io, "<div class='svgwrap'>" * svg * "</div>")
        end
        write(io, "<p class='meta'>verdict: <b class='" * (v.ok ? "ok" : "bad") * "'>" *
                  (v.ok ? "ALL PASSED" : "FAILURES") * "</b> · " *
                  @sprintf("wall %.1f s", v.wall) * "</p>")
    end
    write(io, "</body></html>")
    open(path, "w") do f
        write(f, take!(io))
    end
    return path
end

_html_esc(s) = replace(replace(replace(String(s), "&" => "&amp;"), "<" => "&lt;"),
                        ">" => "&gt;")

"Экспорт всего сессии в папку reports."
function nsb_export_session()
    nsb_ensure_outdirs!()
    stamp = Dates.format(now(), "yyyymmdd_HHMMSS")
    rp = joinpath(NSB_CFG[].out_dir, "reports")
    paths = String[]
    push!(paths, nsb_save_session_txt(joinpath(rp, "session_$stamp.txt")))
    push!(paths, nsb_save_session_md(joinpath(rp, "session_$stamp.md")))
    push!(paths, nsb_save_session_html(joinpath(rp, "session_$stamp.html")))
    alljson = Dict{String,Any}("lab" => NSB_LAB_NAME, "version" => NSB_LAB_VERSION,
                               "results" => [nsb_verdict_dict(v) for v in NSB_RESULTS])
    jp = joinpath(NSB_CFG[].out_dir, "data", "session_$stamp.json")
    open(jp, "w") do io
        write(io, nsb_json(alljson))
    end
    push!(paths, jp)
    for (i, v) in enumerate(NSB_RESULTS)
        if v.series !== nothing
            cp = joinpath(NSB_CFG[].out_dir, "data",
                          "series_$(i)_$(v.experiment)_$(stamp).csv")
            nsb_save_run_csv(v, cp) !== nothing && push!(paths, cp)
        end
        # графики 600 dpi
        for (j, pl) in enumerate(v.plots)
            pp = joinpath(NSB_CFG[].out_dir, "plots",
                          "$(i)_$(j)_$(v.experiment)_$(stamp).png")
            try
                if pl isa NsbPlot
                    nsb_save_plot_png(pl, pp)
                elseif pl isa NsbHeat
                    nsb_save_heat_png(pl, pp)
                elseif pl isa Vector{<:Union{NsbPlot,NsbHeat}}
                    nsb_save_grid_png(pl, pp)
                end
                push!(paths, pp)
            catch err
                nsb_println(nsb_warn("plot save failed: $err"))
            end
        end
    end
    return paths
end
