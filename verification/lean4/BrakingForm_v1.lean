import ResearchPapersVerification.Section1_CorrectionB.Basic
import Mathlib.Tactic
import Mathlib.Data.Real.Pi.Bounds
import Mathlib.Analysis.SpecialFunctions.Trigonometric.Deriv
import Mathlib.Analysis.SpecialFunctions.Log.Deriv
import Mathlib.Analysis.Calculus.Deriv.Slope

/-!
# Идеальная форма торможения завихрения: Protocol и предел γ_eff(dt)/dt

РЕКОНСТРУКЦИЯ (2026-11-08): песочница была перезапущена, рабочая копия
проекта утрачена. Восстановлены по контексту сессии:
(а) протокольная часть `Protocol` — определения и тождества сохранены
дословно (cos_pos, cos_lt_one, theta_b_pos, pow_cos_lt_one, gammaEff,
protocol_ode_form, gammaEff_pos);
(б) ГЛАВНЫЙ РЕЗУЛЬТАТ — цепочка пределов и `gammaEff_ratio_tendsto`:
γ_eff(dt)/dt → θ_b²/2 при dt → 0⁺ (дискретность протокола принципиальна).
Разделы о фурье-модах (L4-machinery tg2d_core.py) и VortexTube в этой
реконструкции опущены; импорт Common.Foundation заменён чистыми
Mathlib-импортами.
-/

open Real Section1 Filter Topology

namespace Protocol

/-- Положительность косинуса на диапазоне протокола `φ ∈ (−π/2, π/2)`. -/
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
noncomputable def gammaEff (dt : ℝ) : ℝ := -(Real.log (Real.cos (dt * θ_b))) / dt

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
