# 🐚 `verification/scripts/` — Cross-Validation and API Bootstrap

> **Navigation:** [`verification`](../README.md) › **`scripts`**

![Type](https://img.shields.io/badge/Type-Shell_scripts-4EAA25?style=flat-square&logo=gnubash&logoColor=white) ![License](https://img.shields.io/badge/License-IPL--RP--1.0-red?style=flat-square)

The one-liner shell entry points for the two most common maintenance
operations: running the whole cross-language validation and booting the
REST API. They exist so the operations are copy-pasteable from CI logs and
issue comments without re-reading the framework hub.

## Contents

| File | Description |
|---|---|
| [`run_cross_validation.sh`](run_cross_validation.sh) | runs every computational port and the validator — the cross-language gate in one command |
| [`start_api.sh`](start_api.sh) | installs the API requirements and boots the Flask server |

## Usage

```bash
bash verification/scripts/run_cross_validation.sh
bash verification/scripts/start_api.sh
```

Both scripts are thin wrappers (set -e, cd to the repo root, invoke the
documented entry points) — read them in ten seconds, trust them in one.

---

---

Navigation: [repository root](../../README.md) · [tests](../tests/README.md) · [api](../api/README.md) · [IPL-RP-1.0](../../LICENSE.md)

*Part of [wild8highlander/navier-stokes-b](https://github.com/wild8highlander/navier-stokes-b) - (c) 2026 Isaev Iskhak Khamzatovich, all rights reserved.*

