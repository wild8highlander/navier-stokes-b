import Mathlib.Data.Real.Basic
import Mathlib.Data.Real.Sqrt
import Mathlib.Data.Real.Pi.Bounds
import Mathlib.Tactic

noncomputable section
open Real

namespace Nsb

def bCorrection : ℝ := Real.pi / (4 * Real.pi^2 + 2 * Real.pi * Real.sqrt 3)

theorem bCorrection_pos : 0 < bCorrection := by
  unfold bCorrection
  have h1 : (0:ℝ) < 4 * Real.pi^2 := by nlinarith [Real.pi_pos]
  have h2 : (0:ℝ) < 2 * Real.pi * Real.sqrt 3 := by positivity
  exact div_pos Real.pi_pos (by linarith)

theorem bCorrection_lt_one : bCorrection < 1 := by
  unfold bCorrection
  have hden : (0:ℝ) < 4 * Real.pi^2 + 2 * Real.pi * Real.sqrt 3 := by positivity
  have hgt : Real.pi < 4 * Real.pi^2 + 2 * Real.pi * Real.sqrt 3 := by
    have hs3 : (1:ℝ) < Real.sqrt 3 :=
      (Real.lt_sqrt (show (0:ℝ) ≤ 1 by norm_num)).mpr (by norm_num)
    nlinarith [Real.pi_gt_three, hs3]
  exact (div_lt_one hden).mpr hgt

end ResearchPapersVerification
