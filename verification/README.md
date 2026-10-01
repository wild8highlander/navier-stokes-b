# 🔬 `verification/` — the Eleven-Language Verification Framework

> **Navigation:** [repository root](../README.md) › **`verification`**

![Languages](https://img.shields.io/badge/Languages-11-9558B2?style=flat-square)
![Sections](https://img.shields.io/badge/Sections-7-2B579A?style=flat-square)
![Tier1](https://img.shields.io/badge/Tier_1-Formal_proofs-1284BA?style=flat-square)
![Tier2](https://img.shields.io/badge/Tier_2-Computational-2EA043?style=flat-square)
![Contract](https://img.shields.io/badge/Contract-PASS_%2B_JSON-FF8C00?style=flat-square)
![License](https://img.shields.io/badge/License-IPL--RP--1.0-red?style=flat-square)

---

This directory is the **independent verification framework** of the
repository: every headline claim of the research programs is re-derived
here, in **eleven programming languages across seven research sections**,
from a single shared contract — run a verifier, it prints per-assertion
`[PASS]`/`[FAIL]` lines plus a final `JSON: {...}` verdict, and exits
non-zero on any failure. Four proof assistants machine-check the
structural facts; seven computational languages re-derive the numbers
from first principles with no hidden dependencies; the
**repository-integrity auditor** walks the whole tree and confirms every
section and folder in one deterministic run. When four kernels with
different foundations and seven arithmetics with different rounding all
agree, the residual risk is concentrated where it belongs — in the
modelling, not in the mechanics.

![The verification matrix — sections 1–7 in every language](../assets/figures/fig_verification_matrix.png)

## The two tiers, precisely

**Tier 1 — proof assistants (formal verification):**

- [`lean4/`](lean4/README.md) — Lean 4 (v4.14, Mathlib4): machine-checked
  proofs of the correction-b bounds, the rotation algebra, NSE stability
  scaffolding, the AB-Cloud structural theorems and the Section-7
  master-relation algebra; the largest formal artifact, with an honest,
  itemised gap ledger ([`lean4/TODO_sorry.md`](lean4/TODO_sorry.md));
- [`coq/`](coq/README.md) — Coq/Rocq (8.18): classical `Reals`-based
  proofs with `lra`/`nia` automation; the files `Compute` the constants
  as they compile, so the reviewer sees the numbers during the build;
  the Section-7 port fully proves the Cassini identity by induction;
- [`isabelle/`](isabelle/README.md) — Isabelle-HOL (2024): an independent
  restatement in Isar over `Complex_Main`, written to be *read*; the
  Section-7 port proves the same Cassini induction in Isar;
- [`agda/`](agda/README.md) — Agda (2.6): a dependently-typed constructive
  development with the minimal trust base made literal — π and √3 are
  explicit `postulate`s, everything else is constructed.

**Tier 2 — computational languages (numerical verification):**

- [`python_levels/`](python_levels/README.md) — the L1–L5 chain: exact
  constants (mpmath, 50 digits), rotation algebra, Kirchhoff vortices,
  2D NSE identities, and the 3D Taylor–Green BKM protocol;
- [`section1_correction_b/`](section1_correction_b/README.md) …
  [`section6_riemann_zeros/`](section6_riemann_zeros/README.md),
  [`section7_smagorinsky_kolmogorov/`](section7_smagorinsky_kolmogorov/README.md)
  — pure-Python reference implementations of the seven research sections
  (stdlib-only, the executable definitions of the claims);
- [`cpp/`](cpp/README.md) — C++17 ports with a uniform `check()` harness
  (CMake, BLAS/LAPACK, the pseudospectral KdV workhorse);
- [`rust/`](rust/README.md) — memory-safe Rust ports (std-only Cargo
  workspace, one binary per section, `i128` exact integer algebra);
- [`haskell/`](haskell/README.md) — GHC 9.4 ports (Cabal project, pure
  functional idioms, `Integer` where exactness matters);
- [`julia_levels/`](julia_levels/README.md) — a fully independent Julia
  implementation of the L1–L5 chain plus L7 (stdlib-only, own radix-2
  FFT, BigFloat/BigInt exactness).

**Integrity (the whole tree):**

- [`repo_integrity/`](repo_integrity/README.md) — the repository-wide
  auditor: nine evidence groups (docs hygiene, core constants, the
  physics chain P1–P6, the baseline chain, the NSB-96 labs, the
  monographs, sections 1–7 end-to-end, the figure/animation sets, the
  services) in one command — `make verify-repo`.

**Infrastructure:**

- [`common/`](common/README.md) — shared Python utilities (verifier base
  class, config, the aggregate CLI over sections 1–7);
- [`api/`](api/README.md) — REST API exposing the verifiers over HTTP;
- [`demo/`](demo/README.md) — interactive Gradio and Streamlit front-ends;
- [`docker/`](docker/README.md) — one pinned container per toolchain
  (lean4, coq, isabelle, agda, cpp, rust, haskell);
- [`tests/`](tests/README.md) — the cross-language validator and the
  extended-language integration tests;
- [`scripts/`](scripts/README.md) — cross-validation and API bootstrap
  shell scripts;
- [`notebooks/`](notebooks/README.md) — the Jupyter entry point;
- [`docs/`](docs/README.md) — notes on the extended toolchains.

## The seven sections

The seven research sections map 1-to-1 onto the research program of the
root README:

| # | Section | Directory | What it verifies |
|---|---|---|---|
| 1 | Correction b — the universal polarization constant | [`section1_correction_b/`](section1_correction_b/README.md) | closed-form value, 0 < b < 1, sin θ_b = b, rotation sanity |
| 2 | Preprint NSE — the regularity chain | [`section2_preprint/`](section2_preprint/README.md) | twist unitarity, BKM bound under the twist, the Leray premise |
| 3 | AB-Cloud — the Hofstadter Hamiltonian | [`section3_ab_cloud/`](section3_ab_cloud/README.md) | flux quantisation, Hermiticity, butterfly slice identities |
| 4 | KdV — soliton interactions | [`section4_kdv/`](section4_kdv/README.md) | conserved quantities across the interaction, the speed–amplitude law |
| 5 | Klein attractor | [`section5_klein_attractor/`](section5_klein_attractor/README.md) | orbit density, isometry at every iterate, the NSE bridge |
| 6 | Riemann zeros — the Hilbert–Pólya programme | [`section6_riemann_zeros/`](section6_riemann_zeros/README.md) | frozen-data embedding, ξ identities, the annihilation contrast |
| 7 | Smagorinsky–Kolmogorov — the master relation *(new)* | [`section7_smagorinsky_kolmogorov/`](section7_smagorinsky_kolmogorov/README.md) | `C_s = 1/(π(3C_K/2)^{3/4})` at 50 digits, the −3/4 exponent law, Cassini, the (5′) coefficient algebra of the φ-audit |

Each section exists as a Python reference port (the directory above), a
formal port in each of the four proof assistants
([`lean4/ResearchPapersVerification/Section1_CorrectionB/`](lean4/README.md)
and its siblings) and an extended computational port in C++, Rust and
Haskell — the full matrix is tabulated in each section's README, and the
figure above is its picture.

## 📜 The verification contract

Every computational port in this framework follows one output contract,
which is what makes cross-language comparison mechanical:

1. print a banner line identifying section and language;
2. compute the section's quantities from closed-form inputs (no data
   files needed at this tier);
3. print one `[PASS]`/`[FAIL]` line per assertion with the measured
   residual;
4. print exactly one machine-readable verdict line
   `JSON: {"section": N, "language": "...", "values": {…}, "all_passed": true}`;
5. exit `0` only if everything passed.

The cross-language validator ([`tests/`](tests/README.md)) parses every
port's verdict and fails CI on any disagreement; the formal tier mirrors
the contract with lemma names, and its admitted gaps are public:
[`lean4/TODO_sorry.md`](lean4/TODO_sorry.md) itemises every `sorry`,
every mechanical `axiom : True` stub and every genuine open-problem
axiom, each with a difficulty estimate and a closing plan — including the
Section-7 ledger entries (`S7-CASSINI`, `S7-EXPLAW`, `S7-ANTI`). Nothing
is hidden behind unconditional assumptions — the trust base is
enumerable, and in Agda it is literally two postulates (π and √3) plus
the Section-7 sign induction.

## How to run everything

```bash
# 1) the seven Python reference sections (< 1 min total)
make verify-all
#    … which is exactly:
python3 verification/common/python/main.py --section 1 --preset default
#    … through section 7

# 2) the repository-wide integrity audit (9 evidence groups, ~1 min)
make verify-repo

# 3) the verification chain L1–L5 + L7 (~20 min; L5 skippable)
python3 verification/python_levels/verify_all.py
NSE3D_SKIP=1 python3 verification/python_levels/verify_all.py

# 4) the extended computational ring (needs the toolchains)
make verify-extended        # C++17, Rust, Haskell + Lean/Coq builds

# 5) the formal tier, one kernel at a time
cd verification/lean4     && lake build && lake exe check
cd ../coq                 && coq_makefile -f _CoqProject -o Makefile && make
cd ../isabelle            && isabelle build -D .
cd ../agda                && agda --safe Section1_CorrectionB/CorrectionB.agda

# 6) over HTTP, without installing anything
uvicorn api.server:app --port 8000        # then GET /api/verify/7
```

Typical wall-clock on two cores: the section ports, seconds; L1–L4 about
two minutes combined; L5 ten to twenty minutes; the repository audit
about one minute. Everything is deterministic (fixed seeds) and
idempotent.

## The framework's layout

```text
verification/
├── lean4/ coq/ isabelle/ agda/     # Tier 1 — four proof kernels
├── section1_correction_b/ …        # Python reference ports, sections 1–7
├── cpp/ rust/ haskell/             # Tier 2 — extended computational ports
├── python_levels/                  # the L1–L5 reference chain
├── julia_levels/                   # the independent Julia chain (L1–L5 + L7)
├── repo_integrity/                 # the whole-tree auditor (9 groups)
├── common/ api/ demo/              # the runner, the REST API, the demos
├── docker/                         # 7 pinned toolchain images
├── tests/ scripts/                 # the validator, the shell entry points
├── notebooks/ docs/                # Jupyter, the porting notes
└── README.md                       # this hub
```

## License

Part of **navier-stokes-b**, license IPL-RP-1.0 ([LICENSE.md](../LICENSE.md)).
