Require Import Reals. Require Import Lra. Open Scope R_scope.

Definition alpha : R := sqrt 168 / (2 * PI).
Definition L_min : R := 2 * PI / sqrt 168.
Definition b_corr : R := PI / (4 * PI^2 + 2 * PI * sqrt 3).
Definition gamma : R := alpha * b_corr * L_min.

Compute alpha. Compute L_min. Compute b_corr. Compute gamma.

Lemma alpha_pos : 0 < alpha.
Proof. unfold alpha. apply Rdiv_lt_0_compat. apply sqrt_pos_lt. lra. apply Rmult_lt_0_compat; lra. Qed.

Lemma alpha_times_L_min : alpha * L_min = 1.
Proof. unfold alpha, L_min. field. lra. Qed.

Lemma gamma_eq_b : gamma = b_corr.
Proof. unfold gamma. rewrite alpha_times_L_min. field. lra. Qed.

Lemma sum_sq_degrees : 1*1 + 3*3 + 3*3 + 6*6 + 7*7 + 8*8 = 168. Proof. reflexivity. Qed.
