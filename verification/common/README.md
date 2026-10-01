# `common/` — shared verification utilities

> **Navigation:** [repository root](../README.md) › [verification](../README.md) › **`common`**

![Role](https://img.shields.io/badge/shared--harness-2EA043?style=flat-square) ![Language](https://img.shields.io/badge/Python-3776AB?style=flat-square) ![License](https://img.shields.io/badge/IPL--RP--1.0-red?style=flat-square)

---

This directory holds the pieces every Python port shares: the aggregate
CLI that runs a section verifier as a subprocess and enforces the output
contract, the section registry, and the preset system. The design rule is
deliberately conservative: **the section verifiers never import this
code** — they stay stdlib-only and independently runnable — while the
*runner* (which is allowed to have opinions) wraps them uniformly.

## What lives here

| Path | Role |
|---|---|
| [`python/main.py`](python/README.md) | the aggregate runner: `--section N --preset P`, enforces banner → PASS/FAIL → JSON verdict → exit code |
| [`python/config.py`](python/README.md) | the section registry (names of sections 1–7) and the preset table (quick / default / full / extreme) |
| [`python/verifier_base.py`](python/README.md) | the base class used by tooling that builds on the contract (API, demos) |
| [`python/__init__.py`](python/README.md) | package marker |

## Run

```bash
# one section through the uniform harness
python3 verification/common/python/main.py --section 7 --preset default

# every section 1..7
python3 verification/common/python/main.py --all
```

The runner is what `make verify-all` invokes; it exits non-zero on any
failure, which is the CI hook.

## License

Part of **navier-stokes-b**, license IPL-RP-1.0. ([LICENSE.md](../LICENSE.md)).
