import Lake
open Lake DSL

package «research_papers_verification» where
  leanOptions := #[
    ⟨`pp.unicode.fun, true⟩,
    ⟨`autoImplicit, false⟩,
    ⟨`relaxedAutoImplicit, false⟩,
    ⟨`maxSynthPendingDepth, 3⟩
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
