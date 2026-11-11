import Foundation
import Basic
import BrakingForm
import ProofChain
import Soliton
import KleinQuartic

/- `totalVerifiedTheorems` — статический подсчёт объявлений `theorem`
в шести основных модулях пакета (Foundation, Basic, BrakingForm,
ProofChain, Soliton, KleinQuartic). Значение обновляется вручную вместе
с модулями; динамический контроль — `python3 tools/audit/audit_lean.py`
(считает то же самое из исходников). -/
def totalVerifiedTheorems : Nat := 72

def main : IO Unit := do
  IO.println "Lean 4 type-check OK"
  IO.println s!"Modules: Foundation, Basic, BrakingForm, ProofChain, Soliton, KleinQuartic"
  IO.println s!"Total formal theorems: {totalVerifiedTheorems}"
