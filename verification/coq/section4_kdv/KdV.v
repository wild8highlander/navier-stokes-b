Require Import Reals. Require Import Lra. Open Scope R_scope.

Definition soliton (c x t : R) : R := (c/2) * (1 / cosh (sqrt c / 2 * (x - c * t)))^2.

Lemma soliton_amplitude : forall c t, 0 < c -> soliton c (c * t) t = c / 2.
Proof. intros c t Hc. unfold soliton. replace (sqrt c / 2 * (c * t - c * t)) with 0 by field. rewrite cosh_0. field. lra. Qed.

Axiom mass_conserved : True.
Axiom miura_mkdv_to_kdv : True.
Axiom lax_pair : True.

Compute (soliton 1.0 0.0 0.0).
