Require Import Reals. Require Import Lra. Open Scope R_scope.

Definition b_correction : R := PI / (4 * PI^2 + 2 * PI * sqrt 3).
Compute b_correction.

Lemma b_pos : 0 < b_correction.
Proof.
  unfold b_correction.
  apply Rdiv_lt_0_compat.
  - apply PI_pos.
  - assert (0 < 4 * PI^2) by (apply Rmult_lt_0_compat; [apply Rmult_lt_0_compat | apply pow_lt_0]; apply PI_pos).
    assert (0 < 2 * PI * sqrt 3) by (apply Rmult_lt_0_compat; [apply Rmult_lt_0_compat | apply sqrt_pos_lt]; apply PI_pos).
    lra.
Qed.

Lemma b_lt_one : b_correction < 1. Proof. admit. Admitted.

Definition theta_b : R := sqrt (1 - b_correction^2).
Lemma cos_plus_sin_sq : theta_b^2 + b_correction^2 = 1.
Proof. unfold theta_b. assert (0 <= 1 - b_correction^2) by nra. rewrite sqrt_def by lra. lra. Qed.

Compute b_correction.
