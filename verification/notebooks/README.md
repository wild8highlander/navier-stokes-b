# 📓 `verification/notebooks/` — the Jupyter Entry Point

> **Navigation:** [`verification`](../README.md) › **`notebook`**

![Jupyter](https://img.shields.io/badge/Tool-Jupyter-F37626?style=flat-square&logo=jupyter&logoColor=white) ![License](https://img.shields.io/badge/License-IPL--RP--1.0-red?style=flat-square)

The notebook-based access layer to the verification ports: launch Jupyter
from this directory and drive the verifiers interactively — run a section,
inspect the JSON verdict, plot the residuals, compare languages cell by
cell.

## Contents

| File | Description |
|---|---|
| [`requirements.txt`](requirements.txt) | pinned Jupyter + scientific dependencies |

## How to use

```bash
pip install -r verification/notebooks/requirements.txt
cd verification/notebooks && jupyter lab
```

Suggested first cells:

```python
import subprocess, json, pathlib
root = pathlib.Path("../..").resolve()
out = subprocess.run(
    ["python3", str(root / "verification/section1_correction_b/python/verify.py")],
    capture_output=True, text=True)
print(out.stdout)
```

The notebook path is intentionally thin: it adds no logic of its own, it
just shells into the same contract-based ports — everything the notebook
shows, the CLI shows identically, and the
[validator](../tests/README.md) consumes.

---

---

Navigation: [repository root](../../README.md) · [framework hub](../README.md) · [IPL-RP-1.0](../../LICENSE.md)

*Part of [wild8highlander/navier-stokes-b](https://github.com/wild8highlander/navier-stokes-b) - (c) 2026 Isaev Iskhak Khamzatovich, all rights reserved.*

