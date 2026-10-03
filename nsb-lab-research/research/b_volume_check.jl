#!/usr/bin/env julia
# ============================================================================
# b_volume_check.jl — Julia mirror of the b-correction <-> volume research
# add-on (companion to research/b_volume_experiment.py).
#
# It verifies, with the lab's OWN solver functions, the two core identities:
#
#   T:  div(R_b u) = -theta_b * (n_b . omega) + O(theta_b^2)
#       (regression slope of sampled div vs -theta_b*(n_b.omega) must be -1)
#
#   Q:  one b-kick on one vortex injects the flux  Q_b = theta_b * B, where
#       B = integral |n_b . omega| dV  is the b-charge (vorticity-weighted
#       volume) — verified on Taylor-Green and on an exact axisymmetric ring.
#
# Usage (from the repository root that contains nsb_lab_standalone.jl):
#   julia -t auto research/b_volume_check.jl
# ============================================================================

include(joinpath(@__DIR__, "..", "nsb_lab_standalone.jl"))
using .NSBLab: NSB_B, NSB_THETA_B, NSB_AXIS, NsbNSE3D, NsbWork3D,
    nsb_zerofield, nsb_prepare_state, nsb_ic_taylor_green, nsb_grid,
    nsb_rotate_pointwise!, nsb_b_rotation_matrix, nsb_curl_hat!,
    nsb_ifft_field!, nsb_fft_field!, nsb_project!, nsb_maskmul!,
    nsb_velocity_from_vorticity!
using Printf, LinearAlgebra, Statistics

const NG = 32                       # grid
const VBOX = (2.0 * pi)^3           # periodic cell volume, code units

"б-заряд B = ∫|n_b·ω| dV (кодовые единицы)."
function b_charge(w::NTuple{3,Array{Float64,3}}, nb)
    acc = 0.0
    n = size(w[1], 1)
    @inbounds @simd for i in eachindex(w[1])
        acc += abs(nb[1] * w[1][i] + nb[2] * w[2][i] + nb[3] * w[3][i])
    end
    return acc / n^3 * VBOX
end

"Q_b = ∫|div(R u)| dV для точечного поворота матрицей R."
function kick_flux(uhat, s::NsbNSE3D, W::NsbWork3D, R)
    ruhat = nsb_zerofield(s.n)
    nsb_rotate_pointwise!(ruhat, uhat, R, s, W)
    divh = im .* (s.kx .* ruhat[1] .+ s.ky .* ruhat[2] .+ s.kz .* ruhat[3])
    zero_re = zeros(s.n, s.n, s.n)
    divx = (zeros(s.n, s.n, s.n), zero_re, zero_re)
    nsb_ifft_field!(divx, (divh, zero_complex(s.n), zero_complex(s.n)), W, s)
    acc = 0.0
    @inbounds @simd for i in eachindex(divx[1])
        acc += abs(divx[1][i])
    end
    return acc / s.n^3 * VBOX
end

zero_complex(n) = zeros(ComplexF64, n, n, n)

"Точное вихревое кольцо: ω = Ω₀·exp(−((r−R₀)²+h²)/2σ²)·ê_φ (нормаль z)."
function ic_vring(n::Int; gamma::Float64 = 1.0, sigma::Float64 = 0.3,
                  R0::Float64 = 1.0, cx::Float64 = Float64(pi),
                  cy::Float64 = Float64(pi), cz::Float64 = Float64(pi))
    x = nsb_grid(n)
    w1 = zeros(n, n, n); w2 = zeros(n, n, n); w3 = zeros(n, n, n)
    Omega0 = gamma / (2.0 * pi * sigma^2)
    Threads.@threads for k in 1:n
        zk = x[k] - cz
        for j in 1:n, i in 1:n
            xi = x[i] - cx
            yj = x[j] - cy
            r = sqrt(xi^2 + yj^2)
            F = Omega0 * exp(-(((r - R0)^2 + zk^2) / (2.0 * sigma^2)))
            if r > 1e-12
                w1[i, j, k] = -F * yj / r
                w2[i, j, k] = F * xi / r
            end
        end
    end
    return (w1, w2, w3)
end

"Точный множитель ориентации f_plane = ⟨|n_b·ê_φ(φ)|⟩."
function ring_fplane(normal::Symbol)
    M = 8192
    acc = 0.0
    dphi = 2.0 * pi / M
    nb = collect(NSB_AXIS)
    for m in 1:M
        phi = m * dphi
        t = normal == :z ? (-sin(phi), cos(phi), 0.0) :
            normal == :x ? (0.0, -sin(phi), cos(phi)) :
                           (cos(phi), 0.0, -sin(phi))
        acc += abs(nb[1] * t[1] + nb[2] * t[2] + nb[3] * t[3])
    end
    return acc / M
end

function main()
    println("="^72)
    println("  b-correction <-> volume check (Julia mirror, lab functions)")
    println("="^72)
    @printf("  b = %.9f   theta_b = %.9f rad (%.4f deg)\n",
            NSB_B, NSB_THETA_B, rad2deg(NSB_THETA_B))
    @printf("  V_b = 4pi+2*sqrt3 = %.6f  -> %.3f%% of the box\n",
            4pi + 2sqrt(3), 100 * (4pi + 2sqrt(3)) / VBOX)

    s = NsbNSE3D(NG, 0.01)
    W = NsbWork3D(NG)
    nb = collect(NSB_AXIS)
    ok = true

    # --- T + Q on Taylor-Green ---------------------------------------------
    uhat = nsb_prepare_state(nsb_ic_taylor_green(NG), s, W)
    what = nsb_zerofield(NG)
    nsb_curl_hat!(what, uhat, s)
    w = (zeros(NG, NG, NG), zeros(NG, NG, NG), zeros(NG, NG, NG))
    nsb_ifft_field!(w, what, W, s)

    B = b_charge(w, nb)
    Q = kick_flux(uhat, s, W, nsb_b_rotation_matrix())
    ratio_tg = Q / (NSB_THETA_B * B)

    # regression: div vs -theta_b*(n_b.omega)
    ruhat = nsb_zerofield(NG)
    nsb_rotate_pointwise!(ruhat, uhat, nsb_b_rotation_matrix(), s, W)
    divh = im .* (s.kx .* ruhat[1] .+ s.ky .* ruhat[2] .+ s.kz .* ruhat[3])
    zr = zeros(NG, NG, NG)
    divx = (zeros(NG, NG, NG), zr, zr)
    nsb_ifft_field!(divx, (divh, zero_complex(NG), zero_complex(NG)), W, s)
    wpar = nb[1] .* w[1] .+ nb[2] .* w[2] .+ nb[3] .* w[3]
    xv = (-NSB_THETA_B) .* vec(wpar)
    yv = vec(divx[1])
    slope = dot(xv, yv) / dot(xv, xv)
    r2 = 1 - sum((yv .- slope .* xv).^2) / sum((yv .- mean(yv)).^2)

    @printf("\n[TG]  B = %.4f   Q_b = %.6f   Q/(theta_b*B) = %.6f\n", B, Q, ratio_tg)
    @printf("[TG]  theorem slope = %+.5f  (theory -1),  R2 = %.6f\n", slope, r2)
    ok = ok && abs(slope + 1) < 0.02 && abs(ratio_tg - 1) < 0.01

    # --- T + Q on the exact ring -------------------------------------------
    gamma, sigma, R0 = 1.0, 0.3, 1.0
    wring = ic_vring(NG; gamma = gamma, sigma = sigma, R0 = R0)
    what = nsb_zerofield(NG)
    nsb_fft_field!(what, wring, W, s)
    nsb_project!(what, what, s, W)
    nsb_maskmul!(what[1], s.mask); nsb_maskmul!(what[2], s.mask)
    nsb_maskmul!(what[3], s.mask)
    uhat = nsb_zerofield(NG)
    nsb_velocity_from_vorticity!(uhat, what, s, W)   # Biot-Savart (lab fn)
    wh = nsb_zerofield(NG)
    nsb_curl_hat!(wh, uhat, s)
    wrr = (zeros(NG, NG, NG), zeros(NG, NG, NG), zeros(NG, NG, NG))
    nsb_ifft_field!(wrr, wh, W, s)
    Bring = b_charge(wrr, nb)
    Qring = kick_flux(uhat, s, W, nsb_b_rotation_matrix())
    fp = ring_fplane(:z)
    theory = NSB_THETA_B * gamma * 2pi * R0 * fp
    @printf("\n[ring] B = %.4f (exact %.4f)   Q_b = %.6f (exact %.6f)\n",
            Bring, gamma * 2pi * R0 * fp, Qring, theory)
    @printf("[ring] Q/(theta_b*Gamma*L*f) = %.6f  (1 + O(theta_b^2))\n",
            Qring / theory)
    ok = ok && abs(Qring / theory - 1) < 0.05

    println("\n" * "="^72)
    println(ok ? "  ALL CHECKS PASS" : "  CHECKS FAILED")
    println("="^72)
    return ok ? 0 : 1
end

main()
