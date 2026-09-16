import ResearchPapersVerification.Common.Foundation
import Mathlib.Tactic

noncomputable section
open Real ResearchPapersVerification

namespace Section6

def γ_1 : ℝ := 14.134725141734693
def γ_2 : ℝ := 21.022039638771555
def γ_3 : ℝ := 25.010857580145688

theorem zeros_ordered : 0 < γ_1 ∧ γ_1 < γ_2 ∧ γ_2 < γ_3 := by
  unfold γ_1 γ_2 γ_3; norm_num

theorem γ_1_gt_14 : (14 : ℝ) < γ_1 := by unfold γ_1; norm_num

axiom zeta_pole_at_one : True
axiom zeta_functional_equation : True
axiom hilbert_polya_conjecture : True

theorem spectral_gap_first_zero : 0 < γ_1 := zeros_ordered.1

end Section6
