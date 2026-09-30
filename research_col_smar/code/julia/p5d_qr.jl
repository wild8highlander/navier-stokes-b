# p5d_qr.jl — P5-D Julia verification track.
#
# Mirrors code/python/p5d_qr_ensemble.py (statistics) and code/cpp/p5d_qr.cpp
# on the SAME artifact: the raw f64 point-tensor dump
# results/p5d_tensors_dns.f64 (layout: point-major (n, n, n, 9) C-order,
# channels [Sxx,Syy,Szz,Sxy,Sxz,Syz,wx,wy,wz], n = 64).
# Recomputes, in Float64:
#   (1) the P5-C scalar block — s_rms, mean strain eigenvalues
#       (LinearAlgebra.eigen), beta_S, <cos^2 theta_i>, alpha mean/std;
#   (2) the P5-D Q-R invariants of A = S + W, W_ij = -eps_ijk omega_k / 2:
#         Q = 1/4 |omega|^2 - 1/2 S:S,  R = -det A,
#         q = Q/<S:S>, r = R/<S:S>^{3/2},  D_S = (r/2)^2 + (q/3)^3,
#       with the same scalar set as qr_stats (masses, tail proximity with
#       the q < -0.5 restriction, tail population fraction).
# Agreement target with the Python/C++ tracks: 1e-10 (relative).
# Writes results/p5d_julia.json (hand-rolled JSON — zero dependencies).
#
# Run:  julia p5d_qr.jl <project_root>   (default: ../..)

using LinearAlgebra

const ROOT = length(ARGS) >= 1 ? ARGS[1] : "../.."
const RES = joinpath(ROOT, "results")
const N = 64
const PTS = N^3

function compute_all(T::Array{Float64,4})
    sxx = view(T, 1, :, :, :); syy = view(T, 2, :, :, :); szz = view(T, 3, :, :, :)
    sxy = view(T, 4, :, :, :); sxz = view(T, 5, :, :, :); syz = view(T, 6, :, :, :)
    wxv = view(T, 7, :, :, :); wyv = view(T, 8, :, :, :); wzv = view(T, 9, :, :, :)
    ss = 0.0
    @inbounds for i in eachindex(sxx)
        ss += sxx[i]^2 + syy[i]^2 + szz[i]^2 +
              2.0 * (sxy[i]^2 + sxz[i]^2 + syz[i]^2)
    end
    s2m = ss / PTS                       # <S:S>
    s_rms = sqrt(s2m)
    s2m_15 = s2m * sqrt(s2m)             # <S:S>^{3/2}

    l1 = 0.0; l2 = 0.0; l3 = 0.0
    c2 = [0.0, 0.0, 0.0]
    am = 0.0; am2 = 0.0
    qm = 0.0; rm = 0.0; rm2 = 0.0
    n_qpos = 0.0; n_node = 0.0; n_focal = 0.0
    n_qp_rn = 0.0; n_qp_rp = 0.0; n_qn_rn = 0.0; n_qn_rp = 0.0
    tail_sum = 0.0; tail_cnt = 0.0; tail_pop = 0.0
    S = Matrix{Float64}(undef, 3, 3)
    @inbounds for i in eachindex(sxx)
        S[1, 1] = sxx[i]; S[2, 2] = syy[i]; S[3, 3] = szz[i]
        S[1, 2] = S[2, 1] = sxy[i]
        S[1, 3] = S[3, 1] = sxz[i]
        S[2, 3] = S[3, 2] = syz[i]
        F = eigen(S)                     # ascending eigenvalues
        lam = F.values
        L = (lam[3] / s_rms, lam[2] / s_rms, lam[1] / s_rms)  # descending
        l1 += L[1]; l2 += L[2]; l3 += L[3]
        wx = wxv[i]; wy = wyv[i]; wz = wzv[i]
        wn = sqrt(wx^2 + wy^2 + wz^2)
        wh = (wx / wn, wy / wn, wz / wn)
        for a in 1:3
            col = F.vectors[:, 4 - a]
            dot = wh[1] * col[1] + wh[2] * col[2] + wh[3] * col[3]
            c2[a] += dot * dot
        end
        wSw = wx * (S[1, 1] * wx + S[1, 2] * wy + S[1, 3] * wz) +
              wy * (S[2, 1] * wx + S[2, 2] * wy + S[2, 3] * wz) +
              wz * (S[3, 1] * wx + S[3, 2] * wy + S[3, 3] * wz)
        alpha = wSw / (wn^2 * s_rms)
        am += alpha
        am2 += alpha^2
        # ---- velocity gradient A = S + W, W_ij = -eps_ijk w_k / 2 ----
        sx = sxx[i]; sy = syy[i]; sz = szz[i]
        s1c = sxy[i]; s2c = sxz[i]; s3c = syz[i]
        A11 = sx;             A12 = s1c - 0.5 * wz; A13 = s2c + 0.5 * wy
        A21 = s1c + 0.5 * wz; A22 = sy;             A23 = s3c - 0.5 * wx
        A31 = s2c - 0.5 * wy; A32 = s3c + 0.5 * wx; A33 = sz
        det = A11 * (A22 * A33 - A23 * A32) -
              A12 * (A21 * A33 - A23 * A31) +
              A13 * (A21 * A32 - A22 * A31)
        w2 = wx^2 + wy^2 + wz^2
        S2 = sx^2 + sy^2 + sz^2 + 2.0 * (s1c^2 + s2c^2 + s3c^2)
        q = (0.25 * w2 - 0.5 * S2) / s2m
        r = -det / s2m_15
        qm += q; rm += r; rm2 += r^2
        d_s = (r / 2.0)^2 + (q / 3.0)^3
        if q > 0.0
            n_qpos += 1.0
        elseif d_s >= 0.0
            n_node += 1.0
        else
            n_focal += 1.0
        end
        if q > 0.0 && r < 0.0; n_qp_rn += 1.0; end
        if q > 0.0 && r > 0.0; n_qp_rp += 1.0; end
        if q < 0.0 && r < 0.0; n_qn_rn += 1.0; end
        if q < 0.0 && r > 0.0; n_qn_rp += 1.0; end
        if q < -0.5
            x = 27.0 * r^2 / (-4.0 * q^3)
            tail_sum += x
            tail_cnt += 1.0
            if x >= 0.9
                tail_pop += 1.0
            end
        end
    end
    mean_lam = (l1 / PTS, l2 / PTS, l3 / PTS)
    return (
        s_rms = s_rms,
        mean_lam = mean_lam,
        beta_S = mean_lam[2] / (mean_lam[1] - mean_lam[3]),
        cos2 = (c2[1] / PTS, c2[2] / PTS, c2[3] / PTS),
        alpha_mean = am / PTS,
        alpha_std = sqrt(am2 / PTS - (am / PTS)^2),
        q_mean_norm = qm / PTS,
        r_mean_norm = rm / PTS,
        r_std_norm = sqrt(rm2 / PTS - (rm / PTS)^2),
        p_q_pos = n_qpos / PTS,
        p_qneg_node = n_node / PTS,
        p_qneg_focal = n_focal / PTS,
        p_qp_rn = n_qp_rn / PTS,
        p_qp_rp = n_qp_rp / PTS,
        p_qn_rn = n_qn_rn / PTS,
        p_qn_rp = n_qn_rp / PTS,
        tail_rel_mean = tail_sum / tail_cnt,
        tail_pop_frac = tail_pop / tail_cnt,
    )
end

function jnum(x::Real)
    return string(Float64(x))
end

function main()
    path = joinpath(RES, "p5d_tensors_dns.f64")
    raw = reinterpret(Float64, read(path))
    @assert length(raw) == 9 * PTS "bad tensor file: $path"
    T = reshape(collect(raw), 9, N, N, N)
    st = compute_all(T)
    out = IOBuffer()
    write(out, "{\n  \"program\": \"P5D_julia\",\n  \"date\": \"2026-09-30\",\n")
    write(out, "  \"artifact\": \"p5d_tensors_dns.f64\",\n")
    write(out, "  \"s_rms\": ", jnum(st.s_rms), ",\n")
    write(out, "  \"mean_lam\": [", jnum(st.mean_lam[1]), ", ",
          jnum(st.mean_lam[2]), ", ", jnum(st.mean_lam[3]), "],\n")
    write(out, "  \"beta_S\": ", jnum(st.beta_S), ",\n")
    write(out, "  \"cos2\": [", jnum(st.cos2[1]), ", ", jnum(st.cos2[2]),
          ", ", jnum(st.cos2[3]), "],\n")
    write(out, "  \"alpha_mean\": ", jnum(st.alpha_mean), ",\n")
    write(out, "  \"alpha_std\": ", jnum(st.alpha_std), ",\n")
    write(out, "  \"qr\": {\n")
    for (k, v) in (
        ("q_mean_norm", st.q_mean_norm), ("r_mean_norm", st.r_mean_norm),
        ("r_std_norm", st.r_std_norm), ("p_q_pos", st.p_q_pos),
        ("p_qneg_node", st.p_qneg_node), ("p_qneg_focal", st.p_qneg_focal),
        ("p_qp_rn", st.p_qp_rn), ("p_qp_rp", st.p_qp_rp),
        ("p_qn_rn", st.p_qn_rn), ("p_qn_rp", st.p_qn_rp),
        ("tail_rel_mean", st.tail_rel_mean),
        ("tail_pop_frac", st.tail_pop_frac),
    )
        write(out, "    \"", k, "\": ", jnum(v), ",\n")
    end
    write(out, "    \"_end\": 0}\n}\n")
    s = String(take!(out))
    s = replace(s, ",\n    \"_end\": 0}" => "\n  }")
    open(joinpath(RES, "p5d_julia.json"), "w") do fh
        write(fh, s)
    end
    println("[p5d_julia] wrote ", joinpath(RES, "p5d_julia.json"))
    return 0
end

main()
