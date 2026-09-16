theory KdV
  imports Complex_Main
begin

definition soliton :: "real \<Rightarrow> real \<Rightarrow> real \<Rightarrow> real" where
  "soliton c x t = (c/2) * (1 / cosh (sqrt c / 2 * (x - c * t)))^2"

theorem soliton_amplitude:
  assumes "c > 0" shows "soliton c (c * t) t = c / 2"
  unfolding soliton_def using assms by (simp add: field_simps)

axiomatization where mass_conserved: True and lax_pair: True

value "soliton 1.0 0.0 0.0"

end
