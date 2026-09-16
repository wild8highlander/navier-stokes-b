theory ProofChain
  imports Complex_Main
begin

definition alpha :: real where "alpha = sqrt 168 / (2 * pi)"
definition L_min :: real where "L_min = 2 * pi / sqrt 168"
definition b_corr :: real where "b_corr = pi / (4 * pi^2 + 2 * pi * sqrt 3)"
definition gamma :: real where "gamma = alpha * b_corr * L_min"

theorem alpha_pos: "0 < alpha"
  unfolding alpha_def by (auto intro: divide_pos_pos)

theorem alpha_times_L_min: "alpha * L_min = 1"
  unfolding alpha_def L_min_def by (auto simp: field_simps)

theorem gamma_eq_b: "gamma = b_corr"
  unfolding gamma_def using alpha_times_L_min by simp

value "alpha" value "L_min" value "gamma"

end
