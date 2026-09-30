theory CorrectionB
  imports Complex_Main
begin

definition b_correction :: real where
  "b_correction = pi / (4 * pi^2 + 2 * pi * sqrt 3)"

value "b_correction"

theorem b_pos: "0 < b_correction"
  unfolding b_correction_def by (auto intro: divide_pos_pos pi_gt_zero)

theorem b_lt_one: "b_correction < 1"
  sorry

definition theta_b :: real where
  "theta_b = arcsin b_correction"

theorem sin_theta_eq_b: "sin theta_b = b_correction"
  unfolding theta_b_def by (simp add: b_pos b_lt_one)

end
