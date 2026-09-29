# -*- coding: utf-8 -*-
"""Monograph, English text, part 3: chapters 13-14 and the appendices."""

from mg_content_en import C, h1, h2, p, f, fig, table

h1("13. Discussion: what is and is not claimed")

p("What is claimed. (i) The relation C_s(C_K) = 1/(π(3C_K/2)^{3/4}) is "
  "derived explicitly, in pinned conventions, and reproduces the "
  "classical Lilly value to 6·10⁻⁶. (ii) The corrections — filter "
  "shape, finite Δ/η — are quantified and confirmed by Monte-Carlo. "
  "(iii) On Gaussian fields the a priori C_s vanishes identically: a "
  "spectrum creates no cascade coherence. (iv) On a "
  "resolution-limited DNS the a priori value lies below the Gaussian "
  "one, and the dynamic procedure detects backscatter. (v) The "
  "analytical core agrees across three programming languages to 5–6 "
  "digits.")

p("What is not claimed. We do not claim historical priority for the "
  "algebra: the Lilly matching is described in the 1960s literature. "
  "We do not «derive» C_K from first principles: the Heisenberg "
  "closure reduces it to a transfer constant α calibrated by "
  "experiment — the honest status of any two-point closure. The a "
  "priori value on the 48³ DNS is a lower bound due to resolution, "
  "not an exact measurement. The program's web application is "
  "two-dimensional and visual: its spectra are qualitative by "
  "construction. Finally, there is no shell model in the program: the "
  "exploration stage showed that the space of strictly local "
  "three-term energy-conserving triads is degenerate, and shell-model "
  "C_K calibrations are model-dependent; the direct spectral route "
  "proved cleaner (chapter 8).")

p("A natural continuation is a 256³ DNS with k_max/k_η ≥ 1.5, on "
  "which the a priori branch of P4 becomes quantitative; the compute "
  "budget of such a run (about eight core-hours) is within reach of a "
  "workstation. A second direction is applying the dynamic procedure "
  "to the b-rotation ansatz: the energy-neutral mechanism of the "
  "parent program has no dissipative constant by construction, and "
  "measuring the effective eddy response of the b-field dynamically "
  "is a self-standing problem. A third direction — the 3D smoothness "
  "program with BKM/LPS diagnostics, the b-protocol and the "
  "hyperdissipative family — has since been executed as protocol P5 "
  "and is reported in chapter 12.")

h1("14. Conclusions")

p("The two most famous undetermined constants of turbulence are linked "
  "by the closed-form relation C_s = 1/(π(3C_K/2)^{3/4}). At the "
  "experimental C_K = 1.50 it gives C_s = 0.17327 — the classical "
  "Lilly value to 6·10⁻⁶; the filter family gives the range "
  "0.157–0.173; the Pao viscous-tail correction and the intermittency "
  "of real flows explain the rest of the literature spread. Every step "
  "of the chain is executed: the analytics is duplicated in three "
  "languages, the spectral identities are verified on 96³ fields, the "
  "dynamical hypothesis on DNS, and all protocols are pinned in JSON "
  "with hashes. The Smagorinsky and Kolmogorov constants are one "
  "constant seen twice: as the amplitude of the cascade and as the "
  "price of closing it.")

h1("Appendix A. Protocol parameters")

table(
    ["Protocol", "Parameters", "Runtime (2 cores)"],
    [
        ["P1", "23-point C_K table; 3 filters; 40 widths Δ/η", "≈ 60 s"],
        ["P2", "400k-point log grid; 3 calibrations of α", "≈ 25 s"],
        ["P3", "96³; 4 realizations; 8 (Δ, filter) pairs; seed 20260929", "≈ 3.5 min"],
        ["P4", "48³; 1600 steps; Δt = 4·10⁻³; 24 snapshots; seed 424242", "≈ 13 min"],
        ["P5", "48³; 5 runs × 3000 IFK steps; Δt = 2·10⁻³; T = 6", "≈ 10 min"],
        ["C++ track", "long double; 2·10⁶ quadrature nodes", "≈ 40 s"],
        ["Julia track", "no external packages", "≈ 10 s"],
    ],
    "Table A.1. Protocol parameters and cost.",
)

h1("Appendix B. The convention map and the factor-of-two trap")

p("A critical reading of published C_s values requires explicit "
  "conventions. Below is the summary of the decisions made in this "
  "work; each is verified numerically (chapters 4 and 8).")

table(
    ["Question", "This work's convention", "Effect of the alternative"],
    [
        ["Spectrum normalization", "∫E dk = ½⟨u²⟩ (kinetic)", "e_shell = 2E(k); else the ε-integral shifts by 2"],
        ["Strain norm", "|S̄|² = 2S̄_ij S̄_ij", "C_s shifts by 2^{3/4} ≈ 1.68"],
        ["Subgrid flux", "τ_ij S̄_ij = −(C_sΔ)²|S̄|³", "an extra 2 in the denominator → C_s/√2"],
        ["Gaussian width", "G = exp(−k²Δ²/24)", "a different Δ-parameter changes k_c"],
        ["Cutoff", "k_c = π/Δ", "with k_c = Δ⁻¹ the C_s range shifts"],
        ["Third moments", "⟨L_ij S̄_ij⟩ = 0 for Gaussian", "a priori C_s on synthetics is noise"],
    ],
    "Table B.1. Program conventions and the cost of violating them.",
)

p("An illustration of the cost: the same algebraic derivation executed "
  "in the «variance-shell» convention instead of the kinetic one gives "
  "C_s = 0.29 instead of 0.17 — a 70 % discrepancy with no arithmetic "
  "mistake anywhere. All protocols in results/ record the convention "
  "next to every number.")

h1("Appendix C. Code map and reproducibility")

p("The code/ directory holds three tracks: python (the full program: "
  "sk_core.py, p1_lilly.py, p2_closures.py, p3_synthetic_apriori.py, "
  "p4_dns_les.py, p5_regularity.py, p5_crosscheck.py, figures.py, "
  "run_all.py), cpp (sk_core.hpp, p1_lilly.cpp, p2_closures.cpp, "
  "p3_apriori_cpp.cpp, p5_regularity.cpp, Makefile) and julia "
  "(sk_core.jl, p1_p2_julia.jl, p5_regularity.jl — no external "
  "packages). Full regeneration: python3 run_all.py from code/python "
  "(~25 minutes with P5), then make run from code/cpp and julia "
  "p1_p2_julia.jl plus p5_regularity.jl ../../results. All programs "
  "are deterministic (fixed seeds), write UTF-8 JSON/CSV, and run on "
  "Linux, macOS and Android (Termux).")

p("Termux recipe: pkg install -y python git clang make; pip install "
  "numpy matplotlib; git clone "
  "https://github.com/wild8highlander/navier-stokes-b; then cd "
  "navier-stokes-b/research_col_smar/code/python; python3 run_all.py "
  "p1 p2 figures. The heavy stages P3/P4 may be skipped — their "
  "protocols are already pinned in results/.")
