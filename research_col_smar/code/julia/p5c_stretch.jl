# p5c_stretch.jl — P5-C Julia verification track.
#
# Mirrors code/python/p5c_stretch_ensemble.py (statistics) and
# code/cpp/p5c_stretch.cpp:
#   (1) artifact recomputation: loads the raw f64 point-tensor files
#       (layout (9, 48, 48, 48), written by
#       `python3 p5c_stretch_ensemble.py --export-tensors`) and recomputes
#       s_rms, mean strain eigenvalues (LinearAlgebra.eigen), beta_S,
#       <cos^2 theta_i>, alpha mean/std (agreement target 1e-12);
#   (2) GOE Monte-Carlo: 200000 traceless symmetric Gaussian 3x3 matrices
#       (independent Xoshiro stream) — mean normalized eigenvalues, beta_S
#       and the alignment identity sum_i <cos^2 theta_i> = 1.
# Writes results/p5c_julia.json (hand-rolled JSON — zero dependencies).
#
# Run:  julia p5c_stretch.jl <project_root>   (default: ../..)

using LinearAlgebra
using Random

const ROOT = length(ARGS) >= 1 ? ARGS[1] : "../.."
const RES = joinpath(ROOT, "results")
const N = 48
const PTS = N^3

# --- artifact statistics ----------------------------------------------------
# File layout: POINT-major (N, N, N, 9) C-order with channels
# [Sxx,Syy,Szz,Sxy,Sxz,Syz,wx,wy,wz], i.e. flat offset = channel + 9*point.
# Julia is column-major, so the flat order maps onto reshape(9, N, N, N):
# the channel index varies fastest — exactly the on-disk layout.
# (reshape(N, N, N, 9) would be WRONG: it strides channels by N^3 and
# scrambles channels with spatial points.)
function compute_stats(T::Array{Float64,4})
    sxx = view(T, 1, :, :, :); syy = view(T, 2, :, :, :); szz = view(T, 3, :, :, :)
    sxy = view(T, 4, :, :, :); sxz = view(T, 5, :, :, :); syz = view(T, 6, :, :, :)
    ss = zero(Float64)
    @inbounds for i in eachindex(sxx)
        ss += sxx[i]^2 + syy[i]^2 + szz[i]^2 +
              2.0 * (sxy[i]^2 + sxz[i]^2 + syz[i]^2)
    end
    s_rms = sqrt(ss / PTS)

    l1 = 0.0; l2 = 0.0; l3 = 0.0
    c2 = [0.0, 0.0, 0.0]
    am = 0.0; am2 = 0.0
    S = Matrix{Float64}(undef, 3, 3)
    wxv = view(T, 7, :, :, :); wyv = view(T, 8, :, :, :); wzv = view(T, 9, :, :, :)
    @inbounds for i in eachindex(sxx)
        S[1, 1] = sxx[i]; S[2, 2] = syy[i]; S[3, 3] = szz[i]
        S[1, 2] = S[2, 1] = sxy[i]
        S[1, 3] = S[3, 1] = sxz[i]
        S[2, 3] = S[3, 2] = syz[i]
        F = eigen(S)  # ascending eigenvalues, columns = eigenvectors
        lam = F.values
        L = (lam[3] / s_rms, lam[2] / s_rms, lam[1] / s_rms)  # descending
        l1 += L[1]; l2 += L[2]; l3 += L[3]
        wx = wxv[i]; wy = wyv[i]; wz = wzv[i]
        wn = sqrt(wx^2 + wy^2 + wz^2)
        wh = (wx / wn, wy / wn, wz / wn)
        for a in 1:3
            col = F.vectors[:, 4 - a]  # descending order
            dot = wh[1] * col[1] + wh[2] * col[2] + wh[3] * col[3]
            c2[a] += dot * dot
        end
        # alpha = (omega_i S_ij omega_j) / (|omega|^2 s_rms), RAW omega
        wSw = wx * (S[1, 1] * wx + S[1, 2] * wy + S[1, 3] * wz) +
              wy * (S[2, 1] * wx + S[2, 2] * wy + S[2, 3] * wz) +
              wz * (S[3, 1] * wx + S[3, 2] * wy + S[3, 3] * wz)
        alpha = wSw / (wn^2 * s_rms)
        am += alpha
        am2 += alpha^2
    end
    mean_lam = (l1 / PTS, l2 / PTS, l3 / PTS)
    beta_S = mean_lam[2] / (mean_lam[1] - mean_lam[3])
    return (
        s_rms = s_rms,
        mean_lam = mean_lam,
        beta_S = beta_S,
        cos2 = (c2[1] / PTS, c2[2] / PTS, c2[3] / PTS),
        alpha_mean = am / PTS,
        alpha_std = sqrt(am2 / PTS - (am / PTS)^2),
    )
end

# --- GOE Monte-Carlo ----------------------------------------------------------
function goe_block(n_samples::Int)
    rng = Xoshiro(987654321017)
    l1 = 0.0; l2 = 0.0; l3 = 0.0; beta = 0.0; c2tot = 0.0
    S = Matrix{Float64}(undef, 3, 3)
    for _ in 1:n_samples
        g = randn(rng, 3, 3)
        S .= (g .+ g') ./ 2.0
        tr = (S[1, 1] + S[2, 2] + S[3, 3]) / 3.0
        S[1, 1] -= tr; S[2, 2] -= tr; S[3, 3] -= tr
        F = eigen(S)
        s_rms = sqrt(S[1, 1]^2 + S[2, 2]^2 + S[3, 3]^2 +
                     2.0 * (S[1, 2]^2 + S[1, 3]^2 + S[2, 3]^2))
        lam = F.values
        L = (lam[3] / s_rms, lam[2] / s_rms, lam[1] / s_rms)
        l1 += L[1]; l2 += L[2]; l3 += L[3]
        beta += L[2] / (L[1] - L[3])
        z = randn(rng, 3)
        zn = sqrt(z[1]^2 + z[2]^2 + z[3]^2)
        for a in 1:3
            col = F.vectors[:, 4 - a]
            c2tot += ((z[1] * col[1] + z[2] * col[2] + z[3] * col[3]) / zn)^2
        end
    end
    return (
        mean_lam = (l1 / n_samples, l2 / n_samples, l3 / n_samples),
        beta_S = beta / n_samples,
        cos2_sum = c2tot / n_samples,
    )
end

# --- hand-rolled JSON -----------------------------------------------------------
function jnum(x::Real)
    return string(Float64(x))
end

function emit(name, st)
    return string(
        "  \"", name, "\": {\n",
        "    \"s_rms\": ", jnum(st.s_rms), ",\n",
        "    \"mean_lam\": [", jnum(st.mean_lam[1]), ", ", jnum(st.mean_lam[2]),
        ", ", jnum(st.mean_lam[3]), "],\n",
        "    \"beta_S\": ", jnum(st.beta_S), ",\n",
        "    \"cos2\": [", jnum(st.cos2[1]), ", ", jnum(st.cos2[2]), ", ",
        jnum(st.cos2[3]), "],\n",
        "    \"alpha_mean\": ", jnum(st.alpha_mean), ",\n",
        "    \"alpha_std\": ", jnum(st.alpha_std), "\n",
        "  },\n",
    )
end

function main()
    out = IOBuffer()
    write(out, "{\n  \"program\": \"P5C_julia\",\n  \"date\": \"2026-09-29\",\n")
    for (tag, fname) in (("gauss_ref48", "p5c_tensors_gauss.f64"),
                         ("dns_ref48", "p5c_tensors_dns.f64"))
        path = joinpath(RES, fname)
        raw = reinterpret(Float64, read(path))
        @assert length(raw) == 9 * PTS "bad tensor file: $path"
        T = reshape(collect(raw), 9, N, N, N)
        st = compute_stats(T)
        write(out, emit(tag, st))
    end
    write(out, "  \"alignment_null\": 0.3333333333333333,\n")
    goe = goe_block(200_000)
    write(out, "  \"goe\": {\n")
    write(out, "    \"n\": 200000,\n")
    write(out, "    \"mean_lam\": [", jnum(goe.mean_lam[1]), ", ",
          jnum(goe.mean_lam[2]), ", ", jnum(goe.mean_lam[3]), "],\n")
    write(out, "    \"beta_S\": ", jnum(goe.beta_S), ",\n")
    write(out, "    \"cos2_sum\": ", jnum(goe.cos2_sum), "\n")
    write(out, "  }\n}\n")
    open(joinpath(RES, "p5c_julia.json"), "w") do fh
        write(fh, take!(out))
    end
    println("[p5c_julia] wrote ", joinpath(RES, "p5c_julia.json"))
    return 0
end

main()
