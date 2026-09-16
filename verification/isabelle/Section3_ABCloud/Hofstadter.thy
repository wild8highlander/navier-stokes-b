theory Hofstadter
  imports Complex_Main
begin

definition N_cloud :: nat where "N_cloud = 36"
definition peierls_phase :: real where "peierls_phase = cos (2 * pi / 7)"
definition gue_ratio :: real where "gue_ratio = 0.6027"

theorem gue_ratio_bounded: "0.5 < gue_ratio \<and> gue_ratio < 0.7"
  by (simp add: gue_ratio_def)

value "peierls_phase" value "gue_ratio"

end
