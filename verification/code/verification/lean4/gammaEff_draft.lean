import Mathlib.Analysis.SpecialFunctions.Trigonometric.Deriv
import Mathlib.Analysis.SpecialFunctions.Log.Deriv
import Mathlib.Analysis.Calculus.Deriv.Slope
import Mathlib.Tactic
open Real Filter Topology

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
  first
  | exact (lt_div_iff₀ hcpos).mp h2
  | exact (lt_div_iff hcpos).mp h2

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

/-- Ядро финала. -/
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
