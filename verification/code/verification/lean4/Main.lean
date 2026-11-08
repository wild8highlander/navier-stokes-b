import ResearchPapersVerification

def main : IO Unit := do
  IO.println "Lean 4 type-check OK"
  IO.println s!"Total formal theorems: {totalVerifiedTheorems}"
