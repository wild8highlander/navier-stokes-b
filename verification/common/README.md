# 🧰 `verification/common/` — Shared Utilities

> **Navigation:** [`verification`](../README.md) › **`common`**

![Python](https://img.shields.io/badge/Python-3.10--3.12-3776AB?style=flat-square&logo=python&logoColor=white) ![License](https://img.shields.io/badge/License-IPL--RP--1.0-red?style=flat-square)

The shared plumbing of the Python tier: the verifier base class that
implements the framework's output protocol (banner → assertions → JSON
verdict → exit code), the central configuration, and the aggregate CLI
that runs sections through the shared base. Everything user-facing — the
[REST API](../api/README.md), the [demos](../demo/README.md), the
[notebooks](../notebooks/README.md) — is a thin shell over this package.

## Design notes

- **The protocol lives in one place.** The PASS/JSON/exit-code contract is
  implemented once, in `verifier_base.py`; a change to the contract is a
  one-file diff plus the atomic validator update — not a sweep over ports.
- **Configuration is data.** Section paths, tolerances and output options
  sit in `config.py`, so adding a section to the aggregate CLI is a data
  change.
- **The CLI is for humans and CI.** `main.py` runs one or all sections with
  the same output the standalone ports produce.

## Contents

| Item | Contents |
|---|---|
| [`python/`](python/README.md) | the package itself: `verifier_base`, `config`, `main`, `__init__` |

## Usage

```bash
python3 verification/common/python/main.py --section 1 --preset default
```

---

---

Navigation: [repository root](../../README.md) · [python package](python/README.md) · [api](../api/README.md) · [IPL-RP-1.0](../../LICENSE.md)

*Part of [wild8highlander/navier-stokes-b](https://github.com/wild8highlander/navier-stokes-b) - (c) 2026 Isaev Iskhak Khamzatovich, all rights reserved.*

