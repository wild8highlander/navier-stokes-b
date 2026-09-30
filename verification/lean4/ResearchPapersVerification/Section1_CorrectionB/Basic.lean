import ResearchPapersVerification.Common.Foundation
import Mathlib.LinearAlgebra.Matrix.Basic
import Mathlib.Tactic

noncomputable section
open Matrix Real ResearchPapersVerification

namespace Section1

def bReference : ℝ := 0.0785
def θ_b : ℝ := Real.arcsin bCorrection

theorem b_pos : 0 < bCorrection := bCorrection_pos
theorem b_lt_one : bCorrection < 1 := bCorrection_lt_one

theorem b_gt_007 : (0.07 : ℝ) < bCorrection := by sorry
theorem b_lt_008 : bCorrection < 0.08 := by sorry

theorem sin_θ_b_eq_b : Real.sin θ_b = bCorrection := by
  unfold θ_b
  exact Real.sin_arcsin (le_of_lt b_pos) (le_of_lt b_lt_one)

def eZ : Fin 3 → ℝ := ![0, 0, 1]

theorem eZ_unit : ‖eZ‖ = 1 := by
  simp [eZ, norm_eq, Fin.sum_univ_three, Real.norm_eq_abs]; norm_num

def crossMatrix (n : Fin 3 → ℝ) : Matrix (Fin 3) (Fin 3) ℝ :=
  !![0, -n 2, n 1; n 2, 0, -n 0; -n 1, n 0, 0]

def rodriguesRotation (θ : ℝ) (n : Fin 3 → ℝ) : Matrix (Fin 3) (Fin 3) ℝ :=
  1 + Real.sin θ • crossMatrix n + (1 - Real.cos θ) • (crossMatrix n * crossMatrix n)

def R_b : Matrix (Fin 3) (Fin 3) ℝ := rodriguesRotation θ_b eZ

theorem rodrigues_zero (n : Fin 3 → ℝ) : rodriguesRotation 0 n = 1 := by
  simp [rodriguesRotation, Real.sin_zero, Real.cos_zero]

theorem rodrigues_orthogonal (θ : ℝ) (n : Fin 3 → ℝ) (hn : ‖n‖ = 1) :
    (rodriguesRotation θ n)ᵀ * rodriguesRotation θ n = 1 := by sorry

theorem R_b_orthogonal : R_bᵀ * R_b = 1 := by
  have := rodrigues_orthogonal θ_b eZ eZ_unit
  exact this

theorem rodrigues_det (θ : ℝ) (n : Fin 3 → ℝ) (hn : ‖n‖ = 1) :
    (rodriguesRotation θ n).det = 1 := by sorry

theorem R_b_det_one : R_b.det = 1 := rodrigues_det θ_b eZ eZ_unit

def sqNorm (u : Fin 3 → ℝ) : ℝ := dotProduct u u

theorem R_b_preserves_norm (u : Fin 3 → ℝ) :
    sqNorm (R_b *ᵥ u) = sqNorm u := by sorry

end Section1
