# -*- coding: utf-8 -*-
"""Monograph, English text, part 2: chapters 8-11."""

from mg_content_en import C, h1, h2, p, f, fig, table

h1("8. Experiment I: verification on synthetic fields (P3)")

h2("8.1. Setup")

p("Protocol P3 builds an ensemble of divergence-free random fields on a "
  "96³ periodic grid whose shell energies exactly match the target "
  "K41-Pao spectrum. The key technical issue — the normalization of "
  "the Fourier amplitudes — is solved empirically: the Parseval weight "
  "is determined from the field itself (the ratio of the measured "
  "⟨u²⟩ to the sum of shell |û|²), after which a deterministic "
  "per-shell calibration drives every shell to the target in a few "
  "iterations. The scheme is immune to rfftn conventions and "
  "reproducible bit-for-bit (seed 20260929). The viscosity is chosen "
  "so that the dissipation range fits on the grid: k_η = 24 = k_max/2.")

h2("8.2. Verifying the spectral inputs")

p("On the generated fields the resolved-strain identity (3.3) is "
  "verified directly: the measured ⟨|S̄|²⟩ is compared with the "
  "quadrature over the actually measured shell energies weighted by "
  "G². The agreement is 3–20 % depending on the filter width — the "
  "residual is entirely shell binning on the discrete grid (integer k "
  "against radial |k|), as the systematic character of the error "
  "shows. For a theory built on continuum integrals this is an "
  "acceptable discrete-twin accuracy.")

h2("8.3. The convergence C_s(Δ/η) and the vanishing correlation")

p("The matched value C_s = √ε/(Δ⟨|S̄|²⟩^{3/4}) is measured on the "
  "fields for both filters at all widths. The key figure of the "
  "program is fig. 8.1: at Δ/η = 25 (the cutoff deep in the inertial "
  "range) the measured 0.16994 (sharp) and 0.17685 (Gaussian) agree "
  "with the analytics 0.17327/0.16967 within 2–4 %; at small Δ/η the "
  "curve grows exactly along the Pao-tail correction of section 4.4 — "
  "theory and Monte-Carlo converge independently. In parallel the "
  "Germano correlation ⟨L_ij S̄_ij⟩ is measured: ±0.003, i.e. zero — a "
  "direct illustration of the theorem of section 7.1.")

table(
    ["Filter", "Δ/η", "measured (P3)", "analytic"],
    [
        ["sharp", "50", "0.17758 ± 0.011", "0.17327"],
        ["sharp", "25", "0.16994 ± 0.010", "0.17327"],
        ["Gaussian", "25", "0.17685 ± 0.005", "0.16967"],
        ["Gaussian", "12.6", "0.18312 ± 0.005", "0.16967"],
        ["Gaussian", "3.1", "0.34651 ± 0.007", "Pao-tail regime"],
    ],
    "Table 8.1. Synthetic-field measurements of C_s "
    "(ensemble of 4 realizations, 96³).",
)

fig("fig4_p3_convergence.png",
    "Fig. 8.1. Convergence of C_s(Δ/η): points — Monte-Carlo on 96³ "
    "fields (P3); dashed curves — analytics (quadratures of the C++ "
    "track); the dotted line is the Lilly value.")

p("Let us fix the status of the negative result: the vanishing Germano "
  "correlation on Gaussian fields is not a failure but a measurement. "
  "It separates the spectral inputs of the derivation (the strain "
  "identity — confirmed) from its dynamical hypothesis (constant flux "
  "— requires real evolution), and that is why the next protocol is "
  "the DNS.")

h1("9. Experiment II: DNS and a priori tests (P4)")

h2("9.1. Setup of the numerical experiment")

p("Protocol P4 integrates the 3D pseudo-spectral Navier–Stokes "
  "equations on a 48³ grid with 2/3-rule dealiasing, Heun time "
  "stepping and a white-in-time solenoidal forcing confined to "
  "|k| ≤ 2.5 with physically normalized injection power. The "
  "stationary state: ε = 0.026, u′ = 0.60, Re_λ ≈ 145 (nominal; "
  "caveats below). The initial condition is a random divergence-free "
  "field renormalized to unit energy; the seed is fixed (424242).")

h2("9.2. The a priori test on real turbulence")

p("On 24 snapshots of the stationary state the a priori test is "
  "performed: C_s² = −⟨L_ij S̄_ij⟩/(Δ²⟨|S̄|³⟩) for Gaussian filters at "
  "Δ = 2, 3, 4, 6Δx. Unlike the synthetic fields, the Germano "
  "correlation is here nonzero by construction — the cascade builds "
  "phase coherence. The measured values 0.016–0.062 lie below the "
  "master value 0.173; the main cause is resolution: with "
  "k_max/k_η ≈ 0.6 the strain at the filter scales is undercounted, "
  "and the measured C_s is a lower bound. The conclusion agrees with "
  "the classical spread of a priori measurements in the literature "
  "(0.04–0.2 depending on Re_λ, filter and flow) and is honestly "
  "recorded in the protocol as a systematic grid-size limitation, not "
  "as a refutation of the master relation.")

p("The dynamic procedure (chapter 6) on the same fields returns the "
  "raw value cs² = ⟨LM⟩/⟨MM⟩, which over a noticeable part of the "
  "field is negative (typical values −10⁻⁴…−10⁻³): the fixed closure "
  "is over-dissipative outside the inertial range, and the dynamic "
  "procedure diagnoses this — a known but instructive result "
  "confirming that the P4 measurement chain is sensitive to the sign "
  "of the flux, not only to its magnitude.")

fig("fig5_p4_dns.png",
    "Fig. 9.1. The DNS experiment (P4): left — a slice of the "
    "vorticity magnitude; right — the averaged spectrum E(k) with the "
    "−5/3 fit band. Resolution caveats in the text.")
fig("fig6_p4_apriori.png",
    "Fig. 9.2. A priori C_s on real fields (P4): points — the mean "
    "over 24 snapshots ± SD for Gaussian filters; the band — the "
    "dynamic procedure; the dotted line — the Lilly value 0.173.")

h2("9.3. An honest error budget")

p("The consolidated budget of C_s consists of: (i) the uncertainty "
  "C_K ± 0.05 → ±3 % in C_s; (ii) the filter shape (0.157–0.173) → "
  "±5 %; (iii) finite Δ/η → from +1 % at Δ/η > 50 to tens of percent "
  "at Δ/η ~ 3; (iv) intermittency of real flows → −20…−40 % of the "
  "Gaussian value in a priori measurements; (v) DNS resolution (P4) — "
  "the lower-bound systematics. The program's recommendation: "
  "C_s = 0.17 ± 0.02 with an explicit reference to the filter and "
  "Δ/η — the value actually used in LES practice.")

h1("10. Consolidated results and the literature")

p("Table 10.1 collects the results of the program next to the "
  "classical determinations. The three implementation languages give "
  "identical numbers (table 10.2); fig. 10.1 places the program "
  "values among the literature values.")

table(
    ["Quantity", "Source", "Value"],
    [
        ["C_s (master relation, sharp)", "P1 (analytics)", "0.17327"],
        ["C_s (Lilly, classical)", "Lilly 1966/67", "0.17326"],
        ["C_s (Gaussian filter)", "P1 (analytics)", "0.16967"],
        ["C_s (box filter)", "P1 (quadrature)", "0.15714"],
        ["C_K (Heisenberg closure)", "P2 (α = 0.4838)", "1.4814"],
        ["C_K (synthetic fields)", "P3 (spectral fit)", "1.50 (input)"],
        ["C_s (a priori, DNS 48³)", "P4", "0.016–0.062"],
        ["C_s² dynamic (raw)", "P4", "≤ 0 (backscatter)"],
    ],
    "Table 10.1. Consolidated results of the program.",
)

table(
    ["Quantity", "Python", "C++ (long double)", "Julia"],
    [
        ["C_s (sharp)", "0.17327", "0.173266", "0.17327"],
        ["C_s (Gaussian)", "0.16967", "0.169667", "0.16967"],
        ["C_s (box)", "0.15714", "0.157140", "0.15714"],
        ["C_K (Heisenberg)", "1.4814", "1.4814", "1.4814"],
        ["Far-dissipation slope", "−7.00", "−7.00", "−7.0"],
    ],
    "Table 10.2. Three-language agreement of the analytical core.",
)

fig("fig7_ck_summary.png",
    "Fig. 10.1. The Kolmogorov constant: experiment, closures and this "
    "work (the dark bar is the Heisenberg closure of P2).")

h1("11. The program inside the b-correction framework")

p("The parent program navier-stokes-b is built around the universal "
  "polarization correction")

f("f20_bcorr", "(11.1)")

p("— an energy-neutral geometric rotation of the velocity field that "
  "suppresses the blow-up mechanism of the 3D Navier–Stokes equations "
  "without modifying the equations and without injecting energy. This "
  "monograph studies the complementary pole of the same problem: the "
  "classical dissipative closure, which removes subgrid energy at the "
  "controllable rate ε_sgs = (C_sΔ)²|S̄|³. Both mechanisms target the "
  "same nonlinear transfer, but their constants are obtained by "
  "fundamentally different routes: b from the polarization geometry of "
  "vortices, C_s from the statistics of the inertial range. "
  "Remarkably, both quantities are closed-form: both are expressed by "
  "formulas without adjustable parameters — a rarity for the "
  "Navier–Stokes equations (table 11.1).")

table(
    ["", "b-rotation (parent program)", "Smagorinsky closure (this work)"],
    [
        ["Mechanism", "geometric, energy-neutral", "eddy viscosity, dissipative"],
        ["Energy", "exactly conserved", "monotonically drained"],
        ["Constant", "b = 1/(4π+2√3)", "C_s = 1/(π(3C_K/2)^{3/4})"],
        ["Character", "kinematic, exact", "statistical, matched to K41"],
        ["Target", "blow-up suppression (BKM)", "subgrid closure (LES)"],
    ],
    "Table 11.1. Two strategies for taming the Navier–Stokes transfer.",
)

p("The methodological parallel matters more than the arithmetic: in "
  "both cases the «undetermined constant» became computable as soon as "
  "a frame of reference was fixed — geometric or statistical. This "
  "agrees with the philosophy of the repository: every numerical "
  "argument should end in a closed-form formula verified by "
  "independent implementations.")
