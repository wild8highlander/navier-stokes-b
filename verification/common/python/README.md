# `common/python/` — the runner, the registry, the base class

> **Navigation:** [repository root](../../README.md) › [verification](../../README.md) › [common](../README.md) › **`python/`**

![Module](https://img.shields.io/badge/main.py_·_config.py-3776AB?style=flat-square) ![Contract](https://img.shields.io/badge/enforced-2EA043?style=flat-square) ![License](https://img.shields.io/badge/IPL--RP--1.0-red?style=flat-square)

---

## `main.py` — the aggregate runner

Runs `verification/sectionN_*/python/verify.py` as a subprocess and
enforces the repository-wide contract:

```text
banner  →  [PASS]/[FAIL] per assertion  →  JSON: {"section": N, …}  →  exit 0 iff all passed
```

Usage:

```bash
python main.py --section 1 --preset default
python main.py --all              # every section 1..7
```

## `config.py` — registry and presets

| Preset | N | tolerance | max_iter |
|---|---|---|---|
| `quick` | 16 | 1e-3 | 1 000 |
| `default` | 36 | 1e-10 | 10 000 |
| `full` | 64 | 1e-14 | 50 000 |
| `extreme` | 128 | 1e-16 | 100 000 |

Section names 1–7: Correction b · Preprint NSE · AB-Cloud · KdV · Klein
attractor · Riemann zeros · **Smagorinsky–Kolmogorov**.

## `verifier_base.py`

The small base class the API and the demos use to parse a port's verdict
line without re-implementing the contract.

## License

Part of **navier-stokes-b**, license IPL-RP-1.0. ([LICENSE.md](../../LICENSE.md)).
