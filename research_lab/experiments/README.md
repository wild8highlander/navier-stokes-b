<!-- nsb-brand:v1 -->
<p align="center">
  <img src="../../assets/assets/brand/header_generic.svg" alt="navier-stokes-b flowing streamlines" width="100%"/>
</p>

# `research_lab/experiments/` — the four lab experiments

> **Navigation:** [repository root](../../README.md) › **`experiments`**

![Docs](https://img.shields.io/badge/Role-documentation-2B579A?style=flat-square)
![License](https://img.shields.io/badge/License-IPL--RP--1.0-red?style=flat-square)

---

The experiment modules behind `python -m research_lab.run_lab
--experiment …`:

| Module | Experiment |
|---|---|
| [`taylor_green.py`](taylor_green.py) | the 3D Taylor–Green decay reference run |
| [`abc_blowup_hunt.py`](abc_blowup_hunt.py) | the ABC-flow blow-up hunt with BKM monitors |
| [`hou_luo_tubes.py`](hou_luo_tubes.py) | the Hou–Luo vortex-tube scenario |
| [`bcorrection_stress.py`](bcorrection_stress.py) | the b-rotation stress audit |
| [`common.py`](common.py) | the shared solver/diagnostics utilities |

Every experiment is deterministic (fixed seeds) and writes a JSON
protocol; the smoke preset is exercised by CI.

## License

Part of **navier-stokes-b**, license IPL-RP-1.0. ([LICENSE.md](../../LICENSE.md))
