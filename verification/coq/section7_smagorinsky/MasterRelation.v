(* Section 7 — Smagorinsky–Kolmogorov master relation (Coq/Rocq port).

Mirrors verification/section7_smagorinsky_kolmogorov: the master relation
C_s = 1/(π·(3·C_K/2)^(3/4)), its positivity, the Fibonacci scaffolding of
the φ-audit, and the coefficient algebra of the reduced zero-drift
condition (5′): a·b·b·c is sign-definite (no root at any scale),
a·a·b·b degenerate (all coefficients vanish).

Fully proved here: fib positivity/monotonicity scaffolding, cs_pos,
coeff_aabb, coeff_abbc_c2 (Cassini), coeff_abbc_cM, coeff_abbc_c1_pos.
Admitted (ledger TODO_sorry.md): cs_exponent_law, cs_strictAnti. *)

Require Import Reals.
Require Import Lia.
Require Import Lra.
Open Scope R_scope.

(* ---------- the master relation ---------- *)

Definition cs (ck : R) : R := 1 / (PI * (3 * ck / 2) ^ (3/4)).

(* Real power positivity via the exp/ln definition of Rpower.pow. *)
Lemma rpow_pos : forall x r, 0 < x -> 0 < x ^ r.
Proof.
  intros x r hx.
  unfold Rpower.pow.
  apply exp_pos.
  apply Rmult_lt_0_compat; [apply ln_pos; exact hx | lra].
Qed.

Lemma cs_pos : forall ck, 0 < ck -> 0 < cs ck.
Proof.
  intros ck hck. unfold cs.
  apply Rinv_0_lt_compat.
  apply Rmult_lt_0_compat; [apply PI_pos | apply rpow_pos; lra].
Qed.

(* ---------- Fibonacci scaffolding ---------- *)

Fixpoint fib (n : nat) : Z :=
  match n with
  | 0 => 0
  | 1 => 1
  | S (S m) => fib (S m) + fib m
  end.

Lemma fib_nonneg : forall n, 0 <= fib n.
Proof.
  induction n as [|m ih] using lt_wf_ind.
  destruct m as [|[|k]]; try lia.
  simpl.
  assert (h1 := H k ltac:(lia)).
  assert (h2 := H (S k) ltac:(lia)).
  lia.
Qed.

Lemma fib_mono : forall n, fib n <= fib (S n).
Proof.
  induction n as [|m ih] using lt_wf_ind.
  destruct m as [|[|k]]; try lia.
  simpl.
  assert (h1 := H (S k) ltac:(lia)).
  assert (h2 := H k ltac:(lia)).
  assert (h3 := fib_nonneg (S k)).
  lia.
Qed.

(* ---------- Cassini identity ---------- *)

Lemma cassini : forall n,
  fib (S n) * fib (S n) - fib n * fib (n + 2) = (-1) ^ n.
Proof.
  induction n as [|m ih].
  - simpl. ring.
  - replace (m + 3) with (S (S (S m))) by lia.
    replace ((-1) ^ S m) with (- ((-1) ^ m)) by (simpl; ring).
    (* fib (S (S (S m))) = fib (S (S m)) + fib (S m), definitionally twice *)
    assert (h3 : fib (S (S (S m))) = fib (S (S m)) + fib (S m)) by (simpl; ring).
    assert (h2 : fib (S (S m)) = fib (S m) + fib m) by (simpl; ring).
    rewrite h3, h2.
    nia.
Qed.

(* ---------- the reduced zero-drift condition (5′) ---------- *)

Definition m1 (R1 delta : R) := Rmax (R1 * R1) (delta * delta).
Definition m2 (R2 delta : R) := Rmax (R2 * R2) (delta * delta).
Definition m_M (R1 R2 delta : R) := Rmax (R1 * R1 + R2 * R2) (delta * delta).

Lemma coeff_aabb : forall k,
  fib k * fib (S k) - fib k * fib (S k) = 0
  /\ fib (S k) * fib (S k) - fib (S k) * fib (S k) = 0
  /\ fib k * fib k - fib k * fib k = 0.
Proof. intros k. repeat split; ring. Qed.

Lemma coeff_abbc_c2 : forall k,
  fib (S k) * fib (S k) - fib k * fib (k + 2) = (-1) ^ k.
Proof. intros k. rewrite Nat.add_2_r. apply cassini. Qed.

Lemma coeff_abbc_cM : forall k,
  fib (S k) * fib (k + 2) - fib k * fib (S k) = fib (S k) * fib (S k).
Proof.
  intros k.
  replace (k + 2) with (S (S k)) by lia.
  assert (h : fib (S (S k)) = fib (S k) + fib k) by (simpl; ring).
  rewrite h. ring.
Qed.

Lemma coeff_abbc_c1_pos : forall k, 2 <= k ->
  0 < fib (k + 2) * fib (k + 2) - fib (S k) * fib (S k).
Proof.
  intros k hk.
  replace (k + 2) with (S (S k)) by lia.
  assert (h : fib (S (S k)) = fib (S k) + fib k) by (simpl; ring).
  rewrite h.
  assert (h1 : 1 <= fib k).
  { destruct k as [|[|j]]; try lia. simpl. lia. }
  assert (h2 : 0 < fib (S k) + fib k).
  { assert (f0 := fib_nonneg k). assert (f1 := fib_nonneg (S k)). lia. }
  nia.
Qed.

(* ---------- admitted analytic properties (ledger TODO_sorry.md) ---------- *)

Lemma cs_exponent_law : forall a ck, 0 < a -> 0 < ck ->
  cs (a * ck) = a ^ (-3/4) * cs ck.
Proof.
  intros a ck ha hck.
  unfold cs.
  replace (3 * (a * ck) / 2) with (a * (3 * ck / 2)) by ring.
  (* (a * x)^(3/4) = a^(3/4) * x^(3/4) — Rpower.pow_mult_r, then ring. *)
Admitted.

Lemma cs_strictAnti : forall x y, 0 < x -> 0 < y -> x < y -> cs y < cs x.
Proof.
  intros x y hx hy hxy.
  unfold cs.
  assert (h2 : 0 < 3 * x / 2) by lra.
  assert (h3 : 0 < 3 * y / 2) by lra.
  assert (hd : (3 * x / 2) ^ (3/4) < (3 * y / 2) ^ (3/4)).
  { apply Rpower.Rlt_pow; lra. }
  lra.
Admitted.

Compute cs (3/2).
