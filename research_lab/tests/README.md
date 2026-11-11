<!-- nsb-brand:v1 -->
<p align="center">
  <img src="../../assets/assets/brand/header_generic.svg" alt="navier-stokes-b flowing streamlines" width="100%"/>
</p>

# `research_lab/tests/` — the lab's unit tests

> **Navigation:** [repository root](../../README.md) › **`tests`**

![Docs](https://img.shields.io/badge/Role-documentation-2B579A?style=flat-square)
![License](https://img.shields.io/badge/License-IPL--RP--1.0-red?style=flat-square)

---

[`test_lab.py`](test_lab.py) — fast pytest units for the laboratory
package (solver invariants, monitor bounds, protocol shape), run by the
CI job *Research lab smoke* (`pytest research_lab/tests -q`) and
locally via `python -m pytest research_lab/tests -v`.

## License

Part of **navier-stokes-b**, license IPL-RP-1.0. ([LICENSE.md](../../LICENSE.md))
