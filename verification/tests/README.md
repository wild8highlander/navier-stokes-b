# 🧪 `verification/tests/` — the Cross-Language Validator and Integration Tests

> **Navigation:** [`verification`](../README.md) › **`tests`**

![Role](https://img.shields.io/badge/Role-Validator_%2B_tests-FF8C00?style=flat-square)
![pytest](https://img.shields.io/badge/Runner-pytest-0A9EDC?style=flat-square&logo=pytest&logoColor=white) ![License](https://img.shields.io/badge/License-IPL--RP--1.0-red?style=flat-square)

The framework's **referee and integration layer**. The validator runs
every registered computational port (or reads archived verdicts), parses
each port's single `JSON: Ellipsis` line, and diffs every language's values
against the Python reference within declared tolerances — non-zero exit on
any disagreement. The pytest suite wraps the extended-language ports as
integration tests that auto-skip when a toolchain is absent, so the same
suite is useful on a full CI runner and on a minimal laptop.

## Contents

| File | Description |
|---|---|
| [`extended_cross_language_validator.py`](extended_cross_language_validator.py) | the referee — collect → normalise → compare → report → exit code |
| [`test_extended_languages.py`](test_extended_languages.py) | pytest integration tests for the extended ports (toolchain-locked, auto-skipping) |

## How to run

```bash
python3 verification/tests/extended_cross_language_validator.py   # the whole matrix
python -m pytest verification/tests/ -v --tb=short                # the integration suite
```

The validator's logic is deliberately transparent: collect every port's
verdict, map section number → expected value-key set, diff against the
Python reference, print a per-section per-language OK/FAIL matrix, exit
non-zero on any disagreement. CI runs it on every push — its green is the
framework's core invariant (see the
[hub's "what passing means"](../README.md)).

---

---

Navigation: [repository root](../../README.md) · [framework hub](../README.md) · [CI](../../.github/workflows/README.md) · [IPL-RP-1.0](../../LICENSE.md)

*Part of [wild8highlander/navier-stokes-b](https://github.com/wild8highlander/navier-stokes-b) - (c) 2026 Isaev Iskhak Khamzatovich, all rights reserved.*

