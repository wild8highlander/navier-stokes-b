# 🧰 `common/python/` — the Utility Package

> **Navigation:** [`common`](../README.md) › **`python`**

![Python](https://img.shields.io/badge/Python-3.10--3.12-3776AB?style=flat-square&logo=python&logoColor=white) ![License](https://img.shields.io/badge/License-IPL--RP--1.0-red?style=flat-square)

The **utility package itself**: four modules totalling ~2 KB. Imported by
the [API](../../api/README.md), the [demos](../../demo/README.md) and the
[notebooks](../../notebooks/README.md); the design notes live in the
[parent README](../README.md).

## Modules

| File | Description |
|---|---|
| [`__init__.py`](__init__.py) | package exports |
| [`config.py`](config.py) | central configuration — section paths, tolerances, output options |
| [`main.py`](main.py) | the aggregate CLI — runs sections through the shared base (`--section N --preset …`) |
| [`verifier_base.py`](verifier_base.py) | the base verifier class — banner, assertion ledger, JSON verdict emission; the single implementation of the framework's output contract |

## Extend

Adding a section to the aggregate flow: append its path and tolerances in
`config.py`; the base class handles banner, ledger and verdict. Adding a
new output surface (API route, demo widget): import `verifier_base` — do
not re-implement the protocol.

---

---

Navigation: [common](../README.md) · [framework hub](../../README.md) · [IPL-RP-1.0](../../../LICENSE.md)

*Part of [wild8highlander/navier-stokes-b](https://github.com/wild8highlander/navier-stokes-b) - (c) 2026 Isaev Iskhak Khamzatovich, all rights reserved.*

