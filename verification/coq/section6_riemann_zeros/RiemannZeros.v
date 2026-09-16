Require Import Reals. Require Import Lra. Open Scope R_scope.

Definition gamma_1 : R := 14.134725141734693.
Definition gamma_2 : R := 21.022039638771555.
Definition gamma_3 : R := 25.010857580145688.

Lemma zeros_ordered : 0 < gamma_1 /\ gamma_1 < gamma_2 /\ gamma_2 < gamma_3.
Proof. unfold gamma_1, gamma_2, gamma_3. lra. Qed.

Lemma gamma_1_gt_14 : 14 < gamma_1. Proof. unfold gamma_1. lra. Qed.

Axiom zeta_functional_equation : True.
Axiom hilbert_polya_conjecture : True.

Compute gamma_1. Compute gamma_2. Compute gamma_3.
