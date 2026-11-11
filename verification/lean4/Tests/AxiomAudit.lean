import Basic
import BrakingForm
import ProofChain
import KleinQuartic

/- Tests/AxiomAudit.lean — печать аксиомной базы центральных теорем.
   Каждая строка `#print axioms` выводит список аксиом, от которых зависит
   теорема. Допустимая база — только встроенные аксиомы Lean/Mathlib:
   propext, Quot.sound, Classical.choice, Lean.ofReduceBool.
   Автоматический контроль: verification/tests/test_lean_core.py
   (запускает этот файл через `lake env lean`, если lake установлен)
   и verification/tools/audit/audit_lean.py (статический аудит).
   Замена и расширение списка — вместе с обновлением теста. -/

-- Section1 (Basic.lean): константа b и алгебра вращения Родрига
#print axioms Section1.rodrigues_orthogonal
#print axioms Section1.R_b_orthogonal
#print axioms Section1.R_b_det_one
#print axioms Section1.R_b_preserves_norm
#print axioms Section1.sin_θ_b_eq_b
#print axioms Section1.b_gt_062
#print axioms Section1.b_lt_063
#print axioms Section1.b_pos
#print axioms Section1.b_lt_one

-- Braking2D (BrakingForm.lean): тормозной протокол на модах
#print axioms Braking2D.vort_brakingStep_div_free
#print axioms Braking2D.vort_brakingIter
#print axioms Braking2D.vort_brakingIter_superpos
#print axioms Braking2D.bkm_factor
#print axioms Braking2D.brakingStep_energy_le
#print axioms Braking2D.leray_energy
#print axioms Braking2D.rot_energy

-- Protocol (BrakingForm.lean): протокол ODE и γ_eff
#print axioms Protocol.protocol_ode_form
#print axioms Protocol.gammaEff_ratio_tendsto
#print axioms Protocol.theta_b_pos
#print axioms Protocol.pow_cos_lt_one

-- VortexTube (BrakingForm.lean): вихревая трубка и точные значения
#print axioms VortexTube.moment_total
#print axioms VortexTube.moment_nonpos
#print axioms VortexTube.sin_θ_b_eq_kirchhoff_value
#print axioms VortexTube.b_eq_kirchhoff_value
#print axioms VortexTube.ode_solution

-- Section2 (ProofChain.lean): цепочка α, L_min, γ
#print axioms Section2.γ_eq_b
#print axioms Section2.L_min_times_α_eq_one
#print axioms Section2.α_bounds
#print axioms Section2.L_min_lt_one

-- Section5 (KleinQuartic.lean): мост Клейна → регулярность
#print axioms Section5.klein_bridge_implies_nse_regularity
