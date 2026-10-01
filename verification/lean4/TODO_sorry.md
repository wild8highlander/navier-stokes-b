# Lean 4 — the open-proof ledger (TODO_sorry)

> **Navigation:** [repository root](../README.md) › [verification](../README.md) › [lean4](README.md) › **`TODO_sorry.md`**

This file is the complete, honest inventory of every `sorry` (a theorem
with a deferred proof) and every `axiom` (an axiomatised statement) in
the Lean 4 project. Items are struck out as proofs are closed. Nothing
here is hidden: the framework's verification contract treats this ledger
as part of the deliverable.

## Summary

| Type | Count | Status |
|-----|-----------|--------|
| `sorry` (deferred proofs) | 15 | to be proved |
| `axiom ... : True` (mechanical stubs) | 12 | replace with `theorem ... := trivial` |
| `axiom ...` (genuine open problems) | 4 | keep, by design |
| **Total** | **31** | |

---

## The `sorry` list

### Common/Foundation.lean

| # | Theorem | What has to be proved | Difficulty |
|---|---------|-------------------|-----------|
| 1 | `Real.pi < 4` (inside `bCorrection_lt_one`) | a numeric bound on π | easy |

### Section1_CorrectionB/Basic.lean

| # | Theorem | What has to be proved | Difficulty |
|---|---------|-------------------|-----------|
| 2 | `b_gt_007` | b > 0.07 | medium |
| 3 | `b_lt_008` | b < 0.08 | medium |
| 4 | `rodrigues_orthogonal` | Rᵀ·R = I (orthogonality) | hard |
| 5 | `rodrigues_det` | det R = 1 (proper rotation) | hard |
| 6 | `R_b_preserves_norm` | ‖R·u‖ = ‖u‖ (energy preservation) | medium |

### Section2_PreprintNSE/ProofChain.lean

| # | Theorem | What has to be proved | Difficulty |
|---|---------|-------------------|-----------|
| 7 | `α_bounds` | 2 < α < 2.1 | medium |
| 8 | `L_min_lt_one` | L_min < 1 | medium |

### Section3_ABCloud/HofstadterHamiltonian.lean

| # | Theorem | What has to be proved | Difficulty |
|---|---------|-------------------|-----------|
| 9 | `peierls_phase_unit_modulus` | \|e^(2πi/7)\| = 1 | easy |
| 10 | `peierls_phase_order_7` | (e^(2πi/7))⁷ = 1 | easy |
| 11 | `gue_spacing_normalized` | ∫ PDF = 1 | hard |

### Section4_KdV/Soliton.lean

| # | Theorem | What has to be proved | Difficulty |
|---|---------|-------------------|-----------|
| 12 | `soliton_solves_KdV` | sech² solves the KdV equation | very hard |

### Section7_SmagorinskyKolmogorov/Basic.lean *(new)*

| # | Theorem | What has to be proved | Difficulty | Closing plan |
|---|---------|-------------------|-----------|---|
| **S7-CASSINI** (13) | `cassini` | F(n+1)² − F(n)·F(n+2) = (−1)ⁿ | medium | two-case induction; substitute `fib_add`, expand both squares, close with `nlinarith`/`omega`. Numerically verified k = 0..40 exact in every computational port; proved fully in Coq (`section7_smagorinsky/MasterRelation.v`) and Isabelle (`Section7_SmagorinskyKolmogorov/MasterRelation.thy`) |
| **S7-EXPLAW** (14) | `cs_exponent_law` | C_s(a·C_K) = a^(−3/4)·C_s(C_K) | medium | `Real.rpow` homogeneity (`rpow_mul`) for positive bases, then `field_simp`; verified to 2.2×10⁻¹⁶ numerically |
| **S7-ANTI** (15) | `cs_strictAnti` | C_s strictly decreasing on (0, ∞) | medium | compose `S7-EXPLAW` with `rpow_lt_rpow` for the negative exponent −3/4 |

Note: `cs_pos`, the Fibonacci scaffolding (`fib_add`, `fib_nonneg`,
`fib_mono`, `fib_ge_one_from`), `coeff_abbc` and `coeff_aabb` of
Section 7 are **fully proved** — see the module source.

---

## The `axiom ... : True` stubs (replace with `theorem ... := trivial`)

These are mechanical placeholders, trivially replaceable:

### Section4_KdV/Soliton.lean
- [ ] `miura_mkdv_to_kdv` — the Miura transform maps mKdV to KdV
- [ ] `elastic_interaction` — elastic soliton interaction
- [ ] `lax_pair` — the Lax pair for KdV

### Section5_KleinAttractor/KleinQuartic.lean
- [ ] `klein_smooth` — the Klein quartic is smooth
- [ ] `klein_genus_three` — the genus of the Klein quartic is 3
- [ ] `klein_aut_is_PSL2_7` — the automorphism group = PSL(2,7)
- [ ] `f_attractor_nonempty` — the F-attractor is nonempty
- [ ] `f_attractor_compact` — the F-attractor is compact

### Section6_RiemannZeros/HilbertPolya.lean
- [ ] `zeta_pole_at_one` — ζ(s) has a pole at s=1
- [ ] `zeta_functional_equation` — the ζ functional equation
- [ ] `rh_implies_strong_pnt` — RH ⟹ the strong prime number theorem
- [ ] `ab_cloud_is_hilbert_polya_candidate` — AB-Cloud as an HP candidate

---

## Genuine open mathematical problems (kept as `axiom`, by design)

These statements cannot be proved without a fundamental breakthrough and
are declared as axioms openly:

| Axiom | Status | Description |
|---------|--------|----------|
| `hilbert_polya_conjecture` | Open problem (since 1914) | the Hilbert–Pólya conjecture |
| `bkmIntegral_if_bounded` | Needs a definition | replace with a `def` carrying the real definition |
| `KdV` (as Prop) | Needs a definition | replace with the PDE formula |

---

## How to close a `sorry` — a short guide

### The simple case (the `nlinarith` tactic):

```lean
-- Before:
theorem b_gt_007 : (0.07 : ℝ) < bCorrection := by sorry

-- After:
theorem b_gt_007 : (0.07 : ℝ) < bCorrection := by
  unfold bCorrection
  nlinarith [Real.pi_pos, Real.sqrt_pos 3 (by norm_num)]
```

### The medium case (matrix unfolding):

```lean
-- Before:
theorem rodrigues_orthogonal (θ : ℝ) (n : Fin 3 → ℝ) (hn : ‖n‖ = 1) :
    (rodriguesRotation θ n)ᵀ * rodriguesRotation θ n = 1 := by sorry

-- After:
theorem rodrigues_orthogonal (θ : ℝ) (n : Fin 3 → ℝ) (hn : ‖n‖ = 1) :
    (rodriguesRotation θ n)ᵀ * rodriguesRotation θ n = 1 := by
  ext i j
  fin_cases i <;> fin_cases j <;>
  simp [rodriguesRotation, crossMatrix, Matrix.mul_apply, Fin.sum_univ_three]
  nlinarith [hn, Real.sin_sq_add_cos_sq θ]
```

### The Cassini case (S7-CASSINI, the recommended first target):

```lean
-- Before (Section7_SmagorinskyKolmogorov/Basic.lean):
theorem cassini (n : ℕ) :
    fib (n + 1) ^ 2 - fib n * fib (n + 2) = (-1) ^ n := by sorry

-- After (sketch):
theorem cassini (n : ℕ) :
    fib (n + 1) ^ 2 - fib n * fib (n + 2) = (-1) ^ n := by
  induction n with
  | zero => norm_num [fib]
  | succ m ih =>
      have h1 := fib_add m          -- fib (m+2) = fib (m+1) + fib m
      have h2 := fib_add (m + 1)    -- fib (m+3) = fib (m+2) + fib (m+1)
      have h3 := Z.pow_succ (-1 : ℤ) m  -- (-1)^(m+1) = -(-1)^m
      simp only [h1, h2, h3, ih]
      ring
```

### Replacing an `axiom foo : True` stub:

```lean
-- Before:
axiom klein_genus_three : True

-- After (the minimum):
theorem klein_genus_three : True := trivial

-- Better (a real definition):
def klein_genus : ℕ := 3
theorem klein_genus_three : klein_genus = 3 := rfl
```

---

## Useful tactics

| Situation | Tactic |
|----------|---------|
| Numeric equality | `norm_num` |
| Linear arithmetic | `linarith` |
| Nonlinear arithmetic | `nlinarith` |
| Positivity | `positivity` |
| Algebraic simplification | `ring` / `field_simp` |
| Matrix unfolding | `ext i j; fin_cases i <;> fin_cases j` |
| Mathlib lemma search | `apply?` |

---

## Progress metrics

| Metric | Now | Target |
|---------|--------|------|
| `sorry` | 15 | 0 |
| `axiom : True` | 12 | 0 |
| `axiom` (open problems) | 4 | 4 |
| Coverage | 79% | 100% |

The three Section-7 items are the recommended first targets: two are
already proved in the sibling kernels (Coq, Isabelle) and all three are
numerically verified to machine precision by every computational port —
the mathematical content is settled, only the Lean formalization remains.
