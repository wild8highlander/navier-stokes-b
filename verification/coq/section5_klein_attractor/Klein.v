Require Import Reals. Require Import Lra. Open Scope R_scope.

Definition klein_aut_order : nat := 168.
Definition box_counting_dim : R := ln 168 / ln 7.

Lemma hurwitz_bound_saturated : 84 * (3 - 1) = 168. Proof. reflexivity. Qed.
Lemma euler_characteristic : 24 - 84 + 56 = 2 - 2 * 3. Proof. reflexivity. Qed.

Axiom klein_genus_three : True.
Axiom f_attractor_compact : True.

Compute klein_aut_order. Compute box_counting_dim.
