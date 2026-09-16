# 📜 verification · scripts — Cross-Validation & API Bootstrap

> **Navigation:** [`verification`](../README.md) › **`scripts`**

![Type](https://img.shields.io/badge/Type-Shell-89E051?style=flat-square&logo=gnubash&logoColor=white) ![License](https://img.shields.io/badge/License-IPL--RP--1.0-red?style=flat-square)

Operational **shell scripts** for the framework's two composed workflows. `run_cross_validation.sh` drives the cross-language validation locally — invoking the section ports across the available toolchains and collecting their verdicts, the same duty `ci-cross-language.yml` performs in CI. `start_api.sh` bootstraps the REST API: installs the pinned requirements, exports the environment and launches [`api/server.py`](../api/README.md).

## 📂 Contents — What Lives Here

| File | Size | Description |
|---|---|---|
| [`run_cross_validation.sh`](run_cross_validation.sh) | 48 B | local cross-language validation driver — runs ports, collects verdicts |
| [`start_api.sh`](start_api.sh) | 77 B | API bootstrap — installs requirements, launches the Flask verifier service |

## ▶️ How to Run

```bash
bash verification/scripts/run_cross_validation.sh
bash verification/scripts/start_api.sh
```

## 🔗 Cross-References

- [REST API](../api/README.md)
- [CI cross-language workflow](../../.github/workflows/README.md)

## 🇷🇺 Brief Summary (Russian Summary)

Two shell scripts: local cross-validation of the ports (a CI analogue) and starting the REST API (dependency installation + Flask launch).

---

<div align="center">

**[⬆ Back to top](#-verification--scripts--cross-validation--api-bootstrap)** · 
**[Repository root](../README.md)**

*Part of [wild8highlander/navier-stokes-b](https://github.com/wild8highlander/navier-stokes-b) · Licensed under [IPL-RP-1.0](https://github.com/wild8highlander/navier-stokes-b/blob/main/LICENSE.md) — All Rights Reserved*

</div>
<!-- doc-enhancer:block v1 (auto-generated block; license files are not affected) -->

---

## 🧭 Navigation and Quick Links (auto)

- 🏠 [Repository root](../../../README.md)
- 📖 [How the claims are verified](../../../verification/README.md)
- 📄 [Papers (PDF)](../../../papers/README.md) · 📚 [Monographs](../../../docs/README.md) · 🧾 [LaTeX](../../../src/README.md)
- ⚖️ [IPL-RP-1.0 License](../../../LICENSE.md) — viewing, a single backup copy, and citation with attribution are permitted; everything else — only with the author's written consent.

*Block added automatically (`doc-enhancer v1`); it is unrelated to the license and does not modify it. Re-running the script does not duplicate the block.*

