# 🔬 Verification — the 11-Language Verification Framework

> **Navigation:** **`verification`**

![Languages](https://img.shields.io/badge/Languages-11-blue?style=flat-square) ![License](https://img.shields.io/badge/License-IPL--RP--1.0-red?style=flat-square) ![CI](https://img.shields.io/badge/CI-ci--cross--language-2088FF?style=flat-square&logo=githubactions&logoColor=white)

This directory is the **independent verification framework** of the repository: every headline claim of the research programs is re-derived here, in **eleven programming languages**, from a single shared contract — run a verifier, it prints per-assertion `[PASS]`/`[FAIL]` lines plus a final `JSON: {...}` verdict, and exits non-zero on any failure. Four proof assistants machine-check the structural facts; seven computational languages re-derive the numbers from first principles with no hidden dependencies.

**Tier 1 — proof assistants (formal verification):**
- [`lean4/`](lean4/README.md) — Lean 4 (v4.14, Mathlib4): machine-checked proofs of the correction-b bounds, NSE stability scaffolding and AB-Cloud structural theorems;
- [`coq/`](coq/README.md) — Coq/Rocq (8.18): classical `Reals`-based proofs with `lra` automation;
- [`isabelle/`](isabelle/README.md) — Isabelle-HOL (2024): independent statement over `Complex_Main`;
- [`agda/`](agda/README.md) — Agda (2.6): dependently-typed constructive development with an explicit, minimal trust base.

**Tier 2 — computational languages (numerical verification):**
- [`section1_correction_b/` … `section6_riemann_zeros/`](section1_correction_b/README.md) — pure-Python reference implementations of the six research sections;
- [`cpp/`](cpp/README.md) — C++17 ports with a uniform `check()` harness (CMake build);
- [`rust/`](rust/README.md) — memory-safe Rust ports (std-only, Cargo);
- [`haskell/`](haskell/README.md) — GHC 9.4 ports (Cabal).

**Infrastructure:**
- [`common/`](common/README.md) — shared Python utilities (verifier base class, config);
- [`api/`](api/README.md) — REST API exposing the verifiers over HTTP;
- [`demo/`](demo/README.md) — interactive Gradio and Streamlit front-ends;
- [`docker/`](docker/README.md) — one pinned container per formal/extended toolchain;
- [`tests/`](tests/README.md) — cross-language validator and extended-language integration tests;
- [`scripts/`](scripts/README.md) — cross-validation and API bootstrap shell scripts;
- [`notebooks/`](notebooks/README.md) — Jupyter entry point;
- [`docs/extended-languages/`](docs/README.md) — notes on the extended toolchains;
- [`web-dashboard/`](web-dashboard/README.md) — dashboard package manifest.

The six research sections map 1-to-1 onto the research programs described in the root README: **1** — the polarization correction *b*; **2** — the NSE regularity chain of the preprint; **3** — the AB-Cloud Hamiltonian; **4** — the KdV soliton interactions; **5** — the Klein attractor; **6** — the Riemann-zeros correspondence. The root README carries the full [Section × Language matrix](../README.md#-верификация-на-11-языках) with direct links into every port.

Historical note: [`README_VERIFICATION.md`](README_VERIFICATION.md) is the original (short) framework description kept for provenance; this README supersedes it. Admitted gaps in the formal systems are tracked openly — see [`lean4/TODO_sorry.md`](lean4/TODO_sorry.md).

## 📜 The Verification Contract

Every computational port in this framework follows one output contract, which is what makes cross-language comparison mechanical:

1. print a banner line identifying section and language;
2. compute the section's quantities from closed-form inputs (no data files needed at this tier);
3. assert each expected property, printing `[PASS] name: expected=…, actual=…` or `[FAIL] …`;
4. print a final line `JSON: {"section": N, "language": "<lang>", "values": {…}, "all_passed": true|false}`;
5. exit with status 0 only if every assertion passed.

The formal tier mirrors the same assertions as lemmas (`b_pos`, `b_lt_one`, `sin_θ_b_eq_b`, …) so that a reviewer can diff the *mathematical content* across systems rather than the code style.

## 🚀 Running the Framework

```bash
# From the repository root:
make install          # Python environment
make verify-all       # Python reference implementations (sections 1–6)
make verify-extended  # extended toolchains (requires those installed)

# Or directly, per language:
python3  verification/section1_correction_b/python/verify.py
cargo run --release --manifest-path verification/rust/Cargo.toml
cmake -S verification/cpp -B /tmp/cppbuild && cmake --build /tmp/cppbuild

# Formal tier:
cd verification/lean4 && lake build && lake exe check
cd verification/isabelle && isabelle build -D .
```

Docker images pin every formal toolchain — see [`docker/`](docker/README.md). The REST API (`api/server.py`) runs the same verifiers over HTTP for scripted audits.

## 📂 Contents — What Lives Here

| File | Size | Description |
|---|---|---|
| [`CODEOWNERS`](CODEOWNERS) | 278 B | review routing — code owners per path |
| [`Makefile`](Makefile) | 1.1 KB | build automation — the verification targets of this layer |
| [`agda/`](agda/) | — | subdirectory with 14 files (see its own README) |
| [`api/`](api/) | — | subdirectory with 3 files (see its own README) |
| [`common/`](common/) | — | subdirectory with 6 files (see its own README) |
| [`coq/`](coq/) | — | subdirectory with 14 files (see its own README) |
| [`cpp/`](cpp/) | — | subdirectory with 14 files (see its own README) |
| [`demo/`](demo/) | — | subdirectory with 4 files (see its own README) |
| [`docker/`](docker/) | — | subdirectory with 15 files (see its own README) |
| [`docs/`](docs/) | — | subdirectory with 2 files (see its own README) |
| [`haskell/`](haskell/) | — | subdirectory with 26 files (see its own README) |
| [`isabelle/`](isabelle/) | — | subdirectory with 14 files (see its own README) |
| [`lean4/`](lean4/) | — | subdirectory with 22 files (see its own README) |
| [`notebooks/`](notebooks/) | — | subdirectory with 2 files (see its own README) |
| [`rust/`](rust/) | — | subdirectory with 26 files (see its own README) |
| [`scripts/`](scripts/) | — | subdirectory with 3 files (see its own README) |
| [`section1_correction_b/`](section1_correction_b/) | — | subdirectory with 3 files (see its own README) |
| [`section2_preprint/`](section2_preprint/) | — | subdirectory with 3 files (see its own README) |
| [`section3_ab_cloud/`](section3_ab_cloud/) | — | subdirectory with 3 files (see its own README) |
| [`section4_kdv/`](section4_kdv/) | — | subdirectory with 3 files (see its own README) |
| [`section5_klein_attractor/`](section5_klein_attractor/) | — | subdirectory with 3 files (see its own README) |
| [`section6_riemann_zeros/`](section6_riemann_zeros/) | — | subdirectory with 3 files (see its own README) |
| [`tests/`](tests/) | — | subdirectory with 3 files (see its own README) |
| [`web-dashboard/`](web-dashboard/) | — | subdirectory with 2 files (see its own README) |

## 🗂 Directory Layout

```
verification/
├── agda/   # 14 files
│   ├── Section1_CorrectionB/   # 2 files
│   │   ├── CorrectionB.agda
│   │   └── README.md  (this file)
│   ├── Section2_PreprintNSE/   # 2 files
│   │   ├── ProofChain.agda
│   │   └── README.md  (this file)
│   ├── Section3_ABCloud/   # 2 files
│   │   ├── Hofstadter.agda
│   │   └── README.md  (this file)
│   ├── Section4_KdV/   # 2 files
│   │   ├── KdV.agda
│   │   └── README.md  (this file)
│   ├── Section5_KleinAttractor/   # 2 files
│   │   ├── Klein.agda
│   │   └── README.md  (this file)
│   ├── Section6_RiemannZeros/   # 2 files
│   │   ├── README.md  (this file)
│   │   └── RiemannZeros.agda
│   ├── agda.agda-lib
│   └── README.md  (this file)
├── api/   # 3 files
│   ├── README.md  (this file)
│   ├── requirements.txt
│   └── server.py
├── common/   # 6 files
│   ├── python/   # 5 files
│   │   ├── __init__.py
│   │   ├── config.py
│   │   ├── main.py
│   │   ├── README.md  (this file)
│   │   └── verifier_base.py
│   └── README.md  (this file)
├── coq/   # 14 files
│   ├── section1_correction_b/   # 2 files
│   │   ├── CorrectionB.v
│   │   └── README.md  (this file)
│   ├── section2_preprint/   # 2 files
│   │   ├── ProofChain.v
│   │   └── README.md  (this file)
│   ├── section3_ab_cloud/   # 2 files
│   │   ├── Hofstadter.v
│   │   └── README.md  (this file)
│   ├── section4_kdv/   # 2 files
│   │   ├── KdV.v
│   │   └── README.md  (this file)
│   ├── section5_klein_attractor/   # 2 files
│   │   ├── Klein.v
│   │   └── README.md  (this file)
│   ├── section6_riemann_zeros/   # 2 files
│   │   ├── README.md  (this file)
│   │   └── RiemannZeros.v
│   ├── _CoqProject
│   └── README.md  (this file)
├── cpp/   # 14 files
│   ├── section1_correction_b/   # 2 files
│   │   ├── main.cpp
│   │   └── README.md  (this file)
│   ├── section2_preprint/   # 2 files
│   │   ├── main.cpp
│   │   └── README.md  (this file)
│   ├── section3_ab_cloud/   # 2 files
│   │   ├── main.cpp
│   │   └── README.md  (this file)
│   ├── section4_kdv/   # 2 files
│   │   ├── main.cpp
│   │   └── README.md  (this file)
│   ├── section5_klein_attractor/   # 2 files
│   │   ├── main.cpp
│   │   └── README.md  (this file)
│   ├── section6_riemann_zeros/   # 2 files
│   │   ├── main.cpp
│   │   └── README.md  (this file)
│   ├── CMakeLists.txt
│   └── README.md  (this file)
├── demo/   # 4 files
│   ├── gradio_app.py
│   ├── README.md  (this file)
│   ├── requirements.txt
│   └── streamlit_app.py
├── docker/   # 15 files
│   ├── agda/   # 2 files
│   │   ├── Dockerfile
│   │   └── README.md  (this file)
│   ├── coq/   # 2 files
│   │   ├── Dockerfile
│   │   └── README.md  (this file)
│   ├── cpp/   # 2 files
│   │   ├── Dockerfile
│   │   └── README.md  (this file)
│   ├── haskell/   # 2 files
│   │   ├── Dockerfile
│   │   └── README.md  (this file)
│   ├── isabelle/   # 2 files
│   │   ├── Dockerfile
│   │   └── README.md  (this file)
│   ├── lean4/   # 2 files
│   │   ├── Dockerfile
│   │   └── README.md  (this file)
│   ├── rust/   # 2 files
│   │   ├── Dockerfile
│   │   └── README.md  (this file)
│   └── README.md  (this file)
├── docs/   # 2 files
│   ├── extended-languages/   # 1 files
│   │   └── README.md  (this file)
│   └── README.md  (this file)
├── haskell/   # 26 files
│   ├── Section1_CorrectionB/   # 4 files
│   │   ├── src/   # 2 files
│   │   ├── README.md  (this file)
│   │   └── Section1_CorrectionB.cabal
│   ├── Section2_PreprintNSE/   # 4 files
│   │   ├── src/   # 2 files
│   │   ├── README.md  (this file)
│   │   └── Section2_PreprintNSE.cabal
│   ├── Section3_ABCloud/   # 4 files
│   │   ├── src/   # 2 files
│   │   ├── README.md  (this file)
│   │   └── Section3_ABCloud.cabal
│   ├── Section4_KdV/   # 4 files
│   │   ├── src/   # 2 files
│   │   ├── README.md  (this file)
│   │   └── Section4_KdV.cabal
│   ├── Section5_KleinAttractor/   # 4 files
│   │   ├── src/   # 2 files
│   │   ├── README.md  (this file)
│   │   └── Section5_KleinAttractor.cabal
│   ├── Section6_RiemannZeros/   # 4 files
│   │   ├── src/   # 2 files
│   │   ├── README.md  (this file)
│   │   └── Section6_RiemannZeros.cabal
│   ├── cabal.project
│   └── README.md  (this file)
├── isabelle/   # 14 files
│   ├── Section1_CorrectionB/   # 2 files
│   │   ├── CorrectionB.thy
│   │   └── README.md  (this file)
│   ├── Section2_PreprintNSE/   # 2 files
│   │   ├── ProofChain.thy
│   │   └── README.md  (this file)
│   ├── Section3_ABCloud/   # 2 files
│   │   ├── Hofstadter.thy
│   │   └── README.md  (this file)
│   ├── Section4_KdV/   # 2 files
│   │   ├── KdV.thy
│   │   └── README.md  (this file)
│   ├── Section5_KleinAttractor/   # 2 files
│   │   ├── Klein.thy
│   │   └── README.md  (this file)
│   ├── Section6_RiemannZeros/   # 2 files
│   │   ├── README.md  (this file)
│   │   └── RiemannZeros.thy
│   ├── README.md  (this file)
│   └── ROOT
├── lean4/   # 22 files
│   ├── ResearchPapersVerification/   # 16 files
│   │   ├── Common/   # 2 files
│   │   ├── Section1_CorrectionB/   # 2 files
│   │   ├── Section2_PreprintNSE/   # 2 files
│   │   ├── Section3_ABCloud/   # 2 files
│   │   ├── Section4_KdV/   # 2 files
│   │   ├── Section5_KleinAttractor/   # 2 files
│   │   ├── Section6_RiemannZeros/   # 2 files
│   │   ├── Basic.lean
│   │   └── README.md  (this file)
│   ├── lakefile.lean
│   ├── lean-toolchain
│   ├── Main.lean
│   ├── README.md  (this file)
│   ├── Test.lean
│   └── TODO_sorry.md
├── notebooks/   # 2 files
│   ├── README.md  (this file)
│   └── requirements.txt
├── rust/   # 26 files
│   ├── section1_correction_b/   # 4 files
│   │   ├── src/   # 2 files
│   │   ├── Cargo.toml
│   │   └── README.md  (this file)
│   ├── section2_preprint/   # 4 files
│   │   ├── src/   # 2 files
│   │   ├── Cargo.toml
│   │   └── README.md  (this file)
│   ├── section3_ab_cloud/   # 4 files
│   │   ├── src/   # 2 files
│   │   ├── Cargo.toml
│   │   └── README.md  (this file)
│   ├── section4_kdv/   # 4 files
│   │   ├── src/   # 2 files
│   │   ├── Cargo.toml
│   │   └── README.md  (this file)
│   ├── section5_klein_attractor/   # 4 files
│   │   ├── src/   # 2 files
│   │   ├── Cargo.toml
│   │   └── README.md  (this file)
│   ├── section6_riemann_zeros/   # 4 files
│   │   ├── src/   # 2 files
│   │   ├── Cargo.toml
│   │   └── README.md  (this file)
│   ├── Cargo.toml
│   └── README.md  (this file)
├── scripts/   # 3 files
│   ├── README.md  (this file)
│   ├── run_cross_validation.sh
│   └── start_api.sh
├── section1_correction_b/   # 3 files
│   ├── python/   # 2 files
│   │   ├── README.md  (this file)
│   │   └── verify.py
│   └── README.md  (this file)
├── section2_preprint/   # 3 files
│   ├── python/   # 2 files
│   │   ├── README.md  (this file)
│   │   └── verify.py
│   └── README.md  (this file)
├── section3_ab_cloud/   # 3 files
│   ├── python/   # 2 files
│   │   ├── README.md  (this file)
│   │   └── verify.py
│   └── README.md  (this file)
├── section4_kdv/   # 3 files
│   ├── python/   # 2 files
│   │   ├── README.md  (this file)
│   │   └── verify.py
│   └── README.md  (this file)
├── section5_klein_attractor/   # 3 files
│   ├── python/   # 2 files
│   │   ├── README.md  (this file)
│   │   └── verify.py
│   └── README.md  (this file)
├── section6_riemann_zeros/   # 3 files
│   ├── python/   # 2 files
│   │   ├── README.md  (this file)
│   │   └── verify.py
│   └── README.md  (this file)
├── tests/   # 3 files
│   ├── extended_cross_language_validator.py
│   ├── README.md  (this file)
│   └── test_extended_languages.py
├── web-dashboard/   # 2 files
│   ├── package.json
│   └── README.md  (this file)
├── CODEOWNERS
├── Makefile
├── README.md  (this file)
└── README_VERIFICATION.md  (this file)
```

## 🇷🇺 Краткое резюме (Russian Summary)

**verification/** — независимый фреймворк верификации на 11 языках: 4 пруф-ассистента (Lean 4, Coq, Isabelle, Agda) машинно проверяют структурные факты, 7 вычислительных языков пересчитывают числа по единому контракту (строки PASS + JSON-вердикт). Шесть разделов соответствуют программам исследований; инфраструктура — common/, api/, demo/, docker/, tests/, scripts/, notebooks/. Исторический короткий README сохранён рядом.

---

<div align="center">

**[⬆ Back to top](#-verification--the-11-language-verification-framework)** · 
**[Repository root](README.md)**

*Part of [wild8highlander/navier-stokes-b](https://github.com/wild8highlander/navier-stokes-b) · Licensed under [IPL-RP-1.0](https://github.com/wild8highlander/navier-stokes-b/blob/main/LICENSE.md) — All Rights Reserved*

</div>


---

## 🧭 How to Use This Framework

### Three Ways In, by Goal

**"I want to see it work in the next two minutes."**
Run the smoke test: `python3 verification/section1_correction_b/python/verify.py`. It prints the section banner, the computed constant, `PASS`, and exits 0 — no dependencies, no configuration. Then run `make verify-all` for all six Python sections.

**"I want to audit one claim end-to-end."**
Pick the claim in the root README's [results table](../README.md#-extended-quantitative-results), follow its "where" link to the section directory, and read this chain: section README (what is claimed) → Python port (executable definition) → formal files (structural skeleton) → cross-language validator result. The [Section-by-Section Guide](../README.md#-section-by-section-verification-guide) narrates this for all six sections.

**"I want to add a port or a section."**
Read the [Verification Contract](#-the-verification-contract) below, then follow the checklists in the root README's [Appendix D](../README.md#-appendix-d--extending-the-framework). The contract is the only invariant that matters; everything else is convention.

### The Two Tiers, Precisely

**Tier 1 (formal)** answers *what is structurally true*: positivity and bounds of the correction, the rotation algebra, matrix structures, Hofstadter identities. Four systems, four independent kernels — Lean 4 (Mathlib4), Coq/Rocq (`Reals` + `lra`), Isabelle (`Complex_Main`), Agda (minimal postulated base). A claim compiled in all four had to be written four times, in three different foundational styles (classical set-theoretic, dependent type theory, simple type theory) — agreement across those paradigms is the point.

**Tier 2 (computational)** answers *what do the numbers say*: every section's quantities re-derived in independent arithmetic (Python stdlib, Rust std, C++ with BLAS, Haskell, plus the extended ring). The ports are diffed mechanically by parsing their JSON verdicts — the validator fails CI on any disagreement, so drift is impossible to merge quietly.

### The Output Contract, Exactly

Every computational port follows the same five-step contract (banner → compute → assert → JSON verdict → exit code). The formal tier mirrors it with lemma names. The full statement, with an annotated example, is in [The Verification Contract](#-the-verification-contract) above; the per-section `values` key sets are tabulated in the root README's [Appendix K.8](../README.md#%EF%B8%8F-appendix-k--full-command-reference).

### Infrastructure Tour

| Component | Directory | What it gives you |
|---|---|---|
| Shared utilities | [`common/`](common/README.md) | verifier base class, config — the Python tier's plumbing |
| REST API | [`api/`](api/README.md) | trigger verifiers over HTTP; JSON verdict passthrough |
| Gradio/Streamlit demos | [`demo/`](demo/README.md) | click-through UI over the same verifiers |
| Docker images | [`docker/`](docker/README.md) | one pinned environment per toolchain (7 images) |
| Integration tests | [`tests/`](tests/README.md) | the cross-language validator + extended-language tests |
| Shell scripts | [`scripts/`](scripts/README.md) | cross-validation and API bootstrap one-liners |
| Jupyter entry | [`notebooks/`](notebooks/README.md) | notebook-based access to the ports |
| Extended-language notes | [`docs/extended-languages/`](docs/README.md) | how the extended ring is organised |
| Dashboard manifest | [`web-dashboard/`](web-dashboard/README.md) | package manifest of the JS dashboard |

### CI Integration

The workflows that exercise this layer (see the root README's [CI/CD reference](../README.md#%EF%B8%8F-cicd-reference)):

- `ci.yml` — the main gate: sections 1–6 + contract checks on every push/PR;
- `ci-python.yml` — the Python 3.10–3.12 matrix;
- `ci-cross-language.yml` — runs [`tests/extended_cross_language_validator.py`](tests/README.md) and fails on any cross-language disagreement;
- `ci-extended-languages.yml` — the extended ring where toolchains are available;
- `coverage.yml` — pytest-cov over the shared utilities.

### Historical Note and Provenance

[`README_VERIFICATION.md`](README_VERIFICATION.md) is the original (short) framework description kept for provenance; this README supersedes it. The framework grew from the six Python sections to the eleven-language matrix across releases v1.1.0 → v1.3.0 (see the [timeline](../README.md#-appendix-i--historical-timeline)); the six-section shape has been stable since v1.2.0, which is why the matrix is the framework's stable identifier.

### Honesty Surface

Admitted gaps are public by policy: [`lean4/TODO_sorry.md`](lean4/TODO_sorry.md) itemises the Lean ledger (13 `sorry`s, 12 axiom stubs, 4 open-problem axioms at last count), and the per-language READMEs state exactly what each system closes. If a gap matters for a claim you care about, the ledger tells you where it stands — that is the framework's contract with its reader.

---
## 📋 Per-Section Content Summary

What each of the six sections verifies, in one paragraph each — the section directories' own READMEs carry the full command tables.

- **Section 1** ([`section1_correction_b/`](section1_correction_b/README.md)) — the polarization correction *b*: closed-form evaluation, positivity, b < 1, the sine identity, and the numeric echo of the rotation algebra. The framework's smoke test and the constant behind Program 1.
- **Section 2** ([`section2_preprint/`](section2_preprint/README.md)) — the NSE regularity chain: twist unitarity, the BKM bound under the twist, estimate ordering. The structural mirror of the preprint's argument.
- **Section 3** ([`section3_ab_cloud/`](section3_ab_cloud/README.md)) — the AB-Cloud Hamiltonian's structural core at reduced scale: flux quantisation, Hermiticity, symmetry classes — the presuppositions of the heavy statistics in `ab-cloud/verification/`.
- **Section 4** ([`section4_kdv/`](section4_kdv/README.md)) — KdV soliton interactions: conserved quantities across the interaction, closed-form two-soliton agreement, the C++ pseudospectral workhorse.
- **Section 5** ([`section5_klein_attractor/`](section5_klein_attractor/README.md)) — the Klein attractor: invariant statistics over the reference ensemble, contraction statements, the bridge back to NSE.
- **Section 6** ([`section6_riemann_zeros/`](section6_riemann_zeros/README.md)) — the ζ-correspondence skeleton: frozen-data embedding, GUE-class gap statistics, Σ²(L) diagnostics.

## 🧯 What Fails How — a Maintenance Map

For maintainers: the failure modes this layer can exhibit, and where each surfaces.

| Failure mode | Surfaced by | First response |
|---|---|---|
| a port's JSON verdict disagrees across languages | `ci-cross-language.yml` → validator | diff the offending section's ports; check for library-version drift first |
| a formal lemma breaks on a toolchain upgrade | `ci-extended-languages.yml` (or local build) | pin the toolchain version per the Dockerfiles; then fix forward |
| a Python port grows a dependency | code review + `pyproject.toml` diff | reject — the six sections stay std-only by contract |
| Docker image rot | scheduled builds in `docker.yml` | bump the base image, re-run the section inside |
| JSON contract drift (missing verdict line) | validator's parse errors | the port must print exactly one `JSON: {...}` line — restore it |

## 🔄 Framework Versioning

The framework's shape is versioned with the repository: sections are stable identifiers (1–6), the language matrix grows additively, and the validator's expectations update in the same commit that adds a port. Documentation of the framework follows the `docs:` track and never silently changes a contract — contract changes are `feat:` and must update the validator, the matrix and every affected port in one atomic change.

---
## 🧪 The Framework's Design Rationale

Four decisions define this framework; each is a deliberate trade-off worth understanding before extending it.

**1. Why a shared output contract instead of per-language APIs?**
Because the evidence must be *mechanically comparable*. A uniform banner/assert/JSON/exit-code interface makes the cross-language validator a 200-line parser instead of an integration project, and makes CI disagreement failures loud and cheap. Portability of the *contract* is what turns eleven languages into one argument.

**2. Why std-only for the reference tier?**
Because the reference implementation is the executable definition of each section. A dependency is a versioned assumption; at definition level, assumptions are liabilities. NumPy enters where performance matters (the AB-Cloud suites), never where definition purity matters (the six sections).

**3. Why four proof assistants instead of one?**
Because kernels have bugs and paradigms have blind spots. Four independent kernels — two classical, one simple-type-theoretic, one dependent — checking the same statements is the formal analogue of the computational tier's cross-language matrix. The redundancy is the result.

**4. Why are the heavy statistics NOT in this directory?**
 A reader can audit the skeleton without downloading anything and the statistics without wading through formalism — and CI can price each tier appropriately.

## 🚦 The Framework's Own Health Model

How this layer self-monitors — useful for maintainers and for anyone trusting the green badges:

| Signal | Source | Meaning |
|---|---|---|
| Section ports green | `ci.yml` | the six sections assert as expected on the current tree |
| Python matrix green | `ci-python.yml` | 3.10–3.12 compatibility holds |
| Validator green | `ci-cross-language.yml` | the JSON verdicts agree across languages — the framework's core invariant |
| Extended ring green | `ci-extended-languages.yml` | the extended toolchains still build and pass |
| Coverage report | `coverage.yml` | the shared utilities' test coverage (uploaded to Codecov) |
| Benchmarks | `benchmark.yml` | the ports' performance has not regressed |

The badges on the root README encode exactly these signals under the hybrid policy — dynamic where green, static where the underlying integration is not yet wired.

## 🧰 Extending the Infrastructure (not the mathematics)

Beyond adding ports and sections ([Appendix D](../README.md#-appendix-d--extending-the-framework)), the infrastructure itself accepts contributions:

- **a new demo surface** (e.g. a JupyterLab widget) over [`api/`](api/README.md);
- **new pinned Docker images** for toolchains the extended ring gains;
- **validator improvements** — richer diff reports, machine-readable summaries of disagreements;
- **script hardening** in [`scripts/`](scripts/README.md) — the cross-validation and API bootstrap one-liners.

The rule is unchanged: infrastructure may change freely as long as the contract, the matrix and the validator move together in one atomic change.

---
## 🗣 Per-Language Quick Reference (compact table)

The whole matrix as a command card — the deep dives live in each language's README:

| Language | Where | Run everything | Run one section |
|---|---|---|---|
| Python | `section1…6/*/python/` | `make verify-all` | `python3 verification/section1_correction_b/python/verify.py` |
| Lean 4 | `lean4/` | `lake build && lake exe check` | `lake exe check` (chain) |
| Coq | `coq/` | `coqc` per `_CoqProject` | `coqc coq/section1_correction_b/CorrectionB.v` |
| Isabelle | `isabelle/` | `isabelle build -D .` | session build |
| Agda | `agda/` | `agda` per module | `agda Section1_CorrectionB/CorrectionB.agda` |
| Rust | `rust/` | `cargo run --release` | `cargo run --release -p section1_correction_b` |
| C++ | `cpp/` | build + run all targets | `./build/section1_correction_b` |
| Haskell | `haskell/` | `cabal build` + run | `cabal run section1-correction-b` |

## 📈 What "Passing" Means, Formally

The framework's green state is a conjunction of five independent conditions — and it is worth being precise about what each covers:

1. **every computational port exits 0** — each section's assertions hold in that language;
2. **every JSON verdict has `all_passed: true`** — machine-parsed, not assumed;
3. **the validator finds zero cross-language disagreement** — the values agree to the declared tolerances;
4. **every formal file compiles without new `sorry`s** — the admitted-gap ledger never grows silently;
5. **the contract itself is unchanged** — a diff touching the JSON schema requires an atomic validator+matrix+port update.

A push that breaks any of the five cannot reach `main` green — that is the whole design.

## 🧠 Reading the Framework as a Reviewer

A reviewer's minimum audit path, in six steps:

1. Read the contract (above) — two minutes, and everything after depends on it;
2. run the smoke test — one command;
3. pick the section your claim lives in; read its README's claim list;
4. run that section in **two** languages of your choosing;
5. open the corresponding formal file in **one** assistant and check the lemma statements against the section README;
6. check the gap ledger for admitted gaps affecting your claim.

If all six steps check out, you have audited the framework's chain for your claim end-to-end — the same path CI automates on every push.

---
## 🧪 Worked Example: Auditing Section 1 in Ten Minutes

The full audit path for one section, concretely — the template for any other:

1. **Claim list.** Open this directory's [`section1_correction_b/README.md`](section1_correction_b/README.md): four assertions (positive, < 1, sine identity, rotation sanity).
2. **Reference run.** `python3 verification/section1_correction_b/python/verify.py` → `b = 0.062381194121028`, `PASS`, exit 0.
3. **Second language.** `cargo run --release -p section1_correction_b` — same banner shape, same PASS pattern, its own JSON verdict.
4. **Validator.** `python3 verification/tests/extended_cross_language_validator.py` — confirms sections 1–6 agree across languages in one shot.
5. **Formal check.** Open [`lean4/ResearchPapersVerification/Common/Foundation.lean`](lean4/ResearchPapersVerification/Common/Foundation.lean): the closed-form definition and the closed positivity theorem; `sin_θ_b_eq_b` in Section 1's file. Compare the statement, not the syntax, with the section README's claim list.
6. **Gap check.** [`lean4/TODO_sorry.md`](lean4/TODO_sorry.md) — which numeric-bound lemmas are admitted gaps (b > 0.07, b < 0.08 among them). Your audit now knows exactly what is compiled, what is computed, and what is admitted.

Ten minutes, one section, the entire evidence chain. Multiply by five other sections at your leisure.

## 🧬 The Validator, Under the Hood

[`tests/extended_cross_language_validator.py`](tests/README.md) is the framework's referee; its logic is deliberately transparent:

1. **Collect** — run every registered port (or read archived verdicts), parse each port's single `JSON: {...}` line;
2. **Normalise** — map section number → expected value-key set (the K.8 table of the root README);
3. **Compare** — for each section, diff each language's values against the Python reference within declared tolerances;
4. **Report** — per-section, per-language OK/FAIL matrix; non-zero exit on any disagreement;
5. **CI wiring** — `ci-cross-language.yml` runs it on push/PR; its green is the framework's core invariant.

Extending the validator (new languages, new sections) is a config change *plus* the same-commit contract updates — the atomicity rule from the design rationale applies verbatim.

<!-- doc-enhancer:block v1 (автоматический блок; файлы лицензии не затрагиваются) -->

---

## 🧭 Навигация и быстрые ссылки (auto)

- 🏠 [Корень репозитория](../../README.md)
- 📖 [Как верифицируются утверждения](../../verification/README.md)
- 📄 [Статьи (PDF)](../../papers/README.md) · 📚 [Монографии](../../docs/README.md) · 🧾 [LaTeX](../../src/README.md)
- ⚖️ [Лицензия IPL-RP-1.0](../../LICENSE.md) — просмотр, одна резервная копия и цитирование с атрибуцией разрешены; остальное — только с письменного согласия автора.

*Блок добавлен автоматически (`doc-enhancer v1`); к лицензии отношения не имеет и её не изменяет. Повторный запуск скрипта блок не дублирует.*

