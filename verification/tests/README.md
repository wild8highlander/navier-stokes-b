# `tests/` — the cross-language validator and the pytest suite

> **Navigation:** [repository root](../README.md) › [verification](../README.md) › **`tests`**

![Validator](https://img.shields.io/badge/extended__cross__language-2B579A?style=flat-square) ![pytest](https://img.shields.io/badge/CI--locked-2EA043?style=flat-square) ![License](https://img.shields.io/badge/IPL--RP--1.0-red?style=flat-square)

---

This directory is the judge of the matrix: it parses every port's verdict
and fails CI on any disagreement, plus the pytest suite that CI runs on
Python 3.11 and 3.12 (toolchain-locked tests auto-skip when the toolchain
is absent).

| File | Role |
|---|---|
| `extended_cross_language_validator.py` | the language × section registry (11 languages × 7 sections), the artifact count, and the report header — extended to Section 7 |
| `test_extended_languages.py` | pytest integration tests for the extended toolchains (auto-skip without the toolchain) |

## Run

```bash
python3 verification/tests/extended_cross_language_validator.py
make test          # pytest over this directory
```

The full mechanical comparison is the pair `make verify-all` (sections
1–7 through the common runner) + `make verify-extended` (C++/Rust/Haskell
builds + Lean/Coq); the repository auditor
([`../repo_integrity/`](../repo_integrity/README.md)) re-runs sections
1–7 end-to-end as its group G.

## License

Part of **navier-stokes-b**, license IPL-RP-1.0. ([LICENSE.md](../LICENSE.md)).
