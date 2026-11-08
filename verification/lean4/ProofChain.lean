import ResearchPapersVerification.Common.Foundation
import ResearchPapersVerification.Section1_CorrectionB.Basic
import Mathlib.Data.Real.Pi.Bounds
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

theorem L_min_times_α_eq_one : L_min * α = 1 := by
  have hα : α ≠ 0 := ne_of_gt α_pos
  rw [L_min_eq_inv_α, div_mul_cancel₀ _ hα]

theorem γ_eq_b : γ = bCorrection := by
  unfold γ
  rw [L_min_eq_inv_α]
  have hα : α ≠ 0 := ne_of_gt α_pos
  field_simp

theorem α_bounds : (2:ℝ) < α ∧ α < 2.1 := by
  unfold α
  have hπ1 : (3.1415:ℝ) < Real.pi := Real.pi_gt_d4
  have hp2lo : 3.1415 * 3.1415 < Real.pi * Real.pi := by nlinarith
  have hp2hi : Real.pi * Real.pi < 3.1416 * 3.1416 := by
    have hπ2 : Real.pi < 3.1416 := Real.pi_lt_d4
    nlinarith
  constructor
  · rw [lt_div_iff₀ (by positivity : (0:ℝ) < 2 * Real.pi),
      Real.lt_sqrt (by nlinarith [hπ1])]
    nlinarith [hp2hi]
  · rw [div_lt_iff₀ (by positivity : (0:ℝ) < 2 * Real.pi),
      Real.sqrt_lt' (by nlinarith [hπ1])]
    nlinarith [hp2lo]

theorem L_min_lt_one : L_min < 1 := by
  unfold L_min
  rw [div_lt_one (by positivity : (0:ℝ) < Real.sqrt 168),
    Real.lt_sqrt (by nlinarith [Real.pi_gt_d4])]
  have hp2hi : Real.pi * Real.pi < 3.1416 * 3.1416 := by
    nlinarith [Real.pi_gt_d4, Real.pi_lt_d4]
  nlinarith [hp2hi]

/- АКСИОМА УДАЛЕНА (2026-11-07): `axiom bkmIntegral_if_bounded (t : ℝ) : Prop`
была пустой заглушкой (Prop без содержания, ничего не утверждала) и попадала
в #print axioms. Интегральное представление BKM-фактора при ограниченности —
НЕ формализовано; содержательная замена — замкнутая форма P2 в Braking2D. -/

end Section2
