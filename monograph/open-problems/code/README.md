# `monograph/open-problems/code/` — the Runnable Scripts of P1–P7

> **Navigation:** [`open-problems`](../README.md) › **`code`**

![Python](https://img.shields.io/badge/Python-3.11%2B-3776AB?style=flat-square&logo=python&logoColor=white) ![License](https://img.shields.io/badge/License-IPL--RP--1.0-red?style=flat-square)

One script per problem plus the aggregator — all deterministic (fixed
seeds), all idempotent (each run overwrites its own JSON in
[`results/`](../results/README.md)), all self-auditing (each prints its
pre-registered success criteria and marks each achieved/failed).

## Scripts

| Script | Role |
|---|---|
| [`core_b.py`](core_b.py) | the shared core: closed-form b, θ_b, the Rodrigues rotation and the Leray projection used by every problem |
| [`run_all.py`](run_all.py) | the aggregator — runs P1b…P7 in dependency order and prints the registered criteria |
| [`make_figures.py`](make_figures.py) | regenerates every figure in [figures/](../figures/README.md) from the JSONs in [results/](../results/README.md) |
| [`p1b_droplet_feedback.py`](p1b_droplet_feedback.py) | P1b — the droplet-feedback follow-up of P1 (paired seeds, two-way coupling) |
| [`p2_track_momentum.py`](p2_track_momentum.py) | P2 — track momentum bookkeeping under the b-protocol |
| [`p3_surface_universality.py`](p3_surface_universality.py) | P3 — universality of θ_b across surfaces |
| [`p4_ensemble.py`](p4_ensemble.py) | P4 — the ensemble dispersion study (the T = 2+ baseline) |
| [`p5_bprotocol.py`](p5_bprotocol.py) | P5 — the b-protocol communication experiment (Weyl–Dirichlet sums) |
| [`p6_taylor_green_bkm.py`](p6_taylor_green_bkm.py) | P6 — the Taylor–Green BKM integration under the continuous rotation |
| [`p7_collider_scale.py`](p7_collider_scale.py) | P7 — the collider-scale extrapolation chapter's numbers |

## Run

```bash
python3 run_all.py             # everything, ~10 min on 2 cores
python3 p5_bprotocol.py        # a single problem
python3 make_figures.py        # regenerate the figures afterwards
```

Every number in the [master document](../OPEN_PROBLEMS_7.md) comes from
these scripts — no hand-written values anywhere. If a rerun on your
platform disagrees with the pinned JSON in
[`results/`](../results/README.md), that is a
[verification request](https://github.com/wild8highlander/navier-stokes-b/issues/new?template=verification_request.yml).

---

---

Navigation: [open-problems](../README.md) · [results](../results/README.md) · [figures](../figures/README.md) · [IPL-RP-1.0](../../../LICENSE.md)

*Part of [wild8highlander/navier-stokes-b](https://github.com/wild8highlander/navier-stokes-b) - (c) 2026 Isaev Iskhak Khamzatovich, all rights reserved.*

