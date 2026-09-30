# -*- coding: utf-8 -*-
"""Monograph, English text, part 5: chapter 12 gains the P5-B (96^3
resolution) and P5-C (stretching ensembles) sections. Inserted before the
old 12.7, which is renumbered to 12.9; chapter title, protocol list 12.6
and the closing summary are patched accordingly."""

from mg_content_en import C

FIG11_CAP = (
    "Fig. 11. P5-B, resolution 96³: left — spectra E(k) at t = 5 for the "
    "baseline run A (solid) and the hyperdissipative H2 with b = 2 "
    "(dashed) on a semilog scale — both tails are exponential, the "
    "smoothness certificate survives the doubling of the resolution; "
    "right — relative deviation of the diagnostics 48³ → 96³ on a log "
    "scale: averaged quantities converge to 10⁻⁶–10⁻⁴, supremum norms "
    "stay at the 1–2 % level.")

FIG12_CAP = (
    "Fig. 12. P5-C, vortex stretching statistics: left — densities of "
    "cos²θ_i for the 96³ DNS at t = 5 (solid) and the Gaussian ensemble "
    "(dashed, coinciding with the 1/3 level of a random direction) — DNS "
    "vorticity is expelled from the compressive direction e₃ and pulled "
    "toward the intermediate e₂ with a heavy tail as cos²θ₂ → 1; right — "
    "densities of the normalized stretching rate α: Gaussian fields and "
    "phase surrogates are symmetric about zero, the DNS mean is shifted "
    "into the positive region.")

NEW_BLOCKS = [
    ("h2", "12.7. Resolution 96³: convergence of the smoothness certificates"),
    ("p",
     "All trajectory-level conclusions of Sections 12.3–12.5 were "
     "obtained on a 48³ grid, and the most natural objection to them is "
     "resolution: do the safety margins of the criteria vanish when the "
     "number of nodes per coordinate is doubled? The P5-B protocol "
     "(code/python/p5b_resolution_96.py) repeats run A exactly — the "
     "same ν = 0.01, Taylor-Green vortex, T = 6, time step dt = 0.002, "
     "integrating-factor RK2 with Leray projection, 2/3 dealiasing — but "
     "on a 96³ grid: an eightfold increase in the number of degrees of "
     "freedom, k_max = 32 versus 16, executed in checkpointed chunks "
     "with the Fourier-space state as the complete integration variable. "
     "Every diagnostic of the chapter is recomputed from scratch, and "
     "the two grids are then compared pairwise."),
    ("p",
     "The result reduces to one sentence: everything that was finite on "
     "48³ stays finite and barely moves on 96³ (Table 12.4). The final "
     "energy differs by 3.1·10⁻⁵, the enstrophy peak by 1.1·10⁻⁴, the "
     "Serrin integrals by 5.7·10⁻⁶ and 5.1·10⁻⁶: spatially averaged "
     "quantities agree to the sixth digit. The BKM integral shifts by "
     "1.3 % (17.642 → 17.879) and the vorticity supremum by 1.9 % "
     "(5.692 → 5.799); both are supremum norms whose value is set by "
     "the position of a nearly degenerate argmax, so their deviation "
     "should be read as a conservative upper estimate of the accuracy, "
     "not as a trajectory disagreement."),
    ("table",
     ["Diagnostic", "48³", "96³", "rel. deviation"],
     [
         ["E(t = 6)", "0.122631", "0.122627", "3.1·10⁻⁵"],
         ["Ω_max", "1.29951", "1.29966", "1.1·10⁻⁴"],
         ["I_BKM(6)", "17.6423", "17.8786", "1.3·10⁻²"],
         ["‖ω‖_∞ (max)", "5.6921", "5.7988", "1.9·10⁻²"],
         ["∫⟨u⁴⟩dt", "0.232475", "0.232473", "5.7·10⁻⁶"],
         ["∫⟨u⁶⟩^{1/2}dt", "0.516896", "0.516893", "5.1·10⁻⁶"],
     ],
     "Table 12.4. Convergence of the smoothness diagnostics under "
     "doubling of the resolution (P5-B): run A at 48³ and 96³."),
    ("fig", "fig11_resolution_96.png", FIG11_CAP),
    ("p",
     "The spectral certificate does not merely survive — it improves. "
     "The tail slope at the enstrophy peak changes from σ = −6.64 to "
     "σ = −11.30, and the power-law fit quality grows from R² = 0.969 "
     "to 0.993: with a larger k_max the distance to the dissipative "
     "frontier increases and the tail is measured at a deeper level — "
     "the certificate band moves from [11, 16] to [22, 32]. The "
     "hyperdissipative run H2 (b = 2) at 96³ raises k_max/η_b from 6.2 "
     "to 12.4, yet the deviation of the measured dissipation peak from "
     "the prediction x*(b) remains at 10.9 % — exactly as on 48³. This "
     "is important negative information: the residual deviation is not "
     "resolution-limited but model-form-limited — it is produced by the "
     "shape of the Pao spectrum in the dissipative range, and doubling "
     "the grid does not remove it. The protocol records this explicitly, "
     "separating the discretization error from the closure error."),
    ("h2", "12.8. Vortex stretching statistics: random-field ensembles"),
    ("p",
     "The certificates of Sections 12.3–12.5 establish that the solution "
     "stays smooth, but they do not ask whose smoothness is being "
     "certified: does the trajectory keep the statistical anatomy of a "
     "genuine 3D cascade — or is it a degenerate flow for which all the "
     "gates close trivially? The mechanism the whole chapter rests on — "
     "stretching of vorticity by strain — has measurable invariants: the "
     "normalized stretching rate α = (ω_i S_ij ω_j)/(|ω|² s_rms), the "
     "parameter β_S = ⟨λ₂⟩/(⟨λ₁⟩ − ⟨λ₃⟩) locating the mean intermediate "
     "strain eigenvalue, and the alignment cos²θ_i — the distribution of "
     "vorticity directions over the strain eigensystem. The P5-C "
     "protocol (code/python/p5c_stretch_ensemble.py) computes these "
     "statistics on three families of 96³ fields: a Gaussian ensemble "
     "GAU of 32 synthetic K41 fields from the Pao generator (the P3 "
     "algorithm), eight phase surrogates SUR of a DNS snapshot "
     "(spectral amplitudes preserved, phases randomized, Leray "
     "projection and energy renormalization), and three snapshots of the "
     "DNS itself at t = 4, 5, 6."),
    ("p",
     "The null check of the theory passes exactly. For Gaussian fields "
     "vorticity and strain are independent, so all alignment must "
     "vanish: the measurement yields ⟨α⟩ = 0.0007 ± 0.0036, "
     "β_S = 0.0007 ± 0.0031 and cos²θ_i = (0.334, 0.334, 0.332) against "
     "the theoretical 1/3 (Table 12.5). Phase surrogates, which preserve "
     "the entire DNS spectrum but destroy the phase structure, give "
     "⟨α⟩ = 0.006 ± 0.007 — zero within the error. Two methodological "
     "conclusions follow. First, a single energy spectrum function, even "
     "an exact one, creates neither stretching nor alignment — these are "
     "dynamical, not spectral, properties of a field. Second, the same "
     "result is a quality control of the measurement pipeline: any bias "
     "it might carry would show up on the Gaussian fields as well."),
    ("table",
     ["Ensemble", "N", "⟨α⟩", "β_S", "cos²θ₁", "cos²θ₂", "cos²θ₃"],
     [
         ["GAU (K41, Gaussian)", "32", "0.0007 ± 0.0036", "0.0007 ± 0.0031",
          "0.334", "0.334", "0.332"],
         ["SUR (phase surrogates)", "8", "0.006 ± 0.007", "0.006 ± 0.006",
          "0.328", "0.352", "0.320"],
         ["DNS 96³, t = 4", "1", "0.125", "0.115", "0.299", "0.446", "0.255"],
         ["DNS 96³, t = 5", "1", "0.091", "0.115", "0.282", "0.432", "0.285"],
         ["DNS 96³, t = 6", "1", "0.095", "0.127", "0.299", "0.407", "0.293"],
     ],
     "Table 12.5. Stretching statistics by ensemble (P5-C): Gaussian "
     "fields and phase surrogates give zero stretching and alignment, "
     "the DNS shows the classical intermediate geometry."),
    ("p",
     "On the DNS snapshots the picture is qualitatively different, and "
     "it matches the classical statistical anatomy of turbulence. The "
     "mean normalized stretching rate is systematically positive, "
     "⟨α⟩ = 0.09–0.12 across the late horizon — stretching dominates "
     "over compression, exactly as the enstrophy balance (12.3) demands: "
     "otherwise Ω could not grow to its peak. The direction distribution "
     "is biased toward the intermediate strain eigenvector: "
     "cos²θ₂ = 0.41–0.45 against 0.28–0.30 and 0.25–0.29 for the largest "
     "and smallest eigenvalues — the celebrated intermediate alignment "
     "observed in grid DNS since Ashurst et al. The parameter "
     "β_S = 0.11–0.13 against 3·10⁻⁴ for a Gaussian orthogonal ensemble "
     "of 2·10⁵ matrices: the strain eigenvalues of the DNS are not "
     "random-matrix-like."),
    ("fig", "fig12_stretch_ensemble.png", FIG12_CAP),
    ("p",
     "The three-language verification of the block is built on the "
     "export of point tensors: for a pair of reference 48³ fields (a "
     "Gaussian one and a DNS snapshot) nine channels per node (S_xx, "
     "S_yy, S_zz, S_xy, S_xz, S_yz, ω_x, ω_y, ω_z) are written to disk, "
     "after which the C++ (long double) and Julia tracks recompute all "
     "statistics from the raw f64 file without any access to the Fourier "
     "representation. This is also where a substantive cross-platform "
     "verification error was caught and fixed: Julia's column-major "
     "layout requires the (9, N, N, N) reshaping — with the "
     "C-programmer's «natural» (N, N, N, 9) layout the channels are "
     "scrambled with spatial nodes and the statistics disagree by tens "
     "of percent; after the fix, the agreement of all three languages "
     "reaches 9·10⁻¹⁴ (the p5c_stretch_stats block in "
     "results/p5_cross_language.json). A GOE Monte-Carlo over 2·10⁵ "
     "matrices serves as the theoretical null for β_S and checks the "
     "identity Σ_i cos²θ_i = 1."),
    ("p",
     "For the theme of the chapter this check closes the circle. On the "
     "one hand, the certified field is not a degenerate artifact on "
     "which the criteria hold trivially: it carries a nonzero mean "
     "stretching, intermediate alignment and a non-random "
     "strain-eigenvalue structure — precisely the mechanism that feeds "
     "the enstrophy balance and keeps the regularity question "
     "non-trivial. On the other hand, the random-field ensembles show "
     "what a spectrum alone cannot supply: a Gaussian field with an "
     "exact K41 spectrum produces zero stretching statistics — hence "
     "the smoothness established for the DNS trajectory certifies the "
     "dynamics, not the spectral shape. Both conclusions strengthen the "
     "final Section 12.9."),
]

PROTO_ADD = (" The protocol extensions — resolution 96³ (P5-B) and the "
             "stretching ensembles (P5-C) — are executed by separate "
             "scripts, code/python/p5b_resolution_96.py and "
             "code/python/p5c_stretch_ensemble.py, with C++/Julia tracks "
             "(code/cpp/p5c_stretch.cpp, code/julia/p5c_stretch.jl), and "
             "are recorded in results/p5b_resolution_96.json and "
             "results/p5c_stretch_ensemble.json.")

INSERT_AFTER = ("the spectral tail keeps the Heisenberg steepness along "
                "the whole trajectory")
INSERT_TEXT = ("; the conclusions are robust to doubling the resolution "
               "48³ → 96³, where averaged diagnostics converge to "
               "10⁻⁶–10⁻⁴ and the tail becomes even steeper; the "
               "certified field carries the statistical anatomy of a real "
               "cascade — a positive mean stretching and intermediate "
               "alignment, absent in Gaussian fields and phase surrogates")
OLD_PHRASE = "and the 48³ resolution leaves the far tail only partially resolved"
NEW_PHRASE = ("and even the 96³ resolution leaves the far tail only "
              "partially resolved")

# 1. locate the old 12.7 heading
idx = next(i for i, b in enumerate(C)
           if b[0] == "h2" and b[1].startswith("12.7."))
C[idx:idx] = NEW_BLOCKS

# 2. renumber old 12.7 -> 12.9
h = C[idx + len(NEW_BLOCKS)]
assert h[0] == "h2" and h[1].startswith("12.7."), h[1]
C[idx + len(NEW_BLOCKS)] = ("h2", h[1].replace("12.7.", "12.9.", 1))

# 3. chapter title
for i, b in enumerate(C):
    if b[0] == "h1" and b[1].startswith("12. 3D smoothness"):
        C[i] = ("h1",
                "12. 3D smoothness: regularity criteria, the b-protocol, "
                "resolution and stretching statistics")
        break

# 4. protocol list in 12.6 (search before the insertion point)
for i in range(idx):
    if C[i][0] == "p" and C[i][1].startswith("The full P5 ensemble"):
        C[i] = ("p", C[i][1].rstrip() + PROTO_ADD)
        break

# 5. closing section
for i in range(idx + len(NEW_BLOCKS), len(C)):
    if C[i][0] == "p" and C[i][1].startswith("Established"):
        t = C[i][1]
        pos = t.find(INSERT_AFTER)
        assert pos >= 0, "insert_after not found"
        pos += len(INSERT_AFTER)
        t = t[:pos] + INSERT_TEXT + t[pos:]
        t = t.replace(OLD_PHRASE, NEW_PHRASE)
        C[i] = ("p", t)
        break
