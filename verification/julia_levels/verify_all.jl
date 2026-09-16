# verify_all.jl — полный прогон Julia-верификации L1–L5 (чистый stdlib)
#
#   julia verify_all.jl                # всё; L5 (N=32) ≈ 5–15 мин
#   NSE3D_SKIP=1 julia verify_all.jl   # без L5
#   NSE3D_SMALL=1 julia verify_all.jl  # L5 в контрольном режиме

include(joinpath(@__DIR__, "l1_exact_constants.jl"))
include(joinpath(@__DIR__, "l2_rotation_algebra.jl"))
include(joinpath(@__DIR__, "l3_kirchhoff_vortices.jl"))
include(joinpath(@__DIR__, "l4_nse_2d.jl"))
include(joinpath(@__DIR__, "l5_nse_3d_bkm.jl"))

function main()
    t0 = time()
    r = Dict{String,Any}()
    r["L1"] = run_l1()
    r["L2"] = run_l2()
    r["L3"] = run_l3()
    r["L4"] = run_l4()
    if get(ENV, "NSE3D_SKIP", "") == "1"
        println("L5: SKIP (NSE3D_SKIP=1)")
        r["L5"] = nothing
    else
        r["L5"] = run_l5()
    end
    println("=" ^ 50)
    for k in sort(collect(keys(r)))
        v = r[k]
        println("  ", k, ": ", v === nothing ? "SKIP" : (v ? "PASS" : "FAIL"))
    end
    nfail = count(v === false for v in values(r))
    println("Итого: ", nfail == 0 ? "ВСЕ УРОВНИ PASS" : "ПРОВАЛЕНО: $nfail",
            " за ", round(time() - t0; digits = 0), " c")
    return nfail == 0
end
