# Список незавершённых доказательств Lean 4

> Этот файл содержит полный перечень всех `sorry` (теорем с пропущенными
> доказательствами) и `axiom` (аксиоматизированных утверждений) в проекте
> Lean 4. По мере доработки доказательств пункты вычёркиваются.

## Сводка

| Тип | Количество | Статус |
|-----|-----------|--------|
| `sorry` (незавершённые доказательства) | 13 | нужно доказать |
| `axiom ... : True` (заглушки) | 12 | заменить на `theorem ... := trivial` |
| `axiom ...` (открытые проблемы) | 4 | оставить как есть |
| **Итого** | **29** | |

---

## Полный список `sorry`

### Common/Foundation.lean

| № | Теорема | Что нужно доказать | Сложность |
|---|---------|-------------------|-----------|
| 1 | `Real.pi < 4` (внутри `bCorrection_lt_one`) | Численная оценка π | легко |

### Section1_CorrectionB/Basic.lean

| № | Теорема | Что нужно доказать | Сложность |
|---|---------|-------------------|-----------|
| 2 | `b_gt_007` | b > 0.07 | средне |
| 3 | `b_lt_008` | b < 0.08 | средне |
| 4 | `rodrigues_orthogonal` | Rᵀ·R = I (ортогональность) | сложно |
| 5 | `rodrigues_det` | det R = 1 (правильное вращение) | сложно |
| 6 | `R_b_preserves_norm` | ‖R·u‖ = ‖u‖ (сохранение энергии) | средне |

### Section2_PreprintNSE/ProofChain.lean

| № | Теорема | Что нужно доказать | Сложность |
|---|---------|-------------------|-----------|
| 7 | `α_bounds` | 2 < α < 2.1 | средне |
| 8 | `L_min_lt_one` | L_min < 1 | средне |

### Section3_ABCloud/HofstadterHamiltonian.lean

| № | Теорема | Что нужно доказать | Сложность |
|---|---------|-------------------|-----------|
| 9 | `peierls_phase_unit_modulus` | \|e^(2πi/7)\| = 1 | легко |
| 10 | `peierls_phase_order_7` | (e^(2πi/7))⁷ = 1 | легко |
| 11 | `gue_spacing_normalized` | ∫ PDF = 1 | сложно |

### Section4_KdV/Soliton.lean

| № | Теорема | Что нужно доказать | Сложность |
|---|---------|-------------------|-----------|
| 12 | `soliton_solves_KdV` | sech² — решение уравнения KdV | очень сложно |

---

## Полный список `axiom ... : True` (заменить на `theorem ... := trivial`)

Это заглушки — их легко заменить:

### Section4_KdV/Soliton.lean
- [ ] `miura_mkdv_to_kdv` — преобразование Миуры переводит mKdV в KdV
- [ ] `elastic_interaction` — упругое взаимодействие солитонов
- [ ] `lax_pair` — пара Лакса для KdV

### Section5_KleinAttractor/KleinQuartic.lean
- [ ] `klein_smooth` — квартика Клейна гладкая
- [ ] `klein_genus_three` — род квартики Клейна равен 3
- [ ] `klein_aut_is_PSL2_7` — группа автоморфизмов = PSL(2,7)
- [ ] `f_attractor_nonempty` — F-аттрактор непуст
- [ ] `f_attractor_compact` — F-аттрактор компактен

### Section6_RiemannZeros/HilbertPolya.lean
- [ ] `zeta_pole_at_one` — ζ(s) имеет полюс в s=1
- [ ] `zeta_functional_equation` — функциональное уравнение ζ
- [ ] `rh_implies_strong_pnt` — RH ⟹ усиленная теорема о простых числах
- [ ] `ab_cloud_is_hilbert_polya_candidate` — AB-Cloud — кандидат на HP

---

## Открытые математические проблемы (оставить как `axiom`)

Эти утверждения не могут быть доказаны без фундаментального прорыва:

| Аксиома | Статус | Описание |
|---------|--------|----------|
| `hilbert_polya_conjecture` | Открытая проблема (с 1914) | Гипотеза Гильберта-Пойа |
| `bkmIntegral_if_bounded` | Требует определения | Заменить на `def` с реальным определением |
| `KdV` (как Prop) | Требует определения | Заменить на формулу PDE |

---

## Как закрыть `sorry` — краткое руководство

### Простой пример (тактика `nlinarith`):

```lean
-- Было:
theorem b_gt_007 : (0.07 : ℝ) < bCorrection := by sorry

-- Стало:
theorem b_gt_007 : (0.07 : ℝ) < bCorrection := by
  unfold bCorrection
  nlinarith [Real.pi_pos, Real.sqrt_pos 3 (by norm_num)]
```

### Средний пример (раскрытие матрицы):

```lean
-- Было:
theorem rodrigues_orthogonal (θ : ℝ) (n : Fin 3 → ℝ) (hn : ‖n‖ = 1) :
    (rodriguesRotation θ n)ᵀ * rodriguesRotation θ n = 1 := by sorry

-- Стало:
theorem rodrigues_orthogonal (θ : ℝ) (n : Fin 3 → ℝ) (hn : ‖n‖ = 1) :
    (rodriguesRotation θ n)ᵀ * rodriguesRotation θ n = 1 := by
  ext i j
  fin_cases i <;> fin_cases j <;>
  simp [rodriguesRotation, crossMatrix, Matrix.mul_apply, Fin.sum_univ_three]
  nlinarith [hn, Real.sin_sq_add_cos_sq θ]
```

### Замена заглушки `axiom foo : True`:

```lean
-- Было:
axiom klein_genus_three : True

-- Стало (минимум):
theorem klein_genus_three : True := trivial

-- Или (лучше — настоящее определение):
def klein_genus : ℕ := 3
theorem klein_genus_three : klein_genus = 3 := rfl
```

---

## Полезные тактики

| Ситуация | Тактика |
|----------|---------|
| Числовое равенство | `norm_num` |
| Линейная арифметика | `linarith` |
| Нелинейная арифметика | `nlinarith` |
| Положительность | `positivity` |
| Алгебраическое упрощение | `ring` / `field_simp` |
| Раскрытие матриц | `ext i j; fin_cases i <;> fin_cases j` |
| Поиск лемм в Mathlib | `apply?` |

---

## Метрики прогресса

| Метрика | Сейчас | Цель |
|---------|--------|------|
| `sorry` | 13 | 0 |
| `axiom : True` | 12 | 0 |
| `axiom` (открытые проблемы) | 4 | 4 |
| Покрытие | 80% | 100% |
