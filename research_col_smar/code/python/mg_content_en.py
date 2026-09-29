# -*- coding: utf-8 -*-
"""Monograph "The Smagorinsky and Kolmogorov Constants", English text."""

META = {
    "title": "The Smagorinsky and Kolmogorov Constants",
    "subtitle": "A Unified Spectral Theory, Closures, and Numerical Experiment",
    "label": "Research monograph · navier-stokes-b program",
    "author": "wild8highlander",
    "org": "navier-stokes-b program · research_col_smar directory",
    "keywords": "turbulence, Kolmogorov constant, Smagorinsky constant, LES, K41, closures",
    "footer_left": "navier-stokes-b",
    "footer_right": "2026",
}

C = []


def h1(t):
    C.append(("h1", t))


def h2(t):
    C.append(("h2", t))


def p(t):
    C.append(("p", t))


def f(key, eqno):
    C.append(("formula", key, eqno))


def fig(name, cap):
    C.append(("fig", name, cap))


def table(headers, rows, cap):
    C.append(("table", headers, rows, cap))


h1("1. Introduction: two constants and one question")

p("Statistical turbulence theory owns the two most famous undetermined "
  "constants of continuum physics. The first is the <b>Kolmogorov "
  "constant</b> C_K — the amplitude of the inertial-range energy spectrum "
  "introduced in the classical 1941 papers. The second is the "
  "<b>Smagorinsky constant</b> C_s — the coefficient of the subgrid "
  "viscosity on which virtually every large-eddy simulation of "
  "turbulence rests, from climate models to acoustic simulators. "
  "Eighty years of measurements fixed the first at 1.50 ± 0.05 and "
  "forty years of testing fixed the second at 0.17 ± 0.02. Both are "
  "measured; neither is derived: self-similarity of the cascade fixes "
  "the spectral slope but not its amplitude.")

p("Yet the two constants describe the same object — the inertial range "
  "— from two sides. C_K measures how much kinetic energy is "
  "distributed across scales; C_s measures how fast the Smagorinsky "
  "closure transfers energy across the resolution boundary in LES. The "
  "question posed by this program is therefore natural: <b>are C_K and "
  "C_s independent empirical parameters, or two faces of one and the "
  "same cascade?</b> This monograph shows that they are rigidly coupled "
  "by a closed-form relation with no adjustable parameters.")

p("The headline result is one formula. Matching the subgrid dissipation "
  "flux of the Smagorinsky closure to the Kolmogorov flux through the "
  "inertial range yields <b>C_s = 1/(π(3C_K/2)^{3/4})</b>. With the "
  "experimental value C_K = 1.50 the formula gives C_s = 0.17327 — "
  "coinciding with the classical Lilly value 0.17326 to within "
  "6·10⁻⁶. The two most famous constants of turbulence are, in this "
  "precise sense, one constant seen twice: once as the spectral "
  "amplitude, once as the closure coefficient.")

p("The program is built so that every step of the derivation is "
  "executed, not postulated. Four numerical protocols — P1 (the master "
  "relation and filter sensitivity), P2 (the Heisenberg and Pao "
  "closures), P3 (Monte-Carlo verification on synthetic K41 fields) and "
  "P4 (3D pseudo-spectral DNS with a priori tests) — are implemented in "
  "Python, and the analytical core is duplicated in C++ (long double) "
  "and Julia. The three languages agree to 5–6 significant digits; all "
  "numbers are pinned in JSON protocols with hashes of the source "
  "files. Full regeneration takes about fifteen minutes on a laptop.")

p("The work is deliberately embedded in the parent repository "
  "navier-stokes-b — the universal b-correction program "
  "b = 1/(4π + 2√3), which approaches global regularity of the 3D "
  "Navier–Stokes equations through an energy-neutral geometric "
  "rotation. This monograph studies the classical, dissipative pole of "
  "the same problem; chapter 11 compares the two mechanisms — "
  "geometric and statistical — as two strategies for taming the same "
  "nonlinear transfer.")

h1("2. Mathematical apparatus")

h2("2.1. Equations and notation")

p("We work with the incompressible Navier–Stokes equations at constant "
  "density on a periodic domain:")

f("f1_nse", "(2.1)")

p("with velocity components u_i, pressure p and kinematic viscosity ν. "
  "The dissipation rate and the Kolmogorov scale are defined in the "
  "standard way:")

f("f4_eta", "(2.2)")

p("For homogeneous isotropic turbulence the basic object is the "
  "kinetic-energy spectrum E(k), defined by (2.3): the integral of the "
  "spectrum equals the kinetic energy per unit mass, and the "
  "dissipation is expressed through the same spectrum with the weight "
  "2νk². Both identities are not only used analytically here but also "
  "verified numerically to machine precision — the conventions are "
  "discussed in section 4.3 and appendix B.")

f("f22_ek_int", "(2.3)")

h2("2.2. Filtering and the LES formalism")

p("Large-eddy simulation splits the velocity into resolved and "
  "subgrid parts by a linear filter of width Δ. Three filter families "
  "are used: the sharp spectral cutoff G(k) = 1 for k < k_c = π/Δ and "
  "zero otherwise; the Gaussian filter G(k) = exp(−k²Δ²/24) with Δ the "
  "width parameter; and the box filter G(k) = sinc(kΔ/2). Filtered "
  "fields are overlined; double filtering is tilde-marked.")

p("The subgrid stresses τ_ij = ū_iū_j − \\widetilde{u_iu_j} are not "
  "closed by the resolved equations, and the practice of LES consists "
  "of modelling them. The Smagorinsky (1963) closure postulates a "
  "local equilibrium response of the subgrid scales to the resolved "
  "strain as an eddy viscosity:")

f("f5_nut", "(2.4)")

p("The Germano identity links the stresses of two filtering levels and "
  "underlies the dynamic procedure (chapter 6): for levels Δ̄ and "
  "Δ̃ = α_d Δ̄ the resolved stress L_ij takes the form (2.5) and "
  "satisfies the Germano relation that allows computing C_s locally, "
  "without external calibration:")

f("f6_germano", "(2.5)")

h2("2.3. Conventions that are usually left implicit")

p("A significant part of the scatter in published values of C_s — from "
  "0.12 to 0.24 — is convention, not physics: whether |S̄| carries the "
  "factor of two, where the resolved integral ends, whether the "
  "spectrum is normalized to kinetic energy or to variance. This "
  "program states its conventions explicitly and — more importantly — "
  "verifies each identity numerically. The full map of the factor-of-"
  "two trap is given in appendix B; the key consequence is that E(k) "
  "is defined as the kinetic spectrum, ∫E dk = ½⟨u²⟩, and the grid "
  "shell energy equals twice the spectrum value. In these conventions "
  "all the classical results — ε = 2ν∫k²E dk, ⟨|S̄|²⟩ = 2∫k²E G² dk — "
  "hold simultaneously, and the Lilly value 0.173 is recovered without "
  "any fitting.")

h1("3. K41 and what it cannot fix")

h2("3.1. Kolmogorov's hypotheses and the −5/3 spectrum")

p("Kolmogorov's three 1941 hypotheses — locality of transfer across "
  "scales, statistical homogeneity and isotropy of the small scales, "
  "and the determinacy of small-scale statistics by the pair (ε, ν) — "
  "lead to the unique dimensionally consistent form of the spectrum in "
  "the inertial range (3.1). The −5/3 slope is confirmed to a few "
  "percent in laboratory, atmospheric and oceanic measurements and in "
  "numerical experiments; together with the exact 4/5 law (3.2) it "
  "forms the rigid skeleton of the theory.")

f("f2_k41", "(3.1)")
f("f3_four5", "(3.2)")

h2("3.2. The status of C_K")

p("Self-similarity of the cascade does not fix the spectral amplitude: "
  "C_K remains a free multiplier to be supplied by measurement, "
  "closure or simulation. The most cited averaged value is "
  "C_K = 1.50 ± 0.05 (Sreenivasan's 1995 review); individual "
  "determinations range from 1.40 (tidal-channel data of Grant et al.) "
  "to 1.77 (the Eulerian DIA closure of Kraichnan). The "
  "Lagrangian-history closure (LhDIA, 1965) gives 1.52 — the closest "
  "theoretical value to experiment. Table 3.1 samples the "
  "determinations; the full survey is in chapter 10.")

table(
    ["Source", "Year", "Method", "C_K"],
    [
        ["Grant, Stewart, Moilliet", "1962", "tidal channel", "1.46"],
        ["Champagne", "1978", "wind tunnel", "1.50"],
        ["Kraichnan (DIA)", "1959", "Eulerian closure", "1.77"],
        ["Kraichnan (LhDIA)", "1965", "Lagrangian closure", "1.52"],
        ["Sreenivasan (review)", "1995", "meta-analysis", "1.50 ± 0.05"],
        ["Yeung, Zhou", "1997", "DNS 256³", "1.62"],
        ["Kaneda et al.", "2003", "DNS 4096³", "1.54"],
        ["This work (P2)", "2026", "Heisenberg closure", "1.48"],
    ],
    "Table 3.1. Determinations of the Kolmogorov constant.",
)

h2("3.3. What is needed to close the system")

p("To relate C_K and C_s, one identity connecting the resolved strain "
  "to the spectrum is missing. It is supplied by the exact spectral "
  "formula for homogeneous isotropic turbulence, verified on actual "
  "fields in chapter 8: the mean square of the filtered strain is the "
  "spectrum weighted by the squared filter (3.3). This formula makes "
  "the derivation of chapter 4 possible — and its numerical "
  "verification distinguishes the present derivation from a purely "
  "formal one.")

f("f8_strain_id", "(3.3)")

h1("4. Derivation I: the master relation C_s(C_K)")

h2("4.1. The subgrid budget")

p("The first budget is subgrid. The Smagorinsky closure drains "
  "resolved energy at a rate computed exactly, without statistics. "
  "Substituting the closure (2.4) into the instantaneous product "
  "τ_ij S̄_ij and using S̄_ij S̄_ij = |S̄|²/2 gives (4.1):")

f("f7_eps_sgs", "(4.1)")

p("Note the single factor of two: it entered the norm definition "
  "|S̄|² = 2S̄_ij S̄_ij and cancelled. Both forms — with one and with "
  "two powers of two — circulate in the literature; confusing them "
  "shifts C_s by the factor 2^{3/4} ≈ 1.68 with no arithmetic error "
  "anywhere. Appendix B returns to this.")

h2("4.2. The cascade budget and the matching")

p("The second budget is the cascade. Substituting the K41 spectrum "
  "into the identity (3.3) with a sharp cutoff k_c = π/Δ, the integral "
  "is taken exactly, and the mean square of the resolved strain is "
  "(4.2). If the cutoff sits deep in the inertial range, all the "
  "dissipation of the underlying flow passes through the subgrid "
  "channel: ε_sgs = ε. Equating (4.1) and ε and substituting (4.2), "
  "everything cancels but one combination:")

f("f9_strain_sharp", "(4.2)")
f("f10_master", "(4.3)")

p("This is the master relation of the program: the Smagorinsky "
  "constant is uniquely determined by the Kolmogorov constant. "
  "Numerically, at the experimental value C_K = 1.50:")

f("f11_master_num", "(4.4)")

p("The agreement with the classical Lilly value 0.17326, obtained in "
  "1966–1967 by the same circle of ideas but without reference to "
  "modern data on C_K, is 6·10⁻⁶. We state the status of the result "
  "carefully: the algebra is classical — the contribution is the "
  "explicit, convention-pinned chain from the measured C_K to C_s with "
  "a declared error budget and full numerical control of every link.")

h2("4.3. The filter family")

p("The master relation depends on the filter shape. For the Gaussian "
  "filter the integral (3.3) is taken in closed form and gives (4.5): "
  "the value is slightly below the sharp cutoff because the Gaussian "
  "tail admits some strain from k > k_c. The box filter requires "
  "numerical quadrature of sinc² and gives 0.15714. All three values "
  "fall inside the commonly used range 0.15–0.20 — which dissolves the "
  "apparent contradiction between «0.17» and «0.2» in the older "
  "literature: those are different filters.")

f("f12_gauss", "(4.5)")

table(
    ["Filter", "Formula", "C_s at C_K = 1.50"],
    [
        ["Sharp cutoff k_c = π/Δ", "1/(π(3C_K/2)^{3/4})", "0.17327"],
        ["Gaussian exp(−k²Δ²/24)", "(C_KΓ(2/3)12^{2/3})^{−3/4}", "0.16967"],
        ["Box sinc(kΔ/2)", "numerical, val^{−3/4}", "0.15714"],
    ],
    "Table 4.1. Master-relation values for the three filters (P1).",
)

fig("fig1_master_lilly.png",
    "Fig. 4.1. Master curves C_s(C_K) for three filter families; the "
    "circle is the reference point (C_K = 1.5, C_s = 0.1733); the band "
    "is the commonly used range. Protocol P1.")

h2("4.4. Sensitivity to the viscous tail")

p("The derivation assumes the cutoff deep in the inertial range. At "
  "finite Δ/η part of the strain belongs to the dissipation range, "
  "where the spectrum is cut by the Pao exponential — the integral "
  "(3.3) shrinks and the matched C_s grows. Protocol P1 quantifies the "
  "correction over Δ/η from 2 to 200: below one percent for "
  "Δ/η > 50, tens of percent at Δ/η ≈ 3. The curve C_s(Δ/η) is also "
  "computed on synthetic fields (chapter 8) — theory and Monte-Carlo "
  "agree within shell binning.")

h1("5. Derivation II: closures for the Kolmogorov constant")

h2("5.1. The Heisenberg spectral balance")

p("The inverse problem — computing C_K from first principles — is "
  "accessible only through two-point closures. The oldest is "
  "Heisenberg's (1948): eddies with wavenumbers above k act on the "
  "large scales as an effective viscosity (5.1), and the stationary "
  "energy flux is the balance (5.2):")

f("f13_heis_nut", "(5.1)")
f("f14_heis_bal", "(5.2)")

p("The system admits an exact solution. Differentiating the balance, "
  "expressing E through derivatives of ν_T and passing to the "
  "dimensionless variable χ = kη yields the closed-form Heisenberg "
  "spectrum (5.3) — a result the literature usually leaves as an "
  "integro-differential equation:")

f("f15_heis_spec", "(5.3)")

p("Formula (5.3) reproduces both limits automatically: in the inertial "
  "range E ∝ χ^{−5/3} with the constant (5.4), and in the far "
  "dissipation range the classical χ⁻⁷ falloff. The numerical check "
  "(protocol P2) confirms both slopes: −1.67 in the window "
  "χ ∈ [0.01, 0.2] (the asymptotic −5/3 is not yet reached in a finite "
  "window) and −7.00 in χ ∈ [3, 20].")

f("f16_heis_ck", "(5.4)")

p("Relation (5.4) is the closure map: the Kolmogorov constant is "
  "expressed through a single transfer constant α. Inverting with the "
  "experimental C_K = 1.50 pins α = 0.4838; re-measuring C_K from the "
  "closed-form spectrum in the same window returns 1.4814 — the "
  "closure is self-consistent to 1.3 %. The balance dissipation "
  "reproduces ε to a relative error of 2.2·10⁻⁴ — pure log-quadrature "
  "accuracy.")

h2("5.2. The Pao spectrum with exact dissipation normalization")

p("The second, more economical model is a Pao-type spectrum with a "
  "Gaussian dissipation-range cutoff. Requiring the exact "
  "dissipation 2ν∫k²E dk = ε fixes the exponent uniquely: "
  "β = (C_K Γ(2/3))^{3/2} ≈ 2.895 (5.5). This self-normalized spectrum "
  "serves as the target form in every numerical experiment of the "
  "program, in the same E(k) convention as the rest of the text.")

f("f17_pao", "(5.5)")

h2("5.3. Comparing the closures")

p("The Heisenberg and Pao spectra agree in the inertial range by "
  "construction (both are normalized to the same C_K) and differ in "
  "the dissipation range: Heisenberg gives the power law χ⁻⁷, Pao an "
  "exponential cutoff. Modern DNS supports the exponential form, so "
  "the Heisenberg closure should be read as inertially exact and "
  "qualitatively viscous. Fig. 5.1 shows both curves in compensated "
  "form; fig. 5.2 shows the map C_K(α) with the experiment and the "
  "Kraichnan closures as anchors.")

fig("fig2_spectra_closures.png",
    "Fig. 5.1. Model spectra in compensated form k^{5/3}E/ε^{2/3}: "
    "the Heisenberg closure (solid) and the Pao spectrum (dashed); the "
    "horizontal line is C_K = 1.5. Protocol P2.")
fig("fig3_ck_alpha.png",
    "Fig. 5.2. The Heisenberg closure map C_K(α); points mark the "
    "calibrations by experiment (1.50), LhDIA (1.52) and DIA (1.77). "
    "Protocol P2.")

h1("6. The dynamic Germano procedure")

p("The static value C_s = 0.173 is a globally averaged quantity. The "
  "Germano–Lilly procedure (1991–1992) makes it a field: the Germano "
  "identity at two filtering levels is solved by least squares "
  "locally at every point, giving (6.1). In applications the "
  "averaging ⟨·⟩ is taken over homogeneous directions or a sliding "
  "window to avoid singularities.")

f("f19_dynamic", "(6.1)")

p("In the limit where both filters lie in the inertial range and the "
  "flow is isotropic, the dynamic value collapses to the static "
  "master relation of chapter 4 — not a coincidence but a "
  "consistency check: the dynamic procedure inherits the same cascade "
  "physics. Away from isotropy (wall layers, stratification, "
  "transition) the local C_s deviates, up to sign changes — the "
  "detection of backscatter. This behaviour is reproduced in "
  "experiment P4 (chapter 9): the raw cs² = ⟨LM⟩/⟨MM⟩ is negative over "
  "part of the field, which is not an artifact but a diagnosis of the "
  "over-dissipativeness of the fixed closure outside its domain of "
  "validity.")

h1("7. Intermittency and the limits of the Gaussian approximation")

h2("7.1. The vanishing Germano correlation on Gaussian fields")

p("The most instructive negative result of the program came from what "
  "looks like the shortest path: why not measure C_s directly on a "
  "synthetic field with an exact K41 spectrum? The answer is "
  "fundamental. The Germano product ⟨L_ij S̄_ij⟩ is a third-order "
  "moment of the field; all third moments of a Gaussian field vanish. "
  "Hence, on a random-phase field with an exact spectrum, the a priori "
  "Smagorinsky constant is zero up to sampling noise — exactly what "
  "the program measures: ⟨L_ij S̄_ij⟩ = ±0.003 against an expected "
  "scale of O(1).")

f("f21_gauss_zero", "(7.1)")

p("The meaning: a spectrum by itself creates no cascade phase "
  "coherence. The Smagorinsky constant lives not in amplitudes but in "
  "phases — in the nonlinearly induced correlation across scales. Any "
  "derivation based on the spectrum alone (including the master "
  "relation) therefore uses the physical hypothesis of constant flux — "
  "and testing that hypothesis requires real dynamics. This motivates "
  "the division of labour in chapters 8–9: the spectral inputs are "
  "verified on synthetics, the flux on DNS.")

h2("7.2. Intermittency and the literature spread")

p("In real flows the small-scale statistics are intermittent: gradient "
  "distributions heavy-tailed, dissipation concentrated in thin "
  "sheets. The dynamic procedure responds by lowering the local C_s "
  "below the Gaussian value — an effect observed consistently since "
  "the work of Piomelli, Meneveau and Porté-Agel. The scatter of "
  "a priori values in the literature (0.04–0.2 depending on Re_λ, "
  "filter and flow) compounds with the conventional spread of chapter "
  "4; this work separates the two sources — conventions are pinned, "
  "and intermittency is measured separately (chapter 9).")

p("Note also the link with Kolmogorov's refined similarity of 1962: "
  "intermittency of the dissipation modulates the spectral amplitude "
  "log-normally, and the effective (finite-band measured) C_K grows "
  "with Re_λ. At DNS-accessible Reynolds numbers this growth amounts "
  "to a few percent — noticeable, but not dominant in the overall "
  "error budget of C_s.")
