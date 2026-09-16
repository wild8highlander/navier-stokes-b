# Changelog

All notable changes to **navier-stokes-b** are documented here.
The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/);
versioning is tag-based (`v*`), and each tag produces a draft GitHub Release with
pinned archives and `SHA256SUMS.txt`.

## [Unreleased]

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
