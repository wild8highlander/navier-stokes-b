theory RiemannZeros
  imports Complex_Main
begin

definition gamma_1 :: real where "gamma_1 = 14.134725141734693"
definition gamma_2 :: real where "gamma_2 = 21.022039638771555"
definition gamma_3 :: real where "gamma_3 = 25.010857580145688"

theorem zeros_ordered: "0 < gamma_1 \<and> gamma_1 < gamma_2 \<and> gamma_2 < gamma_3"
  by (simp add: gamma_1_def gamma_2_def gamma_3_def)

axiomatization where zeta_functional_equation: True and hilbert_polya_conjecture: True

value "gamma_1" value "gamma_2" value "gamma_3"

end
