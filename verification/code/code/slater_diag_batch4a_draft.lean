/-
ДРАФТ БАТЧА 4a (не проверен компилятором — окружение Septinal/lean утрачено,
см. STAGE4_PLAN.md). Вставить в SlaterDiag.lean после `cofG_vanish_L`
(перед секцией «Симметрия переворота пары») при восстановлении проекта,
затем lake env lean SlaterDiag.lean и пофиксить тактические расхождения.
Сигнатуры опорных лемм взяты из проверенной версии SlaterDiag_updated.lean.
-/

/-- Сукцессия не имеет неподвижных точек: `s + 1 ≠ s`. -/
theorem slot_succ_ne_self (s : Slot) : s + 1 ≠ s := by
  intro hc
  have hv1 : ((s + 1 : Slot) : ℕ) = ((s : ℕ) + 1) % numSlots := val_suc s
  have hcc : ((s : ℕ)) = ((s : ℕ) + 1) % numSlots :=
    (congrArg Fin.val hc).symm.trans hv1
  have hlt := s.isLt
  rcases Nat.lt_or_ge ((s : ℕ) + 1) numSlots with hlt2 | hge
  · have hmod : ((s : ℕ) + 1) % numSlots = (s : ℕ) + 1 :=
      Nat.mod_eq_of_lt hlt2
    rw [hmod] at hcc
    omega
  · have heq : (s : ℕ) + 1 = numSlots := by omega
    have hmod : ((s : ℕ) + 1) % numSlots = 0 := by
      rw [heq]
      exact Nat.mod_self numSlots
    rw [hmod] at hcc
    have hnn : 2 ≤ numSlots := by
      rw [show numSlots = 22 from rfl]
      norm_num
    omega

/-- Мода всегда меньше числа слотов (элемент `Slot = Fin numSlots`). -/
theorem modeOf_lt (S : Finset Slot) (i : Fin S.card) : modeOf S i < numSlots := by
  have h22 : numSlots = 22 := rfl
  rw [h22]
  unfold modeOf
  exact Fin.isLt _

/-- Знак циклической перестановки столбцов при нечётном размере матрицы: `+1`.
(используется в wrap-вкладе ребра 21). -/
theorem odd_sign_pow (k : ℕ) (hk : Odd k) : (-1 : ℂ) ^ (k - 1) = 1 := by
  rcases hk with ⟨m, hm⟩
  rw [hm]
  show (-1 : ℂ) ^ (2 * m + 1 - 1) = 1
  rw [show (2 * m + 1 - 1 = 2 * m) from by omega, pow_mul, pow_two]
  norm_num

/-- Обнулитель по частице (справа): если сосед справа `u_j + 1` занят,
омега-сумма по колонке `j` нулевая. Обёртка занятости соседа не нужна:
`psi_shift` циклически корректна для любого `u`. -/
theorem slaterVanish_R (S : Finset Slot) (x : Cfg) (h : (supp x).card = S.card)
    (j : Fin S.card)
    (hnext : (((supp x).orderEmbOfFin h j : Slot) + 1 : Slot) ∈ supp x) :
    ∑ i : Fin S.card,
      omega ^ (modeOf S i % numSlots) *
        slaterMat S x h i j * cofG (slaterMat S x h) i j = 0 := by
  obtain ⟨j', hj'⟩ := exists_orderEmbOfFin h
    (((supp x).orderEmbOfFin h j : Slot) + 1) hnext
  have hjj : j ≠ j' := by
    intro hc
    rw [← hc] at hj'
    exact slot_succ_ne_self _ hj'.symm
  set M := slaterMat S x h with hM
  have hcol : ∀ i : Fin S.card, M i j' = omega ^ (modeOf S i % numSlots) * M i j := by
    intro i
    have hps := psi_shift (modeOf S i) ((supp x).orderEmbOfFin h j)
    have hEq : ((supp x).orderEmbOfFin h j' : Slot)
        = ((supp x).orderEmbOfFin h j : Slot) + 1 := hj'
    rw [hEq] at hps
    calc M i j' = psi (modeOf S i) ((supp x).orderEmbOfFin h j') :=
          slaterMat_entry_emb S x h i j'
      _ = omega ^ (modeOf S i % numSlots) * M i j := by
          rw [hps]
          exact (slaterMat_entry_emb S x h i j).symm
  exact cofG_vanish_R M hjj (fun i => omega ^ (modeOf S i % numSlots)) hcol

/-- Обнулитель по частице (слева): если сосед слева `u_j − 1` занят,
омега-сумма по колонке `j` нулевая. Циклический случай `u_j = 0`
(сосед 21) покрывается той же леммой: `psi_pred_shift` корректна для
любого `u`. -/
theorem slaterVanish_L (S : Finset Slot) (x : Cfg) (h : (supp x).card = S.card)
    (j : Fin S.card)
    (hprev : (((supp x).orderEmbOfFin h j : Slot) - 1 : Slot) ∈ supp x) :
    ∑ i : Fin S.card,
      omega ^ (numSlots - modeOf S i % numSlots) *
        slaterMat S x h i j * cofG (slaterMat S x h) i j = 0 := by
  obtain ⟨j'', hj''⟩ := exists_orderEmbOfFin h
    (((supp x).orderEmbOfFin h j : Slot) - 1) hprev
  have hjj : j ≠ j'' := by
    intro hc
    rw [← hc] at hj''
    have hfix : ((supp x).orderEmbOfFin h j : Slot) + 1
        = ((supp x).orderEmbOfFin h j : Slot) := by
      rw [show ((supp x).orderEmbOfFin h j : Slot) + 1
          = ((supp x).orderEmbOfFin h j : Slot) - 1 + 1 from by rw [pred_add_one],
        hj'']
    exact slot_succ_ne_self _ hfix
  set M := slaterMat S x h with hM
  have hcol : ∀ i : Fin S.card, M i j = omega ^ (modeOf S i % numSlots) * M i j'' := by
    intro i
    have hps := psi_pred_shift (modeOf S i) ((supp x).orderEmbOfFin h j)
    have hEq : ((supp x).orderEmbOfFin h j'' : Slot)
        = ((supp x).orderEmbOfFin h j : Slot) - 1 := hj''
    rw [hEq] at hps
    -- psi k (u_j − 1) = ω^{22−k} · psi k u_j, т.е. M i j'' = ω^{22−k}·M i j;
    -- умножая на ω^{k} (произведение = 1 по omega_mul_inv), получаем M i j = ω^{k}·M i j''.
    calc M i j = psi (modeOf S i) ((supp x).orderEmbOfFin h j) :=
          slaterMat_entry_emb S x h i j
      _ = omega ^ (modeOf S i % numSlots) * M i j'' := by
          rw [hEq, slaterMat_entry_emb S x h i j'', hps]
          ring
  exact cofG_vanish_L M hjj (fun i => omega ^ (modeOf S i % numSlots))
    (fun i => omega ^ (numSlots - modeOf S i % numSlots)) hcol
    (fun i => omega_mul_inv (modeOf S i) (modeOf_lt S i))

/-
Замечания к вставке:
1. `omega_mul_inv` требует `(hk : k < numSlots)` — modeOf_lt поставляет.
2. `slaterMat_entry_emb S x h i j` : slaterMat S x h i j
     = psi (modeOf S i) ((supp x).orderEmbOfFin h j).
3. В slaterVanish_R хвост `exact ... .symm` в hjj может потребовать
   перестановки: slot_succ_ne_self _ hj'.symm — цель (u_{j'}) + 1 = u_{j'}
   после rw [← hc] в hj' (hj' : u_{j'} = u_j + 1 → u_j = u_j + 1).
4. В slaterVanish_L ring в calc-шаге работает с omega-степенями как атомами:
   psi k u_j = ω^k · (ω^{22−k} · psi k u_j) — верно (ω^k·ω^{22−k} = 1),
   но ring видит ω^k и ω^{22−k} как независимые атомы и НЕ свернёт;
   если ring не закроет — вставить явную omega_mul_inv-подстановку:
     have hinv := omega_mul_inv (modeOf S i) (modeOf_lt S i)
     rw [← mul_assoc, mul_comm (omega ^ (modeOf S i % numSlots))
       (omega ^ (numSlots - modeOf S i % numSlots)), hinv, one_mul]
5. set-with-hM: если `set` мешает rewrites по slaterMat — убрать и использовать
   полную форму.
-/
