# `monograph/open-problems/` — the P1–P7 Package

> **Navigation:** [`monograph`](../README.md) › **`open-problems`**

![Runs](https://img.shields.io/badge/Program-P1%E2%80%93P7_executed-2EA043?style=flat-square)
![Bilingual](https://img.shields.io/badge/Master_doc-RU_%2B_EN-1284BA?style=flat-square) ![License](https://img.shields.io/badge/License-IPL--RP--1.0-red?style=flat-square)

The open-problems package of the b = 1/(4π + 2√3) program. Master document:
[`OPEN_PROBLEMS_7.md`](OPEN_PROBLEMS_7.md) (bilingual RU/EN). Every number
comes from real runs of **2026-09-16** — scripts in [`code/`](code/README.md),
raw results in [`results/`](results/README.md) (JSON), figures in
[`figures/`](figures/README.md). Provenance and honesty rules are §0 of the
master document; the program's rule is that **both outcomes count as
results** — a measured effect or a strict bound — and which one was
obtained is recorded explicitly.

## Layout

| Item | Contents |
|---|---|
| [`OPEN_PROBLEMS_7.md`](OPEN_PROBLEMS_7.md) | the master document: statement → plan → criteria → outcome, for each of P1–P7 |
| [`code/`](code/README.md) | the runnable scripts (fixed seeds), one per problem + the aggregator |
| [`results/`](results/README.md) | the JSON protocols — every number of the master document |
| [`figures/`](figures/README.md) | the figures generated from the JSONs |
| `push_open_problems.sh` | Termux/POSIX helper that commits and pushes this package |

## One command

```bash
python3 code/run_all.py       # runs everything, ~10 min, regenerates the JSONs
python3 code/make_figures.py  # regenerates the figures from the JSONs
```

The root-level twin of this program — with the same master document and
the Lean 4 registry (P7) — is [`OPEN_PROBLEMS_7.md`](../../OPEN_PROBLEMS_7.md)
at the repository root; the extension line (P4b, P5b) continues in
[`open-problems-b/`](../open-problems-b/README.md).

---

---

Navigation: [repository root](../../README.md) · [monograph](../README.md) · [data/results](../../data/results/README.md) · [IPL-RP-1.0](../../LICENSE.md)

*Part of [wild8highlander/navier-stokes-b](https://github.com/wild8highlander/navier-stokes-b) - (c) 2026 Isaev Iskhak Khamzatovich, all rights reserved.*

