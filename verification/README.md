# 🔬 `verification/` — the Eleven-Language Verification Framework

> **Navigation:** [repository root](../README.md) › **`verification`**

![Languages](https://img.shields.io/badge/Languages-11-9558B2?style=flat-square)
![Tier1](https://img.shields.io/badge/Tier_1-Formal_proofs-1284BA?style=flat-square)
![Tier2](https://img.shields.io/badge/Tier_2-Computational-2EA043?style=flat-square)
![Contract](https://img.shields.io/badge/Contract-PASS_%2B_JSON-FF8C00?style=flat-square)
![License](https://img.shields.io/badge/License-IPL--RP--1.0-red?style=flat-square)

This directory is the **independent verification framework** of the
repository: every headline claim of the research programs is re-derived
here, in **eleven programming languages**, from a single shared contract —
run a verifier, it prints per-assertion `[PASS]`/`[FAIL]` lines plus a
final `JSON: {...}` verdict, and exits non-zero on any failure. Four proof
assistants machine-check the structural facts; seven computational
languages re-derive the numbers from first principles with no hidden
dependencies. When four kernels with different foundations and seven
arithmetics with different rounding all agree, the residual risk is
concentrated where it belongs — in the modelling, not in the mechanics.

## The two tiers, precisely

**Tier 1 — proof assistants (formal verification):**
- [`lean4/`](lean4/README.md) — Lean 4 (v4.14, Mathlib4): machine-checked
  proofs of the correction-b bounds, the rotation algebra, NSE stability
  scaffolding and the AB-Cloud structural theorems; the largest formal
  artifact, with an honest, itemised gap ledger
  ([`TODO_sorry.md`](lean4/TODO_sorry.md));
- [`coq/`](coq/README.md) — Coq/Rocq (8.18): classical `Reals`-based
  proofs with `lra` automation; the files `Compute` the constants as they
  compile, so the reviewer sees the numbers during the build;
- [`isabelle/`](isabelle/README.md) — Isabelle-HOL (2024): an independent
  restatement in Isar over `Complex_Main`, written to be *read*;
- [`agda/`](agda/README.md) — Agda (2.6): a dependently-typed constructive
  development with the minimal trust base made literal — π and √3 are
  explicit `postulate`s, everything else is constructed.

**Tier 2 — computational languages (numerical verification):**
- [`python_levels/`](python_levels/README.md) — the L1–L5 chain: exact
  constants (mpmath, 50 digits), rotation algebra, Kirchhoff vortices,
  2D NSE identities, and the 3D Taylor–Green BKM protocol;
- [`section1_correction_b/`](section1_correction_b/README.md) …
  [`section6_riemann_zeros/`](section6_riemann_zeros/README.md) —
  pure-Python reference implementations of the six research sections
  (stdlib-only, the executable definitions of the claims);
- [`cpp/`](cpp/README.md) — C++17 ports with a uniform `check()` harness
  (CMake, BLAS/LAPACK, the pseudospectral KdV workhorse);
- [`rust/`](rust/README.md) — memory-safe Rust ports (std-only Cargo
  workspace, one binary per section);
- [`haskell/`](haskell/README.md) — GHC 9.4 ports (Cabal project, pure
  functional idioms);
- [`julia_levels/`](julia_levels/README.md) — a fully independent Julia
  implementation of L1–L5 (stdlib-only, own radix-2 FFT).

**Infrastructure:**
- [`common/`](common/README.md) — shared Python utilities (verifier base
  class, config, aggregate CLI);
- [`api/`](api/README.md) — REST API exposing the verifiers over HTTP;
- [`demo/`](demo/README.md) — interactive Gradio and Streamlit front-ends;
- [`docker/`](docker/README.md) — one pinned container per toolchain
  (lean4, coq, isabelle, agda, cpp, rust, haskell);
- [`tests/`](tests/README.md) — the cross-language validator and the
  extended-language integration tests;
- [`scripts/`](scripts/README.md) — cross-validation and API bootstrap
  shell scripts;
- [`notebooks/`](notebooks/README.md) — the Jupyter entry point;
- [`docs/extended-languages/`](docs/README.md) — notes on the extended
  toolchains;
- [`web-dashboard/`](web-dashboard/README.md) — the dashboard package
  manifest.

## The six sections

The six research sections map 1-to-1 onto the research program of the
root README:

| # | Section | Directory | What it verifies |
|---|---|---|---|
| 1 | Correction b — the universal polarization constant | [`section1_correction_b/`](section1_correction_b/README.md) | closed-form value, 0 < b < 1, sin θ_b = b, rotation sanity |
| 2 | Preprint NSE — the regularity chain | [`section2_preprint/`](section2_preprint/README.md) | twist unitarity, BKM bound under the twist, estimate ordering |
| 3 | AB-Cloud — the Hofstadter Hamiltonian | [`section3_ab_cloud/`](section3_ab_cloud/README.md) | flux quantisation, Hermiticity, symmetry classes |
| 4 | KdV — soliton interactions | [`section4_kdv/`](section4_kdv/README.md) | conserved quantities across the interaction, two-soliton closed form |
| 5 | Klein attractor | [`section5_klein_attractor/`](section5_klein_attractor/README.md) | invariant statistics, contraction statements, the NSE bridge |
| 6 | Riemann zeros — the Hilbert–Pólya programme | [`section6_riemann_zeros/`](section6_riemann_zeros/README.md) | frozen-data embedding, GUE-class gap statistics, Σ²(L) diagnostics |

Each section exists as a Python reference port (the directory above), a
formal port in each of the four proof assistants
([`lean4/ResearchPapersVerification/Section1_CorrectionB/`](lean4/README.md)
and its siblings) and an extended computational port in C++, Rust and
Haskell — the full matrix is tabulated in each section's README.

## 📜 The verification contract

Every computational port in this framework follows one output contract,
which is what makes cross-language comparison mechanical:

1. print a banner line identifying section and language;
2. compute the section's quantities from closed-form inputs (no data
   files needed at this tier);
3. assert each expected property, printing
   `[PASS] name: expected=…, actual=…` or `[FAIL] …`;
4. print a final line
   `JSON: {"section": N, "language": "<lang>", "values": {…}, "all_passed": true|false}`;
5. exit with status 0 only if every assertion passed.

The formal tier mirrors the same assertions as lemmas (`b_pos`,
`b_lt_one`, `sin_θ_b_eq_b`, `R_b_orthogonal`, …) so that a reviewer can
diff the *mathematical content* across systems rather than the code
style. The contract is the only invariant that matters; everything else
is convention — and a change to the contract must update the validator,
the matrix and every affected port in one atomic commit.

## 🚀 Running the framework

```bash
# from the repository root:
make install          # python environment
make verify-all       # python reference implementations (sections 1–6)
make verify-extended  # extended toolchains (requires those installed)

# or directly, per language:
python3  verification/section1_correction_b/python/verify.py
cargo run --release --manifest-path verification/rust/Cargo.toml
cmake -S verification/cpp -B /tmp/cppbuild && cmake --build /tmp/cppbuild

# the L1–L5 chain (python) and its independent julia twin:
python3 verification/python_levels/verify_all.py     # ~20 min; NSE3D_SKIP=1 for fast
julia   verification/julia_levels/verify_all.jl      # ~5–15 min; NSE3D_SKIP=1 for fast

# formal tier:
cd verification/lean4 && lake build && lake exe check
cd verification/isabelle && isabelle build -D .

# integrity + cross-language agreement:
make verify-manifest
python3 verification/tests/extended_cross_language_validator.py
```

Docker images pin every formal toolchain — see
[`docker/`](docker/README.md). The REST API
([`api/server.py`](api/README.md)) runs the same verifiers over HTTP for
scripted audits, and [`demo/`](demo/README.md) wraps them in Gradio and
Streamlit UIs.

## 🧭 Three ways in, by goal

**"I want to see it work in the next two minutes."**
Run the smoke test: `python3 verification/section1_correction_b/python/verify.py`.
It prints the section banner, the computed constant, `PASS`, and exits 0 —
no dependencies, no configuration. Then `make verify-all` for all six
sections.

**"I want to audit one claim end-to-end."**
Pick the claim in the root README's results table, follow its link to the
section directory, and read this chain: section README (what is claimed)
→ Python port (executable definition) → formal file (structural skeleton)
→ validator result. The worked example below narrates this for Section 1.

**"I want to add a port or a section."**
Read the contract above, mirror an existing port's structure, join the
validator's matrix in the same commit, and update every affected README —
the [contribution guide](../CONTRIBUTING.md) has the checklist.

## 🧪 Worked example: auditing Section 1 in ten minutes

1. **Claim list.** Open
   [`section1_correction_b/README.md`](section1_correction_b/README.md):
   four assertions (positive, < 1, sine identity, rotation sanity).
2. **Reference run.** `python3 verification/section1_correction_b/python/verify.py`
   → `b = 0.062381194121028`, `PASS`, exit 0.
3. **Second language.** `cargo run --release -p section1_correction_b` —
   same banner shape, same PASS pattern, its own JSON verdict.
4. **Validator.** `python3 verification/tests/extended_cross_language_validator.py`
   — confirms sections 1–6 agree across languages in one shot.
5. **Formal check.** Open
   [`lean4/ResearchPapersVerification/Common/Foundation.lean`](lean4/README.md):
   the closed-form definition and the positivity theorem; `sin_θ_b_eq_b`
   in Section 1's file. Compare the statement, not the syntax, with the
   claim list.
6. **Gap check.** [`lean4/TODO_sorry.md`](lean4/TODO_sorry.md) — which
   numeric-bound lemmas are admitted gaps. Your audit now knows exactly
   what is compiled, what is computed, and what is admitted.

Ten minutes, one section, the entire evidence chain. Multiply by the other
five sections at your leisure.

## 🔬 What each tier contributes

- **Lean 4** carries the primary formal development: the closed-form
  constant, its bounds, the rotation algebra and the per-section
  scaffolding, with the gap ledger
  ([`TODO_sorry.md`](lean4/TODO_sorry.md): 13 `sorry`s, 12 mechanical
  `axiom : True` stubs, 4 open-problem axioms — each with a difficulty
  estimate and a closing plan).
- **Coq** is the classical-logic witness: `lra`-automated `Reals` proofs
  show the statements' content is routine classical mathematics — the hard
  part is the modelling, not the arithmetic.
- **Isabelle** is the independent restatement: written afresh in Isar from
  the papers, not translated from Lean, so agreement is evidence rather
  than tautology.
- **Agda** enumerates the trust base: two postulates (π, √3), everything
  else constructed.
- **Python** is the executable definition: stdlib-only reference ports of
  the six sections and the L1–L5 chain with mpmath exactness.
- **C++** is the performance witness and the KdV workhorse (BLAS/LAPACK,
  pseudospectral solver) inside the same contract.
- **Rust** proves the sections need *nothing*: six crates, zero external
  dependencies, the contract still holds.
- **Haskell** proves the contract survives paradigm distance: pure
  functions, types as specifications.
- **Julia** is the independent recomputation of the whole L1–L5 chain —
  including its own radix-2 FFT, self-tested against a direct DFT — at a
  different grid size (N = 32), which makes it a genuinely independent
  benchmark rather than a port of the same task.

## 🧬 The validator, under the hood

[`tests/extended_cross_language_validator.py`](tests/README.md) is the
framework's referee; its logic is deliberately transparent:

1. **Collect** — run every registered port (or read archived verdicts),
   parse each port's single `JSON: {...}` line;
2. **Normalise** — map section number → expected value-key set;
3. **Compare** — for each section, diff each language's values against the
   Python reference within declared tolerances;
4. **Report** — a per-section, per-language OK/FAIL matrix; non-zero exit
   on any disagreement;
5. **CI wiring** — the cross-language workflow runs it on push/PR; its
   green is the framework's core invariant.

## 🚦 What "passing" means, formally

The framework's green state is a conjunction of five independent
conditions: (1) every computational port exits 0; (2) every JSON verdict
has `all_passed: true` — machine-parsed, not assumed; (3) the validator
finds zero cross-language disagreement; (4) every formal file compiles
without new `sorry`s — the gap ledger never grows silently; (5) the
contract itself is unchanged. A push that breaks any of the five cannot
reach `main` green — that is the whole design.

## 🧯 Maintenance map

| Failure mode | Surfaced by | First response |
|---|---|---|
| a port's JSON verdict disagrees across languages | validator → CI | diff the offending section's ports; check library-version drift first |
| a formal lemma breaks on a toolchain upgrade | extended-languages CI (or local build) | pin the toolchain per the Dockerfiles; fix forward |
| a Python port grows a dependency | code review + `pyproject.toml` diff | reject — the six sections stay std-only by contract |
| Docker image rot | scheduled rebuilds | bump the base image, re-run the section inside |
| JSON contract drift (missing verdict line) | validator parse errors | restore the exact one-line `JSON: {...}` verdict |

## 📂 Full directory layout

```
verification/
├── lean4/                  # Lean 4 (Mathlib4) — ResearchPapersVerification library
│   ├── ResearchPapersVerification/{Common,Section1..6}/
│   ├── Main.lean · Test.lean · lakefile.lean · TODO_sorry.md
├── coq/                    # Coq 8.18 — one .v file per section + _CoqProject
├── isabelle/               # Isabelle 2024 — one .thy per section + ROOT
├── agda/                   # Agda 2.6 — one .agda module per section + agda-lib
├── python_levels/          # L1–L5 chain (Python, mpmath) + results/
├── julia_levels/           # L1–L5 chain (Julia, stdlib-only, own FFT)
├── section1_correction_b/ … section6_riemann_zeros/    # Python reference ports
│   └── python/verify.py    # the runnable reference of each section
├── cpp/                    # C++17 ports (CMake) — one target per section
├── rust/                   # Rust workspace — one binary per section
├── haskell/                # Cabal project — one package per section
├── common/                 # shared utilities (verifier base, config, CLI)
├── api/                    # Flask REST wrapper over the verifiers
├── demo/                   # Gradio + Streamlit front-ends
├── docker/                 # pinned toolchain images ×7
├── tests/                  # cross-language validator + integration tests
├── scripts/                # run_cross_validation.sh · start_api.sh
├── notebooks/              # Jupyter entry point
├── docs/extended-languages/# extended-toolchain notes
├── web-dashboard/          # dashboard package manifest
├── Makefile                # this layer's build targets
├── CODEOWNERS              # review routing
└── README_VERIFICATION.md  # the original short description (kept for provenance)
```

Historical note: [`README_VERIFICATION.md`](README_VERIFICATION.md) is the
original (short) framework description kept for provenance; this README
supersedes it. Admitted gaps in the formal systems are tracked openly —
see [`lean4/TODO_sorry.md`](lean4/TODO_sorry.md).

## 🔗 See also

- [`VERIFICATION.md`](../VERIFICATION.md) — the repository-wide
  verification & provenance hub (claim inventory, dispute protocol);
- [`data/results/baseline/`](../data/results/baseline/README.md) — the
  pinned L1–L5 verdicts this framework must reproduce;
- [`CONTRIBUTING.md`](../CONTRIBUTING.md) — how to add a port or close a
  `sorry`.

---

Navigation: [repository root](../README.md) · [data](../data/README.md) · [papers](../papers/README.md) · [IPL-RP-1.0](../LICENSE.md)

*Part of [wild8highlander/navier-stokes-b](https://github.com/wild8highlander/navier-stokes-b) — © 2026 Isaev Iskhak Khamzatovich, all rights reserved.*
