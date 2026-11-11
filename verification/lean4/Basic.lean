import Foundation
import Mathlib.Data.Matrix.Basic
import Mathlib.Data.Real.Pi.Bounds
import Mathlib.Tactic

noncomputable section
open Matrix Real Nsb

namespace Section1

def bReference : ℝ := 0.0785
def θ_b : ℝ := Real.arcsin bCorrection

theorem b_pos : 0 < bCorrection := bCorrection_pos
theorem b_lt_one : bCorrection < 1 := bCorrection_lt_one

/-- Точные границы константы: b = 1/(4π+2√3) ≈ 0.06239.
    (Прежний пункт ledger `b_gt_007 : 0.07 < b` был ЛОЖЕН — 0.0785 это
    устаревшее значение b из v1; у v3/скриптов b ≈ 0.0624.) -/
theorem b_gt_062 : (0.062 : ℝ) < bCorrection := by
  unfold bCorrection
  have hπ1 : (3.1415 : ℝ) < Real.pi := Real.pi_gt_d4
  have hπ2 : Real.pi < 3.1416 := Real.pi_lt_d4
  have hs1 : (1.732 : ℝ) < Real.sqrt 3 :=
    (Real.lt_sqrt (show (0:ℝ) ≤ 1.732 by norm_num)).mpr (by norm_num)
  have hs2 : Real.sqrt 3 < 1.7321 :=
    (Real.sqrt_lt' (show (0:ℝ) < 1.7321 by norm_num)).mpr (by norm_num)
  have hp2 : Real.pi * Real.pi < 3.1416 * 3.1416 := by nlinarith [hπ1, hπ2]
  have hps : Real.pi * Real.sqrt 3 < 3.1416 * 1.7321 :=
    lt_of_le_of_lt (mul_le_mul_of_nonneg_right hπ2.le (Real.sqrt_nonneg 3))
      (mul_lt_mul_of_pos_left hs2 (by norm_num : (0:ℝ) < 3.1416))
  rw [lt_div_iff₀ (show (0:ℝ) < 4 * Real.pi^2 + 2 * Real.pi * Real.sqrt 3 by positivity)]
  nlinarith [hp2, hps, hπ1]

theorem b_lt_063 : bCorrection < 0.063 := by
  unfold bCorrection
  have hπ1 : (3.1415 : ℝ) < Real.pi := Real.pi_gt_d4
  have hπ2 : Real.pi < 3.1416 := Real.pi_lt_d4
  have hs1 : (1.732 : ℝ) < Real.sqrt 3 :=
    (Real.lt_sqrt (show (0:ℝ) ≤ 1.732 by norm_num)).mpr (by norm_num)
  have hp2 : 3.1415 * 3.1415 < Real.pi * Real.pi := by nlinarith [hπ1]
  have hps : 3.1415 * 1.732 < Real.pi * Real.sqrt 3 :=
    lt_of_le_of_lt (mul_le_mul_of_nonneg_left hs1.le (by norm_num : (0:ℝ) ≤ 3.1415))
      (mul_lt_mul_of_pos_right hπ1 (Real.sqrt_pos.mpr (by norm_num : (0:ℝ) < 3)))
  rw [div_lt_iff₀ (show (0:ℝ) < 4 * Real.pi^2 + 2 * Real.pi * Real.sqrt 3 by positivity)]
  nlinarith [hp2, hps, hπ2]

theorem sin_θ_b_eq_b : Real.sin θ_b = bCorrection := by
  unfold θ_b
  exact Real.sin_arcsin (by linarith [bCorrection_pos]) (le_of_lt b_lt_one)

def eZ : Fin 3 → ℝ := ![0, 0, 1]

theorem eZ_unit : ‖eZ‖ = 1 := by
  have hle : ‖eZ‖ ≤ 1 := by
    rw [Pi.norm_def]
    exact_mod_cast Finset.sup_le (fun b _ => by
      fin_cases b <;> simp [eZ] <;> norm_num)
  have hge : (1:ℝ) ≤ ‖eZ‖ := by
    have h2 : ‖eZ (2 : Fin 3)‖₊ ≤ Finset.univ.sup (fun b => ‖eZ b‖₊) :=
      Finset.le_sup (f := fun b : Fin 3 => ‖eZ b‖₊) (Finset.mem_univ (2 : Fin 3))
    have h2' : (1:NNReal) ≤ Finset.univ.sup (fun b => ‖eZ b‖₊) := by
      simpa [eZ] using h2
    exact_mod_cast h2'
  exact le_antisymm hle hge

def crossMatrix (n : Fin 3 → ℝ) : Matrix (Fin 3) (Fin 3) ℝ :=
  !![0, -n 2, n 1; n 2, 0, -n 0; -n 1, n 0, 0]

def rodriguesRotation (θ : ℝ) (n : Fin 3 → ℝ) : Matrix (Fin 3) (Fin 3) ℝ :=
  1 + Real.sin θ • crossMatrix n + (1 - Real.cos θ) • (crossMatrix n * crossMatrix n)

def R_b : Matrix (Fin 3) (Fin 3) ℝ := rodriguesRotation θ_b eZ

theorem rodrigues_zero (n : Fin 3 → ℝ) : rodriguesRotation 0 n = 1 := by
  simp [rodriguesRotation, Real.sin_zero, Real.cos_zero]

theorem eZ_euclid : dotProduct eZ eZ = 1 := by
  simp [eZ, dotProduct, Fin.sum_univ_three]

theorem crossMatrix_transpose (n : Fin 3 → ℝ) : (crossMatrix n)ᵀ = -crossMatrix n := by
  ext i j
  fin_cases i <;> fin_cases j <;> simp [crossMatrix, Matrix.transpose_apply] <;> ring

/-- K² = n nᵀ − (n·n)·I в явном виде (без гипотез). -/
theorem crossMatrix_mul_self (n : Fin 3 → ℝ) :
    crossMatrix n * crossMatrix n
      = Matrix.of ![![-(n 1 * n 1 + n 2 * n 2), n 0 * n 1, n 0 * n 2],
                   ![n 0 * n 1, -(n 0 * n 0 + n 2 * n 2), n 1 * n 2],
                   ![n 0 * n 2, n 1 * n 2, -(n 0 * n 0 + n 1 * n 1)]] := by
  ext i j
  fin_cases i <;> fin_cases j <;>
    simp [crossMatrix, Matrix.mul_apply, Fin.sum_univ_three] <;> ring

/-- K⁴ = −(n·n)·K² — общий случай тождества K³ = −(n·n)·K (при n·n = 1 это K³ = −K). -/
theorem crossMatrix_pow_four (n : Fin 3 → ℝ) :
    crossMatrix n * (crossMatrix n * (crossMatrix n * crossMatrix n))
      = -(dotProduct n n) • (crossMatrix n * crossMatrix n) := by
  rw [← Matrix.mul_assoc]
  rw [crossMatrix_mul_self n]
  ext i j
  fin_cases i <;> fin_cases j <;>
    simp [crossMatrix, Matrix.mul_apply, Fin.sum_univ_three, dotProduct] <;> ring

/-- Ортогональность вращения Родрига для ЕВКЛИДОВА единичного n.
    ВАЖНО: прежняя формулировка с гипотезой `‖n‖ = 1` была ЛОЖНА —
    `‖·‖` на `Fin 3 → ℝ` в Mathlib это sup-норма, а нужна сумма квадратов. -/
theorem rodrigues_orthogonal (θ : ℝ) (n : Fin 3 → ℝ) (hnn : dotProduct n n = 1)
    (hcs : Real.sin θ ^ 2 + Real.cos θ ^ 2 = 1) :
    (rodriguesRotation θ n)ᵀ * rodriguesRotation θ n = 1 := by
  have hKT : (crossMatrix n)ᵀ = -crossMatrix n := crossMatrix_transpose n
  have hK2T : ((crossMatrix n * crossMatrix n))ᵀ = crossMatrix n * crossMatrix n := by
    rw [Matrix.transpose_mul, hKT]; simp
  have hK4 : crossMatrix n * (crossMatrix n * (crossMatrix n * crossMatrix n))
      = -(dotProduct n n) • (crossMatrix n * crossMatrix n) := crossMatrix_pow_four n
  have hcoef : ((2 * (1 - Real.cos θ) - Real.sin θ ^ 2) + -(1 - Real.cos θ) ^ 2 : ℝ) = 0 := by
    have h : ((2 * (1 - Real.cos θ) - Real.sin θ ^ 2) + -(1 - Real.cos θ) ^ 2
        = 1 - Real.sin θ ^ 2 - Real.cos θ ^ 2) := by ring
    rw [h]; linarith [hcs]
  unfold rodriguesRotation
  simp only [Matrix.transpose_add, Matrix.transpose_smul, hKT, hK2T,
    Matrix.transpose_one, smul_neg]
  have hmain : (1 + -(Real.sin θ • crossMatrix n)
        + (1 - Real.cos θ) • (crossMatrix n * crossMatrix n))
      * (1 + Real.sin θ • crossMatrix n + (1 - Real.cos θ) • (crossMatrix n * crossMatrix n))
      = 1 + ((2 * (1 - Real.cos θ) - Real.sin θ ^ 2) • (crossMatrix n * crossMatrix n)
        + (1 - Real.cos θ) ^ 2 • (crossMatrix n * (crossMatrix n * (crossMatrix n * crossMatrix n)))) := by
    simp only [Matrix.mul_add, Matrix.add_mul, Matrix.one_mul, Matrix.mul_one,
      Matrix.mul_smul, Matrix.smul_mul, neg_mul, smul_neg, smul_smul, smul_add,
      Matrix.mul_assoc]
    module
  rw [hmain, hK4, hnn]
  simp only [smul_smul, mul_neg_one, ← add_smul]
  rw [hcoef, zero_smul, add_zero]

theorem R_b_orthogonal : R_bᵀ * R_b = 1 :=
  rodrigues_orthogonal θ_b eZ eZ_euclid (Real.sin_sq_add_cos_sq θ_b)

/-- Техническое: дельта-вычисление головы хвоста нулевой строки
(simp сворачивает нулевую строку `crossMatrix eZ` в лямбду, и конс-леммы
больше не достают до её элементов). -/
theorem vecHead_vecTail_zero_row (x : Fin 2) :
    Matrix.vecHead (Matrix.vecTail (fun _ : Fin 3 => (0:ℝ))) x = 0 := rfl

/-- det R_b = 1: поворот вокруг оси z на угол θ_b (после подстановки явного K²
формула det_fin_three даёт ровно sin² + cos²). -/
set_option maxHeartbeats 1000000 in
theorem R_b_det_one : R_b.det = 1 := by
  unfold R_b rodriguesRotation
  rw [crossMatrix_mul_self eZ, Matrix.det_fin_three]
  simp only [Matrix.add_apply, Matrix.smul_apply, Matrix.one_apply, Matrix.mul_apply,
    Matrix.of_apply, vecHead_vecTail_zero_row]
  norm_num
  nlinarith [Real.sin_sq_add_cos_sq θ_b]

def sqNorm (u : Fin 3 → ℝ) : ℝ := dotProduct u u

theorem R_b_preserves_norm (u : Fin 3 → ℝ) :
    sqNorm (R_b *ᵥ u) = sqNorm u := by
  unfold sqNorm
  rw [Matrix.dotProduct_mulVec, ← Matrix.mulVec_transpose, Matrix.mulVec_mulVec,
    R_b_orthogonal, Matrix.one_mulVec]

end Section1
