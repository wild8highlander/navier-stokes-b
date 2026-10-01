theory MasterRelation
  imports Complex_Main
begin

section \<open>Section 7 — Smagorinsky–Kolmogorov master relation\<close>

text \<open>Mirrors verification/section7_smagorinsky_kolmogorov: the master
relation C\<^sub>s = 1/(\<pi> \<cdot> (3C\<^sub>K/2)\<^sup>3\<^isub>/\<^sup>4),
its positivity, the Fibonacci scaffolding of the \<phi>-audit, and the
coefficient algebra of the reduced zero-drift condition (5').
Fully proved here: Cassini (complete induction), Fibonacci positivity and
monotonicity, the a\<cdot>a\<cdot>b\<cdot>b degeneracy and the a\<cdot>b\<cdot>b\<cdot>c
sign-definiteness of (5'). Admitted (ledger): the two rpow-technical
analytic lemmas.\<close>

subsection \<open>The master relation\<close>

definition cs :: "real \<Rightarrow> real" where
  "cs ck = 1 / (pi * (3 * ck / 2) powr (3 / 4))"

lemma cs_pos:
  assumes "0 < ck"
  shows   "0 < cs ck"
proof -
  have h2: "0 < (3::real) * ck / 2" using assms by simp
  have "0 < (3 * ck / 2) powr (3 / 4)"
    by (rule powr_pos) (simp add: h2)
  then show ?thesis unfolding cs_def
    using pi_gt_zero h2 by (auto simp: divide_pos_pos split_div)
qed

subsection \<open>Fibonacci scaffolding (integer-valued, exact)\<close>

fun fib :: "nat \<Rightarrow> int" where
  "fib 0 = 0"
| "fib (Suc 0) = 1"
| "fib (Suc (Suc n)) = fib (Suc n) + fib n"

lemma fib_add: "fib (n + 2) = fib (n + 1) + fib n"
  by (induct n rule: fib.induct) simp_all

lemma fib_nonneg: "0 \<le> fib n"
  by (induct n rule: fib.induct) simp_all

lemma fib_mono: "fib n \<le> fib (Suc n)"
  by (induct n rule: fib.induct) (auto simp add: fib_add)

lemma fib_ge_one_from: "2 \<le> n \<Longrightarrow> 1 \<le> fib n"
  by (induct n rule: fib.induct) (auto simp add: fib_add le_Suc_eq)

subsection \<open>Cassini identity — fully proved\<close>

lemma cassini: "fib (Suc n) * fib (Suc n) - fib n * fib (n + 2) = (-1) ^ n"
proof (induct n)
  case 0
  then show ?case by simp
next
  case (Suc m)
  have rec3: "fib (m + 3) = fib (m + 2) + fib (m + 1)"
    using fib_add[of "m + 1"] by simp
  have rec2: "fib (m + 2) = fib (m + 1) + fib m"
    using fib_add[of m] by simp
  have pow: "(-1) ^ (Suc m) = - ((-1) ^ m)" by simp
  show ?case
  proof -
    have "fib (Suc (Suc m)) * fib (Suc (Suc m))
        - fib (Suc m) * fib (Suc (Suc (Suc m)))
        = -(fib (Suc m) * fib (Suc m) - fib m * fib (m + 2))"
      using rec3 rec2 by simp
    then show ?thesis using Suc pow by simp
  qed
qed

subsection \<open>The reduced zero-drift condition (5') — coefficient algebra\<close>

text \<open>For Fibonacci quads a\<cdot>b\<cdot>b\<cdot>c = (F k, F (k+1), F (k+1), F (k+2))
the three coefficients of (5') are ((-1)\<^sup>k, F(k+1)\<^sup>2,
F(k+2)\<^sup>2 - F(k+1)\<^sup>2); the last two are positive for k \<ge> 2,
so the condition is sign-definite and has no root. For symmetric quads
a\<cdot>a\<cdot>b\<cdot>b all three coefficients vanish.\<close>

lemma coeff_aabb:
  "fib k * fib (Suc k) - fib k * fib (Suc k) = 0
   \<and> fib (Suc k) * fib (Suc k) - fib (Suc k) * fib (Suc k) = 0
   \<and> fib k * fib k - fib k * fib k = 0"
  by simp

lemma coeff_abbc_c2: "fib (Suc k) * fib (Suc k) - fib k * fib (k + 2) = (-1) ^ k"
  using cassini[of k] by simp

lemma coeff_abbc_cM: "fib (Suc k) * fib (k + 2) - fib k * fib (Suc k) = fib (Suc k) * fib (Suc k)"
proof -
  have "fib (k + 2) = fib (Suc k) + fib k" using fib_add[of k] by simp
  then show ?thesis by simp
qed

lemma coeff_abbc_c1_pos:
  assumes "2 \<le> k"
  shows   "0 < fib (k + 2) * fib (k + 2) - fib (Suc k) * fib (Suc k)"
proof -
  have rec: "fib (k + 2) = fib (Suc k) + fib k" using fib_add[of k] by simp
  have h1: "1 \<le> fib k" using assms fib_ge_one_from by auto
  have h2: "0 < fib (Suc k) + fib k"
    using fib_nonneg[of k] fib_nonneg[of "Suc k"] assms by simp
  show ?thesis
  proof -
    have "fib (k + 2) * fib (k + 2) - fib (Suc k) * fib (Suc k)
        = fib k * (fib k + 2 * fib (Suc k))"
      using rec by algebra
    moreover have "0 < fib k + 2 * fib (Suc k)" using h2 by simp
    ultimately show ?thesis using h1 by (simp add: algebra_simps)
  qed
qed

subsection \<open>Admitted analytic properties (ledger TODO_sorry.md)\<close>

lemma cs_exponent_law:
  assumes "0 < a" "0 < ck"
  shows   "cs (a * ck) = a powr (-3 / 4) * cs ck"
  unfolding cs_def
  by (simp add: powr_mult field_simps assms)

lemma cs_strictAnti:
  assumes "0 < x" "0 < y" "x < y"
  shows   "cs y < cs x"
proof -
  have h2: "0 < (3::real) * x / 2" "0 < 3 * y / 2" using assms by simp_all
  have "(3 * x / 2) powr (3 / 4) < (3 * y / 2) powr (3 / 4)"
    using assms h2 powr_less_mono2 by auto
  then show ?thesis unfolding cs_def
    using pi_gt_zero assms(3)
    by (auto simp: divide_strict_right_mono split_div)
qed

value "cs (3 / 2)"

end
