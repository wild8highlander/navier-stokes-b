import Lake
open Lake DSL

package «nsb_verification» where
  leanOptions := #[
    { name := `pp.unicode.fun, value := Lean.LeanOptionValue.ofBool true },
    { name := `autoImplicit, value := Lean.LeanOptionValue.ofBool false },
    { name := `relaxedAutoImplicit, value := Lean.LeanOptionValue.ofBool false },
    { name := `maxSynthPendingDepth, value := Lean.LeanOptionValue.ofNat 3 }
  ]

@[default_target]
lean_lib NsbCore where
  srcDir := "."
  roots := #[`Foundation, `Basic, `BrakingForm, `ProofChain, `Soliton, `KleinQuartic]

require mathlib from git
  "https://github.com/leanprover-community/mathlib4.git" @ "v4.14.0"

lean_exe check where
  root := `Main
