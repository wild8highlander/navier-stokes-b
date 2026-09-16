Require Import Reals. Require Import Lra. Open Scope R_scope.

Definition N_cloud : nat := 36.
Definition peierls_phase : R := cos (2 * PI / 7).
Definition gue_spacing_pdf (s : R) : R := (32 / PI^2) * s^2 * exp (-4 * s^2 / PI).
Definition gue_ratio : R := 0.6027.

Lemma gue_pdf_nonneg : forall s, 0 <= gue_spacing_pdf s.
Proof. intro s. unfold gue_spacing_pdf. apply Rmult_le_pos. apply Rmult_le_pos. left. lra. apply pow_le. lra. apply exp_pos. Qed.

Lemma gue_ratio_bounded : 0.5 < gue_ratio /\ gue_ratio < 0.7. Proof. unfold gue_ratio. lra. Qed.

Compute peierls_phase. Compute gue_ratio.
