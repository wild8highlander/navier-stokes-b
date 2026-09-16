# 🧰 common · python — the Utility Package

> **Navigation:** [`verification`](../../README.md) › [`common`](../README.md) › **`python`**

![Python](https://img.shields.io/badge/Python-3.10–3.12-informational?style=flat-square&logo=python&logoColor=white) ![License](https://img.shields.io/badge/License-IPL--RP--1.0-red?style=flat-square)

The **utility package** itself: four modules totalling ~2 KB. `verifier_base.py` (the heart) implements the shared verifier protocol; `config.py` the settings; `main.py` the aggregate CLI; `__init__.py` the exports. Imported by the API, the demos and the notebooks — see the parent README for the design notes.

## 📂 Contents — What Lives Here

| File | Size | Description |
|---|---|---|
| [`__init__.py`](__init__.py) | 48 B | package exports |
| [`config.py`](config.py) | 766 B | central configuration — section paths, tolerances, output options |
| [`main.py`](main.py) | 617 B | aggregate CLI — runs multiple sections through the shared base |
| [`verifier_base.py`](verifier_base.py) | 714 B | base verifier class — banner, assertion ledger, JSON verdict emission |

## 🔗 Cross-References

- [Parent — common/](../README.md)
- [Framework root](../../README.md)

## 🇷🇺 Brief Summary (Russian Summary)

A package of utilities: verifier_base (the verifier protocol), config, main (the CLI aggregator), __init__.

---

<div align="center">

**[⬆ Back to top](#-common--python--the-utility-package)** · 
**[Repository root](../../README.md)**

*Part of [wild8highlander/navier-stokes-b](https://github.com/wild8highlander/navier-stokes-b) · Licensed under [IPL-RP-1.0](https://github.com/wild8highlander/navier-stokes-b/blob/main/LICENSE.md) — All Rights Reserved*

</div>
<!-- doc-enhancer:block v1 (auto-generated block; license files are not affected) -->

---

## 🧭 Navigation and Quick Links (auto)

- 🏠 [Repository root](../../../../README.md)
- 📖 [How the claims are verified](../../../../verification/README.md)
- 📄 [Papers (PDF)](../../../../papers/README.md) · 📚 [Monographs](../../../../docs/README.md) · 🧾 [LaTeX](../../../../src/README.md)
- ⚖️ [IPL-RP-1.0 License](../../../../LICENSE.md) — viewing, a single backup copy, and citation with attribution are permitted; everything else — only with the author's written consent.

*Block added automatically (`doc-enhancer v1`); it is unrelated to the license and does not modify it. Re-running the script does not duplicate the block.*

