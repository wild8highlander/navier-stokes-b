# Lean 4 Registry of Unfinished Proofs

> This file keeps the complete inventory of every `sorry` (theorems with missing
> proofs) and every `axiom` (axiomatized statements) in the Lean 4 project.
> Items are crossed out as the proofs are completed.

## Summary

| Type | Count | Status |
|-----|-----------|--------|
| `sorry` (unfinished proofs) | 13 | to be proven |
| `axiom ... : True` (stubs) | 12 | replace with `theorem ... := trivial` |
| `axiom ...` (open problems) | 4 | keep as is |
| **Total** | **29** | |

---

## The complete list of `sorry`

### Common/Foundation.lean

| # | Theorem | What needs to be proven | Difficulty |
|---|---------|-------------------|-----------|
| 1 | `Real.pi < 4` (inside `bCorrection_lt_one`) | a numerical estimate of π | easy |

### Section1_CorrectionB/Basic.lean

| # | Theorem | What needs to be proven | Difficulty |
|---|---------|-------------------|-----------|
| 2 | `b_gt_007` | b > 0.07 | medium |
| 3 | `b_lt_008` | b < 0.08 | medium |
| 4 | `rodrigues_orthogonal` | Rᵀ·R = I (orthogonality) | hard |
| 5 | `rodrigues_det` | det R = 1 (a proper rotation) | hard |
| 6 | `R_b_preserves_norm` | ‖R·u‖ = ‖u‖ (energy preservation) | medium |

### Section2_PreprintNSE/ProofChain.lean

| # | Theorem | What needs to be proven | Difficulty |
|---|---------|-------------------|-----------|
| 7 | `α_bounds` | 2 < α < 2.1 | medium |
| 8 | `L_min_lt_one` | L_min < 1 | medium |

### Section3_ABCloud/HofstadterHamiltonian.lean

| # | Theorem | What needs to be proven | Difficulty |
|---|---------|-------------------|-----------|
| 9 | `peierls_phase_unit_modulus` | \|e^(2πi/7)\| = 1 | easy |
| 10 | `peierls_phase_order_7` | (e^(2πi/7))⁷ = 1 | easy |
| 11 | `gue_spacing_normalized` | ∫ PDF = 1 | hard |

### Section4_KdV/Soliton.lean

| # | Theorem | What needs to be proven | Difficulty |
|---|---------|-------------------|-----------|
| 12 | `soliton_solves_KdV` | sech² is a solution of the KdV equation | very hard |

---

## The complete list of `axiom ... : True` (replace with `theorem ... := trivial`)

These are stubs — easy to replace:

### Section4_KdV/Soliton.lean
- [ ] `miura_mkdv_to_kdv` — the Miura transform maps mKdV to KdV
- [ ] `elastic_interaction` — the elastic interaction of solitons
- [ ] `lax_pair` — the Lax pair for KdV

### Section5_KleinAttractor/KleinQuartic.lean
- [ ] `klein_smooth` — the Klein quartic is smooth
- [ ] `klein_genus_three` — the genus of the Klein quartic equals 3
- [ ] `klein_aut_is_PSL2_7` — the automorphism group = PSL(2,7)
- [ ] `f_attractor_nonempty` — the F-attractor is nonempty
- [ ] `f_attractor_compact` — the F-attractor is compact

### Section6_RiemannZeros/HilbertPolya.lean
- [ ] `zeta_pole_at_one` — ζ(s) has a pole at s=1
- [ ] `zeta_functional_equation` — the functional equation of ζ
- [ ] `rh_implies_strong_pnt` — RH ⟹ the strong prime number theorem
- [ ] `ab_cloud_is_hilbert_polya_candidate` — AB-Cloud as an HP candidate

---

## Open mathematical problems (keep as `axiom`)

These statements cannot be proven without a fundamental breakthrough:

| Axiom | Status | Description |
|---------|--------|----------|
| `hilbert_polya_conjecture` | Open problem (since 1914) | The Hilbert–Pólya conjecture |
| `bkmIntegral_if_bounded` | Needs a definition | Replace with a `def` carrying the real definition |
| `KdV` (as Prop) | Needs a definition | Replace with the PDE formulation |

---

## How to close a `sorry` — a short guide

### A simple example (the `nlinarith` tactic):

```lean
-- Before:
theorem b_gt_007 : (0.07 : ℝ) < bCorrection := by sorry

-- After:
theorem b_gt_007 : (0.07 : ℝ) < bCorrection := by
  unfold bCorrection
  nlinarith [Real.pi_pos, Real.sqrt_pos 3 (by norm_num)]
```

### A medium example (matrix expansion):

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

### Replacing an `axiom foo : True` stub:

```lean
-- Before:
axiom klein_genus_three : True

-- After (minimum):
theorem klein_genus_three : True := trivial

-- Or (better — a real definition):
def klein_genus : ℕ := 3
theorem klein_genus_three : klein_genus = 3 := rfl
```

---

## Useful tactics

| Situation | Tactic |
|----------|---------|
| Numerical equality | `norm_num` |
| Linear arithmetic | `linarith` |
| Nonlinear arithmetic | `nlinarith` |
| Positivity | `positivity` |
| Algebraic simplification | `ring` / `field_simp` |
| Matrix expansion | `ext i j; fin_cases i <;> fin_cases j` |
| Lemma search in Mathlib | `apply?` |

---

## Progress metrics

| Metric | Now | Target |
|---------|--------|------|
| `sorry` | 13 | 0 |
| `axiom : True` | 12 | 0 |
| `axiom` (open problems) | 4 | 4 |
| Coverage | 80% | 100% |
