import ResearchPapersVerification.Common.Foundation
import ResearchPapersVerification.Section1_CorrectionB.Basic
import Mathlib.Tactic

noncomputable section
open Real ResearchPapersVerification

namespace Section2

def PSL2_7_order : ℕ := 168
def α : ℝ := Real.sqrt 168 / (2 * Real.pi)
def L_min : ℝ := 2 * Real.pi / Real.sqrt 168
def γ : ℝ := α * bCorrection * L_min

theorem α_pos : 0 < α := by
  unfold α; apply div_pos
  · exact Real.sqrt_pos.mpr (by norm_num)
  · positivity

theorem L_min_eq_inv_α : L_min = 1/α := by
  unfold L_min α
  field_simp
  rw [Real.sqrt_sq (by norm_num : (0:ℝ) ≤ 168)]; ring

theorem L_min_times_α_eq_one : L_min * α = 1 := by
  rw [L_min_eq_inv_α, inv_mul_cancel₀ (ne_of_gt α_pos)]

theorem γ_eq_b : γ = bCorrection := by
  unfold γ
  rw [L_min_eq_inv_α, mul_one_div_cancel₀ (ne_of_gt α_pos)]
  ring

theorem α_bounds : (2:ℝ) < α ∧ α < 2.1 := by sorry
theorem L_min_lt_one : L_min < 1 := by sorry

axiom bkmIntegral_if_bounded (t : ℝ) : Prop

end Section2
