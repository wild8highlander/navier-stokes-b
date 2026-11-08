import ResearchPapersVerification.Common.Foundation
import ResearchPapersVerification.Section1_CorrectionB.Basic
import Mathlib.Tactic
import Mathlib.Data.Real.Pi.Bounds
import Mathlib.Analysis.SpecialFunctions.Trigonometric.Deriv
import Mathlib.Analysis.SpecialFunctions.Log.Deriv
import Mathlib.Analysis.Calculus.Deriv.Slope
import Mathlib.MeasureTheory.Integral.IntervalIntegral

/-!
# Идеальная форма торможения завихрения и распределённое торможение ствола

Формализация в точности machinery `verification/code/tg2d_core.py` (уровень L4):

* одна фурье-мода 2D-поля — пара амплитуд `(û₀, û₁) ∈ ℂ²` при волновом векторе `(k₀, k₁)`;
* проекция Лерэ на моде `P(u) = u − (k·u/|k|²)·k` (метод `div_free`);
* завихренность моды `ω̂(u) = i(k₀û₁ − k₁û₀)` (метод `curl_h`);
* b-поворот значений `R(u) = (c·u₀ − s·u₁, s·u₀ + c·u₁)` с `c = cos φ, s = sin φ`,
  `φ = dt·θ_b` (метод `integrate`, строки 114–116);
* шаг протокола `brakingStep u = P(R u)`.

Ключевая теорема (`vort_brakingStep_div_free`) — «идеальная форма торможения»:
для ЛЮБОЙ бездивергентной моды (т.е. для любого решения с любыми свободными
параметрами U, k, ν, фаза) шаг протокола умножает завихренность моды точно на
`cos φ`. Никаких ручных коэффициентов: k, u, c, s — универсально квантифицированы.

Далее: N-шаговая композиция (`vort_brakingIter`), энергия (поворот норму хранит,
Лерэ только убирает — «инъекции энергии нет», критерий P1/C4), замкнутая форма
BKM-фактора P2, агрегация до конечных суперпозиций мод (`ModeSuperpos` —
коэффициент торможения не зависит от k, поэтому сумма мод тормозит как целое),
связка с моделью распределённого торможения ствола `dτ/ds = −γ(s)·ω(s)`,
`τ = −γΓ` при синхронизации `γ(s) = γ₀`.

Честность терминологии: `sin θ_b = 1/(4π + 2√3)` — это тождество двух записей
ОДНОГО определения `bCorrection` плюс `sin(arcsin b) = b`. Вывод самой константы
b из геометрии относительных равновесий Кирхгофа здесь НЕ формализован (это
отдельная задача). `protocol_ode_form` — тождество при фиксированном dt, а не
вывод ODE: γ_eff(dt) = −log cos(dt·θ_b)/dt зависит от dt и → 0 при dt → 0.
-/ 

noncomputable section
open Real Complex ResearchPapersVerification

namespace Braking2D

/-! ## Моды 2D поля: амплитуды и операции -/

/-- Скалярное произведение волнового вектора на амплитуду моды:
`k·û = k₀û₀ + k₁û₁` (дивергенция моды; в `tg2d_core.py` — метод `div_free`). -/
def modeDot (k₀ k₁ : ℂ) (u : ℂ × ℂ) : ℂ := k₀ * u.1 + k₁ * u.2

/-- Квадрат волнового числа `|k|²` (в мультипликативной форме — для `ring`). -/
def K2c (k₀ k₁ : ℂ) : ℂ := k₀ * k₀ + k₁ * k₁

/-- Проекция Лерэ на одной моде (`tg2d_core.div_free`, строки 39–41):
`P(u) = u − (k·u/|k|²)·k`. -/
def leray (k₀ k₁ : ℂ) (u : ℂ × ℂ) : ℂ × ℂ :=
  (u.1 - modeDot k₀ k₁ u * (k₀ / K2c k₀ k₁),
   u.2 - modeDot k₀ k₁ u * (k₁ / K2c k₀ k₁))

/-- Поворот значений моды на угол φ с `c = cos φ, s = sin φ`
(`tg2d_core.py`, строки 114–116: b-поворот в спектральных коэффициентах). -/
def rotVal (c s : ℝ) (u : ℂ × ℂ) : ℂ × ℂ :=
  ((c : ℂ) * u.1 - (s : ℂ) * u.2, (s : ℂ) * u.1 + (c : ℂ) * u.2)

/-- Завихренность моды: `ω̂ = i(k₀û₁ − k₁û₀)` (`tg2d_core.curl_h`, строка 66). -/
def vort (k₀ k₁ : ℂ) (u : ℂ × ℂ) : ℂ :=
  Complex.I * (k₀ * u.2) - Complex.I * (k₁ * u.1)

/-- Один шаг b-протокола: поворот значений + перепроекция Лерэ. -/
def brakingStep (c s : ℝ) (k₀ k₁ : ℂ) (u : ℂ × ℂ) : ℂ × ℂ :=
  leray k₀ k₁ (rotVal c s u)

/-- Энергия моды: `E(û) = |û₀|² + |û₁|²`. -/
def energy (u : ℂ × ℂ) : ℝ := Complex.normSq u.1 + Complex.normSq u.2

/-- Вспомогательное: сопряжение вещественной амплитуды поворота. -/
theorem conj_rot (c : ℝ) : starRingEnd ℂ (c : ℂ) = (c : ℂ) := Complex.conj_ofReal c

/-- Вспомогательное: `|z|² = Re(z·conj z)` — мост от `normSq` к произведениям. -/
theorem normSq_eq_re_mul_conj (z : ℂ) :
    Complex.normSq z = Complex.re (z * starRingEnd ℂ z) := by
  rw [Complex.mul_re, Complex.conj_re, Complex.conj_im, Complex.normSq_apply]
  ring

/-! ## Алгебра мод: проекция Лерэ -/

theorem leray_div_free (k₀ k₁ : ℂ) (hk2 : K2c k₀ k₁ ≠ 0) (u : ℂ × ℂ) :
    modeDot k₀ k₁ (leray k₀ k₁ u) = 0 := by
  rw [K2c] at hk2
  field_simp [modeDot, leray, K2c]
  ring

theorem vort_leray (k₀ k₁ : ℂ) (hk2 : K2c k₀ k₁ ≠ 0) (u : ℂ × ℂ) :
    vort k₀ k₁ (leray k₀ k₁ u) = vort k₀ k₁ u := by
  rw [K2c] at hk2
  field_simp [vort, leray, modeDot, K2c]
  ring

/-! ## Общая форма шага протокола -/

/-- Общая форма (A3): шаг протокола на произвольной моде — без предположений
о дивергенции; годится для любого угла (c, s) — не обязательно косинус/синус. -/
theorem vort_brakingStep (c s : ℝ) (k₀ k₁ : ℂ) (hk2 : K2c k₀ k₁ ≠ 0) (u : ℂ × ℂ) :
    vort k₀ k₁ (brakingStep c s k₀ k₁ u)
      = (c : ℂ) * vort k₀ k₁ u + (s : ℂ) * Complex.I * modeDot k₀ k₁ u := by
  rw [brakingStep, vort_leray k₀ k₁ hk2]
  simp only [vort, rotVal, modeDot]
  ring

/-- ★ ИДЕАЛЬНАЯ ФОРМА ТОРМОЖЕНИЯ (A4): на бездивергентной моде шаг протокола
умножает завихренность точно на `c = cos φ`. Параметры k, u, c, s свободны —
это утверждение обо ВСЕХ решениях со всеми (U, k, ν, фаза) сразу. -/
theorem vort_brakingStep_div_free (c s : ℝ) (k₀ k₁ : ℂ) (hk2 : K2c k₀ k₁ ≠ 0)
    (u : ℂ × ℂ) (hdf : modeDot k₀ k₁ u = 0) :
    vort k₀ k₁ (brakingStep c s k₀ k₁ u) = (c : ℂ) * vort k₀ k₁ u := by
  rw [vort_brakingStep c s k₀ k₁ hk2 u, hdf]
  ring

/-- Шаг протокола сохраняет бездивергентность (повторная проекция Лерэ). -/
theorem brakingStep_div_free (c s : ℝ) (k₀ k₁ : ℂ) (hk2 : K2c k₀ k₁ ≠ 0) (u : ℂ × ℂ) :
    modeDot k₀ k₁ (brakingStep c s k₀ k₁ u) = 0 :=
  leray_div_free k₀ k₁ hk2 _

/-- Смена вида `k·R(u)`: поворот вектора значений = обратный поворот вектора k (A8). -/
theorem modeDot_rotVal (c s : ℝ) (k₀ k₁ : ℂ) (u : ℂ × ℂ) :
    modeDot k₀ k₁ (rotVal c s u)
      = ((c : ℂ) * k₀ + (s : ℂ) * k₁) * u.1
        + ((c : ℂ) * k₁ - (s : ℂ) * k₀) * u.2 := by
  simp only [modeDot, rotVal]
  ring

/-! ## N-шаговая композиция протокола -/

/-- M-кратный шаг b-протокола (`φ = dt·θ_b` на каждом шаге — как в `integrate`). -/
def brakingIter (c s : ℝ) (k₀ k₁ : ℂ) : ℕ → ℂ × ℂ → ℂ × ℂ
  | 0, u => u
  | (n + 1), u => brakingStep c s k₀ k₁ (brakingIter c s k₀ k₁ n u)

theorem brakingIter_div_free (c s : ℝ) (k₀ k₁ : ℂ) (hk2 : K2c k₀ k₁ ≠ 0)
    (u : ℂ × ℂ) (hdf : modeDot k₀ k₁ u = 0) (n : ℕ) :
    modeDot k₀ k₁ (brakingIter c s k₀ k₁ n u) = 0 := by
  induction n with
  | zero => exact hdf
  | succ n ih => exact brakingStep_div_free c s k₀ k₁ hk2 _

/-- ★ N-шаговая композиция: после M шагов протокола завихренность моды равна
`cos^M φ · ω̂₀` — точная мультипликативная форма торможения. -/
theorem vort_brakingIter (c s : ℝ) (k₀ k₁ : ℂ) (hk2 : K2c k₀ k₁ ≠ 0)
    (u : ℂ × ℂ) (hdf : modeDot k₀ k₁ u = 0) (n : ℕ) :
    vort k₀ k₁ (brakingIter c s k₀ k₁ n u) = (c : ℂ) ^ n * vort k₀ k₁ u := by
  induction n with
  | zero => simp [brakingIter]
  | succ n ih =>
    simp only [brakingIter]
    rw [vort_brakingStep_div_free c s k₀ k₁ hk2 _
      (brakingIter_div_free c s k₀ k₁ hk2 u hdf n), ih, pow_succ]
    ring

/-! ## Энергия: поворот норму хранит, Лерэ только убирает -/

/-- Преобразование суммы квадратов вещественных параметров поворота в ℂ. -/
theorem ofReal_sq_mul_sum {c s : ℝ} (hcs : c ^ 2 + s ^ 2 = 1) :
    (c : ℂ) * (c : ℂ) + (s : ℂ) * (s : ℂ) = 1 := by
  have h1 : ((c : ℂ) * (c : ℂ) : ℂ) = ((c ^ 2 : ℝ) : ℂ) := by
    rw [pow_two, ← Complex.ofReal_mul]
  have h2 : ((s : ℂ) * (s : ℂ) : ℂ) = ((s ^ 2 : ℝ) : ℂ) := by
    rw [pow_two, ← Complex.ofReal_mul]
  rw [h1, h2, ← Complex.ofReal_add, ← Complex.ofReal_one]
  exact congrArg Complex.ofReal (by linarith [hcs])

/-- Поворот значений хранит энергию моды при `c² + s² = 1` (A6). -/
theorem rot_energy (c s : ℝ) (hcs : c ^ 2 + s ^ 2 = 1) (u : ℂ × ℂ) :
    energy (rotVal c s u) = energy u := by
  simp only [energy, rotVal, normSq_eq_re_mul_conj, map_sub, map_add, map_mul,
    conj_rot, Complex.mul_re, Complex.mul_im, Complex.add_re, Complex.sub_re,
    Complex.add_im, Complex.sub_im, Complex.ofReal_re, Complex.ofReal_im,
    Complex.conj_re, Complex.conj_im]
  linear_combination (norm := ring_nf) hcs *
    (u.1.re ^ 2 + u.1.im ^ 2 + u.2.re ^ 2 + u.2.im ^ 2)

/-- Лерэ-проекция убирает ровно `|k·u|²/|k|²` энергии (умноженная на |k|² форма,
для вещественного волнового вектора). -/
theorem leray_energy_mul (k₀ k₁ : ℝ) (hK2 : (k₀ * k₀ + k₁ * k₁ : ℝ) ≠ 0) (u : ℂ × ℂ) :
    ((energy (leray (k₀ : ℂ) (k₁ : ℂ) u) : ℂ)) * ((k₀ * k₀ + k₁ * k₁ : ℝ) : ℂ)
      = ((energy u : ℂ)) * ((k₀ * k₀ + k₁ * k₁ : ℝ) : ℂ)
        - ((Complex.normSq (modeDot (k₀ : ℂ) (k₁ : ℂ) u) : ℝ) : ℂ) := by
  have hK2c : ((k₀ * k₀ + k₁ * k₁ : ℝ) : ℂ) = K2c (k₀ : ℂ) (k₁ : ℂ) := by
    rw [K2c]; push_cast; ring
  have hk2' : ((k₀ : ℂ) ^ 2 + (k₁ : ℂ) ^ 2) ≠ 0 := by
    intro h
    have h2 := congrArg Complex.re h
    simp only [Complex.add_re, pow_two, Complex.mul_re, Complex.ofReal_re,
      Complex.ofReal_im, Complex.zero_re] at h2
    exact hK2 (by linarith)
  have hk2m : ((k₀ : ℂ) * (k₀ : ℂ) + (k₁ : ℂ) * (k₁ : ℂ)) ≠ 0 := by
    rw [← pow_two, ← pow_two]; exact hk2'
  rw [hK2c]
  simp only [energy, Complex.ofReal_add, ← Complex.mul_conj]
  field_simp [leray, modeDot, K2c, map_sub, map_add, map_mul, conj_rot]
  ring

/-- Разделённая форма: `E(P u) = E u − |k·u|²/|k|²` (для вещественного k). -/
theorem leray_energy (k₀ k₁ : ℝ) (hK2 : (k₀ * k₀ + k₁ * k₁ : ℝ) ≠ 0) (u : ℂ × ℂ) :
    energy (leray (k₀ : ℂ) (k₁ : ℂ) u)
      = energy u - Complex.normSq (modeDot (k₀ : ℂ) (k₁ : ℂ) u)
          / (k₀ * k₀ + k₁ * k₁) := by
  have h := leray_energy_mul k₀ k₁ hK2 u
  have hT : ((↑(k₀ * k₀) + ↑(k₁ * k₁) : ℂ)) ≠ 0 := by exact_mod_cast hK2
  refine Complex.ofReal_inj.mp (mul_right_cancel₀ hT ?_)
  simp only [Complex.ofReal_add, Complex.ofReal_sub, Complex.ofReal_div,
    ← Complex.mul_conj] at h ⊢
  rw [sub_mul, div_mul_cancel₀ _ hT]
  exact h

/-- ★ Шаг протокола не инжектирует энергию (критерий P1/C4): энергия после шага
равна `E − |k·R(u)|²/|k|² ≤ E` — уменьшение даёт только проекция Лерэ. -/
theorem brakingStep_energy (c s k₀ k₁ : ℝ) (hcs : c ^ 2 + s ^ 2 = 1)
    (hK2 : (k₀ * k₀ + k₁ * k₁ : ℝ) ≠ 0) (u : ℂ × ℂ) :
    energy (brakingStep c s (k₀ : ℂ) (k₁ : ℂ) u)
      = energy u - Complex.normSq (modeDot (k₀ : ℂ) (k₁ : ℂ) (rotVal c s u))
          / (k₀ * k₀ + k₁ * k₁) := by
  rw [brakingStep, leray_energy k₀ k₁ hK2 _, rot_energy c s hcs u]

theorem brakingStep_energy_le (c s k₀ k₁ : ℝ) (hcs : c ^ 2 + s ^ 2 = 1)
    (hK2 : (k₀ * k₀ + k₁ * k₁ : ℝ) ≠ 0) (u : ℂ × ℂ) :
    energy (brakingStep c s (k₀ : ℂ) (k₁ : ℂ) u) ≤ energy u := by
  rw [brakingStep_energy c s k₀ k₁ hcs hK2 u]
  exact sub_le_self _ (div_nonneg (Complex.normSq_nonneg _)
    (by nlinarith [sq_nonneg k₀, sq_nonneg k₁]))

/-! ## Замкнутая форма BKM-фактора (P2) -/

/-- Сумма геометрической прогрессии `c¹ + … + c^M` (нормировка BKM-фактора). -/
def geoSum (c : ℝ) (M : ℕ) : ℝ := ∑ i ∈ Finset.range M, c ^ (i + 1)

theorem geoSum_eq (c : ℝ) (hc : c ≠ 1) (M : ℕ) :
    geoSum c M = c * (1 - c ^ M) / (1 - c) := by
  induction M with
  | zero => simp [geoSum]
  | succ M ih =>
    rw [geoSum, Finset.sum_range_succ, ← geoSum, ih]
    have h1c : (1 : ℝ) - c ≠ 0 := sub_ne_zero.mpr (fun h => hc h.symm)
    field_simp
    ring

/-- Замкнутая форма BKM-фактора P2: `F = I_ω(b_on)/I_ω(b_off) = c(1−c^M)/(M(1−c))`,
`c = cos(dt·θ_b)` — в точности геометрическое среднее мультипликативного торможения. -/
theorem bkm_factor (c : ℝ) (hc : c ≠ 1) (M : ℕ) (hM : M ≠ 0) :
    geoSum c M / M = c * (1 - c ^ M) / ((M : ℝ) * (1 - c)) := by
  have hM' : (M : ℝ) ≠ 0 := by exact_mod_cast hM
  rw [geoSum_eq c hc M]
  field_simp
  ring

/-! ## Агрегация: конечные суперпозиции мод -/

/-- Конечная суперпозиция `n` бездивергентных мод: волновые векторы `(k j)` и
амплитуды `(u j)` (пары комплексных координат), каждая мода бездивергентна
и имеет ненулевой `\|k\|²`. -/
structure ModeSuperpos (n : ℕ) where
  k : Fin n → ℂ × ℂ
  u : Fin n → ℂ × ℂ
  hk2 : ∀ j, K2c (k j).1 (k j).2 ≠ 0
  hdf : ∀ j, modeDot (k j).1 (k j).2 (u j) = 0

/-- Суммарная завихрённость суперпозиции (коэффициент при 1/i·ω̂-части суммы). -/
def totalVort {n : ℕ} (S : ModeSuperpos n) : ℂ := ∑ j, vort (S.k j).1 (S.k j).2 (S.u j)

/-- Шаг протокола на суперпозиции: каждая мода поворачивается и перепроектируется
независимо — в точности как в `integrate`, коэффициент не зависит от k. -/
def stepSuperpos (c s : ℝ) {n : ℕ} (S : ModeSuperpos n) : ModeSuperpos n where
  k := S.k
  u := fun j => brakingStep c s (S.k j).1 (S.k j).2 (S.u j)
  hk2 := S.hk2
  hdf := fun j => brakingStep_div_free c s (S.k j).1 (S.k j).2 (S.hk2 j) _

/-- ★ Агрегация (шаг): суммарная завихрённость умножается точно на `cos φ` —
коэффициент торможения один для всех мод, поэтому суперпозиция тормозит
как целое (мост от одномодовой теоремы к сумме мод). -/
theorem vort_brakingStep_superpos (c s : ℝ) {n : ℕ} (S : ModeSuperpos n) :
    totalVort (stepSuperpos c s S) = (c : ℂ) * totalVort S := by
  unfold totalVort stepSuperpos
  rw [Finset.mul_sum]
  exact Finset.sum_congr rfl (fun j _ =>
    vort_brakingStep_div_free c s (S.k j).1 (S.k j).2 (S.hk2 j) _ (S.hdf j))

/-- M-кратный шаг протокола на суперпозиции. -/
def iterSuperpos (c s : ℝ) {n : ℕ} (m : ℕ) (S : ModeSuperpos n) : ModeSuperpos n :=
  match m with
  | 0 => S
  | (m + 1) => stepSuperpos c s (iterSuperpos c s m S)

/-- ★ Агрегация (M шагов): суммарная завихрённость суперпозиции после M шагов
равна `cosᴹφ · ω̂_total`. Ссылка на 3D: конечные суперпозиции — ряды Фурье
сходятся в L², так что тождество переносится на поля стандартной плотностью
конечных сумм; L²-теория здесь не формализуется. -/
theorem vort_brakingIter_superpos (c s : ℝ) {n : ℕ} (S : ModeSuperpos n) (m : ℕ) :
    totalVort (iterSuperpos c s m S) = (c : ℂ) ^ m * totalVort S := by
  induction m with
  | zero => simp [iterSuperpos]
  | succ m ih =>
    rw [iterSuperpos, vort_brakingStep_superpos, ih, pow_succ]
    ring

end Braking2D

/-! ## Протокол скриптов: угол θ_b = arcsin b -/

namespace Protocol
open Real Section1 Braking2D

/-- Угол поворота за шаг в протоколе скриптов: `φ = dt·θ_b`,
`θ_b = arcsin b`, `b = bCorrection` (`tg2d_core.py`: `B = 1/(4π+2√3)`). -/
theorem cos_sin_sq (φ : ℝ) : ((Real.cos φ : ℝ) : ℂ) ^ 2 + ((Real.sin φ : ℝ) : ℂ) ^ 2 = 1 := by
  have h1 : (((Real.cos φ : ℝ) : ℂ) ^ 2 : ℂ) = ((Real.cos φ ^ 2 : ℝ) : ℂ) := by
    rw [Complex.ofReal_pow]
  have h2 : (((Real.sin φ : ℝ) : ℂ) ^ 2 : ℂ) = ((Real.sin φ ^ 2 : ℝ) : ℂ) := by
    rw [Complex.ofReal_pow]
  rw [h1, h2, ← Complex.ofReal_add, ← Complex.ofReal_one]
  exact congrArg Complex.ofReal (by linarith [Real.sin_sq_add_cos_sq φ])

/-- Шаг протокола с `c = cos φ, s = sin φ` — в точности идеальная форма торможения. -/
theorem brakingStep_cos_sin (φ k₀ k₁ : ℝ) (u0 : ℂ × ℂ)
    (hK2 : K2c (k₀ : ℂ) (k₁ : ℂ) ≠ 0)
    (hdf : modeDot (k₀ : ℂ) (k₁ : ℂ) u0 = 0) :
    vort (k₀ : ℂ) (k₁ : ℂ) (brakingStep (Real.cos φ) (Real.sin φ) (k₀ : ℂ) (k₁ : ℂ) u0)
      = (Real.cos φ : ℂ) * vort (k₀ : ℂ) (k₁ : ℂ) u0 :=
  vort_brakingStep_div_free (Real.cos φ) (Real.sin φ) (k₀ : ℂ) (k₁ : ℂ) hK2 u0 hdf

/-- Для `φ ∈ (0, π/2)` косинус положителен — торможение в правильную сторону. -/
theorem cos_pos {φ : ℝ} (h1 : -(π / 2) < φ) (h2 : φ < π / 2) : 0 < Real.cos φ :=
  Real.cos_pos_of_mem_Ioo ⟨h1, h2⟩

/-- Строгое торможение: `cos φ < 1` для `φ ∈ (0, π)` (`StrictAntiOn cos`). -/
theorem cos_lt_one {φ : ℝ} (h1 : 0 < φ) (h2 : φ ≤ π) : Real.cos φ < 1 := by
  have h := Real.strictAntiOn_cos
    (Set.mem_Icc.mpr ⟨le_refl 0, le_of_lt (by linarith [Real.pi_pos])⟩)
    (Set.mem_Icc.mpr ⟨le_of_lt h1, h2⟩) h1
  rwa [Real.cos_zero] at h

/-- Положительность угла за шаг: `θ_b = arcsin bCorrection > 0`. -/
theorem theta_b_pos : 0 < θ_b := Real.arcsin_pos.mpr bCorrection_pos

/-- Степень косинуса убывает: `cos^n φ < 1` при `n ≠ 0` — торможение строгое
(для φ из диапазона протокола `0 < φ < π/2`). -/
theorem pow_cos_lt_one {φ : ℝ} (h1 : 0 < φ) (h2 : φ < π / 2) {n : ℕ} (hn : n ≠ 0) :
    (Real.cos φ) ^ n < 1 :=
  pow_lt_one₀ (le_of_lt (cos_pos (by linarith [Real.pi_pos, h1]) h2))
    (cos_lt_one h1 (by linarith [h2, Real.pi_pos])) hn

/-- Эффективная скорость торможения протокола. ВАЖНО: γ_eff зависит от dt;
разложение log(cos x) = −x²/2 − x⁴/12 − … даёт γ_eff(dt) = dt·θ_b²/2 + dt³·θ_b⁴/12 + …,
поэтому γ_eff(dt) → 0 при dt → 0: непрерывного предела протокола с постоянной γ
НЕ существует (за фиксированное время T торможение exp(−γ_eff·T) → 1). -/
def gammaEff (dt : ℝ) : ℝ := -(Real.log (Real.cos (dt * θ_b))) / dt

/-- Тождество при ФИКСИРОВАННОМ dt: `cos^M(dt·θ_b) = exp(−γ_eff·M·dt)` —
это переопределение γ_eff (проверка согласованности протокола с моделью
`∂_tω = −γ·ω`), а НЕ вывод ODE как непрерывного предела: при dt → 0
γ_eff → 0 и торможение исчезает (см. `gammaEff`). -/
theorem protocol_ode_form {dt : ℝ} (hdt : 0 < dt) (hφ1 : -(π / 2) < dt * θ_b)
    (hφ2 : dt * θ_b < π / 2) (M : ℕ) :
    (Real.cos (dt * θ_b)) ^ M
      = Real.exp (-((gammaEff dt) * (M * dt))) := by
  have hc : 0 < Real.cos (dt * θ_b) := cos_pos hφ1 hφ2
  have hcM : 0 < (Real.cos (dt * θ_b)) ^ M := pow_pos hc M
  rw [← Real.exp_log hcM, Real.log_pow]
  have hdt' : dt ≠ 0 := ne_of_gt hdt
  congr 1
  field_simp [gammaEff]
  ring

/-- Эффективная скорость торможения протокола положительна. -/
theorem gammaEff_pos {dt : ℝ} (hdt : 0 < dt) (hφ1 : -(π / 2) < dt * θ_b)
    (hφ2 : dt * θ_b < π / 2) : 0 < gammaEff dt := by
  have hc : 0 < Real.cos (dt * θ_b) := cos_pos hφ1 hφ2
  have hlt : Real.cos (dt * θ_b) < 1 :=
    cos_lt_one (mul_pos hdt theta_b_pos) (by linarith [hφ2, Real.pi_pos])
  have hlog : Real.log (Real.cos (dt * θ_b)) < 0 := Real.log_neg hc hlt
  unfold gammaEff
  exact div_pos (by linarith) hdt

/-! ## Предел γ_eff(dt)/dt при dt → 0⁺: половинно-угловая цепочка -/

/-- Умножение на ненулевую константу сохраняет проколотую окрестность нуля. -/
theorem tendsto_mul_const_nhdsWithin_ne {c : ℝ} (hc : c ≠ 0) :
    Filter.Tendsto (fun x : ℝ => x * c) (nhdsWithin 0 {0}ᶜ) (nhdsWithin 0 {0}ᶜ) := by
  intro S hS
  rw [Filter.mem_map]
  obtain ⟨ε, hε, hSε⟩ := Metric.mem_nhdsWithin_iff.mp hS
  have hcpos : 0 < |c| := abs_pos.mpr hc
  have hnear : ∀ᶠ x in nhdsWithin 0 {0}ᶜ, x ∈ Metric.ball (0:ℝ) (ε / |c|) :=
    Filter.eventually_of_mem
      (mem_nhdsWithin_of_mem_nhds (Metric.ball_mem_nhds 0 (by positivity : 0 < ε / |c|)))
      (fun x hx => hx)
  filter_upwards [hnear, self_mem_nhdsWithin] with x hball hx
  have hx0 : x ≠ 0 := hx
  have h2 : |x| < ε / |c| := by simpa using Metric.mem_ball.mp hball
  refine hSε ⟨?_, by simpa using mul_ne_zero hx0 hc⟩
  rw [Metric.mem_ball, Real.dist_eq, sub_zero, abs_mul]
  exact (lt_div_iff₀ hcpos).mp h2

/-- A: sin x / x → 1. -/
theorem tendsto_sin_div_at_zero :
    Filter.Tendsto (fun x : ℝ => Real.sin x / x) (nhdsWithin 0 {0}ᶜ) (nhds 1) := by
  have h : HasDerivAt Real.sin (Real.cos 0) 0 := Real.hasDerivAt_sin 0
  rw [Real.cos_zero] at h
  have hs := hasDerivAt_iff_tendsto_slope.mp h
  have hEq : (slope Real.sin 0) = fun y : ℝ => Real.sin y / y := by
    funext y
    simp [slope_def_module, Real.sin_zero]
    ring
  rw [hEq] at hs
  exact hs

/-- C: x/2 сохраняет проколотую окрестность нуля. -/
theorem tendsto_half_nhdsWithin :
    Filter.Tendsto (fun x : ℝ => x / 2) (nhdsWithin 0 {0}ᶜ) (nhdsWithin 0 {0}ᶜ) := by
  intro S hS
  rw [Filter.mem_map]
  obtain ⟨ε, hε, hSε⟩ := Metric.mem_nhdsWithin_iff.mp hS
  have hnear : ∀ᶠ x in nhdsWithin 0 {0}ᶜ, x ∈ Metric.ball (0:ℝ) ε :=
    Filter.eventually_of_mem (mem_nhdsWithin_of_mem_nhds (Metric.ball_mem_nhds 0 hε))
      (fun x hx => hx)
  filter_upwards [hnear, self_mem_nhdsWithin] with x hball hx
  have hx0 : x ≠ 0 := hx
  have h2 : |x| < ε := by simpa using Metric.mem_ball.mp hball
  refine hSε ⟨?_, by simpa using div_ne_zero hx0 two_ne_zero⟩
  rw [Metric.mem_ball, Real.dist_eq, sub_zero, abs_div]
  have h22 : |(2:ℝ)| = 2 := abs_of_pos two_pos
  rw [h22]
  linarith

/-- D: sin(x/2)/(x/2) → 1. -/
theorem tendsto_sin_half_div_half :
    Filter.Tendsto (fun x : ℝ => Real.sin (x / 2) / (x / 2))
      (nhdsWithin 0 {0}ᶜ) (nhds 1) := by
  have h := tendsto_sin_div_at_zero.comp tendsto_half_nhdsWithin
  simpa [Function.comp_def] using h

/-- B+E: (1−cos x)/x² = (1/2)·(sin(x/2)/(x/2))². -/
theorem one_sub_cos_div_sq_eq (x : ℝ) (hx : x ≠ 0) :
    (1 - Real.cos x) / x ^ 2 = (1 / 2) * (Real.sin (x / 2) / (x / 2)) ^ 2 := by
  have hcm : Real.cos x = 2 * Real.cos (x / 2) ^ 2 - 1 := by
    rw [← Real.cos_two_mul (x / 2)]; ring
  have h1 := Real.sin_sq_add_cos_sq (x / 2)
  have hsq : 1 - Real.cos x = 2 * Real.sin (x / 2) ^ 2 := by linarith
  rw [hsq]
  field_simp [hx]
  ring

/-- F: (1−cos x)/x² → 1/2. -/
theorem tendsto_one_sub_cos_div_sq :
    Filter.Tendsto (fun x : ℝ => (1 - Real.cos x) / x ^ 2)
      (nhdsWithin 0 {0}ᶜ) (nhds (1 / 2)) := by
  have h1 := tendsto_sin_half_div_half
  have hv : ((1 / 2 : ℝ)) = (1 / 2) * ((1:ℝ) * (1:ℝ)) := by ring
  rw [hv]
  have hEq : (fun x : ℝ => (1 / 2) * ((Real.sin (x / 2) / (x / 2)) * (Real.sin (x / 2) / (x / 2))))
      =ᶠ[nhdsWithin 0 {0}ᶜ] (fun x : ℝ => (1 - Real.cos x) / x ^ 2) := by
    filter_upwards [self_mem_nhdsWithin] with x hx
    rw [one_sub_cos_div_sq_eq x hx]
    ring
  have hcst : Filter.Tendsto (fun _ : ℝ => ((1 / 2 : ℝ))) (nhdsWithin 0 {0}ᶜ)
      (nhds ((1 / 2 : ℝ))) := tendsto_const_nhds
  exact Filter.Tendsto.congr' hEq (hcst.mul (h1.mul h1))

/-- G: log y/(y−1) → 1. -/
theorem tendsto_log_div_sub_one :
    Filter.Tendsto (fun y : ℝ => Real.log y / (y - 1)) (nhdsWithin 1 {1}ᶜ) (nhds 1) := by
  have h : HasDerivAt Real.log ((1:ℝ)⁻¹) 1 := Real.hasDerivAt_log one_ne_zero
  have hs := hasDerivAt_iff_tendsto_slope.mp h
  have hEq : (slope Real.log 1) = fun y : ℝ => Real.log y / (y - 1) := by
    funext y
    simp [slope_def_module, Real.log_one]
    ring
  rw [hEq] at hs
  simpa using hs

/-- H: cos → 1 и cos x ≠ 1 на проколотой окрестности. -/
theorem tendsto_cos_nhdsWithin_one :
    Filter.Tendsto Real.cos (nhdsWithin 0 {0}ᶜ) (nhdsWithin 1 {1}ᶜ) := by
  rw [tendsto_nhdsWithin_iff]
  refine ⟨?_, ?_⟩
  · have h1 : Filter.Tendsto Real.cos (nhds 0) (nhds (Real.cos 0)) :=
      Real.continuous_cos.continuousAt.tendsto
    rw [Real.cos_zero] at h1
    exact h1.mono_left nhdsWithin_le_nhds
  · have hball : Metric.ball (0:ℝ) (2 * π) ∈ nhds 0 := Metric.ball_mem_nhds 0 two_pi_pos
    filter_upwards [mem_nhdsWithin_of_mem_nhds hball, self_mem_nhdsWithin] with x hxb hx
    have habs : |x| < 2 * π := by simpa using Metric.mem_ball.mp hxb
    obtain ⟨hx₁, hx₂⟩ := abs_lt.mp habs
    intro hc
    exact hx (Real.cos_eq_one_iff_of_lt_of_lt hx₁ hx₂ |>.mp (by simpa using hc))

/-- G∘H: log(cos x)/(cos x−1) → 1. -/
theorem tendsto_log_cos_div_sub_one :
    Filter.Tendsto (fun x : ℝ => Real.log (Real.cos x) / (Real.cos x - 1))
      (nhdsWithin 0 {0}ᶜ) (nhds 1) := by
  have h := tendsto_log_div_sub_one.comp tendsto_cos_nhdsWithin_one
  simpa [Function.comp_def] using h

/-- I: log(cos x)/x² → −1/2. -/
theorem tendsto_log_cos_div_sq :
    Filter.Tendsto (fun x : ℝ => Real.log (Real.cos x) / x ^ 2)
      (nhdsWithin 0 {0}ᶜ) (nhds (-(1 / 2))) := by
  have h1 := tendsto_log_cos_div_sub_one
  have h2 : Filter.Tendsto (fun x : ℝ => (Real.cos x - 1) / x ^ 2)
      (nhdsWithin 0 {0}ᶜ) (nhds (-(1 / 2))) := by
    have hneg := tendsto_one_sub_cos_div_sq.neg
    have hEq : (fun x : ℝ => -((1 - Real.cos x) / x ^ 2))
        =ᶠ[nhdsWithin 0 {0}ᶜ] (fun x : ℝ => (Real.cos x - 1) / x ^ 2) := by
      filter_upwards [self_mem_nhdsWithin] with x hx
      ring
    exact Filter.Tendsto.congr' hEq hneg
  have hball : Metric.ball (0:ℝ) (2 * π) ∈ nhds 0 := Metric.ball_mem_nhds 0 two_pi_pos
  have hv : (-(1 / 2 : ℝ)) = 1 * (-(1 / 2)) := by ring
  rw [hv]
  have hEq2 : (fun x : ℝ => (Real.log (Real.cos x) / (Real.cos x - 1)) * ((Real.cos x - 1) / x ^ 2))
      =ᶠ[nhdsWithin 0 {0}ᶜ] (fun x : ℝ => Real.log (Real.cos x) / x ^ 2) := by
    filter_upwards [mem_nhdsWithin_of_mem_nhds hball, self_mem_nhdsWithin] with x hxb hx
    have hx0 : x ≠ 0 := hx
    have habs : |x| < 2 * π := by simpa using Metric.mem_ball.mp hxb
    obtain ⟨hx₁, hx₂⟩ := abs_lt.mp habs
    have hx1 : Real.cos x - 1 ≠ 0 := by
      intro hc
      exact hx0 (Real.cos_eq_one_iff_of_lt_of_lt hx₁ hx₂ |>.mp (by linarith))
    field_simp
  refine Filter.Tendsto.congr' hEq2 ?_
  exact h1.mul h2

/-- J: перенос на dt → 0⁺ через x = dt·θ. -/
theorem tendsto_log_cos_dt_div_sq {θ : ℝ} (hθ : θ ≠ 0) :
    Filter.Tendsto (fun dt : ℝ => Real.log (Real.cos (dt * θ)) / (dt * θ) ^ 2)
      (nhdsWithin 0 (Set.Ioi 0)) (nhds (-(1 / 2))) := by
  have hcomp := tendsto_log_cos_div_sq.comp (tendsto_mul_const_nhdsWithin_ne hθ)
  have hsub : Set.Ioi (0:ℝ) ⊆ {0}ᶜ := by
    intro dt hdt
    simpa using ne_of_gt (Set.mem_Ioi.mp hdt)
  have hmono : (nhdsWithin 0 (Set.Ioi 0) : Filter ℝ) ≤ nhdsWithin 0 {0}ᶜ :=
    nhdsWithin_mono 0 hsub
  have hres := hcomp.mono_left hmono
  simpa [Function.comp_def] using hres

/-- Ядро финала: для любой функции вида −log(cos(dt·θ))/dt отношение
γ_eff(dt)/dt стремится к θ²/2 при dt → 0⁺. -/
theorem gammaEff_ratio_core {θ : ℝ} (hθ : θ ≠ 0) (gammaEff : ℝ → ℝ)
    (hgamma : ∀ dt : ℝ, dt ≠ 0 → gammaEff dt = -(Real.log (Real.cos (dt * θ))) / dt) :
    Filter.Tendsto (fun dt => gammaEff dt / dt) (nhdsWithin 0 (Set.Ioi 0))
      (nhds (θ ^ 2 / 2)) := by
  have hv : (θ ^ 2 / 2 : ℝ) = (-(θ ^ 2)) * (-(1 / 2)) := by ring
  rw [hv]
  have hEq : (fun dt : ℝ => (-(θ ^ 2 : ℝ)) * (Real.log (Real.cos (dt * θ)) / (dt * θ) ^ 2))
      =ᶠ[nhdsWithin 0 (Set.Ioi 0)] (fun dt : ℝ => gammaEff dt / dt) := by
    have hmem : Set.Ioi 0 ∈ (nhdsWithin 0 (Set.Ioi 0) : Filter ℝ) := self_mem_nhdsWithin
    filter_upwards [hmem] with dt hdt
    have hdt' : dt ≠ 0 := ne_of_gt (Set.mem_Ioi.mp hdt)
    rw [hgamma dt hdt']
    field_simp
    ring
  refine Filter.Tendsto.congr' hEq ?_
  have hcst : Filter.Tendsto (fun _ : ℝ => (-(θ ^ 2 : ℝ))) (nhdsWithin 0 (Set.Ioi 0))
      (nhds (-(θ ^ 2 : ℝ))) := tendsto_const_nhds
  exact hcst.mul (tendsto_log_cos_dt_div_sq hθ)


/-- ГЛАВНАЯ ТЕОРЕМА ПРОТОКОЛА: `γ_eff(dt)/dt → θ_b²/2` при `dt → 0⁺`.
Содержательно: на единицу времени дискретный протокол даёт затухание
`θ_b²·dt/2`, стремящееся к нулю при `dt → 0` — непрерывного предела протокола
с постоянной γ не существует, эффект принципиально дискретен. Вместе с
`protocol_ode_form` это превращает описание протокола из тождества
в утверждение о скорости затухания. -/
theorem gammaEff_ratio_tendsto :
    Filter.Tendsto (fun dt => gammaEff dt / dt) (nhdsWithin 0 (Set.Ioi (0:ℝ)))
      (nhds (θ_b ^ 2 / 2)) :=
  gammaEff_ratio_core (ne_of_gt theta_b_pos) gammaEff (fun _ _ => rfl)

end Protocol

/-! ## Распределённое торможение вихревого ствола (3D) -/

namespace VortexTube
open Real Section1

/-- Циркуляция вихревой трубки: `Γ = ∫₀ᴸ ω(s) ds`, где `ω(s)` — завихрённость
в сечении ствола, параметризованном длиной дуги `s`. -/
def circulation (ω : ℝ → ℝ) (L : ℝ) : ℝ := ∫ s in (0:ℝ)..L, ω s

/-- Распределённый тормозной момент на единицу длины ствола:
`dτ/ds = −γ(s)·ω(s)`, где `γ ∝ δ` — коэффициент фазового слипа. -/
def momentDensity (γ ω : ℝ → ℝ) (s : ℝ) : ℝ := -(γ s) * ω s

/-- Синхронизация: коэффициент слипа одинаков во всех сечениях ствола,
`γ(s) = γ₀`. Тогда и угол поворота `θ_b` не «плывёт» вдоль `s` —
ствол тормозит когерентно (одна мода, а не набор рассинхронизированных сечений). -/
def synchronized (γ : ℝ → ℝ) (γ₀ : ℝ) : Prop := ∀ s, γ s = γ₀

/-- ★ Полный тормозной момент при синхронизации: `τ = −γ₀·Γ` — тормозится весь
ствол, и эффект пропорционален циркуляции (линейность интеграла). -/
theorem moment_total {γ ω : ℝ → ℝ} {L γ₀ : ℝ} (hsync : synchronized γ γ₀)
    (hω : ContinuousOn ω (Set.uIcc 0 L)) :
    ∫ s in (0:ℝ)..L, momentDensity γ ω s = -(γ₀ * circulation ω L) := by
  have hint : ∫ s in (0:ℝ)..L, momentDensity γ ω s
      = ∫ s in (0:ℝ)..L, (-γ₀) * ω s :=
    intervalIntegral.integral_congr
      (fun s _ => by simp only [momentDensity]; rw [hsync s])
  rw [hint, intervalIntegral.integral_const_mul, circulation]
  ring

/-- Знак: при `ω ≥ 0` вдоль ствола и `γ₀ ≥ 0` момент тормозящий (`τ ≤ 0`). -/
theorem moment_nonpos {γ ω : ℝ → ℝ} {L γ₀ : ℝ} (hsync : synchronized γ γ₀)
    (hω : ContinuousOn ω (Set.uIcc 0 L)) (hL : 0 ≤ L) (hγ₀ : 0 ≤ γ₀)
    (hωpos : ∀ s ∈ Set.uIcc 0 L, 0 ≤ ω s) :
    ∫ s in (0:ℝ)..L, momentDensity γ ω s ≤ 0 := by
  rw [moment_total hsync hω]
  simp only [circulation]
  exact neg_nonpos.mpr (mul_nonneg hγ₀
    (intervalIntegral.integral_nonneg hL
      fun u hu => hωpos u (by rw [Set.uIcc_of_le hL]; exact hu)))

/-- Алгебраическая форма константы: `π/(4π² + 2π√3) = 1/(4π + 2√3)`.
Это тождество двух записей ОДНОГО определения `bCorrection`, а НЕ вывод
константы из системы Кирхгофа. -/
theorem b_eq_kirchhoff_value : bCorrection = 1 / (4 * Real.pi + 2 * Real.sqrt 3) := by
  unfold bCorrection
  field_simp
  ring

/-- `sin θ_b = 1/(4π + 2√3)`: угол поворота, отвечающий константе b
(через `sin(arcsin b) = b`). Вывод самой b из задачи точечных вихрей Кирхгофа —
отдельная незакрытая задача, здесь не формализован. -/
theorem sin_θ_b_eq_kirchhoff_value :
    Real.sin θ_b = 1 / (4 * Real.pi + 2 * Real.sqrt 3) := by
  rw [Section1.sin_θ_b_eq_b, b_eq_kirchhoff_value]

/-- Модель пользователя (п. 5): `∂_tω = −γ·ω`. Решение: `ω(t) = ω₀·e^{−γt}`. -/
theorem ode_solution (γ ω₀ : ℝ) : ∀ t : ℝ,
    HasDerivAt (fun t => ω₀ * Real.exp (-(γ * t)))
      (-(γ) * (ω₀ * Real.exp (-(γ * t)))) t := by
  intro t
  have h1 : HasDerivAt (fun y => -(γ * y)) (-(γ * 1)) t :=
    ((hasDerivAt_id t).const_mul γ).neg
  have h2 : HasDerivAt (fun y => Real.exp (-(γ * y)))
      (Real.exp (-(γ * t)) * (-(γ * 1))) t :=
    (Real.hasDerivAt_exp (-(γ * t))).comp t h1
  have h3 : HasDerivAt (fun y => ω₀ * Real.exp (-(γ * y)))
      (ω₀ * (Real.exp (-(γ * t)) * (-(γ * 1)))) t := h2.const_mul ω₀
  convert h3 using 1
  ring

/-- Скорость в модели пользователя как свободная «рука»: `γ = δ / T_rev`
(слип δ за период оборота ствола T_rev). -/
def gammaOfSlip (δ T_rev : ℝ) : ℝ := δ / T_rev

theorem gammaOfSlip_pos {δ T_rev : ℝ} (hδ : 0 < δ) (hT : 0 < T_rev) :
    0 < gammaOfSlip δ T_rev := div_pos hδ hT

end VortexTube
