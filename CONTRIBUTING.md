# Contributing to navier-stokes-b

Thank you for considering a contribution. This repository is **proprietary**
(IPL-RP-1.0), which shapes the workflow: contributions are accepted as *offers* to the
copyright holder rather than as transfers of rights. Everything below explains how to
contribute smoothly and what the maintainers check before merging.

## 1. Ways to contribute

| Contribution type | Examples | Where |
|---|---|---|
| Reproduction reports | rerun P1–P6 or L1–L5 and confirm/refute the numbers | [verification request issue](https://github.com/wild8highlander/navier-stokes-b/issues/new?template=verification_request.yml) |
| Bug fixes | path errors, platform quirks (Windows/Termux), API fixes | PR |
| New verification ports | a section port in a new language | PR + issue first |
| Formal proof work | closing a `sorry` from `verification/lean4/TODO_sorry.md` | PR + issue first |
| Documentation | English clarifications, README fixes, site improvements | PR |
| Tooling | Makefile targets, CI, Docker improvements | PR |

**Before opening a PR for a new feature**, open an issue or a Discussion first — this
keeps the scope aligned with the research program.

## 2. Local setup

```bash
git clone https://github.com/wild8highlander/navier-stokes-b.git
cd navier-stokes-b
make install                 # numpy, scipy, matplotlib, mpmath, pytest, ruff
python -m pytest verification/tests/ -v     # heavy toolchains auto-skip
make verify-manifest         # sha256 integrity of the whole tree
```

Optional toolchains (needed only for the corresponding verification targets):

```bash
make verify-lean    # Lean 4 + Mathlib4 (elan)
make verify-coq     # Coq 8.18 (opam)
make verify-rust    # cargo
make verify-cpp     # cmake + a C++17 compiler
make verify-haskell # cabal
```

## 3. Rules of the tree

1. **English-only documentation.** All README files, the site, and license-adjacent
   docs are written in English. Do not introduce Cyrillic or other scripts into
   documentation.
2. **Every directory has a README.** If you add a directory, add an English
   `README.md` describing its contents, entry points, and outputs.
3. **Numbers are contracts.** If your change alters any result, you must update the
   JSON protocol in `data/results/` and every README/monograph text that quotes the
   number — in the same PR.
4. **Integrity.** After legit content changes, regenerate `MANIFEST.json`
   (see `VERIFICATION.md`, §Manifest) and include it in the PR.
5. **No new heavyweight dependencies** in the core scientific stack without discussion.

## 4. Commit and PR style

- Conventional Commits prefixes: `feat:`, `fix:`, `docs:`, `verify:`, `ci:`, `data:`.
- One logical change per PR; keep the PR template checklist green.
- CI must pass: lint, pytest matrix, verification smoke, manifest integrity.

## 5. Licensing of contributions

By submitting a pull request or a patch you agree that:

1. Your contribution is offered **to the copyright holder** under the repository license
   ([`LICENSE.md`](LICENSE.md), IPL-RP-1.0);
2. You retain no rights to demand attribution or removal after acceptance;
3. You confirm the contribution is your own original work or you have the right to
   submit it under these terms.

## 6. Reporting bugs securely

See [`SECURITY.md`](SECURITY.md). Non-security bugs go to
[bug report](https://github.com/wild8highlander/navier-stokes-b/issues/new?template=bug_report.yml).

## 7. Code review process

The author ([@wild8highlander](https://github.com/wild8highlander)) reviews all PRs
(see `.github/CODEOWNERS`). Expect a first response within a few days; verification
PRs may take longer because each one is *executed* before merge, not just read.

---
© 2026 Isaev Iskhak Khamzatovich (wild8highlander). All Rights Reserved.
