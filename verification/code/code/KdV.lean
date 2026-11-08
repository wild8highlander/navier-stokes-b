import Mathlib.Tactic
import Mathlib.Analysis.Calculus.Deriv.Basic
import Mathlib.Analysis.SpecialFunctions.ExpDeriv

/-!
# Уравнение Кортевега–де Фриза и односолитонное решение

Формализация по требованию ТЗ: определено само дифференциальное уравнение
(предикат `IsKdVSolution`: `u_t + 6·u·u_x + u_xxx = 0`) и доказана
подстановка солитона — прежние `axiom KdV (u) : Prop` и
`soliton_solves_KdV := sorry` удалены как фиктивные.

Схема доказательства (полностью машинно проверена):

* `sechR` определён явно через `exp` (2/(eˣ + e⁻ˣ));
* солитон `(c/2)·sech²(k·(x − ct))` с `k = √c/2` сводится к функции
  `U(s) = 2c·s²/(1+s²)²` от `s = exp(k(x−ct))` (`solitonK_eq_U`);
* для `U` вычислены три производные `U'`, `U''`, `U'''` (леммы
  `hasDerivAt_U`, `hasDerivAt_U1`, `hasDerivAt_U2`);
* правило цепочки три раза (`phase_deriv_x`: `s' = k·s`) даёт
  `u_x, u_xx, u_xxx`, правило цепочки по `t` (`phase_deriv_t`:
  `s_t = −ck·s`) даёт `u_t`;
* финальная алгебра — полиномиальное тождество `kdv_master` при `c = 4k²`.

Солитон с `k = √c/2` — точное решение `u_t + 6·u·u_x + u_xxx = 0`
(`soliton_solves_KdV`). Взаимодействие солитонов и преобразование Миуры —
НЕ формализованы (см. `OPEN_PROBLEMS.md`).
-/

noncomputable section
namespace Verification.KdV

/-! ## Уравнение -/

/-- Предикат «u — классическое решение KdV»: `u_t + 6·u·u_x + u_xxx = 0`
(первый аргумент `u` — координата x, второй — время t). -/
def IsKdVSolution (u : ℝ → ℝ → ℝ) : Prop :=
  ∀ x t,
    deriv (fun t' => u x t') t
    + 6 * u x t * deriv (fun x' => u x' t) x
    + deriv (fun x' => deriv (fun x'' => deriv (fun x''' => u x''' t) x'') x') x = 0

/-! ## Определения -/

/-- sech задан явно: `2/(eˣ + e⁻ˣ)`. -/
def sechR (x : ℝ) : ℝ := 2 / (Real.exp x + Real.exp (-x))

/-- Экспоненциальная фаза: `exp(k·(x − c·t))`. -/
def phase (k c x t : ℝ) : ℝ := Real.exp (k * (x - c * t))

/-- Солитон с явной фазой k: `(c/2)·sech²(k·(x − ct))`. -/
def solitonK (c k x t : ℝ) : ℝ := (c/2) * (sechR (k * (x - c*t)))^2

/-- Классический односолитон KdV: `k = √c/2`. -/
def soliton (c x t : ℝ) : ℝ := solitonK c (Real.sqrt c / 2) x t

/-- Профиль солитона как функция одной переменной `s`:
`U(s) = 2c·s²/(1+s²)²`. -/
def U (c s : ℝ) : ℝ := 2 * c * s ^ 2 / (1 + s ^ 2) ^ 2

/-- Производная `U'`. -/
def U1 (c s : ℝ) : ℝ := 4 * c * s * (1 - s ^ 2) / (1 + s ^ 2) ^ 3

/-- Вторая производная `U''`. -/
def U2 (c s : ℝ) : ℝ := 4 * c * (1 - 8 * s ^ 2 + 3 * s ^ 4) / (1 + s ^ 2) ^ 4

/-- Третья производная `U'''`. -/
def U3 (c s : ℝ) : ℝ := -48 * c * s * (s ^ 4 - 5 * s ^ 2 + 2) / (1 + s ^ 2) ^ 5

/-! ## Мастер-тождество -/

/-- Чистое полиномиальное тождество, на которое сводится KdV-остаток
при `c = 4k²`: `-c(1-s²)(1+s²)² + 12cs²(1-s²) + c(1-11s²+11s⁴-s⁶) = 0`
(проверено символьно: обе скобки сокращаются тождественно). -/
theorem kdv_master (k s : ℝ) :
    (4 * k ^ 2) * (-(1 - s ^ 2) * (1 + s ^ 2) ^ 2 + 12 * s ^ 2 * (1 - s ^ 2))
      + (4 * k ^ 2) * (1 - 11 * s ^ 2 + 11 * s ^ 4 - s ^ 6) = 0 := by
  ring

/-! ## Мост: солитон = U(экспонента фазы) -/

theorem solitonK_eq_U (c k x t : ℝ) : solitonK c k x t = U c (phase k c x t) := by
  unfold solitonK phase U sechR
  have hspos : (0:ℝ) < Real.exp (k * (x - c * t)) := Real.exp_pos _
  have hneg : Real.exp (-(k * (x - c * t))) = (Real.exp (k * (x - c * t)))⁻¹ :=
    Real.exp_neg _
  field_simp [hspos, hneg]
  ring

/-! ## Вспомогательные леммы о HasDerivAt -/

/-- Замена значения производной на кольцево равное. -/
private theorem hasDerivAt_congr_value {f : ℝ → ℝ} {x v w : ℝ} (h : HasDerivAt f v x)
    (hvw : v = w) : HasDerivAt f w x := by
  rw [← hvw]; exact h

/-! ## Производные фазы -/

theorem phase_deriv_x (k c t x : ℝ) :
    HasDerivAt (fun y => phase k c y t) (phase k c x t * k) x := by
  unfold phase
  have hsub : HasDerivAt (fun y => y - c * t) 1 x := by
    simpa using (hasDerivAt_id x).sub (hasDerivAt_const x (c * t))
  have hlin : HasDerivAt (fun y => k * (y - c * t)) (k * 1) x := hsub.const_mul k
  have hcomp := (Real.hasDerivAt_exp _).comp x hlin
  convert hcomp using 1
  ring

theorem phase_deriv_t (k c x t : ℝ) :
    HasDerivAt (fun y => phase k c x y) (phase k c x t * (-(c * k))) t := by
  unfold phase
  have hsub : HasDerivAt (fun y => x - c * y) (-(c * 1)) t := by
    simpa using (hasDerivAt_const t x).sub ((hasDerivAt_id t).const_mul c)
  have hlin : HasDerivAt (fun y => k * (x - c * y)) (k * -(c * 1)) t := hsub.const_mul k
  have hcomp := (Real.hasDerivAt_exp _).comp t hlin
  convert hcomp using 1
  ring

/-! ## Производные U -/

theorem hasDerivAt_U (c s : ℝ) : HasDerivAt (U c) (U1 c s) s := by
  have hfun : (U c) = fun y : ℝ => (2 * c) * (y * y) / ((1 + y * y) * (1 + y * y)) := by
    funext y; unfold U; ring
  rw [hfun]
  have hx2 : HasDerivAt (fun y : ℝ => y * y) (s + s) s := by
    simpa using (hasDerivAt_id s).mul (hasDerivAt_id s)
  have hD : HasDerivAt (fun y : ℝ => 1 + y * y) (s + s) s := by
    simpa using (hasDerivAt_const s 1).add hx2
  have hf : HasDerivAt (fun y : ℝ => (2 * c) * (y * y)) ((2 * c) * (s + s)) s :=
    hx2.const_mul (2 * c)
  have hg := hD.mul hD
  have hne : (1:ℝ) + s * s ≠ 0 := by
    intro h
    linarith [sq_nonneg s]
  have hne2 : (1 + s * s) * (1 + s * s) ≠ 0 := mul_ne_zero hne hne
  exact hasDerivAt_congr_value (HasDerivAt.div hf hg hne2) (by
    unfold U1; field_simp [hne]; ring)

theorem hasDerivAt_U1 (c s : ℝ) : HasDerivAt (U1 c) (U2 c s) s := by
  have hfun : (U1 c) = fun y : ℝ =>
      (4 * c) * (y * (1 - y * y)) / ((1 + y * y) * ((1 + y * y) * (1 + y * y))) := by
    funext y; unfold U1; ring
  rw [hfun]
  have hx2 : HasDerivAt (fun y : ℝ => y * y) (s + s) s := by
    simpa using (hasDerivAt_id s).mul (hasDerivAt_id s)
  have hD : HasDerivAt (fun y : ℝ => 1 + y * y) (s + s) s := by
    simpa using (hasDerivAt_const s 1).add hx2
  have hneg2 : HasDerivAt (fun y : ℝ => 1 - y * y) (-(s + s)) s := by
    simpa using (hasDerivAt_const s 1).sub hx2
  have hy : HasDerivAt (fun y : ℝ => y * (1 - y * y)) (1 * (1 - s * s) + s * (-(s + s))) s :=
    (hasDerivAt_id s).mul hneg2
  have hf := hy.const_mul (4 * c)
  have hg := hD.mul (hD.mul hD)
  have hne : (1:ℝ) + s * s ≠ 0 := by
    intro h
    linarith [sq_nonneg s]
  have hne2 : (1 + s * s) * ((1 + s * s) * (1 + s * s)) ≠ 0 :=
    mul_ne_zero hne (mul_ne_zero hne hne)
  exact hasDerivAt_congr_value (HasDerivAt.div hf hg hne2) (by
    unfold U2; field_simp [hne]; ring)

theorem hasDerivAt_U2 (c s : ℝ) : HasDerivAt (U2 c) (U3 c s) s := by
  have hfun : (U2 c) = fun y : ℝ =>
      (4 * c) * (1 - 8 * (y * y) + 3 * ((y * y) * (y * y)))
        / (((1 + y * y) * (1 + y * y)) * ((1 + y * y) * (1 + y * y))) := by
    funext y; unfold U2; ring
  rw [hfun]
  have hx2 : HasDerivAt (fun y : ℝ => y * y) (s + s) s := by
    simpa using (hasDerivAt_id s).mul (hasDerivAt_id s)
  have hD : HasDerivAt (fun y : ℝ => 1 + y * y) (s + s) s := by
    simpa using (hasDerivAt_const s 1).add hx2
  have h8 : HasDerivAt (fun y : ℝ => 8 * (y * y)) (8 * (s + s)) s := hx2.const_mul 8
  have h3 : HasDerivAt (fun y : ℝ => 3 * ((y * y) * (y * y)))
      (3 * ((s + s) * (s * s) + (s * s) * (s + s))) s := (hx2.mul hx2).const_mul 3
  have hf := (((hasDerivAt_const s 1).sub h8).add h3).const_mul (4 * c)
  have hD2 : HasDerivAt (fun y : ℝ => (1 + y * y) * (1 + y * y))
      ((s + s) * (1 + s * s) + (1 + s * s) * (s + s)) s := hD.mul hD
  have hg := hD2.mul hD2
  have hne : (1:ℝ) + s * s ≠ 0 := by
    intro h
    linarith [sq_nonneg s]
  have hne2 : ((1 + s * s) * (1 + s * s)) * ((1 + s * s) * (1 + s * s)) ≠ 0 :=
    mul_ne_zero (mul_ne_zero hne hne) (mul_ne_zero hne hne)
  exact hasDerivAt_congr_value (HasDerivAt.div hf hg hne2) (by
    unfold U3; field_simp [hne]; ring)

/-! ## Производные солитона по x -/

/-- Значения производных по x (первая, вторая, третья). -/
def dSolitonX1 (c k x t : ℝ) : ℝ :=
  U1 c (phase k c x t) * (phase k c x t * k)

def dSolitonX2 (c k x t : ℝ) : ℝ :=
  U2 c (phase k c x t) * (phase k c x t * k) * (phase k c x t * k)
  + U1 c (phase k c x t) * ((phase k c x t * k) * k)

def dSolitonX3 (c k x t : ℝ) : ℝ :=
  U3 c (phase k c x t) * (phase k c x t * k) * (phase k c x t * k) * (phase k c x t * k)
  + U2 c (phase k c x t) * ((phase k c x t * k) * k) * (phase k c x t * k)
  + U2 c (phase k c x t) * (phase k c x t * k) * ((phase k c x t * k) * k)
  + U2 c (phase k c x t) * (phase k c x t * k) * ((phase k c x t * k) * k)
  + U1 c (phase k c x t) * (((phase k c x t * k) * k) * k)

theorem hasDerivAt_solitonK_x (c k x t : ℝ) :
    HasDerivAt (fun y => solitonK c k y t) (dSolitonX1 c k x t) x := by
  have hEq : (fun y => solitonK c k y t) = fun y => U c (phase k c y t) := by
    funext y; exact solitonK_eq_U c k y t
  rw [hEq]
  exact (hasDerivAt_U c (phase k c x t)).comp x (phase_deriv_x k c t x)

theorem hasDerivAt_dSolitonX1 (c k t x : ℝ) :
    HasDerivAt (fun y => dSolitonX1 c k y t) (dSolitonX2 c k x t) x := by
  unfold dSolitonX1 dSolitonX2
  have hE := phase_deriv_x k c t x
  have hp : HasDerivAt (fun y => phase k c y t * k) ((phase k c x t * k) * k) x :=
    HasDerivAt.mul_const hE k
  have hU1 : HasDerivAt (fun y => U1 c (phase k c y t))
      (U2 c (phase k c x t) * (phase k c x t * k)) x :=
    (hasDerivAt_U1 c (phase k c x t)).comp x hE
  exact hasDerivAt_congr_value (hU1.mul hp) (by ring)

theorem hasDerivAt_dSolitonX2 (c k t x : ℝ) :
    HasDerivAt (fun y => dSolitonX2 c k y t) (dSolitonX3 c k x t) x := by
  unfold dSolitonX2 dSolitonX3
  have hE := phase_deriv_x k c t x
  have hp : HasDerivAt (fun y => phase k c y t * k) ((phase k c x t * k) * k) x :=
    HasDerivAt.mul_const hE k
  have hpk : HasDerivAt (fun y => (phase k c y t * k) * k)
      (((phase k c x t * k) * k) * k) x := HasDerivAt.mul_const hp k
  have hU2 : HasDerivAt (fun y => U2 c (phase k c y t))
      (U3 c (phase k c x t) * (phase k c x t * k)) x :=
    (hasDerivAt_U2 c (phase k c x t)).comp x hE
  have hU1 : HasDerivAt (fun y => U1 c (phase k c y t))
      (U2 c (phase k c x t) * (phase k c x t * k)) x :=
    (hasDerivAt_U1 c (phase k c x t)).comp x hE
  exact hasDerivAt_congr_value ((hU2.mul hp).mul hp |>.add (hU1.mul hpk)) (by ring)

/-- Уровень производных по времени. -/
def dSolitonT1 (c k x t : ℝ) : ℝ :=
  U1 c (phase k c x t) * (phase k c x t * (-(c * k)))

theorem hasDerivAt_solitonK_t (c k x t : ℝ) :
    HasDerivAt (fun y => solitonK c k x y) (dSolitonT1 c k x t) t := by
  have hEq : (fun y => solitonK c k x y) = fun y => U c (phase k c x y) := by
    funext y; exact solitonK_eq_U c k x y
  rw [hEq]
  exact (hasDerivAt_U c (phase k c x t)).comp t (phase_deriv_t k c x t)

/-! ## Функциональные уравнения для переписывания вложенных deriv -/

theorem deriv_solitonK_x (c k t : ℝ) :
    deriv (fun y => solitonK c k y t) = fun y => dSolitonX1 c k y t := by
  funext y
  exact HasDerivAt.deriv (hasDerivAt_solitonK_x c k y t)

theorem deriv_solitonK_xx (c k t : ℝ) :
    deriv (fun y => dSolitonX1 c k y t) = fun y => dSolitonX2 c k y t := by
  funext y
  exact HasDerivAt.deriv (hasDerivAt_dSolitonX1 c k t y)

theorem deriv_dSolitonX2 (c k t x : ℝ) :
    deriv (fun y => dSolitonX2 c k y t) x = dSolitonX3 c k x t :=
  HasDerivAt.deriv (hasDerivAt_dSolitonX2 c k t x)

/-! ## Главная теорема: солитон решает KdV -/

/-- ★ Солитон с фазой `k` при `c = 4k²` — точное классическое решение
`u_t + 6·u·u_x + u_xxx = 0`. -/
theorem solitonK_solves_KdV (c k : ℝ) (hck : c = 4 * k ^ 2) :
    IsKdVSolution (solitonK c k) := by
  unfold IsKdVSolution
  intro x t
  rw [HasDerivAt.deriv (hasDerivAt_solitonK_t c k x t)]
  rw [HasDerivAt.deriv (hasDerivAt_solitonK_x c k x t)]
  rw [deriv_solitonK_x c k t]
  rw [deriv_solitonK_xx c k t]
  rw [deriv_dSolitonX2 c k t x]
  rw [solitonK_eq_U c k x t]
  unfold dSolitonT1 dSolitonX1 dSolitonX3 U U1 U2 U3
  set s : ℝ := phase k c x t with hsdef
  rw [hck]
  have hne : (1:ℝ) + s ^ 2 ≠ 0 := by nlinarith [sq_nonneg s]
  field_simp [hne]
  ring

/-- ★ КЛАССИЧЕСКИЙ СОЛИТОН РЕШАЕТ KdV: функция
`u(x,t) = (c/2)·sech²(√c/2·(x − ct))` при `c > 0` — точное классическое
решение `u_t + 6·u·u_x + u_xxx = 0`. -/
theorem soliton_solves_KdV (c : ℝ) (hc : 0 < c) : IsKdVSolution (soliton c) := by
  have hksq : c = 4 * (Real.sqrt c / 2) ^ 2 := by
    calc c = Real.sqrt c ^ 2 := (Real.sq_sqrt (le_of_lt hc)).symm
      _ = 4 * (Real.sqrt c / 2) ^ 2 := by ring
  unfold soliton
  exact solitonK_solves_KdV c _ hksq

end Verification.KdV
