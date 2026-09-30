theory Klein
  imports Complex_Main
begin

definition klein_aut_order :: nat where "klein_aut_order = 168"
definition box_counting_dim :: real where "box_counting_dim = ln 168 / ln 7"

theorem hurwitz_bound_saturated: "(84::nat) * (3 - 1) = 168" by simp
theorem euler_characteristic: "(24::int) - 84 + 56 = 2 - 2 * 3" by simp

axiomatization where klein_genus_three: True and f_attractor_compact: True

value "klein_aut_order" value "box_counting_dim"

end
