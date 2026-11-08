import Mathlib.Tactic
import Mathlib.Data.Real.Pi.Bounds

/-!
# Базовые определения коррекции Брейкинга

РЕКОНСТРУКЦИЯ (2026-11-08): песочница была перезапущена, исходный
`Basic.lean` проекта утрачен вместе с остальной рабочей копией. Файл
восстановлен по контексту сессии: значение амплитуды коррекции
(`bCorrection = π/(4π² + 2π√3) ≈ 0.0624`, символьная выкладка из задачи
Кирхгофа о вихревом диполе) и определение тормозного угла сохранены.
-/

open Real

namespace Section1

/-- Амплитуда фазовой коррекции Брейкинга: `bCorrection = π/(4π² + 2π√3)`. -/
noncomputable def bCorrection : ℝ := π / (4 * π ^ 2 + 2 * π * Real.sqrt 3)

theorem bCorrection_pos : 0 < bCorrection := by
  have hπ : (0:ℝ) < π := Real.pi_pos
  have hsq : (0:ℝ) < π ^ 2 := sq_pos_of_pos hπ
  have h3 : (0:ℝ) < Real.sqrt 3 := Real.sqrt_pos.mpr (by norm_num)
  have hden : (0:ℝ) < 4 * π ^ 2 + 2 * π * Real.sqrt 3 :=
    add_pos (mul_pos (by norm_num) hsq) (mul_pos (mul_pos (by norm_num) hπ) h3)
  exact div_pos hπ hden

/-- Тормозной угол протокола: `θ_b = arcsin bCorrection > 0`. -/
noncomputable def θ_b : ℝ := Real.arcsin bCorrection

end Section1
