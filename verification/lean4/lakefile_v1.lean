import Lake
open Lake DSL

package «research_papers_verification» where
  leanOptions := #[
    { name := `pp.unicode.fun, value := Lean.LeanOptionValue.ofBool true },
    { name := `autoImplicit, value := Lean.LeanOptionValue.ofBool false },
    { name := `relaxedAutoImplicit, value := Lean.LeanOptionValue.ofBool false },
    { name := `maxSynthPendingDepth, value := Lean.LeanOptionValue.ofNat 3 }
  ]

lean_lib ResearchPapersVerification where
  srcDir := "."
  roots := #[`ResearchPapersVerification]

require mathlib from git
  "https://github.com/leanprover-community/mathlib4.git" @ "v4.14.0"

lean_exe check where
  root := `Main

lean_exe test where
  root := `Test
