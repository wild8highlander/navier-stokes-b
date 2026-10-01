# Changelog

All notable changes to **navier-stokes-b** are documented here.
The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/);
versioning is tag-based (`v*`), and each tag produces a draft GitHub Release with
pinned archives and `SHA256SUMS.txt`.

## [Unreleased]

### Added — documentation upgrade (2026-10-01, this revision)
- **Root README rewritten**: the NSB-96-UPGRADE laboratories (L1–L17,
  aggregate WIN 67 · DRAW 7 · LOSS 2), the Smagorinsky–Kolmogorov
  satellite with the master relation `C_s = 1/(π(3C_K/2)^{3/4})`,
  the KdV chapter 16 §16.29 exact-solver protocol, the fluid web app,
  a Mermaid architecture graph, four GIF physics animations and eleven
  academic figures embedded.
- **New academic figure set** (`assets/figures/`, 11 × 300 dpi PNG):
  b-anatomy, Rodrigues rotation geometry, headline residuals, labs
  scoreboard, master relation, verification matrix, program timeline,
  KdV b-family, L16 convergence, P6 universality, BKM protocol — every
  number from a pinned protocol.
- **New animation set** (`assets/animations/`, 4 GIF): stepwise
  b-rotation, exact Hirota two-soliton collision, Taylor–Green decay
  (real pseudo-spectral solver N = 96), the E(k, t) cascade.
- **Verification section 7 — Smagorinsky–Kolmogorov master relation**:
  Python reference port (14 assertions incl. the 50-digit master
  relation, the exact −3/4 exponent law, Cassini k = 0..40, the (5′)
  coefficient algebra a·b·b·c / a·a·b·b, the symmetry theorem) plus
  ports in C++17, Rust, Haskell, Julia (L7) and Lean 4 / Coq /
  Isabelle / Agda; wired into CMake, the Cargo workspace, the Cabal
  project, `_CoqProject`, the Isabelle `ROOT`, `julia verify_all`,
  the common runner, the REST API and both demos.
- **Repository-integrity auditor** (`verification/repo_integrity/`,
  `make verify-repo`): nine evidence groups covering every section and
  folder — docs hygiene, core constants, the physics chain P1–P6, the
  baseline chain, the NSB-96 labs, the monographs, sections 1–7
  end-to-end, the figure/animation sets, the services.
- README layer regenerated/expanded across the whole tree (every
  directory documented, English-only; galleries for `assets/figures/`
  and `assets/animations/`; new READMEs for `papers/kdv/`,
  `papers/kdv/kdv/`, `research_col_smar/{tools,reports,reference}/`,
  `research_col_smar/results/results/`, the NSB-96 figures and the
  updated monograph editions).
- `verification/lean4/TODO_sorry.md` translated to English and extended
  with the Section-7 ledger entries (S7-CASSINI, S7-EXPLAW, S7-ANTI)
  and closing plans.
- `push_wild8highlander.sh` restored to the working tree.
- Makefile: `verify-repo` target; `verify-python` extended to sections
  1–7; cross-language validator rewritten (registry + `--run` mode,
  7 sections × 10 languages).

### Changed — documentation upgrade (2026-10-01)
- `research_col_smar/README.md` restructured (NSB-96 suite section, the
  Section-7 bridge, renumbered TOC, 834 lines).
- `verification/README.md` hub rewritten for the seven-section matrix
  with the integrity-auditor tier.
- `code/README.md`: P2 recorded order corrected to the protocol value
  3.994; NSB-96 cross-references.
- `papers/README.md`, `assets/README.md`: KdV §16.29 and gallery rows.
- `verification/demo/{gradio_app.py,streamlit_app.py}`: real subprocess
  execution of sections 1–7 instead of a static constant printout.

### Added
- Repository modernization: `assets/` brand (SVG logo, banner, favicon), tabbed
  GitHub Pages site (`site/`), CI/Pages/Release workflows, issue forms (bug,
  feature, verification request), pull-request template, `CODEOWNERS`, Dependabot,
  `FUNDING.yml`.
- Community files: `CONTRIBUTING.md`, `SECURITY.md`, `VERIFICATION.md`,
  `CHANGELOG.md`, `.github/CODE_OF_CONDUCT.md`.
- `Makefile` targets: `verify-manifest`, `manifest`, `check-readmes`.
- English-only documentation policy: all 120+ directory READMEs translated to English;
  new READMEs for `code/`, `data/`, `monograph/`, figures and results subdirectories.

### Changed
- Root `README.md` rewritten in English with the full badge set, a seven-way
  verification table, and the GitHub-features overview.
- `MANIFEST.json` regenerated for the modernized tree.

## [1.0.0] — 2026-09-16

### Added
- Initial import of the universal b-correction program from
  [`wild8highlander/research-papers`](https://github.com/wild8highlander/research-papers).
- NSE core: papers (`papers/correction-b`, `papers/preprint`, `papers/kdv`), LaTeX
  sources (`src/`), monographs (`monograph/`, `docs/`), physics runs P1–P6 (`code/`),
  results and plots (`data/`).
- 11-language verification framework (`verification/`): Lean 4, Coq, Isabelle, Agda,
  C++, Rust, Haskell, Julia, Python + infrastructure (API, demos, Docker, notebooks,
  tests).
- Individual Proprietary License IPL-RP-1.0 (`LICENSE.md`, `.ru`, `.zh`), `NOTICE.md`,
  `CITATION.cff` with Zenodo DOI.
- `MANIFEST.json` with sha256 of all files; `push_wild8highlander.sh`;
  `TERMUX_GUIDE.md`.
