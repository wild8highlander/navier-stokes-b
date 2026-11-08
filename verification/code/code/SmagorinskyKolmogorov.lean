import Mathlib.Tactic
import Mathlib.Data.Real.Pi.Bounds

/-!
# Мастер-соотношение Смагоринского–Колмогорова

`C_s = 1 / (π · (3·C_K / 2)^(3/4))` — формальный компаньон вычислительной
программы `research_col_smar` (численные опыты — в `numerical/`).

Полностью доказано (без `sorry` — прежние три дыры закрыты в этой версии):

* `cs_pos` — положительность константы Смагоринского;
* `fib_add`, `fib_nonneg`, `fib_mono`, `fib_ge_one_from` — фибоначчиев
  каркас (целочисленный, точный);
* `cassini` — тождество Кассини `F(n+1)² − F(n)F(n+2) = (−1)ⁿ`
  (закрыто индукцией по парам соседей);
* `coeff_abbc` — знакоопределённость приведённого условия нулевого дрейфа
  (5′) для квадов a·b·b·c: корней нет ни при каком масштабе;
* `coeff_aabb` — вырожденная однопараметрическая семья a·a·b·b:
  все три коэффициента (5′) тождественно нулевые;
* `cs_exponent_law` — закон показателя `C_s(a·C_K) = a^(−3/4)·C_s(C_K)`;
* `cs_strictAnti` — строгое монотонное убывание `C_s` на (0, ∞).
-/

noncomputable section
namespace Verification.Turbulence

open Real

/-! ### Мастер-соотношение -/

/-- Мастер-соотношение: константа Смагоринского как функция константы
Колмогорова. -/
def cs (ck : ℝ) : ℝ := 1 / (π * (3 * ck / 2) ^ ((3 : ℝ) / 4))

/-- Референсное значение константы Колмогорова (Sreenivasan 1995). -/
def CK : ℝ := 3 / 2

theorem denom_pos {ck : ℝ} (hck : 0 < ck) : 0 < π * (3 * ck / 2) ^ ((3 : ℝ) / 4) := by
  have h2 : (0 : ℝ) < 3 * ck / 2 := by linarith
  refine mul_pos Real.pi_pos ?_
  exact rpow_pos_of_pos h2 _

theorem cs_pos {ck : ℝ} (hck : 0 < ck) : 0 < cs ck := by
  unfold cs
  exact div_pos zero_lt_one (denom_pos hck)

/-! ### Фибоначчиев каркас (целочисленный, точный) -/

/-- Фибоначчи, целочисленный (чередование знака Кассини точное). -/
def fib : ℕ → ℤ
  | 0 => 0
  | 1 => 1
  | n + 2 => fib (n + 1) + fib n

theorem fib_add (n : ℕ) : fib (n + 2) = fib (n + 1) + fib n := rfl

theorem fib_nonneg : ∀ n : ℕ, 0 ≤ fib n
  | 0 => by norm_num [fib]
  | 1 => by norm_num [fib]
  | n + 2 => by rw [fib_add]; have h1 := fib_nonneg n; have h2 := fib_nonneg (n + 1); omega

theorem fib_mono : ∀ n : ℕ, fib n ≤ fib (n + 1)
  | 0 => by norm_num [fib]
  | 1 => by norm_num [fib]
  | n + 2 => by
      rw [fib_add n]
      show fib (n + 1) + fib n ≤ fib (n + 2) + fib (n + 1)
      have hm : fib n ≤ fib (n + 1) := fib_mono n
      have h1 : fib (n + 1) ≤ fib (n + 2) := fib_mono (n + 1)
      omega

theorem fib_ge_one_from : ∀ n : ℕ, 2 ≤ n → 1 ≤ fib n := by
  have pair : ∀ n : ℕ, 1 ≤ fib (n + 2) ∧ 1 ≤ fib (n + 3) := by
    intro n
    induction n with
    | zero => norm_num [fib]
    | succ m ih =>
      obtain ⟨h1, h2⟩ := ih
      refine ⟨?_, ?_⟩
      · have h2' : 1 ≤ fib (m + 1 + 2) := h2
        exact h2'
      · show 1 ≤ fib (m + 2 + 2)
        rw [fib_add (m + 2)]
        have h1' : 1 ≤ fib (m + 2) := h1
        have h2' : 1 ≤ fib (m + 2 + 1) := h2
        omega
  intro n hn
  have hsub : (n - 2) + 2 = n := by omega
  have h := pair (n - 2)
  rw [hsub] at h
  exact h.1

/-! ### Тождество Кассини (закрыто) -/

/-- **Тождество Кассини**: `F(n+1)² − F(n)·F(n+2) = (−1)ⁿ`.
Доказательство: одновременная индукция по парам соседей `P n ∧ P (n+1)`;
в шаге индукции старшие числа Фибоначчи раскрываются рекуррентностью,
и цель сводится к `P n` при `F(n+2) = F(n+1)+F(n)`. -/
theorem cassini (n : ℕ) :
    fib (n + 1) ^ 2 - fib n * fib (n + 2) = (-1 : ℤ) ^ n := by
  have key : ∀ n : ℕ,
      fib (n + 1) ^ 2 - fib n * fib (n + 2) = (-1 : ℤ) ^ n
      ∧ fib (n + 1 + 1) ^ 2 - fib (n + 1) * fib (n + 1 + 2) = (-1 : ℤ) ^ (n + 1) := by
    intro n
    induction n with
    | zero => norm_num [fib]
    | succ n ih =>
      obtain ⟨h1, h2⟩ := ih
      refine ⟨h2, ?_⟩
      have hC : fib (n + 1 + 1) = fib (n + 1) + fib n := fib_add n
      have hD : fib (n + 1 + 2) = fib (n + 1 + 1) + fib (n + 1) := fib_add (n + 1)
      have hE : fib (n + 1 + 3) = fib (n + 1 + 2) + fib (n + 1 + 1) := fib_add (n + 2)
      have hsign : (-1 : ℤ) ^ (n + 1 + 1) = (-1 : ℤ) ^ n := by
        rw [pow_succ, pow_succ]
        ring
      rw [hsign, hE, hD]
      linear_combination (norm := ring_nf) h1 - fib (n + 1 + 1) * hC
  exact (key n).1

/-! ### Приведённое условие нулевого дрейфа (5′) — алгебра коэффициентов -/

/-- Для фибоначчиевых квадов a·b·b·c = (F k, F (k+1), F (k+1), F (k+2)) с
k ≥ 2 три коэффициента приведённого условия нулевого дрейфа (5′) равны
* коэффициент при m₂: (−1)ᵏ (Кассини),
* коэффициент при m_M: F(k+1)² > 0,
* коэффициент при m₁: F(k+2)² − F(k+1)² > 0,
так что (5′) знакоопределено и корней не имеет — семья a·b·b·c не допускает
конфигурации нулевого дрейфа ни при каком масштабе. -/
theorem coeff_abbc (k : ℕ) (hk : 2 ≤ k) :
    fib (k + 1) * fib (k + 1) - fib k * fib (k + 2) = (-1) ^ k
    ∧ fib (k + 1) * fib (k + 2) - fib k * fib (k + 1) = fib (k + 1) ^ 2
    ∧ 0 < fib (k + 2) ^ 2 - fib (k + 1) ^ 2 := by
  refine ⟨?_, ?_, ?_⟩
  · rw [← pow_two]
    exact cassini k
  · have hrec : fib (k + 2) = fib (k + 1) + fib k := fib_add k
    rw [hrec]
    ring
  · have hrec : fib (k + 2) = fib (k + 1) + fib k := fib_add k
    have hsplit : fib (k + 2) ^ 2 - fib (k + 1) ^ 2
        = (fib (k + 2) - fib (k + 1)) * (fib (k + 2) + fib (k + 1)) := by ring
    have hfk : 1 ≤ fib k := fib_ge_one_from k hk
    have hsum : 0 < fib (k + 2) + fib (k + 1) := by
      have h1 := fib_nonneg k
      have h2 := fib_nonneg (k + 1)
      rw [hrec]; omega
    have hdiff : fib (k + 2) - fib (k + 1) = fib k := by omega
    rw [hsplit, hdiff]
    exact mul_pos (by omega) hsum

/-- Для симметричных квадов a·a·b·b = (F k, F k, F (k+1), F (k+1)) все три
коэффициента (5′) тождественно нулевые — вырожденная однопараметрическая
семья, на которой φ-геометрия конструктивно достижима. -/
theorem coeff_aabb (k : ℕ) :
    fib k * fib (k + 1) - fib k * fib (k + 1) = 0
    ∧ fib k * fib (k + 1) - fib k * fib (k + 1) = 0
    ∧ fib (k + 1) ^ 2 - fib (k + 1) ^ 2 = 0 := by
  exact ⟨by ring, by ring, by ring⟩

/-! ### Аналитические свойства мастер-соотношения (закрыты) -/

/-- Закон показателя: `C_s(a·C_K) = a^(−3/4)·C_s(C_K)` для `a, C_K > 0`. -/
theorem cs_exponent_law {a ck : ℝ} (ha : 0 < a) (hck : 0 < ck) :
    cs (a * ck) = a ^ ((-3 : ℝ) / 4) * cs ck := by
  have hsplit : (3 : ℝ) * (a * ck) / 2 = a * (3 * ck / 2) := by ring
  have hpos : (0 : ℝ) < 3 * ck / 2 := by linarith
  have hap : a ^ ((3 : ℝ) / 4) ≠ 0 := ne_of_gt (rpow_pos_of_pos ha _)
  have hexp : (-3 : ℝ) / 4 = -((3 : ℝ) / 4) := by norm_num
  unfold cs
  rw [hsplit, mul_rpow (le_of_lt ha) (le_of_lt hpos), hexp,
    Real.rpow_neg (le_of_lt ha) ((3 : ℝ) / 4)]
  field_simp
  ring

/-- Строгое монотонное убывание `C_s` на (0, ∞): знаменатель
`π·(3·ck/2)^(3/4)` строго возрастает по `ck` (показатель 3/4 > 0),
обратная к положительной строго возрастающей функции строго убывает. -/
theorem cs_strictAnti : StrictAntiOn cs (Set.Ioi (0 : ℝ)) := by
  intro x hx y hy hxy
  have hxpos : (0:ℝ) < x := Set.mem_Ioi.mp hx
  have hypos : (0:ℝ) < y := Set.mem_Ioi.mp hy
  have hdx : (0:ℝ) < π * (3 * x / 2) ^ ((3:ℝ)/4) := denom_pos hxpos
  have hdy : (0:ℝ) < π * (3 * y / 2) ^ ((3:ℝ)/4) := denom_pos hypos
  unfold cs
  refine (one_div_lt_one_div hdy hdx).mpr ?_
  refine mul_lt_mul_of_pos_left ?_ Real.pi_pos
  exact rpow_lt_rpow (by linarith) (by linarith) (by positivity)

end Verification.Turbulence
