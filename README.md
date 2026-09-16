<p align="center">
  <img src="assets/banner.svg" alt="navier-stokes-b — the Universal b-Correction Program for the 3D Navier–Stokes Equations" width="100%">
</p>

<h1 align="center">navier-stokes-b</h1>

<p align="center">
  <b>The universal b-correction program for the 3D Navier–Stokes equations:</b><br>
  an analytic route to global regularity, an L1–L5 verification chain, an executed
  seven-open-problem program (P1–P7), a two-language monograph, ready preprints with
  LaTeX sources, a KdV continuation — and an <b>11-language verification framework</b>.
</p>

<p align="center">
  <a href="#-verification-in-11-languages"><img src="https://img.shields.io/badge/verification-11%20languages-9558B2?logo=hackthebox&logoColor=white" alt="Verification: 11 languages"></a>
  <a href="https://github.com/wild8highlander/navier-stokes-b/actions/workflows/ci.yml"><img src="https://github.com/wild8highlander/navier-stokes-b/actions/workflows/ci.yml/badge.svg" alt="CI status"></a>
  <a href="https://github.com/wild8highlander/navier-stokes-b/actions/workflows/pages.yml"><img src="https://github.com/wild8highlander/navier-stokes-b/actions/workflows/pages.yml/badge.svg" alt="Pages deploy"></a>
  <a href="https://zenodo.org/records/21825394"><img src="https://zenodo.org/badge/DOI/10.5281/zenodo.21825394.svg" alt="DOI"></a>
  <img src="https://img.shields.io/badge/license-IPL--RP--1.0-blueviolet" alt="License: IPL-RP-1.0">
</p>

<p align="center">
  <img src="https://img.shields.io/badge/python-3.10%20%7C%203.11%20%7C%203.12-3776AB?logo=python&logoColor=white" alt="Python 3.10 | 3.11 | 3.12">
  <img src="https://img.shields.io/badge/formal%20proofs-Lean%204%20%7C%20Coq%20%7C%20Isabelle%20%7C%20Agda-8CA3C7" alt="Formal proofs: Lean 4 | Coq | Isabelle | Agda">
  <img src="https://img.shields.io/badge/runtime-Linux%20%7C%20macOS%20%7C%20Windows%20%7C%20Android%20(Termux)-2EA043" alt="Runtime platforms">
  <img src="https://img.shields.io/badge/code%20style-ruff-261230?logo=ruff&logoColor=white" alt="code style: ruff">
  <img src="https://img.shields.io/badge/tests-pytest-0A9EDC?logo=pytest&logoColor=white" alt="tests: pytest">
  <img src="https://img.shields.io/badge/reproducible-sha256%20manifest-2EA043" alt="reproducible: sha256 manifest">
</p>

<p align="center">
  <a href="https://github.com/wild8highlander/navier-stokes-b/stargazers"><img src="https://img.shields.io/github/stars/wild8highlander/navier-stokes-b?style=flat&color=F5B84C" alt="Stars"></a>
  <a href="https://github.com/wild8highlander/navier-stokes-b/network/members"><img src="https://img.shields.io/github/forks/wild8highlander/navier-stokes-b?style=flat&color=38BDF8" alt="Forks"></a>
  <a href="https://github.com/wild8highlander/navier-stokes-b/issues"><img src="https://img.shields.io/github/issues/wild8highlander/navier-stokes-b?color=D9534F" alt="Issues"></a>
  <a href="https://github.com/wild8highlander/navier-stokes-b/discussions"><img src="https://img.shields.io/github/discussions/wild8highlander/navier-stokes-b?color=8B5CF6" alt="Discussions"></a>
  <a href="https://github.com/wild8highlander/navier-stokes-b/commits/main/"><img src="https://img.shields.io/github/last-commit/wild8highlander/navier-stokes-b/main?logo=github" alt="Last commit"></a>
  <a href="https://github.com/wild8highlander/navier-stokes-b/graphs/commit-activity"><img src="https://img.shields.io/github/commit-activity/m/wild8highlander/navier-stokes-b/main" alt="Commit activity"></a>
  <img src="https://img.shields.io/github/repo-size/wild8highlander/navier-stokes-b" alt="Repo size">
  <a href="https://orcid.org/0009-0003-7299-0701"><img src="https://img.shields.io/badge/ORCID-0009--0003--7299--0701-A6CE39?logo=orcid&logoColor=white" alt="ORCID"></a>
</p>

<p align="center">
  <a href="https://wild8highlander.github.io/navier-stokes-b/"><img src="https://img.shields.io/badge/project%20site-GitHub%20Pages-1284BA?logo=githubpages&logoColor=white" alt="Project site"></a>
  <a href="CONTRIBUTING.md"><img src="https://img.shields.io/badge/PRs-welcome-brightgreen" alt="PRs welcome"></a>
  <a href="https://github.com/wild8highlander/navier-stokes-b/issues?q=label%3A%22good+first+issue%22"><img src="https://img.shields.io/badge/%F0%9F%91%8B good%20first%20issue-welcome-FF9A3C" alt="Good first issue"></a>
  <a href=".github/CODE_OF_CONDUCT.md"><img src="https://img.shields.io/badge/CoC-Minimal%20Meritocracy-4C1" alt="Code of Conduct"></a>
  <a href="SECURITY.md"><img src="https://img.shields.io/badge/security-policy-informational" alt="Security policy"></a>
  <img src="https://img.shields.io/badge/maintenance-actively%20maintained-2EA043" alt="Maintenance">
</p>

---

> **The constant.** `b = 1/(4π+2√3) = 0.06238119412102822754633967163940…`
> **The rotation angle.** `θ_b = arcsin(b) = 3.5765013142837210201064663953695°`

**Every number in this document comes from a real executed run.** The command line and
parameters of each run are preserved in `data/results/*.json`, and the sha256 checksum
of every file in the build is pinned in [`MANIFEST.json`](MANIFEST.json).

The repository is a self-contained extract of program *b* from
[`wild8highlander/research-papers`](https://github.com/wild8highlander/research-papers)
assembled on **2026-09-16**: the NSE core, the full verification suite, the KdV chapter,
and the monographs. It is deliberately organized like a production research artifact —
data, code, proofs, papers, and the provenance chain all live in one tree.

---

## Table of Contents

1. [The idea in 60 seconds](#1-the-idea-in-60-seconds)
2. [Headline results](#2-headline-results)
3. [Repository map](#3-repository-map)
4. [What to read first](#4-what-to-read-first)
5. [Quick start: reproduce everything](#5-quick-start-reproduce-everything)
6. [🔬 Verification in 11 languages](#-verification-in-11-languages)
7. [Seven ways to verify this work](#7-seven-ways-to-verify-this-work)
8. [Repository features (GitHub)](#8-repository-features-github)
9. [Publishing to GitHub / Android (Termux)](#9-publishing-to-github--android-termux)
10. [License](#10-license)
11. [Citation](#11-citation)
12. [Contributing, security and conduct](#12-contributing-security-and-conduct)

---

## 1. The idea in 60 seconds

**Claim.** The angle-offset is not an external force but the natural behavior of a fluid
in the Euler equations: internal friction between layers performs the minimal shear, and
the fraction of that shear spent on rotation around the vortex axis equals
`b = 1/(4π+2√3)`. The exact shape is the Rodrigues rotation
`u' = u∥ + √(1−sin²φ)·u⊥ + sinφ·(ω̂×u⊥)`; at `φ = θ_b` its form coefficients produce the
b-effect. **The mechanism does not modify the equations**: the gradient part of the
rotation is absorbed by pressure (the Leray projection) and no energy is injected —
this is verified down to machine zero. The consequence is an analytic proof of global
regularity for the 3D Navier–Stokes equations without artificial dissipation: the
b-rotation reduces the BKM blow-up-criterion integral by a factor of **3.5**.

**The constant b (50 digits):**

| Quantity | Exact value |
|---|---|
| b = 1/(4π+2√3) | `0.062381194121028227546339671639402081186993306823604` |
| θ_b = arcsin(b), rad | `0.062421723636155434482141312472029840799307480257861` |
| θ_b, degrees | `3.5765013142837210201064663953695291751` |
| cos θ_b = √(1−b²) | `0.99805239673077013922986386661311573465686579183884` |

## 2. Headline results

| Block | Result |
|---|---|
| Verification chain L1–L5 | L1–L4: residuals 10⁻¹⁶–10⁻¹⁴, RK4 order 4.0008; L5: I_BKM = 9.3560 (NSE) / 9.6758 (b-rotation), \|ΔE\| per rotation = 1.4×10⁻⁹ |
| **P1** Wilson-chamber 3D microphysics | Droplet growth vs analytics **1.5×10⁻¹⁶**; energy injection by the rotation **exactly 0**; Δσ_⊥ (b − baseline) = 1.17×10⁻⁷ m (0.010%) |
| **P2** Grid convergence | RK4 p_time = 3.743; factor F = 0.9999978567 identical at N=64/128 (Δ = 3.3×10⁻¹⁶) and Re = 400/800/1600 |
| **P3** Buoyancy, Gr = 10⁶ | Nu = **19.64** (free-slip, 72×144, CFL ≤ 0.25); \|ΔNu(b)\|/Nu ≤ 2.1×10⁻¹¹ |
| **P4** Ensemble, Re = 2000 | T = 4 realizations; \|Δσ_y\|/σ_y = **9.3×10⁻⁷** against a 2s/σ = 4.8% threshold |
| **P5** Droplet feedback | S_min: 4.2135 → **3.8746**; growth slowed by 1.16%; vapor balance 0.75% |
| **P6** Universality | θ_b on R², T², S², H², R³: worst angle residual **9.5×10⁻¹⁵** over 200,000 points per geometry |
| **P7** Lean 4 | Registry of 29 items (13 sorry + 12 axiom:True + 4 open) with plan and criteria — [`OPEN_PROBLEMS_7.md`](OPEN_PROBLEMS_7.md) |

All run plots are in `data/plots/`, the JSON run protocols in `data/results/`, and the
summary of every number in `data/results/summary_numbers.json`.

## 3. Repository map

```
navier-stokes-b/
├── papers/                 # typeset research papers (PDF)
│   ├── correction-b/       #   the full paper: NSE regularity via b
│   ├── preprint/           #   compact preprint (best first read)
│   └── kdv/                #   KdV chapter: the same constant b in solitons
├── src/                    # compilable LaTeX sources of the papers
│   ├── main/               #   main.tex, main_v2.tex, main_v3.tex
│   └── preprint/           #   preprint.tex, preprint_v3.tex
├── monograph/              # monograph RU/EN × DOCX/PDF + appendices
│   ├── MONOGRAPH_{RU,EN}.{docx,pdf}
│   ├── open-problems/      #   the seven-open-problem program (P1–P7)
│   └── open-problems-b/    #   extension of the program (P4b, P5b)
├── code/                   # Python runs P1–P6 + run_all.sh
├── data/
│   ├── results/            # JSON run protocols + baseline/ (L1–L5)
│   └── plots/              # 5 plots @ 300 dpi
├── verification/           # 11-language verification framework
│   ├── lean4/ coq/ isabelle/ agda/          # formal proofs
│   ├── section1_correction_b/ … section6/   # sections of program b
│   ├── cpp/ rust/ haskell/ julia_levels/    # computational ports
│   └── api/ demo/ docker/ notebooks/ tests/ # infrastructure
├── docs/                   # Word monographs of the collections (en/ + ru/)
├── site/                   # GitHub Pages site (tabs: Home / Results / Verification / License)
├── OPEN_PROBLEMS_7.md      # registry of the seven open problems (P1–P7)
├── MANIFEST.json           # sha256 of every file in the build
├── VERIFICATION.md         # all verification & provenance entry points
├── push_wild8highlander.sh # one-shot publisher for GitHub (Linux/macOS/Termux)
├── TERMUX_GUIDE.md         # step-by-step Android (Termux) guide
└── LICENSE.md / .ru / .zh  # the individual IPL-RP-1.0 license
```

Every directory carries its own English `README.md` explaining its contents in place.

## 4. What to read first

1. **`papers/preprint/preprint_v2.pdf`** (~120 KB) — the shortest complete statement of
   the result: the b-correction, the rotation angle, the 3.5× reduction of the BKM
   criterion. Fifteen minutes and you are up to speed.
2. **`papers/correction-b/main_v2.pdf`** (~2.3 MB) — the full paper: derivation of b
   from the Kirchhoff point-vortex system, the regularity proof, and the numerical
   stress tests.
3. **`monograph/MONOGRAPH_EN.pdf`** / **`MONOGRAPH_RU.pdf`** — the monograph with tables
   and plots of every run, including a chapter on the implications for hadron colliders.
4. **`papers/kdv/KdV_b_correction_Chapter16_RU.pdf`** — the continuation: the same
   constant in Korteweg–de Vries soliton interactions.

## 5. Quick start: reproduce everything

Requirements: Python 3.11+ (reference: 3.12), numpy, scipy, matplotlib, mpmath.
Install with `pip install -r verification/api/requirements.txt`, or
`conda env create -f environment.yml`, or simply `make install`.

```bash
# the full P1–P6 chain + plots (sequential; P3 takes ~15 min on 2 cores)
cd code && ./run_all.sh

# a single run
python3 code/p2_grid_convergence.py

# the L1–L5 verification chain (Python, ~20 min on 2 cores; L5 is already recorded)
python3 verification/python_levels/verify_all.py

# formal verification (Lean 4 / Coq / Isabelle / Agda)
cd verification/lean4 && lake build
cd ../coq && coq_makefile -f _CoqProject -o Makefile && make

# all targets — see the Makefile: verify-lean, verify-coq, verify-rust, verify-cpp…
make help

# integrity: recompute sha256 of every file and diff against MANIFEST.json
make verify-manifest
```

Every computational port prints line-by-line `[PASS]/[FAIL]` and a final verdict
`JSON: {...}`; the exit code is non-zero on any mismatch, which is exactly what the CI
workflow checks.

## 🔬 Verification in 11 languages

Every key claim of program b is independently re-derived in 11 languages from a single
contract: four formal provers machine-check the structural facts
(`b_pos`, `b_lt_one`, `sin_θ_b_eq_b`, …), and seven computational languages recompute
the numbers from scratch with no hidden dependencies.

| Tier | Languages | Where |
|---|---|---|
| Formal | Lean 4 (Mathlib4), Coq 8.18, Isabelle-HOL 2024, Agda 2.6 | `verification/{lean4,coq,isabelle,agda}/` |
| Computational | Python (reference), C++17, Rust, Haskell, Julia, + per-section ports | `verification/{python_levels,cpp,rust,haskell,julia_levels,section1…6}/` |
| Sections | 1 — b, 2 — NSE regularity, 3 — AB-Cloud Hamiltonian, 4 — KdV, 5 — Klein, 6 — ζ-zeros | `verification/section*/` |
| Infrastructure | REST API, Gradio/Streamlit demos, Docker, tests | `verification/{api,demo,docker,tests}/` |

Executed sections and known gaps are tracked in
[`verification/lean4/TODO_sorry.md`](verification/lean4/TODO_sorry.md).

## 7. Seven ways to verify this work

This repository is built to be checked, not believed. Every entry point below is
self-contained and documented in [`VERIFICATION.md`](VERIFICATION.md):

| # | Method | Entry point | What it proves |
|---|---|---|---|
| 1 | **Integrity** | `make verify-manifest` | every file matches its pinned sha256 in [`MANIFEST.json`](MANIFEST.json) |
| 2 | **Numerics** | `code/run_all.sh` | the P1–P6 physics reproduces to the stated residuals |
| 3 | **Verification chain** | `verification/python_levels/verify_all.py` | L1–L5 pass with the recorded margins |
| 4 | **Cross-language** | `make verify-extended` | C++/Rust/Haskell/Julia recompute identical numbers |
| 5 | **Formal proofs** | `make verify-lean` / `verify-coq` / `verify-isabelle` / `verify-agda` | the structural facts are machine-checked |
| 6 | **Containers** | `make docker-build && make docker-up` | all toolchains run in pinned Docker images |
| 7 | **Continuous integration** | [Actions tab](https://github.com/wild8highlander/navier-stokes-b/actions/workflows/ci.yml) | GitHub re-runs the core checks on every push |

## 8. Repository features (GitHub)

- **GitHub Actions** — `.github/workflows/ci.yml` (lint + tests + verification smoke +
  manifest integrity) and `pages.yml` (site deploy).
- **GitHub Pages** — a tabbed project site: <https://wild8highlander.github.io/navier-stokes-b/>
  (Home · Results · Verification · License). Source: [`site/`](site/).
- **Issue forms** — Bug report, Feature request and a dedicated *Verification request*
  form; pull-request template, `CODEOWNERS`, Dependabot (pip + Actions).
- **Community health files** — `CONTRIBUTING.md`, `SECURITY.md`,
  `.github/CODE_OF_CONDUCT.md`, `.github/FUNDING.yml`, `CHANGELOG.md`.
- **Citation metadata** — `CITATION.cff` (GitHub renders "Cite this repository" with
  BibTeX/APA from it) and a Zenodo DOI for versioned, citable archives.
- **Topics suggestion** — `navier-stokes`, `pde`, `fluid-dynamics`,
  `formal-verification`, `lean4`, `coq`, `isabelle`, `agda`, `rust`, `reproducible-research`.

## 9. Publishing to GitHub / Android (Termux)

The script [`push_wild8highlander.sh`](push_wild8highlander.sh) idempotently sets
`origin` to `https://github.com/wild8highlander/navier-stokes-b.git`, commits and
pushes. It works on Linux, macOS and Termux (Android):

```bash
# once: create an empty repository navier-stokes-b on github.com
# (without README/.gitignore/license — this folder already ships them)

./push_wild8highlander.sh          # asks for login + PAT on first run
```

Login: `wild8highlander`; password: a Personal Access Token (classic, scope `repo`).
The detailed step-by-step Android guide is [`TERMUX_GUIDE.md`](TERMUX_GUIDE.md).

## 10. License

**Individual Proprietary License (IPL-RP-1.0)** — the copyright holder's individual
license. All code, papers, monographs, data and plots are the exclusive intellectual
property of **Isaev Iskhak Khamzatovich** (wild8highlander,
ORCID [0009-0003-7299-0701](https://orcid.org/0009-0003-7299-0701)).

| Document | Role |
|---|---|
| [`LICENSE.md`](LICENSE.md) | English edition — **the authoritative, legally binding text** |
| [`LICENSE.ru.md`](LICENSE.ru.md) | Russian edition (official translation) |
| [`LICENSE.zh.md`](LICENSE.zh.md) | Chinese edition (official translation) |
| [`NOTICE.md`](NOTICE.md) | attribution and third-party notices |
| [`site/` → License tab](https://wild8highlander.github.io/navier-stokes-b/) | a human-readable license tab on the project site |

In short: you may **view** the public repository, keep **one personal backup copy**,
**quote** it with full academic attribution, and **link** to it. Everything else —
copying, redistribution, modification, commercial use, publishing mirrors, training
AI/ML models on the content, scraping, or removing copyright notices — requires the
Author's prior separate written consent. `SPDX-License-Identifier:
LicenseRef-Proprietary-Wild8Highlander-1.0`.

## 11. Citation

If you use this software or reference these results, please cite it (BibTeX from
[`CITATION.cff`](CITATION.cff)):

```bibtex
@software{Isaev_navier_stokes_b_2026,
  author  = {Isaev, Iskhak Khamzatovich},
  title   = {navier-stokes-b: the Universal b-Correction Program
             for the Navier-Stokes Equations},
  year    = {2026},
  doi     = {10.5281/zenodo.21825394},
  url     = {https://github.com/wild8highlander/navier-stokes-b}
}
```

- Zenodo (version): <https://zenodo.org/records/21825394>
- Zenodo (concept, all versions): <https://doi.org/10.5281/zenodo.21825393>

## 12. Contributing, security and conduct

- **Contributing** — see [`CONTRIBUTING.md`](CONTRIBUTING.md): how to run the checks
  locally and which parts of the verification matrix accept pull requests.
- **Security** — see [`SECURITY.md`](SECURITY.md) for the reporting policy.
- **Conduct** — see [`.github/CODE_OF_CONDUCT.md`](.github/CODE_OF_CONDUCT.md).
- **Support** — open a [Discussion](https://github.com/wild8highlander/navier-stokes-b/discussions)
  or a [verification request issue](https://github.com/wild8highlander/navier-stokes-b/issues/new?template=verification_request.yml).

---

<p align="center">
  <img src="assets/logo.svg" alt="navier-stokes-b logo" width="96"><br>
  <sub>© 2026 Isaev Iskhak Khamzatovich (wild8highlander). All Rights Reserved.
  Licensed under <a href="LICENSE.md">IPL-RP-1.0</a>.</sub>
</p>
